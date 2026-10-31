
import sys
from pathlib import Path


# НАСТРОЙКИ ЗАПУСКА - меняем под конкретный сервис

HOST = "127.0.0.1"     # "0.0.0.0" — если нужен доступ с других машин
PORT = 8000
RELOAD = True          # автоперезагрузка при изменении кода
LOG_LEVEL = "info"     # critical | error | warning | info | debug | trace


# Чтобы `from app...` работал при запуске из корня проекта
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    import uvicorn

    print(f"▶  http://{HOST}:{PORT}")
    print(f"📖 Swagger: http://{HOST}:{PORT}/docs")
    print(f"❤  Health:  http://{HOST}:{PORT}/health")
    print("   Ctrl+C — остановить\n")

    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        reload_dirs=[str(ROOT / "app")] if RELOAD else None,
        log_level=LOG_LEVEL,
    )


if __name__ == "__main__":
    main()
