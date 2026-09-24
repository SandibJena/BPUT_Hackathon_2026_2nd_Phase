"""
llm/claude.py — Claude API extraction service.

SAFETY RULES (never violate):
1. System prompt forbids any diagnosis names as conclusions.
2. System prompt forbids any medication/dose/treatment advice.
3. LLM may only RAISE urgency, never lower it (enforced by caller).
4. Invalid JSON → fail-safe: return None (caller defaults to HIGH).
5. PII masked before this call (enforced by pipeline.py).
6. All model output is advisory; clinician review is mandatory.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

log = logging.getLogger(__name__)

# ── Approved urgency wording (LLM must use these) ──────────────────────────
APPROVED_LLM_URGENCY_PHRASES = {
    'EMERGENCY': 'Possible urgency signal detected. Requires immediate professional review.',
    'HIGH': 'Possible urgency signal detected. Recommend rapid professional assessment.',
    'INSUFFICIENT_INFO': 'Insufficient information to assess urgency signals. Requires professional assessment.',
    'NORMAL': 'No specific urgency signals detected in the provided description. Requires professional review.',
}

SYSTEM_PROMPT = """You are a clinical information extraction assistant for a human-in-the-loop triage support tool used in Indian government hospitals and public health facilities.

CRITICAL RULES — NEVER VIOLATE:
1. You MUST NOT name, suggest, or imply any medical diagnosis or disease name as a conclusion.
2. You MUST NOT suggest any medication, dose, treatment, or clinical procedure.
3. You MUST NOT provide any medical advice.
4. Output only factual extraction of what the patient reported.
5. Use only these urgency categories: EMERGENCY, HIGH, INSUFFICIENT_INFO, NORMAL.
6. Urgency is a SIGNAL for professional review, not a diagnosis.
7. If information is insufficient, say INSUFFICIENT_INFO. Never guess.
8. Every extracted note must end with: "Requires professional review by a qualified health worker."

Your role: Extract structured information from patient-provided symptom text. Summarize what was reported, identify possible urgency signals, and generate helpful follow-up questions. Never diagnose. Never treat.

OUTPUT FORMAT: Respond with valid JSON only. No explanation text outside the JSON."""

EXTRACTION_SCHEMA = {
    "type": "object",
    "required": ["chief_complaint", "symptoms", "possible_urgency_signals", "missing_info",
                 "follow_up_questions", "suggested_category", "summary_for_reviewer"],
    "properties": {
        "chief_complaint": {"type": "string", "description": "One-sentence summary of the main complaint"},
        "symptoms": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "duration", "severity"],
                "properties": {
                    "name": {"type": "string"},
                    "duration": {"type": "string"},
                    "severity": {"type": "string", "enum": ["mild", "moderate", "severe", "unknown"]},
                    "notes": {"type": "string"}
                }
            }
        },
        "possible_urgency_signals": {
            "type": "array",
            "description": "Factual urgency signals found in the text. Use approved wording.",
            "items": {"type": "string"}
        },
        "missing_info": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["field", "why_it_matters"],
                "properties": {
                    "field": {"type": "string"},
                    "why_it_matters": {"type": "string"}
                }
            }
        },
        "follow_up_questions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["question", "target_role"],
                "properties": {
                    "question": {"type": "string"},
                    "target_role": {"type": "string", "enum": ["health_worker", "nurse", "doctor"]},
                    "hindi": {"type": "string"},
                    "odia": {"type": "string"}
                }
            }
        },
        "suggested_category": {
            "type": "string",
            "enum": ["EMERGENCY", "HIGH", "INSUFFICIENT_INFO", "NORMAL"],
            "description": "Urgency signal category. Can only be RAISED by LLM, not lowered."
        },
        "summary_for_reviewer": {
            "type": "string",
            "description": "2-3 sentence structured summary for the health worker reviewer. MUST NOT contain diagnosis names or treatment advice."
        }
    }
}


def _build_user_prompt(
    masked_text: str,
    age_band: str,
    sex: Optional[str],
    language: str,
    facility_type: str,
    scenario: str,
) -> str:
    sex_str = sex or 'not specified'
    return f"""Patient context:
- Age band: {age_band}
- Sex: {sex_str}
- Preferred language: {language}
- Facility type: {facility_type}
- Scenario: {scenario}

Patient-reported symptoms (PII masked):
{masked_text}

Extract structured information following the JSON schema. Remember:
- Do NOT name any disease or diagnosis as a conclusion
- Do NOT suggest any medication or treatment
- Extract only what the patient reported
- Flag missing critical information
- Generate follow-up questions a health worker should ask
- If the patient wrote in Hindi or Odia, also provide translated follow-up questions
- Respond with JSON only"""


def extract_with_claude(
    masked_text: str,
    age_band: str = 'unknown',
    sex: Optional[str] = None,
    language: str = 'en',
    facility_type: str = 'OPD',
    scenario: str = 'opd_queue',
    api_key: str = '',
    model: str = 'claude-3-5-haiku-20241022',
    max_retries: int = 1,
) -> Optional[dict]:
    """
    Call Claude to extract structured triage information.

    Returns:
        dict with extraction results on success
        None on failure (caller must default to HIGH — fail-safe rule)

    SAFETY: Returns None (not raises) so caller always gets a clear signal to use fail-safe.
    """
    if not api_key:
        log.warning('ANTHROPIC_API_KEY not set — LLM extraction disabled, using fail-safe')
        return None

    try:
        import anthropic
    except ImportError:
        log.error('anthropic package not installed')
        return None

    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = _build_user_prompt(masked_text, age_band, sex, language, facility_type, scenario)

    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{'role': 'user', 'content': user_prompt}],
            )

            content = response.content[0].text if response.content else ''
            result = _parse_json_response(content)

            if result is None:
                log.warning(f'Claude returned invalid JSON (attempt {attempt + 1})')
                if attempt < max_retries:
                    continue
                return None  # fail-safe

            # Validate the suggested category is a known value
            if result.get('suggested_category') not in PRIORITY_ORDER_VALUES:
                log.warning(f'Claude returned invalid category: {result.get("suggested_category")}')
                result['suggested_category'] = 'HIGH'  # fail-safe: unknown → HIGH

            return result

        except anthropic.RateLimitError as e:
            log.error(f'Claude rate limit: {e}')
            if attempt < max_retries:
                import time; time.sleep(2)
                continue
            return None

        except anthropic.APIError as e:
            log.error(f'Claude API error: {e}')
            if attempt < max_retries:
                continue
            return None

        except Exception as e:
            log.error(f'Unexpected error calling Claude: {e}')
            return None

    return None


PRIORITY_ORDER_VALUES = {'EMERGENCY', 'HIGH', 'INSUFFICIENT_INFO', 'NORMAL'}


def _parse_json_response(content: str) -> Optional[dict]:
    """
    Parse JSON from Claude's response. Handles markdown code blocks.
    Returns None if parsing fails.
    """
    if not content:
        return None

    # Strip markdown code fences if present
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', content.strip(), flags=re.MULTILINE)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract JSON object from the response
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
    return None
