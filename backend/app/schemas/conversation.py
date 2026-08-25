"""Conversation and message schemas."""
from pydantic import BaseModel


class ConversationOut(BaseModel):
    id: int
    business_id: int
    customer_id: int
    channel: str
    mode: str
    language: str
    lead_status: str
    assigned_staff_id: int | None
    last_message: str
    last_activity: object | None = None
    is_unread: bool
    created_at: object | None = None

    model_config = {"from_attributes": True}


class ConversationList(BaseModel):
    items: list[ConversationOut]
    total: int
    page: int
    page_size: int


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    direction: str
    channel: str
    sender: str
    body: str
    message_type: str
    language: str
    intent: str
    intent_confidence: float
    transcription: str
    status: str
    is_ai_generated: bool
    ai_failed: bool
    created_at: object | None = None

    model_config = {"from_attributes": True}


class MessageList(BaseModel):
    items: list[MessageOut]
    total: int


class TakeoverRequest(BaseModel):
    staff_id: int | None = None


class SendMessageRequest(BaseModel):
    body: str
    message_type: str = "text"