"""Customer model (tenant-scoped)."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), default="")
    preferred_language: Mapped[str] = mapped_column(String(20), default="unknown")
    tags: Mapped[str] = mapped_column(String(500), default="")  # comma-separated
    source: Mapped[str] = mapped_column(String(50), default="whatsapp")
    notes: Mapped[str] = mapped_column(Text, default="")
    lead_status: Mapped[str] = mapped_column(String(30), default="new")
    last_interaction: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    orders = relationship("Order", back_populates="customer")
