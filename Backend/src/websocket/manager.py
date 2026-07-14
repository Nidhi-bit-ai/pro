from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from pydantic import BaseModel


class ConnectionManager:

    def __init__(self):

        # conversation_id -> list[WebSocket]
        self.active_connections: dict[int, list[WebSocket]] = (
            defaultdict(list)
        )

    async def connect(
        self,
        conversation_id: int,
        websocket: WebSocket,
    ):

        await websocket.accept()

        self.active_connections[
            conversation_id
        ].append(websocket)

    def disconnect(
        self,
        conversation_id: int,
        websocket: WebSocket,
    ):

        if conversation_id not in self.active_connections:
            return

        if websocket in self.active_connections[
            conversation_id
        ]:
            self.active_connections[
                conversation_id
            ].remove(websocket)

        if not self.active_connections[
            conversation_id
        ]:
            del self.active_connections[
                conversation_id
            ]

    async def send_personal_message(
        self,
        message: Any,
        websocket: WebSocket,
    ):

        if isinstance(message, BaseModel):
            message = message.model_dump()

        await websocket.send_json(message)

    async def broadcast(
        self,
        conversation_id: int,
        message: Any,
    ):

        if conversation_id not in self.active_connections:
            return

        if isinstance(message, BaseModel):
            message = message.model_dump()

        disconnected = []

        for websocket in self.active_connections[
            conversation_id
        ]:

            try:

                await websocket.send_json(
                    message,
                )

            except Exception:

                disconnected.append(
                    websocket,
                )

        for websocket in disconnected:

            self.disconnect(
                conversation_id,
                websocket,
            )


manager = ConnectionManager()