"""Authentication endpoints: register, login, me."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.business import Business
from app.models.user import BusinessUser, Role, User
from app.schemas.auth import (
    MeResponse,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.schemas.business import BusinessOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_roles(db: Session):
    """Fetch or create the three system roles."""
    names = ["owner", "admin", "staff"]
    roles = {}
    for name in names:
        role = db.scalar(select(Role).where(Role.name == name))
        if role is None:
            role = Role(name=name, is_system=True)
            db.add(role)
            db.flush()
        roles[name] = role
    return roles


def _create_owner_membership(
    db: Session, user: User, business: Business, roles: dict
) -> BusinessUser:
    """Create an owner membership for the given user/business."""
    owner_role = roles["owner"]
    membership = BusinessUser(
        user_id=user.id,
        business_id=business.id,
        role_id=owner_role.id,
        permissions="",
        is_active=True,
    )
    db.add(membership)
    return membership


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Register a new user. Optionally creates a business with owner role."""
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        is_active=True,
        is_platform_admin=False,
    )
    db.add(user)
    db.flush()

    if payload.business_name:
        roles = _get_roles(db)
        business = Business(name=payload.business_name)
        db.add(business)
        db.flush()
        _create_owner_membership(db, user, business, roles)

    db.commit()

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token, token_type="bearer")


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Login with email (as username) and password. Returns a JWT."""
    user = db.scalar(select(User).where(User.email == form_data.username))
    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token, token_type="bearer")


@router.get("/me", response_model=MeResponse)
def me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeResponse:
    """Return current user info plus all business memberships."""
    memberships = (
        db.query(BusinessUser)
        .filter(BusinessUser.user_id == user.id, BusinessUser.is_active.is_(True))
        .all()
    )

    membership_out = []
    for m in memberships:
        business = db.get(Business, m.business_id)
        if business is None:
            continue
        role = db.get(Role, m.role_id)
        membership_out.append(
            {
                "business": BusinessOut.model_validate(business),
                "role": role.name if role else "",
                "permissions": [p for p in m.permissions.split(",") if p],
            }
        )

    return MeResponse(
        user=UserOut.model_validate(user),
        memberships=membership_out,
    )