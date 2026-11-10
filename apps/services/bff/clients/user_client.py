from common.config import settings
from services.bff.clients.base import BaseClient


class UsersClient(BaseClient):
    def __init__(self, base_url: str | None = None, timeout: float = 5.0):
        super().__init__(base_url or settings.user_url, timeout)

    async def list_users(self, limit: int = 100, offset: int = 0):
        return await self.get("/users", params={"limit": limit, "offset": offset})

    async def get_user(self, user_id: int):
        return await self.get(f"/users/{user_id}")

    async def create_user(self, payload: dict):
        return await self.post("/users", json=payload)

    async def update_user(self, user_id: int, payload: dict):
        return await self._request("PATCH", f"/users/{user_id}", json=payload)

    async def change_password(self, user_id: int, payload: dict):
        return await self._request("PATCH", f"/users/{user_id}/password", json=payload)

    async def delete_user(self, user_id: int):
        return await self._request("DELETE", f"/users/{user_id}")
