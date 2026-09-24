# Multi-Modal Healthcare Triage Assistant — Stages 1–3 Implementation Summary

> **Regulatory Notice & Medical Disclaimer**: Educational prototype for triage support only. Not a medical device. Not a substitute for qualified medical advice. The system generates urgency signals for human clinician review, never definitive diagnoses or treatment prescriptions.

---

## 📌 Executive Overview

This project implements a human-in-the-loop, non-diagnostic multimodal triage assistant tailored for Indian healthcare delivery environments (PHCs, CHCs, district hospitals, company clinics, campus units, and health camps).

| Stage | Focus Area | Status | Verification |
|---|---|---|---|
| **Stage 1** | Foundation, Data Scaffold & Base Architecture | ✅ **Completed** | Full synthetic suite (25 patients), database models, auth |
| **Stage 2** | Core Text Triage Pipeline (Rules Engine + LLM + Risk Merge) | ✅ **Completed** | 40/40 tests passing (`test_rules.py`) |
| **Stage 3** | Multimodal Voice Intake (faster-whisper) & Staff Review Dashboard | ✅ **Completed** | 61/61 tests passing across backend suite |
| **Stage 4** | Lab Report Upload & OCR Pipeline (Tesseract) | ⏳ *Next Phase* | Pending execution |
| **Stage 5** | Image Understanding & Dermatological/Injury Observation | ⏳ *Upcoming* | Pending execution |
| **Stage 6** | Multilingual & Low-Resource Deployment | ⏳ *Upcoming* | Pending execution |
| **Stage 7** | Evaluation Harness & Adversarial Validation | ⏳ *Upcoming* | Pending execution |
| **Stage 8** | Clinician Sign-off, Referral Export & Polish | ⏳ *Upcoming* | Pending execution |

---

## 🟢 Stage 1: Foundation & Data Scaffold

### Objectives
Establish a zero-leakage, regulatory-compliant foundation with non-diagnostic guardrails, synthetic patient cohorts, deterministic rule sets, and modular architecture.

### Key Deliverables Built
1. **Clinical Red Flags Rule Definition** (`data/rules/red_flags.yaml`):
   - 15 illustrative red-flag rules (RULE-001 through RULE-015) calibrated for urgent presentation (acute chest pain, altered sensorium, critical hypoxia SpO2 < 92%, acute seizure, heavy hemorrhage, pregnancy with bleeding/headache, snake/animal bites, severe pediatric dehydration).
2. **Multilingual Lexicons** (`data/glossary/hindi.yaml`, `data/glossary/odia.yaml`):
   - Anatomical and symptom terminology mapped across English, Hindi (Devanagari & romanized), and Odia scripts.
3. **Synthetic Patient Benchmark** (`data/synthetic/patients.json`, `data/synthetic/ground_truth.json`):
   - 25 fictional test patients spanning 6 healthcare operational scenarios (`opd_queue`, `maternal_health`, `industrial_screening`, `campus_health`, `health_camp`, `emergency`) across 4 urgency tiers:
     - 🔴 **EMERGENCY** (5 cases)
     - 🟡 **HIGH** (5 cases)
     - ⬜ **INSUFFICIENT_INFO** (5 cases)
     - 🟢 **NORMAL** (10 cases)
4. **Database & Data Layer**:
   - SQLAlchemy models with SQLite engine: `Patient`, `ConsentRecord`, `TriageNote`, `Upload`, `AuditLog`, `User`.
   - Append-only audit logger (`app/services/audit/logger.py`) with cryptographic hash chaining (`prev_hash`, `row_hash`).
   - Mock JWT authentication system (`app/api/deps.py`) with 4 distinct roles: `health_worker_1`, `nurse_1`, `doctor_1`, `admin_1`.

---

## 🟡 Stage 2: Core Text Triage Pipeline

### Objectives
Build the deterministic rule matching engine, PII masking, Claude LLM extractor, and risk merger.

### Key Deliverables Built
1. **Multilingual NLP Signal Scanner** (`backend/app/services/rules/signals.py`):
   - Tokenizes and extracts symptoms across English, Hindi, and Odia.
   - **Positional Negation & Uncertainty Resolution**:
     - Accurately differentiates affirmed vs. denied vs. uncertain complaints (e.g., *"no chest pain"* is denied; *"chest pain not stopping"* is affirmed).
   - In-line extraction of narrative vitals (e.g., SpO2 percentages embedded in conversational text).
   - Adversarial prompt injection defense (detects *"ignore all previous instructions"*, *"mark as normal"*, *"prescribe antibiotics"*).
2. **Deterministic Rules Engine** (`backend/app/services/rules/engine.py`):
   - Pure functions evaluating all 15 rules without dynamic execution (`eval`).
   - Inputs with no recognizable medical complaint or blank entries safely default to `INSUFFICIENT_INFO`.
