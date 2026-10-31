from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import room as crud_room
from app.crud import house as crud_house
from app.deps import get_db
from app.schemas import RoomCreate, RoomRead

router = APIRouter(prefix="/houses/{house_id}/rooms", tags=["rooms"])


@router.get("/", response_model=list[RoomRead])
async def list_rooms(
    house_id: int, limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)
):
    if not await crud_house.get_house(db, house_id):
        raise HTTPException(status_code=404, detail="House not found")
    return await crud_room.list_rooms_by_house(db, house_id, limit=limit, offset=offset)


@router.post("/", response_model=RoomRead, status_code=status.HTTP_201_CREATED)
async def create_room(house_id: int, payload: RoomCreate, db: AsyncSession = Depends(get_db)):
    if not await crud_house.get_house(db, house_id):
        raise HTTPException(status_code=404, detail="House not found")
    payload.house_id = house_id
    try:
        return await crud_room.create_room(db, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))