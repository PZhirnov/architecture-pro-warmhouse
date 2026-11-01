# Telemetry Service — приём и статистика показаний

Микросервис платформы умного дома (MVP). Принимает показания датчиков из
шины событий NATS, сохраняет в PostgreSQL, отдаёт сырые данные и агрегаты
через HTTP.

**Не знает** про `Device`, `House`, `Room` — работает **только** с
`telemetry_reading`. Если по `device_id` нет данных, это не ошибка —
возвращается пустой результат.

## Что делает

```
┌───────────┐   NATS "telemetry.reading"   ┌───────────────┐
│    ACL    │ ───────────────────────────► │   Telemetry   │
└───────────┘   {device_id, metric, value} └───────┬───────┘
                                                   │ SQL
                                                   ▼
                                           ┌───────────────┐
                                           │  PostgreSQL   │
                                           │ telemetry_    │
                                           │   reading     │
                                           └───────┬───────┘
                                                   ▲
                                                   │ HTTP GET
                                           ┌───────┴───────┐
                                           │      BFF      │ :8080
                                           └───────────────┘
```

1. Подписан на `telemetry.reading` в NATS.
2. На каждое сообщение — `INSERT INTO telemetry_reading`.
3. Через HTTP отдаёт сырые показания и агрегаты (avg/min/max/count).

## Структура

```
services/telemetry/
├── __init__.py
├── main.py         # FastAPI app + lifespan (поднимает NATS-подписки)
├── handlers.py     # handle_reading + register_handlers
└── routers/
    ├── __init__.py
    └── telemetry.py  # все эндпоинты, router = APIRouter(prefix="/telemetry")
```

**Ответственность файлов:**

| Файл | Что внутри |
|---|---|
| `main.py` | Только wiring: `FastAPI(...)`, `lifespan`, `include_router`. ~30 строк |
| `handlers.py` | `handle_reading(data)` — сохранение в БД; `register_handlers(nc)` — подписки |
| `routers/telemetry.py` | `APIRouter(prefix="/telemetry")` + все `@router.get` |

> ⚠️ Если используете `prefix="/telemetry"` в `APIRouter` — в путях
> внутри роутера **не дублируйте** `/telemetry`. Иначе URL
> `/telemetry/telemetry/{device_id}`.

## Быстрый старт

### В составе docker-compose

```bash
docker compose up -d --build telemetry
docker compose logs -f telemetry
```

Сервис в `docker-compose.yml` ждёт `db` (healthy) и `nats`, получает
`DATABASE_URL` и `NATS_URL`.

### Локально

```bash
# из корня проекта
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/smarthome
export NATS_URL=nats://localhost:4222

uvicorn services.telemetry.main:app --reload --port 8082
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `DATABASE_URL` | — (обязательна) | `postgresql+asyncpg://user:pass@host:5432/db` |
| `NATS_URL` | `nats://nats:4222` | Шина событий |

## API

| Метод | Путь | Что |
|---|---|---|
| GET | `/health` | Health-check |
| GET | `/telemetry/stats/all` | Статистика по всем датчикам за всё время |
| GET | `/telemetry/stats/summary` | Сводка по метрикам |
| GET | `/telemetry/{device_id}` | Сырые показания датчика |
| GET | `/telemetry/{device_id}/average` | Средние за период / на дату |

> ⚠️ Порядок роутов важен: `/stats/*` объявлены **до** `/{device_id}`,
> иначе `"stats"` попытается превратиться в `int` и упадёт с `422`.

### `GET /telemetry/stats/all`

Статистика по **всем** датчикам за **весь** период (без фильтра по времени).
Возвращает avg/min/max/count по каждой метрике для каждого `device_id`.

**Параметры:**

| Параметр | Тип | Описание |
|---|---|---|
| `device_id` | int \| null | Только конкретный датчик |
| `metric` | str \| null | Только конкретная метрика |
| `limit` | int (1–500, default 100) | Пагинация по `device_id` |
| `offset` | int (≥0, default 0) | Смещение |

**Пример:**

```bash
curl "http://localhost:8082/telemetry/stats/all"
curl "http://localhost:8082/telemetry/stats/all?device_id=1"
curl "http://localhost:8082/telemetry/stats/all?metric=temperature&limit=10"
```

**Ответ:**

```json
{
  "total": 28,
  "count": 28,
  "offset": 0,
  "limit": 100,
  "devices": [
    {
      "device_id": 1,
      "metrics": [
        {"metric": "humidity",    "unit": "%",  "avg": 47.215, "min": 40.0, "max": 55.0, "count": 2880, "first_at": "2026-10-25T00:00:00+00:00", "last_at": "2026-10-31T23:55:00+00:00"},
        {"metric": "temperature", "unit": "°C", "avg": 23.847, "min": 21.9, "max": 26.5, "count": 2880, "first_at": "2026-10-25T00:00:00+00:00", "last_at": "2026-10-31T23:55:00+00:00"}
      ]
    }
  ]
}
```

