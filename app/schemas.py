from pydantic import BaseModel
from typing import List


class CartItem(BaseModel):
    product_id: int
    quantity: int
    price: int
    discounted_price: int
    discount: int


class CartBase(BaseModel):
    id: str
    cart_items: List[CartItem]
    user_id: str
    product_id: int
    quantity: int


class UpdateProduct(CartBase):
    product_id: int
    quantity: int
    price: int
    discounted_price: int
    discount: int


# Optional: schema for responses including user_id
class CartOut(CartBase):
    user_id: str
