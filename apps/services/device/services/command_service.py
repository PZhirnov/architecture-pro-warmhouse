from typing import Sequence

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from services.device.crud_operation import house, device, command
from services.device.schemas import CommandRead


async def list_commands(
    db: AsyncSession, device_id: int, limit: int = 50
) -> Sequence[CommandRead]:
    if await device.get(db, device_id) is None:
        raise HTTPException(404, f"Device {device_id} not found")
    rows = await command.list_by_device(db, device_id, limit=limit)
    return [CommandRead.model_validate(r) for r in rows]


async def record_command(
    db: AsyncSession, device_id: int, command_res: str, reason: str | None = None
) -> CommandRead:
    cmd = await command.create(
        db, device_id=device_id, command=command_res, status="executed", reason=reason
    )
    return CommandRead.model_validate(cmd)
