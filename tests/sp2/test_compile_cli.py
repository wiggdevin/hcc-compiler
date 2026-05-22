"""Tests for scripts/compile_plan.py CLI — SC8."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from compile_plan import _cli_main

from hcc_compiler.sp2.pack import EvidencePack

# ---------------------------------------------------------------------------
# Constants (mirror test_compile.py)
# ---------------------------------------------------------------------------

QUERY_VEC = [1.0, 0.0, 0.0]
DB_VERSION = "0.1.0"

_DOMAIN_HEADINGS = [
    "## Nutrition",
    "## Training",
    "## Conditioning",
    "## Supplements",
    "## Recovery",
    "## Behavioral",
]


# ---------------------------------------------------------------------------
# Fixture helpers (duplicated from test_compile.py — no refactor to keep simple)
# ---------------------------------------------------------------------------

def _atom_json(atom_id: str, domain: str) -> str:
    return json.dumps({
        "id": atom_id,
        "domain": domain,
        "claim": f"Test claim for {domain}",
        "evidence_level": "L1",
        "citations": [
            {
                "id": "10.1234/test",
                "locator_quote": "Supporting passage.",
                "existence": "VERIFIED",
                "faithfulness": "VERIFIED",
                "cited_title": None,
            }
        ],
        "population_applicability": {
            "age": "adult",
            "sex": "any",
            "training_status": "any",
            "dose_magnitude": "as needed",
            "duration": "ongoing",
        },
        "effect": f"Positive effect in {domain}.",
        "contraindications": [],
        "tier": "high-impact",
        "approval": "Dev Wiggins 2026-05-22",
        "library_version": DB_VERSION,
        "last_reviewed": "2026-05-22",
        "expiry": "2027-05-22",
    })


def _pattern_json(pattern_id: str, domain: str, backing_atom_id: str) -> str:
    return json.dumps({
        "id": pattern_id,
        "domain": domain,
        "pattern": f"Test pattern for {domain}",
        "parameterization": "Apply as indicated.",
        "backing_atom_ids": [backing_atom_id],
        "falsification_signal": "No improvement after 4 weeks.",
        "safety_bounds": "Monitor weekly.",
        "applies_because": "Evidence supports it.",
        "doesnt_apply_if": "Severe contraindication present.",
        "tier": "high-impact",
        "approval": "Dev Wiggins 2026-05-22",
        "version": DB_VERSION,
    })


def _make_fixture_db(tmp_path: Path, db_version: str = DB_VERSION) -> Path:
    """Create a fixture SQLite with 1 atom per domain + 1 nutrition pattern."""
    db = tmp_path / "fixture.db"
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

    domain_atoms = [
        ("EA-NUT-0001", "nutrition"),
        ("EA-TRA-0001", "training"),
        ("EA-CON-0001", "conditioning"),
        ("EA-SUP-0001", "supplements"),
        ("EA-REC-0001", "recovery"),
        ("EA-BEH-0001", "behavioral"),
    ]
    for atom_id, domain in domain_atoms:
        con.execute(
            "INSERT INTO atoms VALUES (?,?,?,?,?)",
            (atom_id, domain, "high-impact", "L1", _atom_json(atom_id, domain)),
        )
        con.execute(
            "INSERT INTO embeddings VALUES (?,?,?)",
            (atom_id, "atom", json.dumps(QUERY_VEC)),
        )

    pat_id = "RP-NUT-test-pattern"
    con.execute(
        "INSERT INTO patterns VALUES (?,?,?,?)",
        (pat_id, "nutrition", "high-impact", _pattern_json(pat_id, "nutrition", "EA-NUT-0001")),
    )
    con.execute(
        "INSERT INTO embeddings VALUES (?,?,?)",
        (pat_id, "pattern", json.dumps(QUERY_VEC)),
    )

    con.execute("INSERT INTO meta VALUES ('library_version', ?)", (db_version,))
    con.commit()
    con.close()
    return db


def _make_intake_yaml(tmp_path: Path, library_version: str = DB_VERSION) -> Path:
    """Write a minimal intake YAML file and return its path."""
    content = f"""\
client_id: cli-test-client
library_version: "{library_version}"
demographics:
  age: 30
  sex: M
  weight_kg: 80.0
  height_cm: 180.0
training_status: trained
goals:
  - strength
