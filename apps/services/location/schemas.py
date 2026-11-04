"""Pydantic-схемы сервиса location."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Houses
# ============================================================
class HouseCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Название дома",
        examples=["Квартира на Ленина"],
    )
    address: Optional[str] = Field(
        None,
        max_length=500,
        description="Адрес (опционально)",
        examples=["г. Москва, ул. Ленина, д. 10, кв. 42"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Квартира на Ленина",
                    "address": "г. Москва, ул. Ленина, д. 10, кв. 42",
                }
            ]
        }
    )


class HouseUpdate(BaseModel):
    name: Optional[str] = Field(
        None, min_length=1, max_length=255,
        description="Новое название (если нужно изменить)",
        examples=["Новое название"],
    )
    address: Optional[str] = Field(
        None, max_length=500,
        description="Новый адрес (если нужно изменить)",
        examples=["г. Москва, ул. Новая, д. 1"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"name": "Новое название"}]
        }
    )


# ============================================================
# Rooms
# ============================================================
class RoomCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Название комнаты",
        examples=["Гостиная"],
    )

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"name": "Гостиная"}]}
    )


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(
        None, min_length=1, max_length=255,
        description="Новое название комнаты",
        examples=["Кабинет"],
    )

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"name": "Кабинет"}]}
    )


# ============================================================
# Memberships
# ============================================================
class MembershipCreate(BaseModel):
    user_id: int = Field(..., gt=0, description="ID пользователя", examples=[3])
    house_id: int = Field(..., gt=0, description="ID дома", examples=[1])
    room_id: Optional[int] = Field(
        None, gt=0,
        description="ID комнаты. Не передавать/null — доступ ко всему дому",
        examples=[2],
    )
    role: str = Field(
        "resident",
        pattern="^(resident|operator|admin)$",
        description="Роль в доме: resident | operator | admin",
        examples=["operator"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"user_id": 3, "house_id": 1, "room_id": None, "role": "resident"},
                {"user_id": 4, "house_id": 1, "room_id": 2,    "role": "operator"},
            ]
        }
    )


class MembershipUpdate(BaseModel):
    room_id: Optional[int] = Field(
        None, gt=0,
        description="ID комнаты. null — отвязать (доступ ко всему дому)",
        examples=[2],
    )
    role: Optional[str] = Field(
        None, pattern="^(resident|operator|admin)$",
        description="Новая роль",
        examples=["operator"],
    )
    is_active: Optional[bool] = Field(
        None, description="Активна ли привязка", examples=[False]
    )

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"role": "operator"}]}
    )
