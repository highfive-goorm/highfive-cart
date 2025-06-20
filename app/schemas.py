import uuid

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class CartItem(BaseModel):
    product_id: int
    quantity: int
    discounted_price: Optional[int] = None
    discount: Optional[int] = None
    img_url: Optional[str] = None
    name: Optional[str] = None
    price: Optional[int] = None

    model_config = ConfigDict(from_attributes=True) # Updated from orm_mode for Pydantic v2


class CartReq(BaseModel):
    quantity: int


class CartBase(BaseModel):
    user_id: str
    cart_items: List[CartItem]
    created_at: datetime = None
    updated_at: datetime = None

    model_config = ConfigDict(from_attributes=True) # Updated from orm_mode for Pydantic v2
