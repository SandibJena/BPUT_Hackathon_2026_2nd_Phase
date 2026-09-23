from sqlalchemy import Column, String, Text, ForeignKey, Integer, Boolean, DateTime
from app.models.base import BaseModel
from app.core.config import settings

class TriageNote(BaseModel):
    __tablename__ = "triage_notes"
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    raw_text_input = Column(Text, nullable=True)
    masked_text_input = Column(Text, nullable=True)
    chief_complaint = Column(String, nullable=True)
    symptoms_json = Column(Text, nullable=False, default="[]")
    timeline_json = Column(Text, nullable=False, default="[]")
    vitals_json = Column(Text, nullable=True)
    history_json = Column(Text, nullable=True)
    missing_info_json = Column(Text, nullable=False, default="[]")
    follow_up_questions_json = Column(Text, nullable=False, default="[]")
    risk_category = Column(String, nullable=False)
    risk_reasons_json = Column(Text, nullable=False, default="[]")
    triggered_rules_json = Column(Text, nullable=False, default="[]")
    risk_source = Column(String, nullable=False)
    review_status = Column(String, nullable=False, default="pending")
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=True)
    reviewer_timestamp = Column(DateTime, nullable=True)
    reviewer_comments_json = Column(Text, nullable=False, default="[]")
    provenance_json = Column(Text, nullable=True)
    disclaimer = Column(String, default=settings.DISCLAIMER)
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
