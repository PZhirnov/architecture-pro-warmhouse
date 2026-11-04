from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.models import CommandLog


async def list_by_device(
    db: AsyncSession, device_id: int, limit: int = 50
) -> Sequence[CommandLog]:
    return (
        await db.execute(
            select(CommandLog)
            .where(CommandLog.device_id == device_id)
            .order_by(CommandLog.id.desc())
            .limit(limit)
        )
    ).scalars().all()


async def create(
    db: AsyncSession,
    device_id: int,
    command: str,
    status: str = "executed",
    reason: str | None = None,
) -> CommandLog:
    cmd = CommandLog(
        device_id=device_id, command=command, status=status, reason=reason
    )
    db.add(cmd)
    await db.commit()
    await db.refresh(cmd)
    return cmd
