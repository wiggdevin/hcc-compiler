"""Tests for compile() orchestrator — SC5."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from hcc_compiler.models import Domain
from hcc_compiler.sp2.compile import LibraryVersionMismatch, compile
from hcc_compiler.sp2.intake import ClientIntake, Demographics
from hcc_compiler.sp2.pack import EvidencePack

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

QUERY_VEC = [1.0, 0.0, 0.0]  # fixed vector returned by mocked embed()
DB_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Fixture: build a tiny SQLite with 1 atom per domain + 1 pattern
# ---------------------------------------------------------------------------

def _atom_json(atom_id: str, domain: str) -> str:
    """Return a minimal valid EvidenceAtom JSON blob for the given domain/id."""
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
    """Return a minimal valid RecommendationPattern JSON blob."""
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


def _make_fixture_db(tmp_path: Path) -> Path:
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

    # 1 atom per domain (6 total)
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

    # 1 pattern in nutrition domain
    pat_id = "RP-NUT-test-pattern"
    con.execute(
        "INSERT INTO patterns VALUES (?,?,?,?)",
        (pat_id, "nutrition", "high-impact", _pattern_json(pat_id, "nutrition", "EA-NUT-0001")),
    )
    con.execute(
        "INSERT INTO embeddings VALUES (?,?,?)",
        (pat_id, "pattern", json.dumps(QUERY_VEC)),
    )

    con.execute("INSERT INTO meta VALUES ('library_version', ?)", (DB_VERSION,))
    con.commit()
    con.close()
    return db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_intake(library_version: str = DB_VERSION) -> ClientIntake:
    return ClientIntake(
        client_id="test-client-001",
        library_version=library_version,
        demographics=Demographics(age=30, sex="M", weight_kg=80.0, height_cm=180.0),
        training_status="trained",
        goals=["strength"],
        current_regimen="4x/week lifting",
        constraints=[],
        contraindications=[],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_compile_returns_evidence_pack(tmp_path: Path) -> None:
    """compile() returns an EvidencePack instance."""
    db = _make_fixture_db(tmp_path)
    intake = _make_intake()
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        pack = compile(intake, db)
    assert isinstance(pack, EvidencePack)


def test_compile_has_all_six_domain_keys(tmp_path: Path) -> None:
    """compile() always returns all 6 domain keys, even if blocks are empty."""
    db = _make_fixture_db(tmp_path)
    intake = _make_intake()
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        pack = compile(intake, db)
    assert set(pack.domain_recommendations.keys()) == set(Domain)


def test_compile_at_least_one_non_empty_block(tmp_path: Path) -> None:
    """At least one domain block has atoms or patterns."""
    db = _make_fixture_db(tmp_path)
    intake = _make_intake()
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        pack = compile(intake, db)
    blocks = pack.domain_recommendations.values()
    non_empty = [b for b in blocks if b.atoms or b.patterns]
    assert len(non_empty) >= 1


def test_compile_metadata_queries_issued_has_six_entries(tmp_path: Path) -> None:
    """compile_metadata.queries_issued has 6 entries — one per domain."""
    db = _make_fixture_db(tmp_path)
    intake = _make_intake()
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        pack = compile(intake, db)
    assert len(pack.compile_metadata.queries_issued) == 6


def test_compile_metadata_fields_filled(tmp_path: Path) -> None:
    """compile_metadata has expected values matching compile() arguments."""
    db = _make_fixture_db(tmp_path)
    intake = _make_intake()
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        pack = compile(intake, db, top_k=3, applicability_threshold=0.3)
    assert pack.compile_metadata.top_k_per_domain == 3
    assert pack.compile_metadata.applicability_threshold == 0.3


def test_compile_compiled_at_is_recent(tmp_path: Path) -> None:
    """compiled_at timestamp is within seconds of now."""
    db = _make_fixture_db(tmp_path)
    intake = _make_intake()
    before = datetime.now(timezone.utc)
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        pack = compile(intake, db)
    after = datetime.now(timezone.utc)
    assert before <= pack.compiled_at <= after


def test_compile_library_version_from_db(tmp_path: Path) -> None:
    """EvidencePack.library_version reflects the DB meta.library_version."""
    db = _make_fixture_db(tmp_path)
    intake = _make_intake()
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        pack = compile(intake, db)
    assert pack.library_version == DB_VERSION


def test_compile_client_id_propagated(tmp_path: Path) -> None:
    """EvidencePack.client_id matches intake.client_id."""
    db = _make_fixture_db(tmp_path)
    intake = _make_intake()
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        pack = compile(intake, db)
    assert pack.client_id == "test-client-001"


def test_compile_applicability_threshold_filters(tmp_path: Path) -> None:
    """Atoms with pop_score below threshold are excluded from blocks."""
    db = _make_fixture_db(tmp_path)
    # All fixture atoms have "any" population → score ~1.0.
    # Use threshold=1.1 to exclude everything.
    intake = _make_intake()
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        pack = compile(intake, db, applicability_threshold=1.1)
    total_atoms = sum(len(b.atoms) for b in pack.domain_recommendations.values())
    assert total_atoms == 0


def test_compile_nutrition_block_has_pattern(tmp_path: Path) -> None:
    """The nutrition block contains the fixture pattern."""
    db = _make_fixture_db(tmp_path)
    intake = _make_intake()
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        pack = compile(intake, db)
    nut_block = pack.domain_recommendations[Domain.NUTRITION]
    pattern_ids = [p.pattern_id for p in nut_block.patterns]
    assert "RP-NUT-test-pattern" in pattern_ids


def _atom_json_with_contraindication(atom_id: str, domain: str, contraindication: str) -> str:
    """Variant of _atom_json that carries a contraindication string."""
    return json.dumps({
        "id": atom_id,
        "domain": domain,
        "claim": f"Risky claim for {domain}",
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
        "effect": f"Has caveats in {domain}.",
        "contraindications": [contraindication],
        "tier": "high-impact",
        "approval": "Dev Wiggins 2026-05-22",
        "library_version": DB_VERSION,
        "last_reviewed": "2026-05-22",
        "expiry": "2027-05-22",
    })


def test_preemptive_contraindication_surfaces_when_atom_not_in_topk(tmp_path: Path) -> None:
    """An atom with a matching contraindication surfaces in preemptive_contraindications
    even when retrieval does NOT pull it into any domain's top-k.

    The renal atom has no row in the embeddings table — retrieve.query() therefore
    never sees it — but the library-wide preemptive scan still discovers it via
    atoms_by_id iteration.
    """
    db = tmp_path / "preemptive.db"
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
    """)
    # One contraindicated atom — NOT in embeddings table.
    con.execute(
        "INSERT INTO atoms VALUES (?,?,?,?,?)",
        (
            "EA-NUT-9999",
            "nutrition",
            "high-impact",
            "L1",
            _atom_json_with_contraindication(
                "EA-NUT-9999", "nutrition", "CKD or other renal contraindication"
            ),
        ),
    )
    # One unrelated atom WITH an embedding so retrieve.query() has something to return.
    con.execute(
        "INSERT INTO atoms VALUES (?,?,?,?,?)",
        ("EA-TRA-0001", "training", "high-impact", "L1", _atom_json("EA-TRA-0001", "training")),
    )
    con.execute(
        "INSERT INTO embeddings VALUES (?,?,?)",
        ("EA-TRA-0001", "atom", json.dumps(QUERY_VEC)),
    )
    con.execute("INSERT INTO meta VALUES ('library_version', ?)", (DB_VERSION,))
    con.commit()
    con.close()

    intake = ClientIntake(
        client_id="renal-client",
        library_version=DB_VERSION,
        demographics=Demographics(age=45, sex="M", weight_kg=92.0, height_cm=182.0),
        training_status="trained",
        goals=["strength"],
        current_regimen="lifting",
        constraints=[],
        contraindications=["renal insufficiency (CKD stage 2)"],
    )

    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        pack = compile(intake, db)

    preemptive = pack.compile_metadata.preemptive_contraindications
    assert any(hit.record_id == "EA-NUT-9999" for hit in preemptive), (
        f"EA-NUT-9999 missing from preemptive hits: {[h.record_id for h in preemptive]}"
    )
    assert all(hit.record_type == "atom" for hit in preemptive if hit.record_id == "EA-NUT-9999")
    # The contraindicated atom must NOT be in any domain block (no embedding → no retrieval).
    for block in pack.domain_recommendations.values():
        assert all(a.atom_id != "EA-NUT-9999" for a in block.atoms)


def test_preemptive_skipped_when_intake_has_no_restrictions(tmp_path: Path) -> None:
    """When intake.contraindications AND intake.constraints are both empty, the
    preemptive scan short-circuits and returns an empty list."""
    db = _make_fixture_db(tmp_path)
    intake = _make_intake()  # contraindications=[], constraints=[]
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = QUERY_VEC
        pack = compile(intake, db)
    assert pack.compile_metadata.preemptive_contraindications == []
