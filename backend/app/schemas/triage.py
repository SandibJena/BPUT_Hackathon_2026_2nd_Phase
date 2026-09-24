from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal, ClassVar
from datetime import datetime

class Symptom(BaseModel):
    name: str
    onset: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[str] = None
    notes: Optional[str] = None
    source: str = 'text'
    # Fields set by signals.py NLP scanner
    assertion: str = 'reported'  # 'reported' | 'denied' | 'uncertain'
    evidence: str = ''           # The exact phrase match that triggered this signal

class TimelineEvent(BaseModel):
    time: str
    event: str
    source: str = 'text'

class Vitals(BaseModel):
    temp: Optional[float] = None
    pulse: Optional[int] = None
    bp_sys: Optional[int] = None
    bp_dia: Optional[int] = None
    spo2: Optional[float] = None
    resp_rate: Optional[int] = None
    weight: Optional[float] = None

class History(BaseModel):
    chronic_conditions: List[str] = []
    meds_mentioned: List[str] = []
    allergies: List[str] = []
    pregnancy_status: Optional[str] = None

class ReportValue(BaseModel):
    test: str
    value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[str] = None
    source: str = 'report'

class ReportExtraction(BaseModel):
    source_file: str
    extracted_values: List[ReportValue] = []
    ocr_confidence: Optional[float] = None
    needs_manual_verification: bool = False

class ImageObservation(BaseModel):
    description: str
    needs_in_person_review: bool = True
    source_file: str

class MissingInfo(BaseModel):
    field: str
    why_it_matters: str

class FollowUpQuestion(BaseModel):
    question: str
    target_role: str
    translated_text: Optional[str] = None
    language: Optional[str] = None

class RiskAssessment(BaseModel):
    category: Literal['EMERGENCY', 'HIGH', 'INSUFFICIENT_INFO', 'NORMAL']
    reasons: List[str] = []
    triggered_rules: List[str] = []
    source: str
    history: List[dict] = []
    
    DISCLAIMER: ClassVar[str] = "Risk category is an urgency signal for professional review only. Not a medical diagnosis."

class ReviewRecord(BaseModel):
    status: Literal['pending', 'approved', 'edited', 'escalated', 'closed'] = 'pending'
    reviewer_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    comments: List[str] = []
    signoff: bool = False

class ProvenanceRecord(BaseModel):
    inputs_used: List[str] = []
    rules_evaluated: List[str] = []
    llm_model: Optional[str] = None
    prompt_version: Optional[str] = None
    masking_applied: bool = True
    steps: List[str] = []

class PatientInfo(BaseModel):
    pseudonym_id: str
    age_band: str
    sex: Optional[str] = None
    language: str = 'en'
    facility_type: Literal['OPD', 'PHC', 'CHC', 'district', 'camp', 'company_clinic', 'industrial_unit', 'campus']
    scenario: str

class TriageNote(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[str] = None
    patient: PatientInfo
    chief_complaint: Optional[str] = None
    symptoms: List[Symptom] = []
    timeline: List[TimelineEvent] = []
    vitals: Vitals = Field(default_factory=Vitals)
    history: History = Field(default_factory=History)
    reports: List[ReportExtraction] = []
    image_observations: List[ImageObservation] = []
    missing_info: List[MissingInfo] = []
    follow_up_questions: List[FollowUpQuestion] = []
    risk: Optional[RiskAssessment] = None
    review: ReviewRecord = Field(default_factory=ReviewRecord)
    provenance: Optional[ProvenanceRecord] = None
    disclaimer: str = "Educational prototype for triage support only. Not a medical device. Not a substitute for qualified medical advice."
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TextIntakeRequest(BaseModel):
    pseudonym_id: str
    age_band: str
    sex: Optional[str] = None
    language: str = 'en'
    facility_type: str = 'OPD'
    scenario: str = 'opd_queue'
    chief_complaint: str
    symptoms_text: str
    vitals: Optional[Vitals] = None
    history: Optional[History] = None
    consent_given: bool
