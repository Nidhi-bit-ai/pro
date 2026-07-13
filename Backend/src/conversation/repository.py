from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.conversation.models import Conversation


class ConversationRepository:

    async def create(
        self,
        conversation: Conversation,
        db: AsyncSession,
    ):

        db.add(conversation)

        await db.commit()
        await db.refresh(conversation)

        return conversation


    async def get(
        self,
        conversation_id: int,
        db: AsyncSession,
    ):

        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
            )
        )

        return result.scalar_one_or_none()


    async def get_user_conversations(
        self,
        user_id: int,
        db: AsyncSession,
    ):

        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
            )
            .order_by(
                Conversation.updated_at.desc(),
            )
        )

        return result.scalars().all()


    async def update(
        self,
        conversation: Conversation,
        db: AsyncSession,
        **kwargs,
    ):

        for key, value in kwargs.items():
            setattr(
                conversation,
                key,
                value,
            )

        await db.commit()
        await db.refresh(conversation)

        return conversation


    async def delete(
        self,
        conversation: Conversation,
        db: AsyncSession,
    ):

        await db.delete(conversation)

        await db.commit()


conversation_repository = ConversationRepository()