"""Product and service schemas."""
from datetime import datetime

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    price: float = 0.0
    currency: str = "NGN"
    sku: str = ""
    category: str = ""
    stock: int = 0
    availability: str = "available"
    images: list[str] = []
    location: str = ""
    additional_info: str = ""
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: float | None = None
    currency: str | None = None
    sku: str | None = None
    category: str | None = None
    stock: int | None = None
    availability: str | None = None
    images: list[str] | None = None
    location: str | None = None
    additional_info: str | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    id: int
    business_id: int
    name: str
    description: str
    price: float
    currency: str
    sku: str
    category: str
    stock: int
    availability: str
    images: list[str] = []
    location: str
    additional_info: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    price: float = 0.0
    currency: str = "NGN"
    duration: str = ""
    category: str = ""
    availability: str = "available"
    images: list[str] = []
    location: str = ""
    additional_info: str = ""
    is_active: bool = True


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: float | None = None
    currency: str | None = None
    duration: str | None = None
    category: str | None = None
    availability: str | None = None
    images: list[str] | None = None
    location: str | None = None
    additional_info: str | None = None
    is_active: bool | None = None


class ServiceOut(BaseModel):
    id: int
    business_id: int
    name: str
    description: str
    price: float
    currency: str
    duration: str
    category: str
    availability: str
    images: list[str] = []
    location: str
    additional_info: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}