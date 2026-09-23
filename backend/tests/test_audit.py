import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.database import session_factory
from app.models.entities import AuditLog
from app.services.audit import GENESIS, append_event, verify_integrity


def test_events_hash_chain_and_database_blocks_mutation(engine):
    with session_factory(engine)() as session:
        session.execute(text('BEGIN IMMEDIATE'))
        first = append_event(session, actor_id='test', action='created', subject_id='DEMO-001')
        second = append_event(session, actor_id='test', action='viewed', subject_id='DEMO-001')
        assert first.previous_hash == GENESIS
        assert second.previous_hash == first.entry_hash
        session.commit()
        assert verify_integrity(session)
    for statement in ("UPDATE audit_log SET action='modified'", 'DELETE FROM audit_log'):
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(text(statement))
    with session_factory(engine)() as session:
        assert verify_integrity(session)


def test_integrity_verifier_detects_forged_insert(engine):
    with session_factory(engine)() as session:
        session.add(AuditLog(timestamp='2026-09-21T10:00:00Z', actor_id='test', action='forged',
                             subject_id='DEMO-001', previous_hash=GENESIS, entry_hash='f' * 64))
        session.commit()
        assert not verify_integrity(session)


def test_foreign_keys_are_enforced(engine):
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO consent_records (patient_id, purpose, language, accepted, policy_version, synthetic, timestamp) VALUES ('MISSING', 'test', 'en', 1, 'v1', 1, '2026-09-21')"))
