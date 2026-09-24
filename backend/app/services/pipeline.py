"""
pipeline.py — Triage pipeline orchestrator.

Flow:
  1. Mask PII (privacy/masking.py)
  2. Rules engine (rules/engine.py) — deterministic, always runs
  3. LLM extraction (llm/claude.py) — optional, may be skipped if no API key
  4. Risk merge — LLM can ONLY RAISE priority, never lower it
  5. Build and return TriageNote

SAFETY RULES (hardcoded, never skip):
- Rules engine ALWAYS runs. LLM is additive only.
- LLM failure → HIGH (fail-safe). LLM suggesting lower priority → ignored.
- Masking is always applied before LLM call.
- Every note carries the disclaimer.
- Audit-ready provenance is always recorded.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.schemas.triage import (
    FollowUpQuestion,
    History,
    MissingInfo,
    PatientInfo,
    ProvenanceRecord,
    ReviewRecord,
    RiskAssessment,
    Symptom,
    TextIntakeRequest,
    TriageNote,
    Vitals,
)
from app.services.llm.claude import extract_with_claude
from app.services.privacy.masking import mask_pii, masking_report
from app.services.rules.engine import PRIORITY_ORDER, RuleResult, evaluate_rules

log = logging.getLogger(__name__)

# Priority fail-safe when LLM errors
LLM_FAILURE_CATEGORY = 'HIGH'


def _merge_priority(rules_category: str, llm_category: str | None) -> str:
    """
    SAFETY: LLM may only RAISE urgency, never lower it.
    If llm_category is None (failure), apply fail-safe → HIGH.
    Final = max(rules, llm_fail_safe if llm_failed else llm_category)
    """
    if llm_category is None:
        # LLM failed → apply fail-safe HIGH, but still respect rules if already higher
        return rules_category if PRIORITY_ORDER[rules_category] >= PRIORITY_ORDER[LLM_FAILURE_CATEGORY] else LLM_FAILURE_CATEGORY

    # LLM returned a category — take the maximum (more severe) of the two
    return (
        rules_category
        if PRIORITY_ORDER[rules_category] >= PRIORITY_ORDER[llm_category]
        else llm_category
    )


def _build_provenance(
    inputs_used: list[str],
    rules_result: RuleResult,
    llm_result: dict | None,
    masking_applied: bool,
    llm_failed: bool,
    model: str,
) -> ProvenanceRecord:
    steps = []
    steps.append('PII masking applied' if masking_applied else 'PII masking attempted (no patterns found)')
    steps.append(f'Rules engine evaluated: {len(rules_result.triggered_rules)} rules triggered')
    if rules_result.scan_flags:
        steps.append(f'Scan flags: {", ".join(rules_result.scan_flags)}')
    if llm_result:
        steps.append('LLM extraction succeeded')
    elif llm_failed:
        steps.append(f'LLM extraction failed — fail-safe applied: category raised to {LLM_FAILURE_CATEGORY}')
    else:
        steps.append('LLM extraction skipped (no API key configured)')

    return ProvenanceRecord(
        inputs_used=inputs_used,
        rules_evaluated=[r for r in ['RULE-001', 'RULE-002', 'RULE-003', 'RULE-004', 'RULE-005',
                                      'RULE-006', 'RULE-007', 'RULE-008', 'RULE-009', 'RULE-010',
                                      'RULE-011', 'RULE-012', 'RULE-013', 'RULE-014', 'RULE-015']],
        llm_model=model if llm_result else None,
        prompt_version='v1.0',
        masking_applied=masking_applied,
        steps=steps,
    )


def run_text_pipeline(req: TextIntakeRequest, note_id: str | None = None) -> TriageNote:
    """
    Full triage pipeline for a text intake request.

    Returns a complete TriageNote with:
    - Symptoms extracted (via rules engine NLP scan)
    - Risk assessment (rules + optional LLM, merged conservatively)
    - Follow-up questions
    - Missing info flags
    - Provenance record
    - Disclaimer on every note
    """
    now = datetime.now(timezone.utc)
    note_id = note_id or str(uuid.uuid4())
    api_key = settings.ANTHROPIC_API_KEY
    llm_model = 'claude-3-5-haiku-20241022'

    # ── 1. Consent check ─────────────────────────────────────────────────────
    if not req.consent_given:
        raise ValueError('Consent is required before processing any patient information.')

    # ── 2. PII masking ───────────────────────────────────────────────────────
    masked_text = mask_pii(req.symptoms_text)
    mask_info = masking_report(req.symptoms_text, masked_text)
    masking_applied = mask_info['masking_applied']

    # ── 3. Rules engine (deterministic, always runs) ─────────────────────────
    vitals = req.vitals or Vitals()
    history = req.history or History()

    rules_result = evaluate_rules(
        text=req.symptoms_text,  # Use original for local scanning (not sent externally)
        vitals=vitals,
        history=history,
        age_band=req.age_band,
        scenario=req.scenario,
    )

    # Extract symptoms from rules scan for the note
    from app.services.rules.signals import scan_text
    scan = scan_text(req.symptoms_text, vitals)
    extracted_symptoms: list[Symptom] = [
        s for s in scan.symptoms if s.assertion == 'reported'
    ]

    # ── 4. LLM extraction (optional, never diagnostic) ───────────────────────
    llm_result: dict | None = None
    llm_failed = False

    if api_key:
        llm_result = extract_with_claude(
            masked_text=masked_text,
            age_band=req.age_band,
            sex=req.sex,
            language=req.language,
            facility_type=req.facility_type,
            scenario=req.scenario,
            api_key=api_key,
            model=llm_model,
        )
        if llm_result is None:
            llm_failed = True
            log.warning(f'LLM extraction failed for note {note_id} — applying fail-safe HIGH')
    else:
        log.info('LLM extraction skipped — ANTHROPIC_API_KEY not configured')

    # ── 5. Risk merge (LLM can only raise, never lower) ──────────────────────
    llm_suggested_category = llm_result.get('suggested_category') if llm_result else None
    final_category = _merge_priority(rules_result.category, llm_suggested_category if not llm_failed else None)

    # Build risk reasons (rules + LLM signals merged)
    risk_reasons = list(rules_result.reasons)
    if llm_result and llm_result.get('possible_urgency_signals'):
        llm_signals = llm_result['possible_urgency_signals']
        # Add LLM signals not already covered by rules
        for sig in llm_signals:
            if sig not in risk_reasons:
                risk_reasons.append(f'[LLM signal] {sig}')
    if llm_failed:
        risk_reasons.append(
            f'LLM extraction failed — category raised to {LLM_FAILURE_CATEGORY} per fail-safe policy.'
        )

    risk_history = [{'category': rules_result.category, 'source': 'rules_engine'}]
    if llm_suggested_category and not llm_failed:
        risk_history.append({'category': llm_suggested_category, 'source': 'llm'})
    if llm_failed:
        risk_history.append({'category': LLM_FAILURE_CATEGORY, 'source': 'fail_safe'})

    risk = RiskAssessment(
        category=final_category,
        reasons=risk_reasons,
        triggered_rules=rules_result.triggered_rules,
        source='rules_engine' if not llm_result else 'rules_engine+llm',
        history=risk_history,
    )

    # ── 6. Follow-up questions ────────────────────────────────────────────────
    follow_ups: list[FollowUpQuestion] = []
    if llm_result and llm_result.get('follow_up_questions'):
        for q in llm_result['follow_up_questions'][:5]:  # cap at 5
            follow_ups.append(FollowUpQuestion(
                question=q.get('question', ''),
                target_role=q.get('target_role', 'health_worker'),
                translated_text=q.get('hindi') or q.get('odia'),
                language='hi' if q.get('hindi') else ('or' if q.get('odia') else None),
            ))
    else:
        # Fallback follow-ups when LLM unavailable
        follow_ups = _default_follow_ups(rules_result, req)

    # ── 7. Missing info ───────────────────────────────────────────────────────
    missing: list[MissingInfo] = []
    if llm_result and llm_result.get('missing_info'):
        for m in llm_result['missing_info'][:6]:
            missing.append(MissingInfo(
                field=m.get('field', ''),
                why_it_matters=m.get('why_it_matters', ''),
            ))
    else:
        missing = _default_missing_info(req, vitals)

    # ── 8. LLM-extracted symptoms (supplement rules scan) ────────────────────
    if llm_result and llm_result.get('symptoms'):
        for s in llm_result['symptoms'][:10]:
            name = s.get('name', '')
            if name and not any(ex.name == name for ex in extracted_symptoms):
                extracted_symptoms.append(Symptom(
                    name=name,
                    duration=s.get('duration'),
                    severity=s.get('severity'),
                    notes=s.get('notes'),
                    source='llm',
                    assertion='reported',
                ))

    # ── 9. Chief complaint ───────────────────────────────────────────────────
    chief_complaint = req.chief_complaint
    if llm_result and llm_result.get('chief_complaint'):
        chief_complaint = llm_result['chief_complaint']

    # ── 10. Provenance ────────────────────────────────────────────────────────
    provenance = _build_provenance(
        inputs_used=['text'],
        rules_result=rules_result,
        llm_result=llm_result,
        masking_applied=masking_applied,
        llm_failed=llm_failed,
        model=llm_model,
    )

    # ── 11. Build final TriageNote ────────────────────────────────────────────
    patient = PatientInfo(
        pseudonym_id=req.pseudonym_id,
        age_band=req.age_band,
        sex=req.sex,
        language=req.language,
        facility_type=req.facility_type,
        scenario=req.scenario,
    )

    return TriageNote(
        id=note_id,
        patient=patient,
        chief_complaint=chief_complaint,
        symptoms=extracted_symptoms,
        vitals=vitals,
        history=history,
        missing_info=missing,
        follow_up_questions=follow_ups,
        risk=risk,
        review=ReviewRecord(status='pending'),
        provenance=provenance,
        disclaimer=settings.DISCLAIMER,
        created_at=now,
        updated_at=now,
    )


def _default_follow_ups(rules_result: RuleResult, req: TextIntakeRequest) -> list[FollowUpQuestion]:
    """Fallback follow-up questions when LLM is unavailable."""
    questions = []

    if not req.vitals or req.vitals.spo2 is None:
        questions.append(FollowUpQuestion(
            question='Please measure and record the patient\'s oxygen saturation (SpO2).',
            target_role='health_worker',
        ))
    if not req.vitals or req.vitals.pulse is None:
        questions.append(FollowUpQuestion(
            question='Please record the patient\'s pulse rate.',
            target_role='health_worker',
        ))
    if not req.vitals or req.vitals.bp_sys is None:
        questions.append(FollowUpQuestion(
            question='Please record the patient\'s blood pressure.',
            target_role='nurse',
        ))
    if req.age_band == 'unknown':
        questions.append(FollowUpQuestion(
            question='Please confirm the patient\'s age.',
            target_role='health_worker',
        ))
    if rules_result.category in ('EMERGENCY', 'HIGH'):
        questions.append(FollowUpQuestion(
            question='Immediate professional assessment required. Please escalate to the senior clinician on duty.',
            target_role='nurse',
        ))

    return questions[:5]


def _default_missing_info(req: TextIntakeRequest, vitals: Vitals) -> list[MissingInfo]:
    """Identify missing critical fields without LLM."""
    missing = []
    if vitals.spo2 is None:
        missing.append(MissingInfo(field='spo2', why_it_matters='SpO2 below 92% is a critical emergency signal'))
    if vitals.pulse is None:
        missing.append(MissingInfo(field='pulse', why_it_matters='Heart rate is essential for triage assessment'))
    if vitals.bp_sys is None:
        missing.append(MissingInfo(field='blood_pressure', why_it_matters='Blood pressure helps identify shock risk'))
    if vitals.temp is None:
        missing.append(MissingInfo(field='temperature', why_it_matters='Temperature helps confirm fever severity'))
    if req.age_band == 'unknown':
        missing.append(MissingInfo(field='age', why_it_matters='Age affects risk profile for several conditions'))
    return missing
