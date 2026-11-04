from datetime import date as date_type, datetime, time, timedelta, timezone
from typing import Optional

from fastapi import  HTTPException, Query, APIRouter
from sqlalchemy import func, select

from common.database import SessionLocal
from common.models import Device, TelemetryReading

from services.telemetry.utils import _ensure_utc


router = APIRouter(prefix="/telemetry", tags=["telemetry"])


# Состояние сервиса
@router.get("/health", description="Проверка состояния")
async def health():
    return {"service": "telemetry", "status": "ok"}


# Статистика по ВСЕМ датчикам за весь период
# ВАЖНО: объявлять ДО /{device_id}, иначе "stats" попадёт в int
# ============================================================
@router.get(
    "/stats/all",
    summary="Статистика по всем датчикам за весь период",
    description="""
Для каждого `device_id` возвращает **avg / min / max / count** по каждой метрике
за всё время наблюдений (без фильтра по времени).

Сервис не знает про `Device`, `House`, `Room` — работает только с `telemetry_reading`.
Если по какому-то `device_id` нет данных — его нет в ответе.

Фильтры:
- `metric` — только конкретная метрика
- `device_id` — только конкретный датчик
- `limit` / `offset` — пагинация по `device_id`
""",
)
async def get_all_devices_stats(
    device_id: Optional[int] = Query(None, gt=0, description="Фильтр по датчику"),
    metric: Optional[str] = Query(None, min_length=1, description="Фильтр по метрике"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    async with SessionLocal() as db:
        # --- 1. Уникальные device_id с пагинацией ---
        dev_stmt = select(TelemetryReading.device_id).distinct()
        if device_id is not None:
            dev_stmt = dev_stmt.where(TelemetryReading.device_id == device_id)

        total = (
            await db.execute(
                select(func.count()).select_from(dev_stmt.subquery())
            )
        ).scalar_one()

        device_ids = (
            await db.execute(
                dev_stmt.order_by(TelemetryReading.device_id)
                       .limit(limit)
                       .offset(offset)
            )
        ).scalars().all()

        if not device_ids:
            return {"total": total, "count": 0, "offset": offset, "limit": limit, "devices": []}

        # --- 2. Агрегаты по этим device_id ---
        stats_stmt = (
            select(
                TelemetryReading.device_id,
                TelemetryReading.metric,
                func.avg(TelemetryReading.value).label("avg"),
                func.min(TelemetryReading.value).label("min"),
                func.max(TelemetryReading.value).label("max"),
                func.count(TelemetryReading.id).label("count"),
                func.max(TelemetryReading.unit).label("unit"),
                func.min(TelemetryReading.recorded_at).label("first_at"),
                func.max(TelemetryReading.recorded_at).label("last_at"),
            )
            .where(TelemetryReading.device_id.in_(device_ids))
        )
        if metric:
            stats_stmt = stats_stmt.where(TelemetryReading.metric == metric)

        stats_stmt = (
            stats_stmt
            .group_by(TelemetryReading.device_id, TelemetryReading.metric)
            .order_by(TelemetryReading.device_id, TelemetryReading.metric)
        )
        rows = (await db.execute(stats_stmt)).all()

    # --- 3. Группировка по device_id ---
    by_device: dict[int, list[dict]] = {}
    for r in rows:
        by_device.setdefault(r.device_id, []).append({
            "metric":   r.metric,
            "unit":     r.unit,
            "avg":      round(float(r.avg), 3),
            "min":      float(r.min),
            "max":      float(r.max),
            "count":    r.count,
            "first_at": r.first_at.isoformat() if r.first_at else None,
            "last_at":  r.last_at.isoformat()  if r.last_at  else None,
        })

    return {
        "total":  total,
        "count":  len(device_ids),
        "offset": offset,
        "limit":  limit,
        "devices": [
            {"device_id": did, "metrics": by_device.get(did, [])}
            for did in device_ids
        ],
    }


# ============================================================
# Сводка по метрикам (без разбивки по устройствам)
# ============================================================
@router.get(
    "/stats/summary",
    summary="Сводная статистика по метрикам за весь период",
    description="avg/min/max/count по каждой метрике среди всех датчиков.",
)
async def get_global_summary(
    metric: Optional[str] = Query(None, min_length=1),
):
    async with SessionLocal() as db:
        stmt = select(
            TelemetryReading.metric,
            func.avg(TelemetryReading.value).label("avg"),
            func.min(TelemetryReading.value).label("min"),
            func.max(TelemetryReading.value).label("max"),
            func.count(TelemetryReading.id).label("count"),
            func.max(TelemetryReading.unit).label("unit"),
            func.count(func.distinct(TelemetryReading.device_id)).label("devices"),
        )
        if metric:
            stmt = stmt.where(TelemetryReading.metric == metric)

        stmt = stmt.group_by(TelemetryReading.metric).order_by(TelemetryReading.metric)
        rows = (await db.execute(stmt)).all()

    return {
        "metrics": [
            {
                "metric":  r.metric,
                "unit":    r.unit,
                "avg":     round(float(r.avg), 3),
                "min":     float(r.min),
                "max":     float(r.max),
                "count":   r.count,
                "devices": r.devices,
            }
            for r in rows
        ],
    }


# Данные телеметрии по идентификатору датчика
@router.get("/{device_id}")
async def get_telemetry(device_id: int, metric: str | None = None, limit: int = 100):
    async with SessionLocal() as db:
        stmt = select(TelemetryReading).where(TelemetryReading.device_id == device_id)
        if metric:
            stmt = stmt.where(TelemetryReading.metric == metric)
        stmt = stmt.order_by(TelemetryReading.recorded_at.desc()).limit(limit)
        rows = (await db.execute(stmt)).scalars().all()
    return [
        {"metric": r.metric, "value": r.value, "unit": r.unit, "recorded_at": r.recorded_at}
        for r in rows
    ]


# Средние показатели датчика на дату или период
@router.get(
    "/{device_id}/average",
    tags=["telemetry"],
    summary="Средние показания датчика за период или на дату",
    description="""
Возвращает **avg / min / max / count** по каждой метрике устройства.

Период задаётся одним из способов:
- `?date=2026-10-31` — за конкретный день (00:00:00.000000–23:59:59.999999 **UTC**)
- `?start=...&end=...` — произвольный период (ISO 8601)
- без параметров — за **последние 24 часа**

`metric` опционален: если задан — считается только по нему, иначе по всем метрикам устройства.
""",
    responses={
        404: {"description": "Device not found"},
        422: {"description": "Invalid time range or parameters"},
    },
)
async def get_telemetry_average(
    device_id: int,
    metric: Optional[str] = Query(None, description="Фильтр по конкретной метрике"),
    date_: Optional[date_type] = Query(
        None, alias="date", description="Конкретный день (UTC)"
    ),
    start: Optional[datetime] = Query(None, description="Начало периода (ISO 8601)"),
    end: Optional[datetime] = Query(None, description="Конец периода (ISO 8601)"),
):
    # --- Разбор периода ---
    if date_ is not None:
        if start is not None or end is not None:
            raise HTTPException(
                422, "Use either 'date' or 'start'/'end', not both"
            )
        start = datetime.combine(date_, time.min, tzinfo=timezone.utc)
        end = datetime.combine(date_, time.max, tzinfo=timezone.utc)
    elif start is None and end is None:
        # По умолчанию — последние 24 часа
        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=24)
    elif start is None or end is None:
        raise HTTPException(
            422, "Provide both 'start' and 'end', or use 'date'"
        )

    start = _ensure_utc(start)
    end = _ensure_utc(end)

    if start >= end:
        raise HTTPException(422, "'start' must be before 'end'")

    # --- Запрос ---
    async with SessionLocal() as db:
        if await db.get(Device, device_id) is None:
            raise HTTPException(404, f"Device {device_id} not found")

        stmt = (
            select(
                TelemetryReading.metric,
                func.avg(TelemetryReading.value).label("avg"),
                func.min(TelemetryReading.value).label("min"),
                func.max(TelemetryReading.value).label("max"),
                func.count(TelemetryReading.id).label("count"),
                func.max(TelemetryReading.unit).label("unit"),
            )
            .where(TelemetryReading.device_id == device_id)
            .where(TelemetryReading.recorded_at >= start)
            .where(TelemetryReading.recorded_at <= end)
        )
        if metric:
            stmt = stmt.where(TelemetryReading.metric == metric)

        stmt = (
            stmt.group_by(TelemetryReading.metric)
                .order_by(TelemetryReading.metric)
        )
        rows = (await db.execute(stmt)).all()

    return {
        "device_id": device_id,
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "metrics": [
            {
                "metric": r.metric,
                "unit":   r.unit,
                "avg":    round(float(r.avg), 3),
                "min":    float(r.min),
                "max":    float(r.max),
                "count":  r.count,
            }
            for r in rows
        ],
    }
