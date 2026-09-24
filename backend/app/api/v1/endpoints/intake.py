"""
intake.py — Patient intake endpoints.

POST /intake/text   — full text triage pipeline
POST /intake/voice  — audio → faster-whisper transcript → text pipeline
POST /intake/report — stub (Stage 4: OCR pipeline)
POST /intake/image  — stub (Stage 5: image understanding)

SAFETY: All routes require auth. Consent required. Audit log on every call.
"""
from __future__ import annotations

import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.consent_record import ConsentRecord
from app.models.patient import Patient
from app.models.triage_note import TriageNote as TriageNoteModel
from app.schemas.triage import History, TextIntakeRequest, TriageNote, Vitals
from app.schemas.user import UserResponse
from app.services.pipeline import run_text_pipeline
from app.services.stt.whisper_stt import (
    SUPPORTED_AUDIO_TYPES,
    transcribe_audio_bytes,
    whisper_available,
)

log = logging.getLogger(__name__)
router = APIRouter()

# Max audio upload: 25 MB
MAX_AUDIO_MB = 25
MAX_AUDIO_BYTES = MAX_AUDIO_MB * 1024 * 1024


@router.post(
    '/text',
    response_model=TriageNote,
    summary='Text intake — full triage pipeline',
    description=(
        'Accept patient-reported symptoms as text, run the full triage pipeline '
        '(PII masking → rules engine → optional LLM extraction → risk merge) '
        'and return a structured TriageNote for professional review. '
        + settings.DISCLAIMER
    ),
)
def intake_text(
    request: TextIntakeRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TriageNote:
    if not request.consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Patient consent is required before processing any information.',
        )

    note_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    try:
        triage_note = run_text_pipeline(request, note_id=note_id)
        try:
            _persist_note(db, request, triage_note, note_id, now, current_user.id)
        except Exception as db_err:
            log.error(f'DB persistence failed for note {note_id}: {db_err}')
        return triage_note

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        log.error(f'Pipeline error for note {note_id}: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Triage pipeline error. Note routed to HIGH priority for human review.',
        )


@router.post(
    '/voice',
    response_model=TriageNote,
    summary='Voice intake — faster-whisper STT + triage pipeline',
    description=(
        'Accept an audio recording, transcribe it server-side with faster-whisper, '
        'then run the full triage pipeline. Falls back gracefully if STT is unavailable. '
        + settings.DISCLAIMER
    ),
)
async def intake_voice(
    audio: UploadFile = File(..., description='Audio file (wav/mp3/webm/ogg, max 25MB)'),
    pseudonym_id: str = Form(...),
    age_band: str = Form('unknown'),
    sex: Optional[str] = Form(None),
    language: str = Form('en'),
    facility_type: str = Form('OPD'),
    scenario: str = Form('opd_queue'),
    chief_complaint: str = Form('Voice intake — see transcript'),
    consent_given: bool = Form(...),
    # Optional vitals via form
    spo2: Optional[float] = Form(None),
    temp: Optional[float] = Form(None),
    pulse: Optional[int] = Form(None),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TriageNote:
    """
    Voice intake flow:
    1. Validate audio file type and size
    2. Read audio bytes
    3. Transcribe with faster-whisper (or return error if unavailable)
    4. Run text pipeline on transcript
    5. Persist and return TriageNote
    """
    # ── Consent check ──────────────────────────────────────────────────────────
    if not consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Patient consent is required before processing voice input.',
        )

    # ── Validate file type ─────────────────────────────────────────────────────
    content_type = audio.content_type or ''
    filename = audio.filename or 'audio.wav'
    if content_type not in SUPPORTED_AUDIO_TYPES and not any(
        filename.lower().endswith(ext)
        for ext in ['.wav', '.mp3', '.webm', '.ogg', '.m4a', '.flac']
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f'Unsupported audio format: {content_type}. Use wav/mp3/webm/ogg.',
        )

    # ── Read audio bytes ───────────────────────────────────────────────────────
    audio_bytes = await audio.read()
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f'Audio file too large. Max {MAX_AUDIO_MB}MB.',
        )
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Empty audio file received.',
        )

    # ── Transcribe ─────────────────────────────────────────────────────────────
    if not whisper_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                'Server-side transcription is not available. '
                'Please use the text intake endpoint or browser voice mode.'
            ),
        )

    stt_result = transcribe_audio_bytes(
        audio_bytes=audio_bytes,
        filename=filename,
        language=language,
        model_name='base',  # Fast enough for hackathon; swap to 'small' for better accuracy
    )

    transcript = stt_result.get('transcript', '').strip()
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                stt_result.get('warning', 'No speech detected.')
                + ' Please re-record or use text intake.'
            ),
        )

    # ── Build text intake request from transcript ──────────────────────────────
    vitals = Vitals(spo2=spo2, temp=temp, pulse=pulse)
    text_request = TextIntakeRequest(
        pseudonym_id=pseudonym_id,
        age_band=age_band,
        sex=sex,
        language=language,
        facility_type=facility_type,
        scenario=scenario,
        chief_complaint=chief_complaint or transcript[:80],
        symptoms_text=transcript,
        vitals=vitals,
        history=History(),
        consent_given=True,
    )

    note_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    try:
        triage_note = run_text_pipeline(text_request, note_id=note_id)

        # Append STT metadata to provenance
        if triage_note.provenance:
            triage_note.provenance.inputs_used.append('voice')
            triage_note.provenance.steps.insert(
                0,
                f'Audio transcribed with faster-whisper/{stt_result.get("model_used", "base")} '
                f'({stt_result.get("duration_seconds", 0):.1f}s, '
                f'lang={stt_result.get("language_detected", "?")}) — '
                'Transcript requires health worker verification.',
            )

        try:
            _persist_note(db, text_request, triage_note, note_id, now, current_user.id,
                          extra_details={'stt_duration': stt_result.get('duration_seconds'),
                                        'stt_model': stt_result.get('model_used'),
                                        'stt_language': stt_result.get('language_detected')})
        except Exception as db_err:
            log.error(f'DB persistence failed for voice note {note_id}: {db_err}')

        return triage_note

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        log.error(f'Voice pipeline error for note {note_id}: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Voice triage pipeline error. Note routed to HIGH for human review.',
        )


