from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from src.auth.dependencies import get_user_from_token
from src.chat.models import ChatRequest
from src.chat.services import chat_service
from src.database.connection import AsyncSessionLocal

from .manager import manager


router = APIRouter()


@router.websocket("/chat/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: int,
):

    token = websocket.query_params.get("token")

    if token is None:

        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Authentication token missing",
        )
        return

    try:

        async with AsyncSessionLocal() as db:

            # Authenticate BEFORE accepting websocket
            user = await get_user_from_token(
                token,
                db,
            )
            # print("=" * 50)
            # print("Authenticated User")
            # print("ID:", user.id)
            # print("Email:", user.email)
            # print("=" * 50)

            await manager.connect(
                conversation_id,
                websocket,
            )

            await manager.send_personal_message(
                {
                    "type": "connection",
                    "message": "Connected successfully",
                },
                websocket,
            )

            while True:

                question = await websocket.receive_text()

                request = ChatRequest(
                    conversation_id=conversation_id,
                    message=question,
                )

                async for event in chat_service.stream_chat(
                    request=request,
                    user=user,
                    db=db,
                ):

                    await manager.send_personal_message(
                        event,
                        websocket,
                    )

    except WebSocketDisconnect:

        manager.disconnect(
            conversation_id,
            websocket,
        )

    except Exception as e:

        try:

            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason=str(e),
            )

        except Exception:
            pass

        manager.disconnect(
            conversation_id,
            websocket,
        )