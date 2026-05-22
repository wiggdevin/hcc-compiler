import json
from pathlib import Path
from unittest.mock import patch

from hcc_compiler.extract import extract_atom
from hcc_compiler.models import EvidenceAtom

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_extract_atom_round_trips_through_model():
    canned = (FIXTURES / "llm_extract_nutrition.json").read_text()
    candidate = {
        "pmid": "28642676",
        "doi": "10.1186/s12970-017-0177-8",
        "title": "International Society of Sports Nutrition Position Stand: protein and exercise",
        "year": 2017,
        "abstract": "Higher protein intakes (2.3-3.1 g/kg/d) may be needed…",
        "journal": "J ISSN",
    }

    with patch("hcc_compiler.extract.call_llm", return_value=canned):
        draft = extract_atom(candidate)
    atom = EvidenceAtom.model_validate(draft)
    assert atom.id.startswith("EA-")
    assert atom.tier in ("high-impact", "routine")
    assert atom.citations[0].id == candidate["doi"]
