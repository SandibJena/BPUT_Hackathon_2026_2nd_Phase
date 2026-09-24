"""
test_notes.py — Stage 3 tests for notes list, review, and sign-off enforcement.

Verified requirements:
1. GET /notes  → returns list sorted EMERGENCY first
2. GET /notes/{id} → returns full note detail
3. PATCH /notes/{id}/review → nurse can approve with sign-off
4. PATCH /notes/{id}/review → BLOCKS approval without sign-off
5. PATCH /notes/{id}/review → BLOCKS approval without comment
6. PATCH /notes/{id}/review → health_worker CANNOT approve (403)
7. GET /notes/{id}/export → blocked if not approved
8. GET /notes/{id}/export → works after sign-off
9. STT service unit tests
10. Voice endpoint status check
"""
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.patient import Patient
from app.models.consent_record import ConsentRecord
from app.models.triage_note import TriageNote as TriageNoteModel
from app.models.audit_log import AuditLog
from app.models import user as user_model  # ensure user table created


# ── Test DB fixtures ──────────────────────────────────────────────────────────
TEST_DB_PATH = "./test_notes_stage3.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """
    Create test DB, override get_db, run all module tests, then restore.
    Must be scoped to module so the override applies to every test here.
    """
    # Create all tables in OUR engine
    Base.metadata.create_all(bind=engine)
    # Override the app's DB dependency to use our test engine
    app.dependency_overrides[get_db] = _override_get_db
    yield
    # Teardown
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    import os, time
    time.sleep(0.3)
    try:
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    except OSError:
        pass


@pytest.fixture
def client(setup_db):  # ensure setup_db runs first
    return TestClient(app)


@pytest.fixture
def db(setup_db):  # ensure setup_db runs first
    session = TestingSessionLocal()
    yield session
    session.close()


# ── Auth headers ──────────────────────────────────────────────────────────────
NURSE_HEADERS = {"Authorization": "Bearer mock-token-nurse_1"}
DOCTOR_HEADERS = {"Authorization": "Bearer mock-token-doctor_1"}
HW_HEADERS = {"Authorization": "Bearer mock-token-health_worker_1"}
ADMIN_HEADERS = {"Authorization": "Bearer mock-token-admin_1"}


# ── Helper: seed a note ───────────────────────────────────────────────────────
def seed_note(db, pseudonym_id="TEST-N001", risk_category="EMERGENCY",
              review_status="pending") -> str:
    """Insert a minimal patient + triage note into the test DB. Returns note_id."""
    import uuid
    from datetime import datetime, timezone
    from app.core.config import settings

    now = datetime.now(timezone.utc)

    consent = ConsentRecord(
        id=str(uuid.uuid4()), pseudonym_id=pseudonym_id,
        purpose="triage", language="en", consent_given=True, timestamp=now,
    )
    db.add(consent)
    db.flush()

    patient = Patient(
        id=str(uuid.uuid4()), pseudonym_id=pseudonym_id,
        age_band="46-60", sex="male", language="en",
        facility_type="OPD", scenario="opd_queue",
        consent_record_id=consent.id,
    )
    db.add(patient)
    db.flush()

    note_id = str(uuid.uuid4())
    note = TriageNoteModel(
        id=note_id,
        patient_id=patient.id,
        raw_text_input="Chest pain and sweating since morning.",
        chief_complaint="Chest pain with sweating",
        symptoms_json=json.dumps([{"name": "chest_pain", "assertion": "reported", "source": "text", "evidence": "chest pain"}]),
        vitals_json=json.dumps({"spo2": 94, "pulse": 98}),
        history_json=json.dumps({"chronic_conditions": ["hypertension"]}),
        missing_info_json=json.dumps([]),
        follow_up_questions_json=json.dumps([]),
        risk_category=risk_category,
        risk_reasons_json=json.dumps(["Possible urgency signal detected."]),
        triggered_rules_json=json.dumps(["RULE-003", "RULE-012"]),
        risk_source="rules_engine",
        review_status=review_status,
        reviewer_comments_json=json.dumps([]),
        disclaimer=settings.DISCLAIMER,
    )
    db.add(note)
    db.commit()
    return note_id


# ── Tests: GET /notes ─────────────────────────────────────────────────────────
class TestListNotes:
    def test_list_returns_200(self, client, db):
        seed_note(db, "TEST-LIST-001", "NORMAL")
        resp = client.get("/api/v1/notes", headers=NURSE_HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_emergency_sorted_first(self, client, db):
        seed_note(db, "TEST-SORT-001", "NORMAL")
        seed_note(db, "TEST-SORT-002", "EMERGENCY")
        resp = client.get("/api/v1/notes", headers=NURSE_HEADERS)
        assert resp.status_code == 200
        notes = resp.json()
        # EMERGENCY must appear before NORMAL
        categories = [n["risk_category"] for n in notes]
        em_idx = next((i for i, c in enumerate(categories) if c == "EMERGENCY"), None)
        norm_idx = next((i for i, c in enumerate(categories) if c == "NORMAL"), -1)
        if em_idx is not None and norm_idx >= 0:
            assert em_idx < norm_idx

    def test_filter_by_risk(self, client, db):
        seed_note(db, "TEST-FILTER-001", "HIGH")
        resp = client.get("/api/v1/notes?risk_category=HIGH", headers=NURSE_HEADERS)
        assert resp.status_code == 200
        for note in resp.json():
            assert note["risk_category"] == "HIGH"

    def test_filter_by_status(self, client, db):
        seed_note(db, "TEST-FILTER-002", "NORMAL", review_status="pending")
        resp = client.get("/api/v1/notes?review_status=pending", headers=NURSE_HEADERS)
        assert resp.status_code == 200
        for note in resp.json():
            assert note["review_status"] == "pending"

    def test_requires_auth(self, client):
        resp = client.get("/api/v1/notes")
        assert resp.status_code == 401


# ── Tests: GET /notes/stats ───────────────────────────────────────────────────
class TestStats:
    def test_stats_returns_counts(self, client, db):
        seed_note(db, "STAT-001", "EMERGENCY")
        resp = client.get("/api/v1/notes/stats", headers=NURSE_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "emergency" in data
        assert data["total"] >= 1
        assert data["emergency"] >= 1


# ── Tests: GET /notes/{id} ────────────────────────────────────────────────────
class TestGetNote:
    def test_get_note_returns_full_detail(self, client, db):
        note_id = seed_note(db, "TEST-GET-001", "EMERGENCY")
        resp = client.get(f"/api/v1/notes/{note_id}", headers=NURSE_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == note_id
        assert data["risk_category"] == "EMERGENCY"
        assert "disclaimer" in data
        assert "symptoms" in data
        assert "triggered_rules" in data

    def test_get_nonexistent_returns_404(self, client):
        resp = client.get("/api/v1/notes/nonexistent-id", headers=NURSE_HEADERS)
        assert resp.status_code == 404


# ── Tests: PATCH /notes/{id}/review ──────────────────────────────────────────
class TestReviewNote:
    def test_nurse_can_approve_with_signoff(self, client, db):
        """Core safety rule: nurse + signoff=True + comment → approved."""
        note_id = seed_note(db, "TEST-APPROVE-001")
        resp = client.patch(
            f"/api/v1/notes/{note_id}/review",
            headers=NURSE_HEADERS,
            json={
                "review_status": "approved",
                "comment": "Reviewed and confirmed. Patient referred for immediate assessment.",
                "signoff": True,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["review_status"] == "approved"

    def test_approval_blocked_without_signoff(self, client, db):
        """SAFETY: Must not approve without signoff=True."""
        note_id = seed_note(db, "TEST-NOSIGN-001")
        resp = client.patch(
            f"/api/v1/notes/{note_id}/review",
            headers=NURSE_HEADERS,
            json={
                "review_status": "approved",
                "comment": "Looks fine.",
                "signoff": False,          # ← missing sign-off
            },
        )
        assert resp.status_code == 400
        assert "sign-off" in resp.json()["detail"].lower() or "signoff" in resp.json()["detail"].lower()

    def test_approval_blocked_without_comment(self, client, db):
        """SAFETY: Must not approve without a reviewer comment."""
        note_id = seed_note(db, "TEST-NOCOMMENT-001")
        resp = client.patch(
            f"/api/v1/notes/{note_id}/review",
            headers=NURSE_HEADERS,
            json={
                "review_status": "approved",
                "comment": "",             # ← empty comment
                "signoff": True,
            },
        )
        assert resp.status_code == 400
        assert "comment" in resp.json()["detail"].lower()

    def test_health_worker_cannot_approve(self, client, db):
        """SAFETY: health_worker role MUST be blocked from approving."""
        note_id = seed_note(db, "TEST-HW-NOAPPROVE-001")
        resp = client.patch(
            f"/api/v1/notes/{note_id}/review",
            headers=HW_HEADERS,           # ← health_worker token
            json={
                "review_status": "approved",
                "comment": "Approved.",
                "signoff": True,
            },
        )
        assert resp.status_code == 403

    def test_escalate_without_signoff(self, client, db):
        """Escalate does NOT require signoff."""
        note_id = seed_note(db, "TEST-ESC-001")
        resp = client.patch(
            f"/api/v1/notes/{note_id}/review",
            headers=NURSE_HEADERS,
            json={
                "review_status": "escalated",
                "comment": "Escalating for senior review.",
                "signoff": False,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["review_status"] == "escalated"

    def test_invalid_status_rejected(self, client, db):
        note_id = seed_note(db, "TEST-INV-001")
        resp = client.patch(
            f"/api/v1/notes/{note_id}/review",
            headers=NURSE_HEADERS,
            json={"review_status": "banana", "signoff": False},
        )
        assert resp.status_code == 400

    def test_review_note_not_found(self, client):
        resp = client.patch(
            "/api/v1/notes/no-such-id/review",
            headers=NURSE_HEADERS,
            json={"review_status": "escalated", "comment": "x", "signoff": False},
        )
        assert resp.status_code == 404


# ── Tests: GET /notes/{id}/export ────────────────────────────────────────────
class TestExportNote:
    def test_export_blocked_if_pending(self, client, db):
        """SAFETY: pending note MUST NOT be exportable."""
        note_id = seed_note(db, "TEST-EXP-BLOCK-001", review_status="pending")
        resp = client.get(f"/api/v1/notes/{note_id}/export", headers=DOCTOR_HEADERS)
        assert resp.status_code == 403

    def test_export_works_after_approval(self, client, db):
        """Export unlocked only after sign-off."""
        note_id = seed_note(db, "TEST-EXP-OK-001", review_status="pending")
        # First approve it
        client.patch(
            f"/api/v1/notes/{note_id}/review",
            headers=DOCTOR_HEADERS,
            json={
                "review_status": "approved",
                "comment": "Reviewed and approved for export.",
                "signoff": True,
            },
        )
        # Now export
        resp = client.get(f"/api/v1/notes/{note_id}/export", headers=DOCTOR_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "disclaimer" in data
        assert "IMPORTANT" in data
        assert data["note"]["review_status"] == "approved"

    def test_export_health_worker_blocked(self, client, db):
        """health_worker cannot export even if approved."""
        note_id = seed_note(db, "TEST-EXP-HW-001", review_status="approved")
        resp = client.get(f"/api/v1/notes/{note_id}/export", headers=HW_HEADERS)
        assert resp.status_code == 403


# ── Tests: STT service unit tests ─────────────────────────────────────────────
class TestSTTService:
    def test_whisper_available(self):
        from app.services.stt.whisper_stt import whisper_available
        assert whisper_available() is True

    def test_empty_audio_returns_empty(self):
        from app.services.stt.whisper_stt import transcribe_audio_bytes
        # Empty bytes → returns empty transcript immediately (no model load)
        result = transcribe_audio_bytes(b"", "test.wav", "en")
        assert result["transcript"] == ""
        assert result["warning"] != ""
        assert result["model_used"] == "none"

    def test_voice_status_endpoint(self, client):
        # Does NOT transcribe; just checks availability metadata
        resp = client.get("/api/v1/intake/voice/status", headers=HW_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "server_stt_available" in data
        assert "browser_fallback" in data
        assert "max_file_mb" in data
