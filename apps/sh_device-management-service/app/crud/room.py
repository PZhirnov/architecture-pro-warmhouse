from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Room
from app.schemas import RoomCreate


async def get_room(db: AsyncSession, room_id: int) -> Room | None:
    return await db.get(Room, room_id)


async def list_rooms_by_house(
    db: AsyncSession, house_id: int, limit: int = 100, offset: int = 0
) -> Sequence[Room]:
    result = await db.execute(
        select(Room)
        .where(Room.house_id == house_id)
        .order_by(Room.id)
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


async def create_room(db: AsyncSession, data: RoomCreate) -> Room:
    room = Room(**data.model_dump())
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


async def delete_room(db: AsyncSession, room: Room) -> None:
    await db.delete(room)
    await db.commit()
