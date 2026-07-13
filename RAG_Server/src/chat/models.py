# from typing import List

# from pydantic import BaseModel

# from src.generation.models import Source


# class ChatRequest(BaseModel):
#     query: str


# class ChatResponse(BaseModel):
#     answer: str
#     sources: List[Source]

# chat/models.py

from typing import List
from typing import Any

from pydantic import BaseModel

from src.generation.models import Source

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    query: str
    answer: str
    sources: List[Source]

    retrieval_results: list

    retrieved_chunks: int

    model: str