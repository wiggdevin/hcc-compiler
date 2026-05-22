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
