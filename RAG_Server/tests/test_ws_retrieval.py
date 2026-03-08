"""
Quick test: send a retrieval query via WebSocket and stream progress.

Usage:
    python tests/test_ws_retrieval.py

Requires the server running:
    cd RAG_Server && uvicorn main:app --port 8000
"""

import asyncio
import json
import websockets

WS_URL = "ws://localhost:8000/retrieval/ws/query"


async def main():
    async with websockets.connect(WS_URL) as ws:
        # Send the query
        request = {"query": "chemical engineering notices 2024", "top_n": 3}
        print(f"Sending: {json.dumps(request)}\n")
        await ws.send(json.dumps(request))

        # Stream responses
        while True:
            raw = await ws.recv()
            msg = json.loads(raw)
            msg_type = msg.get("type", "?")

            if msg_type == "progress":
                print(f"  [{msg['stage']:>25}]  {msg.get('detail', '')}")

            elif msg_type == "result":
                data = msg["data"]
                print(f"\n=== RESULTS ===")
                print(f"Query   : {data['query']}")
                print(f"Filters : {data['filters_applied']}")
                print(f"Queries : {data['generated_queries']}")
                for i, r in enumerate(data["results"], 1):
                    print(f"\n  {i}. {r['title']}")
                    print(f"     File: {r['filename']} | Dept: {r['dept']} | Type: {r['doc_type']} | Year: {r['year']}")
                break

            elif msg_type == "error":
                print(f"\nERROR: {msg['message']}")
                break

            else:
                print(f"  [unknown] {msg}")


if __name__ == "__main__":
    asyncio.run(main())
