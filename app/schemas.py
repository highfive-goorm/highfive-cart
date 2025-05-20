import uuid

from pydantic import BaseModel, Field, ConfigDict
from typing import List
from datetime import datetime


class CartItem(BaseModel):
    product_id: int
    quantity: int
    #discounted_price: int = 0
    #discount: int = 0


class CartBase(BaseModel):
    user_id: str
    cart_items: List[CartItem]
    created_at: datetime = None
    updated_at: datetime = None

    model_config = ConfigDict(
        validate_by_name=True,
        from_attributes=True
    )
