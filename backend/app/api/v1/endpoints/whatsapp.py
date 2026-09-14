"""WhatsApp bulk-broadcast API (accounts, templates, broadcasts, messages).

Every query in this module is tenant-scoped: the ``business`` in the context
tuple comes from the ``X-Business-ID`` header plus the user's active
membership (see app.api.deps).  Client-supplied ids (account / template /
customer) are always cross-checked against the resolved business so tenant A
can never reference tenant B's resources.
"""
import asyncio
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    require_business_owner,
    require_membership,
    require_permission,
)
from app.core.database import get_db
from app.models.business import Business
from app.models.customer import Customer
from app.models.user import BusinessUser, User
from app.models.whatsapp import (
    WhatsAppAccount,
    WhatsAppCampaign,
    WhatsAppEngagement,
    WhatsAppMessage,
    WhatsAppRecipient,
    WhatsAppTemplate,
)
from app.schemas.common import PaginatedResponse
from app.schemas.whatsapp import (
    BroadcastPauseRequest,
    BroadcastStatsResponse,
    RecipientResponse,
    WhatsAppAccountCreate,
    WhatsAppAccountResponse,
    WhatsAppAccountUpdate,
    WhatsAppBroadcastCreate,
    WhatsAppBroadcastResponse,
    WhatsAppMessageResponse,
    WhatsAppSendRequest,
    WhatsAppSendResponse,
    WhatsAppTemplateCreate,
    WhatsAppTemplateResponse,
)
from app.services.whatsapp import get_provider_for_account
from app.services.whatsapp.broadcast import (
    ensure_utc,
    normalise_recipient_phone,
    send_broadcast_task,
)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_testing() -> bool:
    """Return True when running under pytest (background tasks go inline)."""
    return "pytest" in sys.modules


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _get_account_or_404(
    db: Session, business_id: int, account_id: int
) -> WhatsAppAccount:
    account = (
        db.query(WhatsAppAccount)
        .filter(
            WhatsAppAccount.id == account_id,
            WhatsAppAccount.business_id == business_id,
        )
        .first()
    )
    if account is None:
        raise HTTPException(status_code=404, detail="WhatsApp account not found")
    return account


def _get_template_or_404(
    db: Session, business_id: int, template_id: int
) -> WhatsAppTemplate:
    template = (
        db.query(WhatsAppTemplate)
        .filter(
            WhatsAppTemplate.id == template_id,
            WhatsAppTemplate.business_id == business_id,
        )
        .first()
    )
    if template is None:
        raise HTTPException(status_code=404, detail="WhatsApp template not found")
    return template


def _get_broadcast_or_404(
    db: Session, business_id: int, campaign_id: int
) -> WhatsAppCampaign:
    campaign = (
        db.query(WhatsAppCampaign)
        .filter(
            WhatsAppCampaign.id == campaign_id,
            WhatsAppCampaign.business_id == business_id,
        )
        .first()
    )
    if campaign is None:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    return campaign


def _launch_send(campaign: WhatsAppCampaign) -> None:
    """Start the background sender for a campaign.

    The task opens its own database session inside ``send_broadcast_task``, so
    it is safe to fire-and-forget without borrowing the request's session.
    """
    asyncio.create_task(send_broadcast_task(campaign.id, campaign.business_id))
