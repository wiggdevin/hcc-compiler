from __future__ import annotations
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, Field, field_validator

Sex = Literal["M", "F", "other"]
TrainingStatus = Literal["untrained", "recreational", "trained", "competitive"]
Goal = Literal[
    "hypertrophy", "strength", "endurance", "weight_loss",
    "recomposition", "performance", "longevity",
]


class Demographics(BaseModel):
    age: int = Field(ge=14, le=100)
    sex: Sex
    weight_kg: float = Field(gt=0, le=300)
    height_cm: float = Field(gt=0, le=250)


class Constraint(BaseModel):
    type: str  # e.g. "injury", "schedule", "equipment"
    detail: str


class ClientIntake(BaseModel):
    client_id: str
    library_version: str
    demographics: Demographics
    training_status: TrainingStatus
    goals: list[Goal] = Field(min_length=1)
    current_regimen: str = Field(max_length=2000, default="")
    constraints: list[Constraint] = Field(default_factory=list)
    contraindications: list[str] = Field(default_factory=list)


def load_intake(path: Path) -> ClientIntake:
    """Parse an intake YAML file into a validated ClientIntake."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return ClientIntake.model_validate(raw)
