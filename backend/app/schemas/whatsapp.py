"""WhatsApp Pydantic schemas with validation rules.

All schemas use Pydantic v2 syntax.  ``model_config = {"from_attributes": True}``
is set on every response schema so SQLAlchemy model instances can be returned
directly from the API layer.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

# Nigerian phone numbers must start with +234 followed by 10 digits.
_PHONE_RE = re.compile(r"^\+234\d{10}$")

# Allowed enum values.
_ACCOUNT_STATUS = {"active", "inactive"}
_TEMPLATE_CATEGORY = {"marketing", "transactional", "support"}
_TEMPLATE_STATUS = {"approved", "pending", "rejected"}
_CAMPAIGN_STATUS = {"draft", "scheduled", "sending", "completed", "paused", "failed"}
_RECIPIENT_STATUS = {"pending", "sent", "delivered", "read", "failed"}
_MESSAGE_STATUS = {"sent", "delivered", "read", "failed", "received"}
_MESSAGE_TYPE = {"text", "image", "document"}
_DIRECTION = {"inbound", "outbound"}


def _validate_phone(value: str) -> str:
    """Validate that *value* is a Nigerian phone number in +234XXXXXXXXX format."""
    if not isinstance(value, str) or not _PHONE_RE.match(value):
        raise ValueError("Phone number must be in +234XXXXXXXXX format (e.g. +2348012345678)")
    return value


# --------------------------------------------------------------------------- #
# 1. Account schemas
# --------------------------------------------------------------------------- #
class WhatsAppAccountCreate(BaseModel):
    """Payload for creating a new WhatsApp Business account."""

    phone_number: str = Field(min_length=5, max_length=50)
    api_key: str = Field(min_length=20, max_length=500)
    account_name: str = Field(min_length=1, max_length=255)

    @field_validator("phone_number")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        return _validate_phone(v)


class WhatsAppAccountUpdate(BaseModel):
    """Payload for updating an existing WhatsApp account."""

    account_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    status: Optional[str] = Field(default=None, pattern="^(active|inactive)$")
    rate_limit_per_hour: Optional[int] = Field(default=None, ge=1, le=100000)

    model_config = {"extra": "forbid"}


class WhatsAppAccountResponse(BaseModel):
    """Public representation of a WhatsApp account (no api_key exposed)."""

    id: int
    phone_number: str
    account_name: str
    status: str
    rate_limit_per_hour: int
    created_at: datetime
    business_id: int

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------- #
# 2. Template schemas
# --------------------------------------------------------------------------- #
class WhatsAppTemplateCreate(BaseModel):
    """Payload for creating a message template."""

    template_name: str = Field(min_length=1, max_length=255)
    template_text: str = Field(min_length=1, max_length=1000)
    variables: List[str] = Field(default_factory=list)
    category: str = Field(default="marketing", pattern="^(marketing|transactional|support)$")

    @field_validator("variables")
    @classmethod
    def _validate_variables(cls, v: List[str]) -> List[str]:
        """Ensure variable names are non-empty and unique."""
        cleaned = [var.strip() for var in v if var.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("Variable names must be unique")
        return cleaned


class WhatsAppTemplateResponse(BaseModel):
    """Public representation of a message template."""

    id: int
    template_name: str
    template_text: str
    variables: List[str]
    category: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------- #
# 3. Broadcast schemas
# --------------------------------------------------------------------------- #
class WhatsAppBroadcastCreate(BaseModel):
    """Payload for creating a bulk broadcast campaign.

    Either ``template_id`` or ``message_text`` must be provided (not both).
    Either ``recipients`` (customer IDs) or ``phone_numbers`` must be provided
    (not both).
    """

    account_id: int = Field(ge=1)
    campaign_name: str = Field(min_length=1, max_length=255)
    template_id: Optional[int] = Field(default=None, ge=1)
    message_text: Optional[str] = Field(default=None, min_length=1, max_length=4096)
    recipients: List[int] = Field(default_factory=list)
    phone_numbers: Optional[List[str]] = Field(default=None)
    variables_map: Dict[int, Dict[str, str]] = Field(default_factory=dict)
    scheduled_time: Optional[datetime] = None

    @model_validator(mode="after")
    def _validate_message_source(self) -> "WhatsAppBroadcastCreate":
        if self.template_id is not None and self.message_text is not None:
            raise ValueError("Provide either template_id or message_text, not both")
        if self.template_id is None and self.message_text is None:
            raise ValueError("Either template_id or message_text must be provided")
        return self

    @model_validator(mode="after")
    def _validate_recipients(self) -> "WhatsAppBroadcastCreate":
        if not self.recipients and not self.phone_numbers:
            raise ValueError("Either recipients (customer IDs) or phone_numbers must be provided")
        if self.recipients and self.phone_numbers:
            raise ValueError("Provide either recipients or phone_numbers, not both")
        return self

    @field_validator("phone_numbers")
    @classmethod
    def _validate_phone_numbers(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        for phone in v:
            _validate_phone(phone)
        return v


class WhatsAppBroadcastResponse(BaseModel):
    """Public representation of a broadcast campaign."""

    id: int
    campaign_name: str
    status: str
    total_recipients: int
    sent_count: int
    delivered_count: int
    read_count: int
    failed_count: int
    reply_count: int
    scheduled_time: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BroadcastPauseRequest(BaseModel):
    """Payload for pausing or resuming a broadcast."""

    status: str = Field(pattern="^(paused|resumed)$")


# --------------------------------------------------------------------------- #
# 4. Recipient schema
# --------------------------------------------------------------------------- #
class RecipientResponse(BaseModel):
    """Public representation of a single campaign recipient."""

    id: int
    campaign_id: int
    customer_id: Optional[int] = None
    phone_number: str
    status: str
    delivery_timestamp: Optional[datetime] = None
    read_timestamp: Optional[datetime] = None
    replied: bool
    reply_text: str
    error_message: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------- #
# 5. Message schemas
# --------------------------------------------------------------------------- #
class WhatsAppMessageResponse(BaseModel):
    """Public representation of a single WhatsApp message."""

    id: int
    to_number: str
    message_text: str
    status: str
    delivery_timestamp: Optional[datetime] = None
    read_timestamp: Optional[datetime] = None
    is_reply: bool
    reply_text: Optional[str] = None

    model_config = {"from_attributes": True}


class WhatsAppSendRequest(BaseModel):
    """Payload for sending a single (non-broadcast) WhatsApp message."""

    account_id: int = Field(ge=1)
    to_number: str = Field(min_length=5, max_length=50)
    message_text: str = Field(min_length=1, max_length=4096)
    media_url: Optional[str] = Field(default=None, max_length=500)

    @field_validator("to_number")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        return _validate_phone(v)


class WhatsAppSendResponse(BaseModel):
    """Response for a single message send."""

    id: int
    to_number: str
    message_text: str
    status: str
    delivery_timestamp: Optional[datetime] = None
    read_timestamp: Optional[datetime] = None
    is_reply: bool
    reply_text: Optional[str] = None

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------- #
# 6. Engagement / stats schemas
# --------------------------------------------------------------------------- #
class BroadcastStatsResponse(BaseModel):
    """Aggregated engagement metrics for a broadcast campaign."""

    total_sent: int
    delivery_rate: float
    read_rate: float
    reply_rate: float
    failed_count: int
    error_summary: Dict[str, int]
    avg_delivery_time_seconds: int
    avg_read_time_seconds: int


class WhatsAppWebhookPayload(BaseModel):
    """Minimal payload accepted by the inbound webhook endpoint."""

    account_id: int = Field(ge=1)
    from_number: str = Field(min_length=5, max_length=50)
    message_text: str = Field(min_length=1, max_length=4096)
    timestamp: Optional[datetime] = None

    @field_validator("from_number")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        return _validate_phone(v)
