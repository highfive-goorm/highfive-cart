from motor.motor_asyncio import AsyncIOMotorClient

import os

from dotenv import load_dotenv, find_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(find_dotenv(usecwd=True))

user = os.getenv('MONGO_USER')
password = os.getenv('MONGO_PASSWORD')
hosts = os.getenv('MONGO_HOSTS')
db_name = os.getenv('MONGO_DB')
replica_set = os.getenv('MONGO_REPLICA_SET')

MONGO_URI = (
    f"mongodb://{user}:{password}@{hosts}/{db_name}?authSource=admin&replicaSet={replica_set}"
)

client = AsyncIOMotorClient(MONGO_URI)

db = client[os.getenv('MONGO_DB')]

collection = db["cart"]


