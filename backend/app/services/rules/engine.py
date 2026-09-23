"""Validated declarative rules. No Python expression evaluation."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.core.config import ROOT
from app.schemas.triage import PatientInfo, Priority
from app.services.rules.signals import Scan

RULE_PATH = ROOT / 'data' / 'rules' / 'red_flags.yaml'
ALLOWED_FIELDS = {'patient.age', 'patient.age_band', 'history.pregnancy_status', 'vitals.spo2'}


def validate_condition(condition: dict, depth: int = 0) -> None:
    if not isinstance(condition, dict) or depth > 8:
        raise ValueError('Invalid rule condition')
    if 'any' in condition or 'all' in condition:
        if len(condition) != 1:
            raise ValueError('Ambiguous rule combination')
        children = condition.get('any', condition.get('all'))
        if not isinstance(children, list) or not children:
            raise ValueError('Empty rule combination')
        for child in children:
            validate_condition(child, depth + 1)
        return
    from app.services.rules.signals import ALIASES
    fields = ALLOWED_FIELDS | {f'symptoms.{key}' for key in ALIASES}
    if set(condition) - {'field', 'op', 'value', 'unit'} or not {'field', 'op', 'value'} <= set(condition):
        raise ValueError('Unknown rule keys')
    if condition['field'] not in fields or condition['op'] not in ('eq', 'lt', 'gte', 'in'):
        raise ValueError('Unknown rule field or operator')
    if condition['op'] == 'in' and not isinstance(condition['value'], list):
        raise ValueError('Membership rule requires list')
    if condition['op'] in ('lt', 'gte') and (type(condition['value']) not in (int, float)):
        raise ValueError('Numeric rule requires number')
    if 'unit' in condition and (condition['field'] != 'vitals.spo2' or condition['unit'] != '%'):
        raise ValueError('Unsupported rule unit')


def load_rules(path: Path = RULE_PATH) -> dict:
    ruleset = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(ruleset, dict) or not ruleset.get('version') or ruleset.get('executable') is not True:
        raise ValueError('Ruleset is not enabled')
    seen = set()
    for rule in ruleset['rules']:
        if set(rule) != {'id', 'description', 'condition', 'category', 'rationale'} or rule['id'] in seen:
            raise ValueError('Invalid or duplicate rule')
        seen.add(rule['id'])
        Priority(rule['category'])
        validate_condition(rule['condition'])
    if not seen:
        raise ValueError('Empty ruleset')
    return ruleset


def matches(condition: dict, facts: dict[str, Any]) -> bool:
    if 'any' in condition:
        return any(matches(child, facts) for child in condition['any'])
    if 'all' in condition:
        return all(matches(child, facts) for child in condition['all'])
    value = facts.get(condition['field'])
    if value is None:
        return False
    expected, op = condition['value'], condition['op']
    if op == 'eq':
        return expected in value if isinstance(value, set) else value == expected
    if op == 'in':
        return value in expected
    if type(value) not in (int, float):
        return False
    return value < expected if op == 'lt' else value >= expected


@dataclass(frozen=True)
class RuleResult:
    category: Priority
    rule_ids: list[str]
    reasons: list[str]
    facts: dict[str, Any]


def evaluate_rules(patient: PatientInfo, scan: Scan, *, missing: bool, ruleset: dict) -> RuleResult:
    age = patient.age
    band = patient.age_band
    if age is not None:
        band = 'infant' if age < 1 else 'child' if age < 13 else 'adolescent' if age < 18 else 'adult' if age < 65 else 'older_adult'
    facts: dict[str, Any] = {'patient.age': age, 'patient.age_band': band,
        'history.pregnancy_status': scan.pregnancy_status, 'vitals.spo2': scan.vitals.spo2}
    for symptom in scan.symptoms:
        facts.setdefault(f'symptoms.{symptom.name}', set()).add(symptom.assertion)
    triggered = [r for r in ruleset['rules'] if matches(r['condition'], facts)]
    category = Priority.INSUFFICIENT_INFO if missing else Priority.NORMAL
    if triggered:
        category = min([category] + [Priority(r['category']) for r in triggered], key=lambda p: p.rank)
    reasons = [f"Rule triggered: {r['id']} — {r['description']}. {r['rationale']}" for r in triggered]
    if not reasons:
        reasons = ['More information needed; subject to professional confirmation' if missing else
                   'No configured urgency rule triggered; subject to professional confirmation']
    return RuleResult(category, [r['id'] for r in triggered], reasons, facts)
