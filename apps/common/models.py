from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Double, ForeignKey, String, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.database import Base

# ============================================================
# Пользователи
# ============================================================
class UserAccount(Base):
    __tablename__ = "user_account"

    id:            Mapped[int]      = mapped_column(BigInteger, primary_key=True)
    name:          Mapped[str]      = mapped_column(String(100), nullable=False)
    email:         Mapped[str]      = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str]      = mapped_column(String(255), nullable=False)
    role:          Mapped[str]      = mapped_column(String(20), nullable=False, server_default="resident")
    created_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================================
# Локации
# ============================================================
class House(Base):
    __tablename__ = "house"

    id:         Mapped[int]           = mapped_column(BigInteger, primary_key=True)
    name:       Mapped[str]           = mapped_column(String(255), nullable=False)
    address:    Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime]      = mapped_column(DateTime, server_default=func.now())


class Room(Base):
    __tablename__ = "room"

    id:       Mapped[int] = mapped_column(BigInteger, primary_key=True)
    house_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("house.id", ondelete="CASCADE"), nullable=False
    )
    name:     Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (UniqueConstraint("house_id", "name", name="uq_room_house_name"),)


class UserHouse(Base):
    __tablename__ = "user_house"

    id:         Mapped[int]           = mapped_column(BigInteger, primary_key=True)
    user_id:    Mapped[int]           = mapped_column(
        BigInteger, ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False
    )
    house_id:   Mapped[int]           = mapped_column(
        BigInteger, ForeignKey("house.id", ondelete="CASCADE"), nullable=False
    )
    room_id:    Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("room.id", ondelete="SET NULL")
    )
    role:       Mapped[str]           = mapped_column(String(20), nullable=False, server_default="resident")
    is_active:  Mapped[bool]          = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())


# Устройства
# ============================================================
class Device(Base):
    __tablename__ = "device"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    house_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("house.id"))
    room_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("room.id"))
    type: Mapped[str] = mapped_column(String(50))
    vendor: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50))
    online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# Телеметрия
# ============================================================
class TelemetryReading(Base):
    __tablename__ = "telemetry_reading"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    device_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("device.id"))
    metric: Mapped[str] = mapped_column(String(100))
    value: Mapped[float] = mapped_column(Double)
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommandLog(Base):
    __tablename__ = "command_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    device_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("device.id"))
    command: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reason: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
