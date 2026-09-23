from sqlalchemy import Column, String, Text, DateTime
from app.core.database import Base
import uuid
from datetime import datetime, timezone

def generate_uuid():
    return str(uuid.uuid4())

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(String, primary_key=True, default=generate_uuid)
    action = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    actor_role = Column(String, nullable=True)
    patient_pseudonym_id = Column(String, nullable=True)
    triage_note_id = Column(String, nullable=True)
    details_json = Column(Text, nullable=False)
    prev_hash = Column(String, nullable=False)
    row_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
