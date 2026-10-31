from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import device as crud_device
from app.crud import house as crud_house
from app.crud import room as crud_room
from app.deps import get_db
from app.schemas import DeviceCreate, DeviceRead, DeviceUpdate

router = APIRouter(prefix="/houses/{house_id}/devices", tags=["devices"])


# ---------- Утилиты ----------
async def _get_device_or_404(
    db: AsyncSession, house_id: int, device_id: int
):
    device = await crud_device.get_device(db, device_id)
    if not device or device.house_id != house_id:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


async def _validate_room(
    db: AsyncSession, house_id: int, room_id: int | None
) -> None:
    """Проверяет, что комната существует и принадлежит тому же дому."""
    if room_id is None:
        return
    room = await crud_room.get_room(db, room_id)
    if not room or room.house_id != house_id:
        raise HTTPException(
            status_code=422,
            detail=f"Room {room_id} does not belong to house {house_id}",
        )

# Эндпоинты
@router.get("/", response_model=list[DeviceRead])
async def list_devices(
    house_id: int, limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)
):
    if not await crud_house.get_house(db, house_id):
        raise HTTPException(status_code=404, detail="House not found")
    return await crud_device.list_devices_by_house(db, house_id, limit=limit, offset=offset)


@router.post("/", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
async def create_device(house_id: int, payload: DeviceCreate, db: AsyncSession = Depends(get_db)):
    if not await crud_house.get_house(db, house_id):
        raise HTTPException(status_code=404, detail="House not found")
    payload.house_id = house_id
    return await crud_device.create_device(db, payload)


@router.get("/{device_id}", response_model=DeviceRead)
async def get_device(house_id: int, device_id: int, db: AsyncSession = Depends(get_db)):
    device = await crud_device.get_device(db, device_id)
    if not device or device.house_id != house_id:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.patch(
    "/{device_id}",
    response_model=DeviceRead,
    status_code=status.HTTP_200_OK,
    summary="Частичное обновление информации об устройстве",
)
async def patch_device(
    house_id: int,
    device_id: int,
    payload: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Обновляет только переданные поля. Отсутствующие ключи не трогает.
    Чтобы отвязать прибор от комнаты — передайте `"room_id": null`.
    """
    device = await _get_device_or_404(db, house_id, device_id)
    await _validate_room(db, house_id, payload.room_id)
    return await crud_device.update_device(db, device, payload)


@router.put(
    "/{device_id}",
    response_model=DeviceRead,
    status_code=status.HTTP_200_OK,
    summary="Полное обновление информации об устройстве",
)
async def put_device(
    house_id: int,
    device_id: int,
    payload: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Семантически PUT = полная замена. Но так как device.house_id
    менять нельзя (прибор принадлежит дому из URL), все остальные
    поля всё равно опциональны. Если хотите строгий PUT — замените
    тип payload на `DeviceCreate` без house_id и запретите None для
    обязательных полей.
    """
    device = await _get_device_or_404(db, house_id, device_id)
    await _validate_room(db, house_id, payload.room_id)
    return await crud_device.update_device(db, device, payload)
