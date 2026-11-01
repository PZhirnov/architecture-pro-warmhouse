from common.config import settings
from services.bff.clients.base import BaseClient


class DeviceClient(BaseClient):
    def __init__(self, base_url: str | None = None, timeout: float = 5.0):
        super().__init__(base_url or settings.device_url, timeout)

    async def list_devices(self) -> list[dict]:
        return await self.get("/devices")

    async def get_device(self, device_id: int) -> dict:  # ← добавить
        return await self.get(f"/devices/{device_id}")

    async def create_device(self, payload: dict) -> dict:  # ← новый
        return await self.post("/devices", json=payload)

    async def update_device(self, device_id: int, payload: dict) -> dict:  # ← новый
        return await self._request("PATCH", f"/devices/{device_id}", json=payload)

    async def delete_device(self, device_id: int) -> None:  # ← на будущее
        await self._request("DELETE", f"/devices/{device_id}")

    async def list_commands(self, device_id: int, limit: int = 50) -> list[dict]:
        return await self.get(
            f"/devices/{device_id}/commands",
            params={"limit": limit},
        )
