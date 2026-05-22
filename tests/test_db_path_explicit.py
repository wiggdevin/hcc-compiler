"""Tests for T4-nit: db_path must be explicit (no cwd-relative default).

SC5: query() raises ValueError when called without db_path, and succeeds with
an explicit path.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from hcc_compiler.retrieve import query


def _make_minimal_db(path: Path) -> Path:
    """Create a minimal SQLite DB with required tables and one embedding."""
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE atoms (id TEXT PRIMARY KEY, domain TEXT, tier TEXT, evidence_level TEXT, json TEXT);
        CREATE TABLE patterns (id TEXT PRIMARY KEY, domain TEXT, tier TEXT, json TEXT);
        CREATE TABLE embeddings (
            record_id TEXT PRIMARY KEY,
            record_type TEXT NOT NULL,
            vector TEXT NOT NULL
        );
    """)
    con.execute(
        "INSERT INTO embeddings VALUES (?,?,?)",
        ("a1", "atom", json.dumps([1.0, 0.0, 0.0])),
    )
    con.commit()
    con.close()
    return path


def test_query_raises_without_db_path():
    """query() raises ValueError when db_path is not provided."""
    with pytest.raises(ValueError, match="db_path is required"):
        query("anything")


def test_query_succeeds_with_explicit_db_path(tmp_path):
    """query() succeeds when given an explicit db_path."""
    db = _make_minimal_db(tmp_path / "library.db")
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = [1.0, 0.0, 0.0]
        results = query("anything", k=5, db_path=db)
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0][0] == "a1"
