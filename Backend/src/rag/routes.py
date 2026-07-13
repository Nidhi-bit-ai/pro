from fastapi import APIRouter

from .client import RAGClient

router = APIRouter(prefix="/rag", tags=["RAG"])

client = RAGClient()


@router.get("/health")
async def rag_health():

    return await client.health()