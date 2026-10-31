from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TelemetryReading
from app.schemas import TelemetryCreate


async def create_reading(db: AsyncSession, data: TelemetryCreate) -> TelemetryReading:
    reading = TelemetryReading(**data.model_dump(exclude_none=True))
    db.add(reading)
    await db.commit()
    await db.refresh(reading)
    return reading


async def list_readings(
    db: AsyncSession,
    device_id: int,
    metric: str | None = None,
    since: datetime | None = None,
    limit: int = 500,
) -> Sequence[TelemetryReading]:
    stmt = select(TelemetryReading).where(TelemetryReading.device_id == device_id)
    if metric:
        stmt = stmt.where(TelemetryReading.metric == metric)
    if since:
        stmt = stmt.where(TelemetryReading.recorded_at >= since)
    stmt = stmt.order_by(TelemetryReading.recorded_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()