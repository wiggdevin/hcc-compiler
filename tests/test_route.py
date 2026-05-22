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
