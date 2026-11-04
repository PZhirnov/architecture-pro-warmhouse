# Simulator — эмулятор IoT-устройств

Сервис-эмулятор для платформы умного дома (MVP). Читает устройства из
PostgreSQL, генерирует правдоподобные показания и публикует их в MQTT.
Заменяет реальные датчики/актуаторы на время разработки и демо.

## Что делает

```
┌──────────────┐    SELECT devices    ┌─────────────┐
│  Simulator   │ ───────────────────► │  PostgreSQL │
│              │                      └─────────────┘
│  1. читает устройства из БД
│  2. для каждого определяет метрики по type/model
│  3. раз в INTERVAL_SEC генерирует значения
│  4. публикует JSON в MQTT "smarthome/telemetry"
└──────────────┬───────────────────────┘
               │ MQTT
               ▼
         ┌───────────┐
         │ Mosquitto │
         └─────┬─────┘
               ▼
         ┌───────────┐   NATS   ┌───────────┐
         │    ACL    │ ───────► │ Telemetry │  ← сохраняет в БД
         └───────────┘          └───────────┘
                                ┌───────────┐
                                │ Automation│  ← срабатывают правила
                                └───────────┘
```

**Что НЕ делает:** не управляет устройствами, не отвечает на команды, не
меняет `device.online`. Команды `switch_on`/`switch_off` идут из `automation`
в `device`-сервис, симулятор в этой цепочке не участвует.

## Метрики по типу устройства

Профили заданы в функции `metrics_for_device()` в `main.py`.

| `type` | `model` содержит | Метрики |
|---|---|---|
| `sensor` | `motion` | `motion` — 0/1, P(1)=0.15 |
| `sensor` | `temperature`, `monitor`, `temp` | `temperature` (°C, μ=22, σ=2), `humidity` (%, μ=45, σ=5) |
| `sensor` | *(другое)* | `temperature` (°C, μ=22, σ=2) |
| `actuator` | `plug`, `relay` | `power` (W, μ=120, σ=20), `switch` — 0/1, P(1)=0.7 |
| `actuator` | *(другое)* | `power` (W, μ=100, σ=15) |
| `camera` | — | `recording` — 0/1, P(1)=0.9 |
| `gateway` | — | *пропускается* (телеметрию не эмитит) |

Новое устройство, добавленное в БД, подхватывается автоматически раз в
`RELOAD_SEC` секунд.

## Быстрый старт

### В составе docker-compose (рекомендуется)

```bash
docker compose up -d --build simulator
docker compose logs -f simulator
```

Сервис уже настроен в `docker-compose.yml`: ждёт `db` (healthy) и `mqtt`,
получает `DATABASE_URL`.

### Локально (для отладки)

```bash
# из корня проекта (где лежат common/, services/, simulator/)
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/smarthome
export MQTT_URL=localhost
export MQTT_PORT=1883
export INTERVAL_SEC=5
export RELOAD_SEC=60

python -m simulator.main
```

> ⚠️ Запускать только через `-m`. `python simulator/main.py` упадёт с
> `ModuleNotFoundError: No module named 'common'` — не найдётся пакет.

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `DATABASE_URL` | — (обязательна) | `postgresql+asyncpg://user:pass@host:5432/db` |
| `MQTT_URL` | `mqtt` | Хост MQTT-брокера |
| `MQTT_PORT` | `1883` | Порт MQTT-брокера |
| `INTERVAL_SEC` | `5` | Интервал между публикациями (сек) |
| `RELOAD_SEC` | `60` | Как часто перечитывать список устройств из БД (сек) |

## Формат сообщения

Публикуется в топик `smarthome/telemetry`, QoS 1:

```json
{
  "device_id": 1,
  "metric": "temperature",
  "value": 24.3,
  "unit": "°C"
}
```

| Поле | Тип | Значения |
|---|---|---|
| `device_id` | int | `device.id` из БД |
| `metric` | str | `temperature` \| `humidity` \| `motion` \| `power` \| `switch` \| `recording` |
| `value` | float | для бинарных метрик — `0` или `1` |
| `unit` | str \| null | `°C` \| `%` \| `W` \| `null` |

## Логи

```
INFO  MQTT connected to mqtt:1883
INFO  Loaded 43 devices → 61 metric profiles (skipped: 3)
INFO  Simulator running: interval=5s, reload=60s
INFO  Published 61 messages (total: 61)
INFO  Published 61 messages (total: 122)
...
INFO  Loaded 44 devices → 63 metric profiles (skipped: 3)   ← reload через 60с
```

