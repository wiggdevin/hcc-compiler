"""Applicability scoring: score_applicability(atom, intake) -> float in [0, 1].

Weighted rubric:
  0.4 * age_score  +  0.2 * sex_score  +  0.4 * training_status_score

Each sub-score is 1.0 (exact / universal), 0.5 (adjacent), 0.2 (far), or 0.3 (opposite sex).
Atom field values are free-form strings; we use keyword-based normalisation.
"""
from __future__ import annotations

from hcc_compiler.models import EvidenceAtom
from hcc_compiler.sp2.intake import ClientIntake

# ---------------------------------------------------------------------------
# Age band mapping
# ---------------------------------------------------------------------------

# Ordered bands — distance between bucket indices is used for partial credit.
_AGE_BANDS = [
    "adolescent",    # 14–17
    "young adult",   # 18–34
    "adult",         # 35–54
    "older adult",   # 55–64
    "65+",           # 65+
]

_BAND_INDEX: dict[str, int] = {b: i for i, b in enumerate(_AGE_BANDS)}


def _age_band(age: int) -> str:
    """Map an intake age integer to one of the canonical age-band labels."""
    if age <= 17:
        return "adolescent"
    if age <= 34:
        return "young adult"
    if age <= 54:
        return "adult"
    if age <= 64:
        return "older adult"
    return "65+"


# Keywords / phrases that unambiguously map atom age strings to a band.
# We check lower-cased atom value for each pattern.
# Checked in order; first match wins.
_AGE_KEYWORD_MAP: list[tuple[str, str]] = [
    # --- universal / any-age signals ---
    ("general",         "any"),
    ("all",             "any"),
    ("broad",           "any"),
    ("lifespan",        "any"),
    ("unspecified",     "any"),
    ("various",         "any"),
    ("youth and adult", "any"),
    # --- adolescent ---
    ("adolescen",       "adolescent"),
    ("youth",           "adolescent"),
    ("child",           "adolescent"),
    ("school-aged",     "adolescent"),
    ("6-17",            "adolescent"),
    ("10-19",           "adolescent"),
    ("11-17",           "adolescent"),
    ("≤18",             "adolescent"),
    ("≤18",        "adolescent"),  # ≤18 (unicode)
    ("≥14",             "adolescent"),   # ≥14 years
    ("≥14",        "adolescent"),
    ("≥15",             "adolescent"),
    ("≥15",        "adolescent"),
    ("university",      "adolescent"),  # university students = young/adolescent
    # --- young adult ---
    ("young adult",     "young adult"),
    ("young healthy",   "young adult"),
    ("18-30",           "young adult"),
    ("18-55",           "young adult"),  # spans young-adult into adult; map midpoint
    ("18-65",           "young adult"),  # wide span; conservative label
    ("18+",             "young adult"),
    ("adults (≥18",     "young adult"),
    ("adults (≥18","young adult"),
    ("≥18 yr",          "young adult"),
    ("≥18",             "young adult"),
    ("≥18",        "young adult"),
    ("20-47",           "young adult"),
    ("25.16",           "young adult"),  # 25.16 ± 5.22 years
    ("perinatal",       "young adult"),
    ("reproductive",    "young adult"),
    # --- older adult (MUST come before generic "adult" entries) ---
    ("older adults",    "older adult"),
    ("older/postmenop", "older adult"),
    # --- adult (general) ---
    ("adult",           "adult"),
    ("adults",          "adult"),
    ("35-65",           "adult"),
    ("45-64",           "adult"),
    ("< 50",            "adult"),
    ("8 to 68",         "adult"),       # broad mixed span → adult
    ("perimenopaus",    "adult"),
    ("perimenopausal",  "adult"),
    ("postmenopaus",    "adult"),       # without context, postmenopaus → adult (≥45)
    (">60",             "older adult"),
    ("≥40-45",          "older adult"),
    ("≥40-45",     "older adult"),
    ("≥60",             "older adult"),
    ("≥60",        "older adult"),
    ("60-80",           "older adult"),
    ("60.2",            "older adult"),
    ("60+ years",       "older adult"),
    ("55-80",           "older adult"),
    ("50+ years",       "older adult"),
    ("68.3",            "older adult"),
    ("73.1",            "older adult"),
    # --- 65+ ---
    ("65 years and older", "65+"),
    ("65+",             "65+"),
]


