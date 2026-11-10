from typing import AsyncGenerator

from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import SessionLocal
from common.models import UserAccount

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


async def ensure_user(db: AsyncSession, user_id: int) -> UserAccount:
    user = await db.get(UserAccount, user_id)
    if user is None:
        raise HTTPException(404, f"User {user_id} not found")
    return user


def user_dict(u: UserAccount) -> dict:
    """Возвращает пользователя БЕЗ password_hash."""
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "role": u.role,
        "created_at": u.created_at,
    }
