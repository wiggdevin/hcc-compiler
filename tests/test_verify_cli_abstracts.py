"""Tests for `load_abstracts` — the helper that feeds harvested abstracts
into the verify CLI so Layer-2 faithfulness can run instead of bailing to
``ACCESS_LIMITED``."""
from __future__ import annotations

import json

from hcc_compiler.harvest.abstracts import load_abstracts


def test_load_abstracts_keys_by_doi_and_pmid(tmp_path):
    harvest_dir = tmp_path / "harvest-output"
    harvest_dir.mkdir()
    (harvest_dir / "foo.json").write_text(json.dumps([
        {
            "pmid": "99999999",
            "doi": "10.test/abc",
            "title": "T",
            "year": 2026,
            "journal": "J",
            "abstract": "Some abstract with 2.3-3.1 g/kg/d phrasing",
        }
    ]))

    abstracts = load_abstracts(harvest_dir)

    assert abstracts["10.test/abc"] == "Some abstract with 2.3-3.1 g/kg/d phrasing"
    assert abstracts["99999999"] == "Some abstract with 2.3-3.1 g/kg/d phrasing"


def test_load_abstracts_handles_missing_directory(tmp_path):
    assert load_abstracts(tmp_path / "does-not-exist") == {}


def test_load_abstracts_skips_entries_without_abstract(tmp_path):
    harvest_dir = tmp_path / "harvest-output"
    harvest_dir.mkdir()
    (harvest_dir / "x.json").write_text(json.dumps([
        {"pmid": "111", "doi": "10.x/1"},
        {"pmid": "222", "doi": "10.x/2", "abstract": "hello"},
    ]))

    abstracts = load_abstracts(harvest_dir)

    assert "111" not in abstracts
    assert "10.x/1" not in abstracts
    assert abstracts["222"] == "hello"
    assert abstracts["10.x/2"] == "hello"


def test_load_abstracts_merges_multiple_files(tmp_path):
    harvest_dir = tmp_path / "harvest-output"
    harvest_dir.mkdir()
    (harvest_dir / "a.json").write_text(json.dumps(
        [{"pmid": "1", "doi": "10.a/1", "abstract": "A"}]
    ))
    (harvest_dir / "b.json").write_text(json.dumps(
        [{"pmid": "2", "doi": "10.b/2", "abstract": "B"}]
    ))

    abstracts = load_abstracts(harvest_dir)
    assert abstracts["10.a/1"] == "A"
    assert abstracts["10.b/2"] == "B"


def test_verify_cli_threads_abstracts_into_layer2(tmp_path, monkeypatch):
    """End-to-end: a draft YAML whose citation id appears in the harvest dir
    should hit Layer-2 (no ACCESS_LIMITED) and verify against the abstract."""
    import subprocess
    import sys

    harvest_dir = tmp_path / "harvest-output"
    harvest_dir.mkdir()
    abstract_text = (
        "Higher protein intakes (2.3-3.1 g/kg/d) may be needed to maximize "
        "the retention of lean body mass in resistance-trained subjects "
        "during hypocaloric periods."
    )
    (harvest_dir / "nutrition.json").write_text(json.dumps([
        {"pmid": "28642676", "doi": "10.test/abc",
         "title": "T", "abstract": abstract_text}
    ]))

    draft_dir = tmp_path / "draft-output"
    draft_dir.mkdir()
    draft_yaml = (
        "id: EA-NUT-2676\n"
        "domain: nutrition\n"
        "claim: Higher protein intakes (2.3-3.1 g/kg/d) preserve lean mass during "
        "hypocaloric periods.\n"
        "evidence_level: L1\n"
        "citations:\n"
        "- id: 10.test/abc\n"
        f"  locator_quote: \"{abstract_text}\"\n"
        "  existence: UNVERIFIABLE\n"
        "  faithfulness: ACCESS_LIMITED\n"
        "  cited_title: T\n"
        "population_applicability:\n"
        "  age: 18-55\n"
        "  sex: both\n"
        "  training_status: resistance-trained\n"
        "  dose_magnitude: 2.3-3.1 g/kg/d\n"
        "  duration: 8-16 wk\n"
        "effect: Preserves LBM\n"
        "contraindications: []\n"
        "tier: routine\n"
        "approval: auto\n"
        "library_version: 0.1.0\n"
        "last_reviewed: 2026-05-22\n"
        "expiry: 2027-05-22\n"
    )
    (draft_dir / "EA-NUT-2676.yaml").write_text(draft_yaml)

    repo_root = tmp_path
    monkeypatch.chdir(repo_root)
    script = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "scripts" / "curation" / "verify.py"
    )
    result = subprocess.run(
        [sys.executable, str(script), str(draft_dir), "--harvest", str(harvest_dir)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    verify_json = json.loads(
        (repo_root / "verify-output" / "EA-NUT-2676.json").read_text()
    )
    # The atom's only citation has source text, so Layer 2 must NOT be
    # ACCESS_LIMITED — it should be VERIFIED (quote + numbers both match).
    faithfulness = verify_json["citations"][0]["faithfulness"]
    assert faithfulness != "ACCESS_LIMITED", verify_json
