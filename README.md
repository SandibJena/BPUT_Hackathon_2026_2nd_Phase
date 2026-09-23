# Healthcare Triage Assistant — BPUT Hackathon 2026

> **Disclaimer**: Educational prototype for triage support only. Not a medical device. Not a substitute for qualified medical advice.

A human-in-the-loop, NON-DIAGNOSTIC multimodal triage assistant for Indian government hospitals, PHCs, district hospitals, health camps, company clinics, industrial-estate units and campus health centers.

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Tesseract OCR installed (`winget install UB-Mannheim.TesseractOCR` on Windows)
- Anthropic API key (get free at [console.anthropic.com](https://console.anthropic.com))

### 1. Clone & Configure
```bash
# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local

# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Run Everything
```bash
make dev          # Starts backend (port 8000) + frontend (port 3000)
make seed         # Load 25 synthetic patients into the database
make test         # Run backend tests
make eval         # Run evaluation harness (Stage 7+)
```

### 3. Demo Users (mock auth)
| Username | Password | Role |
|---|---|---|
| health_worker_1 | demo123 | Health Worker |
| nurse_1 | demo123 | Nurse |
| doctor_1 | demo123 | Doctor |
| admin_1 | demo123 | Admin |

---

## Architecture

```
Patient Input → [Consent Gate] → [PII Masking] → [Rules Engine] ─┐
                                                                   ↓
                                              [Risk Merge: max(rules, llm)]
                                                                   ↓
[LLM Extraction (Claude)] ─────────────────────────────────────→ [TriageNote]
                                                                   ↓
                                              [Reviewer Dashboard (Human)]
                                                                   ↓
                                              [Sign-off → Export / Referral PDF]
```

**The LLM can only RAISE priority, never lower it. Rules engine always wins.**

---

## Project Structure

```
BPUT_Hackathon_2026/
├── backend/              FastAPI + SQLite backend
│   ├── app/
│   │   ├── api/          Route handlers
│   │   ├── core/         Config, database
│   │   ├── models/       SQLAlchemy models
│   │   ├── schemas/      Pydantic v2 schemas
│   │   └── services/     Rules, LLM, OCR, STT, translation, privacy, audit
│   ├── tests/            pytest test suite
│   └── seed.py           Load synthetic data
├── frontend/             Next.js 15 frontend
│   └── app/              App Router pages
├── data/
│   ├── synthetic/        25 fictional patients, lab reports, images
│   ├── rules/            red_flags.yaml (illustrative rules)
│   └── glossary/         Hindi/Odia medical term glossary
├── docs/                 Architecture, safety, privacy, demo script
├── CLAUDE.md             Master context (hard rules, stack, schema)
├── Makefile              Dev commands
└── docker-compose.yml    One-command deployment
```

---

## Judging Criteria Coverage

| Criterion | Weight | Stages |
|---|---|---|
| Safety-first triage workflow | 20% | 2, 7 |
| Extraction & summarization | 20% | 2, 4, 7 |
| Multimodal capability | 15% | 4 |
| India-wide relevance | 15% | 6 |
| Human review & escalation | 15% | 3 |
| Privacy & responsible AI | 10% | 5 |
| Demo quality | 5% | 8 |

---

## Safety & Compliance

- **Non-diagnostic**: System produces urgency signals, not diagnoses
- **Human-in-the-loop**: Every note requires qualified reviewer sign-off
- **Privacy**: Pseudonymous IDs, PII masking before LLM, configurable TTL purge
- **Audit**: Append-only, hash-chained audit log
- **Consent**: Required before any intake; recorded with timestamp
- **Synthetic data**: No real patient records used anywhere

See [docs/safety.md](docs/safety.md) and [docs/privacy.md](docs/privacy.md) for full details.
