"""Auth and user schemas."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.business import BusinessOut


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    phone: str = ""
    business_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    """JSON login body (alternative to OAuth2 form)."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    phone: str = ""
    is_platform_admin: bool = False
    is_active: bool = True
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class BusinessMembershipOut(BaseModel):
    business: BusinessOut
    role: str
    permissions: list[str] = []


class MeResponse(BaseModel):
    user: UserOut
    memberships: list[BusinessMembershipOut]