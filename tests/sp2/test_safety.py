"""Tests for check_contraindications (T4)."""
from __future__ import annotations
from datetime import date
import pytest

from hcc_compiler.models import (
    EvidenceAtom,
    RecommendationPattern,
    EvidenceLevel,
    Domain,
    Tier,
    Citation,
    PopulationApplicability,
)
from hcc_compiler.sp2.intake import ClientIntake, Demographics, Constraint
from hcc_compiler.sp2.safety import check_contraindications


# ── Helpers ──────────────────────────────────────────────────────────────────

def _demographics() -> Demographics:
    return Demographics(age=30, sex="M", weight_kg=80.0, height_cm=178.0)


def _citation() -> Citation:
    return Citation(
        id="10.0000/test",
        locator_quote="Tested in healthy adults.",
        existence="VERIFIED",
        faithfulness="VERIFIED",
    )


def _population() -> PopulationApplicability:
    return PopulationApplicability(
        age="18-65",
        sex="all",
        training_status="trained",
        dose_magnitude="3-5 g/day",
        duration="4-12 weeks",
    )


def _creatine_atom(contraindications: list[str] | None = None) -> EvidenceAtom:
    return EvidenceAtom(
        id="EA-SUP-0001",
        domain=Domain.SUPPLEMENTS,
        claim="Creatine monohydrate increases maximal strength.",
        evidence_level=EvidenceLevel.L1,
        citations=[_citation()],
        population_applicability=_population(),
        effect="Strength +5-10%",
        contraindications=contraindications if contraindications is not None else [
            "renal insufficiency",
            "kidney disease",
        ],
        tier=Tier.HIGH_IMPACT,
        approval="approved",
        library_version="1.0.0",
        last_reviewed=date(2025, 1, 1),
        expiry=date(2027, 1, 1),
    )


def _squat_pattern(doesnt_apply_if: str = "acute knee injury") -> RecommendationPattern:
    return RecommendationPattern(
        id="RP-TRA-deep-squat",
        domain=Domain.TRAINING,
        pattern="Deep squat protocol",
        parameterization="3x8 @ 80% 1RM",
        backing_atom_ids=["EA-TRA-0001"],
        falsification_signal="Pain or range-of-motion loss.",
        safety_bounds="Stop if sharp pain.",
        applies_because="Compound movement for strength.",
        doesnt_apply_if=doesnt_apply_if,
        tier=Tier.HIGH_IMPACT,
        approval="approved",
        version="1.0.0",
    )


def _healthy_intake() -> ClientIntake:
    return ClientIntake(
        client_id="healthy-001",
        library_version="1.0.0",
        demographics=_demographics(),
        training_status="trained",
        goals=["strength"],
        contraindications=[],
        constraints=[],
    )


def _ckd_intake() -> ClientIntake:
    return ClientIntake(
        client_id="ckd-001",
        library_version="1.0.0",
        demographics=_demographics(),
        training_status="trained",
        goals=["strength"],
        contraindications=["renal insufficiency"],
        constraints=[],
    )


