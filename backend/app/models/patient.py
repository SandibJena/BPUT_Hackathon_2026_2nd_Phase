from sqlalchemy import Column, String, ForeignKey, DateTime
from app.models.base import BaseModel

class Patient(BaseModel):
    __tablename__ = "patients"
    pseudonym_id = Column(String, unique=True, index=True, nullable=False)
    age_band = Column(String, nullable=False)
    sex = Column(String, nullable=True)
    language = Column(String, nullable=False)
    facility_type = Column(String, nullable=False)
    scenario = Column(String, nullable=False)
    consent_record_id = Column(String, ForeignKey("consent_records.id"), nullable=False)
    purge_at = Column(DateTime, nullable=True)
