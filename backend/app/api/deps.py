"""Shared FastAPI dependencies: auth, tenant isolation, RBAC."""
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.business import Business
from app.models.user import BusinessUser, Role, User

bearer_scheme = HTTPBearer(auto_error=False)

# Permission keys used across the platform.
PERMISSIONS = {
    "view_customers",
    "manage_customers",
    "view_conversations",
    "reply_conversations",
    "manage_products",
    "manage_campaigns",
    "manage_automations",
    "view_analytics",
    "manage_leads",
    "assign_leads",
    "takeover_conversations",
    "manage_staff",
    "manage_settings",
    "manage_ai",
    "manage_knowledge",
    "manage_whatsapp",
    "manage_sms",
}

# Owner gets every permission.
OWNER_PERMISSIONS = set(PERMISSIONS)

# Role names recognized by RBAC helpers.
OWNER_ROLE = "owner"
ADMIN_ROLE = "admin"
STAFF_ROLE = "staff"


def _role_belongs_to_platform(role: Role) -> bool:
    """Platform admins / owner role grants full access."""
    return role.name in {OWNER_ROLE, ADMIN_ROLE}


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def get_user_membership(
    db: Session, user_id: int, business_id: int
) -> Optional[BusinessUser]:
    """Return the active membership for a user in a business, if any."""
    return (
        db.query(BusinessUser)
        .filter(
            BusinessUser.user_id == user_id,
            BusinessUser.business_id == business_id,
            BusinessUser.is_active.is_(True),
        )
        .first()
    )


def get_current_business_user(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> tuple[User, BusinessUser, Business]:
    """Resolve the user's active business membership.

    The active business is the first active membership. This keeps tenant
    isolation simple: every tenant-scoped route uses this dependency.
    """
    membership = (
        db.query(BusinessUser)
        .filter(
            BusinessUser.user_id == user.id,
            BusinessUser.is_active.is_(True),
        )
        .first()
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No business membership found",
        )
    business = db.get(Business, membership.business_id)
    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    if business.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business is suspended",
        )
    return user, membership, business


def get_current_business(
    x_business_id: Optional[str] = Header(default=None, alias="X-Business-ID"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Business:
    """Resolve the business selected by the client (X-Business-ID header).

    The user MUST be a member of that business or a 403 is raised.
    This is the primary multi-tenant guard for tenant-scoped routes.
    """
    if not x_business_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Business-ID header is required",
        )
    try:
        business_id = int(x_business_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Business-ID must be an integer",
        )
    membership = get_user_membership(db, user.id, business_id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this business",
        )
    business = db.get(Business, business_id)
    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    if business.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business is suspended",
        )
    return business


def _current_membership(
    user: User, business: Business, db: Session
) -> BusinessUser:
    """Internal helper: fetch the user's membership for a business or 403."""
    membership = get_user_membership(db, user.id, business.id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this business",
        )
    return membership


def get_business_for_current_user(
    business_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Business:
    """Return a business only if the current user is an active member.

    Raises 403 if the user is not a member (never leaks existence).
    This is the core tenant-isolation guard for path-param routes.
    """
    membership = get_user_membership(db, user.id, business_id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this business",
        )
    business = db.get(Business, business_id)
    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    if business.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business is suspended",
        )
    return business


def require_membership(
    business: Business = Depends(get_current_business),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> tuple[User, BusinessUser, Business]:
    """A tenant-scoped context: user, membership, business.

    Verifies the user belongs to the business selected via X-Business-ID.
    """
    membership = _current_membership(user, business, db)
    return user, membership, business


def require_business_owner(
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
) -> tuple[User, BusinessUser, Business]:
    """Allow only owners (and platform admins) of the active business."""
    user, membership, business = ctx
    if user.is_platform_admin:
        return ctx
    if membership.role.name != OWNER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required",
        )
    return ctx


def require_business_staff_or_owner(
    ctx: tuple[User, BusinessUser, Business] = Depends(require_membership),
) -> tuple[User, BusinessUser, Business]:
    """Allow owners, admins and staff of the active business."""
    user, membership, business = ctx
    if user.is_platform_admin:
        return ctx
    if membership.role.name not in {OWNER_ROLE, ADMIN_ROLE, STAFF_ROLE}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff or owner access required",
        )
    return ctx


def require_permission(permission: str):
    """Dependency factory that checks a permission on the active membership."""

    def checker(
        ctx: tuple[User, BusinessUser, Business] = Depends(get_current_business_user),
    ) -> tuple[User, BusinessUser, Business]:
        _, membership, _ = ctx
        role = membership.role
        if role.name == OWNER_ROLE:
            return ctx
        perms = {p.strip() for p in membership.permissions.split(",") if p.strip()}
        if permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return ctx

    return checker


def require_platform_admin(
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access required",
        )
    return user