def _normalise_age(atom_age: str) -> str:
    """Map a free-form atom age string to a canonical band or 'any'."""
    v = atom_age.strip().lower()
    if not v:
        return "any"
    for keyword, band in _AGE_KEYWORD_MAP:
        if keyword in v:
            return band
    # Fallback: if "adult" appears, call it "adult"
    if "adult" in v:
        return "adult"
    return "any"


def _age_score(atom_age: str, intake_age: int) -> float:
    intake_band = _age_band(intake_age)
    atom_band = _normalise_age(atom_age)
    if atom_band == "any":
        return 1.0
    if atom_band == intake_band:
        return 1.0
    dist = abs(_BAND_INDEX.get(atom_band, 2) - _BAND_INDEX.get(intake_band, 2))
    if dist == 1:
        return 0.5
    return 0.2


# ---------------------------------------------------------------------------
# Sex scoring
# ---------------------------------------------------------------------------

_SEX_UNIVERSAL: frozenset[str] = frozenset({
    "both", "any", "all", "", "male and female", "male/female", "female/male",
    "males and females", "males and females", "mixed", "not specified",
    "unspecified", "male and female", "healthy adults",
})


def _normalise_sex(v: str) -> str:
    """Return 'M', 'F', 'any', or 'mixed'."""
    v = v.strip().lower()
    if not v or v in _SEX_UNIVERSAL:
        return "any"
    # percentage-style descriptions → mixed
    if "%" in v or "male and female" in v or "females" in v and "males" in v:
        return "any"
    if "female" in v and "male" not in v:
        return "F"
    if "male" in v and "female" not in v:
        return "M"
    return "any"


def _sex_score(atom_sex: str, intake_sex: str) -> float:
    atom = _normalise_sex(atom_sex)
    if atom == "any":
        return 1.0
    # intake sex is already "M", "F", or "other" (from ClientIntake)
    intake = intake_sex  # "M", "F", "other"
    if intake == "other":
        return 0.7  # no clean match possible; give moderate score
    if atom == intake:
        return 1.0
    # opposite sex
    return 0.3


# ---------------------------------------------------------------------------
# Training-status scoring
# ---------------------------------------------------------------------------

# Ordered training ladder (for distance-based partial credit)
_TRAINING_RANKS: list[str] = ["untrained", "recreational", "trained", "competitive"]
_TRAINING_RANK_IDX: dict[str, int] = {t: i for i, t in enumerate(_TRAINING_RANKS)}

