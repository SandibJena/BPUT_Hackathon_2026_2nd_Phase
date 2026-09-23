"""
Seed script â€” loads 25 synthetic patients and demo users into the database.
Run: python seed.py
Run with reset: python seed.py --reset

IMPORTANT: All data here is FICTIONAL / SYNTHETIC. No real patient records.
"""
import os
import sys
import json
import uuid
from datetime import datetime, timezone, timedelta

# Add parent to path so we can import app modules
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, init_db, engine
from app.models.base import Base
from app.models.user import User, RoleEnum
from app.models.patient import Patient
from app.models.consent_record import ConsentRecord
from app.models.triage_note import TriageNote
from app.models.audit_log import AuditLog
from app.core.config import settings

# â”€â”€ Paths â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic")
PATIENTS_FILE = os.path.join(DATA_DIR, "patients.json")
GROUND_TRUTH_FILE = os.path.join(DATA_DIR, "ground_truth.json")


def hash_password_mock(password: str) -> str:
    """Mock password hash for demo. Replace with bcrypt in production."""
    return f"mock_hashed_{password}"


def seed_users(db: Session) -> dict:
    """Create 4 demo users, one per role."""
    demo_users = [
        {"username": "health_worker_1", "password": "demo123", "role": RoleEnum.health_worker, "facility_type": "PHC"},
        {"username": "nurse_1",         "password": "demo123", "role": RoleEnum.nurse,         "facility_type": "PHC"},
        {"username": "doctor_1",        "password": "demo123", "role": RoleEnum.doctor,        "facility_type": "PHC"},
        {"username": "admin_1",         "password": "demo123", "role": RoleEnum.admin,         "facility_type": None},
    ]
    user_map = {}
    for u in demo_users:
        user = User(
            id=str(uuid.uuid4()),
            username=u["username"],
            hashed_password=hash_password_mock(u["password"]),
            role=u["role"],
            facility_type=u.get("facility_type"),
            is_active=True,
        )
        db.add(user)
        user_map[u["username"]] = user
        print(f"  âœ“ Created user: {u['username']} (role={u['role'].value})")
    db.flush()
    return user_map


