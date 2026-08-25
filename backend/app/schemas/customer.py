"""Customer schemas."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

ALLOWED_LANGUAGES = {"en", "ha", "ha-en"}


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=50)
    email: EmailStr | None = None
    preferred_language: str = Field(default="en", pattern="^(en|ha|ha-en)$")
    tags: list[str] = []
    source: str = ""
    notes: str = ""
    lead_status: str = "new"

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, v: list[str]) -> list[str]:
        return [t.strip() for t in v if t.strip()]


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = None
    preferred_language: str | None = Field(default=None, pattern="^(en|ha|ha-en)$")
    tags: list[str] | None = None
    source: str | None = None
    notes: str | None = None
    lead_status: str | None = None

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        return [t.strip() for t in v if t.strip()]


class CustomerOut(BaseModel):
    id: int
    business_id: int
    name: str
    phone: str
    email: str
    preferred_language: str
    tags: list[str] = []
    source: str
    notes: str
    lead_status: str
    last_interaction: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}