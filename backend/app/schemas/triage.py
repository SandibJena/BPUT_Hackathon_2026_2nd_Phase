from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.core.config import DISCLAIMER

Text = Annotated[str, Field(min_length=1, max_length=4000)]
Source = Literal['text', 'voice', 'report', 'image']
Language = Literal['en', 'hi', 'or']
Scenario = Literal['opd_queue', 'campus_fever', 'industrial_screening', 'maternal_followup', 'chronic_checkin', 'health_camp', 'referral']
Facility = Literal['OPD', 'PHC', 'CHC', 'district', 'camp', 'company_clinic', 'industrial_unit', 'campus']


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)


class Priority(str, Enum):
    EMERGENCY = 'EMERGENCY'
    HIGH = 'HIGH'
    INSUFFICIENT_INFO = 'INSUFFICIENT_INFO'
    NORMAL = 'NORMAL'

    @property
    def rank(self) -> int:
        return {'EMERGENCY': 1, 'HIGH': 2, 'INSUFFICIENT_INFO': 3, 'NORMAL': 4}[self.value]


class PatientInfo(StrictModel):
    pseudonym_id: Annotated[str, Field(pattern=r'^[A-Z][A-Z0-9-]{2,39}$')]
    # Preserve supplied age for threshold rules; never infer it from an age band.
    age: Annotated[int, Field(ge=0, le=120)] | None = None
    age_band: Literal['infant', 'child', 'adolescent', 'adult', 'older_adult'] | None = None
    sex: Literal['female', 'male', 'intersex', 'not_reported'] = 'not_reported'
    language: Language
    facility_type: Facility
    scenario: Scenario


class Symptom(StrictModel):
    name: Text
    onset: Text | None = None
    duration: Text | None = None
    severity: Text | None = None
    notes: Text | None = None
    source: Source
    assertion: Literal['reported', 'denied', 'uncertain'] = 'reported'
    evidence: Text | None = None


class TimelineEvent(StrictModel):
    time: Text
    event: Text
    source: Source
    # Keep narrative time when an exact date cannot be grounded.
    resolved_at: AwareDatetime | None = None


class Vitals(StrictModel):
    temp: Annotated[float, Field(ge=0, le=60, allow_inf_nan=False)] | None = None
    pulse: Annotated[float, Field(ge=0, le=400, allow_inf_nan=False)] | None = None
    bp_sys: Annotated[float, Field(ge=0, le=400, allow_inf_nan=False)] | None = None
    bp_dia: Annotated[float, Field(ge=0, le=300, allow_inf_nan=False)] | None = None
    spo2: Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)] | None = None
    resp_rate: Annotated[float, Field(ge=0, le=150, allow_inf_nan=False)] | None = None
    weight: Annotated[float, Field(gt=0, le=700, allow_inf_nan=False)] | None = None
    temp_unit: Literal['C'] = 'C'
    pulse_unit: Literal['beats/min'] = 'beats/min'
    bp_unit: Literal['mmHg'] = 'mmHg'
    spo2_unit: Literal['%'] = '%'
    resp_rate_unit: Literal['breaths/min'] = 'breaths/min'
    weight_unit: Literal['kg'] = 'kg'


class History(StrictModel):
    # Empty arrays mean no information extracted, NOT a confirmed negative history.
    chronic_conditions: list[Text] = Field(default_factory=list)
    meds_mentioned: list[Text] = Field(default_factory=list)
    allergies: list[Text] = Field(default_factory=list)
    pregnancy_status: Literal['pregnant', 'not_pregnant', 'unknown', 'not_applicable'] = 'unknown'


class ReportValue(StrictModel):
    test: Text
    value: str | float | None
    unit: Text | None = None
    reference_range: Text | None = None
    flag: Literal['above_reference_range', 'below_reference_range', 'within_reference_range', 'manual_verification_needed'] | None = None


class Report(StrictModel):
    source_file: Text
    report_date: Text | None = None
    extracted_values: list[ReportValue] = Field(default_factory=list)
    ocr_confidence: Annotated[float, Field(ge=0, le=1)] | None = None


class ImageObservation(StrictModel):
    description: Text
    source_file: Text
    needs_in_person_review: Literal[True] = True


class MissingInfo(StrictModel):
    field: Text
    why_it_matters: Text


class FollowUp(StrictModel):
    question: Text
    target_role: Literal['health_worker', 'nurse', 'doctor']
    translated_text: Text | None = None


class RiskChange(StrictModel):
    timestamp: AwareDatetime
    previous: Priority | None = None
    category: Priority
    source: Literal['rules', 'llm_escalation', 'failsafe', 'reviewer', 'scheduler']
    reason: Text


class Risk(StrictModel):
    category: Priority
    reasons: Annotated[list[Text], Field(min_length=1)]
    triggered_rules: list[Text] = Field(default_factory=list)
    source: Literal['rules', 'llm_escalation', 'failsafe', 'reviewer', 'scheduler']
    history: list[RiskChange] = Field(default_factory=list)


class ReviewComment(StrictModel):
    reviewer_id: Text
    timestamp: AwareDatetime
    text: Text


class Review(StrictModel):
    status: Literal['waiting', 'needs_review', 'escalated', 'reviewed', 'closed'] = 'waiting'
    reviewer_id: Text | None = None
    timestamp: AwareDatetime | None = None
    comments: list[ReviewComment] = Field(default_factory=list)
    signoff: bool = False
    approved_version: Annotated[int, Field(ge=1)] | None = None

    @model_validator(mode='after')
    def validate_signoff(self):
        if self.signoff and (not self.reviewer_id or not self.timestamp or not self.approved_version
                            or self.status not in ('reviewed', 'closed')):
            raise ValueError('Sign-off requires reviewer, timestamp, approved version and reviewed/closed status')
        if self.status == 'closed' and not self.signoff:
            raise ValueError('A case cannot close without professional sign-off')
        return self


class FieldSource(StrictModel):
    field_path: Text
    source: Source
    evidence: Text
    source_file: Text | None = None


class Provenance(StrictModel):
    summary: Text
    input_sources: list[Source]
    rules_version: Text | None = None
    model: Text | None = None
    prompt_version: Text | None = None
    generated_at: AwareDatetime
    reference_time: AwareDatetime | None = None
    field_sources: list[FieldSource] = Field(default_factory=list)


class TriageNote(StrictModel):
    version: Annotated[int, Field(ge=1)] = 1
    patient: PatientInfo
    chief_complaint: Text | None = None
    symptoms: list[Symptom] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    vitals: Vitals = Field(default_factory=Vitals)
    history: History = Field(default_factory=History)
    reports: list[Report] = Field(default_factory=list)
    image_observations: list[ImageObservation] = Field(default_factory=list)
    missing_info: list[MissingInfo] = Field(default_factory=list)
    follow_up_questions: list[FollowUp] = Field(default_factory=list)
    risk: Risk
    review: Review = Field(default_factory=Review)
    provenance: Provenance
    disclaimer: Literal[DISCLAIMER] = DISCLAIMER

    @model_validator(mode='after')
    def validate_review_version(self):
        if self.review.signoff and self.review.approved_version != self.version:
            raise ValueError('Sign-off must match the current note version')
        return self
