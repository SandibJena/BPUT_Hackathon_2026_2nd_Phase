from fastapi import APIRouter, Depends, Query
from app.api.deps import get_current_user, require_role
from app.schemas.user import UserResponse
from typing import Optional

router = APIRouter()

@router.get("")
def list_notes(status: Optional[str] = None, risk_category: Optional[str] = None, facility_type: Optional[str] = None, current_user: UserResponse = Depends(get_current_user)):
    return []

@router.get("/{note_id}")
def get_note(note_id: str, current_user: UserResponse = Depends(get_current_user)):
    return {"id": note_id, "status": "stub"}

@router.patch("/{note_id}/review")
def review_note(note_id: str, status: str, current_user: UserResponse = Depends(require_role("nurse", "doctor"))):
    return {"id": note_id, "status": status}
