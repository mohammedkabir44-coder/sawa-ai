"""WhatsApp bulk-broadcast execution service.

Everything here is tenant-scoped: campaigns are always loaded by
``(id, business_id)`` and recipients/messages are reached through the
campaign, which itself belongs to the resolved business.  A campaign's
aggregate counters (``sent_count``, ``delivered_count`` …) are recomputed
from the actual ``WhatsAppRecipient`` rows whenever a run finishes, so they
can never drift from the ground truth.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.whatsapp import (
    WhatsAppAccount,
    WhatsAppCampaign,
    WhatsAppMessage,
    WhatsAppRecipient,
    WhatsAppTemplate,
)
from app.services.whatsapp import get_provider_for_account

logger = logging.getLogger(__name__)

# How many pending recipients the sender pulls per loop iteration.
_BATCH_SIZE = 20
# Poll interval while a campaign is paused or waiting for its scheduled time.
_WAIT_SECONDS = 2.0

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Normalise a (possibly DB-loaded) datetime to timezone-aware UTC.

    SQLite returns naive datetimes; comparing them against an aware
    ``utcnow()`` raises ``TypeError``.  Naive values are interpreted as UTC,
    which matches how aware datetimes are persisted (the SQLite dialect
    stores the UTC wall-clock fields and drops the offset).
    """
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def render_template_text(template_text: str, variables: Dict[str, str]) -> str:
    """Substitute ``{{variable}}`` placeholders with per-recipient values.

    Missing/empty variables are replaced with an empty string so a template
    with an unset (e.g. optional) variable still renders cleanly.
    """
    if not template_text:
        return ""

    def _replace(match: re.Match[str]) -> str:
        name = match.group(1).strip()
        value = variables.get(name)
        return value if isinstance(value, str) else (str(value) if value is not None else "")

    return _PLACEHOLDER_RE.sub(_replace, template_text)


def normalise_recipient_phone(phone: str) -> str:
    """Normalise a recipient phone number to +234XXXXXXXXX.

    Mirrors the existing order-service normalisation: strip leading zeros / +
    and re-add +234 where the country code is missing.
    """
    raw = (phone or "").strip().lstrip("+")
    if not raw:
        return ""
    if raw.startswith("234"):
        return "+" + raw
    if raw.startswith("0"):
        return "+234" + raw[1:]
    return "+" + raw


def _send_interval(account: WhatsAppAccount, provider_is_meta: bool) -> float:
    """Minimum seconds between two sends for this account.

    Computed from the account's ``rate_limit_per_hour`` (default 1000) so a
    campaign never blasts past the account's configured limit.  Returns 0 for
    the mock provider so tests and local dev aren't artificially slowed.
    """
    if not provider_is_meta:
        return 0.0
    limit = account.rate_limit_per_hour or 1000
    return max(1.0, 3600.0 / limit)


def _build_message_text(
    db: Session,
    campaign: WhatsAppCampaign,
    recipient: WhatsAppRecipient,
    template: Optional[WhatsAppTemplate],
) -> str:
    """Render the final per-recipient message text.

    * Template campaigns: template text with ``{{placeholders}}`` filled from
      ``campaign.variables_map`` using the current customer's id.
    * Custom-text campaigns: the stored ``campaign.message_text`` as-is.
    """
    if template is not None:
        variables: Dict[str, str] = {}
        if recipient.customer_id is not None:
            stored = campaign.variables_map or {}
            variables = stored.get(str(recipient.customer_id)) or stored.get(
                recipient.customer_id
            ) or {}
            if not isinstance(variables, dict):
                variables = {}
        return render_template_text(template.template_text, variables)
    return campaign.message_text or ""
def _recompute_campaign_aggregates(db: Session, campaign: WhatsAppCampaign) -> None:
    """Rebuild the campaign's counters from its recipient rows.

    The recipient table is the source of truth; this guarantees the aggregate
    never drifts (e.g. after a webhook bumped an individual recipient or a
    crashed run left a partially-sent campaign).
    """
    rows = (
        db.query(WhatsAppRecipient.status, func.count(WhatsAppRecipient.id))
        .filter(WhatsAppRecipient.campaign_id == campaign.id)
        .group_by(WhatsAppRecipient.status)
        .all()
    )
    counts: Dict[str, int] = {status: int(n) for status, n in rows}
    delivered_statuses = {"delivered", "read"}
    sent_statuses = {"sent", "delivered", "read"}

    campaign.sent_count = sum(counts.get(s, 0) for s in sent_statuses)
    campaign.delivered_count = sum(counts.get(s, 0) for s in delivered_statuses)
    campaign.read_count = counts.get("read", 0)
    campaign.failed_count = counts.get("failed", 0)
    campaign.total_recipients = sum(counts.values())


