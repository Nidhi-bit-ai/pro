"""
Indexing routes — HTTP trigger + WebSocket progress stream + DB status.

Endpoints:
  POST /indexing/start           → kick off indexing in background thread
  GET  /indexing/progress        → single-poll JSON progress snapshot
  WS   /indexing/ws/progress     → stream progress every ~1 s until done
  GET  /indexing/db-status       → vector-store stats (chunks, docs, size)
"""

from __future__ import annotations

import asyncio
import logging
import threading

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse

from .services import IndexingService

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Module-level state for the active indexing job ───────────────────
_active_indexer: IndexingService | None = None
_indexer_lock = threading.Lock()


def _run_indexing(indexer: IndexingService) -> None:
    """Target for the background thread."""
    try:
        result = indexer.index_all()
        logger.info("Indexing finished: %s", result)
    except Exception as e:
        logger.exception("Indexing failed: %s", e)
        with indexer._progress_lock:
            indexer._status = "error"


# ── Start indexing ───────────────────────────────────────────────────

@router.post("/start")
async def start_indexing(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    max_workers: int | None = None,
):
    """
    Kick off PDF indexing in the background.

    Query params:
      - chunk_size:    text splitter chunk size (default 1000)
      - chunk_overlap: overlap between chunks (default 200)
      - max_workers:   thread-pool size (default: number of API keys)
    """
    global _active_indexer

    with _indexer_lock:
        if _active_indexer is not None and _active_indexer._status == "running":
            raise HTTPException(
                status_code=409,
                detail="Indexing is already running. Wait for it to finish or check /progress.",
            )

        indexer = IndexingService(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            max_workers=max_workers,
        )
        _active_indexer = indexer

    t = threading.Thread(target=_run_indexing, args=(indexer,), daemon=True)
    t.start()

    return JSONResponse(
        content={"status": "indexing started"},
        status_code=202,
    )


# ── REST progress (single poll) ─────────────────────────────────────

@router.get("/progress")
async def get_progress():
    """Return the current indexing progress as a single JSON snapshot."""
    if _active_indexer is None:
        raise HTTPException(status_code=404, detail="No indexing job has been started yet.")
    return JSONResponse(content=_active_indexer.get_progress())


# ── WebSocket progress stream ────────────────────────────────────────

@router.websocket("/ws/progress")
async def indexing_progress(websocket: WebSocket):
    """
    Stream indexing progress to the client every ~1 second.

    JSON payload per tick:
        {
            "status":           "idle" | "running" | "completed" | "error",
            "phase":            "processing" | "embedding" | "",
            "total_pdfs":       int,
            "pdfs_processed":   int,
            "pdfs_indexed":     int,
            "pdfs_skipped":     int,
            "chunks_total":     int,
            "chunks_embedded":  int,
            "current_pdf":      str,
            "recent_files":     [str, ...]
        }

    Closes automatically when indexing reaches a terminal state.
    """
    await websocket.accept()
    logger.info("WebSocket client connected for indexing progress.")

    try:
        while True:
            if _active_indexer is None:
                await websocket.send_json({
                    "status": "idle",
                    "message": "No indexing job running. POST /indexing/start to begin.",
                })
                await asyncio.sleep(1)
                continue

            progress = _active_indexer.get_progress()
            await websocket.send_json(progress)

            if progress["status"] in ("completed", "error"):
                logger.info(
                    "Indexing reached terminal state '%s'. Closing WebSocket.",
                    progress["status"],
                )
                break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected (indexing).")
    except Exception as e:
        logger.exception("WebSocket error (indexing): %s", e)
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass


# ── Vector DB status ─────────────────────────────────────────────────

@router.get("/db-status")
async def db_status():
    """
    Return information about the current ChromaDB vector store.

    Response:
        {
            "collection_name": "mnit_docs",
            "total_chunks":    int,
            "total_documents": int,
            "departments":     [str, ...],
            "doc_types":       [str, ...],
            "db_size_mb":      float,
            "db_path":         str
        }
    """
    # We need an IndexingService instance to query the DB.
    # Reuse the active one if available, otherwise create a lightweight one.
    indexer = _active_indexer
    if indexer is None:
        indexer = IndexingService()

    status = indexer.get_db_status()
    if "error" in status:
        raise HTTPException(status_code=500, detail=status["error"])
    return JSONResponse(content=status)
