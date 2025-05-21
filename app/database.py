from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://postgres:han00719()@mongodb_cart:27017"
client = AsyncIOMotorClient(MONGO_URI)
db = client['cart']

collection = db['cart']

