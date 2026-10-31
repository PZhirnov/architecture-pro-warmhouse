Структура проекта:


smart-home/
├── app/
│   ├── __init__.py
│   ├── main.py                 # точка входа FastAPI
│   ├── config.py               # настройки (pydantic-settings)
│   ├── database.py             # engine, session, Base
│   ├── models.py               # SQLAlchemy-модели
│   ├── schemas.py              # Pydantic-схемы
│   ├── deps.py                 # зависимости (get_db и т.п.)
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── user_account.py
│   │   ├── house.py
│   │   ├── room.py
│   │   ├── user_house_room.py
│   │   ├── device.py
│   │   ├── device_state.py
│   │   ├── telemetry.py
│   │   └── command_log.py
│   └── routers/
│       ├── __init__.py
│       ├── users.py
│       ├── houses.py
│       ├── rooms.py
│       ├── devices.py
│       ├── telemetry.py
│       └── commands.py
├── schema.sql                  # ваш DDL-скрипт
├── seed.sql                    # ваш seed-скрипт
├── .env
├── requirements.txt
└── README.md


# DEV
🧪 Проверка после запуска
bash
uvicorn app.main:app --reload
Откройте:

http://localhost:8000/docs — Swagger UI со всеми эндпоинтами;

http://localhost:8000/health — должно вернуть {"status":"ok","database":"up","error":null};

http://localhost:8000/ — метаинформация.

Примеры запросов:

bash
## Список пользователей
curl http://localhost:8000/users/

## Создать пользователя
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Тест","email":"test@example.com","password":"secret123","role":"resident"}'

## Список домов
curl http://localhost:8000/houses/

## Комнаты дома 1
curl http://localhost:8000/houses/1/rooms/

## Устройства дома 1
curl http://localhost:8000/houses/1/devices/

## Телеметрия устройства 1 (температура за последний час)
curl "http://localhost:8000/devices/1/telemetry/?metric=temperature&limit=50"

## Отправить команду устройству 2
curl -X POST http://localhost:8000/devices/2/commands/ \
  -H "Content-Type: application/json" \
  -d '{"device_id":2,"command":"switch_on"}'


# PROD
Запуск без compose
## Сборка
docker build -t smart-home-api:latest .

## Запуск (БД должна быть доступна по сети)
docker run -d --name smart-home -p 8000:8000 -e DATABASE_URL="postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/smarthome_mvp" -e DEBUG=false --restart unless-stopped smart-home-api:latest

## Проверка
curl http://localhost:8000/health