def seed_patients(db: Session, ground_truth: dict) -> None:
    """Load 25 synthetic patients from patients.json."""
    if not os.path.exists(PATIENTS_FILE):
        print(f"  âš  patients.json not found at {PATIENTS_FILE}")
        return

    with open(PATIENTS_FILE, "r", encoding="utf-8") as f:
        patients_data = json.load(f)

    now = datetime.now(timezone.utc)
    purge_at = now + timedelta(hours=settings.DATA_RETENTION_HOURS)

    for p in patients_data:
        pid = p["pseudonym_id"]
        gt = ground_truth.get(pid, {})

        # Consent record
        consent = ConsentRecord(
            id=str(uuid.uuid4()),
            pseudonym_id=pid,
            purpose="Triage-support demonstration â€” BPUT Hackathon 2026",
            language=p.get("language", "en"),
            timestamp=now,
            consent_given=True,
        )
        db.add(consent)
        db.flush()

        # Patient record
        patient = Patient(
            id=str(uuid.uuid4()),
            pseudonym_id=pid,
            age_band=p.get("age_band") or "unknown",
            sex=p.get("sex"),
            language=p.get("language", "en"),
            facility_type=p.get("facility_type", "OPD"),
            scenario=p.get("scenario", "opd_queue"),
            consent_record_id=consent.id,
            purge_at=purge_at,
        )
        db.add(patient)
        db.flush()

        # Triage note (placeholder â€” real note created by pipeline in Stage 2+)
        expected_priority = p.get("expected_priority", gt.get("expected_priority", "NORMAL"))
        triggered_rules = p.get("expected_triggered_rules", gt.get("expected_triggered_rules", []))

        note = TriageNote(
            id=str(uuid.uuid4()),
            patient_id=patient.id,
            raw_text_input=p.get("symptoms_text", ""),
            masked_text_input="[MASKED â€” not yet processed]",
            chief_complaint=p.get("chief_complaint", ""),
            vitals_json=json.dumps(p.get("vitals", {})),
            history_json=json.dumps(p.get("history", {})),
            risk_category=expected_priority,
            risk_reasons_json=json.dumps(
                [f"Seeded from synthetic data. Expected: {expected_priority}"]
            ),
            triggered_rules_json=json.dumps(triggered_rules),
            risk_source="default",
            review_status="pending",
            provenance_json=json.dumps({
                "inputs_used": ["text"],
                "steps": ["Seeded from synthetic patients.json"],
                "llm_model": None,
                "masking_applied": False,
                "note": "Placeholder note â€” run pipeline to generate real triage note",
            }),
            disclaimer=settings.DISCLAIMER,
        )
        db.add(note)

        # Audit entry for seed action
        audit = AuditLog(
            id=str(uuid.uuid4()),
            action="patient_seeded",
            actor_id="system",
            actor_role="system",
            patient_pseudonym_id=pid,
            triage_note_id=note.id,
            details_json=json.dumps({
                "source": "seed.py",
                "expected_priority": expected_priority,
                "synthetic_data": True,
            }),
            prev_hash="GENESIS",
            row_hash="seed_hash_" + pid,  # Real hash computed by AuditLogger in production
            created_at=now,
        )
        db.add(audit)

        priority_emoji = {"EMERGENCY": "ðŸ”´", "HIGH": "ðŸŸ¡", "NORMAL": "ðŸŸ¢", "INSUFFICIENT_INFO": "â¬œ"}.get(
            expected_priority, "â¬œ"
        )
        print(f"  {priority_emoji} {pid}: {p.get('chief_complaint', 'N/A')[:50]} [{expected_priority}]")

    db.commit()


def load_ground_truth() -> dict:
    """Load ground_truth.json as a dict keyed by pseudonym_id."""
    if not os.path.exists(GROUND_TRUTH_FILE):
        return {}
    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["pseudonym_id"]: item for item in data}


def main():
    reset = "--reset" in sys.argv

    print("\n[SEED] Healthcare Triage Assistant - Seed Script")
    print("   [!] SYNTHETIC DATA ONLY - No real patient records")
    print("   [!] Educational prototype for triage support only\n")

    if reset:
        print("â™»  Resetting database...")
        Base.metadata.drop_all(bind=engine)

    # Initialize DB (create tables)
    init_db()
    print("âœ“ Database tables created\n")

    db = SessionLocal()
    try:
        # Check if already seeded
        existing_users = db.query(User).count()
        if existing_users > 0 and not reset:
            print(f"âš   Database already has {existing_users} users. Use --reset to re-seed.\n")
            return

        print("ðŸ‘¤ Creating demo users...")
        seed_users(db)

        print("\nðŸ“‹ Loading 25 synthetic patients...")
        ground_truth = load_ground_truth()
        seed_patients(db, ground_truth)

        count = db.query(Patient).count()
        notes_count = db.query(TriageNote).count()
        print(f"\nâœ… Seed complete!")
        print(f"   {db.query(User).count()} demo users")
        print(f"   {count} synthetic patients")
        print(f"   {notes_count} placeholder triage notes")
        print(f"\nðŸ”‘ Demo credentials:")
        print(f"   health_worker_1 / demo123  â†’  Health Worker")
        print(f"   nurse_1         / demo123  â†’  Nurse")
        print(f"   doctor_1        / demo123  â†’  Doctor")
        print(f"   admin_1         / demo123  â†’  Admin")
        print(f"\nðŸŒ Start the app: make dev")
        print(f"   Backend: http://localhost:8000")
        print(f"   API docs: http://localhost:8000/docs")
        print(f"   Frontend: http://localhost:3000")
        print(f"\nâš   Disclaimer: {settings.DISCLAIMER}\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()

