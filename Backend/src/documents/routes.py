from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
)

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.models import User

from src.database.session import get_db

from src.documents.schemas import (
    DocumentResponse,
    DocumentListResponse,
    DeleteDocumentResponse,
    ReindexResponse,
)

from src.documents.services import document_service


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentResponse,
)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await document_service.upload(
        file=file,
        user=user,
        db=db,
    )


@router.get(
    "",
    response_model=DocumentListResponse,
)
async def get_documents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    documents = await document_service.get_user_documents(
        user=user,
        db=db,
    )

    return {
        "documents": documents,
    }


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await document_service.get(
        document_id=document_id,
        user=user,
        db=db,
    )


@router.delete(
    "/{document_id}",
    response_model=DeleteDocumentResponse,
)
async def delete_document(
    document_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await document_service.delete(
        document_id=document_id,
        user=user,
        db=db,
    )


@router.post(
    "/{document_id}/reindex",
    response_model=ReindexResponse,
)
async def reindex_document(
    document_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await document_service.reindex(
        document_id=document_id,
        user=user,
        db=db,
    )
    
    
    
    