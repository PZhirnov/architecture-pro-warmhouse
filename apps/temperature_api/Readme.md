# temperature_api

Общие сведения:
Простой HTTP-сервис, отдающий случайную температуру для комнаты.

Порт по умолчанию: **8081**.

🚀 Сборка и запуск
```bash
# собрать
docker build -t temperature_api .

# запустить
docker run -d --name temperature_api -p 8081:8081 temperature-service

# остановить (контейнер останется, но будет остановлен)
docker stop temperature_api

# остановить и удалить контейнер
docker rm -f temperature_api
```

## Эндпоинты:

### `GET /temperature`

Температура по query-параметрам.

**Query-параметры**

| Параметр   | Тип    | Обязательный | Описание                                   |
|------------|--------|--------------|--------------------------------------------|
| `location` | string | нет          | Название комнаты (`Living Room`, `Bedroom`, `Kitchen`) |
| `sensorId` | string | нет          | Идентификатор датчика (`1`, `2`, `3`)      |

**Логика разрешения параметров**

- Если `location` не передан — определяется по `sensorId`:
  `1` → Living Room, `2` → Bedroom, `3` → Kitchen, иначе `Unknown`.
- Если `sensorId` не передан — определяется по `location` (обратный маппинг), иначе `0`.
- Если переданы оба — используются как есть.

**Примеры**

```bash
curl "http://localhost:8081/temperature?location=Bedroom"
curl "http://localhost:8081/temperature?sensorId=3"
curl "http://localhost:8081/temperature?location=Kitchen&sensorId=1"
```
### GET /temperature/<sensorId>
Температура по датчику, переданному в пути. location можно опционально уточнить query-параметром.

##### Path-параметры
Параметр	Тип	Описание
sensorId	string	Идентификатор датчика



##### Query-параметры

Параметр	Тип	Обязательный	Описание
location	string	нет	Название комнаты
Примеры

bash
curl "http://localhost:8081/temperature/3"
curl "http://localhost:8081/temperature/1?location=Garage"


# Структура проекта
```
temperature_api/
├── app/
│   ├── __init__.py          # app factory
│   ├── config.py            # конфигурация
│   ├── routes/
│   │   ├── __init__.py
│   │   └── temperature.py   # blueprint с эндпоинтом /temperature
│   ├── services/
│   │   ├── __init__.py
│   │   └── temperature.py   # бизнес-логика: маппинг + генерация
│   └── data/
│       ├── __init__.py
│       └── sensors.py       # справочники location <-> sensorId
├── run.py                   # точка входа
├── requirements.txt
└── .gitignore
```

