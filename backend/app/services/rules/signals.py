"""
signals.py — Multilingual symptom signal scanner.

SAFETY NOTE: This is a small, transparent illustrative lexicon; NOT a general
clinical NLP model. Unknown language/phrasing is not a negative finding.
Narrative context is conservatively marked uncertain; a professional must
confirm every note.

Source: adapted from SandibJena/BPUT_Hackathon_2026_2nd_Phase (Stage 2 partial).
"""
from dataclasses import dataclass, field
import re

from app.schemas.triage import Symptom, Vitals

# ── Symptom signal aliases (English / Hindi / Odia) ────────────────────────
ALIASES: dict[str, tuple[str, ...]] = {
    'breathing_difficulty': (
        'difficulty breathing', 'breathing difficulty', 'breathlessness',
        'shortness of breath', 'can\'t breathe', 'cannot breathe',
        'saans lene mein takleef', 'saans lene mein dikkat',
        'ଶ୍ୱାସ ନେବାରେ କଷ୍ଟ',
    ),
    'unconsciousness': (
        'unconscious', 'not responding', 'not waking up', 'unresponsive',
        'बेहोश', 'behosh', 'beHosh', 'ଅଚେତ',
    ),
    'altered_consciousness': (
        'altered consciousness', 'new confusion', 'suddenly confused',
        'disoriented', 'not making sense',
    ),
    'chest_pain': (
        'chest pain', 'chest discomfort', 'chest tightness', 'chest pressure',
        'सीने में दर्द', 'seene mein dard', 'ছাতিরে ব্যথা',
        'ଛାତିରେ ଯନ୍ତ୍ରଣା', 'buka byatha',
    ),
    'sweating': (
        'sweating', 'diaphoresis', 'drenched in sweat', 'cold sweat',
        'पसीना', 'paseena', 'ଝାଳ',
    ),
    'seizure': (
        'seizure', 'convulsions', 'convulsion', 'fit', 'jerking',
        'दौरा', 'daura', 'ଖିଞ୍ଚୁଣି',
    ),
    'heavy_bleeding': (
        'heavy bleeding', 'bleeding heavily', 'uncontrolled bleeding',
        'blood not stopping', 'बहुत खून बह', 'khoon ruk nahi raha',
        'ଅଧିକ ରକ୍ତସ୍ରାବ',
    ),
    'bleeding': (
        'bleeding', 'blood', 'खून बह', 'ରକ୍ତସ୍ରାବ',
    ),
    'severe_headache': (
        'severe headache', 'worst headache', 'thunderclap headache',
        'तेज सिरदर्द', 'bahut zyada sir dard', 'ତୀବ୍ର ମୁଣ୍ଡବିନ୍ଧା',
    ),
    'headache': (
        'headache', 'head ache', 'head pain', 'सिरदर्द', 'sir dard',
        'ମୁଣ୍ଡବିନ୍ଧା',
    ),
    'reduced_fetal_movement': (
        'reduced fetal movement', 'baby not moving', 'baby moving less',
        'fetal movement decreased', 'बच्चे की हलचल कम',
    ),
    'high_fever': (
        'high fever', 'very high fever', 'तेज बुखार', 'tej bukhar',
        'ଅଧିକ ଜ୍ୱର',
    ),
    'persistent_high_fever': (
        'persistent high fever', 'fever for days', 'fever not going down',
        'लगातार तेज बुखार',
    ),
    'fever': (
        'fever', 'temperature', 'bukhar', 'बुखार', 'ଜ୍ୱର', 'jara',
    ),
    'neck_stiffness': (
        'neck stiffness', 'stiff neck', 'neck rigidity', 'cannot bend neck',
        'गर्दन में अकड़न', 'gardan akadna', 'ବେକ ଶକ୍ତ',
    ),
    'severe_dehydration_signs': (
        'severe dehydration', 'no urine all day', 'sunken eyes', 'extreme thirst',
        'unable to drink', 'cannot drink', 'गंभीर निर्जलीकरण',
    ),
    'snake_or_animal_bite': (
        'snake bite', 'snakebite', 'snake has bitten', 'bitten by snake',
        'dog bite', 'dog bit', 'dog has bitten', 'animal bite', 'bitten by',
        'सांप ने काटा', 'saamp ne kata', 'saanp ne kata',
        'कुत्ते ने काटा', 'ସାପ କାମୁଡ଼ିଛି',
    ),
    'sudden_vision_loss': (
        'cannot see', 'vision gone', 'sudden blindness', 'lost vision',
        'vision loss', 'eyes not working', 'दिखना बंद',
    ),
    'sudden_hearing_loss': (
        'cannot hear', 'hearing gone', 'sudden deafness', 'hearing loss',
        'सुनना बंद',
    ),
    'severe_abdominal_pain': (
        'severe abdominal pain', 'severe stomach pain', 'unbearable stomach pain',
        'severe belly pain', 'abdomen is very painful',
        'पेट में बहुत दर्द', 'pet mein bahut dard', 'ତୀବ୍ର ପେଟ ବ୍ୟଥା',
    ),
    'abdominal_pain': (
        'abdominal pain', 'stomach pain', 'belly pain', 'pet dard',
        'पेट दर्द', 'ପେଟ ଦରଜ',
    ),
    'cough': ('cough', 'coughing', 'khansi', 'खांसी', 'खाँसी', 'କାଶ'),
    'weakness': ('weakness', 'feeling weak', 'kamzori', 'कमजोरी', 'ଦୁର୍ବଳ'),
    'fatigue': ('fatigue', 'exhausted', 'thakaan', 'थकान'),
    'vomiting': ('vomiting', 'nausea', 'ulti', 'उल्टी', 'ବାନ୍ତି'),
    'diarrhea': ('diarrhea', 'loose stools', 'dast', 'दस्त', 'ପତଳା ଝାଡ଼ା'),
    'dizziness': ('dizziness', 'dizzy', 'chakkar', 'चक्कर', 'ଘୁରଣୀ'),
    'runny_nose': ('runny nose', 'naak behna'),
    'sore_throat': ('sore throat', 'throat pain', 'gala dard', 'गले में दर्द'),
    'skin_rash': ('rash', 'skin rash', 'skin lesion', 'red spots', 'चकत्ते'),
    'wrist_discomfort': ('wrist discomfort', 'wrist pain'),
    'ear_noise': ('ear noise', 'ringing in ears', 'कान में आवाज'),
    'back_pain': ('back pain', 'lower back pain', 'पीठ दर्द'),
    'joint_pain': ('joint pain', 'knee pain', 'घुटने में दर्द'),
}

