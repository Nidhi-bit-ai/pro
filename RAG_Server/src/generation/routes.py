from fastapi import APIRouter, HTTPException
from langchain_core.documents import Document

from .models import GenerationRequest
from .services import QAService

router = APIRouter()

qa = QAService()


@router.post("/")
def generate(req: GenerationRequest):

    try:

        documents = [
            Document(
                page_content=doc["page_content"],
                metadata=doc["metadata"],
            )
            for doc in req.documents
        ]

        return qa.generate(
            query=req.query,
            documents=documents,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )