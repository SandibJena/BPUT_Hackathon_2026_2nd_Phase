from fastapi import APIRouter, Depends
from app.api.deps import require_role
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("")
def list_audit(current_user: UserResponse = Depends(require_role("admin"))):
    return []

@router.get("/verify")
def verify_audit(current_user: UserResponse = Depends(require_role("admin"))):
    return {"status": "ok"}
