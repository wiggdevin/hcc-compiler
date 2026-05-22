"""Tests for scripts/curation/derive_patterns.py — SC8 TDD suite."""
from __future__ import annotations

import math
import sqlite3
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

from hcc_compiler.models import (
    Citation,
    Domain,
    EvidenceAtom,
    EvidenceLevel,
    PopulationApplicability,
    RecommendationPattern,
    Tier,
)


def _unit(v: list[float]) -> list[float]:
    mag = math.sqrt(sum(x * x for x in v))
    return [x / mag for x in v]


def _make_atom(atom_id: str, domain: Domain, idx: int) -> EvidenceAtom:
    return EvidenceAtom(
        id=atom_id,
        domain=domain,
        claim=f"Claim {idx}",
        evidence_level=EvidenceLevel.L2,
        citations=[Citation(
            id=f"10.1000/test{idx}",
            locator_quote="test quote",
            existence="VERIFIED",
            faithfulness="VERIFIED",
            cited_title="Test Study",
        )],
        population_applicability=PopulationApplicability(
            age="adults",
            sex="all",
            training_status="active",
            dose_magnitude="moderate",
            duration="12 weeks",
        ),
        effect=f"Effect {idx}",
        contraindications=[],
        tier=Tier.ROUTINE,
        approval="approved",
        library_version="0.1.0",
        last_reviewed=date(2026, 1, 1),
        expiry=date(2027, 1, 1),
    )


def _make_pattern(pat_id: str, domain: Domain, atom_ids: list[str]) -> RecommendationPattern:
    return RecommendationPattern(
        id=pat_id,
        domain=domain,
        pattern="Test pattern statement.",
        parameterization="No adjustment.",
        backing_atom_ids=atom_ids,
        falsification_signal="No effect after 8 weeks.",
        safety_bounds="Standard bounds apply.",
        applies_because="Multiple trials confirm.",
        doesnt_apply_if="Contraindication present.",
        tier=Tier.ROUTINE,
        approval="auto",
        version="0.1.0",
    )


# Deterministic close vectors (cosine distance ~ 0, within 0.30)
_CLOSE_A = _unit([1.0, 0.01, 0.0, 0.0])
_CLOSE_B = _unit([1.0, 0.02, 0.0, 0.0])
_CLOSE_C = _unit([1.0, 0.03, 0.0, 0.0])

# Deterministic close vectors for training domain
_CLOSE_D = _unit([0.0, 0.0, 1.0, 0.01])
_CLOSE_E = _unit([0.0, 0.0, 1.0, 0.02])
_CLOSE_F = _unit([0.0, 0.0, 1.0, 0.03])

# Weak cluster: all pairs dist=0.25 < 0.30 (cluster together), but mean sim=0.75 < 0.80.
# Derived from Cholesky of G=[[1,0.75,0.75],[0.75,1,0.75],[0.75,0.75,1]].
_WEAK_A = [1.0, 0.0, 0.0]
_WEAK_B = [0.75, 0.6614378277661477, 0.0]
_WEAK_C = [0.75, 0.2834733547569204, 0.5976143046671968]


@pytest.fixture
def lib_db(tmp_path):
    """Create a tmp library with 6 atoms across 2 domains + SQLite with embeddings."""
    lib = tmp_path / "library"

    # Nutrition atoms
    nut_dir = lib / "atoms" / "nutrition"
    nut_dir.mkdir(parents=True)
    nut_atoms = [
        _make_atom("EA-NUT-0001", Domain.NUTRITION, 1),
        _make_atom("EA-NUT-0002", Domain.NUTRITION, 2),
        _make_atom("EA-NUT-0003", Domain.NUTRITION, 3),
    ]
    nut_vecs = [_CLOSE_A, _CLOSE_B, _CLOSE_C]
    for atom, vec in zip(nut_atoms, nut_vecs):
        (nut_dir / f"{atom.id}.yaml").write_text(
            yaml.safe_dump(atom.model_dump(mode="json"), sort_keys=False)
        )

    # Training atoms
    tra_dir = lib / "atoms" / "training"
    tra_dir.mkdir(parents=True)
    tra_atoms = [
        _make_atom("EA-TRA-0001", Domain.TRAINING, 4),
        _make_atom("EA-TRA-0002", Domain.TRAINING, 5),
        _make_atom("EA-TRA-0003", Domain.TRAINING, 6),
    ]
    tra_vecs = [_CLOSE_D, _CLOSE_E, _CLOSE_F]
    for atom, vec in zip(tra_atoms, tra_vecs):
        (tra_dir / f"{atom.id}.yaml").write_text(
            yaml.safe_dump(atom.model_dump(mode="json"), sort_keys=False)
        )

    # Build SQLite DB with embeddings
    db_path = tmp_path / "library.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE embeddings (record_id TEXT PRIMARY KEY, vector TEXT)"
    )
    import json as _json
    all_atoms = list(zip(nut_atoms, nut_vecs)) + list(zip(tra_atoms, tra_vecs))
    for atom, vec in all_atoms:
        conn.execute(
            "INSERT INTO embeddings (record_id, vector) VALUES (?, ?)",
            (atom.id, _json.dumps(vec)),
        )
    conn.commit()
    conn.close()

    return lib, db_path, nut_atoms, tra_atoms


