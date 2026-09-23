import json
from pathlib import Path

from app.core.config import ROOT
from app.schemas.fixtures import GroundTruth, PatientDataset

DATA = ROOT / 'data' / 'synthetic'


def load_fixtures(path: Path = DATA) -> tuple[PatientDataset, GroundTruth]:
    patients = PatientDataset.model_validate_json((path / 'patients.json').read_text(encoding='utf-8'))
    truth = GroundTruth.model_validate_json((path / 'ground_truth.json').read_text(encoding='utf-8'))
    ids = [p.pseudonym_id for p in patients.patients]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate synthetic patient IDs')
    if set(ids) != set(truth.cases):
        raise ValueError('Fixture inputs and expectations must have identical patient IDs')
    if patients.reference_time != truth.reference_time:
        raise ValueError('Reference timestamps must match')
    return patients, truth
