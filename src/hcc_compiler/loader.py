from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml
from pydantic import BaseModel, ValidationError


@dataclass
class LoadError:
    path: str
    message: str


def load_dir(directory: Path, model: type[BaseModel]):
    """Load + validate every *.yaml under `directory`. Returns (records, errors)."""
    records, errors = [], []
    for f in sorted(Path(directory).rglob("*.yaml")):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            records.append(model.model_validate(data))
        except (yaml.YAMLError, ValidationError) as e:
            errors.append(LoadError(str(f), str(e)))
    return records, errors