# Keywords that unambiguously tag an atom training_status to a canonical rank
_TRAINING_KEYWORD_MAP: list[tuple[str, str]] = [
    # universal
    ("any",             "any"),
    ("all",             "any"),
    ("general population","any"),
    ("general",         "any"),
    ("various",         "any"),
    ("unspecified",     "any"),
    ("mixed",           "any"),
    ("healthy adults",  "any"),
    ("healthy individuals","any"),
    ("healthy populations","any"),
    ("individuals",     "any"),
    ("not specified",   "any"),
    # clinical / special populations → treat as any (not on rank ladder)
    ("patient",         "any"),
    ("cancer",          "any"),
    ("diabetes",        "any"),
    ("stroke",          "any"),
    ("rehabilitation",  "any"),
    ("clinical",        "any"),
    ("community-dwelling","any"),
    ("ambulatory",      "any"),
    ("cerebral",        "any"),
    ("asthma",          "any"),
    ("pain",            "any"),
    ("copd",            "any"),
    ("hemodialysis",    "any"),
    ("heart",           "any"),
    ("sickle",          "any"),
    ("fibromyalgia",    "any"),
    ("sarcopenic",      "any"),
    ("sarcopenia",      "any"),
    ("osteosarcopenic", "any"),
    ("hypertensive",    "any"),
    ("overweight",      "any"),
    ("obese",           "any"),
    ("obesity",         "any"),
    ("non-diabetic",    "any"),
    ("older adults",    "any"),
    ("school-aged",     "any"),
    ("youth",           "any"),
    ("adolescen",       "any"),
    ("workers",         "any"),
    ("hip fracture",    "any"),
    ("lung cancer",     "any"),
    ("post-stroke",     "any"),
    ("post-surgical",   "any"),
    ("parkinson",       "any"),
    ("multiple sclerosis","any"),
    ("congenital",      "any"),
    # untrained
    ("untrained",       "untrained"),
    ("sedentary",       "untrained"),
    ("beginner",        "untrained"),
    # recreational / moderate
    ("recreational",    "recreational"),
    ("physically active","recreational"),
    ("active",          "recreational"),
    ("exercising",      "recreational"),
    ("engaged in resistance","recreational"),
    ("engaging in strength","recreational"),
    ("resistance training participants","recreational"),
    # trained
    ("resistance-trained","trained"),
    ("resistance trained","trained"),
    ("trained",         "trained"),
    ("trained (minimum","trained"),
    ("trained and untrained","any"),
    ("trained or untrained","any"),
    ("untrained and trained","any"),
    ("untrained to moderately","any"),
    # competitive / elite
    ("elite",           "competitive"),
    ("competitive",     "competitive"),
    ("professional",    "competitive"),
    ("national",        "competitive"),
    ("world-class",     "competitive"),
    # sport-specific athletes → trained (default unless qualified as elite)
    ("athlete",         "trained"),
    ("player",          "trained"),
    ("swimmer",         "trained"),
    ("runner",          "trained"),
    ("wrestler",        "trained"),
    ("esport",          "recreational"),
    ("combat sport",    "trained"),
    ("martial arts",    "trained"),
    ("soccer",          "trained"),
    ("volleyball",      "trained"),
    ("basketball",      "trained"),
    ("racket",          "trained"),
    ("distance runner", "trained"),
]


def _normalise_training(v: str) -> str:
    """Return a canonical training rank or 'any'."""
    v_lower = v.strip().lower()
    if not v_lower:
        return "any"
    for keyword, rank in _TRAINING_KEYWORD_MAP:
        if keyword in v_lower:
            return rank
    return "any"


def _training_score(atom_training: str, intake_training: str) -> float:
    """intake_training is one of: untrained, recreational, trained, competitive."""
    atom = _normalise_training(atom_training)
    if atom == "any":
        return 1.0
    intake_idx = _TRAINING_RANK_IDX.get(intake_training, 1)
    atom_idx = _TRAINING_RANK_IDX.get(atom, 1)
    dist = abs(atom_idx - intake_idx)
    if dist == 0:
        return 1.0
    if dist == 1:
        return 0.7
    if dist == 2:
        return 0.4
    return 0.2


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_applicability(atom: EvidenceAtom, intake: ClientIntake) -> float:
    """Return a [0, 1] applicability score for an atom given a client intake.

    Weighted rubric:
      0.4 × age_score + 0.2 × sex_score + 0.4 × training_status_score
    """
    pa = atom.population_applicability
    age_s = _age_score(pa.age, intake.demographics.age)
    sex_s = _sex_score(pa.sex, intake.demographics.sex)
    train_s = _training_score(pa.training_status, intake.training_status)
    raw = 0.4 * age_s + 0.2 * sex_s + 0.4 * train_s
    return max(0.0, min(1.0, raw))
