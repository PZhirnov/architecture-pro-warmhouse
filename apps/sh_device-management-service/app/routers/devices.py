from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import device as crud_device
from app.crud import house as crud_house
from app.deps import get_db
from app.schemas import DeviceCreate, DeviceRead

router = APIRouter(prefix="/houses/{house_id}/devices", tags=["devices"])


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