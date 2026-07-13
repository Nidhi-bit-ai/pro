from fastapi import APIRouter, UploadFile, File, Form

from src.documents.schemas import (
    UploadResponse,
    DeleteDocumentResponse,
    ReindexResponse,
)
from src.documents.services import document_service

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    document_id: int = Form(...),
    file: UploadFile = File(...),
):
    result = await document_service.upload_document(
        document_id=document_id,
        file=file,
    )

    return UploadResponse(
        document_id=result["document_id"],
        stored_filename=result["stored_filename"],
        message="Document uploaded successfully",
    )


@router.delete("/{stored_filename}", response_model=DeleteDocumentResponse)
async def delete_document(
    stored_filename: str,
):
    return await document_service.delete_document(
        stored_filename,
    )


@router.post("/{stored_filename}/reindex", response_model=ReindexResponse)
async def reindex_document(
    stored_filename: str,
):
    return await document_service.reindex_document(
        stored_filename,
    )