from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import requests
import asyncio

router = APIRouter(prefix="/scraping", tags=["Scraping"])

RAG_URL = "http://127.0.0.1:9000"


# ─────────────────────────────────────────────
# Start scraping (calls RAG server)
# ─────────────────────────────────────────────
@router.post("/start")
async def start_scraping(start_url: str):
    try:
        res = requests.post(f"{RAG_URL}/scrapping/start", params={
            "start_url": start_url
        })

        return res.json()

    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────
# Progress (REST)
# ─────────────────────────────────────────────
@router.get("/progress")
async def progress():
    try:
        res = requests.get(f"{RAG_URL}/scrapping/progress")
        return res.json()

    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────
# WebSocket bridge (backend → RAG)
# ─────────────────────────────────────────────
@router.websocket("/ws")
async def websocket_progress(ws: WebSocket):
    await ws.accept()

    try:
        import websockets

        async with websockets.connect(f"{RAG_URL.replace('http', 'ws')}/scrapping/ws/progress") as rag_ws:
            while True:
                data = await rag_ws.recv()
                await ws.send_text(data)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await ws.send_json({"error": str(e)})