from fastapi import FastAPI
from sqlalchemy import text

from src.rag.routes import router as rag_router

from src.chat.routes import router as chat_router

from src.database.connection import engine
from src.database.base import Base

# Import models so SQLAlchemy registers them
from src.auth import models
from src.auth.routes import router as auth_router

from src.conversation import models as conversation_models
from src.conversation.routes import router as conversation_router

from src.documents import models as document_models
from src.documents.routes import router as document_router

from src.health.routes import router as health_router

from src.websocket.routes import router as websocket_router

app = FastAPI(
    title="MNIT Backend",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True,},
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router,prefix="/chat",tags=["Chat"])
app.include_router(rag_router)
app.include_router(conversation_router)
app.include_router(document_router)
app.include_router(websocket_router,prefix="/ws",tags=["WebSocket"])

@app.get("/")
def root():

    return {
        "message": "MNIT Backend Running"
    }


@app.on_event("startup")
async def startup():

    # Test database connection
    async with engine.begin() as conn:

        await conn.execute(
            text("SELECT 1")
        )

        # Create tables
        await conn.run_sync(
            Base.metadata.create_all
        )


    print("Database connected successfully")