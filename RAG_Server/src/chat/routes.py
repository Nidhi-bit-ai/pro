from fastapi import APIRouter, HTTPException

from .models import ChatRequest
from .services import ChatService

router = APIRouter()

chat_service = ChatService()


@router.post("/", summary="Answer user query using RAG")
async def chat(request: ChatRequest):

    try:
        response = chat_service.chat(request.query)

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )