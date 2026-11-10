from common.config import settings
from services.bff.clients.base import BaseClient


class AutomationClient(BaseClient):
    def __init__(self, base_url: str | None = None, timeout: float = 5.0):
        super().__init__(base_url or settings.automation_url, timeout)

    async def list_rules(self) -> list[dict]:
        return await self.get("/rules")
    