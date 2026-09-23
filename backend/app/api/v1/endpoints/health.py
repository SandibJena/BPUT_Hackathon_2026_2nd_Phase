from fastapi import APIRouter
from app.schemas.common import HealthResponse
from app.core.config import settings

router = APIRouter()

@router.get("", response_model=HealthResponse)
def get_health():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        disclaimer=settings.DISCLAIMER
    )
