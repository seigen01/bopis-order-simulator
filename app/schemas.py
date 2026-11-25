from datetime import datetime
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=120)
    available_stock: int = Field(..., ge=0)


class ProductResponse(BaseModel):
    sku: str
    name: str
    available_stock: int

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    quantity: int = Field(..., gt=0)


class OrderResponse(BaseModel):
    order_id: int
    sku: str
    quantity: int
    status: str
    remaining_stock: int
    created_at: datetime