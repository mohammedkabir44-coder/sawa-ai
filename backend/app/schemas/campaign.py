"""Campaign schemas."""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

ALLOWED_CHANNELS = {"whatsapp", "sms", "both"}


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    channel: str = Field(default="whatsapp", pattern="^(whatsapp|sms|both)$")
    audience: dict = Field(default_factory=dict)  # {"all": True} | {"tags": ["VIP"]}
    message: str = Field(default="", max_length=4096)
    language: str = "en"
    schedule_at: datetime | None = None


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    channel: str | None = Field(default=None, pattern="^(whatsapp|sms|both)$")
    audience: dict | None = None
    message: str | None = Field(default=None, max_length=4096)
    language: str | None = None
    schedule_at: datetime | None = None
    status: str | None = None


class CampaignOut(BaseModel):
    id: int
    business_id: int
    name: str
    channel: str
    audience: dict = Field(default_factory=dict)
    message: str
    language: str
    schedule_at: datetime | None = None
    status: str
    is_ai_generated: bool
    ai_prompt: str
    approved: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

    @field_validator("audience", mode="before")
    @classmethod
    def _parse_audience(cls, v):
        """Accept either a dict or a JSON string (as stored on the model)."""
        if isinstance(v, str):
            import json

            try:
                parsed = json.loads(v or "{}")
                return parsed if isinstance(parsed, dict) else {}
            except (ValueError, TypeError):
                return {}
        return v or {}


class CampaignList(BaseModel):
    items: list[CampaignOut]
    total: int


class CampaignApprove(BaseModel):
    approved: bool = True


class CampaignExecuteOut(BaseModel):
    campaign_id: int
    total: int
    sent: int
    failed: int
    status: str


class AIGenerateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=2000)


class AIGenerateResponse(BaseModel):
    title: str
    message: str
    short_version: str
    english_version: str
    hausa_version: str