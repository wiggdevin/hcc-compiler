"""Tests for scripts/retrieve.py CLI — SC5."""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Path to the CLI script under test
_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "retrieve.py"

QUERY_VEC = [1.0, 0.0, 0.0]


def _make_db(tmp_path: Path) -> Path:
    """Build a minimal SQLite fixture with 3 atoms + 1 pattern."""
    db = tmp_path / "test.db"
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE atoms (id TEXT PRIMARY KEY, domain TEXT, tier TEXT, evidence_level TEXT, json TEXT);
        CREATE TABLE patterns (id TEXT PRIMARY KEY, domain TEXT, tier TEXT, json TEXT);
        CREATE TABLE embeddings (
            record_id TEXT PRIMARY KEY,
            record_type TEXT NOT NULL,
            vector TEXT NOT NULL
        );
    """)

    # 3 atoms: 2 nutrition, 1 training
    atoms = [
        ("a1", "nutrition", "tier_1", "A", json.dumps({"id": "a1", "claim": "Protein intake supports muscle synthesis in athletes"})),
        ("a2", "nutrition", "tier_2", "B", json.dumps({"id": "a2", "claim": "Omega-3 reduces inflammation markers significantly"})),
        ("a3", "training",  "tier_1", "A", json.dumps({"id": "a3", "claim": "Progressive overload is key to strength adaptation"})),
    ]
    con.executemany("INSERT INTO atoms VALUES (?,?,?,?,?)", atoms)

    # 1 pattern: nutrition
    patterns = [
        ("p1", "nutrition", "tier_1", json.dumps({"id": "p1", "pattern": "High protein diet paired with resistance training yields superior lean mass gains"})),
    ]
    con.executemany("INSERT INTO patterns VALUES (?,?,?,?)", patterns)

    # Embeddings: a1 closest to QUERY_VEC [1,0,0]
    embeddings = [
        ("a1", "atom",    json.dumps([1.0, 0.0, 0.0])),   # sim=1.0
        ("a2", "atom",    json.dumps([0.8, 0.2, 0.0])),   # sim~0.97
        ("a3", "atom",    json.dumps([0.6, 0.4, 0.0])),   # sim~0.83
        ("p1", "pattern", json.dumps([0.9, 0.1, 0.0])),   # sim~0.99
    ]
    con.executemany("INSERT INTO embeddings VALUES (?,?,?)", embeddings)
    con.commit()
    con.close()
    return db


def _run(args: list[str], env_patch: dict | None = None) -> subprocess.CompletedProcess:
    """Run the CLI script as a subprocess."""
    env = None
    if env_patch:
        import os
        env = {**os.environ, **env_patch}
    return subprocess.run(
        [sys.executable, str(_SCRIPT)] + args,
        capture_output=True,
        text=True,
        env=env,
    )


# ---------------------------------------------------------------------------
# Test 1: basic output format
# ---------------------------------------------------------------------------

def test_output_format(tmp_path):
    """Each result line is <id>\\t<sim:.4f>\\t<excerpt<=80chars>."""
    db = _make_db(tmp_path)
    result = _run(["protein", "--db", str(db), "--embed-mock"])
    assert result.returncode == 0, result.stderr
    lines = [l for l in result.stdout.strip().splitlines() if l]
    assert len(lines) > 0
    for line in lines:
        parts = line.split("\t")
        assert len(parts) == 3, f"Expected 3 tab-separated fields, got: {line!r}"
        record_id, sim_str, excerpt = parts
        # sim must parse as float
        sim = float(sim_str)
        # 4 decimal places
        assert "." in sim_str
        assert len(sim_str.split(".")[-1]) == 4, f"Expected 4 decimal places: {sim_str!r}"
        # excerpt must be <= 80 chars
        assert len(excerpt) <= 80, f"Excerpt too long ({len(excerpt)}): {excerpt!r}"


# ---------------------------------------------------------------------------
# Test 2: --domain filter
# ---------------------------------------------------------------------------

def test_domain_filter(tmp_path):
    """--domain nutrition returns only nutrition records (a1, a2, p1)."""
    db = _make_db(tmp_path)
    result = _run(["protein", "--domain", "nutrition", "--db", str(db), "--embed-mock"])
    assert result.returncode == 0, result.stderr
    lines = [l for l in result.stdout.strip().splitlines() if l]
    ids = [line.split("\t")[0] for line in lines]
    for rid in ids:
        assert rid in {"a1", "a2", "p1"}, f"Unexpected record in nutrition filter: {rid}"
    assert "a3" not in ids


# ---------------------------------------------------------------------------
# Test 3: --k limits results
# ---------------------------------------------------------------------------

def test_k_limits_results(tmp_path):
    """--k 2 returns exactly 2 results."""
    db = _make_db(tmp_path)
    result = _run(["protein", "--k", "2", "--db", str(db), "--embed-mock"])
    assert result.returncode == 0, result.stderr
    lines = [l for l in result.stdout.strip().splitlines() if l]
    assert len(lines) == 2


# ---------------------------------------------------------------------------
# Test 4: missing --db file exits non-zero
# ---------------------------------------------------------------------------

def test_missing_db_nonzero_exit(tmp_path):
    """--db pointing to nonexistent file exits with non-zero status."""
    missing_db = tmp_path / "nonexistent.db"
    result = _run(["protein", "--db", str(missing_db)])
    assert result.returncode != 0
