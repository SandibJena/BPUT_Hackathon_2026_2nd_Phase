"""Deny-by-default outbound projection, stronger than regex-only name masking.

Only enums, bounded measurements and enumerated question keys leave the process.
No raw text, evidence spans, identifiers, filenames, history prose or logs go to
an external model. This intentionally limits extraction breadth until Phase 5.
"""
from app.schemas.intake import TextIntake
from app.services.rules.signals import Scan


def clinical_projection(request: TextIntake, scan: Scan, missing: list[str]) -> dict:
    return {
        'age': request.patient.age,
        'language': request.patient.language,
        'symptoms': [{'name': s.name, 'assertion': s.assertion, 'evidence': s.name} for s in scan.symptoms],
        'vitals': scan.vitals.model_dump(),
        'pregnancy_status': scan.pregnancy_status,
        'missing_fields': missing,
    }
