"""SMS schemas."""
from pydantic import BaseModel, Field


class SMSSendRequest(BaseModel):
    phone: str = Field(min_length=5, max_length=50)
    message: str = Field(min_length=1, max_length=1600)


class SMSSendResponse(BaseModel):
    success: bool
    provider: str
    message_id: str = ""
    error: str = ""


class SMSTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    language: str = "en"


class SMSTemplateOut(BaseModel):
    id: int
    business_id: int
    name: str
    body: str
    language: str

    model_config = {"from_attributes": True}


class SMSMessageOut(BaseModel):
    id: int
    business_id: int
    to_phone: str
    body: str
    provider: str
    status: str
    provider_message_id: str
    error_message: str
    created_at: object | None = None

    model_config = {"from_attributes": True}