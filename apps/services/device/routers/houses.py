from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from services.device.deps import get_db
from services.device.schemas import DeviceRead
from services.device.services import device_service

router = APIRouter(prefix="/houses", tags=["devices"])


@router.get(
    "/{house_id}/devices",
    response_model=list[DeviceRead],
    summary="Устройства дома",
    description="Все устройства, привязанные к дому. 404, если дом не существует.",
    responses={404: {"description": "House not found"}},
)
async def list_devices_by_house(
    house_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await device_service.list_by_house(
        db, house_id, limit=limit, offset=offset
    )
