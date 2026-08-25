"""Business (tenant) model."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Business(Base):
    """A tenant. Every tenant-owned record references a business."""

    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_type: Mapped[str] = mapped_column(String(100), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    website: Mapped[str] = mapped_column(String(255), default="")
    primary_language: Mapped[str] = mapped_column(
        String(20), default="en"
    )  # en | ha | ha-en
    currency: Mapped[str] = mapped_column(String(10), default="NGN")
    timezone: Mapped[str] = mapped_column(String(50), default="Africa/Lagos")
    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active | suspended
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    members: Mapped[list["BusinessUser"]] = relationship(back_populates="business")  # noqa: F821
