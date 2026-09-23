"""Small, transparent illustrative lexicon; not a general clinical NLP model.

Unknown language/phrasing is not a negative finding. Narrative context is
conservatively marked uncertain; a professional must confirm every note.
"""
from dataclasses import dataclass, field
import re

from app.schemas.triage import Symptom, Vitals

ALIASES = {
    'breathing_difficulty': ('difficulty breathing', 'breathing difficulty', 'breathlessness', 'shortness of breath', 'सांस लेने में तकलीफ', 'साँस लेने में तकलीफ', 'ଶ୍ୱାସ ନେବାରେ କଷ୍ଟ'),
    'unconsciousness': ('unconscious', 'not responding', 'बेहोश', 'ଅଚେତ'),
    'altered_consciousness': ('altered consciousness', 'new confusion', 'suddenly confused'),
    'chest_pain': ('chest pain', 'सीने में दर्द', 'ଛାତିରେ ଯନ୍ତ୍ରଣା'),
    'sweating': ('sweating', 'पसीना', 'ଝାଳ'),
    'seizure': ('seizure', 'convulsions', 'दौरा', 'ଖିଞ୍ଚୁଣି'),
    'heavy_bleeding': ('heavy bleeding', 'bleeding heavily', 'बहुत खून बह', 'ଅଧିକ ରକ୍ତସ୍ରାବ'),
    'bleeding': ('bleeding', 'खून बह', 'ରକ୍ତସ୍ରାବ'),
    'severe_headache': ('severe headache', 'तेज सिरदर्द', 'ତୀବ୍ର ମୁଣ୍ଡବିନ୍ଧା'),
    'reduced_fetal_movement': ('reduced fetal movement', 'baby moving less', 'बच्चे की हलचल कम'),
    'high_fever': ('high fever', 'तेज बुखार', 'ଅଧିକ ଜ୍ୱର'),
    'persistent_high_fever': ('persistent high fever', 'लगातार तेज बुखार'),
    'neck_stiffness': ('neck stiffness', 'stiff neck', 'गर्दन में अकड़न'),
    'severe_dehydration_signs': ('severe dehydration signs', 'unable to drink', 'cannot drink', 'no urine all day'),
    'snake_or_animal_bite': ('snake bite', 'snakebite', 'animal bite', 'dog bite', 'सांप ने काटा', 'कुत्ते ने काटा'),
    'fever': ('fever', 'बुखार', 'ଜ୍ୱର'),
    'cough': ('cough', 'खांसी', 'खाँसी', 'କାଶ'),
    'weakness': ('weakness', 'feeling weak', 'कमजोरी', 'ଦୁର୍ବଳ'),
    'fatigue': ('fatigue', 'थकान'),
    'headache': ('headache', 'सिर में हल्का दर्द'),
    'runny_nose': ('runny nose',),
    'wrist_discomfort': ('wrist discomfort',),
    'ear_noise': ('ear noise', 'कान में आवाज'),
}
PREGNANCY = ('pregnant', 'गर्भवती', 'गर्भावस्था', 'ଗର୍ଭବତୀ')
UNCERTAIN = re.compile(r'\b(uncertain|might|maybe|possibly|unsure|not sure|history of|previously|last year|if|hypothetical|denies?)\b|शायद|ସନ୍ଦେହ', re.I)
NEGATIVE = re.compile(r'\b(no|not|without|denied)\b|नहीं|ନାହିଁ', re.I)
DURATION = re.compile(r'\b(?:\d{1,3}|one|two|three|four|five|six|seven)\s+(?:minutes?|hours?|days?|weeks?)\b|(?:एक|दो|तीन|चार|पांच|\d{1,3})\s+(?:दिन|घंटे|सप्ताह)|(?:ଦୁଇ|ତିନି|ଏକ)\s+ଦିନ', re.I)
TIME = re.compile(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|today|yesterday|this morning)\b|आज|कल|ଆଜି', re.I)


@dataclass
class Scan:
    symptoms: list[Symptom] = field(default_factory=list)
    pregnancy_status: str = 'unknown'
    duration: str | None = None
    times: list[str] = field(default_factory=list)
    vitals: Vitals = field(default_factory=Vitals)
    flags: list[str] = field(default_factory=list)
    routine: bool = False


