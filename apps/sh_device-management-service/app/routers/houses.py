from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import house as crud_house
from app.deps import get_db
from app.schemas import HouseCreate, HouseRead

router = APIRouter(prefix="/houses", tags=["houses"])


@router.get("/", response_model=list[HouseRead])
async def list_houses(limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)):
    return await crud_house.list_houses(db, limit=limit, offset=offset)


@router.post("/", response_model=HouseRead, status_code=status.HTTP_201_CREATED)
async def create_house(payload: HouseCreate, db: AsyncSession = Depends(get_db)):
    return await crud_house.create_house(db, payload)


@router.get("/{house_id}", response_model=HouseRead)
async def get_house(house_id: int, db: AsyncSession = Depends(get_db)):
    house = await crud_house.get_house(db, house_id)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    return house


@router.delete("/{house_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_house(house_id: int, db: AsyncSession = Depends(get_db)):
    house = await crud_house.get_house(db, house_id)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    await crud_house.delete_house(db, house)