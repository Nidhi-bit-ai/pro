from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User


class AuthRepository:

    async def get_by_email(
        self,
        email: str,
        db: AsyncSession,
    ):

        result = await db.execute(
            select(User).where(
                User.email == email
            )
        )

        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        user_id: int,
        db: AsyncSession,
    ):

        result = await db.execute(
            select(User).where(
                User.id == user_id
            )
        )

        return result.scalar_one_or_none()

    async def create_user(
        self,
        user: User,
        db: AsyncSession,
    ):

        db.add(user)

        await db.commit()

        await db.refresh(user)

        return user


auth_repository = AuthRepository()