"""Campaign endpoints (tenant-scoped create, list, execute)."""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import (
    require_business_owner,
    require_membership,
    require_permission,
)
from app.core.database import get_db
from app.models.business import Business
from app.models.campaign import Campaign, CampaignRecipient
from app.models.customer import Customer
from app.models.user import BusinessUser, User
from app.schemas.campaign import (
    CampaignCreate,
    CampaignExecuteOut,
    CampaignList,
    CampaignOut,
)
from app.services.sms import get_sms_provider
from app.services.workflow_engine import send_whatsapp_message

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_campaign_or_404(db: Session, business_id: int, campaign_id: int) -> Campaign:
    """Fetch a campaign that belongs to the given business or raise 404."""
    campaign = (
        db.query(Campaign)
        .filter(Campaign.id == campaign_id, Campaign.business_id == business_id)
        .first()
    )
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return campaign


def _parse_audience(audience_raw: str) -> Dict[str, Any]:
    """Parse the JSON ``audience`` column into a dict (safe fallback to {})."""
    try:
        parsed = json.loads(audience_raw or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, TypeError):
        return {}


def _match_customers(db: Session, business_id: int, audience: Dict[str, Any]) -> List[Customer]:
    """Return customers in the business that match the campaign audience.

    Supported audience shapes:
      * ``{"all": true}`` — every customer of the business.
      * ``{"tags": ["VIP", ...]}`` — customers with at least one of the tags
        (tags are stored comma-separated on the Customer row).
      * ``{"source": "whatsapp"}`` — customers from a given source.
      * ``{"language": "ha"}`` — customers with a given preferred_language.
    When the audience dict is empty we fall back to *all* customers so a
    manual "send to everyone" campaign still works.
    """
    query = db.query(Customer).filter(Customer.business_id == business_id)

    tags = audience.get("tags") or []
    if tags:
        like_conditions = [Customer.tags.ilike(f"%{tag.strip()}%") for tag in tags]
        query = query.filter(or_(*like_conditions))

    source = audience.get("source")
    if source:
        query = query.filter(Customer.source == source)

    language = audience.get("language")
    if language:
        query = query.filter(Customer.preferred_language == language)

    customers = query.order_by(Customer.id.asc()).all()

    # Only target customers that have a usable phone number.
    return [c for c in customers if c.phone and c.phone.strip()]


async def _deliver_one(
    campaign: Campaign,
    phone: str,
) -> tuple[str, str]:
    """Send the campaign message on the campaign channel(s).

    Returns ``(status, provider_message_id)`` where status is ``sent`` or
    ``failed``.
    """
    channel = campaign.channel
    provider_ids: List[str] = []
    try:
        if channel in ("whatsapp", "both"):
            wa = await send_whatsapp_message(phone, campaign.message)
            if wa.get("status") in ("error",):
                raise RuntimeError(f"WhatsApp send failed: {wa.get('detail', 'unknown')}")
            provider_ids.append(str(wa.get("response", {}).get("messages", [{}])[0].get("id", "")))

        if channel in ("sms", "both"):
            sms_provider = get_sms_provider()
            sms = await asyncio.to_thread(sms_provider.send_sms, phone, campaign.message)
            if not sms.get("success"):
                raise RuntimeError(f"SMS send failed: {sms.get('error', 'unknown')}")
            provider_ids.append(str(sms.get("message_id", "")))

        return "sent", ",".join(pid for pid in provider_ids if pid)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Campaign %s delivery to %s failed: %s", campaign.id, phone, exc
        )
        return "failed", str(exc)


