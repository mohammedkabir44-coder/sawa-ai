"""Lead schemas."""
from datetime import datetime

from pydantic import BaseModel, field_validator

LEAD_STAGES = {"new", "contacted", "interested", "negotiating", "won", "lost"}


def _normalize_stage(value: str) -> str:
    """Normalize a stage value to lowercase and validate it."""
    normalized = value.strip().lower()
    if normalized not in LEAD_STAGES:
        raise ValueError(
            f"Invalid stage '{value}'. Allowed: {sorted(LEAD_STAGES)}"
        )
    return normalized


class LeadCreate(BaseModel):
    customer_id: int
    stage: str = "new"
    source: str = ""
    product_id: int | None = None
    estimated_value: float = 0.0
    currency: str = "NGN"
    notes: str = ""
    assigned_staff_id: int | None = None
    next_follow_up: datetime | None = None

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        return _normalize_stage(v)


class LeadUpdate(BaseModel):
    stage: str | None = None
    source: str | None = None
    product_id: int | None = None
    estimated_value: float | None = None
    currency: str | None = None
    notes: str | None = None
    assigned_staff_id: int | None = None
    next_follow_up: datetime | None = None

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _normalize_stage(v)


class LeadOut(BaseModel):
    id: int
    business_id: int
    customer_id: int
    source: str
    product_id: int | None
    estimated_value: float
    currency: str
    notes: str
    assigned_staff_id: int | None
    stage: str
    last_contact: datetime | None = None
    next_follow_up: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}