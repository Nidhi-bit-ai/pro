from fastapi import APIRouter, Depends

from app.profile.services import get_profile, update_profile
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/")
async def profile(user=Depends(get_current_user)):
    return await get_profile(user["user_id"])


@router.put("/")
async def update(name: str, user=Depends(get_current_user)):
    return await update_profile(user["user_id"], name)