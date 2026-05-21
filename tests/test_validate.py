# tests/test_validate.py
from pathlib import Path
import yaml
from hcc_compiler.validate import validate_library
from tests.test_models_atom import VALID as ATOM
from tests.test_models_pattern import VALID as PATTERN

def _setup(root: Path, atoms: list[dict], patterns: list[dict]):
    (root / "atoms").mkdir(parents=True)
    (root / "patterns").mkdir(parents=True)
    for i, a in enumerate(atoms):
        (root / "atoms" / f"a{i}.yaml").write_text(yaml.safe_dump(a))
    for i, p in enumerate(patterns):
        (root / "patterns" / f"p{i}.yaml").write_text(yaml.safe_dump(p))

def test_clean_library_has_no_problems(tmp_path):
    _setup(tmp_path, [ATOM], [PATTERN])
    assert validate_library(tmp_path) == []

def test_dangling_backing_ref_flagged(tmp_path):
    _setup(tmp_path, [ATOM], [{**PATTERN, "backing_atom_ids": ["EA-NUT-9999"]}])
    problems = validate_library(tmp_path)
    assert any("EA-NUT-9999" in p for p in problems)

def test_duplicate_atom_id_flagged(tmp_path):
    _setup(tmp_path, [ATOM, ATOM], [PATTERN])
    problems = validate_library(tmp_path)
    assert any("duplicate" in p.lower() for p in problems)

def test_high_impact_auto_approval_flagged(tmp_path):
    _setup(tmp_path, [{**ATOM, "approval": "auto"}], [PATTERN])
    problems = validate_library(tmp_path)
    assert any("high-impact" in p.lower() for p in problems)
