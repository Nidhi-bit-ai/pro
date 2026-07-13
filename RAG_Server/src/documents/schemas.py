from pydantic import BaseModel


class UploadResponse(BaseModel):

    document_id: int

    stored_filename: str

    message: str
    
    
class DeleteDocumentResponse(BaseModel):
    message: str


class ReindexResponse(BaseModel):
    message: str