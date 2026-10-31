# ============================================================
# Stage 1: builder — установка зависимостей в отдельный слой
# ============================================================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Системные зависимости для сборки (bcrypt, asyncpg и т.п.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Ставим зависимости в отдельную директорию — потом скопируем в runtime
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt


# ============================================================
# Stage 2: runtime — минимальный образ без компиляторов
# ============================================================
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    # Uvicorn: 2 воркера по умолчанию (настроить под CPU)
    WEB_CONCURRENCY=2

# Только runtime-библиотеки (без -dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root пользователь
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --shell /bin/bash --create-home app

WORKDIR /app

# Зависимости из builder
COPY --from=builder /install /usr/local

# Код приложения
COPY --chown=app:app app ./app
COPY --chown=app:app static ./static

# Если нужны SQL-скрипты (schema.sql, seed.sql) — для инициализации
# COPY --chown=app:app schema.sql seed.sql ./

USER app

EXPOSE 8000

# Healthcheck — использует ваш /health эндпоинт
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Запуск через uvicorn. Для продакшена — без --reload!
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
