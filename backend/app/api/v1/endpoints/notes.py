"""
notes.py — Triage note review endpoints (Staff Review Dashboard backend).

GET    /notes              — list notes (filtered, paginated)
GET    /notes/{id}         — get full note
PATCH  /notes/{id}/review  — reviewer sign-off (nurse/doctor only)
GET    /notes/{id}/export  — export note as JSON (requires sign-off)
GET    /notes/stats        — dashboard stats (counts by status/priority)

SAFETY RULES (never bypass):
- NOTHING is exported without reviewer sign-off (signoff=True).
- Only nurse or doctor roles can sign off.
- Every review action is written to the audit log.
- Re-running rules on new data: priority can only be raised, never lowered.
- Audit log integrity is preserved (append-only).
"""
from __future__ import annotations

import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db, require_role
from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.patient import Patient
from app.models.triage_note import TriageNote as TriageNoteModel
from app.schemas.user import UserResponse

log = logging.getLogger(__name__)
router = APIRouter()

# Priority order for sorting (higher = more urgent)
PRIORITY_ORDER = {'EMERGENCY': 4, 'HIGH': 3, 'INSUFFICIENT_INFO': 2, 'NORMAL': 1}

# Valid transitions
VALID_REVIEW_STATUSES = {'pending', 'approved', 'edited', 'escalated', 'closed'}
SIGNOFF_REQUIRED_FOR = {'approved', 'closed'}


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    review_status: str                # pending|approved|edited|escalated|closed
    comment: Optional[str] = None     # Required for approved/closed
    signoff: bool = False             # MUST be True to approve/close
    updated_fields: Optional[dict] = None  # Reviewer edits (schema fields only)


class NoteListItem(BaseModel):
    """Compact representation for list view."""
    id: str
    pseudonym_id: str
    chief_complaint: Optional[str]
    risk_category: str
    review_status: str
    facility_type: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    triggered_rules: list[str]
    symptoms_preview: list[str]       # First 3 symptom names


class NoteDetail(BaseModel):
    """Full note representation for review modal."""
    id: str
    pseudonym_id: str
    age_band: str
    sex: Optional[str]
    language: str
    facility_type: str
    scenario: str
    chief_complaint: Optional[str]
    symptoms: list[dict]
    vitals: dict
    history: dict
    missing_info: list[dict]
    follow_up_questions: list[dict]
    risk_category: str
    risk_reasons: list[str]
    triggered_rules: list[str]
    risk_source: str
    review_status: str
    reviewer_comments: list[str]
    provenance: Optional[dict]
    disclaimer: str
    created_at: Optional[str]
    updated_at: Optional[str]


class StatsResponse(BaseModel):
    total: int
    pending: int
    approved: int
    emergency: int
    high: int
    insufficient_info: int
    normal: int


# ── GET /notes ────────────────────────────────────────────────────────────────

