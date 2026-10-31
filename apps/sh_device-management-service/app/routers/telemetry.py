from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import device as crud_device
from app.crud import telemetry as crud_telemetry
from app.deps import get_db
from app.schemas import TelemetryCreate, TelemetryRead

router = APIRouter(prefix="/devices/{device_id}/telemetry", tags=["telemetry"])


@router.get("/", response_model=list[TelemetryRead])
async def list_readings(
    device_id: int,
    metric: str | None = Query(None),
    since: datetime | None = Query(None),
    limit: int = Query(500, le=5000),
    db: AsyncSession = Depends(get_db),
):
    if not await crud_device.get_device(db, device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    return await crud_telemetry.list_readings(
        db, device_id=device_id, metric=metric, since=since, limit=limit
    )


@router.post("/", response_model=TelemetryRead, status_code=status.HTTP_201_CREATED)
async def create_reading(
    device_id: int, payload: TelemetryCreate, db: AsyncSession = Depends(get_db)
):
    if not await crud_device.get_device(db, device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    payload.device_id = device_id
    return await crud_telemetry.create_reading(db, payload)