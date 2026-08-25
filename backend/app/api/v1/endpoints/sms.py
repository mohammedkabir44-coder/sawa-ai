"""SMS endpoints (tenant-scoped single send + history)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_business_staff_or_owner
from app.core.database import get_db
from app.models.business import Business
from app.models.sms import SMSMessage
from app.models.user import BusinessUser, User
from app.schemas.common import PaginatedResponse
from app.schemas.sms import SMSMessageOut, SMSSendRequest, SMSSendResponse
from app.services.sms import get_sms_provider

router = APIRouter(prefix="/sms", tags=["sms"])


@router.post("/send", response_model=SMSSendResponse)
def send_sms(
    payload: SMSSendRequest,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_staff_or_owner),
    db: Session = Depends(get_db),
) -> SMSSendResponse:
    """Send a single SMS to a phone number.

    Tenant isolation: the message is attributed to the current business
    (via ``X-Business-ID``), and the delivery history is stored under that
    same business.
    """
    _, _, business = ctx
    provider = get_sms_provider()
    result = provider.send_sms(to=payload.phone, body=payload.message)

    success = bool(result.get("success"))
    provider_name = result.get("provider", "mock")
    message_id = result.get("message_id", "")
    error_message = "" if success else str(result.get("error", result.get("detail", "")))

    # Persist a history record so GET /sms/history works.
    record = SMSMessage(
        business_id=business.id,
        to_phone=payload.phone,
        body=payload.message,
        provider=provider_name,
        status="sent" if success else "failed",
        provider_message_id=message_id,
        error_message=error_message,
    )
    db.add(record)
    db.commit()

    return SMSSendResponse(
        success=success,
        provider=provider_name,
        message_id=message_id,
        error=error_message,
    )


@router.get("/history", response_model=PaginatedResponse[SMSMessageOut])
def sms_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_staff_or_owner),
    db: Session = Depends(get_db),
) -> PaginatedResponse[SMSMessageOut]:
    """List sent SMS for the current business, paginated (newest first).

    Tenant isolation is enforced by filtering strictly on ``business_id``.
    """
    _, _, business = ctx
    query = db.query(SMSMessage).filter(SMSMessage.business_id == business.id)

    total = query.count()
    records = (
        query.order_by(SMSMessage.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [SMSMessageOut.model_validate(r) for r in records]
    return PaginatedResponse[SMSMessageOut](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )