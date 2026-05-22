"""Tests for score_applicability (SP2 — T3).

Covers:
- Exact-match intake → score close to 1.0
- Totally-wrong intake → score < 0.4
- Atom "any" on all axes → 1.0 regardless of intake
- Parametrized test: every unique atom value found via:
    grep -h "  age:" library/atoms/**/*.yaml | sort -u
    grep -h "  sex:" library/atoms/**/*.yaml | sort -u
    grep -h "  training_status:" library/atoms/**/*.yaml | sort -u
  Each must produce a finite score without raising.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Any

import pytest

from hcc_compiler.models import (
    Citation,
    Domain,
    EvidenceAtom,
    EvidenceLevel,
    PopulationApplicability,
    Tier,
)
from hcc_compiler.sp2.intake import ClientIntake, Demographics
from hcc_compiler.sp2.score import score_applicability


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_intake(
    age: int = 30,
    sex: str = "M",
    training_status: str = "trained",
) -> ClientIntake:
    return ClientIntake(
        client_id="test-client",
        library_version="0.1.0",
        demographics=Demographics(
            age=age,
            sex=sex,
            weight_kg=80.0,
            height_cm=178.0,
        ),
        training_status=training_status,
        goals=["hypertrophy"],
    )


def _make_atom(
    age: str = "adults",
    sex: str = "both",
    training_status: str = "trained",
) -> EvidenceAtom:
    return EvidenceAtom(
        id="EA-TRA-0001",
        domain=Domain.TRAINING,
        claim="Test claim",
        evidence_level=EvidenceLevel.L1,
        citations=[
            Citation(
                id="10.1000/test",
                locator_quote="test",
                existence="VERIFIED",
                faithfulness="VERIFIED",
            )
        ],
        population_applicability=PopulationApplicability(
            age=age,
            sex=sex,
            training_status=training_status,
            dose_magnitude="N/A",
            duration="N/A",
        ),
        effect="test effect",
        tier=Tier.ROUTINE,
        approval="APPROVED",
        library_version="0.1.0",
        last_reviewed=date(2024, 1, 1),
        expiry=date(2026, 1, 1),
        contraindications=[],
    )


# ---------------------------------------------------------------------------
# Core behaviour tests
# ---------------------------------------------------------------------------

def test_exact_match_near_one():
    """Intake demographics aligning closely with atom → score near 1.0."""
    intake = _make_intake(age=28, sex="M", training_status="trained")
    atom = _make_atom(age="young adults", sex="male", training_status="trained")
    score = score_applicability(atom, intake)
    assert score >= 0.85, f"Expected ≥0.85 for exact-ish match, got {score}"


def test_totally_wrong_intake_low_score():
    """14yo untrained vs atom requiring 65+ competitive → score < 0.4."""
    intake = _make_intake(age=14, sex="F", training_status="untrained")
    # atom targets 65+, elite athletes
    atom = _make_atom(
        age="65 years and older",
        sex="male",
        training_status="elite",
    )
    score = score_applicability(atom, intake)
    assert score < 0.4, f"Expected <0.4 for totally wrong intake, got {score}"


def test_any_on_all_axes_returns_one():
    """Atom with any/all on every axis → 1.0 regardless of intake."""
    intake = _make_intake(age=14, sex="other", training_status="untrained")
    atom = _make_atom(age="general", sex="both", training_status="any")
    score = score_applicability(atom, intake)
    assert score == pytest.approx(1.0), f"Expected 1.0 for universal atom, got {score}"


def test_empty_strings_any_returns_one():
    """Empty strings on all axes → 1.0 (treated as any)."""
    intake = _make_intake(age=70, sex="F", training_status="recreational")
    atom = _make_atom(age="", sex="", training_status="")
    score = score_applicability(atom, intake)
    assert score == pytest.approx(1.0)


def test_score_range():
    """score_applicability always returns a value in [0, 1]."""
    import itertools
    ages = [14, 25, 45, 60, 75]
    sexes = ["M", "F", "other"]
    trainings = ["untrained", "recreational", "trained", "competitive"]
    for age, sex, ts in itertools.product(ages, sexes, trainings):
        intake = _make_intake(age=age, sex=sex, training_status=ts)
        atom = _make_atom(age="adults", sex="both", training_status="trained")
        score = score_applicability(atom, intake)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Parametrized: every unique age value found in library/atoms/**/*.yaml
# ---------------------------------------------------------------------------

_ALL_LIBRARY_AGE_VALUES = [
    ">60 years",
    "≤18 years",
    "≥14 years",
    "≥40-45 years (mean ≈ 62 y)",
    "11–17",
    "14.32 ± 2.29 years",
    "18-55",
    "18-65",
    "73.1 ± 6.6 years",
    "Adults (≥18 years)",
    "< 50 years",
    "10-19 years old",
    "≥15 years",
    "≥18 yr",
    "18-30 years",
    "18+",
    "20-47.2 years",
    "25.16 +/- 5.22 years",
    "35-65 years",
    "45-64 years",
    "50+ years",
    "55-80 years",
    "6-17 years",
    "≥60 years",
    "60-80 years",
    "60.2 years (mean)",
    "60+ years",
    "65 years and older",
    "68.3 ± 5.3 years",
    "8 to 68 years",
    "adult",
    "adults",
    "adults (subgroup analysis indicated age influenced outcomes)",
    "Adults (subgroups <60 and ≥60 years)",
    "adults (subgroups analyzed)",
    "adults (younger adults showed significant increases; older adults did not)",
    "broad (reproductive stages)",
    "children",
    "children and adolescents",
    "general",
    "general population (no definitive conclusion reached between middle-aged/elderly",
    "lifespan",
    "older adults",
    "Older adults",
    "Older adults (average 69 years)",
    "Older adults (implied by sarcopenia diagnosis)",
    "Older/Postmenopausal",
    "perimenopausal",
    "perinatal (pregnancy to 1 year postpartum)",
    "postmenopausal",
    "reproductive-age",
    "university students",
    "unspecified",
    "various",
    "young adults",
    "young healthy persons and athletes",
    "youth and adult",
]


@pytest.mark.parametrize("age_value", _ALL_LIBRARY_AGE_VALUES)
def test_age_value_no_exception(age_value: str):
    """Every unique age value in the library produces a finite score."""
    intake = _make_intake(age=30, sex="M", training_status="trained")
    atom = _make_atom(age=age_value, sex="both", training_status="any")
    score = score_applicability(atom, intake)
    assert math.isfinite(score), f"Non-finite score for age={age_value!r}"
    assert 0.0 <= score <= 1.0, f"Score out of range for age={age_value!r}: {score}"


# ---------------------------------------------------------------------------
# Parametrized: every unique sex value found in library/atoms/**/*.yaml
# ---------------------------------------------------------------------------

_ALL_LIBRARY_SEX_VALUES = [
    "both",
    "385 women (73%) and 143 men (27%)",
    "79.1% male, 20.9% female",
    "79.5% female",
    "all",
    "female",
    "Female",
    "female (breast cancer subgroup)",
    "female/male",
    "healthy adults",
    "male and female",
    "Male and female",
    "Male and Female",
    "male/female",
    "males (significant increases observed); females (benefits not observed)",
    "males and females",
    "Males and Females",
    "mixed",
    "Mixed",
    "Mixed (10.7% female)",
    "Mixed (63% male, 37% female)",
    "mixed (77% male)",
    "mixed (implied by 'volleyball athletes')",
    "mixed (limited female representation)",
    "mixed (predominantly male)",
    "not specified",
    "Not specified",
    "unspecified",
    "Unspecified",
]


@pytest.mark.parametrize("sex_value", _ALL_LIBRARY_SEX_VALUES)
def test_sex_value_no_exception(sex_value: str):
    """Every unique sex value in the library produces a finite score."""
    intake = _make_intake(age=30, sex="M", training_status="trained")
    atom = _make_atom(age="adults", sex=sex_value, training_status="any")
    score = score_applicability(atom, intake)
    assert math.isfinite(score), f"Non-finite score for sex={sex_value!r}"
    assert 0.0 <= score <= 1.0, f"Score out of range for sex={sex_value!r}: {score}"


# ---------------------------------------------------------------------------
# Parametrized: every unique training_status value found in library/atoms/**/*.yaml
# ---------------------------------------------------------------------------

_ALL_LIBRARY_TRAINING_VALUES = [
    "resistance-trained",
    "trained",
    "active",
    "amateur esports players",
    "ambulatory children with cerebral palsy (Gross Motor Function Classification",
    "asthma patients",
    "athletes",
    "Athletes",
    "athletes (any level)",
    "athletes and non-athletes",
    "athletes and physically active individuals",
    "athletes and RT enthusiasts",
    "basketball players",
    "cancer patients",
    "cancer survivors",
    "cardiovascular rehabilitation patients",
    "chronic pain patients",
    "combat sport athletes",
    "combined with resistance training",
    "Community-dwelling",
    "community-dwelling older adults",
    "competitive swimmers",
    "congenital heart disease patients",
    "COPD patients",
    "distance runners",
    "elite",
    "elite athletes",
    "engaged in resistance training",
    "engaging in strength training",
    "exercising",
    "fibromyalgia patients",
    "fit (70th percentile VO2max or higher) vs below-average",
    "general adolescents",
    "general population",
    "healthy adults",
    "Healthy adults",
    "healthy individuals, athletes, and clinical populations",
    "healthy older adults",
    "healthy populations",
    "hemodialysis patients",
    "highly trained endurance and elite other (mainly team sport) athletes",
    "hip fracture patients",
    "Hypertensive patients",
    "individuals with type 2 diabetes",
    "lung cancer patients",
    "martial arts athletes",
    "mixed",
    "Mixed",
    "mixed (46% trained)",
    "mixed (adjusted for)",
    "mixed (trained and untrained)",
    "mixed/untrained",
    "national to elite-level",
    "non-diabetic",
    "non-hospitalized elderly",
    "nonathletes and athletes inexperienced with NHE",
    "Not specified/Overweight or Obese",
    "older adults",
    "Older adults (physically healthy)",
    "osteosarcopenic",
    "overweight and obesity",
    "overweight or obesity",
    "patellofemoral pain patients",
    "patients with cancer",
    "patients with chronic obstructive pulmonary disease",
    "patients with coronary artery disease",
    "patients with fibromyalgia",
    "patients with heart failure with preserved ejection fraction (HFpEF)",
    "patients with sickle cell disease",
    "patients with stroke, Parkinson's disease, and multiple sclerosis",
    "people with type 2 diabetes",
    "physically active",
    "post-stroke patients",
    "post-surgical rehabilitation",
    "professional athletes",
    "racket sports athletes",
    "resistance training",
    "resistance training participants",
    "sarcopenic",
    "Sarcopenic",
    "Sarcopenic obesity",
    "Sarcopenic older adults",
    "sarcopenic or non-sarcopenic older adults",
    "school-aged youth",
    "sedentary",
    "Sedentary/Community-dwelling",
    "sedentary/general",
    "soccer players",
    "swimmers",
    "trained (minimum 6 months)",
    "trained and untrained",
    "trained and untrained individuals",
    "trained or untrained",
    "unspecified",
    "unspecified (overweight/obese)",
    "unspecified/clinical",
    "unspecified/older adults",
    "unspecified/overweight or obese",
    "unspecified/sedentary",
    "untrained",
    "untrained and trained individuals",
    "Untrained sedentary individuals to elite/world-class athletes",
    "untrained to moderately trained",
    "various",
    "volleyball players",
    "workers' compensation rehabilitation",
    "wrestlers",
    "youth",
    "Youth athletes",
]


@pytest.mark.parametrize("training_value", _ALL_LIBRARY_TRAINING_VALUES)
def test_training_value_no_exception(training_value: str):
    """Every unique training_status value in the library produces a finite score."""
    intake = _make_intake(age=30, sex="M", training_status="trained")
    atom = _make_atom(age="adults", sex="both", training_status=training_value)
    score = score_applicability(atom, intake)
    assert math.isfinite(score), f"Non-finite score for training_status={training_value!r}"
    assert 0.0 <= score <= 1.0, f"Score out of range for training_status={training_value!r}: {score}"


# ---------------------------------------------------------------------------
# A few targeted sub-score checks
# ---------------------------------------------------------------------------

def test_adjacent_age_band_partial_credit():
    """Intake in 'adult' band, atom in 'older adult' → age_score = 0.5 → reflected in final."""
    # adult (35-54) vs older adult (55-64): 1 band apart → age_score = 0.5
    # sex: both → 1.0; training: any → 1.0
    # final = 0.4*0.5 + 0.2*1.0 + 0.4*1.0 = 0.2 + 0.2 + 0.4 = 0.80
    intake = _make_intake(age=40, sex="M", training_status="trained")
    atom = _make_atom(age="older adults", sex="both", training_status="any")
    score = score_applicability(atom, intake)
    assert 0.75 <= score <= 0.85, f"Expected ~0.80 for adjacent age band, got {score}"


def test_opposite_sex_partial_credit():
    """Male intake, female atom → sex_score = 0.3."""
    # sex: 0.3, age: adults→any=1.0, training: any→1.0
    # final = 0.4*1.0 + 0.2*0.3 + 0.4*1.0 = 0.4 + 0.06 + 0.4 = 0.86
    intake = _make_intake(age=30, sex="M", training_status="trained")
    atom = _make_atom(age="adults", sex="female", training_status="any")
    score = score_applicability(atom, intake)
    assert 0.80 <= score <= 0.92, f"Expected ~0.86 for opposite sex, got {score}"


def test_training_one_rank_apart():
    """Recreational intake vs trained atom → training_score = 0.7 (dist=1).

    age: adults → "adult", intake age=30 → "young adult" (1 band apart → age_score=0.5)
    sex: both → 1.0
    training: trained vs recreational, dist=1 → 0.7
    final = 0.4*0.5 + 0.2*1.0 + 0.4*0.7 = 0.2 + 0.2 + 0.28 = 0.68
    """
    intake = _make_intake(age=30, sex="M", training_status="recreational")
    atom = _make_atom(age="adults", sex="both", training_status="trained")
    score = score_applicability(atom, intake)
    # training dist=1 → 0.7; age dist=1 → 0.5 (young adult vs adult)
    # final = 0.4*0.5 + 0.2*1.0 + 0.4*0.7 = 0.68
    assert 0.60 <= score <= 0.76, f"Expected ~0.68 for one rank apart training, got {score}"


def test_training_two_ranks_apart():
    """Untrained intake vs trained atom → training_score = 0.4 (dist=2).

    With age=adults (any), sex=both (any):
    final = 0.4*1.0 + 0.2*1.0 + 0.4*0.4 = 0.76
    """
    intake = _make_intake(age=50, sex="M", training_status="untrained")  # age=50 → adult
    atom = _make_atom(age="adult", sex="both", training_status="trained")
    score = score_applicability(atom, intake)
    # age: exact match, sex: 1.0, training: dist=2 → 0.4
    # final = 0.4*1.0 + 0.2*1.0 + 0.4*0.4 = 0.76
    assert 0.70 <= score <= 0.82, f"Expected ~0.76 for two ranks apart training, got {score}"


def test_training_three_ranks_apart():
    """Untrained intake vs competitive atom → training_score = 0.2 (dist=3).

    With age=adults, sex=both — note age=30 → "young adult" vs "adult" (dist=1 → 0.5):
    final = 0.4*0.5 + 0.2*1.0 + 0.4*0.2 = 0.2 + 0.2 + 0.08 = 0.48
    """
    intake = _make_intake(age=30, sex="M", training_status="untrained")
    atom = _make_atom(age="adults", sex="both", training_status="elite")
    score = score_applicability(atom, intake)
    assert 0.40 <= score <= 0.56, f"Expected ~0.48 for three ranks apart training, got {score}"
