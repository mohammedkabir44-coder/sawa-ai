"""Conversation, Message and MessageMedia models (tenant-scoped)."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    channel: Mapped[str] = mapped_column(String(20), default="whatsapp")  # whatsapp | sms
    mode: Mapped[str] = mapped_column(
        String(20), default="AI_ACTIVE"
    )  # AI_ACTIVE | HUMAN_ACTIVE | AI_PAUSED
    language: Mapped[str] = mapped_column(String(20), default="unknown")
    lead_status: Mapped[str] = mapped_column(String(30), default="new")
    assigned_staff_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    last_message: Mapped[str] = mapped_column(Text, default="")
    last_activity: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, index=True
    )
    is_unread: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # inbound | outbound
    channel: Mapped[str] = mapped_column(String(20), default="whatsapp")
    sender: Mapped[str] = mapped_column(String(50), default="")  # phone number
    body: Mapped[str] = mapped_column(Text, default="")
    message_type: Mapped[str] = mapped_column(String(30), default="text")  # text | voice | image
    language: Mapped[str] = mapped_column(String(20), default="unknown")
    intent: Mapped[str] = mapped_column(String(40), default="unknown")
    intent_confidence: Mapped[float] = mapped_column(default=0.0)
    transcription: Mapped[str] = mapped_column(Text, default="")  # for voice notes
    status: Mapped[str] = mapped_column(String(30), default="received")  # received | sent | delivered | read | failed
    provider_message_id: Mapped[str] = mapped_column(String(255), default="")
    is_ai_generated: Mapped[bool] = mapped_column(default=False)
    ai_failed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class MessageMedia(Base):
    __tablename__ = "message_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), index=True, nullable=False
    )
    media_type: Mapped[str] = mapped_column(String(30), default="")  # audio | image | video
    provider_media_id: Mapped[str] = mapped_column(String(255), default="")
    mime_type: Mapped[str] = mapped_column(String(100), default="")
    local_path: Mapped[str] = mapped_column(String(500), default="")
    transcription: Mapped[str] = mapped_column(Text, default="")
    transcription_confidence: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)