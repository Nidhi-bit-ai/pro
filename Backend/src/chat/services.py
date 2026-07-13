from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User

from src.rag.services import RAGService

from src.chat.models import (
    ChatRequest,
    ChatResponse,
)

from src.message.models import Message
from src.message.repository import message_repository

from src.conversation.services import conversation_service


class ChatService:

    def __init__(self):

        self.rag_service = RAGService()

    async def chat(
        self,
        request: ChatRequest,
        user: User,
        db: AsyncSession,
    ) -> ChatResponse:

        # Existing conversation
        if request.conversation_id is not None:

            conversation = await conversation_service.get(
                conversation_id=request.conversation_id,
                user=user,
                db=db,
            )

        # New conversation
        else:

            conversation = await conversation_service.create(
                user=user,
                db=db,
            )

                # Save user message
        await message_repository.create(
            Message(
                conversation_id=conversation.id,
                role="user",
                content=request.message,
            ),
            db,
        )

        print("STEP 1 - User message saved")

        # Call RAG Server
        rag_response = await self.rag_service.chat(
            request.message,
        )

        print("STEP 2 - RAG response received")
        print(rag_response)

        # Save assistant message
        await message_repository.create(
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content=rag_response["answer"],
            ),
            db,
        )

        print("STEP 3 - Assistant message saved")

        response = ChatResponse(
            conversation_id=conversation.id,
            answer=rag_response["answer"],
            sources=rag_response["sources"],
        )

        print("STEP 4 - Returning response")

        return response


chat_service = ChatService()