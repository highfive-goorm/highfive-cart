# cart/app/database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://root:mongodb_cart@mongodb_cart:27017")
DB_NAME = os.getenv("DB_NAME", "cart")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "cart")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]