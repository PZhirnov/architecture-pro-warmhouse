from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CommandLog
from app.schemas import CommandLogCreate


async def create_command(db: AsyncSession, data: CommandLogCreate) -> CommandLog:
    cmd = CommandLog(
        device_id=data.device_id,
        command=data.command,
        status="pending",
    )
    db.add(cmd)
    await db.commit()
    await db.refresh(cmd)
    return cmd


async def mark_status(
    db: AsyncSession,
    cmd: CommandLog,
    status: str,
    reason: str | None = None,
) -> CommandLog:
    cmd.status = status
    cmd.reason = reason
    if status in ("executed", "failed", "timeout"):
        cmd.executed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(cmd)
    return cmd


async def list_commands_by_device(
    db: AsyncSession, device_id: int, limit: int = 100, offset: int = 0
) -> Sequence[CommandLog]:
    result = await db.execute(
        select(CommandLog)
        .where(CommandLog.device_id == device_id)
        .order_by(CommandLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()