def _knee_intake() -> ClientIntake:
    return ClientIntake(
        client_id="knee-001",
        library_version="1.0.0",
        demographics=_demographics(),
        training_status="recreational",
        goals=["strength"],
        contraindications=[],
        constraints=[Constraint(type="injury", detail="left knee patellar tendinopathy")],
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_ckd_intake_vs_creatine_atom_hits():
    """CKD intake with 'renal insufficiency' should flag creatine atom."""
    warnings = check_contraindications(_creatine_atom(), _ckd_intake())
    assert len(warnings) >= 1
    assert any("renal insufficiency" in w for w in warnings)


def test_knee_constraint_vs_squat_pattern_hits():
    """Knee injury constraint detail should trigger squat pattern warning."""
    # "acute knee injury" is a substring of the pattern's doesnt_apply_if;
    # intake has "left knee patellar tendinopathy" which contains "knee".
    # Use a needle that IS in the detail to guarantee a match.
    pattern = _squat_pattern(doesnt_apply_if="patellar tendinopathy")
    warnings = check_contraindications(pattern, _knee_intake())
    assert len(warnings) >= 1
    assert any("patellar tendinopathy" in w for w in warnings)


def test_healthy_intake_no_warnings_atom():
    """Healthy intake (no contraindications, no constraints) → empty list for atom."""
    warnings = check_contraindications(_creatine_atom(), _healthy_intake())
    assert warnings == []


def test_healthy_intake_no_warnings_pattern():
    """Healthy intake → empty list for pattern."""
    warnings = check_contraindications(_squat_pattern(), _healthy_intake())
    assert warnings == []


def test_case_insensitive_match():
    """Uppercase in intake ('CKD') still matches lowercase needle ('ckd')."""
    atom = _creatine_atom(contraindications=["ckd"])
    intake = ClientIntake(
        client_id="case-001",
        library_version="1.0.0",
        demographics=_demographics(),
        training_status="trained",
        goals=["strength"],
        contraindications=["CKD"],
        constraints=[],
    )
    warnings = check_contraindications(atom, intake)
    assert len(warnings) >= 1


def test_pattern_multi_needle_parsing():
    """doesnt_apply_if with commas, semicolons, newlines parses 3 distinct needles."""
    pattern = _squat_pattern(
        doesnt_apply_if="acute kidney injury, severe hypertension; uncontrolled diabetes"
    )
    intake = ClientIntake(
        client_id="multi-001",
        library_version="1.0.0",
        demographics=_demographics(),
        training_status="trained",
        goals=["longevity"],
        contraindications=["acute kidney injury", "severe hypertension", "uncontrolled diabetes"],
        constraints=[],
    )
    warnings = check_contraindications(pattern, intake)
    assert len(warnings) == 3


def test_empty_doesnt_apply_if_no_warnings():
    """Empty doesnt_apply_if string → no false positives."""
    pattern = _squat_pattern(doesnt_apply_if="")
    warnings = check_contraindications(pattern, _ckd_intake())
    assert warnings == []


def test_empty_atom_contraindications_no_warnings():
    """atom.contraindications=[] → empty list."""
    atom = _creatine_atom(contraindications=[])
    warnings = check_contraindications(atom, _ckd_intake())
    assert warnings == []


def test_warning_contains_matches_intake_suffix():
    """Each warning string ends with '(matches intake)'."""
    warnings = check_contraindications(_creatine_atom(), _ckd_intake())
    for w in warnings:
        assert w.endswith("(matches intake)")


def test_non_negotiable_constraint_does_not_match_non_hospitalized_atom():
    """Regression for 2026-05-23 test_v2 batch (Bradley): a healthy intake
    whose constraint detail contains 'non-negotiable' must NOT match an atom
    contraindication mentioning 'non-hospitalized populations' on the shared
    short token 'non'. 'non' is 3 chars — below the 5-char floor and not in
    the clinical-abbreviation allow-list — so it must drop out of significant
    tokens on both sides."""
    intake = ClientIntake(
        client_id="non-neg-001",
        library_version="1.0.0",
        demographics=_demographics(),
        training_status="trained",
        goals=["recomposition"],
        contraindications=[],
        constraints=[Constraint(type="dietary", detail="Mediterranean baseline is non-negotiable")],
    )
    atom = _creatine_atom(contraindications=["non-hospitalized populations"])
    warnings = check_contraindications(atom, intake)
    assert warnings == [], f"Expected no false-positive match on 'non' token, got: {warnings}"


def test_fatty_liver_intake_does_not_match_renal_disease_atom():
    """Regression for 2026-05-23 test_v2 batch (Tori): an intake with
    'MASLD (fatty liver disease)' must NOT match an atom contraindication
    'Pre-existing renal disease' on the shared token 'disease'. 'disease' is
    clinical-narrative filler (in _STOPWORDS) — distinct organ systems must
    not collide via generic words."""
    intake = ClientIntake(
        client_id="masld-001",
        library_version="1.0.0",
        demographics=_demographics(),
        training_status="recreational",
        goals=["weight_loss"],
        contraindications=["MASLD (fatty liver disease)"],
        constraints=[],
    )
    atom = _creatine_atom(contraindications=["Pre-existing renal disease"])
    warnings = check_contraindications(atom, intake)
    assert warnings == [], f"Expected no false-positive match on 'disease' token, got: {warnings}"


def test_renal_single_token_match_via_high_specificity():
    """Carl-CKD harm-reduction guardrail: a single shared token like 'renal'
    (organ-system anatomical adjective in _CLINICAL_HIGH_SPECIFICITY) MUST
    fire a contraindication match even when no other tokens overlap. Without
    this gate, clinically meaningful organ-system flags ('Pre-existing renal
    disease' atom contraindication vs 'renal insufficiency' intake) would
    silently miss when generic descriptors like 'pre-existing' and 'disease'
    get stopworded out. False-negative on a real safety signal is the worse
    error than over-warning."""
    intake = ClientIntake(
        client_id="carl-like-001",
        library_version="1.0.0",
        demographics=_demographics(),
        training_status="trained",
        goals=["strength"],
        contraindications=["renal insufficiency (CKD stage 2)"],
        constraints=[],
    )
    atom = _creatine_atom(contraindications=["Pre-existing renal disease"])
    warnings = check_contraindications(atom, intake)
    assert len(warnings) >= 1, (
        "Expected single-token match via 'renal' (high-specificity organ "
        "system); this is the Carl-CKD harm-reduction guardrail"
    )
    assert any("renal disease" in w for w in warnings)


def test_lone_generic_token_does_not_match():
    """Regression for 2026-05-23 test_v2 batch (David): a single shared
    generic word like 'weeks' (or 'weight', 'programming') from intake
    constraints must NOT fire a match against atom pattern contraindications.
    These tokens lack clinical specificity — the ≥2-token-or-high-specificity
    rule kills the lone-generic-word false positive."""
    intake = ClientIntake(
        client_id="david-like-001",
        library_version="1.0.0",
        demographics=_demographics(),
        training_status="trained",
        goals=["weight_loss"],
        contraindications=[],
        constraints=[Constraint(type="schedule", detail="~10 days every 8 weeks unsupervised travel")],
    )
    pattern = _squat_pattern(
        doesnt_apply_if="acute post-surgical rehabilitation within 6 weeks of procedure"
    )
    warnings = check_contraindications(pattern, intake)
    assert warnings == [], (
        f"Expected no false-positive on lone 'weeks' overlap; "
        f"both contexts share only the generic word. got: {warnings}"
    )
