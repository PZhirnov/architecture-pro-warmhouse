from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from services.location import services
from services.location.utils import get_db

from services.location.schemas import (
    HouseCreate,
    HouseUpdate,
    MembershipCreate,
    MembershipUpdate,
    RoomCreate,
    RoomUpdate,
)

router = APIRouter(prefix="/locations", tags=["location"])


# ============================================================
# Схемы запросов
# ============================================================
# class HouseCreate(BaseModel):
#     name: str = Field(..., min_length=1, max_length=255)
#     address: Optional[str] = Field(None, max_length=500)
#
#
# class HouseUpdate(BaseModel):
#     name: Optional[str] = Field(None, min_length=1, max_length=255)
#     address: Optional[str] = Field(None, max_length=500)
#
#
# class RoomCreate(BaseModel):
#     name: str = Field(..., min_length=1, max_length=255)
#
#
# class RoomUpdate(BaseModel):
#     name: Optional[str] = Field(None, min_length=1, max_length=255)
#
#
# class MembershipCreate(BaseModel):
#     user_id: int = Field(..., gt=0)
#     house_id: int = Field(..., gt=0)
#     room_id: Optional[int] = Field(None, gt=0)
#     role: str = Field("resident", pattern="^(resident|operator|admin)$")
#
#
# class MembershipUpdate(BaseModel):
#     room_id: Optional[int] = Field(None, gt=0)
#     role: Optional[str] = Field(None, pattern="^(resident|operator|admin)$")
#     is_active: Optional[bool] = None


# ============================================================
# Houses
# ============================================================
@router.get("/houses", tags=["houses"], summary="Список домов")
async def list_houses(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await services.list_houses(db, limit=limit, offset=offset)


@router.post(
    "/houses",
    tags=["houses"],
    status_code=status.HTTP_201_CREATED,
    summary="Создать дом",
)
async def create_house(payload: HouseCreate, db: AsyncSession = Depends(get_db)):
    return await services.create_house(db, payload.name, payload.address)


@router.get(
    "/houses/{house_id}",
    tags=["houses"],
    summary="Дом по id",
    responses={404: {"description": "House not found"}},
)
async def get_house(house_id: int, db: AsyncSession = Depends(get_db)):
    return await services.get_house(db, house_id)


@router.patch(
    "/houses/{house_id}",
    tags=["houses"],
    summary="Обновить дом",
    responses={404: {"description": "House not found"}},
)
async def update_house(
    house_id: int, payload: HouseUpdate, db: AsyncSession = Depends(get_db)
):
    return await services.update_house(
        db, house_id, payload.model_dump(exclude_unset=True)
    )


@router.delete(
    "/houses/{house_id}",
    tags=["houses"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить дом (каскадно комнаты, привязки, устройства)",
    responses={404: {"description": "House not found"}},
)
async def delete_house(house_id: int, db: AsyncSession = Depends(get_db)):
    await services.delete_house(db, house_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ============================================================
# Rooms
# ============================================================
@router.get(
    "/houses/{house_id}/rooms",
    tags=["rooms"],
    summary="Комнаты дома",
    responses={404: {"description": "House not found"}},
)
async def list_rooms(house_id: int, db: AsyncSession = Depends(get_db)):
    return await services.list_rooms(db, house_id)


@router.post(
    "/houses/{house_id}/rooms",
    tags=["rooms"],
    status_code=status.HTTP_201_CREATED,
    summary="Создать комнату",
    responses={
        404: {"description": "House not found"},
        409: {"description": "Room name already exists in this house"},
    },
)
async def create_room(
    house_id: int, payload: RoomCreate, db: AsyncSession = Depends(get_db)
):
    return await services.create_room(db, house_id, payload.name)


@router.get(
    "/rooms/{room_id}",
    tags=["rooms"],
    summary="Комната по id",
    responses={404: {"description": "Room not found"}},
)
async def get_room(room_id: int, db: AsyncSession = Depends(get_db)):
    return await services.get_room(db, room_id)


@router.patch(
    "/rooms/{room_id}",
    tags=["rooms"],
    summary="Обновить комнату",
    responses={404: {"description": "Room not found"}},
)
async def update_room(
    room_id: int, payload: RoomUpdate, db: AsyncSession = Depends(get_db)
):
    return await services.update_room(
        db, room_id, payload.model_dump(exclude_unset=True)
    )


@router.delete(
    "/rooms/{room_id}",
    tags=["rooms"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить комнату",
    responses={404: {"description": "Room not found"}},
)
async def delete_room(room_id: int, db: AsyncSession = Depends(get_db)):
    await services.delete_room(db, room_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ============================================================
# Memberships
# ============================================================
@router.get(
    "/memberships/users/{user_id}",
    tags=["memberships"],
    summary="Локации пользователя",
)
async def list_user_memberships(user_id: int, db: AsyncSession = Depends(get_db)):
    return await services.list_user_memberships(db, user_id)


@router.get(
    "/memberships/houses/{house_id}",
    tags=["memberships"],
    summary="Пользователи дома",
    responses={404: {"description": "House not found"}},
)
async def list_house_memberships(house_id: int, db: AsyncSession = Depends(get_db)):
    return await services.list_house_memberships(db, house_id)


@router.post(
    "/memberships",
    tags=["memberships"],
    status_code=status.HTTP_201_CREATED,
    summary="Выдать доступ пользователю к локации",
    responses={
        404: {"description": "House not found"},
        409: {"description": "Membership already exists"},
        422: {"description": "Room does not belong to house"},
    },
)
async def create_membership(
    payload: MembershipCreate, db: AsyncSession = Depends(get_db)
):
    return await services.create_membership(
        db,
        user_id=payload.user_id,
        house_id=payload.house_id,
        room_id=payload.room_id,
        role=payload.role,
    )


@router.patch(
    "/memberships/{membership_id}",
    tags=["memberships"],
    summary="Изменить привязку",
    responses={404: {"description": "Membership not found"}},
)
async def update_membership(
    membership_id: int,
    payload: MembershipUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await services.update_membership(
        db, membership_id, payload.model_dump(exclude_unset=True)
    )


@router.delete(
    "/memberships/{membership_id}",
    tags=["memberships"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отозвать доступ",
    responses={404: {"description": "Membership not found"}},
)
async def delete_membership(membership_id: int, db: AsyncSession = Depends(get_db)):
    await services.delete_membership(db, membership_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