### `GET /telemetry/stats/summary`

Сводка по метрикам — агрегаты по всем датчикам вместе.

**Параметры:**

| Параметр | Тип | Описание |
|---|---|---|
| `metric` | str \| null | Только конкретная метрика |

**Пример:**

```bash
curl "http://localhost:8082/telemetry/stats/summary"
```

**Ответ:**

```json
{
  "metrics": [
    {"metric": "humidity",    "unit": "%",  "avg": 46.83, "min": 35.0, "max": 58.0, "count": 12500, "devices": 12},
    {"metric": "motion",      "unit": null, "avg": 0.32,  "min": 0.0,  "max": 1.0,  "count": 8600,  "devices": 8},
    {"metric": "temperature", "unit": "°C", "avg": 23.12, "min": 18.4, "max": 28.9, "count": 31200, "devices": 28}
  ]
}
```

### `GET /telemetry/{device_id}`

Сырые показания датчика (последние N).

**Параметры:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `metric` | str \| null | — | Фильтр по метрике |
| `limit` | int (1–1000) | 100 | Сколько строк вернуть |

**Пример:**

```bash
curl "http://localhost:8082/telemetry/1?limit=5"
curl "http://localhost:8082/telemetry/1?metric=temperature&limit=100"
```

**Ответ:**

```json
[
  {"metric": "temperature", "value": 23.5, "unit": "°C", "recorded_at": "2026-10-31T23:55:00+00:00"},
  {"metric": "humidity",    "value": 47.0, "unit": "%",  "recorded_at": "2026-10-31T23:55:00+00:00"}
]
```

### `GET /telemetry/{device_id}/average`

Средние показания за период. Три режима:

| Как задать | Пример | Что считается |
|---|---|---|
| `?date=YYYY-MM-DD` | `?date=2026-10-31` | За конкретный день (UTC, 00:00–23:59:59.999999) |
| `?start=...&end=...` | `?start=2026-10-30T00:00:00Z&end=2026-10-31T00:00:00Z` | Произвольный период (ISO 8601) |
| без параметров | `/telemetry/1/average` | Последние 24 часа |

**Параметры:**

| Параметр | Тип | Описание |
|---|---|---|
| `metric` | str \| null | Фильтр по метрике |
| `date` | `YYYY-MM-DD` | Конкретный день (UTC) |
| `start` | ISO 8601 | Начало периода |
| `end` | ISO 8601 | Конец периода |

**Пример:**

```bash
curl "http://localhost:8082/telemetry/1/average?date=2026-10-31"
curl "http://localhost:8082/telemetry/1/average?start=2026-10-30T00:00:00Z&end=2026-10-31T00:00:00Z"
curl "http://localhost:8082/telemetry/1/average"
curl "http://localhost:8082/telemetry/1/average?date=2026-10-31&metric=temperature"
```

**Ответ:**

```json
{
  "device_id": 1,
  "period": {"start": "2026-10-31T00:00:00+00:00", "end": "2026-10-31T23:59:59.999999+00:00"},
  "metrics": [
    {"metric": "humidity",    "unit": "%",  "avg": 47.215, "min": 40.0, "max": 55.0, "count": 288},
    {"metric": "temperature", "unit": "°C", "avg": 23.847, "min": 22.1, "max": 26.3, "count": 288}
  ]
}
```

## Формат входящего сообщения

Из NATS `telemetry.reading`:

```json
{
  "device_id": 1,
  "metric": "temperature",
  "value": 24.3,
  "unit": "°C"
}
```

| Поле | Тип | Обязательно | Значения |
|---|---|---|---|
| `device_id` | int | да | `device.id` из БД |
| `metric` | str | да | `temperature` \| `humidity` \| `motion` \| `power` \| `switch` \| `recording` |
| `value` | float | да | приводится к `float` |
| `unit` | str \| null | нет | `°C` \| `%` \| `W` \| `null` |

Невалидный JSON или отсутствие обязательного поля — сообщение пропускается
с записью в лог, сервис продолжает работу.

## Схема данных

```sql
CREATE TABLE telemetry_reading (
    id          BIGSERIAL PRIMARY KEY,
    device_id   BIGINT    NOT NULL REFERENCES device(id) ON DELETE CASCADE,
    metric      VARCHAR(100) NOT NULL,
    value       DOUBLE PRECISION NOT NULL,
    unit        VARCHAR(20),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_readings_device_ts
    ON telemetry_reading(device_id, recorded_at DESC);
```

