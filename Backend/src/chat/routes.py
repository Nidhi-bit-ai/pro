from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.models import User

from src.database.session import get_db

from .models import ChatRequest, ChatResponse
from .services import chat_service


router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    return await chat_service.chat(
        request=request,
        user=current_user,
        db=db,
    )