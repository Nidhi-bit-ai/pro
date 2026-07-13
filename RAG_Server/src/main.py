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
from src.generation.routes import router as generation_router
from src.chat.routes import router as chat_router
from src.documents.routes import router as document_router

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
app.include_router(generation_router, prefix="/generation", tags=["Generation"])
app.include_router(chat_router,prefix="/chat",tags=["Chat"])
app.include_router(document_router)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "RAG_Server",
        "version": "0.1.0",
    }
    
@app.get("/")
async def root():
    return {"message": "RAG Server is running."}
