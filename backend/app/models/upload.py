from sqlalchemy import Column, String, ForeignKey, Boolean, Float, Text, DateTime
from app.models.base import BaseModel

class Upload(BaseModel):
    __tablename__ = "uploads"
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    triage_note_id = Column(String, ForeignKey("triage_notes.id"), nullable=True)
    file_type = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    encrypted = Column(Boolean, default=True)
    ocr_confidence = Column(Float, nullable=True)
    extracted_data_json = Column(Text, nullable=True)
    purge_at = Column(DateTime, nullable=True)
