import asyncio
import json
import websockets

TOKEN = "PASTE_YOUR_JWT_HERE"

URI = f"ws://127.0.0.1:8000/ws/chat/1?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzg0MDMzNDIwfQ.KY39qjOFYnaU2fHDdKMT5ffJlQ5jQcMYKvuC0OELkMY"


async def main():

    async with websockets.connect(URI) as websocket:

        print(await websocket.recv())

        await websocket.send("what is AIDE?")

        while True:

            message = await websocket.recv()

            print(json.loads(message))


asyncio.run(main())