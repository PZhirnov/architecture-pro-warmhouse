from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import SessionLocal


async def get_db():
    async with SessionLocal() as session:
        yield session
