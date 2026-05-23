"""Tests for hcc_compiler.sp2.queries.derive_queries."""
from __future__ import annotations

import pytest

from hcc_compiler.models import Domain
from hcc_compiler.sp2.intake import ClientIntake, Constraint, Demographics
from hcc_compiler.sp2.queries import derive_queries


def _make_intake(
    goals=("hypertrophy",),
    training_status="trained",
    constraints=(),
    contraindications=(),
) -> ClientIntake:
    return ClientIntake(
        client_id="test-client",
        library_version="0.1.0",
        demographics=Demographics(age=30, sex="M", weight_kg=80.0, height_cm=178.0),
        training_status=training_status,
        goals=list(goals),
        constraints=list(constraints),
        contraindications=list(contraindications),
    )


class TestAllDomainsPresent:
    """Every Domain enum value must appear as a key."""

    def test_all_six_domains_returned(self):
        intake = _make_intake()
        result = derive_queries(intake)
        assert set(result.keys()) == set(Domain)

    def test_all_domains_have_at_least_one_query(self):
        intake = _make_intake()
        result = derive_queries(intake)
        for domain in Domain:
            assert len(result[domain]) >= 1, f"{domain} has no queries"


class TestGoalSurfacedInQueries:
    """The goal string must appear literally in at least one query per domain."""

    def test_hypertrophy_in_nutrition_queries(self):
        intake = _make_intake(goals=["hypertrophy"])
        result = derive_queries(intake)
        assert any("hypertrophy" in q for q in result[Domain.NUTRITION])

    def test_hypertrophy_in_training_queries(self):
        intake = _make_intake(goals=["hypertrophy"])
        result = derive_queries(intake)
        assert any("hypertrophy" in q for q in result[Domain.TRAINING])

    def test_hypertrophy_in_conditioning_queries(self):
        intake = _make_intake(goals=["hypertrophy"])
        result = derive_queries(intake)
        assert any("hypertrophy" in q for q in result[Domain.CONDITIONING])

    def test_hypertrophy_in_supplements_queries(self):
        intake = _make_intake(goals=["hypertrophy"])
        result = derive_queries(intake)
        assert any("hypertrophy" in q for q in result[Domain.SUPPLEMENTS])

    def test_hypertrophy_in_recovery_queries(self):
        intake = _make_intake(goals=["hypertrophy"])
        result = derive_queries(intake)
        assert any("hypertrophy" in q for q in result[Domain.RECOVERY])

    def test_hypertrophy_in_behavioral_queries(self):
        intake = _make_intake(goals=["hypertrophy"])
        result = derive_queries(intake)
        assert any("hypertrophy" in q for q in result[Domain.BEHAVIORAL])

    def test_endurance_goal_appears_in_queries(self):
        intake = _make_intake(goals=["endurance"])
        result = derive_queries(intake)
        all_queries = [q for qs in result.values() for q in qs]
        assert any("endurance" in q for q in all_queries)


class TestInjuryConstraint:
    """Injury constraints must surface in TRAINING and CONDITIONING queries."""

    def test_injury_in_training(self):
        constraint = Constraint(type="injury", detail="left knee ligament strain")
        intake = _make_intake(constraints=[constraint])
        result = derive_queries(intake)
        assert any("left knee ligament strain" in q for q in result[Domain.TRAINING])

    def test_injury_in_conditioning(self):
        constraint = Constraint(type="injury", detail="left knee ligament strain")
        intake = _make_intake(constraints=[constraint])
        result = derive_queries(intake)
        assert any("left knee ligament strain" in q for q in result[Domain.CONDITIONING])

    def test_injury_avoidance_phrase(self):
        constraint = Constraint(type="injury", detail="shoulder impingement")
        intake = _make_intake(constraints=[constraint])
        result = derive_queries(intake)
        assert any("avoiding shoulder impingement" in q for q in result[Domain.TRAINING])

    def test_dietary_constraint_in_nutrition(self):
        constraint = Constraint(type="dietary", detail="lactose intolerance")
        intake = _make_intake(constraints=[constraint])
        result = derive_queries(intake)
        assert any("lactose intolerance" in q for q in result[Domain.NUTRITION])

    def test_schedule_constraint_in_training(self):
        constraint = Constraint(type="schedule", detail="45-min cap")
        intake = _make_intake(constraints=[constraint])
        result = derive_queries(intake)
        assert any("45-min cap" in q for q in result[Domain.TRAINING])


class TestDomainCap:
    """Each domain must have ≤ 5 queries (PRD spec)."""

    def test_no_domain_exceeds_five_queries(self):
        constraints = [
            Constraint(type="injury", detail="rotator cuff"),
            Constraint(type="injury", detail="ankle sprain"),
            Constraint(type="schedule", detail="60-min cap"),
        ]
        intake = _make_intake(
            goals=["strength", "hypertrophy", "endurance"],
            constraints=constraints,
        )
        result = derive_queries(intake)
        for domain, queries in result.items():
            assert len(queries) <= 5, f"{domain} has {len(queries)} queries (max 5)"


class TestTotalQueryCount:
    """Total queries across all domains must be ≤ 30 (5 per domain × 6 domains)."""

    def test_total_queries_at_most_30(self):
        constraints = [
            Constraint(type="injury", detail="knee"),
            Constraint(type="dietary", detail="gluten"),
            Constraint(type="schedule", detail="30-min cap"),
        ]
        intake = _make_intake(
            goals=["strength", "hypertrophy", "endurance"],
            constraints=constraints,
        )
        result = derive_queries(intake)
        total = sum(len(qs) for qs in result.values())
        assert total <= 30, f"Total queries {total} exceeds 30"

    def test_single_goal_total_reasonable(self):
        intake = _make_intake(goals=["weight_loss"], training_status="recreational")
        result = derive_queries(intake)
        total = sum(len(qs) for qs in result.values())
        assert 6 <= total <= 30


