from fastapi import (
    HTTPException,
    UploadFile,
    status,
)

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User

from src.documents.repository import document_repository
from src.documents.models import Document

from src.rag.services import RAGService


class DocumentService:

    def __init__(
        self,
        rag_service: RAGService,
    ):
        self.rag_service = rag_service


    async def upload(
        self,
        file: UploadFile,
        user: User,
        db: AsyncSession,
    ):

        document = Document(
            user_id=user.id,
            original_filename=file.filename,
            status="PROCESSING",
        )


        document = await document_repository.create(
            document,
            db,
        )


        try:

            upload_response = await self.rag_service.upload_document(
                file=file,
                document_id=document.id,
            )


            await document_repository.update(
                document,
                db,
                status="READY",
                stored_filename=upload_response["stored_filename"],
            )


        except Exception:

            await document_repository.update(
                document,
                db,
                status="FAILED",
            )

            raise


        return document



    async def get(
        self,
        document_id: int,
        user: User,
        db: AsyncSession,
    ):

        document = await document_repository.get(
            document_id,
            db,
        )


        if document is None:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )


        if document.user_id != user.id:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )


        return document



    async def get_user_documents(
        self,
        user: User,
        db: AsyncSession,
    ):

        return await document_repository.get_user_documents(
            user.id,
            db,
        )

    
    async def delete(
        self,
        document_id: int,
        user: User,
        db: AsyncSession,
    ):

        document = await self.get(
            document_id,
            user,
            db,
        )

        await self.rag_service.delete_document(
            stored_filename=document.stored_filename,
        )

        await document_repository.delete(
            document,
            db,
        )

        return {
            "message": "Document deleted successfully",
        }


    async def reindex(
        self,
        document_id: int,
        user: User,
        db: AsyncSession,
    ):

        document = await self.get(
            document_id,
            user,
            db,
        )

        await document_repository.update(
            document,
            db,
            status="PROCESSING",   
        )

        try:

            await self.rag_service.reindex_document(
                stored_filename=document.stored_filename,
            )

            await document_repository.update(
                document,
                db,
                status="READY",
            )

        except Exception:

            await document_repository.update(
                document,
                db,
                status="FAILED",
            )

            raise

        return {
            "message": "Document reindexed successfully",
        }


rag_service = RAGService()

document_service = DocumentService(
    rag_service,
)