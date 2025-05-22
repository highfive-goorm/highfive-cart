# cart/app/main.py
from datetime import datetime
from typing import Dict, List
from bson import ObjectId
from fastapi import FastAPI, HTTPException, status, Path, Depends, Body
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorClient, AsyncIOMotorDatabase
from .schemas import CartBase, CartItem, CartReq
import httpx

app = FastAPI()

MONGO_URI = "mongodb://postgres:han00719()@mongodb_cart:27017/admin?authSource=admin"
DB_NAME = "cart"


# 1) db dependency
async def get_db() -> AsyncIOMotorDatabase:
    client = AsyncIOMotorClient(MONGO_URI)
    return client[DB_NAME]


# 2) collection dependency
def get_cart_collection(
        db: AsyncIOMotorDatabase = Depends(get_db)
) -> AsyncIOMotorCollection:
    return db["cart"]  # ← whatever your collection name is


def object_id_or_404(object_id: str) -> ObjectId:
    try:
        return ObjectId(object_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


@app.post("/cart/{user_id}", response_model=CartBase, status_code=201)
async def add_to_cart(
        user_id: str,
        item: CartItem,
        cart_collection: AsyncIOMotorCollection = Depends(get_cart_collection)  # <- note no ()
):
    now = datetime.utcnow()
    cart = await cart_collection.find_one({"user_id": user_id})

    if cart is None:
        # 새로운 카트 생성
        doc = {
            "user_id": user_id,
            "cart_items": [item.dict()],
            "created_at": now,
            "updated_at": now,
        }
        result = await cart_collection.insert_one(doc)  # <- use cart_collection
        doc["id"] = str(result.inserted_id)
        return CartBase(**doc)

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

    cart_1 = await cart_collection.update_one(
        {"user_id": user_id},
        {"$set": {"cart_items": updated_items, "updated_at": now}}
    )
    if cart_1 is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DB 연결 오류"
        )
    # prepare return payload
    cart["cart_items"] = updated_items
    cart["updated_at"] = now
    cart["id"] = str(cart.pop("_id"))
    return CartBase(**cart)


@app.get(
    "/cart/{user_id}",
    response_model=CartBase,
    summary="유저 카트와 각 상품·브랜드 정보를 합쳐서 반환"
)
async def get_cart(
        user_id: str,
        cart_collection: AsyncIOMotorCollection = Depends(get_cart_collection),  # ← remove ()
):
    # 0) 컬렉션 연결 확인
    if cart_collection is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DB 연결 오류"
        )

    # 1) 카트 문서 단일 조회
    cart_doc = await cart_collection.find_one({"user_id": user_id})
    if cart_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )

    # 2) cart_items 꺼내기 (없으면 빈 리스트)
    cart_items = cart_doc.get("cart_items", [])
    product_ids = [item["product_id"] for item in cart_items]

    # 3) 상품 서비스에 bulk 요청
    detailed_map: dict[str, dict] = {}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://product:8001/product/bulk",
                json={"product_ids": product_ids},
                timeout=10.0
            )
            resp.raise_for_status()
            bulk_json = resp.json()
            if isinstance(bulk_json, dict):
                prods = bulk_json.get("cart_items", [])
            elif isinstance(bulk_json, list):
                prods = bulk_json
            else:
                prods = []
            for prod in prods:
                detailed_map[prod["id"]] = prod

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"상품 서비스 네트워크 오류: {e}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"상품 서비스 처리 중 오류: {e}"
        )

    # 4) cart_items에 상품·브랜드 정보 결합
    enriched_items = []
    for item in cart_items:
        prod = detailed_map.get(item["product_id"], {})
        enriched_items.append({
            **item,
            "name": prod.get("name", "알 수 없음"),
            "img_url": prod.get("img_url", ""),
            "discount": prod.get("discount", 0),
            "price": prod.get("price", 0),
            "discounted_price": prod.get("discounted_price", 0),
            "brand_id": prod.get("brand_id", 0),
            "brand_kor": prod.get("brand_kor", ""),
            "brand_eng": prod.get("brand_eng", ""),
        })

    # 5) 반환 직전 포맷 정리
    cart_doc["cart_items"] = enriched_items
    cart_doc["id"] = str(cart_doc.pop("_id"))
    return CartBase(**cart_doc)


