from contextlib import asynccontextmanager

from fastapi import FastAPI

from common.nats_client import connect
from common.swagger import setup_local_docs

from services.telemetry.handlers import register_handlers
from services.telemetry.routers import router as telemetry_router

_nc = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _nc
    _nc = await connect()
    await register_handlers(_nc)
    yield
    if _nc:
        await _nc.drain()


app = FastAPI(title="Telemetry Service", lifespan=lifespan)
setup_local_docs(app)
app.include_router(telemetry_router)
