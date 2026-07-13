from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from src.auth.models import User
from src.auth.schemas import RegisterRequest, LoginRequest
from src.auth.repository import auth_repository
from src.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
)


class AuthService:

    async def register(
        self,
        request: RegisterRequest,
        db: AsyncSession,
    ):

        existing_user = await auth_repository.get_by_email(
            request.email,
            db,
        )

        if existing_user:

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=request.email,
            password_hash=hash_password(
                request.password
            ),
        )

        return await auth_repository.create_user(
            user,
            db,
        )

    async def login(
        self,
        request: LoginRequest,
        db: AsyncSession,
    ):

        user = await auth_repository.get_by_email(
            request.email,
            db,
        )

        if (
            user is None
            or not verify_password(
                request.password,
                user.password_hash,
            )
        ):

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        token = create_access_token(
            user.id
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }


auth_service = AuthService()