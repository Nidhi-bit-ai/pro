from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class ChatRequest(BaseModel):
    query: str
    chat_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    chat_id: str


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime


class ChatHistoryResponse(BaseModel):
    chat_id: str
    messages: List[Message]