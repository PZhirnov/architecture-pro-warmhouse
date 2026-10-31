from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device
from app.schemas import DeviceCreate, DeviceUpdate


async def get_device(db: AsyncSession, device_id: int) -> Device | None:
    return await db.get(Device, device_id)


async def list_devices_by_house(
    db: AsyncSession, house_id: int, limit: int = 100, offset: int = 0
) -> Sequence[Device]:
    result = await db.execute(
        select(Device)
        .where(Device.house_id == house_id)
        .order_by(Device.id)
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


async def create_device(db: AsyncSession, data: DeviceCreate) -> Device:
    device = Device(**data.model_dump())
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


async def update_device(
    db: AsyncSession, device: Device, data: DeviceUpdate
) -> Device:
    """
    Частичное обновление. Применяет только переданные поля
    (exclude_unset=True): если клиент не передал room_id — останется как было;
    если передал "room_id": null — отвяжет от комнаты.
    """
    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(device, field, value)

    await db.commit()
    await db.refresh(device)
    return device


async def set_online(db: AsyncSession, device: Device, online: bool) -> Device:
    device.online = online
    if online:
        from datetime import datetime, timezone
        device.last_seen_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(device)
    return device