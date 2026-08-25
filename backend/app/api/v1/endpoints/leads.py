"""Lead endpoints (tenant-scoped CRUD)."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    require_business_owner,
    require_business_staff_or_owner,
    require_membership,
)
from app.core.database import get_db
from app.models.business import Business
from app.models.customer import Customer
from app.models.lead import Lead
from app.models.user import BusinessUser, User
from app.schemas.common import PaginatedResponse
from app.schemas.lead import LeadCreate, LeadOut, LeadUpdate
from app.services.workflow_engine import trigger_automations

router = APIRouter(prefix="/leads", tags=["leads"])

logger = logging.getLogger(__name__)


def _lead_phone(db: Session, business_id: int, customer_id: int) -> str:
    """Look up the phone number of a lead's customer within the business."""
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.business_id == business_id)
        .first()
    )
    return customer.phone if customer else ""


def _get_lead_or_404(db: Session, business_id: int, lead_id: int) -> Lead:
    """Fetch a lead that belongs to the given business or raise 404."""
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.business_id == business_id)
        .first()
    )
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    return lead


def _validate_customer_in_business(
    db: Session, business_id: int, customer_id: int
) -> None:
    """Ensure the customer belongs to the current business."""
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.business_id == business_id)
        .first()
    )
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer does not belong to this business",
        )


@router.get("/", response_model=PaginatedResponse[LeadOut])
def list_leads(
    stage: str | None = Query(default=None, description="Filter by stage"),
    customer_id: int | None = Query(default=None, description="Filter by customer"),
    assigned_staff_id: int | None = Query(
        default=None, description="Filter by assigned staff"
    ),
    source: str | None = Query(default=None, description="Filter by source"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> PaginatedResponse[LeadOut]:
    """List leads for the current business only."""
    _, _, business = ctx
    query = db.query(Lead).filter(Lead.business_id == business.id)

    if stage:
        query = query.filter(Lead.stage == stage.strip().lower())
    if customer_id:
        query = query.filter(Lead.customer_id == customer_id)
    if assigned_staff_id:
        query = query.filter(Lead.assigned_staff_id == assigned_staff_id)
    if source:
        query = query.filter(Lead.source == source)

    total = query.count()
    leads = (
        query.order_by(Lead.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedResponse[LeadOut](
        items=[LeadOut.model_validate(l) for l in leads],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/",
    response_model=LeadOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_lead(
    payload: LeadCreate,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_staff_or_owner),
    db: Session = Depends(get_db),
) -> LeadOut:
    """Create a lead in the current business."""
    _, _, business = ctx
    _validate_customer_in_business(db, business.id, payload.customer_id)

    lead = Lead(
        business_id=business.id,
        customer_id=payload.customer_id,
        stage=payload.stage,
        source=payload.source,
        product_id=payload.product_id,
        estimated_value=payload.estimated_value,
        currency=payload.currency,
        notes=payload.notes,
        assigned_staff_id=payload.assigned_staff_id,
        next_follow_up=payload.next_follow_up,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    # Fire any active new_lead_created automations (best-effort).
    try:
        await trigger_automations(
            business.id,
            "new_lead_created",
            {
                "lead_id": lead.id,
                "customer_id": lead.customer_id,
                "phone": _lead_phone(db, business.id, lead.customer_id),
                "business_id": business.id,
            },
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to fire new_lead_created automations")

    return LeadOut.model_validate(lead)


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(
    lead_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> LeadOut:
    """Return a single lead if it belongs to the current business."""
    _, _, business = ctx
    lead = _get_lead_or_404(db, business.id, lead_id)
    return LeadOut.model_validate(lead)


@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_staff_or_owner),
    db: Session = Depends(get_db),
) -> LeadOut:
    """Update a lead (including moving its stage)."""
    _, _, business = ctx
    lead = _get_lead_or_404(db, business.id, lead_id)

    data = payload.model_dump(exclude_unset=True)
    if "customer_id" in data and data["customer_id"] is not None:
        _validate_customer_in_business(db, business.id, data["customer_id"])
    for field, value in data.items():
        if value is not None:
            setattr(lead, field, value)

    db.commit()
    db.refresh(lead)
    return LeadOut.model_validate(lead)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    lead_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_owner),
    db: Session = Depends(get_db),
) -> None:
    """Delete a lead. Owner-only."""
    _, _, business = ctx
    lead = _get_lead_or_404(db, business.id, lead_id)
    db.delete(lead)
    db.commit()