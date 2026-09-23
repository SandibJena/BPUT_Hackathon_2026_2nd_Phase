from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    role: Mapped[str] = mapped_column(String(32))
    display_name: Mapped[str] = mapped_column(String(120))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Patient(Base):
    __tablename__ = 'patients'
    pseudonym_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    language: Mapped[str] = mapped_column(String(8))
    facility_type: Mapped[str] = mapped_column(String(32))
    scenario: Mapped[str] = mapped_column(String(32))
    created_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    # Phase 1 stores synthetic fixture input only. Encryption precedes any wider use.
    intake: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ConsentRecord(Base):
    __tablename__ = 'consent_records'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey('patients.pseudonym_id', ondelete='CASCADE'), index=True)
    purpose: Mapped[str] = mapped_column(String(300))
    language: Mapped[str] = mapped_column(String(8))
    accepted: Mapped[bool] = mapped_column(Boolean)
    policy_version: Mapped[str] = mapped_column(String(32), default='demo-v1')
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TriageNoteRecord(Base):
    __tablename__ = 'triage_notes'
    __table_args__ = (UniqueConstraint('patient_id', 'version'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey('patients.pseudonym_id', ondelete='CASCADE'), index=True)
    version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    priority: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default='waiting')
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    signed_off: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Upload(Base):
    __tablename__ = 'uploads'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey('patients.pseudonym_id', ondelete='CASCADE'), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    storage_key: Mapped[str] = mapped_column(String(200), unique=True)
    content_type: Mapped[str] = mapped_column(String(80))
    sha256: Mapped[str] = mapped_column(String(64))
    encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditLog(Base):
    __tablename__ = 'audit_log'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # No patient FK: a minimal pseudonymous audit event survives future deletion.
    timestamp: Mapped[str] = mapped_column(String(40))
    actor_id: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(80))
    subject_id: Mapped[str] = mapped_column(String(64))
    previous_hash: Mapped[str] = mapped_column(String(64))
    entry_hash: Mapped[str] = mapped_column(String(64), unique=True)
