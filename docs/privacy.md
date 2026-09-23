# Privacy and Data Governance

## DPDP Act Alignment
Our system is designed in alignment with India's Digital Personal Data Protection (DPDP) Act, ensuring user privacy and data security.

## Consent
- Purpose of data collection is explicitly stated.
- Consent language and timestamp are recorded for every interaction.

## Purpose Limitation
The system is explicitly restricted for triage support demo purposes only.

## Data Minimization
Only clinically relevant information necessary for triage is collected. We strictly avoid collecting unnecessary identifiers.

## Retention
- Defined Time-To-Live (TTL) for all data.
- Automated purge processes ensure data is permanently deleted post-retention.

## Anonymization
- All patients use pseudonymous IDs.
- Personal Identifiable Information (PII) masking is enforced before data processing.

## Data Flow Description
Patient Data -> PII Scrubbing -> Processing -> Triage Note -> Display -> Auto-Purge.

## No Real Patient Data Policy
As a hackathon project, NO real patient data is used. All data processed by this system is entirely synthetic.
