from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, intake, notes, audit

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(intake.router, prefix="/intake", tags=["intake"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
