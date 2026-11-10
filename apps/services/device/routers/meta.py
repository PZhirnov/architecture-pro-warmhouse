from fastapi import APIRouter

router = APIRouter(tags=["meta"])


@router.get("/health", summary="Health-check device")
async def health():
    return {"service": "device", "status": "ok"}
