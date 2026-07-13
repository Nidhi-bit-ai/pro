from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):

    id: int

    stored_filename: str

    original_filename: str

    status: str

    created_at: datetime

    model_config = {
        "from_attributes": True,
    }
    
    
class DocumentListResponse(BaseModel):

    documents: list[DocumentResponse]


class DocumentUploadResponse(BaseModel):

    pass


class ReindexResponse(BaseModel):

    message: str


class DeleteDocumentResponse(BaseModel):

    message: str