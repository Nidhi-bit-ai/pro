"""
Retrieval routes — REST query + WebSocket live-progress query.

Endpoints:
  POST /retrieval/query           → run full RAG pipeline, return results
  WS   /retrieval/ws/query        → stream per-stage progress, then results
  GET  /retrieval/status           → vector store / BM25 health info
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from queue import Queue, Empty
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .services import RetrievalService

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Lazy singleton — only created on first use so startup is fast ────
_service: RetrievalService | None = None
_service_lock = threading.Lock()


def _get_service() -> RetrievalService:
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = RetrievalService()
    return _service


# ── Request / response models ────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(..., description="User search query", min_length=1)
    k_fetch: int = Field(10, description="Number of results per search method", ge=1, le=50)
    top_n: int = Field(5, description="Max PDFs to return after reranking", ge=1, le=20)


# ── POST /query — synchronous retrieval ──────────────────────────────

@router.post("/query")
async def retrieval_query(body: QueryRequest):
    """
    Run the full 6-stage RAG retrieval pipeline and return results.

    This is a blocking call — the response is sent once all stages
    (query analysis → multi-query → hybrid search → RRF → rerank → dedup)
    are complete.  Typical latency: 3-15 s depending on LLM providers.
    """
    svc = _get_service()

    # Run the blocking pipeline in a thread so we don't block the event loop.
    result: dict = {}
    error: str | None = None

    def _run():
        nonlocal result, error
        try:
            result = svc.retrieve(body.query, k_fetch=body.k_fetch, top_n=body.top_n)
        except Exception as e:
            logger.exception("Retrieval failed: %s", e)
            error = str(e)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join()  # wait (we're already async, but join is fine in a threadpool)

    if error:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {error}")

    return JSONResponse(content=result)


# ── WebSocket /ws/query — live-progress retrieval ─────────────────────

@router.websocket("/ws/query")
async def retrieval_ws(websocket: WebSocket):
    """
    Run the retrieval pipeline with live per-stage progress.

    Client sends a JSON message to start:
        { "query": "...", "k_fetch": 10, "top_n": 5 }

    Server streams JSON messages for each stage:
        { "type": "progress", "stage": "query_analysis", "detail": "..." }
        { "type": "progress", "stage": "multi_query_done", "detail": "[...]" }
        ...
        { "type": "result", "data": { ... full result dict ... } }

    or on error:
        { "type": "error", "message": "..." }

    The socket is closed after sending the result or error.
    """
    await websocket.accept()
    logger.info("WebSocket client connected for retrieval.")

    try:
        # 1. Wait for the client's query message
        raw = await websocket.receive_text()
        try:
            msg = json.loads(raw)
            query = msg["query"]
            k_fetch = msg.get("k_fetch", 10)
            top_n = msg.get("top_n", 5)
        except (json.JSONDecodeError, KeyError) as e:
            await websocket.send_json({"type": "error", "message": f"Invalid request: {e}"})
            return

        svc = _get_service()

        # 2. Set up a thread-safe queue for stage progress events
        progress_queue: Queue[dict] = Queue()

        def _on_progress(stage: str, detail: str = ""):
            progress_queue.put({"type": "progress", "stage": stage, "detail": detail})

        result_holder: dict = {}
        error_holder: list = []

        def _run():
            try:
                result_holder["data"] = svc.retrieve(
                    query, k_fetch=k_fetch, top_n=top_n, on_progress=_on_progress,
                )
            except Exception as e:
                error_holder.append(str(e))
            finally:
                progress_queue.put(None)  # sentinel

        t = threading.Thread(target=_run, daemon=True)
        t.start()

        # 3. Drain the queue and forward progress to the WebSocket
        while True:
            # Non-blocking poll so we can use asyncio.sleep
            try:
                item = progress_queue.get_nowait()
            except Empty:
                await asyncio.sleep(0.15)
                continue

            if item is None:
                # Pipeline finished
                break

            await websocket.send_json(item)

        # 4. Send final result or error
        if error_holder:
            await websocket.send_json({"type": "error", "message": error_holder[0]})
        elif "data" in result_holder:
            await websocket.send_json({"type": "result", "data": result_holder["data"]})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected (retrieval).")
    except Exception as e:
        logger.exception("WebSocket error (retrieval): %s", e)
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass


# ── GET /status — service health ──────────────────────────────────────

@router.get("/status")
async def retrieval_status():
    """
    Return information about the retrieval service.

    Response:
        {
            "vector_store_chunks": int,
            "bm25_enabled":       bool,
            "bm25_documents":     int,
            "groq_keys":          int,
            "google_keys":        int
        }
    """
    svc = _get_service()
    chunk_count = 0
    try:
        chunk_count = svc._vectorstore._collection.count()
    except Exception:
        pass

    bm25_count = 0
    if svc._bm25 is not None:
        try:
            bm25_count = len(svc._bm25.docs)
        except Exception:
            pass

    from .services import GROQ_API_KEYS, GOOGLE_API_KEYS

    return JSONResponse(content={
        "vector_store_chunks": chunk_count,
        "bm25_enabled": svc._bm25 is not None,
        "bm25_documents": bm25_count,
        "groq_keys": len(GROQ_API_KEYS),
        "google_keys": len(GOOGLE_API_KEYS),
    })