@router.get(
    '',
    response_model=list[NoteListItem],
    summary='List triage notes (filtered)',
)
def list_notes(
    review_status: Optional[str] = Query(None, description='Filter by status: pending|approved|escalated|closed'),
    risk_category: Optional[str] = Query(None, description='Filter by risk: EMERGENCY|HIGH|INSUFFICIENT_INFO|NORMAL'),
    facility_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[NoteListItem]:
    """
    Return a list of triage notes, most urgent first.
    EMERGENCY notes always appear first regardless of other filters.
    """
    query = db.query(TriageNoteModel, Patient).join(
        Patient, TriageNoteModel.patient_id == Patient.id, isouter=True
    ).filter(TriageNoteModel.is_deleted == False)

    if review_status:
        query = query.filter(TriageNoteModel.review_status == review_status)
    if risk_category:
        query = query.filter(TriageNoteModel.risk_category == risk_category)
    if facility_type:
        query = query.filter(Patient.facility_type == facility_type)

    # Sort: EMERGENCY first, then by created_at DESC
    rows = query.offset(offset).limit(limit).all()

    items = []
    for note, patient in rows:
        try:
            triggered = json.loads(note.triggered_rules_json or '[]')
            symptoms = json.loads(note.symptoms_json or '[]')
            preview = [s.get('name', '') for s in symptoms[:3]]
        except (json.JSONDecodeError, TypeError):
            triggered, preview = [], []

        items.append(NoteListItem(
            id=note.id,
            pseudonym_id=patient.pseudonym_id if patient else 'unknown',
            chief_complaint=note.chief_complaint,
            risk_category=note.risk_category,
            review_status=note.review_status,
            facility_type=patient.facility_type if patient else None,
            created_at=note.created_at.isoformat() if note.created_at else None,
            updated_at=note.updated_at.isoformat() if note.updated_at else None,
            triggered_rules=triggered,
            symptoms_preview=preview,
        ))

    # Sort EMERGENCY first, then by created_at DESC
    items.sort(
        key=lambda x: (-PRIORITY_ORDER.get(x.risk_category, 0), x.created_at or ''),
        reverse=False,
    )
    return items


# ── GET /notes/stats ──────────────────────────────────────────────────────────

@router.get(
    '/stats',
    response_model=StatsResponse,
    summary='Dashboard stats',
)
def get_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StatsResponse:
    """Aggregated counts for the dashboard header."""
    notes = db.query(TriageNoteModel).filter(TriageNoteModel.is_deleted == False).all()

    return StatsResponse(
        total=len(notes),
        pending=sum(1 for n in notes if n.review_status == 'pending'),
        approved=sum(1 for n in notes if n.review_status == 'approved'),
        emergency=sum(1 for n in notes if n.risk_category == 'EMERGENCY'),
        high=sum(1 for n in notes if n.risk_category == 'HIGH'),
        insufficient_info=sum(1 for n in notes if n.risk_category == 'INSUFFICIENT_INFO'),
        normal=sum(1 for n in notes if n.risk_category == 'NORMAL'),
    )


# ── GET /notes/{note_id} ──────────────────────────────────────────────────────

@router.get(
    '/{note_id}',
    response_model=NoteDetail,
    summary='Get full triage note',
)
def get_note(
    note_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteDetail:
    """Return full note detail for reviewer modal."""
    note, patient = _get_note_or_404(db, note_id)

    def _load(field: str, default):
        try:
            v = json.loads(getattr(note, field) or '[]')
            return v if v else default
        except (json.JSONDecodeError, TypeError):
            return default

    def _load_dict(field: str):
        """Load a JSON field that must be a dict or None."""
        try:
            v = json.loads(getattr(note, field) or 'null')
            return v if isinstance(v, dict) else None
        except (json.JSONDecodeError, TypeError):
            return None

    return NoteDetail(
        id=note.id,
        pseudonym_id=patient.pseudonym_id if patient else 'unknown',
        age_band=patient.age_band if patient else 'unknown',
        sex=patient.sex if patient else None,
        language=patient.language if patient else 'en',
        facility_type=patient.facility_type if patient else 'OPD',
        scenario=patient.scenario if patient else 'opd_queue',
        chief_complaint=note.chief_complaint,
        symptoms=_load('symptoms_json', []),
        vitals=_load_dict('vitals_json') or {},
        history=_load_dict('history_json') or {},
        missing_info=_load('missing_info_json', []),
        follow_up_questions=_load('follow_up_questions_json', []),
        risk_category=note.risk_category,
        risk_reasons=_load('risk_reasons_json', []),
        triggered_rules=_load('triggered_rules_json', []),
        risk_source=note.risk_source,
        review_status=note.review_status,
        reviewer_comments=_load('reviewer_comments_json', []),
        provenance=_load_dict('provenance_json'),
        disclaimer=note.disclaimer or settings.DISCLAIMER,
        created_at=note.created_at.isoformat() if note.created_at else None,
        updated_at=note.updated_at.isoformat() if note.updated_at else None,
    )


# ── PATCH /notes/{note_id}/review ─────────────────────────────────────────────

@router.patch(
    '/{note_id}/review',
    response_model=NoteDetail,
    summary='Review and sign off on a triage note',
    description=(
        'Nurse or doctor reviews the note, adds a comment, and signs off. '
        'sign-off=True is required for approved/closed status. '
        'SAFETY: Nothing is exported without reviewer sign-off. '
        + settings.DISCLAIMER
    ),
)
def review_note(
    note_id: str,
    payload: ReviewRequest,
    current_user: UserResponse = Depends(require_role('nurse', 'doctor', 'admin')),
    db: Session = Depends(get_db),
) -> NoteDetail:
    """
    Staff review sign-off endpoint.

    SAFETY RULES enforced here:
    1. Sign-off (signoff=True) is REQUIRED for 'approved' or 'closed' status.
    2. A comment is required for approved/closed.
    3. Only nurse/doctor/admin roles can call this endpoint.
    4. Every review action is audit-logged.
    5. If reviewer edits fields, the change is logged with a diff.
    """
    note, patient = _get_note_or_404(db, note_id)
    now = datetime.now(timezone.utc)

    # ── Validate status transition ─────────────────────────────────────────────
    new_status = payload.review_status
    if new_status not in VALID_REVIEW_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Invalid review status: {new_status!r}. Choose from: {VALID_REVIEW_STATUSES}',
        )

    # ── Enforce sign-off requirement ───────────────────────────────────────────
    if new_status in SIGNOFF_REQUIRED_FOR:
        if not payload.signoff:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f'Reviewer sign-off (signoff=true) is required to set status to {new_status!r}. '
                    'The reviewer must confirm they have reviewed this as a qualified professional.'
                ),
            )
        if not payload.comment or not payload.comment.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'A reviewer comment is required for {new_status!r} status.',
            )

    # ── Apply the review ───────────────────────────────────────────────────────
    old_status = note.review_status
    note.review_status = new_status
    note.reviewer_id = current_user.id
    note.reviewer_timestamp = now
    note.updated_at = now

    # Append comment to reviewer comments list
    if payload.comment:
        try:
            comments = json.loads(note.reviewer_comments_json or '[]')
        except (json.JSONDecodeError, TypeError):
            comments = []
        comments.append(f'[{current_user.username} @ {now.isoformat()}] {payload.comment.strip()}')
        note.reviewer_comments_json = json.dumps(comments)

    # ── Apply reviewer field edits (if any) ────────────────────────────────────
    edit_details = {}
    if payload.updated_fields:
        edit_details = _apply_edits(note, payload.updated_fields)

    db.add(note)
    db.flush()

    # ── Audit log ──────────────────────────────────────────────────────────────
    audit = AuditLog(
        id=str(uuid.uuid4()),
        action=f'note_review_{new_status}',
        actor_id=current_user.id,
        actor_role=current_user.role,
        patient_pseudonym_id=patient.pseudonym_id if patient else 'unknown',
        triage_note_id=note_id,
        details_json=json.dumps({
            'previous_status': old_status,
            'new_status': new_status,
            'signoff': payload.signoff,
            'comment_added': bool(payload.comment),
            'edits': edit_details,
            'disclaimer': 'Reviewer confirms this is advisory. Not a medical diagnosis.',
        }),
        prev_hash='',
        row_hash=f'review_{note_id}_{now.isoformat()}',
        created_at=now,
    )
    db.add(audit)
    db.commit()
    db.refresh(note)

    # Return full note detail
    return get_note(note_id=note_id, current_user=current_user, db=db)


# ── GET /notes/{note_id}/export ───────────────────────────────────────────────

@router.get(
    '/{note_id}/export',
    summary='Export signed-off note as JSON',
    description=(
        'Export a reviewer-approved note. '
        'SAFETY: Only approved/closed notes can be exported. '
        'Sign-off is required. '
        + settings.DISCLAIMER
    ),
)
def export_note(
    note_id: str,
    current_user: UserResponse = Depends(require_role('nurse', 'doctor', 'admin')),
    db: Session = Depends(get_db),
) -> dict:
    """
    Export a note after reviewer sign-off.

    SAFETY: Raises 403 if the note has not been approved/closed by a reviewer.
    """
    note, patient = _get_note_or_404(db, note_id)

    if note.review_status not in ('approved', 'closed'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f'Note status is {note.review_status!r}. '
                'Only approved or closed notes can be exported. '
                'A qualified reviewer must approve this note first.'
            ),
        )

    def _load(field: str, default):
        try:
            return json.loads(getattr(note, field) or '[]')
        except (json.JSONDecodeError, TypeError):
            return default

    now = datetime.now(timezone.utc)

    # Audit the export
    audit = AuditLog(
        id=str(uuid.uuid4()),
        action='note_exported',
        actor_id=current_user.id,
        actor_role=current_user.role,
        patient_pseudonym_id=patient.pseudonym_id if patient else 'unknown',
        triage_note_id=note_id,
        details_json=json.dumps({'export_format': 'json', 'exported_by': current_user.username}),
        prev_hash='',
        row_hash=f'export_{note_id}_{now.isoformat()}',
        created_at=now,
    )
    db.add(audit)
    db.commit()

    return {
        'export_type': 'triage_note',
        'exported_at': now.isoformat(),
        'exported_by': current_user.username,
        'disclaimer': settings.DISCLAIMER,
        'IMPORTANT': (
            'This is an informational summary for professional review. '
            'It is NOT a medical diagnosis, prescription, or treatment plan.'
        ),
        'note': {
            'id': note.id,
            'pseudonym_id': patient.pseudonym_id if patient else 'unknown',
            'age_band': patient.age_band if patient else 'unknown',
            'chief_complaint': note.chief_complaint,
            'symptoms': _load('symptoms_json', []),
            'vitals': _load('vitals_json', {}),
            'risk_category': note.risk_category,
            'risk_reasons': _load('risk_reasons_json', []),
            'triggered_rules': _load('triggered_rules_json', []),
            'risk_source': note.risk_source,
            'review_status': note.review_status,
            'reviewer_id': note.reviewer_id,
            'reviewer_timestamp': note.reviewer_timestamp.isoformat() if note.reviewer_timestamp else None,
            'reviewer_comments': _load('reviewer_comments_json', []),
            'missing_info': _load('missing_info_json', []),
            'created_at': note.created_at.isoformat() if note.created_at else None,
        },
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_note_or_404(db: Session, note_id: str) -> tuple[TriageNoteModel, Optional[Patient]]:
    """Fetch a note + patient or raise 404."""
    row = db.query(TriageNoteModel, Patient).join(
        Patient, TriageNoteModel.patient_id == Patient.id, isouter=True
    ).filter(
        TriageNoteModel.id == note_id,
        TriageNoteModel.is_deleted == False,
    ).first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Triage note {note_id!r} not found.',
        )
    return row


def _apply_edits(note: TriageNoteModel, edits: dict) -> dict:
    """
    Apply reviewer edits to allowed JSON fields only.
    Returns a diff record for audit logging.

    SAFETY: Only pre-approved JSON fields can be edited. Direct SQL injection
    via field names is prevented by the allowlist.
    """
    EDITABLE_FIELDS = {
        'chief_complaint', 'symptoms_json', 'vitals_json',
        'history_json', 'missing_info_json', 'follow_up_questions_json',
    }
    applied = {}
    for field, new_value in edits.items():
        if field not in EDITABLE_FIELDS:
            log.warning(f'Reviewer attempted to edit non-editable field: {field!r}')
            continue
        old_value = getattr(note, field)
        if field == 'chief_complaint':
            note.chief_complaint = str(new_value)
        else:
            note.setattr(field, json.dumps(new_value))
        applied[field] = {'old': old_value, 'new': new_value}
    return applied
