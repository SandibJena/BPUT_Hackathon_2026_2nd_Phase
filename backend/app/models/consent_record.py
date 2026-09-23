from sqlalchemy import Column, String, Boolean, DateTime
from app.models.base import BaseModel
from datetime import datetime, timezone

class ConsentRecord(BaseModel):
    __tablename__ = "consent_records"
    pseudonym_id = Column(String, nullable=False)
    purpose = Column(String, nullable=False)
    language = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ip_hash = Column(String, nullable=True)
    consent_given = Column(Boolean, nullable=False)
