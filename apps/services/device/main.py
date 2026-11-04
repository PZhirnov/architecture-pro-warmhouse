from contextlib import asynccontextmanager

from fastapi import FastAPI

from common.nats_client import connect
from common.swagger import setup_local_docs
from services.device.handlers.command_handler import register_handlers
from services.device.routers import devices, houses, meta

_nc = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _nc
    _nc = await connect()
    await register_handlers(_nc)
    yield
    if _nc:
        await _nc.drain()


app = FastAPI(
    title="Device Service",
    version="0.1.0",
    description="Сервис управления устройствами платформы умного дома (MVP)",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)
setup_local_docs(app)

app.include_router(meta.router)
app.include_router(devices.router)
app.include_router(houses.router)
