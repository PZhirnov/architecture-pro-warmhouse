from fastapi import APIRouter, Depends, Query, Response, status

from services.bff.clients.location_client import LocationsClient
from services.bff.deps import get_locations_client

router = APIRouter(prefix="/api/locations", tags=["locations"])


# --- Houses ---
@router.get("/houses", summary="Список домов (прокси)")
async def list_houses(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    c: LocationsClient = Depends(get_locations_client),
):
    return await c.list_houses(limit=limit, offset=offset)


@router.post("/houses", status_code=status.HTTP_201_CREATED,
             summary="Создать дом (прокси)")
async def create_house(
    payload: dict,
    c: LocationsClient = Depends(get_locations_client),
):
    return await c.create_house(payload)


@router.get("/houses/{house_id}", summary="Дом по id (прокси)")
async def get_house(
    house_id: int,
    c: LocationsClient = Depends(get_locations_client),
):
    return await c.get_house(house_id)


@router.patch("/houses/{house_id}", summary="Обновить дом (прокси)")
async def update_house(
    house_id: int,
    payload: dict,
    c: LocationsClient = Depends(get_locations_client),
):
    return await c.update_house(house_id, payload)


@router.delete("/houses/{house_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Удалить дом (прокси)")
async def delete_house(
    house_id: int,
    c: LocationsClient = Depends(get_locations_client),
):
    await c.delete_house(house_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Rooms ---
@router.get("/houses/{house_id}/rooms", summary="Комнаты дома (прокси)")
async def list_rooms(
    house_id: int,
    c: LocationsClient = Depends(get_locations_client),
):
    return await c.list_rooms(house_id)


@router.post("/houses/{house_id}/rooms", status_code=status.HTTP_201_CREATED,
             summary="Создать комнату (прокси)")
async def create_room(
    house_id: int,
    payload: dict,
    c: LocationsClient = Depends(get_locations_client),
):
    return await c.create_room(house_id, payload)


@router.patch("/rooms/{room_id}", summary="Обновить комнату (прокси)")
async def update_room(
    room_id: int,
    payload: dict,
    c: LocationsClient = Depends(get_locations_client),
):
    return await c.update_room(room_id, payload)


@router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Удалить комнату (прокси)")
async def delete_room(
    room_id: int,
    c: LocationsClient = Depends(get_locations_client),
):
    await c.delete_room(room_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Memberships ---
@router.get("/memberships/users/{user_id}", summary="Локации пользователя (прокси)")
async def list_user_memberships(
    user_id: int,
    c: LocationsClient = Depends(get_locations_client),
):
    return await c.list_user_memberships(user_id)


@router.get("/memberships/houses/{house_id}", summary="Пользователи дома (прокси)")
async def list_house_members(
    house_id: int,
    c: LocationsClient = Depends(get_locations_client),
):
    return await c.list_house_members(house_id)


@router.post("/memberships", status_code=status.HTTP_201_CREATED,
             summary="Выдать доступ (прокси)")
async def create_membership(
    payload: dict,
    c: LocationsClient = Depends(get_locations_client),
):
    return await c.create_membership(payload)


@router.patch("/memberships/{membership_id}", summary="Изменить привязку (прокси)")
async def update_membership(
    membership_id: int,
    payload: dict,
    c: LocationsClient = Depends(get_locations_client),
):
    return await c.update_membership(membership_id, payload)


@router.delete("/memberships/{membership_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Отозвать доступ (прокси)")
async def delete_membership(
    membership_id: int,
    c: LocationsClient = Depends(get_locations_client),
):
    await c.delete_membership(membership_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
