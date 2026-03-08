"""
RAG Server — FastAPI entry point.

Run with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import logging

from fastapi import FastAPI

from src.scrapping.routes import router as scrapping_router
from src.indexing.routes import router as indexing_router
from src.retrieval.routes import router as retrieval_router

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="RAG Server",
    version="0.1.0",
    description="Scrapping, indexing & retrieval APIs for MNIT documents.",
)

app.include_router(scrapping_router, prefix="/scrapping", tags=["Scrapping"])
app.include_router(indexing_router, prefix="/indexing", tags=["Indexing"])
app.include_router(retrieval_router, prefix="/retrieval", tags=["Retrieval"])


@app.get("/")
async def root():
    return {"message": "RAG Server is running."}
