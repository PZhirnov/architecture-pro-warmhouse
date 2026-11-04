from typing import Optional, Sequence

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from services.device.crud_operation import house, device, room
from services.device.schemas import DeviceRead, DeviceCreate, DeviceUpdate


async def get_device(db: AsyncSession, device_id: int) -> DeviceRead:
    device_res = await device.get(db, device_id)
    if device_res is None:
        raise HTTPException(404, f"Device {device_id} not found")
    return DeviceRead.model_validate(device_res)


async def list_devices(
    db: AsyncSession,
    house_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[DeviceRead]:
    rows = await device.list_all(db, house_id=house_id, limit=limit, offset=offset)
    return [DeviceRead.model_validate(r) for r in rows]


async def list_by_house(
    db: AsyncSession, house_id: int, limit: int = 100, offset: int = 0
) -> Sequence[DeviceRead]:
    if await house.get(db, house_id) is None:
        raise HTTPException(404, f"House {house_id} not found")
    rows = await device.list_by_house(db, house_id, limit=limit, offset=offset)
    return [DeviceRead.model_validate(r) for r in rows]


async def create_device(db: AsyncSession, payload: DeviceCreate) -> DeviceRead:
    # 1. Дом должен существовать
    if await house.get(db, payload.house_id) is None:
        raise HTTPException(404, f"House {payload.house_id} not found")

    # 2. Если указана комната — она должна принадлежать этому же дому
    if payload.room_id is not None:
        target_room = await room.get(db, payload.room_id)
        if target_room is None or target_room.house_id != payload.house_id:
            raise HTTPException(
                422,
                f"Room {payload.room_id} does not belong to house {payload.house_id}",
            )

    # 3. Создаём
    new_device = await device.create(
        db, **payload.model_dump()
    )
    return DeviceRead.model_validate(new_device)


async def delete_device(db: AsyncSession, device_id: int) -> None:
    target_device = await device.get(db, device_id)
    if target_device is None:
        raise HTTPException(404, f"Device {device_id} not found")
    await device.delete(db, target_device)


async def update_device(
    db: AsyncSession, device_id: int, payload: DeviceUpdate
) -> DeviceRead:
    target_device = await device.get(db, device_id)
    if device is None:
        raise HTTPException(404, f"Device {device_id} not found")

    # exclude_unset=True: только переданные клиентом поля.
    # "room_id": null → поле передано явно → отвязка от комнаты.
    fields = payload.model_dump(exclude_unset=True)

    # Если room_id передан и не null — комната должна принадлежать тому же дому
    if "room_id" in fields and fields["room_id"] is not None:
        target_room = await room.get(db, fields["room_id"])
        if room is None or room.house_id != device.house_id:
            raise HTTPException(
                422,
                f"Room {fields['room_id']} does not belong to house {device.house_id}",
            )

    updated = await device.update(db, target_device, **fields)
    return DeviceRead.model_validate(updated)
