from typing import Optional, Sequence

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.models import House, Room, UserHouse
from services.location.utils import (
    ensure_house,
    ensure_room_in_house,
    house_dict,
    membership_dict,
    room_dict,
)


# ============================================================
# Houses
# ============================================================
async def list_houses(
    db: AsyncSession, limit: int = 100, offset: int = 0
) -> list[dict]:
    rows = (
        await db.execute(
            select(House).order_by(House.id).limit(limit).offset(offset)
        )
    ).scalars().all()
    return [house_dict(h) for h in rows]


async def get_house(db: AsyncSession, house_id: int) -> dict:
    return house_dict(await ensure_house(db, house_id))


async def create_house(db: AsyncSession, name: str, address: Optional[str]) -> dict:
    house = House(name=name, address=address)
    db.add(house)
    await db.commit()
    await db.refresh(house)
    return house_dict(house)


async def update_house(
    db: AsyncSession, house_id: int, fields: dict
) -> dict:
    house = await ensure_house(db, house_id)
    for k, v in fields.items():
        setattr(house, k, v)
    await db.commit()
    await db.refresh(house)
    return house_dict(house)


async def delete_house(db: AsyncSession, house_id: int) -> None:
    house = await ensure_house(db, house_id)
    await db.delete(house)
    await db.commit()


# ============================================================
# Rooms
# ============================================================
async def list_rooms(db: AsyncSession, house_id: int) -> list[dict]:
    await ensure_house(db, house_id)
    rows = (
        await db.execute(
            select(Room).where(Room.house_id == house_id).order_by(Room.id)
        )
    ).scalars().all()
    return [room_dict(r) for r in rows]


async def get_room(db: AsyncSession, room_id: int) -> dict:
    room = await db.get(Room, room_id)
    if room is None:
        raise HTTPException(404, f"Room {room_id} not found")
    return room_dict(room)


async def create_room(db: AsyncSession, house_id: int, name: str) -> dict:
    await ensure_house(db, house_id)
    room = Room(house_id=house_id, name=name)
    db.add(room)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(409, f"Room '{name}' already exists in house {house_id}")
    await db.refresh(room)
    return room_dict(room)


async def update_room(
    db: AsyncSession, room_id: int, fields: dict
) -> dict:
    room = await db.get(Room, room_id)
    if room is None:
        raise HTTPException(404, f"Room {room_id} not found")
    for k, v in fields.items():
        setattr(room, k, v)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(409, "Room name conflict in this house")
    await db.refresh(room)
    return room_dict(room)


async def delete_room(db: AsyncSession, room_id: int) -> None:
    room = await db.get(Room, room_id)
    if room is None:
        raise HTTPException(404, f"Room {room_id} not found")
    await db.delete(room)
    await db.commit()


# ============================================================
# Memberships (user_house)
# ============================================================
async def _find_membership(
    db: AsyncSession, user_id: int, house_id: int, room_id: Optional[int]
) -> Optional[UserHouse]:
    stmt = (
        select(UserHouse)
        .where(UserHouse.user_id == user_id)
        .where(UserHouse.house_id == house_id)
    )
    if room_id is None:
        stmt = stmt.where(UserHouse.room_id.is_(None))
    else:
        stmt = stmt.where(UserHouse.room_id == room_id)
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_user_memberships(db: AsyncSession, user_id: int) -> list[dict]:
    rows = (
        await db.execute(
            select(UserHouse)
            .where(UserHouse.user_id == user_id)
            .order_by(UserHouse.id)
        )
    ).scalars().all()
    return [membership_dict(m) for m in rows]


async def list_house_memberships(db: AsyncSession, house_id: int) -> list[dict]:
    await ensure_house(db, house_id)
    rows = (
        await db.execute(
            select(UserHouse)
            .where(UserHouse.house_id == house_id)
            .order_by(UserHouse.id)
        )
    ).scalars().all()
    return [membership_dict(m) for m in rows]


async def create_membership(
    db: AsyncSession,
    user_id: int,
    house_id: int,
    room_id: Optional[int],
    role: str,
) -> dict:
    await ensure_house(db, house_id)
    if room_id is not None:
        await ensure_room_in_house(db, room_id, house_id)

    if await _find_membership(db, user_id, house_id, room_id) is not None:
        raise HTTPException(409, "Membership already exists")

    uh = UserHouse(
        user_id=user_id, house_id=house_id, room_id=room_id, role=role
    )
    db.add(uh)
    await db.commit()
    await db.refresh(uh)
    return membership_dict(uh)


async def update_membership(
    db: AsyncSession, membership_id: int, fields: dict
) -> dict:
    uh = await db.get(UserHouse, membership_id)
    if uh is None:
        raise HTTPException(404, f"Membership {membership_id} not found")

    if "room_id" in fields and fields["room_id"] is not None:
        await ensure_room_in_house(db, fields["room_id"], uh.house_id)

    for k, v in fields.items():
        setattr(uh, k, v)
    await db.commit()
    await db.refresh(uh)
    return membership_dict(uh)


async def delete_membership(db: AsyncSession, membership_id: int) -> None:
    uh = await db.get(UserHouse, membership_id)
    if uh is None:
        raise HTTPException(404, f"Membership {membership_id} not found")
    await db.delete(uh)
    await db.commit()