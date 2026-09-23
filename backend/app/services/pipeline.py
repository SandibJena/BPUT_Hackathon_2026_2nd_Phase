from datetime import datetime, timezone

from app.schemas.intake import TextIntake
from app.schemas.triage import FieldSource, History, Priority, Provenance, Review, Risk, RiskChange, TimelineEvent, TriageNote
from app.services.followups import missing_fields, render_missing, render_questions
from app.services.llm.provider import PROMPT_VERSION, Provider, extract_validated
from app.services.privacy.projection import clinical_projection
from app.services.rules.engine import evaluate_rules, load_rules
from app.services.rules.signals import ALIASES, TIME, Scan, phrase_matches, scan_text
import re


def timeline(text: str) -> list[TimelineEvent]:
    events = []
    for clause in re.split(r'[.!?;।\n]', text):
        markers = [m.group(0) for m in TIME.finditer(clause)]
        if not markers:
            continue
        names = [name.replace('_', ' ') for name, aliases in ALIASES.items()
                 if any(list(phrase_matches(alias, clause)) for alias in aliases)]
        for marker in markers:
            events.append(TimelineEvent(time=marker, event='Narrative mentions: ' + ', '.join(names)
                          if names else 'Time marker reported; event needs clarification', source='text'))
    return events[:30]


def run_pipeline(request: TextIntake, provider: Provider) -> TriageNote:
    if not request.consent or not request.synthetic:
        raise PermissionError('Consent and synthetic-data confirmation are required')
    now = datetime.now(timezone.utc)
    scan = scan_text(request.text, request.vitals)
    fields = missing_fields(request, scan)
    ruleset = load_rules()
    result = evaluate_rules(request.patient, scan, missing=bool(fields), ruleset=ruleset)
    category, source = result.category, 'rules'
    reasons = list(result.reasons)
    changes = [RiskChange(timestamp=now, category=category, source='rules', reason='; '.join(reasons)[:4000])]
    questions = []
    flags = list(scan.flags)
    try:
        output = extract_validated(provider, clinical_projection(request, scan, fields))
        # Model omissions/negative assertions never remove the independent raw-text signals.
        questions = output.question_keys
        if output.suggested_priority and output.suggested_priority.rank < category.rank:
            previous = category
            category, source = output.suggested_priority, 'llm_escalation'
            reasons.append('Possible urgency signal detected; model requested additional professional review')
            changes.append(RiskChange(timestamp=now, previous=previous, category=category,
                                      source='llm_escalation', reason=reasons[-1]))
        elif output.suggested_priority and output.suggested_priority.rank > category.rank:
            reasons.append('Lower-priority model suggestion ignored')
    except Exception:
        # Do not log SDK errors or responses: they can contain submitted identifiers.
        flags.append('extraction_failed')
    if flags:
        previous = category
        category = min([category, Priority.HIGH], key=lambda p: p.rank)
        if previous.rank > Priority.HIGH.rank:
            source = 'failsafe'
        reasons.append('manual review needed')
        reasons.extend('Verification flag: ' + flag for flag in sorted(set(flags)))
        changes.append(RiskChange(timestamp=now, previous=previous, category=category,
                                  source='failsafe', reason='manual review needed'))
    reported = list(dict.fromkeys(s.name.replace('_', ' ') for s in scan.symptoms if s.assertion == 'reported'))
    chief = ('Reported symptoms: ' + ', '.join(reported)) if reported else 'Main concern requires professional confirmation'
    provenance = [FieldSource(field_path=f'symptoms.{i}', source='text', evidence=s.evidence or s.name)
                  for i, s in enumerate(scan.symptoms)]
    for field, value in scan.vitals.model_dump().items():
        if value is not None and not field.endswith('_unit'):
            provenance.append(FieldSource(field_path=f'vitals.{field}', source='text',
                evidence=f'Structured or explicitly unit-labelled narrative measurement: {value}; verify against intake'))
    return TriageNote(patient=request.patient, chief_complaint=chief, symptoms=scan.symptoms,
        timeline=timeline(request.text), vitals=scan.vitals,
        history=History(pregnancy_status=scan.pregnancy_status), missing_info=render_missing(fields),
        follow_up_questions=render_questions(fields, questions),
        risk=Risk(category=category, reasons=reasons, triggered_rules=result.rule_ids, source=source, history=changes),
        review=Review(status='escalated' if category in (Priority.EMERGENCY, Priority.HIGH) else 'needs_review'),
        provenance=Provenance(summary='Independent local signal scan and illustrative rules; constrained extraction; human review required. Free-text identifiers are excluded from model input.',
            input_sources=['text'], rules_version=ruleset['version'], model=provider.name,
            prompt_version=PROMPT_VERSION, generated_at=now, reference_time=request.reference_time,
            field_sources=provenance))


def preserve_previous_priority(note: TriageNote, previous: TriageNote | None) -> TriageNote:
    """New information cannot silently undo an earlier escalation or reuse sign-off."""
    if previous is None:
        return note
    payload = note.model_dump(mode='json')
    payload['version'] = previous.version + 1
    payload['risk']['history'] = [*previous.model_dump(mode='json')['risk']['history'], *payload['risk']['history']]
    if previous.risk.category.rank < note.risk.category.rank:
        payload['risk']['category'] = previous.risk.category.value
        payload['risk']['source'] = previous.risk.source
        payload['risk']['reasons'] = list(dict.fromkeys(previous.risk.reasons + note.risk.reasons + ['Prior urgency retained pending professional review']))
        payload['risk']['triggered_rules'] = list(dict.fromkeys(previous.risk.triggered_rules + note.risk.triggered_rules))
        payload['review']['status'] = 'escalated'
        payload['risk']['history'].append(RiskChange(timestamp=datetime.now(timezone.utc), previous=note.risk.category,
            category=previous.risk.category, source=previous.risk.source, reason='Prior urgency retained pending professional review').model_dump(mode='json'))
    return TriageNote.model_validate(payload)