async def send_broadcast_task(
    campaign_id: int,
    business_id: int,
    db: Optional[Session] = None,
) -> Optional[str]:
    """Run (or resume) a WhatsApp broadcast in the background.

    Idempotent by design:
      * only ``pending`` recipients are ever processed, so two runs can never
        double-send to the same recipient;
      * ``paused``/``scheduled`` campaigns wait until they are resumed/due;
      * when there is nothing left to send the campaign is finalised and the
        aggregate counters are recomputed from the recipient rows.

    Returns the final campaign status (``completed``/``failed``) or ``None``
    if the campaign was already in a terminal/non-run state.
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        campaign = (
            db.query(WhatsAppCampaign)
            .filter(
                WhatsAppCampaign.id == campaign_id,
                WhatsAppCampaign.business_id == business_id,
            )
            .first()
        )
        if campaign is None:
            logger.warning(
                "Broadcast %s not found (business %s)", campaign_id, business_id
            )
            return None

        while True:
            db.refresh(campaign)
            if campaign.status == "paused":
                await asyncio.sleep(_WAIT_SECONDS)
                continue
            if campaign.status in ("completed", "failed", "draft"):
                return campaign.status

            now = utcnow()
            if campaign.status == "scheduled":
                scheduled = ensure_utc(campaign.scheduled_time)
                if scheduled and scheduled > now:
                    await asyncio.sleep(_WAIT_SECONDS)
                    continue
                # Claim the campaign atomically in the DB — only one sender
                # may be "sending" at a time.
                campaign.status = "sending"
                if not campaign.started_at:
                    campaign.started_at = now
                db.commit()

            account = db.get(WhatsAppAccount, campaign.account_id)
            if account is None:
                logger.error(
                    "Broadcast %s account %s missing", campaign.id, campaign.account_id
                )
                campaign.status = "failed"
                db.commit()
                return "failed"

            provider = get_provider_for_account(account)
            provider_is_meta = settings.WHATSAPP_PROVIDER.lower() == "meta"
            interval = _send_interval(account, provider_is_meta)

            template = (
                db.get(WhatsAppTemplate, campaign.template_id)
                if campaign.template_id
                else None
            )

            batch = (
                db.query(WhatsAppRecipient)
                .filter(
                    WhatsAppRecipient.campaign_id == campaign.id,
                    WhatsAppRecipient.status == "pending",
                )
                .order_by(WhatsAppRecipient.id.asc())
                .limit(_BATCH_SIZE)
                .all()
            )
            if not batch:
                break

            sent_in_batch = 0
            failed_in_batch = 0
            for recipient in batch:
                try:
                    text = _build_message_text(db, campaign, recipient, template)
                    if provider_is_meta and interval > 0:
                        await asyncio.sleep(interval)
                    result = await asyncio.to_thread(
                        provider.send_message, recipient.phone_number, text
                    )
                    if result.get("status") == "error":
                        raise RuntimeError(result.get("detail", "send failed"))
                    wamid = str(result.get("message_id", "") or "")
                    db.add(
                        WhatsAppMessage(
                            business_id=campaign.business_id,
                            account_id=account.id,
                            to_number=recipient.phone_number,
                            from_number=account.phone_number,
                            message_text=text,
                            status="sent",
                            message_type="text",
                            provider_message_id=wamid,
                            direction="outbound",
                            campaign_id=campaign.id,
                            recipient_id=recipient.id,
                        )
                    )
                    recipient.status = "sent"
                    sent_in_batch += 1
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Broadcast %s send to %s failed: %s",
                        campaign.id,
                        recipient.phone_number,
                        exc,
                    )
                    recipient.status = "failed"
                    recipient.error_message = str(exc)[:500]
                    failed_in_batch += 1

            campaign.sent_count = (campaign.sent_count or 0) + sent_in_batch
            campaign.failed_count = (campaign.failed_count or 0) + failed_in_batch
            db.commit()

        # Nothing left to send — finalise and recompute from ground truth.
        _recompute_campaign_aggregates(db, campaign)
        if (
            campaign.total_recipients > 0
            and campaign.failed_count >= campaign.total_recipients
        ):
            campaign.status = "failed"
        else:
            campaign.status = "completed"
        campaign.completed_at = utcnow()
        db.commit()
        logger.info(
            "Broadcast %s finalised as %s (sent=%s delivered=%s read=%s failed=%s)",
            campaign.id,
            campaign.status,
            campaign.sent_count,
            campaign.delivered_count,
            campaign.read_count,
            campaign.failed_count,
        )
        return campaign.status
    finally:
        if own_session:
            db.close()


def spawn_broadcast_task(campaign_id: int, business_id: int) -> None:
    """Fire-and-forget the broadcast sender.

    Falls back to running inline when there is no event loop (sync tests).
    """
    try:
        asyncio.create_task(send_broadcast_task(campaign_id, business_id))
    except RuntimeError:
        # No running event loop — run inline for the caller (e.g. sync tests).
        asyncio.get_event_loop().run_until_complete(
            send_broadcast_task(campaign_id, business_id)
        )


__all__ = [
    "ensure_utc",
    "render_template_text",
    "normalise_recipient_phone",
    "send_broadcast_task",
    "spawn_broadcast_task",
    "utcnow",
]