import uuid

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class CartItem(BaseModel):
    product_id: Optional[int]
    quantity: int
    discounted_price: Optional[int] = None
    discount: Optional[int] = None
    img_url: Optional[str] = None
    name: Optional[str] = None
    price: Optional[int] = None

    class Config:
        orm_mode = True


class CartReq(BaseModel):
    quantity: int


class CartBase(BaseModel):
    user_id: str
    cart_items: List[CartItem]
    created_at: datetime = None
    updated_at: datetime = None

    class Config:
        orm_mode = True
