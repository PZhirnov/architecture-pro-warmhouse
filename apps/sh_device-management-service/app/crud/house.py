from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import House
from app.schemas import HouseCreate


async def get_house(db: AsyncSession, house_id: int) -> House | None:
    return await db.get(House, house_id)


async def list_houses(db: AsyncSession, limit: int = 100, offset: int = 0) -> Sequence[House]:
    result = await db.execute(
        select(House).order_by(House.id).limit(limit).offset(offset)
    )
    return result.scalars().all()


async def create_house(db: AsyncSession, data: HouseCreate) -> House:
    house = House(**data.model_dump())
    db.add(house)
    await db.commit()
    await db.refresh(house)
    return house


async def delete_house(db: AsyncSession, house: House) -> None:
    await db.delete(house)
    await db.commit()