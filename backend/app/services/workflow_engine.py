"""Workflow engine: Zapier-style automation execution (V1)."""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.automation import Automation, AutomationRun, AutomationStep
from app.models.customer import Customer
from app.services.sms import get_sms_provider
from app.services.whatsapp import get_whatsapp_provider

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _step_config(step: AutomationStep) -> Dict[str, Any]:
    """Parse a step's JSON config column into a dict (safe fallback {})."""
    try:
        parsed = json.loads(step.config or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, TypeError):
        return {}


async def _send_whatsapp(phone: str, message: str) -> Dict[str, Any]:
    """Send a WhatsApp message via the configured provider."""
    provider = get_whatsapp_provider()
    # Provider.send_message is synchronous; do NOT await its result.
    return await asyncio.to_thread(provider.send_message, phone, message)


async def _send_sms(phone: str, message: str) -> Dict[str, Any]:
    """Send an SMS via the configured provider."""
    provider = get_sms_provider()
    return await asyncio.to_thread(provider.send_sms, phone, message)


def _apply_tag(db: Session, business_id: int, phone: str, tag: str) -> str:
    """Append a comma-separated tag to a customer (matched by phone)."""
    customer = (
        db.query(Customer)
        .filter(Customer.business_id == business_id, Customer.phone == phone)
        .first()
    )
    if customer is None:
        return "no customer found for add_tag"
    existing = [t.strip() for t in customer.tags.split(",") if t.strip()]
    if tag and tag.strip() not in existing:
        existing.append(tag.strip())
    customer.tags = ",".join(existing)
    db.commit()
    return "ok"


async def _run_step(
    db: Session, step: AutomationStep, context: Dict[str, Any], run: AutomationRun
) -> None:
    """Execute a single step; raises on hard failure."""
    step_type = step.step_type
    action_type = step.action_type or ""
    config = _step_config(step)
    phone = context.get("phone") or config.get("to") or ""
    message = (
        context.get("message")
        or context.get("text")
        or config.get("message")
        or ""
    )

    if step_type == "delay" or action_type == "wait_delay":
        seconds = float(config.get("seconds", 0))
        if config.get("hours"):
            seconds = float(config["hours"]) * 3600
        run.status = "waiting"
        db.commit()
        await asyncio.sleep(seconds)
        run.status = "running"
        return

    if step_type == "condition":
        # V1 conditions always pass (simple workflow engine).
        return

    if step_type == "action":
        if action_type == "send_whatsapp":
            if not phone:
                raise ValueError("send_whatsapp requires a phone number")
            await _send_whatsapp(phone, message)
        elif action_type == "send_sms":
            if not phone:
                raise ValueError("send_sms requires a phone number")
            await _send_sms(phone, message)
        elif action_type == "add_tag":
            tag = config.get("tag") or (config.get("tags") or [""])[0]
            if not tag:
                raise ValueError("add_tag requires a tag")
            detail = _apply_tag(db, context.get("business_id"), phone, tag)
            if detail != "ok":
                logger.info("add_tag skipped: %s", detail)
        else:
            logger.warning("Unsupported automation action_type=%s", action_type)


async def execute_automation(
    automation_id: int,
    context_data: Dict[str, Any],
    db: Optional[Session] = None,
) -> Optional[int]:
    """Execute an automation's steps in order. Returns the AutomationRun id.

    When ``db`` is omitted a fresh session is opened (and closed) by this
    function, so callers from webhooks / the scheduler never share sessions
    across async boundaries.
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()

    run = None
    try:
        automation = db.get(Automation, automation_id)
        if automation is None:
            logger.warning("Automation %s not found", automation_id)
            return None

        steps = (
            db.query(AutomationStep)
            .filter(
                AutomationStep.automation_id == automation_id,
                AutomationStep.is_enabled.is_(True),
            )
            .order_by(AutomationStep.position.asc())
            .all()
        )

        context = dict(context_data or {})
        context.setdefault("business_id", automation.business_id)

        run = AutomationRun(
            business_id=automation.business_id,
            automation_id=automation.id,
            trigger_event=automation.trigger_type,
            context=json.dumps(context),
            status="running",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        for index, step in enumerate(steps):
            run.current_step = index
            db.commit()
            await _run_step(db, step, context, run)

        run.status = "completed"
        db.commit()
        return run.id
    except Exception as exc:  # noqa: BLE001
        logger.exception("Automation %s run failed", automation_id)
        if run is not None:
            run.status = "failed"
            run.error = str(exc)[:200]
            db.commit()
        return run.id if run else None
    finally:
        if own_session:
            db.close()


async def trigger_automations(
    business_id: int,
    trigger_type: str,
    context_data: Dict[str, Any],
    db: Optional[Session] = None,
) -> int:
    """Fire active automations matching a trigger, each on a background task."""
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        automations = (
            db.query(Automation)
            .filter(
                Automation.business_id == business_id,
                Automation.trigger_type == trigger_type,
                Automation.is_active.is_(True),
            )
            .all()
        )
    finally:
        if own_session:
            db.close()

    for automation in automations:
        # Fire-and-forget: never block the webhook / request path.
        try:
            asyncio.create_task(execute_automation(automation.id, context_data))
        except RuntimeError:
            # No running event loop (e.g. tests): run inline.
            await execute_automation(automation.id, context_data)
    return len(automations)


# --------------------------------------------------------------------------- #
# Legacy workflow helpers (kept for backwards compatibility)
# --------------------------------------------------------------------------- #
def _post_to_webhook(webhook_url: str, data: Dict[str, Any]) -> None:
    """Synchronous HTTP POST to a webhook URL.

    Used with asyncio.to_thread to avoid blocking the event loop.
    """
    import httpx

    try:
        with httpx.Client(timeout=10) as client:
            client.post(
                webhook_url,
                json=data,
                headers={"Content-Type": "application/json"},
            )
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to post to webhook %s: %s", webhook_url, e)


async def trigger_workflow_actions(
    tenant_id: int, event_type: str, payload: Dict[str, Any]
) -> None:
    """Trigger Zapier-like workflow actions asynchronously (external hooks)."""
    phone = payload.get("phone", "")
    text = payload.get("text", "")
    msg_type = payload.get("type", "")

    event_data: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "event_type": event_type,
        "phone": phone,
        "text": text,
        "type": msg_type,
        "payload": payload,
    }

    import os

    webhook_url = os.getenv("WORKFLOW_WEBHOOK_URL")
    if webhook_url:
        try:
            await asyncio.to_thread(_post_to_webhook, webhook_url, event_data)
        except Exception as e:  # noqa: BLE001
            logger.warning("Workflow webhook error: %s", e)


async def send_whatsapp_message(to_number: str, message: str) -> Dict[str, Any]:
    """Send a WhatsApp message via the configured provider."""
    provider = get_whatsapp_provider()
    return provider.send_message(to_number, message)