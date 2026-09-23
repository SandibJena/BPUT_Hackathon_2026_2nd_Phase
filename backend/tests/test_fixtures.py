import json

import pytest
from pydantic import ValidationError

from app.evaluate import evaluate_foundation
from app.fixtures import DATA, load_fixtures
from app.schemas.fixtures import SyntheticPatient


def test_foundation_fixture_coverage_not_clinical_accuracy():
    report = evaluate_foundation()
    assert all(report['checks'].values())
    assert set(report['emergency_expected_ids']) == {f'DEMO-{i:03d}' for i in range(2, 7)}
    assert all(value is None for value in report['clinical_metrics'].values())


@pytest.mark.parametrize('field', ['consent', 'synthetic'])
def test_unconsented_or_non_synthetic_fixture_rejected(field):
    dataset, _ = load_fixtures()
    payload = dataset.patients[0].model_dump()
    payload[field] = False
    with pytest.raises(ValidationError):
        SyntheticPatient.model_validate(payload)


def test_duplicate_ids_are_rejected(tmp_path):
    payload = json.loads((DATA / 'patients.json').read_text(encoding='utf-8'))
    payload['patients'].append(payload['patients'][0])
    (tmp_path / 'patients.json').write_text(json.dumps(payload), encoding='utf-8')
    (tmp_path / 'ground_truth.json').write_text((DATA / 'ground_truth.json').read_text(encoding='utf-8'), encoding='utf-8')
    with pytest.raises(ValueError, match='Duplicate'):
        load_fixtures(tmp_path)
