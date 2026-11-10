from fastapi import APIRouter, Depends

from services.bff.deps import get_dashboard_service
from services.bff.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get(
    "/overview",
    summary="Сводка по платформе",
    description="""
Агрегация одним запросом:
- количество домов
- количество устройств
- количество пользователей
- сводная статистика по метрикам (avg/min/max/count)

Все данные забираются параллельно (`asyncio.gather`).
""",
)
async def get_overview(
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.get_overview()


@router.get(
    "/devices/{device_id}",
    summary="Карточка устройства",
    description="Данные устройства + последнее показание температуры.",
    responses={404: {"description": "Device not found"}},
)
async def get_device_overview(
    device_id: int,
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.get_device_overview(device_id)
