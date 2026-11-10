from fastapi import APIRouter, Depends, Query, Response, status

from services.bff.clients.user_client import UsersClient
from services.bff.deps import get_users_client

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", summary="Список пользователей (прокси)")
async def list_users(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    c: UsersClient = Depends(get_users_client),
):
    return await c.list_users(limit=limit, offset=offset)


@router.post("", status_code=status.HTTP_201_CREATED,
             summary="Создать пользователя (прокси)")
async def create_user(
    payload: dict,
    c: UsersClient = Depends(get_users_client),
):
    return await c.create_user(payload)


@router.get("/{user_id}", summary="Пользователь по id (прокси)")
async def get_user(
    user_id: int,
    c: UsersClient = Depends(get_users_client),
):
    return await c.get_user(user_id)


@router.patch("/{user_id}", summary="Обновить пользователя (прокси)")
async def update_user(
    user_id: int,
    payload: dict,
    c: UsersClient = Depends(get_users_client),
):
    return await c.update_user(user_id, payload)


@router.patch("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT,
              summary="Сменить пароль (прокси)")
async def change_password(
    user_id: int,
    payload: dict,
    c: UsersClient = Depends(get_users_client),
):
    await c.change_password(user_id, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Удалить пользователя (прокси)")
async def delete_user(
    user_id: int,
    c: UsersClient = Depends(get_users_client),
):
    await c.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)