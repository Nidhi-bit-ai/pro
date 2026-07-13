from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.documents.models import Document


class DocumentRepository:

    async def create(
        self,
        document: Document,
        db: AsyncSession,
    ):

        db.add(document)

        await db.commit()

        await db.refresh(document)

        return document

    async def get(
        self,
        document_id: int,
        db: AsyncSession,
    ):

        result = await db.execute(
            select(Document).where(
                Document.id == document_id
            )
        )

        return result.scalar_one_or_none()

    async def get_user_documents(
        self,
        user_id: int,
        db: AsyncSession,
    ):

        result = await db.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )

        return result.scalars().all()

    async def delete(
        self,
        document: Document,
        db: AsyncSession,
    ):

        await db.delete(document)

        await db.commit()

    async def update(
        self,
        document: Document,
        db: AsyncSession,
        **kwargs,
    ) -> Document:

        for key, value in kwargs.items():

            setattr(
                document,
                key,
                value,
            )

        await db.commit()

        await db.refresh(
            document,
        )

        return document


document_repository = DocumentRepository()