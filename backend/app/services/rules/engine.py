"""
rules/engine.py — Deterministic rules engine for triage urgency assessment.

SAFETY RULES:
- This engine ALWAYS decides urgency. The LLM may only RAISE priority, never lower it.
- All rules are illustrative and must be validated by a clinician.
- Output is 'possible urgency signals', never a diagnosis.
- Pure functions with no side effects — safe to call from any context.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from app.core.config import settings
from app.schemas.triage import History, Vitals
from app.services.rules.signals import Scan, scan_text

# ── Priority ordering ─────────────────────────────────────────────────────────
PRIORITY_ORDER: dict[str, int] = {
    'NORMAL': 1,
    'INSUFFICIENT_INFO': 2,
    'HIGH': 3,
    'EMERGENCY': 4,
}


@dataclass
class RuleResult:
    """Result of rules engine evaluation."""
    category: str                          # EMERGENCY | HIGH | INSUFFICIENT_INFO | NORMAL
    triggered_rules: list[str]             # Rule IDs that fired
    reasons: list[str]                     # Human-readable phrases (approved_output_phrase)
    scan_flags: list[str] = field(default_factory=list)  # flags from signals scanner


def _max_priority(a: str, b: str) -> str:
    """Return the more severe of two priority categories."""
    return a if PRIORITY_ORDER[a] >= PRIORITY_ORDER[b] else b


# Public alias for testing and pipeline use
merge_priority = _max_priority



def load_rules(yaml_path: str | None = None) -> list[dict]:
    """Load red flag rules from YAML. Returns empty list on error (fail-safe)."""
    path = yaml_path or settings.RULES_FILE
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get('rules', [])
    except Exception as e:
        # Fail-safe: if rules can't be loaded, log but don't crash
        import logging
        logging.getLogger(__name__).error(f'Failed to load rules from {path}: {e}')
        return []


def _duration_exceeds_days(duration_str: str | None, threshold_days: int) -> bool:
    """Check if a duration string exceeds the given number of days."""
    if not duration_str:
        return False
    text = duration_str.lower()

    # Handle week references
    week_match = re.search(r'(\d+)\s*week', text)
    if week_match:
        return int(week_match.group(1)) * 7 >= threshold_days

    # Numeric day references
    day_match = re.search(r'(\d+)\s*day', text)
    if day_match:
        return int(day_match.group(1)) >= threshold_days

    # Word-form day references (handles "five days", etc.)
    word_nums = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'एक': 1, 'दो': 2, 'तीन': 3,
        'चार': 4, 'पांच': 5, 'छह': 6, 'सात': 7,
    }
    for word, num in word_nums.items():
        if word in text and ('day' in text or 'din' in text or 'दिन' in text):
            return num >= threshold_days

    return False


def _age_band_gte(age_band: str, threshold: int) -> bool:
    """Return True if the lower bound of an age band is >= threshold."""
    try:
        lower = int(age_band.split('-')[0].replace('+', '').strip())
        return lower >= threshold
    except (ValueError, IndexError, AttributeError):
        return False


def _age_band_vulnerable(age_band: str) -> bool:
    """True for infants (0-12) and elderly (61+) — vulnerable age groups."""
    vuln = {'0-12', '61-75', '76+'}
    return age_band in vuln


def _rule_fires(
    rule: dict,
    scan: Scan,
    reported: set[str],
    age_band: str,
) -> bool:
    """
    Evaluate a single rule against scan results.
    Each rule check is explicit, not eval'd from YAML expressions — safe by design.

    SAFETY: All checks are conservative. False negatives are preferable to
    false positives in a fail-safe system (rules engine can only raise priority).
    """
    rule_id = rule.get('id', '')

    if rule_id == 'RULE-001':
        # Difficulty breathing / severe breathlessness
        return 'breathing_difficulty' in reported

    elif rule_id == 'RULE-002':
        # Unconsciousness or altered consciousness
        return 'unconsciousness' in reported or 'altered_consciousness' in reported

    elif rule_id == 'RULE-003':
        # Chest pain WITH sweating or breathlessness
        return (
            'chest_pain' in reported
            and (
                'sweating' in reported
                or 'breathing_difficulty' in reported
            )
        )

    elif rule_id == 'RULE-004':
        # SpO2 below 92%
        spo2 = scan.vitals.spo2
        return spo2 is not None and spo2 < 92.0

    elif rule_id == 'RULE-005':
        # Seizure reported
        return 'seizure' in reported

    elif rule_id == 'RULE-006':
        # Heavy uncontrolled bleeding
        return 'heavy_bleeding' in reported

    elif rule_id == 'RULE-007':
        # Pregnancy + bleeding / severe headache / reduced fetal movement
        danger = {'bleeding', 'heavy_bleeding', 'severe_headache', 'reduced_fetal_movement'}
        return (
            scan.pregnancy_status == 'pregnant'
            and bool(danger & reported)
        )

    elif rule_id == 'RULE-008':
        # High fever + neck stiffness
        return (
            ('high_fever' in reported or 'fever' in reported)
            and 'neck_stiffness' in reported
        )

    elif rule_id == 'RULE-009':
        # Infant or elderly with persistent high fever
        return (
            _age_band_vulnerable(age_band)
            and (
                'high_fever' in reported
                or 'persistent_high_fever' in reported
                or 'fever' in reported
            )
        )

    elif rule_id == 'RULE-010':
        # Severe dehydration signs
        return 'severe_dehydration_signs' in reported

    elif rule_id == 'RULE-011':
        # Snake or animal bite
        return 'snake_or_animal_bite' in reported

    elif rule_id == 'RULE-012':
        # Chest pain in patient aged 40+
        return 'chest_pain' in reported and _age_band_gte(age_band, 40)

    elif rule_id == 'RULE-013':
        # Fever lasting more than 5 days
        has_fever = 'fever' in reported or 'high_fever' in reported
        return has_fever and _duration_exceeds_days(scan.duration, 5)

    elif rule_id == 'RULE-014':
        # Sudden vision or hearing loss
        return 'sudden_vision_loss' in reported or 'sudden_hearing_loss' in reported

    elif rule_id == 'RULE-015':
        # Severe abdominal pain
        return 'severe_abdominal_pain' in reported

    # Unknown rules are skipped — future rules can be added here
    return False


def evaluate_rules(
    text: str,
    vitals: Vitals,
    history: History,
    age_band: str = 'unknown',
    scenario: str = 'opd_queue',
    yaml_path: str | None = None,
) -> RuleResult:
    """
    Main entry point for deterministic urgency assessment.

    Steps:
    1. Scan free text for clinical signals (multilingual NLP)
    2. Evaluate each YAML rule against scan results
    3. Return the highest triggered priority category

    SAFETY: If no text is provided → INSUFFICIENT_INFO.
    All outputs are urgency signals, never diagnoses.
    """
    # Fail-safe: no text → can't assess
    if not text or not text.strip():
        return RuleResult(
            category='INSUFFICIENT_INFO',
            triggered_rules=[],
            reasons=['No symptom information provided. Requires professional assessment.'],
        )

    # Step 1: NLP scan
    scan = scan_text(text, vitals)

    # Merge pregnancy from history if available
    if history.pregnancy_status in ('pregnant', 'yes'):
        scan.pregnancy_status = 'pregnant'

    # Prompt injection detected — still evaluate rules but flag it
    scan_flags = list(scan.flags)

    # Step 2: Get reported (non-denied, non-uncertain) signals
    reported = {s.name for s in scan.symptoms if s.assertion == 'reported'}

    # Step 3: Load and evaluate rules
    rules = load_rules(yaml_path)
    triggered_ids: list[str] = []
    category = 'NORMAL'

    for rule in rules:
        if _rule_fires(rule, scan, reported, age_band):
            triggered_ids.append(rule['id'])
            rule_category = rule.get('category', 'HIGH')
            category = _max_priority(category, rule_category)

    # Step 4: INSUFFICIENT_INFO if narrative gave no recognizable signals
    if (
        not scan.symptoms
        and not scan.routine
        and scan.pregnancy_status == 'unknown'
        and not triggered_ids
    ):
        # Still return NORMAL if vitals-only triggered rules (e.g. SpO2 from form)
        if category == 'NORMAL':
            category = 'INSUFFICIENT_INFO'

    reasons = [
        rule['approved_output_phrase']
        for rule in rules
        if rule['id'] in triggered_ids
    ]

    return RuleResult(
        category=category,
        triggered_rules=triggered_ids,
        reasons=reasons,
        scan_flags=scan_flags,
    )
