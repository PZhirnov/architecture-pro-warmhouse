from typing import AsyncGenerator, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import SessionLocal
from common.models import House, Room, UserHouse


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def ensure_house(db: AsyncSession, house_id: int) -> House:
    house = await db.get(House, house_id)
    if house is None:
        raise HTTPException(404, f"House {house_id} not found")
    return house


async def ensure_room_in_house(
    db: AsyncSession, room_id: int, house_id: int
) -> Room:
    room = await db.get(Room, room_id)
    if room is None or room.house_id != house_id:
        raise HTTPException(
            422, f"Room {room_id} does not belong to house {house_id}"
        )
    return room


def house_dict(h: House) -> dict:
    return {
        "id": h.id,
        "name": h.name,
        "address": h.address,
        "created_at": h.created_at,
    }


def room_dict(r: Room) -> dict:
    return {"id": r.id, "house_id": r.house_id, "name": r.name}


def membership_dict(uh: UserHouse) -> dict:
    return {
        "id": uh.id,
        "user_id": uh.user_id,
        "house_id": uh.house_id,
        "room_id": uh.room_id,
        "role": uh.role,
        "is_active": uh.is_active,
        "created_at": uh.created_at,
    }