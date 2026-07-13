# src/rag/models.py

from typing import List

from pydantic import BaseModel


class Source(BaseModel):
    title: str
    department: str
    source: str
    page: int


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]