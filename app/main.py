from datetime import datetime
from typing import Dict, List

import httpx
from bson import ObjectId
from fastapi import FastAPI, HTTPException, status, Path, Depends
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorClient

from .schemas import CartBase


def get_db() -> AsyncIOMotorCollection:
    """
    MongoDB에 연결하여 Order 컬렉션을 반환합니다.
    URI는 환경변수나 시크릿 매니저로 관리할 것을 권장합니다.
    """
    client = AsyncIOMotorClient("mongodb://root:mongodb_cart@mongodb_cart:27017")
    return client.cart.cart  # 'order' 데이터베이스의 'order' 컬렉션


app = FastAPI()


async def create_cart(
    payload: CartBase,
    collection: AsyncIOMotorCollection = Depends(get_db)
):
    # 1) DB 연결 확인
    if collection is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "DB 연결 오류")

    # 2) 상품 서비스 호출
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"http://product:8001/product/{payload.product_id}",
                timeout=5.0
            )
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"상품 서비스 호출 실패: {e}")

    product_data = resp.json()

    # 3) 문서 준비
    now = datetime.utcnow()
    doc = {
        "user_id":      payload.user_id,
        "product_id":   payload.product_id,
        "quantity":     payload.quantity,
        "product":      product_data,
        "created_at":   now,
        "updated_at":   now,
    }

    # 4) DB 삽입
    result = await collection.insert_one(doc)
    if result.inserted_id is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "DB 삽입 실패")

    # 5) 응답용 필드 세팅
    doc["id"] = str(result.inserted_id)
    return CartBase(**doc)


@app.get(
    "/cart/{user_id}",
    response_model=CartBase,
    status_code=status.HTTP_200_OK
)
async def read_cart(
        user_id: int,
        collection: AsyncIOMotorCollection = Depends(get_db)
):
    # 1) user_id 로 한 건 조회 (find_one 사용)
    if collection is None:
        raise HTTPException(500, "DB 연결 오류")
    cart_doc = await collection.find_one({"user_id": user_id})
    if cart_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )

    # 2) BSON ObjectId -> 문자열 변환
    cart_doc["id"] = str(cart_doc["_id"])

    # 3) 총가격 계산 및 추가
    items = cart_doc.get("cart_items", [])
    total_price = sum(
        item.get("discounted_price", 0) * item.get("quantity", 0)
        for item in items
    )
    cart_doc["total_price"] = total_price

    # (선택) 아이템 내 중첩된 ObjectId도 문자열로 변환하고 싶다면:
    for item in items:
        if "_id" in item:
            item["id"] = str(item["_id"])

    # 4) Pydantic 모델로 변환해 반환
    return CartBase(**cart_doc)


@app.get("/cart/{user_id}/{product_id}", response_model=CartBase)
async def get_order(
        user_id: str,
        product_id: str,
        collection: AsyncIOMotorCollection = Depends(get_db)
):
    if collection is None:
        raise HTTPException(500, "DB 연결 오류")

    # 1) ObjectId 변환 검사
    cart_doc = await collection.find({"user_id": user_id})
    if cart_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )

    # 2) BSON ObjectId -> 문자열 변환 (필요시)
    product = cart_doc.find_one({'product_id': product_id})

    return product


@app.delete("/cart/{user_id}", status_code=204)
async def delete_cart(
        user_id: str,
        collection: AsyncIOMotorCollection = Depends(get_db)
):
    if collection is None:
        raise HTTPException(500, "DB 연결 오류")
    # 1) ObjectId 변환 검사
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # 2) 삭제 실행
    result = await collection.delete({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return


@app.put("/cart/{user_id}/{product_id}", status_code=204)
async def put_cart(
        user_id: str,
        collection: AsyncIOMotorCollection = Depends(get_db)
):
    # 1) ObjectId 변환 검사
    if collection is None:
        raise HTTPException(500, "DB 연결 오류")
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # 2) 삭제 실행
    result = await collection.delete({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return
