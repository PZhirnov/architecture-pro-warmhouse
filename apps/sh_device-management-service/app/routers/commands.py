from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import command_log as crud_cmd
from app.crud import device as crud_device
from app.deps import get_db
from app.schemas import CommandLogCreate, CommandLogRead

router = APIRouter(prefix="/devices/{device_id}/commands", tags=["commands"])


@router.get("/", response_model=list[CommandLogRead])
async def list_commands(
    device_id: int, limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)
):
    if not await crud_device.get_device(db, device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    return await crud_cmd.list_commands_by_device(
        db, device_id=device_id, limit=limit, offset=offset
    )


@router.post("/", response_model=CommandLogRead, status_code=status.HTTP_201_CREATED)
async def send_command(
    device_id: int, payload: CommandLogCreate, db: AsyncSession = Depends(get_db)
):
    if not await crud_device.get_device(db, device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    payload.device_id = device_id
    return await crud_cmd.create_command(db, payload)


@router.patch("/{command_id}", response_model=CommandLogRead)
async def update_status(
    device_id: int,
    command_id: int,
    status: str,
    reason: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if status not in ("pending", "sent", "executed", "failed", "timeout"):
        raise HTTPException(status_code=400, detail="Invalid status")
    cmd = await db.get(crud_cmd.CommandLog, command_id) if hasattr(crud_cmd, "CommandLog") else None
    if cmd is None:
        from app.models import CommandLog
        cmd = await db.get(CommandLog, command_id)
    if not cmd or cmd.device_id != device_id:
        raise HTTPException(status_code=404, detail="Command not found")
    return await crud_cmd.mark_status(db, cmd, status=status, reason=reason)