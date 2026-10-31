# ... продолжение app/main.py после app.include_router(commands.router)

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.config import settings
from app.database import engine
from app.routers import commands, devices, houses, rooms, telemetry, users

from fastapi.openapi.docs import get_swagger_ui_html
from starlette.staticfiles import StaticFiles


# ============================================================
# Lifespan: проверка подключения к БД при старте/остановке
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print(f"✅ Connected to database: {settings.database_url.split('@')[-1]}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise

    yield

    # Shutdown
    await engine.dispose()
    print("🛑 Database connections closed")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
    description="API платформы умного дома (MVP)",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None
)

# Монтируем папку static
app.mount("/static", StaticFiles(directory="static"), name="static")


# ============================================================
# CORS
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для MVP; на проде — конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Глобальные обработчики ошибок
# ============================================================
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Нарушение UNIQUE / FK / CHECK — отдаём 409 вместо 500."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "Database integrity error",
            "error": str(exc.orig) if exc.orig else str(exc),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """Прочие ошибки БД — 500 с кратким описанием."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error", "error": str(exc)},
    )


# ============================================================
# Роутеры
# ============================================================
app.include_router(users.router)
app.include_router(houses.router)
app.include_router(rooms.router)
app.include_router(devices.router)
app.include_router(telemetry.router)
app.include_router(commands.router)


# ============================================================
# Служебные эндпоинты
# ============================================================
@app.get("/", tags=["meta"])
async def root():
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health", tags=["meta"])
async def health():
    """Проверка живости приложения и доступности БД."""
    db_ok = True
    db_error: str | None = None
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_ok = False
        db_error = str(e)

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "up" if db_ok else "down",
        "error": db_error,
    }



# 3. Создаём свой эндпоинт для документации
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url="/static/favicon-32x32.png",
    )
