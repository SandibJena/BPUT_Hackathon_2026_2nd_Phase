def mask_pii(text: str) -> str:
    """
    Safety rationale: Removes PII before LLM processing.
    """
    # TODO Stage 5: implement regex + NER masking for names, phones, Aadhaar
    return text
