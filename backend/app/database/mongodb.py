from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"

client = AsyncIOMotorClient(MONGO_URI)

db = client["mnit_rag"]

users_collection = db["users"]
chats_collection = db["chats"]
messages_collection = db["messages"]
documents_collection = db["documents"]
blacklist_collection = db["blacklisted_tokens"]