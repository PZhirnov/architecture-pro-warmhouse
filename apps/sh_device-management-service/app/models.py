"""
BigInteger + Identity вместо BIGSERIAL — это современный способ, эквивалентный GENERATED ALWAYS AS IDENTITY.
Если хотите строго BIGSERIAL — замените на Column(BigInteger, primary_key=True, autoincrement=True);
SQLAlchemy сам создаст BIGSERIAL при create_all, но у вас схема уже есть, так что модели лишь отражают её.

"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Double,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserAccount(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="resident"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('resident', 'operator', 'admin')",
            name="chk_user_account_role",
        ),
    )

    memberships: Mapped[list["UserHouseRoom"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class House(Base):
    __tablename__ = "house"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    rooms: Mapped[list["Room"]] = relationship(
        back_populates="house", cascade="all, delete-orphan"
    )
    devices: Mapped[list["Device"]] = relationship(
        back_populates="house", cascade="all, delete-orphan"
    )


class Room(Base):
    __tablename__ = "room"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    house_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("house.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (UniqueConstraint("house_id", "name", name="uq_room_house_name"),)

    house: Mapped["House"] = relationship(back_populates="rooms")
    devices: Mapped[list["Device"]] = relationship(back_populates="room")


class UserHouseRoom(Base):
    __tablename__ = "user_house_room"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False
    )
    house_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("house.id", ondelete="CASCADE"), nullable=False
    )
    room_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("room.id", ondelete="SET NULL")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    user: Mapped["UserAccount"] = relationship(back_populates="memberships")
    house: Mapped["House"] = relationship()
    room: Mapped[Optional["Room"]] = relationship()


class Device(Base):
    __tablename__ = "device"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    house_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("house.id", ondelete="CASCADE"), nullable=False
    )
    room_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("room.id", ondelete="SET NULL")
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50))
    online: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('sensor', 'actuator', 'camera', 'gateway')",
            name="chk_device_type",
        ),
        Index("idx_device_house_id", "house_id"),
        Index("idx_device_room_id", "room_id"),
        Index("idx_device_online", "online"),
    )

    house: Mapped["House"] = relationship(back_populates="devices")
    room: Mapped[Optional["Room"]] = relationship(back_populates="devices")
    states: Mapped[list["DeviceState"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )
    readings: Mapped[list["TelemetryReading"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )
    commands: Mapped[list["CommandLog"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )


class DeviceState(Base):
    __tablename__ = "device_state"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    device_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("device.id", ondelete="CASCADE"), nullable=False
    )
    property: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (UniqueConstraint("device_id", "property"),)

    device: Mapped["Device"] = relationship(back_populates="states")


class TelemetryReading(Base):
    __tablename__ = "telemetry_reading"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    device_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("device.id", ondelete="CASCADE"), nullable=False
    )
    metric: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Double, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_readings_device_ts", "device_id", "recorded_at"),
    )

    device: Mapped["Device"] = relationship(back_populates="readings")


class CommandLog(Base):
    __tablename__ = "command_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    device_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("device.id", ondelete="CASCADE"), nullable=False
    )
    command: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    reason: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'sent', 'executed', 'failed', 'timeout')",
            name="chk_command_log_status",
        ),
        Index("idx_commands_device", "device_id", "created_at"),
        Index("idx_commands_status", "status"),
    )

    device: Mapped["Device"] = relationship(back_populates="commands")