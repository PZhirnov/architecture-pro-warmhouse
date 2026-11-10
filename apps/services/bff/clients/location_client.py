from common.config import settings
from services.bff.clients.base import BaseClient


class LocationsClient(BaseClient):
    def __init__(self, base_url: str | None = None, timeout: float = 5.0):
        super().__init__(base_url or settings.location_url, timeout)

    # --- Houses ---
    async def list_houses(self, limit: int = 100, offset: int = 0):
        return await self.get("/locations/houses", params={"limit": limit, "offset": offset})

    async def get_house(self, house_id: int):
        return await self.get(f"/locations/houses/{house_id}")

    async def create_house(self, payload: dict):
        return await self.post("/locations/houses", json=payload)

    async def update_house(self, house_id: int, payload: dict):
        return await self._request("PATCH", f"/locations/houses/{house_id}", json=payload)

    async def delete_house(self, house_id: int):
        return await self._request("DELETE", f"/locations/houses/{house_id}")

    # --- Rooms ---
    async def list_rooms(self, house_id: int):
        return await self.get(f"/locations/houses/{house_id}/rooms")

    async def create_room(self, house_id: int, payload: dict):
        return await self.post(f"/locations/houses/{house_id}/rooms", json=payload)

    async def update_room(self, room_id: int, payload: dict):
        return await self._request("PATCH", f"/locations/rooms/{room_id}", json=payload)

    async def delete_room(self, room_id: int):
        return await self._request("DELETE", f"/locations/rooms/{room_id}")

    # --- Memberships ---
    async def list_user_memberships(self, user_id: int):
        return await self.get(f"/locations/memberships/users/{user_id}")

    async def list_house_members(self, house_id: int):
        return await self.get(f"/locations/memberships/houses/{house_id}")

    async def create_membership(self, payload: dict):
        return await self.post("/locations/memberships", json=payload)

    async def update_membership(self, membership_id: int, payload: dict):
        return await self._request("PATCH", f"/locations/memberships/{membership_id}", json=payload)

    async def delete_membership(self, membership_id: int):
        return await self._request("DELETE", f"/locations/memberships/{membership_id}")
