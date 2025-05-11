from fastapi import APIRouter, HTTPException, FastAPI
from .models import create_cart, get_cart_by_user, update_cart_product, delete_cart_product
from .schemas import CartBase, UpdateProduct

app = FastAPI()
router = APIRouter()


@router.post("/cart/{user_id}", response_model=dict)
async def create_cart_endpoint(cart: CartBase):
    return await create_cart(cart.dict())


@router.get("/cart/{user_id}", response_model=dict)
async def read_cart(user_id: int):
    cart = await get_cart_by_user(user_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart


@router.put("/cart/{user_id}")
async def update_product(user_id: int, update: UpdateProduct):
    success = await update_cart_product(user_id, update.product_id, update.quantity)
    if not success:
        raise HTTPException(status_code=400, detail="Update failed")
    return {"message": "Product updated in cart"}


@router.delete("/cart/{user_id}/{product_id}")
async def delete_product(user_id: int, product_id: int):
    success = await delete_cart_product(user_id, product_id)
    if not success:
        raise HTTPException(status_code=400, detail="Delete failed")
    return {"message": "Product deleted from cart"}
