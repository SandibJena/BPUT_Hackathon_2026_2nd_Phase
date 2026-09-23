# CLAUDE.md — Master Context for Healthcare Triage Assistant

## Project Purpose
Build a human-in-the-loop, NON-DIAGNOSTIC Multimodal Healthcare Triage Assistant for Indian government
hospitals, PHCs, district hospitals, health camps, company clinics, industrial-estate units and campus health centers.

Turns patient-provided symptoms (text or voice), uploaded lab reports and basic images into a structured
triage note for a qualified reviewer (health worker, nurse, doctor). Organizes information, highlights
possible urgency signals, finds missing info, generates follow-up questions, prepares referral notes.

**The AI is an assistant, not a doctor.** Flow: intake → AI extraction/summary → rules flag urgency
signals → nurse/doctor reviews → professional acts.

---

## HARD RULES (never violate)

1. **Non-diagnostic**: no diagnosis names as conclusions, no medication/dose/treatment advice, anywhere
   (UI, API, LLM output). Identify signals, not diseases.
2. **Approved wording**: "Possible urgency signal detected", "Requires immediate professional review",
   "Rule triggered: [RULE-ID]". Never: "You have X", "Take Y mg of Z".
3. **Deterministic rules engine decides urgency.** The LLM may only RAISE urgency, never lower it.
4. **Fail-safe**: any extraction/OCR/LLM failure defaults to HIGH (AMBER) and routes to human.
5. **Nothing leaves the system without reviewer sign-off.**
6. **Synthetic/public data ONLY.** No real patient data, ever.
7. **Every screen and every exported note carries the disclaimer:**
   > "Educational prototype for triage support only. Not a medical device. Not a substitute for qualified medical advice."
8. **PII is masked before any LLM call.** Consent is required before intake.
9. **Every action is written to an append-only audit log.**

---

## Priority Categories

| Category | Color | Rank | Meaning |
|---|---|---|---|
| EMERGENCY | 🔴 Red | 1 | Immediate attention |
| HIGH | 🟡 Amber | 2 | Review soon |
| INSUFFICIENT_INFO | ⬜ Grey | 3 | More questions needed |
| NORMAL | 🟢 Green | 4 | Regular queue (subject to professional confirmation) |

**Final priority = most severe of (rules result, LLM suggestion).**
Re-run rules whenever new info is added. Priority updates must be shown to reviewer and audit-logged.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), React, Tailwind, mobile-first |
| Backend | FastAPI, SQLAlchemy, SQLite (Postgres-ready), Pydantic v2 |
| LLM | Anthropic SDK (Claude), strict JSON-schema output, behind provider interface |
| Voice | faster-whisper (server-side), Web Speech API (browser fallback) |
| OCR | Tesseract (pytesseract), PaddleOCR optional |
| Translation | LLM + glossary (English, Hindi, Odia) |
| Auth | Mock JWT, role-based (Health Worker / Nurse+Doctor / Admin) |
| Tests | pytest + evaluation harness |

---

## Repo Layout

```
/backend    FastAPI app, services, schemas, models, tests
/frontend   Next.js app, components, lib
/data       Synthetic patients, rules/red_flags.yaml, glossary/
/docs       architecture.md, safety.md, privacy.md, demo_script.md
CLAUDE.md   This file — master context
Makefile    make dev / make test / make eval / make seed
```

---

## LLM System Prompt Constraints (always enforced)
- Forbid diagnosis or treatment recommendations
- Verbatim-grounded extraction only (null for unknown, never guess)
- Always produce missing_info[] list
- Always produce 3–6 follow-up questions for a health worker
- Retry once on invalid JSON, then fail-safe to HIGH

---

## Hackathon: BPUT Hackathon 2026

### Judging Weights
| Criterion | Weight |
|---|---|
| Safety-first triage workflow | 20% |
| Quality of extraction & summarization | 20% |
| Multimodal capability | 15% |
| India-wide facility relevance | 15% |
| Human-review design & escalation | 15% |
| Privacy & responsible AI | 10% |
| Demo quality | 5% |

### Priority Cut Order (if time runs short)
1. Image understanding
2. Regional languages beyond Hindi
3. Referral PDF polish
4. Extra scenarios
**NEVER cut:** Rules engine, human-review flow, consent/audit/purge, disclaimers
