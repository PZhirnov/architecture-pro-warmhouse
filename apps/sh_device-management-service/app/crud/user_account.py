from typing import Sequence

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserAccount
from app.schemas import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_user(db: AsyncSession, user_id: int) -> UserAccount | None:
    return await db.get(UserAccount, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> UserAccount | None:
    result = await db.execute(select(UserAccount).where(UserAccount.email == email))
    return result.scalar_one_or_none()


async def list_users(db: AsyncSession, limit: int = 100, offset: int = 0) -> Sequence[UserAccount]:
    result = await db.execute(
        select(UserAccount).order_by(UserAccount.id).limit(limit).offset(offset)
    )
    return result.scalars().all()


async def create_user(db: AsyncSession, data: UserCreate) -> UserAccount:
    user = UserAccount(
        name=data.name,
        email=data.email,
        role=data.role,
        password_hash=pwd_context.hash(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: UserAccount) -> None:
    await db.delete(user)
    await db.commit()