import json
from pathlib import Path

import yaml
from hcc_compiler.route import route_draft


def _atom_yaml(atom_id: str, tier: str) -> dict:
    return {
        "id": atom_id, "domain": "nutrition",
        "claim": "x", "evidence_level": "L1",
        "citations": [{"id": "10.x/y", "locator_quote": "q", "existence": "VERIFIED", "faithfulness": "VERIFIED", "cited_title": "t"}],
        "population_applicability": {"age": "18-55", "sex": "both", "training_status": "trained", "dose_magnitude": "x", "duration": "x"},
        "effect": "x", "tier": tier, "approval": "auto",
        "library_version": "0.1.0", "last_reviewed": "2026-05-22", "expiry": "2027-05-22",
    }


def test_routine_pass_goes_to_library_atoms(tmp_path):
    draft = tmp_path / "draft-output"
    verify = tmp_path / "verify-output"
    library = tmp_path / "library"
    draft.mkdir(); verify.mkdir()
    (draft / "EA-NUT-0099.yaml").write_text(yaml.safe_dump(_atom_yaml("EA-NUT-0099", "routine")))
    (verify / "EA-NUT-0099.json").write_text(json.dumps({"atom_id": "EA-NUT-0099", "overall": "PASS"}))
    out = route_draft(draft, verify, library)
    assert (library / "atoms" / "nutrition" / "EA-NUT-0099.yaml").exists()
    assert out["EA-NUT-0099"] == "admitted"


def test_high_impact_pass_goes_to_queue(tmp_path):
    draft = tmp_path / "draft-output"
    verify = tmp_path / "verify-output"
    library = tmp_path / "library"
    draft.mkdir(); verify.mkdir()
    (draft / "EA-NUT-0100.yaml").write_text(yaml.safe_dump(_atom_yaml("EA-NUT-0100", "high-impact")))
    (verify / "EA-NUT-0100.json").write_text(json.dumps({"atom_id": "EA-NUT-0100", "overall": "PASS"}))
    out = route_draft(draft, verify, library)
    assert (library / "queue" / "EA-NUT-0100.yaml").exists()
    assert out["EA-NUT-0100"] == "queued"


def test_fail_verdict_routes_to_queue_even_for_routine(tmp_path):
    draft = tmp_path / "draft-output"
    verify = tmp_path / "verify-output"
    library = tmp_path / "library"
    draft.mkdir(); verify.mkdir()
    (draft / "EA-NUT-0101.yaml").write_text(yaml.safe_dump(_atom_yaml("EA-NUT-0101", "routine")))
    (verify / "EA-NUT-0101.json").write_text(json.dumps({"atom_id": "EA-NUT-0101", "overall": "FAIL"}))
    out = route_draft(draft, verify, library)
    assert (library / "queue" / "EA-NUT-0101.yaml").exists()
    assert out["EA-NUT-0101"] == "queued"


def test_pass_with_notes_routes_routine_to_queue(tmp_path):
    draft = tmp_path / "draft-output"
    verify = tmp_path / "verify-output"
    library = tmp_path / "library"
    draft.mkdir(); verify.mkdir()
    (draft / "EA-NUT-0102.yaml").write_text(yaml.safe_dump(_atom_yaml("EA-NUT-0102", "routine")))
    (verify / "EA-NUT-0102.json").write_text(json.dumps({"atom_id": "EA-NUT-0102", "overall": "PASS_WITH_NOTES"}))
    out = route_draft(draft, verify, library)
    assert (library / "queue" / "EA-NUT-0102.yaml").exists()
    assert out["EA-NUT-0102"] == "queued"


def test_routine_pass_skips_when_destination_already_exists(tmp_path):
    draft = tmp_path / "draft-output"
    verify = tmp_path / "verify-output"
    library = tmp_path / "library"
    draft.mkdir(); verify.mkdir()
    existing_dir = library / "atoms" / "nutrition"
    existing_dir.mkdir(parents=True)
    existing_path = existing_dir / "EA-NUT-0104.yaml"
    original_atom = _atom_yaml("EA-NUT-0104", "routine")
    original_atom["claim"] = "ORIGINAL CLAIM — must not be overwritten"
    existing_path.write_text(yaml.safe_dump(original_atom))

    new_atom = _atom_yaml("EA-NUT-0104", "routine")
    new_atom["claim"] = "NEW CLAIM — should not land"
    draft_path = draft / "EA-NUT-0104.yaml"
    draft_path.write_text(yaml.safe_dump(new_atom))
    (verify / "EA-NUT-0104.json").write_text(json.dumps({"atom_id": "EA-NUT-0104", "overall": "PASS"}))

    out = route_draft(draft, verify, library)

    assert out["EA-NUT-0104"] == "skipped-collision"
    # Existing file untouched
    assert "ORIGINAL CLAIM" in existing_path.read_text()
    # Draft preserved for manual triage
    assert draft_path.exists()


def test_skips_when_id_already_in_other_destination(tmp_path):
    """An id already admitted to atoms/ must not be re-queued under queue/ (and vice versa)."""
    draft = tmp_path / "draft-output"
    verify = tmp_path / "verify-output"
    library = tmp_path / "library"
    draft.mkdir(); verify.mkdir()
    admitted_dir = library / "atoms" / "training"
    admitted_dir.mkdir(parents=True)
    (admitted_dir / "EA-TRA-7777.yaml").write_text(yaml.safe_dump(_atom_yaml("EA-TRA-7777", "routine")))

    # New extraction tags this id as high-impact PASS → would go to queue under old rules.
    hi = _atom_yaml("EA-TRA-7777", "high-impact")
    hi["domain"] = "training"
    draft_path = draft / "EA-TRA-7777.yaml"
    draft_path.write_text(yaml.safe_dump(hi))
    (verify / "EA-TRA-7777.json").write_text(json.dumps({"atom_id": "EA-TRA-7777", "overall": "PASS"}))

    out = route_draft(draft, verify, library)

    assert out["EA-TRA-7777"] == "skipped-collision"
    assert not (library / "queue" / "EA-TRA-7777.yaml").exists()
    assert draft_path.exists()


def test_routed_draft_removed_from_source(tmp_path):
    draft = tmp_path / "draft-output"
    verify = tmp_path / "verify-output"
    library = tmp_path / "library"
    draft.mkdir(); verify.mkdir()
    draft_path = draft / "EA-NUT-0103.yaml"
    draft_path.write_text(yaml.safe_dump(_atom_yaml("EA-NUT-0103", "routine")))
    (verify / "EA-NUT-0103.json").write_text(json.dumps({"atom_id": "EA-NUT-0103", "overall": "PASS"}))
    route_draft(draft, verify, library)
    assert not draft_path.exists()
    assert (library / "atoms" / "nutrition" / "EA-NUT-0103.yaml").exists()
