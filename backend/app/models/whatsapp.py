"""WhatsApp bulk broadcast models (tenant-scoped).

Six tables that power the WhatsApp Bulk Broadcast feature:

* WhatsAppAccount   – connected WhatsApp Business API accounts
* WhatsAppTemplate  – reusable message templates with variable substitution
* WhatsAppCampaign  – a single bulk-broadcast run (engagement aggregate)
* WhatsAppRecipient – one row per customer in a campaign
* WhatsAppMessage   – every individual message sent or received
* WhatsAppEngagement – granular engagement events for analytics

Security
--------
Every model carries a ``business_id`` foreign-key to ``businesses.id`` so that
tenant isolation is enforced at the database level.  All queries in the API
layer **must** filter by ``business_id``.

The ``api_key`` column on :class:`WhatsAppAccount` is transparently encrypted
at rest using Fernet (AES-128-CBC + HMAC) via the :class:`EncryptedString`
type-decorator.
"""
from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.database import Base


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def utcnow() -> datetime:
    """Return the current UTC timestamp (timezone-aware)."""
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Encryption
# --------------------------------------------------------------------------- #
_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    """Return a process-wide :class:`Fernet` instance.

    The key is deterministically derived from ``settings.JWT_SECRET`` so that
    encrypted values survive process restarts.  In production you would set a
    dedicated ``WHATSAPP_API_KEY_ENCRYPTION_KEY`` environment variable; the
    derivation here is a safe development default.
    """
    global _fernet
    if _fernet is None:
        key_material = settings.WHATSAPP_API_KEY_ENCRYPTION_KEY or settings.JWT_SECRET
        key = base64.urlsafe_b64encode(hashlib.sha256(key_material.encode()).digest())
        _fernet = Fernet(key)
    return _fernet


class EncryptedString(TypeDecorator):
    """SQLAlchemy type that encrypts/decrypts string values with Fernet.

    * ``process_bind_param`` – encrypts the value before it hits the DB.
    * ``process_result_value`` – decrypts the value when it is loaded.

    The underlying column is a ``String(500)`` which is more than enough for a
    Fernet token (typically ~100-200 chars for a short API key).
    """

    impl = String(500)
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect: Any) -> Optional[str]:
        if value is None:
            return None
        return _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")

    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[str]:
        if value is None:
            return None
        try:
            return _get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
        except (InvalidToken, ValueError):
            # If the stored value cannot be decrypted (e.g. legacy plaintext),
            # return it as-is so the application can still read it.
            return value