# Pregnancy markers
PREGNANCY_TERMS = (
    'pregnant', 'pregnancy', 'गर्भवती', 'गर्भावस्था',
    'गर्भ', 'ଗର୍ଭବତୀ', 'shishu garbh',
)

# Negative context patterns
NEGATIVE = re.compile(
    r'\b(no|not|without|denied|denies|never|negative for)\b'
    r'|नहीं|नही|ନାହିଁ',
    re.I,
)

# Uncertain context patterns
UNCERTAIN = re.compile(
    r'\b(uncertain|might|maybe|possibly|unsure|not sure|history of|'
    r'previously|last year|if|hypothetical|denies?|suspects?)\b'
    r'|शायद|ସନ୍ଦେହ',
    re.I,
)

# Duration patterns (e.g. "3 days", "since Monday")
DURATION = re.compile(
    r'\b(?:\d{1,3}|one|two|three|four|five|six|seven)\s+'
    r'(?:minutes?|hours?|days?|weeks?)\b'
    r'|(?:एक|दो|तीन|चार|पांच|\d{1,3})\s+(?:दिन|घंटे|सप्ताह)'
    r'|(?:ଦୁଇ|ତିନି|ଏକ)\s+ଦିନ',
    re.I,
)

# Time reference patterns
TIME_REF = re.compile(
    r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|'
    r'today|yesterday|this morning|since morning|since last night)\b'
    r'|आज|कल|ଆଜି',
    re.I,
)

# Prompt injection / advice request detection
INJECTION = re.compile(
    r'ignore\s+(?:all\s+)?(?:previous\s+)?(?:rules|instructions)'
    r'|mark\s+(?:as\s+)?normal'
    r'|prescribe|diagnos[ei]s?|which medicine|give medicine|treatment for',
    re.I,
)


@dataclass
class Scan:
    """Result of scanning a free-text narrative for clinical signals."""
    symptoms: list[Symptom] = field(default_factory=list)
    pregnancy_status: str = 'unknown'   # 'pregnant' | 'not_pregnant' | 'unknown'
    duration: str | None = None
    times: list[str] = field(default_factory=list)
    vitals: Vitals = field(default_factory=Vitals)
    flags: list[str] = field(default_factory=list)
    routine: bool = False


def _phrase_matches(phrase: str, text: str):
    """
    Match a phrase in text. Enforce word boundaries only for ASCII phrases
    (Unicode languages need language-specific tokenizers).
    """
    pattern = re.escape(phrase)
    if phrase.isascii():
        pattern = r'(?<!\w)' + pattern + r'(?!\w)'
    return list(re.finditer(pattern, text, re.I))


