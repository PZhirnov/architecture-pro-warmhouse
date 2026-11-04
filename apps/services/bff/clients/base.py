import httpx


class BaseClient:
    """Тонкая обёртка над httpx. Один AsyncClient на вызов — для MVP."""

    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def _request(self, method: str, path: str, **kwargs) -> dict | list:
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.request(method, f"{self.base_url}{path}", **kwargs)
            r.raise_for_status()
            return r.json()

    async def get(self, path: str, **kwargs) -> dict | list:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> dict | list:
        return await self._request("POST", path, **kwargs)

    async def ping(self) -> dict:
        """Проверка /health downstream-сервиса. Не бросает исключение."""
        import time
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as c:
                r = await c.get(f"{self.base_url}/health")
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            ok = 200 <= r.status_code < 300
            body: dict
            try:
                body = r.json()
            except Exception:
                body = {"raw": r.text[:200]}
            return {
                "status": "ok" if ok else "error",
                "http_code": r.status_code,
                "latency_ms": elapsed_ms,
                "body": body,
            }
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            return {
                "status": "unreachable",
                "http_code": None,
                "latency_ms": elapsed_ms,
                "error": f"{type(e).__name__}: {e}",
            }
