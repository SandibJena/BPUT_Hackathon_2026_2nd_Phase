"""
privacy/masking.py — PII masking before any LLM call.

SAFETY: PII must be masked BEFORE text is sent to any external LLM.
This module provides simple pattern-based masking. Masked text is
used ONLY for LLM extraction — original text stays in the local DB.
"""
from __future__ import annotations
import re

# ── PII patterns ──────────────────────────────────────────────────────────────
_PHONE = re.compile(r'\b(?:\+91[-\s]?)?[6-9]\d{9}\b')
_EMAIL = re.compile(r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b')
_AADHAAR = re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b')
_NAME_TAGS = re.compile(r'\b(?:my name is|mera naam|I am|main hoon)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', re.I)
_DOB = re.compile(r'\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b')
_ADDRESS = re.compile(
    r'\b(?:village|vill|gram|mohalla|street|road|nagar|colony|district|dist|block|ward)\b'
    r'.{0,40}',
    re.I,
)


def mask_pii(text: str) -> str:
    """
    Mask known PII patterns before sending to any external service.
    Returns the masked text. Original text is never modified.

    SAFETY: Conservative — unknown patterns are left as-is.
    Reviewers must check original text for any missed PII.
    """
    masked = text
    masked = _PHONE.sub('[PHONE]', masked)
    masked = _EMAIL.sub('[EMAIL]', masked)
    masked = _AADHAAR.sub('[AADHAAR]', masked)
    masked = _NAME_TAGS.sub('[NAME REDACTED]', masked)
    masked = _DOB.sub('[DOB]', masked)
    # Note: Address masking is approximate — reviewers should verify
    masked = _ADDRESS.sub('[ADDRESS]', masked)
    return masked


def masking_report(original: str, masked: str) -> dict:
    """Return a report of what was masked for audit logging."""
    changed = original != masked
    return {
        'masking_applied': changed,
        'warning': (
            'Reviewer should verify no PII remains in masked text.'
            if changed else
            'No patterns detected — verify manually before any export.'
        ),
    }
