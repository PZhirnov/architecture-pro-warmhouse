from functools import lru_cache

from services.bff.clients.automation_client import AutomationClient
from services.bff.clients.device_client import DeviceClient
from services.bff.clients.location_client import LocationsClient
from services.bff.clients.telemetry_client import TelemetryClient
from services.bff.clients.user_client import UsersClient
from services.bff.services.dashboard_service import DashboardService


@lru_cache
def get_device_client() -> DeviceClient:
    return DeviceClient()


@lru_cache
def get_telemetry_client() -> TelemetryClient:
    return TelemetryClient()


@lru_cache
def get_automation_client() -> AutomationClient:
    return AutomationClient()


@lru_cache
def get_locations_client() -> LocationsClient:
    return LocationsClient()


@lru_cache
def get_users_client() -> UsersClient:
    return UsersClient()


def get_dashboard_service() -> DashboardService:
    return DashboardService(
        device=get_device_client(),
        telemetry=get_telemetry_client(),
        locations=get_locations_client(),
        users=get_users_client(),
    )
