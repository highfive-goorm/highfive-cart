from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database
import os
client = AsyncIOMotorClient("mongodb://root:mongodb_order@mongodb_order:27017")
db = client["cart"]  # 사용할 DB 이름

collection = db["cart"]