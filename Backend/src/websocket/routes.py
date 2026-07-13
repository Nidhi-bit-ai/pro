from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from .manager import manager


router = APIRouter()


@router.websocket("/chat/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: int,
):

    await manager.connect(
        conversation_id,
        websocket,
    )

    try:

        await manager.send_personal_message(
            {
                "type": "connection",
                "message": "Connected successfully",
            },
            websocket,
        )

        while True:

            data = await websocket.receive_text()

            await manager.send_personal_message(
                {
                    "type": "echo",
                    "message": data,
                },
                websocket,
            )

    except WebSocketDisconnect:

        manager.disconnect(
            conversation_id,
            websocket,
        )