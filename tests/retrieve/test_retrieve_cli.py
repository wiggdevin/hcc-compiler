"""Tests for scripts/retrieve.py CLI — SC5."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Import main() from the CLI script directly (no subprocess needed).
from retrieve import main as _cli_main

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


def _run_main(args: list[str], capsys) -> str:
    """Invoke CLI main() directly with patched argv and embed mock."""
    with patch("sys.argv", ["retrieve.py"] + args), \
         patch("hcc_compiler.retrieve.embed", return_value=QUERY_VEC):
        rc = _cli_main()
    assert rc == 0, f"CLI exited with {rc}"
    return capsys.readouterr().out


# ---------------------------------------------------------------------------
# Test 1: basic output format
# ---------------------------------------------------------------------------

def test_output_format(tmp_path, capsys):
    """Each result line is <id>\\t<sim:.4f>\\t<excerpt<=80chars>."""
    db = _make_db(tmp_path)
    stdout = _run_main(["protein", "--db", str(db)], capsys)
    lines = [l for l in stdout.strip().splitlines() if l]
    assert len(lines) > 0
    for line in lines:
        parts = line.split("\t")
        assert len(parts) == 3, f"Expected 3 tab-separated fields, got: {line!r}"
        record_id, sim_str, excerpt = parts
        # sim must parse as float
        float(sim_str)
        # 4 decimal places
        assert "." in sim_str
        assert len(sim_str.split(".")[-1]) == 4, f"Expected 4 decimal places: {sim_str!r}"
        # excerpt must be <= 80 chars
        assert len(excerpt) <= 80, f"Excerpt too long ({len(excerpt)}): {excerpt!r}"


# ---------------------------------------------------------------------------
# Test 2: --domain filter
# ---------------------------------------------------------------------------

def test_domain_filter(tmp_path, capsys):
    """--domain nutrition returns only nutrition records (a1, a2, p1)."""
    db = _make_db(tmp_path)
    stdout = _run_main(["protein", "--domain", "nutrition", "--db", str(db)], capsys)
    lines = [l for l in stdout.strip().splitlines() if l]
    ids = [line.split("\t")[0] for line in lines]
    for rid in ids:
        assert rid in {"a1", "a2", "p1"}, f"Unexpected record in nutrition filter: {rid}"
    assert "a3" not in ids


# ---------------------------------------------------------------------------
# Test 3: --k limits results
# ---------------------------------------------------------------------------

def test_k_limits_results(tmp_path, capsys):
    """--k 2 returns exactly 2 results."""
    db = _make_db(tmp_path)
    stdout = _run_main(["protein", "--k", "2", "--db", str(db)], capsys)
    lines = [l for l in stdout.strip().splitlines() if l]
    assert len(lines) == 2


# ---------------------------------------------------------------------------
# Test 4: missing --db file exits non-zero
# ---------------------------------------------------------------------------

def test_missing_db_nonzero_exit(tmp_path):
    """--db pointing to nonexistent file exits with non-zero status."""
    missing_db = tmp_path / "nonexistent.db"
    with patch("sys.argv", ["retrieve.py", "protein", "--db", str(missing_db)]):
        rc = _cli_main()
    assert rc != 0
