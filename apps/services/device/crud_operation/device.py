from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.models import Device



async def get(db: AsyncSession, device_id: int) -> Optional[Device]:
    return await db.get(Device, device_id)


async def list_by_house(
    db: AsyncSession, house_id: int, limit: int = 100, offset: int = 0
) -> Sequence[Device]:
    return (
        await db.execute(
            select(Device)
            .where(Device.house_id == house_id)
            .order_by(Device.id)
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()


async def list_all(
    db: AsyncSession,
    house_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[Device]:
    stmt = select(Device).order_by(Device.id).limit(limit).offset(offset)
    if house_id is not None:
        stmt = stmt.where(Device.house_id == house_id)
    return (await db.execute(stmt)).scalars().all()


async def create(db: AsyncSession, **fields) -> Device:
    device = Device(**fields)
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


async def update(db: AsyncSession, device: Device, **fields) -> Device:
    for k, v in fields.items():
        setattr(device, k, v)
    await db.commit()
    await db.refresh(device)
    return device


async def delete(db: AsyncSession, device: Device) -> None:
    await db.delete(device)
    await db.commit()


