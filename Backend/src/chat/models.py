from typing import List, Optional

from pydantic import BaseModel


class Source(BaseModel):
    title: str
    department: str
    source: str


class ChatRequest(BaseModel):
    conversation_id: Optional[int] = None
    message: str


class ChatResponse(BaseModel):
    conversation_id: int
    answer: str
    sources: List[Source]