Индекс покрывает **все** запросы сервиса: и `/{device_id}`, и
`/{device_id}/average`, и `COUNT(*)` в `/stats/all`.

## Логи

```
INFO  Connected to NATS at nats://nats:4222
INFO  Subscribed: telemetry.reading
INFO  Saved reading: {'device_id': 1, 'metric': 'temperature', 'value': 24.3, 'unit': '°C'}
INFO  Saved reading: {'device_id': 1, 'metric': 'humidity', 'value': 47.0, 'unit': '%'}
...
INFO  Uvicorn running on http://0.0.0.0:8082
```

| Строка | Что значит |
|---|---|
| `Connected to NATS` | Подключение к шине установлено |
| `Subscribed: telemetry.reading` | Готов принимать показания |
| `Saved reading: {...}` | Успешный INSERT |
| `Bad message on telemetry.reading` | Невалидный JSON — пропущено |
| `Handler error on telemetry.reading` | Ошибка БД при INSERT — пропущено |

## Проверка, что всё работает

### 1. Сервис запущен

```bash
curl http://localhost:8082/health
# {"service":"telemetry","status":"ok"}
```

### 2. NATS-подписка активна

```bash
docker compose logs --tail=5 telemetry
# Subscribed: telemetry.reading
# Saved reading: {...}
```

### 3. Данные в БД

```bash
docker compose exec db psql -U postgres -d smarthome -c \
  "SELECT device_id, metric, COUNT(*), ROUND(AVG(value)::numeric, 2) AS avg
   FROM telemetry_reading GROUP BY device_id, metric
   ORDER BY device_id, metric LIMIT 10;"
```

### 4. API отвечает

```bash
# сырые данные
curl "http://localhost:8082/telemetry/1?limit=5"

# статистика по всем
curl "http://localhost:8082/telemetry/stats/all"

# сводка по метрикам
curl "http://localhost:8082/telemetry/stats/summary"

# средние за день
curl "http://localhost:8082/telemetry/1/average?date=2026-10-31"

# несуществующий датчик — пустой ответ, не 404
curl "http://localhost:8082/telemetry/99999"
# []
```

## Производительность

- **`/{device_id}` и `/{device_id}/average`** — используют индекс
  `(device_id, recorded_at DESC)`, range scan. Быстро на любом объёме.
- **`/stats/all` и `/stats/summary`** — `GROUP BY` по всей таблице. На
  100k строк — миллисекунды, на 10M — секунды.

Если `/stats/*` станут медленными — **материализованное представление**:

```sql
CREATE MATERIALIZED VIEW mv_telemetry_stats AS
SELECT device_id, metric,
       AVG(value)::double precision AS avg,
       MIN(value) AS min,
       MAX(value) AS max,
       COUNT(*) AS count,
       MAX(unit) AS unit,
       MIN(recorded_at) AS first_at,
       MAX(recorded_at) AS last_at
FROM telemetry_reading
GROUP BY device_id, metric;

CREATE UNIQUE INDEX ON mv_telemetry_stats(device_id, metric);
```

Обновление: `REFRESH MATERIALIZED VIEW CONCURRENTLY mv_telemetry_stats;`
по cron или после батча записей. Сервис переключается на чтение из `mv_*` —
контракт API не меняется.

## Траблшутинг

| Симптом | Причина | Решение |
|---|---|---|
| `Subscribed: telemetry.reading` не появляется | NATS недоступен | `docker compose ps nats`, `docker compose logs nats` |
| `Saved reading` не появляется, хотя симулятор публикует | ACL не бриджит, или неверный субъект | `docker compose logs acl` |
| `recorded_at` «прыгает» при смене таймзоны сервера | `TIMESTAMP` вместо `TIMESTAMPTZ` | В схеме — `TIMESTAMPTZ`, проверить `\d telemetry_reading` |
| `422 "stats" is not a valid integer` | `/stats/*` объявлены **после** `/{device_id}` | Переставить роуты: `stats/*` **до** `{device_id}` |
| `/telemetry/telemetry/1` → 404 | Двойной префикс `/telemetry` в `APIRouter` и в пути | Убрать `/telemetry` из путей внутри роутера |
| `Can't load plugin: sqlalchemy.dialects:postgres` | URL с `postgres://` | `postgresql+asyncpg://` |
| `AttributeError: module 'services.telemetry.handlers' has no attribute ...` | `main.py` импортирует из старого места | Проверить `from services.telemetry.handlers import register_handlers` |