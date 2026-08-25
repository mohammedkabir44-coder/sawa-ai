"""Business schemas."""
from pydantic import BaseModel, EmailStr, Field


class BusinessCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    business_type: str = ""
    description: str = ""
    location: str = ""
    phone: str = ""
    email: EmailStr | None = None
    website: str = ""
    primary_language: str = "en"


class BusinessUpdate(BaseModel):
    name: str | None = None
    business_type: str | None = None
    description: str | None = None
    location: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    website: str | None = None
    primary_language: str | None = None
    currency: str | None = None
    timezone: str | None = None


class BusinessOut(BaseModel):
    id: int
    name: str
    business_type: str
    description: str
    location: str
    phone: str
    email: str
    website: str
    primary_language: str
    currency: str
    timezone: str
    status: str
    onboarding_completed: bool
    created_at: object | None = None

    model_config = {"from_attributes": True}


class OnboardingStep1(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    business_type: str = ""
    description: str = ""
    location: str = ""
    phone: str = ""
    email: EmailStr | None = None
    website: str = ""


class OnboardingStep2(BaseModel):
    primary_language: str = Field(pattern="^(en|ha|ha-en)$")


class OnboardingComplete(BaseModel):
    message: str = "Your AI assistant is ready."