from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- User ----------
class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role: str = Field("resident", pattern="^(resident|operator|admin)$")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- House ----------
class HouseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = Field(None, max_length=500)


class HouseCreate(HouseBase):
    pass


class HouseRead(HouseBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Room ----------
class RoomBase(BaseModel):
    house_id: int
    name: str = Field(..., min_length=1, max_length=255)


class RoomCreate(RoomBase):
    pass


class RoomRead(RoomBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ---------- UserHouseRoom ----------
class UserHouseRoomBase(BaseModel):
    user_account_id: int
    house_id: int
    room_id: Optional[int] = None
    is_active: bool = True


class UserHouseRoomCreate(UserHouseRoomBase):
    pass


class UserHouseRoomRead(UserHouseRoomBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ---------- Device ----------
class DeviceBase(BaseModel):
    house_id: int
    room_id: Optional[int] = None
    type: str = Field(..., pattern="^(sensor|actuator|camera|gateway)$")
    vendor: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    firmware_version: Optional[str] = Field(None, max_length=50)
    online: bool = False


class DeviceCreate(DeviceBase):
    pass


class DeviceRead(DeviceBase):
    id: int
    last_seen_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- DeviceState ----------
class DeviceStateBase(BaseModel):
    device_id: int
    property: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1, max_length=255)


class DeviceStateCreate(DeviceStateBase):
    pass


class DeviceStateRead(DeviceStateBase):
    id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Telemetry ----------
class TelemetryBase(BaseModel):
    device_id: int
    metric: str = Field(..., min_length=1, max_length=100)
    value: float
    unit: Optional[str] = Field(None, max_length=20)
    recorded_at: Optional[datetime] = None


class TelemetryCreate(TelemetryBase):
    pass


class TelemetryRead(TelemetryBase):
    id: int
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- CommandLog ----------
class CommandLogBase(BaseModel):
    device_id: int
    command: str = Field(..., min_length=1, max_length=50)


class CommandLogCreate(CommandLogBase):
    pass


class CommandLogRead(CommandLogBase):
    id: int
    status: str
    reason: Optional[str]
    created_at: datetime
    executed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
