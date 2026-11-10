import httpx

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from common.swagger import setup_local_docs
from services.bff.routers import devices, docs, location, meta, rules, telemetry, user, health, dashboard

app = FastAPI(title="BFF API", docs_url=None, redoc_url=None)
setup_local_docs(app)

@app.exception_handler(httpx.HTTPStatusError)
async def upstream_error_handler(request: Request, exc: httpx.HTTPStatusError):
    """Пробрасывает статус downstream-сервиса клиенту BFF."""
    return JSONResponse(
        status_code=exc.response.status_code,
        content={
            "detail": f"Upstream error: {exc.request.url}",
            "upstream_body": exc.response.text[:500],
        },
    )


app.include_router(meta.router)
app.include_router(health.router)
app.include_router(docs.router)
app.include_router(dashboard.router)
app.include_router(devices.router)
app.include_router(telemetry.router)
app.include_router(rules.router)
app.include_router(location.router)
app.include_router(user.router)
