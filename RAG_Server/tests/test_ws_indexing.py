"""
Quick test: start indexing via HTTP, then stream progress via WebSocket.

Usage:
    python tests/test_ws_indexing.py

Requires the server running:
    cd RAG_Server && uvicorn main:app --port 8000
"""

import asyncio
import json
import httpx
import websockets

SERVER = "http://localhost:8000"
WS_URL = "ws://localhost:8000/indexing/ws/progress"


async def main():
    # 1. Check DB status before
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{SERVER}/indexing/db-status")
        print("=== DB Status (before) ===")
        print(json.dumps(resp.json(), indent=2))
        print()

    # 2. Start indexing
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{SERVER}/indexing/start")
        print(f"POST /indexing/start → {resp.status_code}")
        print(json.dumps(resp.json(), indent=2))
        print()

    # 3. Stream progress via WebSocket
    async with websockets.connect(WS_URL) as ws:
        while True:
            raw = await ws.recv()
            progress = json.loads(raw)
            status = progress.get("status", "?")
            phase = progress.get("phase", "")

            if phase == "processing":
                print(
                    f"[{status:>10} | {phase:>10}]  "
                    f"pdfs={progress['pdfs_processed']}/{progress['total_pdfs']}  "
                    f"indexed={progress['pdfs_indexed']}  "
                    f"skipped={progress['pdfs_skipped']}  "
                    f"current={progress.get('current_pdf', '')}"
                )
            elif phase == "embedding":
                print(
                    f"[{status:>10} | {phase:>10}]  "
                    f"chunks={progress['chunks_embedded']}/{progress['chunks_total']}"
                )
            else:
                print(f"[{status:>10}]  {progress}")

            if progress.get("recent_files"):
                print(f"             recent: {progress['recent_files']}")

            if status in ("completed", "error"):
                print("\nIndexing finished.")
                break

    # 4. Check DB status after
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{SERVER}/indexing/db-status")
        print("\n=== DB Status (after) ===")
        print(json.dumps(resp.json(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
