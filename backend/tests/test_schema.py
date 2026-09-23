import pytest
from pydantic import ValidationError

from app.core.config import DISCLAIMER
from app.schemas.triage import Priority, Review, Symptom, TriageNote, Vitals


def valid_note():
    return {
        'patient': {'pseudonym_id': 'DEMO-001', 'language': 'hi', 'facility_type': 'PHC', 'scenario': 'opd_queue'},
        'risk': {'category': 'INSUFFICIENT_INFO', 'reasons': ['Manual review needed to complete missing information'], 'source': 'rules'},
        'provenance': {'summary': 'Synthetic schema test only; not a processed clinical note',
                       'input_sources': ['text'], 'generated_at': '2026-09-21T10:00:00Z'},
    }


def test_note_roundtrip_and_unknowns():
    note = TriageNote.model_validate(valid_note())
    assert note.disclaimer == DISCLAIMER
    assert note.vitals.temp is None
    assert note.history.pregnancy_status == 'unknown'
    assert not note.review.signoff
    assert TriageNote.model_validate_json(note.model_dump_json()) == note


def test_priority_order_is_explicit():
    assert [p.rank for p in Priority] == [1, 2, 3, 4]


@pytest.mark.parametrize('spo2', [-1, 101, float('nan'), float('inf')])
def test_invalid_spo2_rejected(spo2):
    with pytest.raises(ValidationError):
        Vitals(spo2=spo2)


def test_units_are_fixed_and_extra_fields_rejected():
    with pytest.raises(ValidationError):
        Vitals(temp=98.6, temp_unit='F')
    with pytest.raises(ValidationError):
        TriageNote.model_validate({**valid_note(), 'diagnosis': 'invented conclusion'})


def test_disclaimer_cannot_be_replaced():
    with pytest.raises(ValidationError):
        TriageNote.model_validate({**valid_note(), 'disclaimer': 'Clinical service'})


def test_missing_denied_and_uncertain_are_distinct():
    assert TriageNote.model_validate(valid_note()).symptoms == []
    assert Symptom(name='breathing difficulty', source='text', assertion='denied').assertion == 'denied'
    assert Symptom(name='breathing difficulty', source='text', assertion='uncertain').assertion == 'uncertain'


def test_signoff_requires_reviewer_timestamp_and_version():
    with pytest.raises(ValidationError):
        Review(signoff=True)
    with pytest.raises(ValidationError):
        Review(status='closed')
    review = {'status': 'reviewed', 'reviewer_id': 'demo-doctor', 'timestamp': '2026-09-21T10:00:00Z',
              'signoff': True, 'approved_version': 1}
    assert TriageNote.model_validate({**valid_note(), 'review': review}).review.signoff
    with pytest.raises(ValidationError):
        TriageNote.model_validate({**valid_note(), 'version': 2, 'review': review})


def test_timezone_required():
    payload = valid_note()
    payload['provenance']['generated_at'] = '2026-09-21T10:00:00'
    with pytest.raises(ValidationError):
        TriageNote.model_validate(payload)


def test_schema_can_be_generated():
    schema = TriageNote.model_json_schema()
    assert schema['properties']['disclaimer']['const'] == DISCLAIMER
