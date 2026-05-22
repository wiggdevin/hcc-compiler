"""Tests for T3: embeddings table written by build_index."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch, call

import pytest
import yaml

from hcc_compiler.build_index import build_index
from tests.test_models_atom import VALID as ATOM
from tests.test_models_pattern import VALID as PATTERN


# ---------------------------------------------------------------------------
# Deterministic mock embed — offline, hash-based, returns reproducible floats
# ---------------------------------------------------------------------------

def _mock_embed(req):
    digest = hashlib.md5(req.text.encode()).hexdigest()
    # Turn 32 hex chars into 16 floats in [0.0, 1.0)
    return [int(digest[i : i + 2], 16) / 255.0 for i in range(0, 32, 2)]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _setup_atoms_only(root: Path):
    """Library with atoms but NO patterns directory."""
    (root / "atoms").mkdir(parents=True)
    (root / "VERSION").write_text("0.1.0\n")
    (root / "atoms" / "a.yaml").write_text(yaml.safe_dump(ATOM))


def _setup_atoms_and_patterns(root: Path):
    """Library with both atoms and patterns."""
    _setup_atoms_only(root)
    (root / "patterns").mkdir(parents=True)
    (root / "patterns" / "p.yaml").write_text(yaml.safe_dump(PATTERN))


# ---------------------------------------------------------------------------
# Tests: schema
# ---------------------------------------------------------------------------

def test_embeddings_table_exists(tmp_path):
    """build_index creates the embeddings table with the correct schema."""
    _setup_atoms_and_patterns(tmp_path)
    db = tmp_path / "library.db"
    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed):
        build_index(tmp_path, db)

    con = sqlite3.connect(db)
    try:
        rows = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings'"
        ).fetchall()
        assert rows, "embeddings table not found"

        # Verify columns
        cols = {r[1] for r in con.execute("PRAGMA table_info(embeddings)")}
        assert {"record_id", "record_type", "vector"}.issubset(cols)
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Tests: atom embeddings
# ---------------------------------------------------------------------------

def test_atom_embedding_row_exists(tmp_path):
    """Each atom gets an embeddings row with record_type='atom'."""
    _setup_atoms_and_patterns(tmp_path)
    db = tmp_path / "library.db"
    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed):
        build_index(tmp_path, db)

    con = sqlite3.connect(db)
    try:
        row = con.execute(
            "SELECT record_type, vector FROM embeddings WHERE record_id=?",
            (ATOM["id"],),
        ).fetchone()
        assert row is not None, f"No embeddings row for atom {ATOM['id']}"
        record_type, vector_json = row
        assert record_type == "atom"
        vec = json.loads(vector_json)
        assert isinstance(vec, list) and len(vec) > 0
        assert all(isinstance(v, float) for v in vec)
    finally:
        con.close()


def test_atom_embedding_uses_claim(tmp_path):
    """embed() is called with the atom's claim field."""
    _setup_atoms_and_patterns(tmp_path)
    db = tmp_path / "library.db"
    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed) as mock_fn:
        build_index(tmp_path, db)

    call_texts = [c.args[0].text for c in mock_fn.call_args_list]
    assert ATOM["claim"] in call_texts, (
        f"embed() was not called with claim text. Got calls: {call_texts}"
    )


# ---------------------------------------------------------------------------
# Tests: pattern embeddings
# ---------------------------------------------------------------------------

def test_pattern_embedding_row_exists(tmp_path):
    """Each pattern gets an embeddings row with record_type='pattern'."""
    _setup_atoms_and_patterns(tmp_path)
    db = tmp_path / "library.db"
    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed):
        build_index(tmp_path, db)

    con = sqlite3.connect(db)
    try:
        row = con.execute(
            "SELECT record_type, vector FROM embeddings WHERE record_id=?",
            (PATTERN["id"],),
        ).fetchone()
        assert row is not None, f"No embeddings row for pattern {PATTERN['id']}"
        record_type, vector_json = row
        assert record_type == "pattern"
        vec = json.loads(vector_json)
        assert isinstance(vec, list) and len(vec) > 0
        assert all(isinstance(v, float) for v in vec)
    finally:
        con.close()


def test_pattern_embedding_uses_pattern_plus_parameterization(tmp_path):
    """embed() is called with 'pattern + space + parameterization' for patterns."""
    _setup_atoms_and_patterns(tmp_path)
    db = tmp_path / "library.db"
    expected_text = f"{PATTERN['pattern']} {PATTERN['parameterization']}"
    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed) as mock_fn:
        build_index(tmp_path, db)

    call_texts = [c.args[0].text for c in mock_fn.call_args_list]
    assert expected_text in call_texts, (
        f"embed() not called with pattern+parameterization. Got: {call_texts}"
    )


# ---------------------------------------------------------------------------
# Tests: missing patterns directory (graceful skip)
# ---------------------------------------------------------------------------

def test_missing_patterns_dir_does_not_error(tmp_path):
    """build_index runs without error when patterns/ dir doesn't exist."""
    _setup_atoms_only(tmp_path)
    db = tmp_path / "library.db"
    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed):
        build_index(tmp_path, db)  # must not raise

    con = sqlite3.connect(db)
    try:
        count = con.execute(
            "SELECT COUNT(*) FROM embeddings WHERE record_type='pattern'"
        ).fetchone()[0]
        assert count == 0, "Expected zero pattern embeddings when patterns/ is absent"
    finally:
        con.close()


def test_missing_patterns_dir_still_embeds_atoms(tmp_path):
    """Atoms are still embedded when patterns/ dir doesn't exist."""
    _setup_atoms_only(tmp_path)
    db = tmp_path / "library.db"
    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed):
        build_index(tmp_path, db)

    con = sqlite3.connect(db)
    try:
        count = con.execute(
            "SELECT COUNT(*) FROM embeddings WHERE record_type='atom'"
        ).fetchone()[0]
        assert count == 1
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Tests: idempotency (INSERT OR REPLACE)
# ---------------------------------------------------------------------------

def test_rerun_does_not_duplicate_embeddings(tmp_path):
    """Running build_index twice yields exactly one embeddings row per record."""
    _setup_atoms_and_patterns(tmp_path)
    db = tmp_path / "library.db"
    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed):
        build_index(tmp_path, db)
        build_index(tmp_path, db)

    con = sqlite3.connect(db)
    try:
        count = con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        # 1 atom + 1 pattern = 2 rows
        assert count == 2
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Tests: existing tables unaffected
# ---------------------------------------------------------------------------

def test_existing_tables_still_populated(tmp_path):
    """atoms, patterns, meta tables are unaffected by the embeddings extension."""
    _setup_atoms_and_patterns(tmp_path)
    db = tmp_path / "library.db"
    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed):
        build_index(tmp_path, db)

    con = sqlite3.connect(db)
    try:
        assert con.execute("SELECT COUNT(*) FROM atoms").fetchone()[0] == 1
        assert con.execute("SELECT COUNT(*) FROM patterns").fetchone()[0] == 1
        assert con.execute(
            "SELECT value FROM meta WHERE key='library_version'"
        ).fetchone()[0] == "0.1.0"
    finally:
        con.close()
