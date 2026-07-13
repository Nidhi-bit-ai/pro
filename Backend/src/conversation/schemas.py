from datetime import datetime

from pydantic import BaseModel


class ConversationResponse(BaseModel):

    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ConversationListResponse(BaseModel):

    conversations: list[ConversationResponse]


class RenameConversationRequest(BaseModel):

    title: str


class DeleteConversationResponse(BaseModel):

    message: str