current_regimen: "4x/week lifting"
constraints: []
contraindications: []
"""
    path = tmp_path / "intake.yaml"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Test 1: Happy path
# ---------------------------------------------------------------------------

def test_happy_path(tmp_path: Path) -> None:
    """CLI exits 0, both output files exist, JSON is a valid EvidencePack, MD has all 6 headings."""
    db = _make_fixture_db(tmp_path)
    intake_path = _make_intake_yaml(tmp_path)
    json_out = tmp_path / "out.json"
    md_out = tmp_path / "out.md"

    with patch("hcc_compiler.retrieve.embed", return_value=QUERY_VEC):
        rc = _cli_main([
            str(intake_path),
            "--db", str(db),
            "--out-json", str(json_out),
            "--out-md", str(md_out),
        ])

    assert rc == 0
    assert json_out.exists(), "JSON output file not created"
    assert md_out.exists(), "Markdown output file not created"

    # JSON parses to a valid EvidencePack
    pack = EvidencePack.model_validate_json(json_out.read_text(encoding="utf-8"))
    assert pack.client_id == "cli-test-client"

    # MD contains all 6 domain headings
    md_text = md_out.read_text(encoding="utf-8")
    for heading in _DOMAIN_HEADINGS:
        assert heading in md_text, f"Missing heading {heading!r} in markdown output"


# ---------------------------------------------------------------------------
# Test 2: Version mismatch → exit 1
# ---------------------------------------------------------------------------

def test_version_mismatch_exit_1(tmp_path: Path, capsys) -> None:
    """Intake with mismatched library_version exits 1, stderr contains 'version'."""
    db = _make_fixture_db(tmp_path, db_version="0.1.0")
    intake_path = _make_intake_yaml(tmp_path, library_version="0.99.0")

    with patch("hcc_compiler.retrieve.embed", return_value=QUERY_VEC):
        rc = _cli_main([
            str(intake_path),
            "--db", str(db),
            "--out-json", str(tmp_path / "out.json"),
            "--out-md", str(tmp_path / "out.md"),
        ])

    assert rc == 1
    captured = capsys.readouterr()
    assert "version" in captured.err.lower()


# ---------------------------------------------------------------------------
# Test 3: --no-version-check skips mismatch → exit 0
# ---------------------------------------------------------------------------

def test_no_version_check_skips_mismatch(tmp_path: Path) -> None:
    """--no-version-check allows mismatched version to succeed (exit 0)."""
    db = _make_fixture_db(tmp_path, db_version="0.1.0")
    intake_path = _make_intake_yaml(tmp_path, library_version="0.99.0")
    json_out = tmp_path / "out.json"
    md_out = tmp_path / "out.md"

    with patch("hcc_compiler.retrieve.embed", return_value=QUERY_VEC):
        rc = _cli_main([
            str(intake_path),
            "--db", str(db),
            "--out-json", str(json_out),
            "--out-md", str(md_out),
            "--no-version-check",
        ])

    assert rc == 0
    assert json_out.exists()
    assert md_out.exists()


# ---------------------------------------------------------------------------
# Test 4: Default output paths land at <intake_basename>.{json,md} in cwd
# ---------------------------------------------------------------------------

def test_defaults_land_in_cwd(tmp_path: Path, monkeypatch) -> None:
    """Without --out-json/--out-md, files land at <stem>.json + <stem>.md in cwd."""
    monkeypatch.chdir(tmp_path)

    db = _make_fixture_db(tmp_path)
    intake_path = _make_intake_yaml(tmp_path)  # stem = "intake"

    with patch("hcc_compiler.retrieve.embed", return_value=QUERY_VEC):
        rc = _cli_main([str(intake_path), "--db", str(db)])

    assert rc == 0
    assert (tmp_path / "intake.json").exists(), "Default JSON output not in cwd"
    assert (tmp_path / "intake.md").exists(), "Default MD output not in cwd"


# ---------------------------------------------------------------------------
# Test 5: Non-existent intake file → exit 2
# ---------------------------------------------------------------------------

def test_bad_intake_path_exit_2(tmp_path: Path) -> None:
    """Non-existent intake path exits with code 2."""
    db = _make_fixture_db(tmp_path)
    missing = tmp_path / "no_such_file.yaml"

    rc = _cli_main([
        str(missing),
        "--db", str(db),
        "--out-json", str(tmp_path / "out.json"),
        "--out-md", str(tmp_path / "out.md"),
    ])

    assert rc == 2
