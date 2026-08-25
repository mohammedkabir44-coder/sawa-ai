"""Usage tracking model (tenant-scoped)."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UsageRecord(Base):
    __tablename__ = "usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    metric: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # monthly_ai_messages | monthly_sms | monthly_whatsapp_messages |
    # active_automations | customers | staff_members
    value: Mapped[int] = mapped_column(Integer, default=0)
    period: Mapped[str] = mapped_column(String(10), default="")  # YYYY-MM
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)