class TestHIITConditioning:
    """HIIT should appear only for conditioning-appropriate goals."""

    def test_hiit_present_for_endurance(self):
        intake = _make_intake(goals=["endurance"])
        result = derive_queries(intake)
        assert any("HIIT" in q for q in result[Domain.CONDITIONING])

    def test_hiit_present_for_weight_loss(self):
        intake = _make_intake(goals=["weight_loss"])
        result = derive_queries(intake)
        assert any("HIIT" in q for q in result[Domain.CONDITIONING])

    def test_hiit_absent_for_strength_only(self):
        intake = _make_intake(goals=["strength"])
        result = derive_queries(intake)
        assert not any("HIIT" in q for q in result[Domain.CONDITIONING])


class TestTrainingStatusInQueries:
    """Training status must appear in nutrition and behavioral queries."""

    def test_training_status_in_nutrition(self):
        intake = _make_intake(training_status="competitive")
        result = derive_queries(intake)
        assert any("competitive" in q for q in result[Domain.NUTRITION])

    def test_training_status_in_behavioral(self):
        intake = _make_intake(training_status="untrained")
        result = derive_queries(intake)
        assert any("untrained" in q for q in result[Domain.BEHAVIORAL])

    def test_training_status_in_recovery(self):
        intake = _make_intake(training_status="recreational")
        result = derive_queries(intake)
        assert any("recreational" in q for q in result[Domain.RECOVERY])


class TestLongevityGoal:
    """Longevity goal must produce ≥1 TRAINING query containing 'longevity'."""

    def test_longevity_goal_produces_training_query(self):
        """Spec: every goal must produce ≥1 query in TRAINING domain."""
        intake = _make_intake(goals=["longevity"])
        queries = derive_queries(intake)
        assert len(queries[Domain.TRAINING]) >= 1
        assert any("longevity" in q.lower() for q in queries[Domain.TRAINING])


class TestReturnTypes:
    """Output must be dict[Domain, list[str]]."""

    def test_result_is_dict(self):
        intake = _make_intake()
        result = derive_queries(intake)
        assert isinstance(result, dict)

    def test_values_are_lists_of_strings(self):
        intake = _make_intake()
        result = derive_queries(intake)
        for domain, queries in result.items():
            assert isinstance(queries, list), f"{domain} value is not a list"
            for q in queries:
                assert isinstance(q, str), f"{domain} query {q!r} is not a str"


def _make_intake_with_regimen(regimen: str, **kwargs) -> ClientIntake:
    return ClientIntake(
        client_id="test-client",
        library_version="0.1.0",
        demographics=Demographics(age=30, sex="F", weight_kg=65.0, height_cm=170.0),
        training_status=kwargs.get("training_status", "trained"),
        goals=list(kwargs.get("goals", ("recomposition",))),
        current_regimen=regimen,
        constraints=list(kwargs.get("constraints", ())),
        contraindications=list(kwargs.get("contraindications", ())),
    )


def test_regimen_keywords_inject_queries():
    """Regimen keywords inject domain-scoped queries, respect the per-domain cap of 5,
    and produce zero regimen-derived queries when current_regimen is empty."""
    kettle_intake = _make_intake_with_regimen(
        "Mini-cut + kettlebell 4-week cycle Mon/Tue/Thu/Fri."
    )
    kettle_queries = derive_queries(kettle_intake)
    assert any("kettlebell" in q.lower() for q in kettle_queries[Domain.TRAINING])

    luteal_intake = _make_intake_with_regimen(
        "Cycle-aware: luteal phase +150-200 kcal mostly carb.",
        goals=["recomposition", "hypertrophy", "performance"],
    )
    luteal_queries = derive_queries(luteal_intake)
    assert any("luteal" in q.lower() for q in luteal_queries[Domain.NUTRITION])

    heavy_regimen = (
        "kettlebell circuits + Peloton + rower + boxing + Bulgarian split squat "
        "+ trap-bar deadlift + landmine press + front squat + SSB + HIIT + LISS "
        "+ treadmill + tempo + eccentric work + corrective drills + yoga"
    )
    heavy_constraints = [
        Constraint(type="injury", detail="left knee strain"),
        Constraint(type="schedule", detail="45-min cap"),
        Constraint(type="dietary", detail="lactose intolerance"),
    ]
    heavy_intake = _make_intake_with_regimen(
        heavy_regimen,
        goals=["weight_loss", "recomposition", "hypertrophy"],
        constraints=heavy_constraints,
    )
    heavy_queries = derive_queries(heavy_intake)
    for domain, queries in heavy_queries.items():
        assert len(queries) <= 5, f"{domain} has {len(queries)} queries (max 5)"

    empty_intake = _make_intake_with_regimen("")
    empty_queries = derive_queries(empty_intake)
    baseline_intake = ClientIntake(
        client_id="baseline-no-regimen",
        library_version="0.1.0",
        demographics=Demographics(age=30, sex="F", weight_kg=65.0, height_cm=170.0),
        training_status="trained",
        goals=["recomposition"],
    )
    baseline_queries = derive_queries(baseline_intake)
    for domain in Domain:
        assert empty_queries[domain] == baseline_queries[domain], (
            f"empty regimen produced extra {domain} queries: "
            f"{empty_queries[domain]} vs baseline {baseline_queries[domain]}"
        )
