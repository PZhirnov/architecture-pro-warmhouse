from typing import Optional

from fastapi import APIRouter, Depends, Query

from services.bff.clients.telemetry_client import TelemetryClient
from services.bff.deps import get_telemetry_client

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


@router.get(
    "/stats/all",
    summary="Статистика по всем датчикам за всё время (прокси)",
    description="Агрегаты avg/min/max/count по каждой метрике каждого датчика. "
                "Сервис telemetry не знает про дома/комнаты — только device_id.",
)
async def get_all_stats(
    device_id: Optional[int] = Query(None, gt=0, description="Только конкретный датчик"),
    metric: Optional[str] = Query(None, min_length=1, description="Только конкретная метрика"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    c: TelemetryClient = Depends(get_telemetry_client),
):
    return await c.get_all_stats(
        device_id=device_id, metric=metric, limit=limit, offset=offset
    )


@router.get(
    "/stats/summary",
    summary="Сводная статистика по метрикам (прокси)",
    description="avg/min/max/count по каждой метрике среди всех датчиков.",
)
async def get_summary(
    metric: Optional[str] = Query(None, min_length=1),
    c: TelemetryClient = Depends(get_telemetry_client),
):
    return await c.get_summary(metric=metric)


@router.get(
    "/{device_id}/average",
    summary="Средние показания датчика за период или на дату (прокси)",
    description="""
Один из режимов:
- `?date=YYYY-MM-DD` — за конкретный день (UTC)
- `?start=...&end=...` — произвольный период (ISO 8601)
- без параметров — последние 24 часа
""",
)
async def get_average(
    device_id: int,
    metric: Optional[str] = Query(None),
    date: Optional[str] = Query(None, alias="date", description="YYYY-MM-DD"),
    start: Optional[str] = Query(None, description="ISO 8601"),
    end: Optional[str] = Query(None, description="ISO 8601"),
    c: TelemetryClient = Depends(get_telemetry_client),
):
    return await c.get_average(
        device_id, metric=metric, date=date, start=start, end=end
    )


@router.get(
    "/{device_id}",
    summary="Сырые показания датчика (прокси)",
)
async def get_telemetry(
    device_id: int,
    metric: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    c: TelemetryClient = Depends(get_telemetry_client),
):
    return await c.get_telemetry(device_id, metric=metric, limit=limit)
