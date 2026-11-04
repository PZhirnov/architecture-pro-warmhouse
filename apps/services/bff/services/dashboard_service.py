import asyncio

from services.bff.clients.device_client import DeviceClient
from services.bff.clients.location_client import LocationsClient
from services.bff.clients.telemetry_client import TelemetryClient
from services.bff.clients.user_client import UsersClient


class DashboardService:
    """Агрегация: сводка по платформе и карточка устройства."""

    def __init__(
        self,
        device: DeviceClient,
        telemetry: TelemetryClient,
        locations: LocationsClient,
        users: UsersClient,
    ):
        self.device = device
        self.telemetry = telemetry
        self.locations = locations
        self.users = users

    async def get_overview(self) -> dict:
        """Сводка по всей платформе: дома, устройства, пользователи, метрики."""
        houses, devices, users, stats = await asyncio.gather(
            self.locations.list_houses(limit=500),
            self.device.list_devices(),
            self.users.list_users(limit=500),
            self.telemetry.get_all_stats(),
        )
        return {
            "houses_count": len(houses),
            "devices_count": len(devices),
            "users_count": len(users),
            "metrics_summary": stats.get("metrics", []),
        }

    async def get_device_overview(self, device_id: int) -> dict:
        """Карточка одного устройства: данные + последняя телеметрия."""
        device = await self.device.get_device(device_id)
        readings = await self.telemetry.get_telemetry(
            device_id=device_id, metric="temperature", limit=1
        )
        return {
            "device": device,
            "latest_temperature": readings[0] if readings else None,
        }
