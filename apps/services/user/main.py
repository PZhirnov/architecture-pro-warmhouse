from fastapi import FastAPI

from common.swagger import setup_local_docs
from services.user.routes import router

app = FastAPI(
    title="Users Service",
    version="0.1.0",
    description="Управление пользователями платформы",
    docs_url=None,
    redoc_url=None,
)
setup_local_docs(app)
app.include_router(router)


@app.get("/health", tags=["meta"], summary="Health-check")
async def health():
    return {"service": "users", "status": "ok"}
