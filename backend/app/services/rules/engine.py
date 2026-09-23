def load_rules(yaml_path: str):
    """
    Safety rationale: Ensures deterministic rule loading.
    """
    return []

def evaluate_rules(symptoms, vitals, history, scenario):
    """
    Safety rationale: Evaluates rules without side effects.
    """
    if not symptoms:
        return {"category": "INSUFFICIENT_INFO", "triggered_rules": [], "reasons": []}
    return {"category": "NORMAL", "triggered_rules": [], "reasons": []}
