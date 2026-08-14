from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["health"])

@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "UP", "service": settings.APP_NAME, "version": settings.APP_VERSION}
