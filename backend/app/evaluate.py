"""Foundation validation, intentionally not a clinical accuracy evaluator."""
import json

from app.fixtures import load_fixtures
from app.schemas.triage import Priority


def evaluate_foundation() -> dict:
    dataset, truth = load_fixtures()
    cases = dataset.patients
    emergency = [key for key, value in truth.cases.items() if value.priority == Priority.EMERGENCY]
    checks = {
        '25_patients': len(cases) == 25,
        'six_scenarios': len({p.scenario for p in cases}) == 6,
        'three_languages': {p.language for p in cases} == {'en', 'hi', 'or'},
        'five_emergency_expectations': len(emergency) == 5,
        'all_synthetic_and_consented': all(p.synthetic and p.consent for p in cases),
    }
    return {
        'scope': 'Phase 1 fixture validation ONLY',
        'checks': checks,
        'emergency_expected_ids': emergency,
        'clinical_metrics': {
            'priority_accuracy': None, 'emergency_under_triage_rate': None,
            'field_precision': None, 'field_recall': None,
            'missing_info_detection_rate': None, 'ocr_accuracy': None, 'stage_latency': None,
        },
        'clinical_metrics_status': 'NOT MEASURED — pipeline and clinical evaluation are future phases',
    }


def main() -> None:
    report = evaluate_foundation()
    print(json.dumps(report, indent=2))
    if not all(report['checks'].values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
