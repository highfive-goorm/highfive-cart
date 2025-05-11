from typing import Dict
from bson import ObjectId
from database import db

cart_collection = db["cart"]


def cart_helper(cart) -> dict:
    return {
        "id": cart["id"],
        "user_id": cart["user_id"],
        "products": cart["products"]
    }


async def create_cart(data: dict):
    cart = await cart_collection.insert_one(data)
    new_cart = await cart_collection.find_one({"id": cart.inserted_id})
    return cart_helper(new_cart)


async def get_cart_by_user(user_id: int):
    cart = await cart_collection.find_one({"user_id": user_id})
    if cart:
        return cart_helper(cart)


async def update_cart_product(user_id: int, product_id: int, quantity: int):
    result = await cart_collection.update_one(
        {"user_id": user_id},
        {"$set": {f"products.{product_id}": quantity}},
        upsert=True
    )
    return result.modified_count > 0 or result.upserted_id is not None


async def delete_cart_product(user_id: int, product_id: int):
    result = await cart_collection.update_one(
        {"user_id": user_id},
        {"$unset": {f"products.{product_id}": ""}}
    )
    return result.modified_count > 0
