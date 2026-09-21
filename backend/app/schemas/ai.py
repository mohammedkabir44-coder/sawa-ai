"""AI-related schemas."""
from pydantic import BaseModel, Field


class AISettingsUpdate(BaseModel):
    assistant_name: str | None = None
    greeting_message: str | None = None
    auto_reply_enabled: bool | None = None
    language: str | None = None
    tone: str | None = None
    confidence_threshold: float | None = None
    handoff_on_low_confidence: bool | None = None


class AISettingsOut(BaseModel):
    id: int
    business_id: int
    assistant_name: str
    greeting_message: str
    auto_reply_enabled: bool
    language: str
    tone: str
    confidence_threshold: float
    handoff_on_low_confidence: bool

    model_config = {"from_attributes": True}


class KnowledgeCreate(BaseModel):
    category: str = "faq"
    title: str = ""
    content: str = Field(min_length=1)
    language: str = "en"


class KnowledgeUpdate(BaseModel):
    category: str | None = None
    title: str | None = None
    content: str | None = None
    language: str | None = None
    is_active: bool | None = None


class KnowledgeOut(BaseModel):
    id: int
    business_id: int
    category: str
    title: str
    content: str
    language: str
    is_active: bool
    created_at: object | None = None

    model_config = {"from_attributes": True}


class IntentResult(BaseModel):
    intent: str
    language: str
    confidence: float
    message: str = ""