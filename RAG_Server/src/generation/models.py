from typing import List, Dict, Any

from pydantic import BaseModel


class Source(BaseModel):
    title: str
    department: str
    source: str


class GenerationRequest(BaseModel):
    query: str

    # Retrieved documents from RetrievalService
    documents: List[Dict[str, Any]]


class AnswerResponse(BaseModel):
    answer: str
    sources: List[Source]