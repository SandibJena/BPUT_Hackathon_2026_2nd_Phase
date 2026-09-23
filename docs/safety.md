# Safety-First Design Principles

## Hard Rules
1. All patient data must be completely fictional/synthetic — no real people.
2. NON-DIAGNOSTIC: no disease names as conclusions, no medication advice.
3. Risk categories: EMERGENCY (red) | HIGH (amber) | INSUFFICIENT_INFO (grey) | NORMAL (green).
4. All urgency signals say 'Possible urgency signal detected' not a diagnosis.

## Rule Descriptions (Red Flag Rules)
- RULE-001: Difficulty breathing / severe breathlessness - EMERGENCY
- RULE-002: Unconsciousness or altered consciousness reported - EMERGENCY
- RULE-003: Chest pain with sweating or breathlessness - EMERGENCY
- RULE-004: SpO2 below 92% - EMERGENCY
- RULE-005: Seizure reported - EMERGENCY
- RULE-006: Heavy uncontrolled bleeding - EMERGENCY
- RULE-007: Pregnancy with bleeding, severe headache, or reduced fetal movement - EMERGENCY
- RULE-008: High fever with neck stiffness - EMERGENCY
- RULE-009: Infant or elderly patient with persistent high fever (>24h) - HIGH
- RULE-010: Severe dehydration signs - EMERGENCY
- RULE-011: Suspected snake bite or animal bite - EMERGENCY
- RULE-012: Chest pain in patient aged 40 or above - HIGH
- RULE-013: Fever lasting more than 5 days - HIGH
- RULE-014: Sudden loss of vision or hearing - HIGH
- RULE-015: Severe abdominal pain - HIGH

## Escalation Logic
If any EMERGENCY rule is triggered, the overall priority is immediately escalated to EMERGENCY.
If no EMERGENCY rule is triggered but a HIGH rule is, the priority is HIGH.
If required fields (symptoms, duration) are missing, it defaults to INSUFFICIENT_INFO.

## Limitations
- This system CANNOT diagnose conditions.
- It CANNOT prescribe medication or treatment plans.
- It is NOT a replacement for a qualified healthcare professional.

## Threat Model
- Risk of false negatives (under-triage): Mitigated by prioritizing recall over precision for red flags.
- Prompt injection: Handled by strict system prompts and output schema validation.

## Non-diagnostic Policy Explanation
The system acts purely as an information structuring and alert-flagging tool. It explicitly uses language like "Possible urgency signal detected" rather than concluding specific diseases.