def phrase_matches(phrase: str, text: str):
    # Unicode words need language-specific tokenizers; only enforce English boundaries here.
    pattern = re.escape(phrase)
    if phrase.isascii():
        pattern = r'(?<!\w)' + pattern + r'(?!\w)'
    return re.finditer(pattern, text, re.I)


def assertion(clause: str, phrase: str) -> str:
    context = re.sub(re.escape(phrase), '', clause, flags=re.I)
    if UNCERTAIN.search(context):
        # "denies" is deliberately uncertain until a reviewer verifies scope.
        return 'uncertain'
    if NEGATIVE.search(context):
        return 'denied'
    return 'reported'


def scan_text(text: str, structured: Vitals) -> Scan:
    result = Scan(vitals=structured.model_copy(deep=True))
    clauses = re.split(r'[.!?;।\n]|\b(?:but|however|now)\b|लेकिन', text, flags=re.I)
    seen: set[tuple[str, str, str]] = set()
    for clause in clauses:
        for name, phrases in ALIASES.items():
            for phrase in phrases:
                for match in phrase_matches(phrase, clause):
                    state = assertion(clause, phrase)
                    evidence = match.group(0)
                    key = (name, state, evidence.casefold())
                    if key not in seen:
                        # Only a whitelisted symptom span, not the whole raw clause, is exposed.
                        result.symptoms.append(Symptom(name=name, assertion=state, evidence=evidence, source='text'))
                        seen.add(key)
        for phrase in PREGNANCY:
            if list(phrase_matches(phrase, clause)):
                state = assertion(clause, phrase)
                pregnancy = {'reported': 'pregnant', 'denied': 'not_pregnant', 'uncertain': 'unknown'}[state]
                if result.pregnancy_status not in ('unknown', pregnancy):
                    result.flags.append('conflicting_pregnancy_information')
                if pregnancy == 'pregnant' or result.pregnancy_status == 'unknown':
                    result.pregnancy_status = pregnancy
    for name in {s.name for s in result.symptoms}:
        states = {s.assertion for s in result.symptoms if s.name == name}
        if len(states) > 1:
            result.flags.append('contradictory_symptom_assertions')
    if any(s.assertion == 'uncertain' for s in result.symptoms):
        result.flags.append('uncertain_symptom_context')
    duration = DURATION.search(text)
    result.duration = duration.group(0) if duration else None
    result.times = list(dict.fromkeys(m.group(0) for m in TIME.finditer(text)))
    result.routine = bool(re.search(r'\b(?:routine|scheduled)\s+(?:screening|check-in|hearing screening)|नियमित जांच', text, re.I))
    patterns = {
        'spo2': r'(?:spo2|oxygen saturation)\s*(?:of|is|:|=)?\s*(\d{1,3}(?:\.\d+)?)\s*(?:%|percent)',
        'temp': r'(?:temperature|temp|तापमान)\s*(?:of|is|:|=)?\s*(\d{2}(?:\.\d+)?)\s*(?:°?\s*C\b|celsius)',
    }
    for name, pattern in patterns.items():
        for match in re.finditer(pattern, text, re.I):
            value = float(match.group(1))
            try:
                candidate = Vitals(**{name: value})
            except ValueError:
                result.flags.append('invalid_narrative_measurement')
                continue
            old = getattr(result.vitals, name)
            if old is not None and old != value:
                result.flags.append('conflicting_measurements')
                # Preserve the more urgent measured SpO2; neither measurement is called confirmed.
                value = min(old, value) if name == 'spo2' else max(old, value)
            setattr(result.vitals, name, value)
    if re.search(r'ignore\s+(?:all\s+)?(?:previous\s+)?(?:rules|instructions)|mark\s+(?:as\s+)?normal|prescribe|diagnos[ei]|which medicine', text, re.I):
        result.flags.append('instruction_or_advice_request_needs_review')
    if not result.symptoms and not result.routine and result.pregnancy_status == 'unknown':
        result.flags.append('unrecognized_or_empty_narrative')
    return result
