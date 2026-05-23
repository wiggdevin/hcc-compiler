from __future__ import annotations
import re
from hcc_compiler.models import EvidenceAtom, RecommendationPattern
from hcc_compiler.sp2.intake import ClientIntake

_SPLIT_RE = re.compile(r"[,;\n]")
_TOKEN_SPLIT_RE = re.compile(r"[\W_]+")

# Words too generic to anchor a clinical contraindication match. Spans English
# connective tissue, generic descriptors, and recurring clinical-narrative
# filler that appears across disparate atom contraindications ("disease",
# "patients", "training", ...) without identifying the actual condition.
# Anything kept after stopword + length filtering must carry real specificity
# — an organ system, condition, drug class, or measurable signal.
_STOPWORDS = frozenset({
    # connective tissue
    "or", "and", "the", "of", "with", "if", "in", "to", "for", "by", "on", "at",
    "is", "are", "as", "an", "a", "be", "any", "other", "where", "these", "from",
    # generic descriptors
    "pre", "post", "existing", "active", "type", "history", "current", "recent",
    "chronic", "acute", "currently", "directly", "apply", "applies",
    "based", "specific", "modality", "without", "clearance", "rules",
    # clinical-narrative filler — appears as backdrop, not as the condition
    "contraindication", "contraindications", "disease", "diseases", "disorder",
    "disorders", "patient", "patients", "population", "populations",
    "individual", "individuals", "subject", "subjects", "people", "person",
    "persons", "adult", "adults", "child", "children", "older", "younger",
    "study", "studies", "evidence", "training", "exercise", "exercising",
    "condition", "conditions", "clinical", "medical", "health", "healthy",
    "treatment", "treatments", "intervention", "interventions",
    "protocol", "protocols", "phase", "phases", "session", "sessions",
})

# Short clinical abbreviations admitted despite being below the 5-char floor.
# Lowercased. Keep this list short — every entry is a single-shot exception to
# the length rule, so each addition risks readmitting generic short tokens
# (units, prepositions). Only add entries when a real clinical use surfaces.
_CLINICAL_ABBREVIATIONS = frozenset({
    "ckd", "esrd", "afib", "copd", "cvd", "ibd", "ibs", "uti",
    "hiv", "hbv", "hcv", "t1d", "t2d", "dm1", "dm2",
    "gerd", "ptsd", "adhd", "rls", "osa", "pcos", "lvh", "hfpef", "hfref",
})

# Tokens with intrinsic clinical specificity — named organ systems, condition
# names, drug classes, life-stage states. When such a token is the lone shared
# signal between needle and haystack, that single match is still meaningful
# enough to fire a contraindication warning. Generic words like "weeks",
# "weight", "based" must share ≥2 tokens to fire; high-specificity terms only
# need 1. This is the harm-reduction gate that preserves Carl-CKD's
# "Pre-existing renal disease" match on the lone shared token "renal".
_CLINICAL_HIGH_SPECIFICITY = _CLINICAL_ABBREVIATIONS | frozenset({
    # Organ systems / anatomical adjectives
    "renal", "hepatic", "cardiac", "pulmonary", "cerebral", "spinal",
    "thyroid", "pancreatic", "adrenal", "ovarian", "uterine", "prostatic",
    "gastric", "intestinal", "musculoskeletal", "neurological", "neurologic",
    "endocrine", "gastrointestinal", "respiratory", "cardiovascular",
    "hematologic", "hematological", "oncologic", "oncological",
    "dermatologic", "dermatological", "psychiatric",
    # Named conditions (full-word)
    "hypothyroidism", "hyperthyroidism", "hypertension", "hypotension",
    "diabetes", "asthma", "anemia", "epilepsy", "depression", "obesity",
    "anorexia", "bulimia", "hypogonadism", "osteoporosis", "osteopenia",
    "arthritis", "fibromyalgia", "rhabdomyolysis", "myocarditis",
    "pericarditis", "nephritis", "cirrhosis", "hepatitis", "pancreatitis",
    "gastritis", "colitis", "dermatitis", "psoriasis", "eczema", "lupus",
    "alzheimer", "parkinson", "schizophrenia", "bipolar",
    "leukemia", "lymphoma", "melanoma", "carcinoma", "sarcoma",
    "masld", "nafld", "preeclampsia",
    # Drug names and classes
    "warfarin", "metformin", "insulin", "statin", "statins", "ssri",
    "opioid", "opioids", "benzodiazepine", "benzodiazepines",
    "corticosteroid", "corticosteroids", "anticoagulant", "anticoagulants",
    "immunosuppressant", "immunosuppressants", "antidepressant",
    "antipsychotic", "chemotherapy",
    # Life-stage and reproductive states
    "pregnancy", "pregnant", "lactation", "breastfeeding",
    "menstrual", "menopausal", "perimenopausal", "postmenopausal",
    "premenopausal",
    # Acute events and structural pathologies (single-token harm-reduction:
    # a lone "stroke" or "seizure" in intake matching a lone occurrence in
    # an atom contraindication MUST fire — these are catastrophic if missed)
    "cancer", "tumor", "tumors", "stroke", "seizure", "seizures", "angina",
    "fracture", "fractures", "arrhythmia", "arrhythmias", "embolism",
    "thrombosis", "hemorrhage", "dialysis", "ischemia", "infarction",
})


def _significant_tokens(text: str) -> set[str]:
    """Lowercased tokens with clinical specificity, excluding stopwords. Used
    as fallback matching when direct substring fails. ≥5-char floor blocks
    generic 3-4-char filler ('non', 'low', 'high', 'mid', 'iron'); the
    abbreviation allow-list re-admits short clinical codes ('ckd', 'copd', …)."""
    return {
        tok
        for tok in _TOKEN_SPLIT_RE.split(text.lower())
        if tok not in _STOPWORDS
        and (len(tok) >= 5 or tok in _CLINICAL_ABBREVIATIONS)
    }


def check_contraindications(
    record: EvidenceAtom | RecommendationPattern,
    intake: ClientIntake,
) -> list[str]:
    """Return list of warning strings, one per matched contraindication."""
    haystack_parts = list(intake.contraindications) + [c.detail for c in intake.constraints]
    haystack = " ".join(haystack_parts).lower()
    haystack_tokens = _significant_tokens(haystack)

    if isinstance(record, EvidenceAtom):
        originals = list(record.contraindications)
    else:
        parts = _SPLIT_RE.split(record.doesnt_apply_if)
        originals = [p.strip() for p in parts if p.strip()]

    warnings: list[str] = []
    for original in originals:
        needle = original.lower().strip()
        if not needle:
            continue
        if needle in haystack:
            warnings.append(f"⚠ {original} (matches intake)")
            continue
        # Fallback: significant-token overlap. Two paths fire a match —
        # (a) ≥1 shared token is high-specificity clinical (organ system,
        #     named condition, drug class, clinical abbreviation), or
        # (b) ≥2 shared tokens regardless of specificity.
        # The two-path rule lets "renal" alone match "renal insufficiency"
        # while requiring multiple shared tokens before a lone generic
        # word fires. Kills lone-generic-word false positives ("weeks",
        # "based", "weight") that plagued the 2026-05-23 test_v2 batch
        # without sacrificing single-token organ-system or acute-event
        # safety signals.
        overlap = _significant_tokens(needle) & haystack_tokens
        if (overlap & _CLINICAL_HIGH_SPECIFICITY) or len(overlap) >= 2:
            warnings.append(f"⚠ {original} (matches intake)")

    return warnings
