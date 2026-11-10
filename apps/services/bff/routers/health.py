import asyncio

from fastapi import APIRouter, Depends

from services.bff.clients.automation_client import AutomationClient
from services.bff.clients.device_client import DeviceClient
from services.bff.clients.location_client import LocationsClient
from services.bff.clients.telemetry_client import TelemetryClient
from services.bff.clients.user_client import UsersClient
from services.bff.deps import (
    get_automation_client,
    get_device_client,
    get_locations_client,
    get_telemetry_client,
    get_users_client,
)

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get(
    "/services",
    summary="Проверка состояния всех downstream-сервисов",
    description="""
Параллельно опрашивает `/health` каждого сервиса.
Возвращает общий статус (`ok` / `degraded` / `down`) и детали по каждому.

`status`:
- `ok` — все сервисы отвечают 2xx
- `degraded` — хотя бы один отвечает, но не все
- `down` — ни один не отвечает
""",
)
async def health_services(
    device: DeviceClient = Depends(get_device_client),
    telemetry: TelemetryClient = Depends(get_telemetry_client),
    automation: AutomationClient = Depends(get_automation_client),
    locations: LocationsClient = Depends(get_locations_client),
    users: UsersClient = Depends(get_users_client),
):
    clients = {
        "device":     device,
        "telemetry":  telemetry,
        "automation": automation,
        "locations":  locations,
        "users":      users,
    }

    # Параллельный опрос всех сервисов
    results = await asyncio.gather(*(c.ping() for c in clients.values()))
    services = {name: result for name, result in zip(clients.keys(), results)}

    up = sum(1 for r in results if r["status"] == "ok")
    total = len(results)

    if up == total:
        overall = "ok"
    elif up == 0:
        overall = "down"
    else:
        overall = "degraded"

    return {
        "status": overall,
        "up": up,
        "total": total,
        "services": services,
    }


@router.get(
    "/services/{service_name}",
    summary="Проверка состояния конкретного сервиса",
    responses={404: {"description": "Unknown service"}},
)
async def health_service(
    service_name: str,
    device: DeviceClient = Depends(get_device_client),
    telemetry: TelemetryClient = Depends(get_telemetry_client),
    automation: AutomationClient = Depends(get_automation_client),
    locations: LocationsClient = Depends(get_locations_client),
    users: UsersClient = Depends(get_users_client),
):
    clients = {
        "device":     device,
        "telemetry":  telemetry,
        "automation": automation,
        "locations":  locations,
        "users":      users,
    }
    if service_name not in clients:
        from fastapi import HTTPException
        raise HTTPException(404, f"Unknown service '{service_name}'")

    result = await clients[service_name].ping()
    return {"name": service_name, **result}
