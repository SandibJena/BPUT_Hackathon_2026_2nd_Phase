from fastapi import APIRouter, Depends
from app.schemas.triage import TextIntakeRequest, TriageNote, PatientInfo
from app.api.deps import get_current_user
from app.schemas.user import UserResponse
from app.core.config import settings

router = APIRouter()

@router.post("/text", response_model=TriageNote)
def intake_text(request: TextIntakeRequest, current_user: UserResponse = Depends(get_current_user)):
    patient_info = PatientInfo(
        pseudonym_id=request.pseudonym_id,
        age_band=request.age_band,
        sex=request.sex,
        language=request.language,
        facility_type=request.facility_type,
        scenario=request.scenario
    )
    return TriageNote(
        id="mock-note-id",
        patient=patient_info,
        chief_complaint=request.chief_complaint,
        disclaimer=settings.DISCLAIMER
    )

@router.post("/voice")
def intake_voice():
    return {"status": "stub"}

@router.post("/report")
def intake_report():
    return {"status": "stub"}

@router.post("/image")
def intake_image():
    return {"status": "stub"}
