from datetime import datetime

from pydantic import BaseModel


class MessageResponse(BaseModel):

    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class MessageListResponse(BaseModel):

    messages: list[MessageResponse]