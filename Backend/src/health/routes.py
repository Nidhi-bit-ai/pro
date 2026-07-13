from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from src.health.services import health_service

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

@router.get("")
async def health():

    return {
        "status": "healthy",
    }
    
@router.get("/ready")
async def readiness(
    db: AsyncSession = Depends(get_db),
):

    database = await health_service.check_database(db)

    rag = await health_service.check_rag()

    if database and rag:

        return {
            "status": "ready",
            "database": "healthy",
            "rag_server": "healthy",
        }

    return {
        "status": "not_ready",
        "database": (
            "healthy"
            if database
            else "unhealthy"
        ),
        "rag_server": (
            "healthy"
            if rag
            else "unhealthy"
        ),
    }