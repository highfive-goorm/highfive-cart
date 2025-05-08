from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URI)
db: Database = client["cart"]  # 사용할 DB 이름

