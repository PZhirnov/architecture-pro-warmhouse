from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from common.config import settings

router = APIRouter(tags=["meta"], include_in_schema=False)

DOCS_SERVICES = {
    "BFF":        "http://localhost:8089/docs",
    "User":   "http://localhost:8086/docs",
    "Location":   "http://localhost:8085/docs",
    "Device":     "http://localhost:8087/docs",
    "Telemetry":  "http://localhost:8082/docs",
    "Automation": "http://localhost:8083/docs",
    "ACL":        "http://localhost:8084/docs",
}


@router.get("/api/docs", response_class=HTMLResponse)
async def docs_index():
    links = "".join(
        f'<li><a href="{url}" target="_blank">{name}</a> — <code>{url}</code></li>'
        for name, url in DOCS_SERVICES.items()
    )
    return f"""
    <html>
      <head><title>Smart Home — API Docs</title>
        <style>
          body {{ font-family: sans-serif; max-width: 720px; margin: 40px auto; }}
          code {{ background: #f0f0f0; padding: 2px 4px; border-radius: 3px; }}
        </style>
      </head>
      <body>
        <h1>Smart Home API — Documentation</h1>
        <ul>{links}</ul>
        <p>OpenAPI JSON:
          <a href="/api/openapi/user">user</a> ·
          <a href="/api/openapi/device">device</a> ·
          <a href="/api/openapi/telemetry">telemetry</a> ·
          <a href="/api/openapi/automation">automation</a> .
          <a href="/api/openapi/location">location</a>
        </p>
      </body>
    </html>
    """


@router.get("/api/openapi/{service}")
async def proxy_openapi(service: str):
    urls = {
        "bff":        "http://localhost:8089/openapi.json",
        "user": f"{settings.user_url}/openapi.json",
        "device":     f"{settings.device_url}/openapi.json",
        "telemetry":  f"{settings.telemetry_url}/openapi.json",
        "automation": f"{settings.automation_url}/openapi.json",
        "location": f"{settings.location_url}/openapi.json",
    }
    if service not in urls:
        raise HTTPException(404, "Unknown service")
    from services.bff.clients.base import BaseClient

    return await BaseClient(urls[service], timeout=5).get("")


@router.get("/api/docs-all", response_class=HTMLResponse)
async def docs_all():
    return """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Smart Home — All APIs</title>
        <link rel="stylesheet" href="/static/swagger-ui.css">
      </head>
      <body>
        <div id="swagger-ui"></div>
        <script src="/static/swagger-ui-bundle.js"></script>
        <script>
          SwaggerUIBundle({
            urls: [
              { url: "/api/openapi/bff",        name: "BFF" },
              { url: "/api/openapi/user",     name: "User" },
              { url: "/api/openapi/device",     name: "Device" },
              { url: "/api/openapi/telemetry",  name: "Telemetry" },
              { url: "/api/openapi/automation", name: "Automation" },
              { url: "/api/openapi/location", name: "Location" }
            ],
            dom_id: "#swagger-ui",
            deepLinking: true,
            presets: [SwaggerUIBundle.presets.apis],
            layout: "BaseLayout"
          });
        </script>
      </body>
    </html>
    """
