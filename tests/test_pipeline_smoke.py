import json
from pathlib import Path
from unittest.mock import patch

import yaml
from hcc_compiler.extract import extract_atom
from hcc_compiler.citation_gate.orchestrator import verify_atom
from hcc_compiler.models import EvidenceAtom
from hcc_compiler.route import route_draft

FIXTURES = Path(__file__).parent / "fixtures"


def test_pipeline_routes_fixture_candidate_into_queue(tmp_path):
    candidate = {
        "pmid": "28642676",
        "doi": "10.1186/s12970-017-0177-8",
        "title": "International Society of Sports Nutrition Position Stand: protein and exercise",
        "year": 2017,
        "abstract": "Higher protein intakes (2.3-3.1 g/kg/d) may be needed…",
        "journal": "JISSN",
    }
    canned_llm = (FIXTURES / "llm_extract_nutrition.json").read_text()

    draft_dir = tmp_path / "draft-output"
    verify_dir = tmp_path / "verify-output"
    library_root = tmp_path / "library"
    draft_dir.mkdir(); verify_dir.mkdir()

    with patch("hcc_compiler.extract.call_llm", return_value=canned_llm):
        draft = extract_atom(candidate)
    atom = EvidenceAtom.model_validate(draft)
    (draft_dir / f"{atom.id}.yaml").write_text(yaml.safe_dump(draft, sort_keys=False))

    # verify atom (no source text → PASS_WITH_NOTES; existence cannot run live without network → UNVERIFIABLE)
    from hcc_compiler.citation_gate import layer1 as l1
    with patch.object(l1, "resolve_doi", side_effect=Exception("offline")):
        result = verify_atom(atom)
    (verify_dir / f"{atom.id}.json").write_text(json.dumps(result))

    decisions = route_draft(draft_dir, verify_dir, library_root)
    # High-impact tier → always queued.
    assert decisions[atom.id] == "queued"
    assert (library_root / "queue" / f"{atom.id}.yaml").exists()