3. **Claude LLM Extraction Service** (`backend/app/services/llm/claude.py`):
   - Non-diagnostic system prompt with strict Pydantic JSON schema formatting.
   - Built-in retry and graceful fail-safe: if the LLM fails or is unavailable, the pipeline defaults to `HIGH` (amber) priority to ensure human clinical evaluation.
4. **Deterministic Priority Merge** (`backend/app/services/pipeline.py`):
   - **Enforced Safety Invariant**: `final_priority = max(rules_priority, llm_priority)`.
   - The LLM can **only elevate** urgency; it cannot overturn or downgrade a deterministic clinical red flag.
5. **API Endpoint** (`POST /api/v1/intake/text`):
   - Verifies explicit patient consent before processing.
   - Runs PII masking → Rules evaluation → LLM extraction → Priority merge → Database persistence → Cryptographic audit logging.
6. **Testing Verification**:
   - 40/40 passing unit and integration tests (`tests/test_rules.py`).

---

## 🔵 Stage 3: Multimodal Voice Intake & Staff Review Dashboard

### Objectives
Enable voice symptom reporting via local speech-to-text (server and client fallback) and provide a professional clinician review and escalation dashboard.

### Key Deliverables Built
1. **Server-Side Speech-to-Text (`backend/app/services/stt/whisper_stt.py`)**:
   - `faster-whisper` integration running CPU `int8` quantization.
   - Lazy singleton model initialization to preserve memory.
   - Support for WAV, MP3, WebM, OGG, and FLAC audio files up to 25 MB with automatic temporary file cleanup.
   - Non-blocking metadata endpoint (`GET /api/v1/intake/voice/status`).
2. **Voice Intake Endpoint (`POST /api/v1/intake/voice`)**:
   - Validates audio format, transcribes spoken speech into text, enriches provenance records, and streams into the core triage pipeline.
3. **Staff Review & Escalation API (`backend/app/api/v1/endpoints/notes.py`)**:
   - `GET /api/v1/notes`: List triage notes sorted by urgency (`EMERGENCY` cases guaranteed top of queue). Supports filters for `review_status`, `risk_category`, and `facility_type`.
   - `GET /api/v1/notes/stats`: Real-time queue counters (total, pending, approved, emergency, high, normal).
   - `GET /api/v1/notes/{id}`: Detailed triage note inspection.
   - `PATCH /api/v1/notes/{id}/review`: **Enforced Clinician Sign-Off Gate**:
     - Non-clinicians (`health_worker`) are restricted from approving.
     - Clinicians (`nurse`, `doctor`, `admin`) must provide a clinical rationale comment.
     - `signoff=True` is strictly required for approval.
   - `GET /api/v1/notes/{id}/export`: Export is locked (`403 Forbidden`) until signed off by a qualified reviewer.
4. **Modern Frontend Web Application (Next.js 15, React 18, Tailwind CSS)**:
   - **Voice Recorder Component** (`frontend/components/VoiceRecorder.tsx`):
     - Uses Web Speech API for low-latency in-browser transcription across English, Hindi, and Odia.
     - MediaRecorder audio stream capture for server-side fallback.
     - Clear local-privacy disclosure banner.
   - **Interactive Priority Badge** (`frontend/components/PriorityBadge.tsx`):
     - Color-coded badges with pulsing visual indicator for emergencies.
   - **Patient Intake Interface** (`frontend/app/intake/page.tsx`):
     - Consent modal gate, language selector, dual Text/Voice tabs, optional vitals form, real-time submission, and structured note presentation.
   - **Clinical Review Dashboard** (`frontend/app/dashboard/page.tsx`):
     - Role-aware interface, top emergency banner, real-time status counters, 30-second auto-refresh, and review/sign-off modal.
5. **Comprehensive Test Suite**:
   - **61/61 passing backend tests** (`test_auth.py`, `test_health.py`, `test_rules.py`, `test_notes.py`).

---

## 🛡️ Core Safety Principles Enforced Throughout

1. **Non-Diagnostic**: The system outputs descriptive *urgency signals* for health worker review, never definitive disease labels or medication prescriptions.
2. **Determinism First**: The rules engine decides base urgency. The LLM can only raise urgency, never lower it.
3. **Fail-Safe Defaults**: Missing info defaults to `INSUFFICIENT_INFO`. Extraction/LLM failures default to `HIGH` priority.
4. **Human-in-the-Loop Sign-Off**: No note or referral can be exported without verified sign-off and clinical commentary from a nurse or doctor.
5. **Zero Data Leakage**: Explicit consent required before intake; PII masked prior to any external LLM invocation.