def _assertion(clause: str, phrase: str) -> str:
    """
    Determine if a phrase is affirmed, denied, or uncertain in a clause.
    Conservative: 'denies' is uncertain until a reviewer verifies.

    Negation must appear BEFORE the symptom phrase to count as denial
    (e.g. "no chest pain" → denied, but "chest pain not stopping" → reported).
    """
    phrase_pos = clause.lower().find(phrase.lower())
    if phrase_pos < 0:
        # Shouldn't happen since we found a match, but be safe
        return 'reported'

    # Check for uncertainty in full clause
    if UNCERTAIN.search(clause):
        return 'uncertain'

    # Only check negation in the text BEFORE the matched phrase
    context_before = clause[:phrase_pos]
    if NEGATIVE.search(context_before):
        return 'denied'

    return 'reported'


def scan_text(text: str, structured_vitals: Vitals) -> Scan:
    """
    Scan free-text narrative for clinical signals.

    SAFETY: Only whitelisted phrase spans are extracted, not raw clauses.
    Unrecognized text is never treated as a negative finding.
    All output is advisory and must be reviewed by a qualified professional.
    """
    result = Scan(vitals=structured_vitals.model_copy(deep=True))

    # Split text into clauses for local assertion checking
    clauses = re.split(r'[.!?;।\n]|\b(?:but|however|now)\b|लेकिन', text, flags=re.I)

    seen: set[tuple[str, str, str]] = set()

    for clause in clauses:
        # ── Symptom signal matching ──────────────────────────────────────────
        for signal_name, phrases in ALIASES.items():
            for phrase in phrases:
                matches = _phrase_matches(phrase, clause)
                for m in matches:
                    state = _assertion(clause, phrase)
                    evidence = m.group(0)
                    key = (signal_name, state, evidence.casefold())
                    if key not in seen:
                        result.symptoms.append(Symptom(
                            name=signal_name,
                            assertion=state,
                            evidence=evidence,
                            source='text',
                        ))
                        seen.add(key)

        # ── Pregnancy detection ───────────────────────────────────────────────
        for phrase in PREGNANCY_TERMS:
            if _phrase_matches(phrase, clause):
                state = _assertion(clause, phrase)
                preg = {
                    'reported': 'pregnant',
                    'denied': 'not_pregnant',
                    'uncertain': 'unknown',
                }[state]
                if result.pregnancy_status not in ('unknown', preg):
                    result.flags.append('conflicting_pregnancy_information')
                if preg == 'pregnant' or result.pregnancy_status == 'unknown':
                    result.pregnancy_status = preg

    # ── Contradictory assertions ──────────────────────────────────────────────
    for name in {s.name for s in result.symptoms}:
        states = {s.assertion for s in result.symptoms if s.name == name}
        if len(states) > 1:
            result.flags.append(f'contradictory_assertions_for_{name}')

    if any(s.assertion == 'uncertain' for s in result.symptoms):
        result.flags.append('uncertain_symptom_context')

    # ── Narrative SpO2 / Temperature extraction ───────────────────────────────
    _extract_narrative_vitals(text, result)

    # ── Duration / Time extraction ────────────────────────────────────────────
    dur = DURATION.search(text)
    result.duration = dur.group(0) if dur else None
    result.times = list(dict.fromkeys(m.group(0) for m in TIME_REF.finditer(text)))

    # ── Routine screening flag ────────────────────────────────────────────────
    result.routine = bool(re.search(
        r'\b(?:routine|scheduled)\s+(?:screening|check-in|hearing screening)'
        r'|नियमित जांच',
        text, re.I,
    ))

    # ── Prompt injection / advice request detection ───────────────────────────
    if INJECTION.search(text):
        result.flags.append('instruction_or_advice_request_needs_review')

    # ── Empty narrative flag ──────────────────────────────────────────────────
    if not result.symptoms and not result.routine and result.pregnancy_status == 'unknown':
        result.flags.append('unrecognized_or_empty_narrative')

    return result


def _extract_narrative_vitals(text: str, result: Scan) -> None:
    """Extract SpO2 and temperature mentioned in free text."""
    patterns = {
        'spo2': r'(?:spo2|oxygen saturation|o2 sat)\s*(?:of|is|:|=)?\s*(\d{2,3}(?:\.\d+)?)\s*(?:%|percent)',
        'temp': r'(?:temperature|temp|तापमान)\s*(?:of|is|:|=)?\s*(\d{2}(?:\.\d+)?)\s*(?:°?\s*C\b|celsius)',
    }
    for field_name, pattern in patterns.items():
        for m in re.finditer(pattern, text, re.I):
            try:
                value = float(m.group(1))
                candidate = Vitals(**{field_name: value})
                old = getattr(result.vitals, field_name)
                if old is not None and old != value:
                    result.flags.append(f'conflicting_narrative_{field_name}')
                    # Conservative: take the more urgent value
                    value = min(old, value) if field_name == 'spo2' else max(old, value)
                setattr(result.vitals, field_name, value)
            except (ValueError, TypeError):
                result.flags.append('invalid_narrative_measurement')
