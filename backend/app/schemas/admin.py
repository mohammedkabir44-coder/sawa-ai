"""Platform admin schemas."""
from pydantic import BaseModel


class PlatformStats(BaseModel):
    total_businesses: int
    active_businesses: int
    suspended_businesses: int
    total_customers: int
    total_messages: int
    whatsapp_messages: int
    sms_messages: int
    ai_requests: int
    failed_requests: int
    failed_jobs: int


class BusinessAdminOut(BaseModel):
    id: int
    name: str
    status: str
    primary_language: str
    created_at: object | None = None

    model_config = {"from_attributes": True}