| Строка | Что значит |
|---|---|
| `Loaded N devices → M metric profiles` | N устройств в БД, M профилей метрик (одно устройство может дать несколько метрик) |
| `skipped: K` | K устройств без метрик (обычно gateway) |
| `Workload is empty` | В БД нет устройств — добавьте через `POST /devices` |
| `DB not ready (...), retry in 3s` | БД не отвечает — ждёт и повторяет |
| `MQTT not ready (...), retry in 3s` | MQTT не отвечает — ждёт и повторяет |

## Проверка, что всё работает

### 1. Симулятор публикует

```bash
docker compose logs --tail=20 simulator
# Published 61 messages (total: N)
```

### 2. ACL принимает и бриджит в NATS

```bash
docker compose logs --tail=20 acl
# Bridged → {'device_id': 1, 'metric': 'temperature', 'value': 24.3, 'unit': '°C'}
```

### 3. Telemetry сохраняет в БД

```bash
docker compose logs --tail=20 telemetry
# Saved reading: {'device_id': 1, 'metric': 'temperature', ...}
```

### 4. В БД растут данные

```bash
docker compose exec db psql -U postgres -d smarthome -c \
  "SELECT metric, COUNT(*), ROUND(AVG(value)::numeric, 2) AS avg
   FROM telemetry_reading GROUP BY metric ORDER BY metric;"
```

Ожидаемо:

```
   metric    | count |  avg
-------------+-------+-------
 humidity    |  5760 | 45.02
 motion      |  1440 |  0.15
 power       |  2880 | 119.87
 recording   |   720 |  0.90
 switch      |  2880 |  0.70
 temperature |  5760 | 22.01
```

### 5. Automation срабатывает

```bash
docker compose logs --tail=20 automation device | grep -E "Rule|Executed"
# Rule triggered: temp 27.3 > 25.0 on device 1
# Executed switch_off on device 1 (reason: temperature 27.3 > 25.0)
```

### 6. Через API

```bash
# свежие показания датчика 1
curl "http://localhost:8082/telemetry/1?limit=5"

# статистика по всем датчикам
curl "http://localhost:8082/telemetry/stats/all"

# сводка по метрикам
curl "http://localhost:8082/telemetry/stats/summary"
```

## Настройка под свои данные

### Добавить новый тип метрик

1. Создать устройство в БД:
   ```bash
   curl -X POST http://localhost:8081/devices \
     -H "Content-Type: application/json" \
     -d '{"house_id":1,"type":"sensor","vendor":"Acme","model":"CO2 Monitor"}'
   ```
2. Расширить `metrics_for_device()` в `main.py`:
   ```python
   if typ == "sensor":
       if "co2" in model:
           return [{"metric": "co2", "unit": "ppm",
                    "gen": "gauss", "base": 600.0, "std": 80.0}]
   ```
3. Пересобрать контейнер:
   ```bash
   docker compose up -d --build simulator
   ```

### Изменить частоту

```yaml
# docker-compose.yml, сервис simulator
environment:
  INTERVAL_SEC: "1"     # 1 публикация/сек на профиль
  RELOAD_SEC: "30"      # перечитывать устройства раз в 30с
```

### Нагрузочный тест

`INTERVAL_SEC=1` + 100 устройств × 2 метрики ≈ 120k строк `telemetry_reading`
за 10 минут. Полезно для проверки индексов и производительности статистики.

## Траблшутинг

| Симптом | Причина | Решение |
|---|---|---|
| `Workload is empty` | В БД нет устройств | `POST /devices` или `docker compose down -v && up -d` |
| `DB not ready` бесконечно | Неверный `DATABASE_URL` или БД не запущена | `docker compose ps db`, `docker compose logs db` |
| `MQTT not ready` бесконечно | Неверный `MQTT_URL`/`MQTT_PORT` | `docker compose ps mqtt`, `docker compose logs mqtt` |
| Публикует, но `telemetry_reading` не растёт | ACL или telemetry не работают | `docker compose logs acl telemetry` |
| `ModuleNotFoundError: No module named 'common'` | Запуск не из корня или `python main.py` | Из корня, `python -m simulator.main` |
| `AttributeError: 'Device' object has no attribute ...` | Рассинхрон `common/models.py` и схемы БД | Пересобрать образ, проверить `\d device` |

## Структура

```
simulator/
├── __init__.py
├── main.py       # точка входа, MQTT-клиент, основной цикл
└── README.md     # этот файл
```

Всё «интересное» — в двух функциях `main.py`:

| Функция | Что делает |
|---|---|
| `metrics_for_device(d)` | тип/модель устройства → список профилей метрик |
| `gen_value(profile)` | профиль → случайное значение (`gauss` или `binary`) |

Остальное — MQTT, БД, ретраи, reload.