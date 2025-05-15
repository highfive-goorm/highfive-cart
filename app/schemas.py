# cart/app/schemas.py
from pydantic import BaseModel, Field
from typing import List

class CartItem(BaseModel):
    product_id: int
    quantity: int
    price: int = 0
    discounted_price: int = 0
    discount: int = 0

class CartBase(BaseModel):
    id: str = Field(default=None, alias="id")
    user_id: str
    cart_items: List[CartItem]
    created_at: str = None
    updated_at: str = None

    class Config:
        allow_population_by_field_name = True
        orm_mode = True