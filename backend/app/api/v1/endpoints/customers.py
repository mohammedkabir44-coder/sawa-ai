"""Customer endpoints (tenant-scoped CRUD)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import (
    require_business_owner,
    require_business_staff_or_owner,
    require_membership,
)
from app.core.database import get_db
from app.models.business import Business
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.lead import Lead
from app.models.user import BusinessUser, User
from app.schemas.common import PaginatedResponse
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


def _tags_to_str(tags: list[str]) -> str:
    """Convert a list of tags to the comma-separated storage format."""
    return ",".join(t.strip() for t in tags if t.strip())


def _tags_from_str(tags: str) -> list[str]:
    """Convert the comma-separated storage format to a list."""
    return [t.strip() for t in tags.split(",") if t.strip()]


def _customer_out(customer: Customer) -> CustomerOut:
    """Build a CustomerOut with tags converted to a list."""
    return CustomerOut(
        id=customer.id,
        business_id=customer.business_id,
        name=customer.name,
        phone=customer.phone,
        email=customer.email,
        preferred_language=customer.preferred_language,
        tags=_tags_from_str(customer.tags),
        source=customer.source,
        notes=customer.notes,
        lead_status=customer.lead_status,
        last_interaction=customer.last_interaction,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
    )


def _get_customer_or_404(db: Session, business_id: int, customer_id: int) -> Customer:
    """Fetch a customer that belongs to the given business or raise 404."""
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.business_id == business_id)
        .first()
    )
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return customer


@router.get("/", response_model=PaginatedResponse[CustomerOut])
def list_customers(
    search: str | None = Query(default=None, description="Search by name or phone"),
    language: str | None = Query(default=None, description="Filter by preferred language"),
    source: str | None = Query(default=None, description="Filter by source"),
    lead_status: str | None = Query(default=None, description="Filter by lead status"),
    tag: str | None = Query(default=None, description="Filter by tag"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> PaginatedResponse[CustomerOut]:
    """List customers for the current business only."""
    _, _, business = ctx
    query = db.query(Customer).filter(Customer.business_id == business.id)

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(Customer.name.ilike(like), Customer.phone.ilike(like))
        )
    if language:
        query = query.filter(Customer.preferred_language == language)
    if source:
        query = query.filter(Customer.source == source)
    if lead_status:
        query = query.filter(Customer.lead_status == lead_status)
    if tag:
        query = query.filter(Customer.tags.ilike(f"%{tag}%"))

    total = query.count()
    customers = (
        query.order_by(Customer.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedResponse[CustomerOut](
        items=[_customer_out(c) for c in customers],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/",
    response_model=CustomerOut,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    payload: CustomerCreate,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_staff_or_owner),
    db: Session = Depends(get_db),
) -> CustomerOut:
    """Create a customer in the current business."""
    _, _, business = ctx
    customer = Customer(
        business_id=business.id,
        name=payload.name,
        phone=payload.phone,
        email=payload.email or "",
        preferred_language=payload.preferred_language,
        tags=_tags_to_str(payload.tags),
        source=payload.source,
        notes=payload.notes,
        lead_status=payload.lead_status,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return _customer_out(customer)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
    db: Session = Depends(get_db),
) -> CustomerOut:
    """Return a single customer if it belongs to the current business."""
    _, _, business = ctx
    customer = _get_customer_or_404(db, business.id, customer_id)
    return _customer_out(customer)


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_staff_or_owner),
    db: Session = Depends(get_db),
) -> CustomerOut:
    """Update allowed fields of a customer in the current business."""
    _, _, business = ctx
    customer = _get_customer_or_404(db, business.id, customer_id)

    data = payload.model_dump(exclude_unset=True)
    if "tags" in data and data["tags"] is not None:
        data["tags"] = _tags_to_str(data["tags"])
    for field, value in data.items():
        if value is not None:
            setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return _customer_out(customer)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int,
    ctx: tuple[User, BusinessUser, Business] = Depends(require_business_owner),
    db: Session = Depends(get_db),
) -> None:
    """Delete a customer. Owner-only.

    If the customer has leads or conversations, refuse with a clear message
    to avoid silently destroying related data.
    """
    _, _, business = ctx
    customer = _get_customer_or_404(db, business.id, customer_id)

    has_leads = (
        db.query(Lead)
        .filter(Lead.customer_id == customer_id, Lead.business_id == business.id)
        .first()
        is not None
    )
    has_conversations = (
        db.query(Conversation)
        .filter(
            Conversation.customer_id == customer_id,
            Conversation.business_id == business.id,
        )
        .first()
        is not None
    )
    if has_leads or has_conversations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Cannot delete customer with existing leads or conversations. "
                "Remove or reassign them first."
            ),
        )

    db.delete(customer)
    db.commit()