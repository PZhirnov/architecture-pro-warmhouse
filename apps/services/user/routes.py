from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from services.user import services
from services.user.utils import get_db

router = APIRouter(prefix="/users", tags=["users"])


# ============================================================
# Схемы
# ============================================================
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(resident|operator|admin)$")


class PasswordChange(BaseModel):
    old_password: Optional[str] = None
    new_password: str = Field(..., min_length=6, max_length=100)


# ============================================================
# Endpoints
# ============================================================
@router.get("", summary="Список пользователей")
async def list_users(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await services.list_users(db, limit=limit, offset=offset)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Создать пользователя",
    responses={409: {"description": "Email already registered"}},
)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    return await services.create_user(
        db, name=payload.name, email=payload.email, password=payload.password
    )


@router.get(
    "/{user_id}",
    summary="Пользователь по id",
    responses={404: {"description": "User not found"}},
)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await services.get_user(db, user_id)


@router.patch(
    "/{user_id}",
    summary="Обновить пользователя (name, email, role)",
    description="Пароль меняется отдельным эндпоинтом `/users/{id}/password`.",
    responses={
        404: {"description": "User not found"},
        409: {"description": "Email already registered"},
    },
)
async def update_user(
    user_id: int, payload: UserUpdate, db: AsyncSession = Depends(get_db)
):
    return await services.update_user(
        db, user_id, payload.model_dump(exclude_unset=True)
    )


@router.patch(
    "/{user_id}/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Сменить пароль",
    description="Если `old_password` передан — проверяется. "
                "Если нет — админский сброс (в проде нужна авторизация).",
    responses={
        403: {"description": "Old password is incorrect"},
        404: {"description": "User not found"},
    },
)
async def change_password(
    user_id: int, payload: PasswordChange, db: AsyncSession = Depends(get_db)
):
    await services.change_password(
        db,
        user_id,
        old_password=payload.old_password,
        new_password=payload.new_password,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить пользователя (каскадно привязки)",
    responses={404: {"description": "User not found"}},
)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    await services.delete_user(db, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
