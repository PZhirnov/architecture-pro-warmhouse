from typing import Optional

from fastapi import APIRouter, Depends, Query, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from services.device.deps import get_db
from services.device.schemas import CommandRead, DeviceRead, DeviceCreate, DeviceUpdate
from services.device.services import command_service, device_service

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get(
    "",
    response_model=list[DeviceRead],
    summary="Список устройств (опционально — по дому)",
)
async def list_devices(
    house_id: Optional[int] = Query(None, description="Фильтр по дому"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await device_service.list_devices(
        db, house_id=house_id, limit=limit, offset=offset
    )


@router.post(
    "",
    response_model=DeviceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить устройство",
    description="Создаёт устройство. Проверяет, что дом существует, "
                "а комната (если указана) принадлежит этому дому.",
    responses={
        404: {"description": "House not found"},
        422: {"description": "Room does not belong to house"},
    },
)
async def create_device(
    payload: DeviceCreate,
    db: AsyncSession = Depends(get_db),
):
    return await device_service.create_device(db, payload)



@router.get(
    "/{device_id}",
    response_model=DeviceRead,
    summary="Устройство по id",
    responses={404: {"description": "Device not found"}},
)
async def get_device(device_id: int, db: AsyncSession = Depends(get_db)):
    return await device_service.get_device(db, device_id)


@router.get(
    "/{device_id}/commands",
    response_model=list[CommandRead],
    summary="История команд устройства",
    responses={404: {"description": "Device not found"}},
)
async def list_commands(
    device_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    return await command_service.list_commands(db, device_id, limit=limit)


@router.patch(
    "/{device_id}",
    response_model=DeviceRead,
    summary="Обновить устройство (частично)",
    description="Меняет только переданные поля. Чтобы отвязать от комнаты — "
                'передать `"room_id": null`. `house_id` изменить нельзя.',
    responses={
        404: {"description": "Device not found"},
        422: {"description": "Room does not belong to device's house"},
    },
)
async def update_device(
    device_id: int,
    payload: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await device_service.update_device(db, device_id, payload)



@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить устройство",
    description="Удаляет устройство. Каскадно удаляются связанные "
                "телеметрия и журнал команд (ON DELETE CASCADE).",
    responses={404: {"description": "Device not found"}},
)
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
):
    await device_service.delete_device(db, device_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
