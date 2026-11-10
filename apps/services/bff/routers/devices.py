from fastapi import APIRouter, Depends, HTTPException, status, Body
from httpx import HTTPStatusError

from services.bff.clients.device_client import DeviceClient
from services.bff.deps import get_device_client

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", summary="Список устройств")
async def list_devices(client: DeviceClient = Depends(get_device_client)):
    return await client.list_devices()


# 2. Одно устройство по id — с обработкой 404 от downstream
@router.get("/{device_id}", summary="Устройство по id")
async def get_device(
    device_id: int,
    client: DeviceClient = Depends(get_device_client),
):
    try:
        return await client.get_device(device_id)
    except HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(404, f"Device {device_id} not found")
        raise


@router.get("/{device_id}/commands", summary="История команд устройства")
async def list_commands(
    device_id: int,
    limit: int = 50,
    client: DeviceClient = Depends(get_device_client),
):
    return await client.list_commands(device_id, limit=limit)

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Добавить устройство",
    description="""
Создаёт устройство. `house_id` обязателен. `room_id` опционален — если указан,
комната должна принадлежать тому же дому.

Примеры:
- Простой датчик без комнаты
- Датчик температуры в гостиной
- Шлюз без комнаты
""",
    responses={
        201: {
            "description": "Устройство создано",
            "content": {
                "application/json": {
                    "example": {
                        "id": 44,
                        "type": "sensor",
                        "vendor": "Xiaomi",
                        "model": "Mi Temperature & Humidity Monitor 2",
                        "online": False,
                        "room_id": 1,
                        "last_seen_at": None,
                    }
                }
            },
        },
        404: {"description": "House not found"},
        422: {"description": "Room does not belong to house / validation error"},
    },
)
async def create_device(
    payload: dict = Body(
        ...,
        openapi_examples={
            "simple_sensor": {
                "summary": "Датчик без комнаты",
                "value": {
                    "house_id": 1,
                    "type": "sensor",
                    "vendor": "Xiaomi",
                    "model": "Mi Temperature & Humidity Monitor 2",
                    "online": False,
                },
            },
            "sensor_in_room": {
                "summary": "Датчик в гостиной",
                "value": {
                    "house_id": 1,
                    "room_id": 1,
                    "type": "sensor",
                    "vendor": "Aqara",
                    "model": "Motion Sensor P1",
                    "firmware_version": "1.2.1",
                    "online": True,
                },
            },
            "gateway": {
                "summary": "Шлюз (без комнаты)",
                "value": {
                    "house_id": 2,
                    "type": "gateway",
                    "vendor": "Zigbee",
                    "model": "CC2531",
                    "online": True,
                },
            },
        },
    ),
    client: DeviceClient = Depends(get_device_client),
):
    return await client.create_device(payload)


@router.patch(
    "/{device_id}",
    summary="Обновить устройство (частично)",
    description="""
Меняет только переданные поля. Чтобы отвязать от комнаты — передать
`"room_id": null`. `house_id` изменить нельзя.

Примеры:
- Только `online`
- Сменить комнату
- Обновить прошивку
- Отвязать от комнаты
""",
    responses={
        404: {"description": "Device not found"},
        422: {"description": "Room does not belong to device's house"},
    },
)
async def update_device(
    device_id: int,
    payload: dict = Body(
        ...,
        openapi_examples={
            "online": {
                "summary": "Только статус online",
                "value": {"online": True},
            },
            "change_room": {
                "summary": "Перевести в другую комнату",
                "value": {"room_id": 2},
            },
            "firmware": {
                "summary": "Обновить прошивку",
                "value": {"firmware_version": "1.1.0"},
            },
            "detach_room": {
                "summary": "Отвязать от комнаты",
                "value": {"room_id": None},
            },
        },
    ),
    client: DeviceClient = Depends(get_device_client),
):
    return await client.update_device(device_id, payload)


