from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.models import UserAccount
from services.user.utils import (
    ensure_user,
    hash_password,
    user_dict,
    verify_password,
)


async def _find_by_email(db: AsyncSession, email: str) -> Optional[UserAccount]:
    return (
        await db.execute(select(UserAccount).where(UserAccount.email == email))
    ).scalar_one_or_none()


async def list_users(
    db: AsyncSession, limit: int = 100, offset: int = 0
) -> list[dict]:
    rows = (
        await db.execute(
            select(UserAccount).order_by(UserAccount.id).limit(limit).offset(offset)
        )
    ).scalars().all()
    return [user_dict(u) for u in rows]


async def get_user(db: AsyncSession, user_id: int) -> dict:
    return user_dict(await ensure_user(db, user_id))


async def create_user(
    db: AsyncSession, name: str, email: str, password: str
) -> dict:
    if await _find_by_email(db, email) is not None:
        raise HTTPException(409, f"Email '{email}' already registered")

    user = UserAccount(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role="resident",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user_dict(user)


async def update_user(db: AsyncSession, user_id: int, fields: dict) -> dict:
    user = await ensure_user(db, user_id)

    if "email" in fields and fields["email"] != user.email:
        if await _find_by_email(db, fields["email"]) is not None:
            raise HTTPException(409, f"Email '{fields['email']}' already registered")

    for k, v in fields.items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return user_dict(user)


async def change_password(
    db: AsyncSession,
    user_id: int,
    old_password: Optional[str],
    new_password: str,
) -> None:
    user = await ensure_user(db, user_id)

    # Если старый пароль передан — проверяем.
    # Если не передан — это админский сброс (в проде нужна авторизация).
    if old_password is not None and not verify_password(old_password, user.password_hash):
        raise HTTPException(403, "Old password is incorrect")

    user.password_hash = hash_password(new_password)
    await db.commit()


async def delete_user(db: AsyncSession, user_id: int) -> None:
    user = await ensure_user(db, user_id)
    await db.delete(user)
    await db.commit()
