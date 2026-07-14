from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .models import ChatRequest
from .services import ChatService
from .streamer import ChatStreamer


router = APIRouter()

chat_service = ChatService()
chat_streamer = ChatStreamer(chat_service)


@router.post("/", summary="Answer user query using RAG")
async def chat(request: ChatRequest):

    try:

        return chat_service.chat(
            request.query,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post(
    "/stream",
    summary="Stream RAG response",
)
async def chat_stream(
    request: ChatRequest,
):

    return StreamingResponse(
        chat_streamer.stream(
            request.query,
        ),
        media_type="application/x-ndjson",
    )