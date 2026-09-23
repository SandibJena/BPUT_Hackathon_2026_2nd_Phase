import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AuditLog, utcnow

GENESIS = '0' * 64


def digest(row: AuditLog) -> str:
    payload = {key: getattr(row, key) for key in
               ('timestamp', 'actor_id', 'action', 'subject_id', 'previous_hash')}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def append_event(session: Session, *, actor_id: str, action: str, subject_id: str) -> AuditLog:
    """Caller must hold a serialized write transaction (seed uses BEGIN IMMEDIATE).

    No raw input or mutable metadata is accepted here. This is not an external
    integrity anchor and is not yet a concurrent multi-writer service.
    """
    previous = session.scalar(select(AuditLog).order_by(AuditLog.id.desc()).limit(1))
    row = AuditLog(timestamp=utcnow().isoformat(), actor_id=actor_id, action=action,
                   subject_id=subject_id, previous_hash=previous.entry_hash if previous else GENESIS)
    row.entry_hash = digest(row)
    session.add(row)
    session.flush()
    return row


def verify_integrity(session: Session) -> bool:
    previous = GENESIS
    for row in session.scalars(select(AuditLog).order_by(AuditLog.id)):
        if row.previous_hash != previous or row.entry_hash != digest(row):
            return False
        previous = row.entry_hash
    return True
