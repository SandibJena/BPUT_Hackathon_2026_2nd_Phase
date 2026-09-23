"""Reviewer-only questions; controlled templates, never model-generated advice."""
import re

from app.schemas.intake import TextIntake
from app.schemas.triage import FollowUp, MissingInfo
from app.services.rules.signals import Scan

QUESTIONS = {
    'age': ('Age affects review of reported signals.', 'What is the patient’s age?'),
    'temperature': ('A measured value is not the same as feeling feverish.', 'What is the highest measured temperature, in Celsius, and when was it measured?'),
    'duration': ('Onset and changes help organize the timeline.', 'When did each symptom start, and how has it changed?'),
    'breathing_difficulty': ('Breathing-related signals need explicit clarification.', 'Is there any difficulty breathing now?'),
    'chronic_conditions': ('Reported history provides context for professional review.', 'Are there any existing conditions relevant to this visit?'),
    'medication_history': ('Current medicine history may be missing.', 'Which medicines are currently being taken, if any?'),
    'allergies': ('Allergy history has not been confirmed.', 'Are any allergies known?'),
    'pregnancy_status': ('Pregnancy context may change urgency review.', 'If relevant, is the patient pregnant, and what is the gestational age?'),
    'pain_pattern': ('The timing and pattern of pain need clarification.', 'When did chest pain start, and is it continuous or occasional?'),
    'pain_spread': ('Additional reported features help professional review.', 'Does the pain spread to the arm, back or jaw?'),
    'associated_signals': ('Co-occurring signals may require escalation.', 'Is there sweating or breathlessness with the chest pain?'),
    'heart_history': ('Reported history needs qualified review.', 'Is there any known heart-related medical history?'),
    'main_complaint': ('The narrative is not sufficiently understood.', 'Please clarify the main concern using the patient’s own words.'),
    'confirm_measurements': ('Conflicting values must not be silently resolved.', 'Please verify the measurements, units and time recorded.'),
    'confirm_summary': ('All extracted information requires human confirmation.', 'Does this summary accurately reflect what the patient reported?'),
    'recent_change': ('A new signal may require re-triage.', 'Has anything changed since this information was collected?'),
}


def missing_fields(request: TextIntake, scan: Scan) -> list[str]:
    fields = []
    names = {s.name for s in scan.symptoms if s.assertion != 'denied'}
    if request.patient.age is None:
        fields.append('age')
    if names & {'fever', 'high_fever', 'persistent_high_fever'} and scan.vitals.temp is None:
        fields.append('temperature')
    if names and not scan.duration and not scan.times:
        fields.append('duration')
    breathing = [s for s in scan.symptoms if s.name == 'breathing_difficulty']
    if not breathing or any(s.assertion == 'uncertain' for s in breathing):
        fields.append('breathing_difficulty')
    # Do not infer negative history from absent keywords.
    if not re.search(r'\bno (?:existing |chronic )?conditions\b', request.text, re.I):
        fields.append('chronic_conditions')
    if not re.search(r'\bno[^.!?;।\n]*\bmedicines\b', request.text, re.I):
        fields.append('medication_history')
    if not re.search(r'\bno[^.!?;।\n]*\ballergies\b', request.text, re.I):
        fields.append('allergies')
    if scan.pregnancy_status == 'unknown' and request.patient.sex in ('female', 'not_reported'):
        fields.append('pregnancy_status')
    if 'chest_pain' in names:
        fields.extend(['pain_pattern', 'pain_spread', 'associated_signals', 'heart_history'])
    if 'unrecognized_or_empty_narrative' in scan.flags:
        fields.insert(0, 'main_complaint')
    if any('measurement' in flag for flag in scan.flags):
        fields.insert(0, 'confirm_measurements')
    return list(dict.fromkeys(fields))


def render_missing(fields: list[str]) -> list[MissingInfo]:
    return [MissingInfo(field=key, why_it_matters=QUESTIONS[key][0]) for key in fields]


def render_questions(fields: list[str], extra: list[str] | None = None) -> list[FollowUp]:
    keys = list(dict.fromkeys(fields + (extra or []) + ['confirm_summary', 'recent_change', 'medication_history']))[:6]
    return [FollowUp(question=QUESTIONS[key][1], target_role='health_worker') for key in keys]
