from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.models import User

from src.database.session import get_db

from src.conversation.schemas import (
    ConversationResponse,
    ConversationListResponse,
    RenameConversationRequest,
    DeleteConversationResponse,
)

from src.message.schemas import (
    MessageListResponse,
)

from src.conversation.services import conversation_service


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.post(
    "",
    response_model=ConversationResponse,
)
async def create_conversation(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    return await conversation_service.create(
        user=user,
        db=db,
    )


@router.get(
    "",
    response_model=ConversationListResponse,
)
async def get_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    conversations = await conversation_service.get_user_conversations(
        user=user,
        db=db,
    )

    return {
        "conversations": conversations,
    }


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
async def get_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    return await conversation_service.get(
        conversation_id=conversation_id,
        user=user,
        db=db,
    )


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
async def rename_conversation(
    conversation_id: int,
    request: RenameConversationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    return await conversation_service.rename(
        conversation_id=conversation_id,
        title=request.title,
        user=user,
        db=db,
    )


@router.delete(
    "/{conversation_id}",
    response_model=DeleteConversationResponse,
)
async def delete_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    return await conversation_service.delete(
        conversation_id=conversation_id,
        user=user,
        db=db,
    )


@router.get(
    "/{conversation_id}/messages",
    response_model=MessageListResponse,
)
async def get_messages(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    messages = await conversation_service.get_messages(
        conversation_id=conversation_id,
        user=user,
        db=db,
    )

    return {
        "messages": messages,
    }