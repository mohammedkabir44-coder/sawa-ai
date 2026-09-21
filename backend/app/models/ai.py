"""AI settings model (tenant-scoped)."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AISettings(Base):
    __tablename__ = "ai_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    assistant_name: Mapped[str] = mapped_column(String(100), default="SAWA Assistant")
    greeting_message: Mapped[str] = mapped_column(Text, default="")
    auto_reply_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    language: Mapped[str] = mapped_column(String(20), default="en")
    tone: Mapped[str] = mapped_column(String(30), default="friendly")
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.6)
    handoff_on_low_confidence: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)