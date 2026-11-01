from common.config import settings
from services.bff.clients.base import BaseClient


class TelemetryClient(BaseClient):
    def __init__(self, base_url: str | None = None, timeout: float = 5.0):
        super().__init__(base_url or settings.telemetry_url, timeout)

    async def get_telemetry(
        self, device_id: int, metric: str | None = None, limit: int = 100
    ) -> list[dict]:
        return await self.get(
            f"/telemetry/{device_id}",
            params={"metric": metric, "limit": limit},
        )

    async def get_average(
            self,
            device_id: int,
            metric: str | None = None,
            date: str | None = None,
            start: str | None = None,
            end: str | None = None,
    ) -> dict:
        params: dict = {}
        for key, value in {
            "metric": metric,
            "date": date,
            "start": start,
            "end": end,
        }.items():
            if value:
                params[key] = value
        return await self.get(f"/telemetry/{device_id}/average", params=params)


    async def get_all_stats(
            self,
            device_id: int | None = None,
            metric: str | None = None,
            limit: int = 100,
            offset: int = 0,
    ) -> dict:
        params: dict = {"limit": limit, "offset": offset}
        if device_id is not None:
            params["device_id"] = device_id
        if metric:
            params["metric"] = metric
        return await self.get("/telemetry/stats/all", params=params)

    async def get_summary(self, metric: str | None = None) -> dict:
        params: dict = {}
        if metric:
            params["metric"] = metric
        return await self.get("/telemetry/stats/summary", params=params)
