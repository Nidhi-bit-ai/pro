from fastapi import APIRouter, UploadFile, File
from app.documents.services import query_custom_docs

router = APIRouter(prefix="/docs", tags=["Documents"])


@router.post("/query")
async def query_docs(file: UploadFile = File(...), query: str = ""):
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    return query_custom_docs(query, text)