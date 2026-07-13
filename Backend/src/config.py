from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


HOST = os.getenv("HOST", "0.0.0.0")

PORT = int(os.getenv("PORT", 8000))


RAG_SERVER_URL = os.getenv(
    "RAG_SERVER_URL",
    "http://localhost:8001",
)


# JWT Configuration

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY"
)

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256"
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        60*24,  # 1 day
    )
)


# PostgreSQL Configuration

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)