from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import Room

async def get(db: AsyncSession, room_id: int) -> Optional[Room]:
    return await db.get(Room, room_id)
