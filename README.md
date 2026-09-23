# Saathi — Multimodal Healthcare Triage Assistant

BPUT Hackathon 2026. Human-in-the-loop information organization for Indian government and institutional health facilities.

> Educational prototype for triage support only. This system provides decision-support information only. It does not diagnose, prescribe treatment, or replace a qualified healthcare professional.

## Phase 1 scope

Implemented: Next.js 15/React/Tailwind shell, consent-gated **local-only** intake preview, FastAPI health endpoint, Pydantic v2 note schema, SQLAlchemy tables, append-only hash-chained demo audit log, idempotent synthetic seed, 25 fictional patient fixtures, five generated fake reports (PNG and PDF, one intentionally blurry), three schematic images, tests and a foundation fixture evaluation command.

**Not implemented yet:** clinical processing, risk classification, LLM/STT/OCR calls, real authentication/authorization, reviewer workflow, export, encryption, retention/purge, offline storage and clinical evaluation. No real patient records, public deployment, or clinical use. The intake preview neither stores nor transmits input. Seeded users cannot log in. Phase 1 does not claim the later-phase safety gates are complete.

## Run locally

Requirements: Python 3.11 or 3.12, Node.js 22 LTS, npm, GNU Make. On Windows use WSL2. No API key, model download, OCR engine or GPU is required for Phase 1.

```sh
cp .env.example .env
make setup
make seed
make dev
```

Open http://localhost:3000 and http://127.0.0.1:8000/health. `make dev` also seeds idempotently before starting both apps; Ctrl+C stops both. Ports must be free. If setup changes dependencies, run `make setup` again. Dependency ranges are declared; generated npm lockfiles should be reviewed and committed after the first verified install.

```sh
make test          # backend tests and frontend TypeScript checking
make build         # production frontend build
make eval          # foundation fixture validation ONLY, not triage accuracy
```

Evaluation intentionally states that emergency under-triage and all clinical metrics are **not measured** until the processing pipeline exists. Never use expected fixture labels as runtime predictions. Tests use temporary SQLite databases, not the developer database.

## Configuration and data

`.env` is read by the backend from the repository root. The default database is `backend/triage.db`. `DATABASE_URL` can select a PostgreSQL SQLAlchemy URL, but PostgreSQL migrations and database-enforced audit immutability must be added and tested before using it; Phase 1 is SQLite-only at runtime. Timestamps are UTC. Keep `.env`, database files, uploads, and reports generated from real data out of Git.

`make seed` loads `data/synthetic/patients.json`, inserts explicitly synthetic demo consent records, creates non-login role fixtures, and generates fake assets under `data/synthetic/reports/` and `data/synthetic/images/`. Rerunning seed does not duplicate records. The synthetic consent records are fixture metadata, not a substitute for consent for future intake. Seed intentionally creates **no triage notes**: processing has not happened yet.

Dataset: 25 fictional records across six scenarios, EN/HI/Odia narratives, missing values, denied and uncertain symptoms, and five emergency **test expectations**, all illustrative and unvalidated. DEMO-001 starts with incomplete information for the proposed PHC demo. Ground-truth reference date is fixed for reproducible timelines. Generated images are schematic illustrations, not clinical evidence.

## Layout

- `backend/app/{api,core,models,schemas,services}` — typed API and persistence
- `backend/tests` — schema, persistence, seed and fixture tests
- `frontend/app` — accessible mobile-first shell and phase-gated screens
- `data/synthetic` — fictional inputs and independent expected labels/fields
- `data/rules/red_flags.yaml` — non-executable illustrative rules for Phase 2
- `data/glossary` — initial symptom translations (human validation required)

## Additional engineering requirements

- Unknown is not negative: distinguish reported, denied and uncertain symptoms; use null for unknown numeric values.
- Every vital has an explicit unit. Reference time and timezone are fixed in fixtures; future narrative dates must retain uncertainty.
- Consent starts unchecked. No browser persistence, upload or external request from the foundation intake.
- Priority must remain ordinal (EMERGENCY before HIGH before INSUFFICIENT_INFO before NORMAL); later queue weights must never let a lower category outrank an emergency.
- Failure escalation must preserve an existing EMERGENCY (HIGH is a minimum, never a downgrade).
- Future note edits must invalidate sign-off; exports must bind to an approved note version.
- Audit events contain pseudonymous references, never raw symptoms or identifiable payloads. Hash chaining alone is not tamper-proof against database-owner access; external anchoring and concurrency controls are future requirements.
- Diagnosis names or medications reported by a patient may be retained as attributed history, never generated as conclusions or recommendations. Output controls need to distinguish these cases.

## Roadmap and verification

1. Foundation (this change).
2. Rules + text extraction + monotonic escalation + pipeline tests.
3. Human review, roles, queue, escalation and signed review revisions.
4. Voice, OCR, translation and narrow descriptive image support.
5. Privacy lifecycle, encryption and responsible-AI controls.
6. Scenario modules, referral PDF and accessibility/offline support.
7. Clinical fixture evaluation, adversarial tests and resilience.
8. Demo packaging, deployment, docs and pitch.

The files are authored remotely. Installation, tests and runtime acceptance must be verified; no passing result is asserted by this README. `.gitlab-ci.yml` runs independent backend tests/seed/fixture validation and frontend typecheck/build jobs for merge requests and the default branch. Inspect the actual pipeline result before merging; CI requires an available runner and package-registry access. A passing build does not replace a browser smoke test of `make dev` and consent withdrawal.