def _run_script(args: list[str], mock_pattern_factory):
    """Import and run derive_patterns.main() with given argv, mocking derive_pattern."""
    script_path = (
        Path(__file__).resolve().parents[2] / "scripts" / "curation" / "derive_patterns.py"
    )
    import importlib.util

    # Patch the source symbol BEFORE exec_module so the module's import binds the mock.
    with patch("hcc_compiler.patterns.derive.derive_pattern", side_effect=mock_pattern_factory):
        spec = importlib.util.spec_from_file_location("derive_patterns", script_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        saved_argv = sys.argv[:]
        try:
            sys.argv = ["derive_patterns.py"] + args
            return mod.main()
        finally:
            sys.argv = saved_argv


# ---------------------------------------------------------------------------
# Test 1: strong cluster → admitted to library/patterns/<domain>/<id>.yaml
# ---------------------------------------------------------------------------

def test_strong_cluster_admitted(lib_db, tmp_path):
    lib, db_path, nut_atoms, tra_atoms = lib_db

    nut_pattern = _make_pattern("RP-NUT-protein-synthesis", Domain.NUTRITION, [a.id for a in nut_atoms])
    tra_pattern = _make_pattern("RP-TRA-volume-load", Domain.TRAINING, [a.id for a in tra_atoms])
    call_count = [0]

    def fake_derive(atoms):
        call_count[0] += 1
        if atoms[0].domain == Domain.NUTRITION:
            return nut_pattern
        return tra_pattern

    tally = _run_script(
        ["--library", str(lib), "--db", str(db_path), "--auto-admit-threshold", "0.80"],
        fake_derive,
    )

    # Both patterns should be admitted (mean sim is very high for near-identical vectors)
    assert (lib / "patterns" / "nutrition" / "RP-NUT-protein-synthesis.yaml").exists(), \
        "Nutrition pattern should be admitted to library/patterns/nutrition/"
    assert (lib / "patterns" / "training" / "RP-TRA-volume-load.yaml").exists(), \
        "Training pattern should be admitted to library/patterns/training/"

    # Should NOT be in queue
    assert not (lib / "queue" / "RP-NUT-protein-synthesis.yaml").exists()
    assert not (lib / "queue" / "RP-TRA-volume-load.yaml").exists()

    assert tally["admitted"] == 2
    assert tally["queued"] == 0
    assert tally["skipped-too-small"] == 0
    assert tally["skipped-existing"] == 0


# ---------------------------------------------------------------------------
# Test 2: weak cluster (mean sim < 0.80) → queued to library/queue/<id>.yaml
# ---------------------------------------------------------------------------

def test_weak_cluster_queued(tmp_path):
    import json as _json

    lib = tmp_path / "library"
    nut_dir = lib / "atoms" / "nutrition"
    nut_dir.mkdir(parents=True)

    weak_atoms = [
        _make_atom("EA-NUT-0011", Domain.NUTRITION, 11),
        _make_atom("EA-NUT-0012", Domain.NUTRITION, 12),
        _make_atom("EA-NUT-0013", Domain.NUTRITION, 13),
    ]
    weak_vecs = [_WEAK_A, _WEAK_B, _WEAK_C]
    for atom, vec in zip(weak_atoms, weak_vecs):
        (nut_dir / f"{atom.id}.yaml").write_text(
            yaml.safe_dump(atom.model_dump(mode="json"), sort_keys=False)
        )

    db_path = tmp_path / "library.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE embeddings (record_id TEXT PRIMARY KEY, vector TEXT)")
    for atom, vec in zip(weak_atoms, weak_vecs):
        conn.execute(
            "INSERT INTO embeddings (record_id, vector) VALUES (?, ?)",
            (atom.id, _json.dumps(vec)),
        )
    conn.commit()
    conn.close()

    weak_pattern = _make_pattern("RP-NUT-weak-pattern", Domain.NUTRITION, [a.id for a in weak_atoms])

    def fake_derive(atoms):
        return weak_pattern

    tally = _run_script(
        ["--library", str(lib), "--db", str(db_path), "--auto-admit-threshold", "0.80"],
        fake_derive,
    )

    assert (lib / "queue" / "RP-NUT-weak-pattern.yaml").exists(), \
        "Weak cluster pattern should land in library/queue/"
    assert not (lib / "patterns" / "nutrition" / "RP-NUT-weak-pattern.yaml").exists()

    assert tally["queued"] == 1
    assert tally["admitted"] == 0


