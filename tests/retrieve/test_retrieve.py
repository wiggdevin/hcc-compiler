"""Tests for retrieve.query() — SC4."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from hcc_compiler.retrieve import query

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(tmp_path: Path) -> Path:
    """Build a minimal SQLite fixture with:
    - 5 atoms: 2 nutrition, 2 training, 1 supplements
    - 2 patterns: 1 nutrition, 1 training
    Vectors are 3-dimensional and deterministic.
    """
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
    atoms = [
        ("a1", "nutrition",    "tier_1", "A", "{}"),
        ("a2", "nutrition",    "tier_2", "B", "{}"),
        ("a3", "training",     "tier_1", "A", "{}"),
        ("a4", "training",     "tier_2", "B", "{}"),
        ("a5", "supplements",  "tier_3", "C", "{}"),
    ]
    con.executemany("INSERT INTO atoms VALUES (?,?,?,?,?)", atoms)

    patterns = [
        ("p1", "nutrition", "tier_1", "{}"),
        ("p2", "training",  "tier_2", "{}"),
    ]
    con.executemany("INSERT INTO patterns VALUES (?,?,?,?)", patterns)

    # Vectors: a1 is closest to query [1,0,0]; the rest are clearly further.
    embeddings = [
        ("a1", "atom",    json.dumps([1.0, 0.0, 0.0])),   # sim=1.0 with query
        ("a2", "atom",    json.dumps([0.8, 0.2, 0.0])),   # sim~0.97
        ("a3", "atom",    json.dumps([0.6, 0.4, 0.0])),   # sim~0.83
        ("a4", "atom",    json.dumps([0.0, 1.0, 0.0])),   # sim=0.0
        ("a5", "atom",    json.dumps([-1.0, 0.0, 0.0])),  # sim=-1.0
        ("p1", "pattern", json.dumps([0.9, 0.1, 0.0])),   # sim~0.99
        ("p2", "pattern", json.dumps([0.0, 0.0, 1.0])),   # sim=0.0
    ]
    con.executemany("INSERT INTO embeddings VALUES (?,?,?)", embeddings)
    con.commit()
    con.close()
    return db


QUERY_VEC = [1.0, 0.0, 0.0]  # embed() always returns this in tests


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_basic_top_k(tmp_path):
    """query returns top-3 results, descending similarity, a1 first."""
    db = _make_db(tmp_path)
    # Patch the import-site binding: retrieve.py uses "from X import embed",
    # so this binding must be patched here. Patching the canonical definition
    # site (embed_client.embed) would NOT intercept retrieve.py's local name.
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        results = query("anything", k=3, db_path=db)

    assert len(results) == 3
    ids = [r[0] for r in results]
    sims = [r[1] for r in results]
    # a1 should be first (sim=1.0)
    assert ids[0] == "a1"
    # similarities descending
    assert sims[0] >= sims[1] >= sims[2]
    # all similarities are floats
    for _, sim in results:
        assert isinstance(sim, float)


def test_domain_filter_nutrition(tmp_path):
    """domain='nutrition' returns only nutrition atoms and nutrition patterns."""
    db = _make_db(tmp_path)
    # Patch the import-site binding: retrieve.py uses "from X import embed",
    # so this binding must be patched here. Patching the canonical definition
    # site (embed_client.embed) would NOT intercept retrieve.py's local name.
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        results = query("anything", k=10, domain="nutrition", db_path=db)

    ids = {r[0] for r in results}
    # nutrition atoms: a1, a2; nutrition pattern: p1
    assert ids == {"a1", "a2", "p1"}
    # training/supplements should be absent
    assert "a3" not in ids
    assert "a4" not in ids
    assert "a5" not in ids
    assert "p2" not in ids


def test_k_larger_than_results(tmp_path):
    """k > total records returns all sorted without error."""
    db = _make_db(tmp_path)
    # Patch the import-site binding: retrieve.py uses "from X import embed",
    # so this binding must be patched here. Patching the canonical definition
    # site (embed_client.embed) would NOT intercept retrieve.py's local name.
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        results = query("anything", k=1000, db_path=db)

    # 5 atoms + 2 patterns = 7 total
    assert len(results) == 7
    sims = [r[1] for r in results]
    assert sims == sorted(sims, reverse=True)


def test_empty_embeddings_table(tmp_path):
    """Empty embeddings table returns [] without error."""
    db = tmp_path / "empty.db"
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE atoms (id TEXT PRIMARY KEY, domain TEXT, tier TEXT, evidence_level TEXT, json TEXT);
        CREATE TABLE patterns (id TEXT PRIMARY KEY, domain TEXT, tier TEXT, json TEXT);
        CREATE TABLE embeddings (record_id TEXT PRIMARY KEY, record_type TEXT NOT NULL, vector TEXT NOT NULL);
    """)
    con.commit()
    con.close()

    # Patch the import-site binding: retrieve.py uses "from X import embed",
    # so this binding must be patched here. Patching the canonical definition
    # site (embed_client.embed) would NOT intercept retrieve.py's local name.
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        results = query("anything", db_path=db)

    assert results == []


def test_patterns_included_without_domain_filter(tmp_path):
    """Patterns appear in results when no domain filter is applied."""
    db = _make_db(tmp_path)
    # Patch the import-site binding: retrieve.py uses "from X import embed",
    # so this binding must be patched here. Patching the canonical definition
    # site (embed_client.embed) would NOT intercept retrieve.py's local name.
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        results = query("anything", k=10, db_path=db)

    ids = {r[0] for r in results}
    assert "p1" in ids
    assert "p2" in ids


def test_malformed_vector_skipped(tmp_path, caplog):
    """Rows with NULL or non-JSON vector are skipped; valid rows still returned."""
    db = tmp_path / "bad.db"
    con = sqlite3.connect(db)
    # Use nullable vector column to allow NULL insertion.
    con.executescript("""
        CREATE TABLE atoms (id TEXT PRIMARY KEY, domain TEXT, tier TEXT, evidence_level TEXT, json TEXT);
        CREATE TABLE patterns (id TEXT PRIMARY KEY, domain TEXT, tier TEXT, json TEXT);
        CREATE TABLE embeddings (record_id TEXT PRIMARY KEY, record_type TEXT NOT NULL, vector TEXT);
    """)
    valid_rows = [
        ("good1", "atom", json.dumps([1.0, 0.0, 0.0])),
        ("good2", "atom", json.dumps([0.5, 0.5, 0.0])),
        ("good3", "atom", json.dumps([0.0, 1.0, 0.0])),
    ]
    bad_rows = [
        ("bad_str", "atom", "not-json"),
        ("bad_null", "atom", None),
    ]
    con.executemany("INSERT INTO embeddings VALUES (?,?,?)", valid_rows + bad_rows)
    con.commit()
    con.close()

    import logging
    # Patch the import-site binding: retrieve.py uses "from X import embed",
    # so this binding must be patched here. Patching the canonical definition
    # site (embed_client.embed) would NOT intercept retrieve.py's local name.
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        with caplog.at_level(logging.WARNING, logger="hcc_compiler.retrieve"):
            results = query("anything", k=10, db_path=db)

    # Only valid rows returned.
    ids = {r[0] for r in results}
    assert ids == {"good1", "good2", "good3"}
    assert "bad_str" not in ids
    assert "bad_null" not in ids

    # Warnings emitted for both bad rows.
    warned_ids = [r.message for r in caplog.records]
    assert any("bad_str" in m for m in warned_ids)
    assert any("bad_null" in m for m in warned_ids)