@app.delete("/cart/{user_id}", status_code=204)
async def delete_cart(
        user_id: str,
        cart_collection: AsyncIOMotorCollection = Depends(get_cart_collection),  # ← no ()
):
    # 0) DB 연결 확인
    if cart_collection is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DB 연결 오류"
        )

    # 1) 해당 유저의 모든 카트 문서 삭제
    result = await cart_collection.delete_many({"user_id": user_id})
    if result is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="DB 연결 오류")
    # 2) 삭제된 게 없으면 404
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )

    # 3) 204 No Content (FastAPI handles empty return)
    return


@app.delete(
    "/cart/{user_id}/{product_id}",
    status_code=204,
    summary="카트에서 단일 아이템 제거"
)
async def delete_cart_item(
        user_id: str,
        product_id: int,
        cart_collection=Depends(get_cart_collection),  # ← correct dependency
):
    # remove one item
    result = await cart_collection.update_one(
        {"user_id": user_id},
        {"$pull": {"cart_items": {"product_id": product_id}}}
    )

    # 404: no such cart
    if result.matched_count == 0:
        raise HTTPException(404, "Cart not found")

    # 404: cart exists, but item not in it
    if result.modified_count == 0:
        raise HTTPException(404, "Cart item not found")

    # 204 No Content on success
    return


@app.put(
    "/cart/{user_id}/{product_id}",
    response_model=CartBase,
    summary="카트 항목 수량을 업데이트하고 전체 카트(상품·브랜드 정보 포함)를 반환"
)
async def update_cart_item(
    user_id: str,
    product_id: int,
    item: CartReq = Body(..., description="새 수량({\"quantity\": N})"),
    cart_collection: AsyncIOMotorCollection = Depends(get_cart_collection),
):
    now = datetime.utcnow()

    # 1) 수량 업데이트
    update_res = await cart_collection.update_one(
        {"user_id": user_id, "cart_items.product_id": product_id},
        {"$set": {"cart_items.$.quantity": item.quantity, "updated_at": now}}
    )

    if update_res.matched_count == 0:
        raise HTTPException(404, "Cart not found")
    if update_res.modified_count == 0:
        raise HTTPException(404, "Cart item not found")

    # 2) 업데이트된 카트 문서 가져오기
    cart_doc = await cart_collection.find_one({"user_id": user_id})
    if not cart_doc:
        raise HTTPException(404, "Cart not found after update")

    # 3) cart_items & product_ids 준비
    cart_items = cart_doc.get("cart_items", [])
    product_ids = [ci["product_id"] for ci in cart_items]

    # 4) 상품 서비스에 bulk 요청
    detailed_map: dict[int, dict] = {}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://product:8001/product/bulk",
                json={"product_ids": product_ids},
                timeout=10.0
            )
            resp.raise_for_status()
            bulk_json = resp.json()
            if isinstance(bulk_json, dict):
                prods = bulk_json.get("product_ids", [])
            elif isinstance(bulk_json, list):
                prods = bulk_json
            else:
                prods = []
            for p in prods:
                detailed_map[p["id"]] = p

    except httpx.RequestError as e:
        raise HTTPException(502, f"상품 서비스 네트워크 오류: {e}")
    except Exception as e:
        raise HTTPException(502, f"상품 서비스 처리 중 오류: {e}")

    # 5) cart_items를 상품·브랜드 정보로 enrich
    enriched = []
    for ci in cart_items:
        prod = detailed_map.get(ci["product_id"], {})
        enriched.append({
            **ci,
            "name":             prod.get("name", "알 수 없음"),
            "img_url":          prod.get("img_url", ""),
            "discount":         prod.get("discount", 0),
            "price":            prod.get("price", 0),
            "discounted_price": prod.get("discounted_price", 0),
            "brand_id":         prod.get("brand_id", 0),
            "brand_kor":        prod.get("brand_kor", ""),
            "brand_eng":        prod.get("brand_eng", ""),
        })

    # 6) 최종 포맷 정리 및 반환
    cart_doc["cart_items"] = enriched
    cart_doc["id"] = str(cart_doc.pop("_id"))
    return CartBase(**cart_doc)