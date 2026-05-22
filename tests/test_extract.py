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


def test_extract_atom_id_is_deterministic_from_pmid():
    """The id field the LLM emits is overwritten with EA-<canonical>-<last4 PMID>."""
    # Bogus id + bogus domain prefix from a "misbehaving" LLM payload.
    bogus = json.dumps({
        "id": "EA-FOO-9999",
        "domain": "nutrition",
        "claim": "x",
        "evidence_level": "L1",
        "citations": [{
            "id": "WRONG-DOI",
            "locator_quote": "x",
            "existence": "UNVERIFIABLE",
            "faithfulness": "ACCESS_LIMITED",
            "cited_title": "wrong title",
        }],
        "population_applicability": {
            "age": "x", "sex": "x", "training_status": "x",
            "dose_magnitude": "x", "duration": "x",
        },
        "effect": "x",
        "contraindications": [],
        "tier": "routine",
        "approval": "auto",
        "library_version": "0.1.0",
        "last_reviewed": "2026-05-22",
        "expiry": "2027-05-22",
    })
    candidate = {
        "pmid": "42124009",
        "doi": "10.3390/nu18091409",
        "title": "Real Title",
        "year": 2026,
        "journal": "J",
        "abstract": "x",
    }
    with patch("hcc_compiler.extract.call_llm", return_value=bogus):
        draft = extract_atom(candidate)
    # Last 4 digits of "42124009" → "4009".
    assert draft["id"] == "EA-NUT-4009"
    assert draft["citations"][0]["id"] == "10.3390/nu18091409"
    assert draft["citations"][0]["cited_title"] == "Real Title"


def test_extract_atom_id_pads_short_pmid():
    bogus = json.dumps({
        "id": "EA-XX-0000",
        "domain": "supplements",
        "claim": "x",
        "evidence_level": "L2",
        "citations": [{
            "id": "any",
            "locator_quote": "x",
            "existence": "UNVERIFIABLE",
            "faithfulness": "ACCESS_LIMITED",
            "cited_title": "t",
        }],
        "population_applicability": {
            "age": "x", "sex": "x", "training_status": "x",
            "dose_magnitude": "x", "duration": "x",
        },
        "effect": "x",
        "contraindications": [],
        "tier": "routine",
        "approval": "auto",
        "library_version": "0.1.0",
        "last_reviewed": "2026-05-22",
        "expiry": "2027-05-22",
    })
    candidate = {"pmid": "42", "doi": "10.x/y", "title": "T", "year": 2026, "journal": "J", "abstract": "a"}
    with patch("hcc_compiler.extract.call_llm", return_value=bogus):
        draft = extract_atom(candidate)
    assert draft["id"] == "EA-SUP-0042"