# ---------------------------------------------------------------------------
# Test 3: cluster smaller than min-atoms → skipped, no file written
# ---------------------------------------------------------------------------

def test_small_cluster_skipped(tmp_path):
    import json as _json

    lib = tmp_path / "library"
    nut_dir = lib / "atoms" / "nutrition"
    nut_dir.mkdir(parents=True)

    # Only 2 atoms that cluster together — below default min-atoms=3
    small_atoms = [
        _make_atom("EA-NUT-0021", Domain.NUTRITION, 21),
        _make_atom("EA-NUT-0022", Domain.NUTRITION, 22),
    ]
    close_vecs = [_CLOSE_A, _CLOSE_B]
    for atom, vec in zip(small_atoms, close_vecs):
        (nut_dir / f"{atom.id}.yaml").write_text(
            yaml.safe_dump(atom.model_dump(mode="json"), sort_keys=False)
        )

    db_path = tmp_path / "library.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE embeddings (record_id TEXT PRIMARY KEY, vector TEXT)")
    for atom, vec in zip(small_atoms, close_vecs):
        conn.execute(
            "INSERT INTO embeddings (record_id, vector) VALUES (?, ?)",
            (atom.id, _json.dumps(vec)),
        )
    conn.commit()
    conn.close()

    call_count = [0]

    def fake_derive(atoms):
        call_count[0] += 1
        return _make_pattern("RP-NUT-should-not-exist", Domain.NUTRITION, [a.id for a in atoms])

    tally = _run_script(
        ["--library", str(lib), "--db", str(db_path), "--min-atoms", "3"],
        fake_derive,
    )

    # derive_pattern should NOT have been called
    assert call_count[0] == 0, "derive_pattern must not be called for small clusters"
    # No files written
    assert not (lib / "patterns").exists() or not any((lib / "patterns").rglob("*.yaml"))
    assert not (lib / "queue").exists() or not any((lib / "queue").rglob("*.yaml"))

    assert tally["skipped-too-small"] >= 1
    assert tally["admitted"] == 0
    assert tally["queued"] == 0


# ---------------------------------------------------------------------------
# Test 4: idempotency — second run produces zero new files
# ---------------------------------------------------------------------------

def test_idempotency(lib_db, tmp_path):
    lib, db_path, nut_atoms, tra_atoms = lib_db

    nut_pattern = _make_pattern("RP-NUT-protein-synthesis", Domain.NUTRITION, [a.id for a in nut_atoms])
    tra_pattern = _make_pattern("RP-TRA-volume-load", Domain.TRAINING, [a.id for a in tra_atoms])

    def fake_derive(atoms):
        if atoms[0].domain == Domain.NUTRITION:
            return nut_pattern
        return tra_pattern

    # Run 1
    tally1 = _run_script(
        ["--library", str(lib), "--db", str(db_path), "--auto-admit-threshold", "0.80"],
        fake_derive,
    )
    assert tally1["admitted"] == 2

    # Run 2 — everything should skip
    tally2 = _run_script(
        ["--library", str(lib), "--db", str(db_path), "--auto-admit-threshold", "0.80"],
        fake_derive,
    )
    assert tally2["admitted"] == 0
    assert tally2["queued"] == 0
    assert tally2["skipped-existing"] == 2


# ---------------------------------------------------------------------------
# Test 5: pattern id already in library/queue/ → also skipped (cross-dest)
# ---------------------------------------------------------------------------

def test_cross_destination_collision(lib_db, tmp_path):
    lib, db_path, nut_atoms, tra_atoms = lib_db

    nut_pattern = _make_pattern("RP-NUT-protein-synthesis", Domain.NUTRITION, [a.id for a in nut_atoms])
    tra_pattern = _make_pattern("RP-TRA-volume-load", Domain.TRAINING, [a.id for a in tra_atoms])

    def fake_derive(atoms):
        if atoms[0].domain == Domain.NUTRITION:
            return nut_pattern
        return tra_pattern

    # Pre-plant the nutrition pattern in queue/ (simulating it landed there previously)
    queue_dir = lib / "queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    (queue_dir / "RP-NUT-protein-synthesis.yaml").write_text(
        yaml.safe_dump(nut_pattern.model_dump(mode="json"), sort_keys=False)
    )

    tally = _run_script(
        ["--library", str(lib), "--db", str(db_path), "--auto-admit-threshold", "0.80"],
        fake_derive,
    )

    # Nutrition pattern was in queue → skip; training pattern is new → admit
    assert tally["skipped-existing"] >= 1
    assert tally["admitted"] == 1
    # The pre-planted queue file should NOT have been overwritten into patterns/
    assert not (lib / "patterns" / "nutrition" / "RP-NUT-protein-synthesis.yaml").exists()
