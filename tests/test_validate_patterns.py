# tests/test_validate_patterns.py
"""
Tests for the cross-record validator's pattern → atom reference check.
Covers SC9: validate_library flags dangling backing_atom_ids in patterns.
"""
from pathlib import Path
import yaml
import pytest
from hcc_compiler.validate import validate_library
from tests.test_models_atom import VALID as ATOM
from tests.test_models_pattern import VALID as PATTERN


def _write_atom(directory: Path, atom: dict, name: str = "atom.yaml"):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(yaml.safe_dump(atom))


def _write_pattern(directory: Path, pattern: dict, name: str = "pattern.yaml"):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(yaml.safe_dump(pattern))


# Test 1: pattern's backing_atom_ids resolves to an existing atom → passes
def test_valid_pattern_backing_atom_passes(tmp_path):
    _write_atom(tmp_path / "atoms", ATOM)
    _write_pattern(tmp_path / "patterns", PATTERN)
    problems = validate_library(tmp_path)
    assert problems == []


# Test 2: pattern with dangling backing_atom_id → flagged with id and ref
def test_dangling_backing_atom_id_flagged(tmp_path):
    dangling_id = "EA-NUT-9999"
    bad_pattern = {**PATTERN, "backing_atom_ids": [dangling_id]}
    _write_atom(tmp_path / "atoms", ATOM)
    _write_pattern(tmp_path / "patterns", bad_pattern)
    problems = validate_library(tmp_path)
    assert len(problems) == 1
    assert PATTERN["id"] in problems[0]
    assert dangling_id in problems[0]


# Test 3: no patterns directory at all → validator passes
def test_no_patterns_directory_passes(tmp_path):
    _write_atom(tmp_path / "atoms", ATOM)
    # patterns/ dir intentionally absent
    problems = validate_library(tmp_path)
    assert problems == []


# Test 4: pattern with mixed valid + dangling refs → only dangling ones flagged
def test_mixed_valid_and_dangling_refs(tmp_path):
    dangling_id = "EA-NUT-8888"
    valid_id = ATOM["id"]  # "EA-NUT-0001"
    mixed_pattern = {**PATTERN, "backing_atom_ids": [valid_id, dangling_id]}
    _write_atom(tmp_path / "atoms", ATOM)
    _write_pattern(tmp_path / "patterns", mixed_pattern)
    problems = validate_library(tmp_path)
    # Only the dangling ref should appear, not the valid one
    assert len(problems) == 1
    assert dangling_id in problems[0]
    assert valid_id not in problems[0]
