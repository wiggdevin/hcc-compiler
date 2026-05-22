"""Tests for ClientIntake Pydantic model and YAML loader (T1)."""
from __future__ import annotations
import pytest
import yaml
from pathlib import Path
from pydantic import ValidationError

from hcc_compiler.sp2.intake import (
    ClientIntake,
    Demographics,
    Constraint,
    load_intake,
)


# ── Fixtures ────────────────────────────────────────────────────────────────

def _valid_intake_data() -> dict:
    return {
        "client_id": "test-001",
        "library_version": "0.1.0",
        "demographics": {
            "age": 30,
            "sex": "M",
            "weight_kg": 80.0,
            "height_cm": 175.0,
        },
        "training_status": "trained",
        "goals": ["strength", "hypertrophy"],
        "current_regimen": "4x/week lifting",
        "constraints": [{"type": "equipment", "detail": "no barbell"}],
        "contraindications": ["peanut allergy"],
    }


# ── Valid intake parses ──────────────────────────────────────────────────────

def test_valid_intake_parses():
    data = _valid_intake_data()
    intake = ClientIntake.model_validate(data)
    assert intake.client_id == "test-001"
    assert intake.library_version == "0.1.0"
    assert intake.training_status == "trained"
    assert intake.goals == ["strength", "hypertrophy"]


def test_valid_intake_defaults():
    """current_regimen, constraints, contraindications are optional."""
    data = {
        "client_id": "min-client",
        "library_version": "0.1.0",
        "demographics": {"age": 25, "sex": "F", "weight_kg": 60.0, "height_cm": 165.0},
        "training_status": "recreational",
        "goals": ["endurance"],
    }
    intake = ClientIntake.model_validate(data)
    assert intake.current_regimen == ""
    assert intake.constraints == []
    assert intake.contraindications == []


def test_all_goal_literals_accepted():
    all_goals = [
        "hypertrophy", "strength", "endurance", "weight_loss",
        "recomposition", "performance", "longevity",
    ]
    for goal in all_goals:
        data = _valid_intake_data()
        data["goals"] = [goal]
        intake = ClientIntake.model_validate(data)
        assert intake.goals == [goal]


def test_all_training_status_literals_accepted():
    for status in ["untrained", "recreational", "trained", "competitive"]:
        data = _valid_intake_data()
        data["training_status"] = status
        intake = ClientIntake.model_validate(data)
        assert intake.training_status == status


# ── Demographics validation ─────────────────────────────────────────────────

def test_age_below_14_rejected():
    data = _valid_intake_data()
    data["demographics"]["age"] = 5
    with pytest.raises(ValidationError):
        ClientIntake.model_validate(data)


def test_age_above_100_rejected():
    data = _valid_intake_data()
    data["demographics"]["age"] = 101
    with pytest.raises(ValidationError):
        ClientIntake.model_validate(data)


def test_age_boundary_14_accepted():
    data = _valid_intake_data()
    data["demographics"]["age"] = 14
    intake = ClientIntake.model_validate(data)
    assert intake.demographics.age == 14


def test_age_boundary_100_accepted():
    data = _valid_intake_data()
    data["demographics"]["age"] = 100
    intake = ClientIntake.model_validate(data)
    assert intake.demographics.age == 100


def test_invalid_sex_rejected():
    data = _valid_intake_data()
    data["demographics"]["sex"] = "X"
    with pytest.raises(ValidationError):
        ClientIntake.model_validate(data)


def test_sex_other_accepted():
    data = _valid_intake_data()
    data["demographics"]["sex"] = "other"
    intake = ClientIntake.model_validate(data)
    assert intake.demographics.sex == "other"


def test_negative_weight_rejected():
    data = _valid_intake_data()
    data["demographics"]["weight_kg"] = -10.0
    with pytest.raises(ValidationError):
        ClientIntake.model_validate(data)


def test_zero_weight_rejected():
    data = _valid_intake_data()
    data["demographics"]["weight_kg"] = 0.0
    with pytest.raises(ValidationError):
        ClientIntake.model_validate(data)


def test_negative_height_rejected():
    data = _valid_intake_data()
    data["demographics"]["height_cm"] = -1.0
    with pytest.raises(ValidationError):
        ClientIntake.model_validate(data)


# ── Goals validation ─────────────────────────────────────────────────────────

def test_missing_goals_rejected():
    data = _valid_intake_data()
    data["goals"] = []
    with pytest.raises(ValidationError):
        ClientIntake.model_validate(data)


def test_invalid_goal_rejected():
    data = _valid_intake_data()
    data["goals"] = ["bulk"]  # not a valid Goal literal
    with pytest.raises(ValidationError):
        ClientIntake.model_validate(data)


# ── Contraindications optional ───────────────────────────────────────────────

def test_contraindications_optional():
    data = _valid_intake_data()
    del data["contraindications"]
    intake = ClientIntake.model_validate(data)
    assert intake.contraindications == []


def test_contraindications_list_accepted():
    data = _valid_intake_data()
    data["contraindications"] = ["renal insufficiency", "CKD stage 2"]
    intake = ClientIntake.model_validate(data)
    assert len(intake.contraindications) == 2


# ── Constraint model ─────────────────────────────────────────────────────────

def test_constraint_parses():
    c = Constraint.model_validate({"type": "injury", "detail": "left knee"})
    assert c.type == "injury"
    assert c.detail == "left knee"


# ── YAML loader round-trip ───────────────────────────────────────────────────

def test_yaml_loader_round_trip(tmp_path: Path):
    data = _valid_intake_data()
    yaml_file = tmp_path / "intake.yaml"
    yaml_file.write_text(yaml.dump(data), encoding="utf-8")

    intake = load_intake(yaml_file)
    assert intake.client_id == data["client_id"]
    assert intake.library_version == data["library_version"]
    assert intake.demographics.age == data["demographics"]["age"]
    assert intake.demographics.sex == data["demographics"]["sex"]
    assert intake.goals == data["goals"]
    assert intake.training_status == data["training_status"]


def test_yaml_loader_invalid_raises(tmp_path: Path):
    """A YAML with invalid demographics should raise ValidationError."""
    data = _valid_intake_data()
    data["demographics"]["age"] = 5  # too young
    yaml_file = tmp_path / "bad_intake.yaml"
    yaml_file.write_text(yaml.dump(data), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_intake(yaml_file)
