from pydantic import BaseModel
from typing import Dict


class CartBase(BaseModel):
    user_id: int
    products: Dict[int, int]  # product_id: quantity


class UpdateProduct(BaseModel):
    product_id: int
    quantity: int
