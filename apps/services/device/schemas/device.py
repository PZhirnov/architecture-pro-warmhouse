from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DeviceCreate(BaseModel):
    house_id: int = Field(..., gt=0, description="Дом, к которому относится устройство")
    room_id: Optional[int] = Field(None, gt=0, description="Комната в этом доме (опционально)")
    type: str = Field(..., pattern="^(sensor|actuator|camera|gateway)$")
    vendor: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    firmware_version: Optional[str] = Field(None, max_length=50)
    online: bool = False


class DeviceUpdate(BaseModel):
    """Частичное обновление. Все поля опциональны.

    Переданное поле применяется; отсутствующее — не трогается.
    Чтобы явно отвязать от комнаты: передать `"room_id": null`.
    """
    room_id: Optional[int] = Field(None, gt=0)
    type: Optional[str] = Field(None, pattern="^(sensor|actuator|camera|gateway)$")
    vendor: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    firmware_version: Optional[str] = Field(None, max_length=50)
    online: Optional[bool] = None


class DeviceRead(BaseModel):
    id: int
    type: str
    vendor: Optional[str] = None
    model: Optional[str] = None
    online: bool
    room_id: Optional[int] = None
    last_seen_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CommandRead(BaseModel):
    id: int
    command: str
    status: str
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
