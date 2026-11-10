from fastapi import APIRouter

router = APIRouter(tags=["meta"])


@router.get("/health", summary="Health-check BFF")
async def health():
    return {"service": "bff", "status": "ok"}