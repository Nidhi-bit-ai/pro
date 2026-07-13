from typing import Literal

from pydantic import BaseModel

from src.chat.models import Source


class ConnectionEvent(BaseModel):

    type: Literal["connection"] = "connection"

    message: str


class StatusEvent(BaseModel):

    type: Literal["status"] = "status"

    stage: str

    message: str


class TokenEvent(BaseModel):

    type: Literal["token"] = "token"

    content: str


class SourcesEvent(BaseModel):

    type: Literal["sources"] = "sources"

    sources: list[Source]


class DoneEvent(BaseModel):

    type: Literal["done"] = "done"


class ErrorEvent(BaseModel):

    type: Literal["error"] = "error"

    message: str