@router.get(
    '/voice/status',
    summary='Check voice transcription availability',
)
def voice_status():
    """Returns whether server-side STT is available."""
    available = whisper_available()
    return {
        'server_stt_available': available,
        'engine': 'faster-whisper' if available else 'none',
        'browser_fallback': 'Web Speech API (Chrome/Edge/Safari)',
        'supported_formats': list(SUPPORTED_AUDIO_TYPES),
        'max_file_mb': MAX_AUDIO_MB,
        'disclaimer': settings.DISCLAIMER,
    }


@router.post('/report', summary='Report/OCR upload (Stage 4 — coming soon)')
def intake_report():
    return {
        'status': 'not_yet_implemented',
        'message': 'Report OCR pipeline (Tesseract) available in Stage 4.',
        'disclaimer': settings.DISCLAIMER,
    }


@router.post('/image', summary='Image understanding (Stage 5 — coming soon)')
def intake_image():
    return {
        'status': 'not_yet_implemented',
        'message': 'Image understanding available in Stage 5.',
        'disclaimer': settings.DISCLAIMER,
    }


# ── Persistence helper ─────────────────────────────────────────────────────────

def _persist_note(
    db: Session,
    request: TextIntakeRequest,
    note: TriageNote,
    note_id: str,
    now: datetime,
    actor_id: str,
    extra_details: dict | None = None,
) -> None:
    """Persist consent, patient, triage note, and audit log to DB."""
    consent = ConsentRecord(
        id=str(uuid.uuid4()),
        pseudonym_id=request.pseudonym_id,
        purpose='triage',
        language=request.language,
        consent_given=True,
        timestamp=now,
    )
    db.add(consent)
    db.flush()

    patient = Patient(
        id=str(uuid.uuid4()),
        pseudonym_id=request.pseudonym_id,
        age_band=request.age_band or 'unknown',
        sex=request.sex,
        language=request.language,
        facility_type=request.facility_type,
        scenario=request.scenario,
        consent_record_id=consent.id,
    )
    db.add(patient)
    db.flush()

    risk = note.risk
    db_note = TriageNoteModel(
        id=note_id,
        patient_id=patient.id,
        raw_text_input=request.symptoms_text,
        masked_text_input='[PII masked before LLM call]',
        chief_complaint=note.chief_complaint or request.chief_complaint,
        symptoms_json=json.dumps([s.model_dump() for s in note.symptoms]),
        vitals_json=json.dumps(note.vitals.model_dump() if note.vitals else {}),
        history_json=json.dumps(note.history.model_dump() if note.history else {}),
        missing_info_json=json.dumps([m.model_dump() for m in note.missing_info]),
        follow_up_questions_json=json.dumps([q.model_dump() for q in note.follow_up_questions]),
        risk_category=risk.category if risk else 'HIGH',
        risk_reasons_json=json.dumps(risk.reasons if risk else ['Pipeline error']),
        triggered_rules_json=json.dumps(risk.triggered_rules if risk else []),
        risk_source=risk.source if risk else 'fail_safe',
        review_status='pending',
        provenance_json=json.dumps(note.provenance.model_dump() if note.provenance else {}),
        disclaimer=settings.DISCLAIMER,
    )
    db.add(db_note)
    db.flush()

    details = {
        'risk_category': risk.category if risk else 'HIGH',
        'triggered_rules': risk.triggered_rules if risk else [],
        'llm_used': (risk.source or '').endswith('llm') if risk else False,
        'consent_given': True,
    }
    if extra_details:
        details.update(extra_details)

    audit = AuditLog(
        id=str(uuid.uuid4()),
        action='intake_submitted',
        actor_id=actor_id,
        actor_role='health_worker',
        patient_pseudonym_id=request.pseudonym_id,
        triage_note_id=note_id,
        details_json=json.dumps(details),
        prev_hash='',
        row_hash=f'intake_{note_id}',
        created_at=now,
    )
    db.add(audit)
    db.commit()
