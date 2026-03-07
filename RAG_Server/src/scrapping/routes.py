"""
Scrapping routes — HTTP trigger + WebSocket progress stream.

Flow:
  1. Client POSTs /scrapping/start  → crawl begins in a background thread,
     response returns immediately with status.
  2. Client opens  ws://.../scrapping/ws/progress → receives a JSON progress
     object every ~1 s until the crawl finishes, then the socket is closed.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from urllib.parse import urlparse

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse

from .services import CrawlService

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Module-level state for the active crawl ──────────────────────────
_active_crawl: CrawlService | None = None
_crawl_lock = threading.Lock()           # guards _active_crawl


def _run_crawl(crawler: CrawlService, start_url: str) -> None:
    """Target for the background thread — just calls .start()."""
    try:
        result = crawler.start(start_url)
        logger.info("Crawl finished: %s", result)
    except Exception as e:
        logger.exception("Crawl failed: %s", e)
        crawler._status = "error"


# ── Health ────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    return JSONResponse(content={"status": "ok"}, status_code=200)


# ── Start crawl ──────────────────────────────────────────────────────

@router.post("/start")
async def start_scrapping(
    start_url: str,
    max_download: int = 100,
    num_workers: int = 5,
):
    """
    Kick off a crawl in the background.

    Query params:
      - start_url:    root URL to begin crawling (e.g. https://www.mnit.ac.in)
      - max_download:  maximum PDFs to download (default 100)
      - num_workers:   thread-pool size (default 5)
    """
    global _active_crawl

    with _crawl_lock:
        if _active_crawl is not None and _active_crawl._status == "running":
            raise HTTPException(
                status_code=409,
                detail="A crawl is already running. Wait for it to finish or check /progress.",
            )

        # Extract bare domain from the URL so _is_valid_url works correctly.
        # e.g. "https://www.mnit.ac.in/dept/cse" → "mnit.ac.in"
        parsed = urlparse(start_url)
        domain = parsed.netloc or parsed.path  # handle with/without scheme
        # Strip "www." prefix for a broader match
        domain = domain.removeprefix("www.")

        crawler = CrawlService(
            allowed_domain=domain,
            max_downloads=max_download,
            num_threads=num_workers,
        )
        _active_crawl = crawler

    # Start the blocking crawl in a daemon thread so the HTTP response
    # returns immediately.
    t = threading.Thread(
        target=_run_crawl,
        args=(crawler, start_url),
        daemon=True,
    )
    t.start()

    return JSONResponse(
        content={"status": "scrapping started", "max_download": max_download},
        status_code=202,
    )


# ── REST progress (single poll) ─────────────────────────────────────

@router.get("/progress")
async def get_progress():
    """Return the current crawl progress as a single JSON snapshot."""
    if _active_crawl is None:
        raise HTTPException(status_code=404, detail="No crawl has been started yet.")
    return JSONResponse(content=_active_crawl.get_progress())


# ── WebSocket progress stream ────────────────────────────────────────

@router.websocket("/ws/progress")
async def scrapping_progress(websocket: WebSocket):
    """
    Stream crawl progress to the client every ~1 second.

    The server sends a JSON object on each tick:
        {
            "status":          "running" | "completed" | "idle" | "error",
            "pages_visited":   int,
            "pdfs_found":      int,
            "pdfs_downloaded":  int,
            "max_downloads":   int,
            "recent_files":    [str, ...],   # last 5 filenames
            "current_url":     str
        }

    The socket is closed automatically once the crawl reaches a terminal
    state ("completed" or "error").
    """
    await websocket.accept()
    logger.info("WebSocket client connected for progress updates.")

    try:
        while True:
            if _active_crawl is None:
                await websocket.send_json({
                    "status": "idle",
                    "message": "No crawl running. POST /scrapping/start to begin.",
                })
                # Keep the socket open so the client doesn't have to
                # reconnect once the crawl starts.
                await asyncio.sleep(1)
                continue

            progress = _active_crawl.get_progress()
            await websocket.send_json(progress)

            # If the crawl has finished, send one final message and close.
            if progress["status"] in ("completed", "error"):
                logger.info("Crawl reached terminal state '%s'. Closing WebSocket.", progress["status"])
                break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.exception("WebSocket error: %s", e)
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass  # already closed