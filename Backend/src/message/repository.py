from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.message.models import Message


class MessageRepository:

    async def create(
        self,
        message: Message,
        db: AsyncSession,
    ):

        db.add(message)

        await db.commit()
        await db.refresh(message)

        return message


    async def get_conversation_messages(
        self,
        conversation_id: int,
        db: AsyncSession,
    ):

        result = await db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
            )
            .order_by(
                Message.created_at.asc(),
            )
        )

        return result.scalars().all()


message_repository = MessageRepository()