# --------------------------------------------------------------------------- #
# 1. WhatsAppAccount
# --------------------------------------------------------------------------- #
class WhatsAppAccount(Base):
    """A connected WhatsApp Business API account for a tenant."""

    __tablename__ = "whatsapp_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)
    api_key: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), default="")
    # Meta / Cloud-API fields (kept for backward compatibility with commerce flow)
    phone_number_id: Mapped[str] = mapped_column(String(255), default="")
    business_account_id: Mapped[str] = mapped_column(String(255), default="")
    display_name: Mapped[str] = mapped_column(String(255), default="")
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(
        String(20), default="active", index=True
    )  # active | inactive
    rate_limit_per_hour: Mapped[int] = mapped_column(Integer, default=1000)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        # business_id + phone_number must be unique per tenant
        Index("ix_whatsapp_accounts_business_phone", "business_id", "phone_number", unique=True),
    )

    campaigns: Mapped[list["WhatsAppCampaign"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    messages: Mapped[list["WhatsAppMessage"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# --------------------------------------------------------------------------- #
# 2. WhatsAppTemplate
# --------------------------------------------------------------------------- #
class WhatsAppTemplate(Base):
    """A reusable message template with variable placeholders."""

    __tablename__ = "whatsapp_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_text: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[List[str]] = mapped_column(JSON, default=list)
    category: Mapped[str] = mapped_column(
        String(30), default="marketing", index=True
    )  # marketing | transactional | support
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )  # approved | pending | rejected
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("ix_whatsapp_templates_business_name", "business_id", "template_name", unique=True),
    )

    campaigns: Mapped[list["WhatsAppCampaign"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# --------------------------------------------------------------------------- #
# 3. WhatsAppCampaign
# --------------------------------------------------------------------------- #
class WhatsAppCampaign(Base):
    """A bulk-broadcast campaign run.

    Aggregates engagement counts so the API can return stats without
    scanning every recipient row.
    """

    __tablename__ = "whatsapp_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey("whatsapp_accounts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    campaign_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="draft", index=True
    )  # draft | scheduled | sending | completed | paused | failed
    template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("whatsapp_templates.id", ondelete="SET NULL"), nullable=True
    )
    scheduled_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_recipients: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0)
    read_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("ix_whatsapp_campaigns_business_status", "business_id", "status"),
        Index("ix_whatsapp_campaigns_scheduled_time", "scheduled_time"),
    )

    account: Mapped["WhatsAppAccount"] = relationship(
        back_populates="campaigns", lazy="joined"
    )
    template: Mapped[Optional["WhatsAppTemplate"]] = relationship(
        back_populates="campaigns", lazy="joined"
    )
    recipients: Mapped[list["WhatsAppRecipient"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    messages: Mapped[list["WhatsAppMessage"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    engagements: Mapped[list["WhatsAppEngagement"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# --------------------------------------------------------------------------- #
# 4. WhatsAppRecipient
# --------------------------------------------------------------------------- #
class WhatsAppRecipient(Base):
    """One customer in a campaign – tracks per-recipient delivery status."""

    __tablename__ = "whatsapp_recipients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("whatsapp_campaigns.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    customer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), index=True, nullable=True
    )
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )  # pending | sent | delivered | read | failed
    delivery_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    read_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    replied: Mapped[bool] = mapped_column(Boolean, default=False)
    reply_text: Mapped[str] = mapped_column(Text, default="")
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("ix_whatsapp_recipients_campaign_status", "campaign_id", "status"),
    )

    campaign: Mapped["WhatsAppCampaign"] = relationship(
        back_populates="recipients", lazy="joined"
    )
    messages: Mapped[list["WhatsAppMessage"]] = relationship(
        back_populates="recipient",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# --------------------------------------------------------------------------- #
# 5. WhatsAppMessage
# --------------------------------------------------------------------------- #
class WhatsAppMessage(Base):
    """Every individual WhatsApp message (sent or received)."""

    __tablename__ = "whatsapp_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey("whatsapp_accounts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    to_number: Mapped[str] = mapped_column(String(50), nullable=False)
    from_number: Mapped[str] = mapped_column(String(50), default="")
    message_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(
        String(30), default="sent", index=True
    )  # sent | delivered | read | failed | received
    delivery_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    read_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    message_type: Mapped[str] = mapped_column(
        String(30), default="text"
    )  # text | image | document
    media_url: Mapped[str] = mapped_column(String(500), default="")
    media_id: Mapped[str] = mapped_column(String(255), default="")
    transcript: Mapped[str] = mapped_column(Text, default="")
    direction: Mapped[str] = mapped_column(
        String(10), default="outbound", index=True
    )  # inbound | outbound
    is_reply: Mapped[bool] = mapped_column(Boolean, default=False)
    reply_text: Mapped[str] = mapped_column(Text, default="")
    error_message: Mapped[str] = mapped_column(Text, default="")
    campaign_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("whatsapp_campaigns.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    recipient_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("whatsapp_recipients.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("ix_whatsapp_messages_business_created", "business_id", "created_at"),
    )

    account: Mapped["WhatsAppAccount"] = relationship(
        back_populates="messages", lazy="joined"
    )
    campaign: Mapped[Optional["WhatsAppCampaign"]] = relationship(
        back_populates="messages", lazy="joined"
    )
    recipient: Mapped[Optional["WhatsAppRecipient"]] = relationship(
        back_populates="messages", lazy="joined"
    )
    engagements: Mapped[list["WhatsAppEngagement"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# --------------------------------------------------------------------------- #
# 6. WhatsAppEngagement
# --------------------------------------------------------------------------- #
class WhatsAppEngagement(Base):
    """Granular engagement events for analytics (sent, delivered, read, replied)."""

    __tablename__ = "whatsapp_engagements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    message_id: Mapped[int] = mapped_column(
        ForeignKey("whatsapp_messages.id", ondelete="CASCADE"), index=True, nullable=False
    )
    campaign_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("whatsapp_campaigns.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    customer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(20), default="sent", index=True
    )  # sent | delivered | read | replied
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, index=True
    )
    response_time_seconds: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    __table_args__ = (
        Index("ix_whatsapp_engagements_business_event", "business_id", "event_type"),
        Index("ix_whatsapp_engagements_event_ts", "event_timestamp"),
    )

    message: Mapped["WhatsAppMessage"] = relationship(
        back_populates="engagements", lazy="joined"
    )
    campaign: Mapped[Optional["WhatsAppCampaign"]] = relationship(
        back_populates="engagements", lazy="joined"
    )