@router.post("/", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
def create_campaign(
    payload: CampaignCreate,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_permission("manage_campaigns")),
    db: Session = Depends(get_db),
) -> CampaignOut:
    """Create a campaign for the current business.

    Tenant isolation: ``business_id`` comes from the active membership
    resolved from the ``X-Business-ID`` header — never from the payload.
    """
    user, _, business = ctx
    campaign = Campaign(
        business_id=business.id,
        name=payload.name,
        channel=payload.channel,
        audience=json.dumps(payload.audience or {}),
        message=payload.message,
        language=payload.language,
        schedule_at=payload.schedule_at,
        status="draft",
        created_by=user.id,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return CampaignOut.model_validate(campaign)


@router.get("/", response_model=CampaignList)
def list_campaigns(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> CampaignList:
    """List campaigns for the current business, newest first."""
    _, _, business = ctx
    query = db.query(Campaign).filter(Campaign.business_id == business.id)

    total = query.count()
    campaigns = (
        query.order_by(Campaign.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [CampaignOut.model_validate(c) for c in campaigns]
    return CampaignList(items=items, total=total)


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(
    campaign_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> CampaignOut:
    """Return a campaign only if it belongs to the current business."""
    _, _, business = ctx
    campaign = _get_campaign_or_404(db, business.id, campaign_id)
    return CampaignOut.model_validate(campaign)


async def run_campaign_execution(
    db: Session,
    campaign: Campaign,
    user_id: Optional[int] = None,
) -> Optional[CampaignExecuteOut]:
    """Execute a campaign's delivery. Returns None if it's already done.

    Shared by the ``POST /campaigns/{id}/execute`` endpoint and the
    background scheduler (for ``Campaign.schedule_at``). Best-effort
    delivery: one bad recipient never aborts the whole run.
    """
    if campaign.status in ("completed", "running"):
        return None

    audience = _parse_audience(campaign.audience)
    customers = _match_customers(db, campaign.business_id, audience)

    campaign.status = "running"
    if user_id is not None:
        campaign.approved = True
        campaign.approved_by = user_id
        campaign.approved_at = utcnow()
    db.commit()

    sent = 0
    failed = 0
    recipients: List[CampaignRecipient] = []

    for customer in customers:
        phone = customer.phone.strip()
        recipients.append(
            CampaignRecipient(
                campaign_id=campaign.id,
                customer_id=customer.id,
                phone=phone,
                status="pending",
            )
        )

    db.add_all(recipients)
    db.commit()

    # Deliver best-effort; each recipient is reloaded before being updated.
    for recipient in recipients:
        try:
            current = db.get(CampaignRecipient, recipient.id)
            if current is None:
                continue
            delivery_status, provider_detail = await _deliver_one(
                campaign, current.phone
            )
            current.status = delivery_status
            if delivery_status == "sent":
                current.provider_message_id = provider_detail
                current.sent_at = utcnow()
                sent += 1
            else:
                current.error = provider_detail
                failed += 1
            db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Campaign %s recipient update failed: %s",
                campaign.id,
                exc,
            )
            failed += 1

    campaign.status = "completed" if customers else "failed"
    db.commit()
    db.refresh(campaign)

    return CampaignExecuteOut(
        campaign_id=campaign.id,
        total=len(customers),
        sent=sent,
        failed=failed,
        status=campaign.status,
    )


@router.post("/{campaign_id}/execute", response_model=CampaignExecuteOut)
async def execute_campaign(
    campaign_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_permission("manage_campaigns")),
    db: Session = Depends(get_db),
) -> CampaignExecuteOut:
    """Execute a campaign: send its message to matching customers.

    Steps:
      1. Load the campaign (tenant-scoped) and refuse to re-run a completed one.
      2. Resolve the audience filters against the business's customers.
      3. For each match create a :class:`CampaignRecipient` row and deliver the
         message via the WhatsApp and/or SMS provider.
      4. Mark the campaign ``completed`` (or ``failed`` if nothing was sent).

    Delivery is sequential and best-effort: one bad recipient never aborts the
    whole run.  Strict tenant isolation: only customers of the current business
    are ever targeted.
    """
    user, _, business = ctx
    campaign = _get_campaign_or_404(db, business.id, campaign_id)

    result = await run_campaign_execution(db, campaign, user_id=user.id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Campaign is already {campaign.status}",
        )
    return result


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_owner),
    db: Session = Depends(get_db),
) -> None:
    """Delete a campaign. Owner-only (or platform admin). Audited."""
    from app.services.audit_service import log_audit

    user, _, business = ctx
    campaign = _get_campaign_or_404(db, business.id, campaign_id)

    campaign_name = campaign.name
    db.delete(campaign)
    db.commit()

    log_audit(
        db,
        user_id=user.id,
        business_id=business.id,
        action="campaign.deleted",
        resource_type="campaign",
        resource_id=str(campaign_id),
        details=f"Deleted campaign '{campaign_name}'",
    )