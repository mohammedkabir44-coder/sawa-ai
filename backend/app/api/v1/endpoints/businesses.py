"""Business (tenant) endpoints with full tenant isolation."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    get_business_for_current_user,
    get_current_user,
    get_user_membership,
)
from app.core.database import get_db
from app.models.business import Business
from app.models.user import BusinessUser, Role, User
from app.schemas.business import BusinessCreate, BusinessOut, BusinessUpdate

router = APIRouter(prefix="/businesses", tags=["businesses"])


def _get_owner_role(db: Session) -> Role:
    """Fetch or create the owner role."""
    role = db.scalar(select(Role).where(Role.name == "owner"))
    if role is None:
        role = Role(name="owner", is_system=True)
        db.add(role)
        db.flush()
    return role


def _ensure_business_owner(
    db: Session, user: User, business: Business, owner_role: Role
) -> BusinessUser:
    """Create an owner membership for the current user."""
    existing = get_user_membership(db, user.id, business.id)
    if existing is not None:
        return existing
    membership = BusinessUser(
        user_id=user.id,
        business_id=business.id,
        role_id=owner_role.id,
        permissions="",
        is_active=True,
    )
    db.add(membership)
    return membership


@router.post("/", response_model=BusinessOut, status_code=status.HTTP_201_CREATED)
def create_business(
    payload: BusinessCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BusinessOut:
    """Create a new business and make the current user its owner."""
    business = Business(
        name=payload.name,
        business_type=payload.business_type,
        description=payload.description,
        location=payload.location,
        phone=payload.phone,
        email=payload.email or "",
        website=payload.website,
        primary_language=payload.primary_language,
        currency="NGN",
        timezone="Africa/Lagos",
        status="active",
        onboarding_completed=False,
    )
    db.add(business)
    db.flush()

    owner_role = _get_owner_role(db)
    _ensure_business_owner(db, user, business, owner_role)
    db.commit()
    db.refresh(business)

    return BusinessOut.model_validate(business)


@router.get("/", response_model=list[BusinessOut])
def list_my_businesses(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BusinessOut]:
    """Return ONLY the businesses the current user belongs to."""
    memberships = (
        db.query(BusinessUser)
        .filter(BusinessUser.user_id == user.id, BusinessUser.is_active.is_(True))
        .all()
    )
    business_ids = [m.business_id for m in memberships]
    if not business_ids:
        return []
    businesses = db.query(Business).filter(Business.id.in_(business_ids)).all()
    return [BusinessOut.model_validate(b) for b in businesses]


@router.get("/{business_id}", response_model=BusinessOut)
def get_business(
    business: Business = Depends(get_business_for_current_user),
) -> BusinessOut:
    """Return a business only if the current user is a member."""
    return BusinessOut.model_validate(business)


@router.patch("/{business_id}", response_model=BusinessOut)
def update_business(
    business_id: int,
    payload: BusinessUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    business: Business = Depends(get_business_for_current_user),
) -> BusinessOut:
    """Update a business. Owner-only."""
    membership = db.query(BusinessUser).filter(
        BusinessUser.user_id == user.id,
        BusinessUser.business_id == business.id,
        BusinessUser.is_active.is_(True),
    ).first()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this business",
        )
    role = db.get(Role, membership.role_id)
    if role is None or role.name != "owner":
        if not user.is_platform_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner access required",
            )

    data = payload.model_dump(exclude_unset=True)
    changed = [k for k, v in data.items() if v is not None]
    for field, value in data.items():
        if value is not None:
            setattr(business, field, value)
    db.commit()
    db.refresh(business)

    from app.services.audit_service import log_audit

    log_audit(
        db,
        user_id=user.id,
        business_id=business.id,
        action="business.updated",
        resource_type="business",
        resource_id=str(business_id),
        details=f"Updated fields: {', '.join(changed) or 'none'}",
    )
    return BusinessOut.model_validate(business)