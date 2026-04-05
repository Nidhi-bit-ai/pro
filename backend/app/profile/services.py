from bson import ObjectId
from app.database.mongodb import users_collection


async def get_profile(user_id: str):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        return {"error": "User not found"}

    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
    }


async def update_profile(user_id: str, name: str):
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"name": name}}
    )

    return {"message": "Profile updated"}