from fastapi import FastAPI

from common.swagger import setup_local_docs
from services.location.routes import router as location_router

app = FastAPI(
    title="Locations Service",
    version="0.1.0",
    description="Управление домами, комнатами и привязками пользователей",
    docs_url=None,
    redoc_url=None,
)
setup_local_docs(app)
app.include_router(location_router)


@app.get("/health", tags=["meta"], summary="Health-check")
async def health():
    return {"service": "location", "status": "ok"}


