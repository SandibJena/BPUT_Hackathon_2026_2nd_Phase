from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.engine import Engine

from app.core.config import Settings
from app.core.database import build_engine, initialize, session_factory
from app.fixtures import DATA, load_fixtures
from app.models.entities import ConsentRecord, Patient, User
from app.services.audit import append_event
from app.synthetic_assets import generate_assets

ROLES = ('health_worker', 'nurse', 'doctor', 'admin')


def seed(engine: Engine, *, data_dir: Path = DATA, asset_dir: Path | None = None) -> int:
    dataset, _ = load_fixtures(data_dir)
    initialize(engine)
    generate_assets(asset_dir or data_dir)
    count = 0
    with session_factory(engine)() as session:
        # Serialize audit-chain writers in the local SQLite demonstration.
        session.execute(text('BEGIN IMMEDIATE'))
        try:
            for role in ROLES:
                user_id = f'demo-{role}'
                if session.get(User, user_id) is None:
                    session.add(User(id=user_id, role=role, display_name=f'Demo {role}', is_demo=True))
                    session.flush()
                    append_event(session, actor_id='seed', action='synthetic_user_created', subject_id=user_id)
            for record in dataset.patients:
                if session.get(Patient, record.pseudonym_id) is not None:
                    continue
                # Fixture validation requires explicit true consent and synthetic flags.
                patient = Patient(pseudonym_id=record.pseudonym_id, language=record.language,
                                  facility_type=record.facility_type, scenario=record.scenario,
                                  created_by='demo-health_worker', synthetic=True,
                                  intake=record.model_dump(mode='json'))
                session.add(patient)
                session.flush()
                session.add(ConsentRecord(patient_id=record.pseudonym_id, language=record.language,
                    purpose='Synthetic fixture for triage-support demonstration; no real person',
                    accepted=True, synthetic=True))
                session.flush()
                append_event(session, actor_id='seed', action='synthetic_consent_recorded', subject_id=record.pseudonym_id)
                append_event(session, actor_id='seed', action='synthetic_patient_created', subject_id=record.pseudonym_id)
                count += 1
            append_event(session, actor_id='seed', action='synthetic_assets_generated', subject_id='fixture-assets-v1')
            session.commit()
        except Exception:
            session.rollback()
            raise
    return count


def main() -> None:
    engine = build_engine(Settings().resolved_database_url)
    try:
        count = seed(engine)
        print(f'Seed complete: {count} fictional patients added. No triage has been performed.')
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
