"""Smoke test: compile Tori Shaw intake and assert core output invariants.

Runs directly against the local library.db; no HTTP server needed.
Set LIBRARY_DB_PATH to override the default (../../library.db relative to
the services/compiler-api/ working directory).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path wiring: allow running from repo root OR from services/compiler-api/
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent          # tests/
_SERVICE_ROOT = _HERE.parent                     # services/compiler-api/
_REPO_ROOT = _SERVICE_ROOT.parents[1]            # hcc-compiler/

# Ensure hcc_compiler package is importable.
sys.path.insert(0, str(_REPO_ROOT / "src"))
# Ensure compile_runner (sibling of this test's package) is importable.
sys.path.insert(0, str(_SERVICE_ROOT))

# Point at the development library.db unless overridden.
os.environ.setdefault("LIBRARY_DB_PATH", str(_REPO_ROOT / "library.db"))

# compile_runner imports are deferred until after path setup above.
from compile_runner import run_compile  # noqa: E402


INTAKE_YAML_PATH = _REPO_ROOT / "tests" / "fixtures" / "intakes" / "intake_test_v2_tori_shaw.yaml"


@pytest.fixture(scope="module")
def tori_result():
    """Compile Tori Shaw once for all assertions in this module."""
    import yaml

    raw = yaml.safe_load(INTAKE_YAML_PATH.read_text(encoding="utf-8"))
    return run_compile(raw, top_k=30, threshold=0.5)


# ---------------------------------------------------------------------------
# Structural assertions
# ---------------------------------------------------------------------------

def test_result_has_json_and_md_keys(tori_result):
    assert "json" in tori_result
    assert "md" in tori_result


def test_training_patterns_non_empty(tori_result):
    """Training domain must have at least one pattern."""
    training = tori_result["json"]["domain_recommendations"].get("training", {})
    patterns = training.get("patterns", [])
    assert len(patterns) >= 1, f"Expected >=1 training patterns, got {len(patterns)}"


def test_nutrition_atoms_non_empty(tori_result):
    """Nutrition domain must have at least one atom."""
    nutrition = tori_result["json"]["domain_recommendations"].get("nutrition", {})
    atoms = nutrition.get("atoms", [])
    assert len(atoms) >= 1, f"Expected >=1 nutrition atoms, got {len(atoms)}"


def test_markdown_contains_lumbar_fusion_annotation(tori_result):
    """Rendered markdown must contain the post-lumbar-fusion constraint annotation."""
    md = tori_result["md"]
    assert "Post-lumbar-fusion" in md, (
        "Expected 'Post-lumbar-fusion' constraint annotation in rendered markdown"
    )


# ---------------------------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------------------------

def test_compile_metadata_present(tori_result):
    meta = tori_result["json"].get("compile_metadata", {})
    assert meta.get("top_k_per_domain") == 30
    assert meta.get("applicability_threshold") == 0.5


def test_client_id_preserved(tori_result):
    assert tori_result["json"]["client_id"] == "test_v2_tori_shaw"
