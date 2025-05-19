# cart/app/main.py
from datetime import datetime
from typing import Dict, List
from bson import ObjectId
from fastapi import FastAPI, HTTPException, status, Path, Depends
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorClient
from .schemas import CartBase, CartItem
from .database import collection
import httpx

app = FastAPI()

def get_db() -> AsyncIOMotorCollection:
    client = AsyncIOMotorClient("mongodb://root:mongodb_cart@mongodb_cart:27017")
    return client.cart.cart
def object_id_or_404(object_id: str) -> ObjectId:
    try:
        return ObjectId(object_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


@app.post("/cart/{user_id}", response_model=CartBase, status_code=201)
async def add_to_cart(user_id: str, item: CartItem):
    now = datetime.utcnow()
    cart = await collection.find_one({"user_id": user_id})

    if not cart:
        # 새로운 카트 생성
        doc = {
            "user_id": user_id,
            "cart_items": [item.dict()],
            "created_at": now,
            "updated_at": now,
        }
        result = await collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        return CartBase(**doc)
    else:
        # 기존 카트에 상품 추가 또는 수량 업데이트
        updated_items = []
        item_updated = False
        for cart_item in cart["cart_items"]:
            if cart_item["product_id"] == item.product_id:
                cart_item["quantity"] += item.quantity
                item_updated = True
            updated_items.append(cart_item)
        if not item_updated:
            updated_items.append(item.dict())
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"cart_items": updated_items, "updated_at": now}}
        )
        cart["cart_items"] = updated_items
        cart["updated_at"] = now
        cart["id"] = str(cart.pop("_id"))
        return CartBase(**cart)


@app.get("/cart/{user_id}", response_model=CartBase)
async def get_cart(user_id: str):
    cart = await collection.find_one({"user_id": user_id})
    if not cart:
        raise HTTPException(404, "Cart not found")
    
    cart_items = cart.get("cart_items", [])
    product_id_list = [item["product_id"] for item in cart_items]

    # 🟡 상품 정보를 bulk로 한 번에 받아오기
    detailed_map = {}
    if product_id_list:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    "http://product:8001/products/bulk",
                    json={"product_ids": product_id_list},
                    timeout=10.0
                )
                resp.raise_for_status()
                bulk_result = resp.json()
                for prod in bulk_result.get("products", []):
                    detailed_map[prod["id"]] = prod
            except Exception as e:
                raise HTTPException(502, f"Failed to fetch product details: {e}")

    # cart_items에 상품 정보 합성
    for item in cart_items:
        prod = detailed_map.get(item["product_id"], {})
        item.update({
            "name": prod.get("name", "알 수 없음"),
            "img_url": prod.get("img_url", ""),
            "discount": prod.get("discount", 0),
            "price": prod.get("price", 0),
            "discounted_price": prod.get("discounted_price", 0),
            "brand_id": prod.get("brand_id", 0),
            "brand_kor": prod.get("brand_kor", ""),
            "brand_eng": prod.get("brand_eng", ""),
            "brand_like_count": prod.get("brand_like_count", 0),
        })

    cart["cart_items"] = cart_items
    cart["id"] = str(cart.pop("_id"))
    return CartBase(**cart)


@app.delete("/cart/{user_id}", status_code=204)
async def delete_cart(user_id: str):
    result = await collection.delete_many({"user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cart not found")
    return


@app.delete("/cart/{user_id}/{product_id}", status_code=204)
async def delete_cart_item(user_id: str, product_id: int):
    result = await collection.update_one(
        {"user_id": user_id},
        {"$pull": {"cart_items": {"product_id": product_id}}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return


@app.put("/cart/{user_id}/{product_id}", response_model=CartBase)
async def update_cart_item(user_id: str, product_id: int, quantity: int):
    now = datetime.utcnow()
    result = await collection.update_one(
        {"user_id": user_id, "cart_items.product_id": product_id},
        {"$set": {"cart_items.$.quantity": quantity, "updated_at": now}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Cart item not found")
    cart = await collection.find_one({"user_id": user_id})
    cart["id"] = str(cart.pop("_id"))
    return CartBase(**cart)