# --------------------------------------------------------------------------- #
# Accounts
# --------------------------------------------------------------------------- #
@router.get("/accounts", response_model=List[WhatsAppAccountResponse])
def list_accounts(
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> List[WhatsAppAccountResponse]:
    """List the current business's connected WhatsApp accounts."""
    _, _, business = ctx
    accounts = (
        db.query(WhatsAppAccount)
        .filter(WhatsAppAccount.business_id == business.id)
        .order_by(WhatsAppAccount.id.desc())
        .all()
    )
    return [WhatsAppAccountResponse.model_validate(a) for a in accounts]


@router.post(
    "/accounts",
    response_model=WhatsAppAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_account(
    payload: WhatsAppAccountCreate,
    ctx: tuple[User, BusinessUser, Business] = Depends(
        require_permission("manage_whatsapp")
    ),
    db: Session = Depends(get_db),
) -> WhatsAppAccountResponse:
    """Connect a WhatsApp Business account for the current business.

    The ``api_key`` (Meta long-lived access token) is encrypted at rest via
    Fernet before it is stored and is never returned in any response.
    """
    _, _, business = ctx
    account = WhatsAppAccount(
        business_id=business.id,
        phone_number=payload.phone_number,
        api_key=payload.api_key,
        account_name=payload.account_name,
        phone_number_id=payload.phone_number_id or "",
        business_account_id=payload.business_account_id or "",
        display_name=payload.display_name or "",
        is_connected=bool(payload.phone_number_id),
        rate_limit_per_hour=payload.rate_limit_per_hour or 1000,
        status="active",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return WhatsAppAccountResponse.model_validate(account)


@router.patch("/accounts/{account_id}", response_model=WhatsAppAccountResponse)
def update_account(
    account_id: int,
    payload: WhatsAppAccountUpdate,
    ctx: tuple[User, BusinessUser, Business] = Depends(
        require_permission("manage_whatsapp")
    ),
    db: Session = Depends(get_db),
) -> WhatsAppAccountResponse:
    """Update a WhatsApp account (name, status, rate limit, IDs)."""
    _, _, business = ctx
    account = _get_account_or_404(db, business.id, account_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("phone_number_id"):
        data["is_connected"] = True
    for field, value in data.items():
        if value is not None:
            setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return WhatsAppAccountResponse.model_validate(account)


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_owner),
    db: Session = Depends(get_db),
) -> None:
    """Delete an account. Owner-only."""
    _, _, business = ctx
    account = _get_account_or_404(db, business.id, account_id)
    db.delete(account)
    db.commit()
# --------------------------------------------------------------------------- #
# Templates
# --------------------------------------------------------------------------- #
@router.get("/templates", response_model=PaginatedResponse[WhatsAppTemplateResponse])
def list_templates(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    category: Optional[str] = Query(default=None),
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> PaginatedResponse[WhatsAppTemplateResponse]:
    """List the current business's WhatsApp templates."""
    _, _, business = ctx
    query = db.query(WhatsAppTemplate).filter(
        WhatsAppTemplate.business_id == business.id
    )
    if category:
        query = query.filter(WhatsAppTemplate.category == category)
    total = query.count()
    templates = (
        query.order_by(WhatsAppTemplate.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedResponse[WhatsAppTemplateResponse](
        items=[WhatsAppTemplateResponse.model_validate(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/templates",
    response_model=WhatsAppTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_template(
    payload: WhatsAppTemplateCreate,
    ctx: tuple[User, BusinessUser, Business] = Depends(
        require_permission("manage_whatsapp")
    ),
    db: Session = Depends(get_db),
) -> WhatsAppTemplateResponse:
    """Create a WhatsApp message template with variable placeholders."""
    _, _, business = ctx
    template = WhatsAppTemplate(
        business_id=business.id,
        template_name=payload.template_name,
        template_text=payload.template_text,
        variables=payload.variables,
        category=payload.category,
        status="approved" if payload.category == "marketing" else "pending",
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return WhatsAppTemplateResponse.model_validate(template)


@router.patch("/templates/{template_id}", response_model=WhatsAppTemplateResponse)
def update_template(
    template_id: int,
    payload: WhatsAppTemplateCreate,
    ctx: tuple[User, BusinessUser, Business] = Depends(
        require_permission("manage_whatsapp")
    ),
    db: Session = Depends(get_db),
) -> WhatsAppTemplateResponse:
    """Update a template (name, body, variables, category)."""
    _, _, business = ctx
    template = _get_template_or_404(db, business.id, template_id)
    template.template_name = payload.template_name
    template.template_text = payload.template_text
    template.variables = payload.variables
    template.category = payload.category
    db.commit()
    db.refresh(template)
    return WhatsAppTemplateResponse.model_validate(template)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_owner),
    db: Session = Depends(get_db),
) -> None:
    """Delete a template. Owner-only."""
    _, _, business = ctx
    template = _get_template_or_404(db, business.id, template_id)
    db.delete(template)
    db.commit()
# --------------------------------------------------------------------------- #
# Broadcasts
# --------------------------------------------------------------------------- #
@router.get("/broadcasts", response_model=PaginatedResponse[WhatsAppBroadcastResponse])
def list_broadcasts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    campaign_status: Optional[str] = Query(default=None, alias="status"),
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> PaginatedResponse[WhatsAppBroadcastResponse]:
    """List the current business's broadcasts, newest first."""
    _, _, business = ctx
    query = db.query(WhatsAppCampaign).filter(
        WhatsAppCampaign.business_id == business.id
    )
    if campaign_status:
        query = query.filter(WhatsAppCampaign.status == campaign_status)
    total = query.count()
    campaigns = (
        query.order_by(WhatsAppCampaign.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedResponse[WhatsAppBroadcastResponse](
        items=[WhatsAppBroadcastResponse.model_validate(c) for c in campaigns],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/broadcasts",
    response_model=WhatsAppBroadcastResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_broadcast(
    payload: WhatsAppBroadcastCreate,
    ctx: tuple[User, BusinessUser, Business] = Depends(
        require_permission("manage_whatsapp")
    ),
    db: Session = Depends(get_db),
) -> WhatsAppBroadcastResponse:
    """Create a broadcast campaign and persist its recipient rows.

    The campaign is ``draft`` (send now) or ``scheduled`` (scheduled_time in
    the future).  Recipients are either existing customer ids (verified to
    belong to the current business) or raw phone numbers.
    """
    _, _, business = ctx
    account = _get_account_or_404(db, business.id, payload.account_id)

    template = None
    if payload.template_id is not None:
        template = _get_template_or_404(db, business.id, payload.template_id)

    recipients_rows = []
    if payload.recipients:
        customer_ids = list(dict.fromkeys(payload.recipients))
        customers = (
            db.query(Customer)
            .filter(
                Customer.business_id == business.id,
                Customer.id.in_(customer_ids),
            )
            .all()
        )
        if len(customers) != len(customer_ids):
            raise HTTPException(
                status_code=400,
                detail="One or more recipients are not customers of your business",
            )
        for customer in customers:
            phone = normalise_recipient_phone(customer.phone)
            if not phone:
                raise HTTPException(
                    status_code=400,
                    detail=f"Customer '{customer.name}' has no valid phone number",
                )
            recipients_rows.append(
                WhatsAppRecipient(
                    customer_id=customer.id, phone_number=phone, status="pending"
                )
            )
    else:
        for raw in payload.phone_numbers or []:
            phone = normalise_recipient_phone(raw)
            if not phone:
                raise HTTPException(status_code=400, detail=f"Invalid phone number: {raw}")
            recipients_rows.append(
                WhatsAppRecipient(phone_number=phone, status="pending")
            )

    if not recipients_rows:
        raise HTTPException(status_code=400, detail="No valid recipients provided")

    campaign = WhatsAppCampaign(
        business_id=business.id,
        account_id=account.id,
        campaign_name=payload.campaign_name,
        template_id=template.id if template else None,
        message_text=payload.message_text or "",
        variables_map=payload.variables_map or {},
        scheduled_time=payload.scheduled_time,
        total_recipients=len(recipients_rows),
        status="scheduled" if payload.scheduled_time else "draft",
    )
    db.add(campaign)
    db.flush()
    for row in recipients_rows:
        row.campaign_id = campaign.id
    db.add_all(recipients_rows)
    db.commit()
    db.refresh(campaign)
    return WhatsAppBroadcastResponse.model_validate(campaign)
@router.get("/broadcasts/{campaign_id}", response_model=WhatsAppBroadcastResponse)
def get_broadcast(
    campaign_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> WhatsAppBroadcastResponse:
    """Return a broadcast if it belongs to the current business."""
    _, _, business = ctx
    campaign = _get_broadcast_or_404(db, business.id, campaign_id)
    return WhatsAppBroadcastResponse.model_validate(campaign)


@router.get(
    "/broadcasts/{campaign_id}/recipients",
    response_model=PaginatedResponse[RecipientResponse],
)
def list_recipients(
    campaign_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> PaginatedResponse[RecipientResponse]:
    """List the per-recipient delivery status of a broadcast."""
    _, _, business = ctx
    _get_broadcast_or_404(db, business.id, campaign_id)
    query = db.query(WhatsAppRecipient).filter(
        WhatsAppRecipient.campaign_id == campaign_id
    )
    total = query.count()
    rows = (
        query.order_by(WhatsAppRecipient.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedResponse[RecipientResponse](
        items=[RecipientResponse.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/broadcasts/{campaign_id}/stats", response_model=BroadcastStatsResponse)
def broadcast_stats(
    campaign_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> BroadcastStatsResponse:
    """Aggregated engagement metrics for a broadcast (tenant-scoped)."""
    _, _, business = ctx
    campaign = _get_broadcast_or_404(db, business.id, campaign_id)

    sent = campaign.sent_count or 0
    delivered = campaign.delivered_count or 0
    read_count = campaign.read_count or 0
    replied = campaign.reply_count or 0
    failed = campaign.failed_count or 0

    # Error summary from the failed recipient rows (grouped by first 60 chars).
    error_rows = (
        db.query(WhatsAppRecipient.error_message)
        .filter(
            WhatsAppRecipient.campaign_id == campaign.id,
            WhatsAppRecipient.status == "failed",
            WhatsAppRecipient.error_message != "",
        )
        .all()
    )
    error_summary: Dict[str, int] = {}
    for (message,) in error_rows:
        bucket = (str(message) or "unknown")[:60]
        error_summary[bucket] = error_summary.get(bucket, 0) + 1

    def _avg_seconds(event: str) -> int:
        rows = (
            db.query(WhatsAppEngagement.response_time_seconds)
            .filter(
                WhatsAppEngagement.business_id == business.id,
                WhatsAppEngagement.campaign_id == campaign.id,
                WhatsAppEngagement.event_type == event,
                WhatsAppEngagement.response_time_seconds.isnot(None),
            )
            .all()
        )
        times = [int(r[0]) for r in rows if r[0] is not None]
        return int(sum(times) / len(times)) if times else 0

    return BroadcastStatsResponse(
        total_sent=sent,
        delivery_rate=round((delivered / sent) * 100, 2) if sent else 0.0,
        read_rate=round((read_count / sent) * 100, 2) if sent else 0.0,
        reply_rate=round((replied / sent) * 100, 2) if sent else 0.0,
        failed_count=failed,
        error_summary=error_summary,
        avg_delivery_time_seconds=_avg_seconds("delivered"),
        avg_read_time_seconds=_avg_seconds("read"),
    )
@router.post("/broadcasts/{campaign_id}/start", response_model=WhatsAppBroadcastResponse)
def start_broadcast(
    campaign_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(
        require_permission("manage_whatsapp")
    ),
    db: Session = Depends(get_db),
) -> WhatsAppBroadcastResponse:
    """Start (or schedule) a broadcast.

    * Future ``scheduled_time`` → the campaign is marked ``scheduled`` and the
      background worker launches it when due.
    * Otherwise the campaign moves to ``sending`` and the sender task starts
      immediately (background, non-blocking).
    """
    _, _, business = ctx
    campaign = _get_broadcast_or_404(db, business.id, campaign_id)
    if campaign.status in ("completed", "sending"):
        raise HTTPException(
            status_code=400,
            detail=f"Broadcast is already {campaign.status}",
        )

    now = utcnow()
    scheduled = ensure_utc(campaign.scheduled_time)
    if scheduled and scheduled > now:
        campaign.status = "scheduled"
        db.commit()
        db.refresh(campaign)
        return WhatsAppBroadcastResponse.model_validate(campaign)

    campaign.status = "sending"
    campaign.started_at = now
    db.commit()

    if not _is_testing():
        _launch_send(campaign)

    db.refresh(campaign)
    return WhatsAppBroadcastResponse.model_validate(campaign)


@router.post("/broadcasts/{campaign_id}/pause", response_model=WhatsAppBroadcastResponse)
def pause_broadcast(
    campaign_id: int,
    payload: BroadcastPauseRequest,
    ctx: tuple[User, BusinessUser, Business] = Depends(
        require_permission("manage_whatsapp")
    ),
    db: Session = Depends(get_db),
) -> WhatsAppBroadcastResponse:
    """Pause a mid-send broadcast (or cancel a scheduled one).

    The sender task polls the campaign status between batches, so a pause is
    honoured without dropping the run — resume continues where it left off.
    """
    if payload.status != "paused":
        raise HTTPException(status_code=400, detail='Set status to "paused"')
    _, _, business = ctx
    campaign = _get_broadcast_or_404(db, business.id, campaign_id)
    if campaign.status not in ("sending", "scheduled"):
        raise HTTPException(
            status_code=400,
            detail=f"Broadcast is {campaign.status} and cannot be paused",
        )
    campaign.status = "paused"
    db.commit()
    db.refresh(campaign)
    return WhatsAppBroadcastResponse.model_validate(campaign)


@router.post("/broadcasts/{campaign_id}/resume", response_model=WhatsAppBroadcastResponse)
def resume_broadcast(
    campaign_id: int,
    payload: BroadcastPauseRequest,
    ctx: tuple[User, BusinessUser, Business] = Depends(
        require_permission("manage_whatsapp")
    ),
    db: Session = Depends(get_db),
) -> WhatsAppBroadcastResponse:
    """Resume a paused broadcast. Starts a fresh sender task if none is alive."""
    if payload.status != "resumed":
        raise HTTPException(status_code=400, detail='Set status to "resumed"')
    _, _, business = ctx
    campaign = _get_broadcast_or_404(db, business.id, campaign_id)
    if campaign.status != "paused":
        raise HTTPException(
            status_code=400,
            detail=f"Broadcast is {campaign.status} and cannot be resumed",
        )

    now = utcnow()
    scheduled = ensure_utc(campaign.scheduled_time)
    if scheduled and scheduled > now:
        campaign.status = "scheduled"
    else:
        campaign.status = "sending"
        if not campaign.started_at:
            campaign.started_at = now
    db.commit()

    if campaign.status == "sending" and not _is_testing():
        _launch_send(campaign)

    db.refresh(campaign)
    return WhatsAppBroadcastResponse.model_validate(campaign)


@router.delete("/broadcasts/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_broadcast(
    campaign_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_owner),
    db: Session = Depends(get_db),
) -> None:
    """Delete a broadcast. Owner-only. Refuses while it is actively sending."""
    _, _, business = ctx
    campaign = _get_broadcast_or_404(db, business.id, campaign_id)
    if campaign.status == "sending":
        raise HTTPException(
            status_code=409,
            detail="Pause the broadcast before deleting it",
        )
    db.delete(campaign)
    db.commit()
# --------------------------------------------------------------------------- #
# Messages
# --------------------------------------------------------------------------- #
@router.post("/messages", response_model=WhatsAppSendResponse)
async def send_message(
    payload: WhatsAppSendRequest,
    ctx: tuple[User, BusinessUser, Business] = Depends(
        require_permission("manage_whatsapp")
    ),
    db: Session = Depends(get_db),
) -> WhatsAppSendResponse:
    """Send a single (non-broadcast) WhatsApp message and persist it."""
    _, _, business = ctx
    account = _get_account_or_404(db, business.id, payload.account_id)
    if account.status != "active":
        raise HTTPException(status_code=400, detail="Account is not active")

    to_number = normalise_recipient_phone(payload.to_number)
    if not to_number:
        raise HTTPException(status_code=400, detail="Invalid recipient number")

    provider = get_provider_for_account(account)
    result = await asyncio.to_thread(
        provider.send_message, to_number, payload.message_text
    )
    success = result.get("status") == "sent"
    wamid = str(result.get("message_id", "") or "") if success else ""

    message = WhatsAppMessage(
        business_id=business.id,
        account_id=account.id,
        to_number=to_number,
        from_number=account.phone_number,
        message_text=payload.message_text,
        status="sent" if success else "failed",
        message_type="text",
        media_url=payload.media_url or "",
        provider_message_id=wamid,
        direction="outbound",
        error_message="" if success else str(result.get("detail", "")),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return WhatsAppSendResponse.model_validate(message)


@router.get("/messages", response_model=PaginatedResponse[WhatsAppMessageResponse])
def list_messages(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    direction: Optional[str] = Query(default=None, pattern="^(inbound|outbound)$"),
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> PaginatedResponse[WhatsAppMessageResponse]:
    """Recent WhatsApp messages for the current business (newest first)."""
    _, _, business = ctx
    query = db.query(WhatsAppMessage).filter(
        WhatsAppMessage.business_id == business.id
    )
    if direction:
        query = query.filter(WhatsAppMessage.direction == direction)
    total = query.count()
    rows = (
        query.order_by(WhatsAppMessage.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedResponse[WhatsAppMessageResponse](
        items=[WhatsAppMessageResponse.model_validate(m) for m in rows],
        total=total,
        page=page,
        page_size=page_size,
    )