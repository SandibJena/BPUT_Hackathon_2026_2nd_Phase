from datetime import datetime
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field

from app.schemas.triage import Facility, Language, Priority, Scenario, StrictModel, Vitals


class SyntheticPatient(StrictModel):
    pseudonym_id: Annotated[str, Field(pattern=r'^DEMO-\d{3}$')]
    synthetic: Literal[True]
    consent: Literal[True]
    age: Annotated[int, Field(ge=0, le=120)] | None = None
    sex: Literal['female', 'male', 'intersex', 'not_reported'] = 'not_reported'
    language: Language
    facility_type: Facility
    scenario: Scenario
    text: Annotated[str, Field(min_length=1, max_length=12000)]
    vitals: Vitals = Field(default_factory=Vitals)


class PatientDataset(StrictModel):
    synthetic: Literal[True]
    reference_time: AwareDatetime
    patients: list[SyntheticPatient]


class ExpectedCase(StrictModel):
    priority: Priority
    fields: dict[str, str | int | float | None]
    missing_info: list[str]


class GroundTruth(StrictModel):
    illustrative_not_clinically_validated: Literal[True]
    reference_time: AwareDatetime
    cases: dict[str, ExpectedCase]
