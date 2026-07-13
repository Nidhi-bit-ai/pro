from fastapi import (
    HTTPException,
    status,
)

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User

from src.conversation.models import Conversation
from src.conversation.repository import conversation_repository

from src.message.repository import message_repository


class ConversationService:

    async def create(
        self,
        user: User,
        db: AsyncSession,
    ):

        conversation = Conversation(
            user_id=user.id,
        )

        return await conversation_repository.create(
            conversation,
            db,
        )


    async def get(
        self,
        conversation_id: int,
        user: User,
        db: AsyncSession,
    ):

        conversation = await conversation_repository.get(
            conversation_id,
            db,
        )

        if conversation is None:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        if conversation.user_id != user.id:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        return conversation


    async def get_user_conversations(
        self,
        user: User,
        db: AsyncSession,
    ):

        return await conversation_repository.get_user_conversations(
            user.id,
            db,
        )


    async def rename(
        self,
        conversation_id: int,
        title: str,
        user: User,
        db: AsyncSession,
    ):

        conversation = await self.get(
            conversation_id,
            user,
            db,
        )

        return await conversation_repository.update(
            conversation,
            db,
            title=title,
        )


    async def delete(
        self,
        conversation_id: int,
        user: User,
        db: AsyncSession,
    ):

        conversation = await self.get(
            conversation_id,
            user,
            db,
        )

        await conversation_repository.delete(
            conversation,
            db,
        )

        return {
            "message": "Conversation deleted successfully",
        }


    async def get_messages(
        self,
        conversation_id: int,
        user: User,
        db: AsyncSession,
    ):

        await self.get(
            conversation_id,
            user,
            db,
        )

        return await message_repository.get_conversation_messages(
            conversation_id,
            db,
        )


conversation_service = ConversationService()