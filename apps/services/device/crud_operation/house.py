from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from common.models import House


async def get(db: AsyncSession, house_id: int) -> Optional[House]:
    return await db.get(House, house_id)
