from typing import Annotated

from pydantic import AwareDatetime, Field, StrictBool

from app.schemas.triage import PatientInfo, StrictModel, TriageNote, Vitals


class TextIntake(StrictModel):
    consent: StrictBool
    synthetic: StrictBool
    patient: PatientInfo
    text: Annotated[str, Field(max_length=12000)]
    vitals: Vitals = Field(default_factory=Vitals)
    reference_time: AwareDatetime | None = None


class NoteResponse(StrictModel):
    id: int
    note: TriageNote
