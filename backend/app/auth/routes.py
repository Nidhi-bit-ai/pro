from fastapi import APIRouter, HTTPException
from app.auth.schemas import RegisterRequest, LoginRequest
from app.auth.services import register_user, login_user

router = APIRouter()


@router.post("/register")
async def register(data: RegisterRequest):
    try:
        return await register_user(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(data: LoginRequest):
    try:
        return await login_user(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
from fastapi import Depends
from app.utils.auth_utils import get_current_user, get_token

@router.post("/logout")
async def logout(token: str = Depends(get_token)):
    await blacklist_collection.insert_one({"token": token})
    return {"message": "Logged out successfully"}