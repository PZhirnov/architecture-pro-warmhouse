from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def setup_local_docs(app: FastAPI) -> None:
    """Заменяет стандартный /docs на локальный Swagger UI (без CDN)."""

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Убираем встроенный /docs
    app.docs_url = None

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " — Docs",
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
            swagger_favicon_url="/static/favicon-32x32.png",
        )
