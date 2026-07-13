from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.rag.services import RAGService


class HealthService:

    def __init__(
        self,
        rag_service: RAGService,
    ):
        self.rag_service = rag_service

    async def check_database(
        self,
        db: AsyncSession,
    ) -> bool:

        try:
            await db.execute(text("SELECT 1"))
            return True

        except Exception:
            return False

    async def check_rag(self) -> bool:

        try:
            await self.rag_service.health()
            return True

        except Exception:
            return False


rag_service = RAGService()

health_service = HealthService(rag_service)