"""Tests for LibraryVersionMismatch version guard — SC6."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from hcc_compiler.sp2.compile import LibraryVersionMismatch, compile
from hcc_compiler.sp2.intake import ClientIntake, Demographics
from hcc_compiler.sp2.pack import EvidencePack

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

QUERY_VEC = [1.0, 0.0, 0.0]
DB_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Fixture: minimal SQLite with meta.library_version = "0.1.0"
# ---------------------------------------------------------------------------

def _make_db(tmp_path: Path, db_version: str = DB_VERSION) -> Path:
    """Minimal fixture SQLite with meta.library_version set."""
    db = tmp_path / "guard.db"
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE atoms (
            id TEXT PRIMARY KEY, domain TEXT, tier TEXT, evidence_level TEXT, json TEXT
        );
        CREATE TABLE patterns (
            id TEXT PRIMARY KEY, domain TEXT, tier TEXT, json TEXT
        );
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE embeddings (
            record_id TEXT PRIMARY KEY,
            record_type TEXT NOT NULL,
            vector TEXT NOT NULL
        );
        CREATE INDEX idx_atoms_domain ON atoms(domain);
        CREATE INDEX idx_patterns_domain ON patterns(domain);
    """)
    con.execute("INSERT INTO meta VALUES ('library_version', ?)", (db_version,))
    con.commit()
    con.close()
    return db


def _make_intake(library_version: str) -> ClientIntake:
    return ClientIntake(
        client_id="guard-client",
        library_version=library_version,
        demographics=Demographics(age=28, sex="F", weight_kg=65.0, height_cm=170.0),
        training_status="recreational",
        goals=["endurance"],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_version_mismatch_raises(tmp_path: Path) -> None:
    """Mismatched library_version raises LibraryVersionMismatch (version_check=True)."""
    db = _make_db(tmp_path, db_version="0.1.0")
    intake = _make_intake(library_version="0.99.0")

    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        with pytest.raises(LibraryVersionMismatch) as exc_info:
            compile(intake, db, version_check=True)

    err = str(exc_info.value)
    assert "0.99.0" in err
    assert "0.1.0" in err


def test_version_mismatch_bypass_succeeds(tmp_path: Path) -> None:
    """version_check=False skips the guard and returns an EvidencePack."""
    db = _make_db(tmp_path, db_version="0.1.0")
    intake = _make_intake(library_version="0.99.0")

    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        pack = compile(intake, db, version_check=False)

    assert isinstance(pack, EvidencePack)


def test_version_match_no_raise(tmp_path: Path) -> None:
    """Matching version with version_check=True succeeds normally."""
    db = _make_db(tmp_path, db_version="0.1.0")
    intake = _make_intake(library_version="0.1.0")

    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        pack = compile(intake, db, version_check=True)

    assert isinstance(pack, EvidencePack)


def test_error_message_contains_both_versions(tmp_path: Path) -> None:
    """The exception message names both the intake version and the DB version."""
    db = _make_db(tmp_path, db_version="1.0.0")
    intake = _make_intake(library_version="2.0.0")

    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        with pytest.raises(LibraryVersionMismatch) as exc_info:
            compile(intake, db)

    msg = str(exc_info.value)
    assert "2.0.0" in msg
    assert "1.0.0" in msg


def test_version_mismatch_default_version_check_true(tmp_path: Path) -> None:
    """version_check defaults to True — mismatch still raises."""
    db = _make_db(tmp_path, db_version="0.1.0")
    intake = _make_intake(library_version="9.9.9")

    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        with pytest.raises(LibraryVersionMismatch):
            compile(intake, db)  # no explicit version_check
