from datetime import datetime
from bson import ObjectId

from app.database.mongodb import users_collection
from app.utils.auth_utils import hash_password, verify_password, create_access_token
from app.auth.schemas import RegisterRequest, LoginRequest


async def register_user(data: RegisterRequest):

    existing_user = await users_collection.find_one({"email": data.email})
    if existing_user:
        raise Exception("Email already registered")

    hashed_pw = hash_password(data.password)

    user_doc = {
        "name": data.name,
        "email": data.email,
        "password": hashed_pw,
        "created_at": datetime.utcnow()
    }

    result = await users_collection.insert_one(user_doc)

    user = {
        "id": str(result.inserted_id),
        "name": data.name,
        "email": data.email,
        "created_at": user_doc["created_at"]
    }

    token = create_access_token({"user_id": str(result.inserted_id)})

    return {
        "user": user,
        "token": {
            "access_token": token,
            "token_type": "bearer"
        }
    }


async def login_user(data: LoginRequest):

    user = await users_collection.find_one({"email": data.email})

    if not user:
        raise Exception("Invalid email or password")

    if not verify_password(data.password, user["password"]):
        raise Exception("Invalid email or password")

    token = create_access_token({"user_id": str(user["_id"])})

    return {
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "created_at": user["created_at"]
        },
        "token": {
            "access_token": token,
            "token_type": "bearer"
        }
    }