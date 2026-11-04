# ---- Базовый образ ----
FROM python:3.11-slim

# Не писать .pyc, не буферизовать stdout/stderr (важно для логов)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Рабочая директория
WORKDIR /app

# Сначала зависимости — чтобы кэш слоя не сбрасывался при изменении кода
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Затем код
COPY . .

# Непривилегированный пользователь
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Порт, который слушает gunicorn
EXPOSE 8081

# Healthcheck — чтобы docker/compose видели, что сервис жив
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8081/temperature/1').status == 200 else 1)"

# Продакшн-запуск: gunicorn, а не app.run()
CMD ["gunicorn", "--bind", "0.0.0.0:8081", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-", "run:app"]
