"""
Quick test: start a crawl via HTTP, then stream progress via WebSocket.

Usage:
    python tests/test_ws_progress.py

Requires the server to be running:
    cd RAG_Server && uvicorn main:app --port 8000
"""

import asyncio
import json
import httpx
import websockets

SERVER = "http://localhost:8000"
WS_URL = "ws://localhost:8000/scrapping/ws/progress"

START_URL = "https://www.mnit.ac.in"
MAX_DOWNLOAD = 5  # small number for a quick test


async def main():
    # 1. Kick off the crawl via HTTP POST
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{SERVER}/scrapping/start",
            params={
                "start_url": START_URL,
                "max_download": MAX_DOWNLOAD,
                "num_workers": 3,
            },
        )
        print(f"POST /scrapping/start → {resp.status_code}")
        print(json.dumps(resp.json(), indent=2))
        print()

    # 2. Open a WebSocket and stream progress until done
    async with websockets.connect(WS_URL) as ws:
        while True:
            raw = await ws.recv()
            progress = json.loads(raw)
            status = progress.get("status", "?")
            print(
                f"[{status.upper():>10}]  "
                f"pages={progress.get('pages_visited', 0):>4}  "
                f"pdfs_found={progress.get('pdfs_found', 0):>3}  "
                f"downloaded={progress.get('pdfs_downloaded', 0):>3}  "
                f"url={progress.get('current_url', '')[:80]}"
            )
            if progress.get("recent_files"):
                print(f"             recent: {progress['recent_files']}")

            if status in ("completed", "error"):
                print("\nCrawl finished.")
                break


if __name__ == "__main__":
    asyncio.run(main())
