import pytest
from pydantic import ValidationError
from hcc_compiler.models import EvidenceAtom

VALID = {
    "id": "EA-NUT-0001",
    "domain": "nutrition",
    "claim": "1.6-2.2 g/kg/day protein maximizes lean mass retention in a deficit.",
    "evidence_level": "L1",
    "citations": [{
        "id": "10.1234/jissn.2023.001",
        "locator_quote": "protein intakes of 1.6-2.2 g/kg/day...",
        "existence": "VERIFIED",
        "faithfulness": "VERIFIED",
    }],
    "population_applicability": {
        "age": "18-55", "sex": "both", "training_status": "trained",
        "dose_magnitude": "moderate deficit", "duration": "8-16 wk",
    },
    "effect": "Preserves FFM vs lower intake (SMD ~0.3).",
    "tier": "high-impact",
    "approval": "Dev Wiggins 2026-05-21",
    "library_version": "0.1.0",
    "last_reviewed": "2026-05-21",
    "expiry": "2027-05-21",
}

def test_valid_atom_parses():
    a = EvidenceAtom.model_validate(VALID)
    assert a.id == "EA-NUT-0001"
    assert a.citations[0].existence == "VERIFIED"

def test_atom_requires_at_least_one_citation():
    bad = {**VALID, "citations": []}
    with pytest.raises(ValidationError):
        EvidenceAtom.model_validate(bad)

def test_atom_id_pattern_enforced():
    bad = {**VALID, "id": "NUT-1"}
    with pytest.raises(ValidationError):
        EvidenceAtom.model_validate(bad)

def test_bad_enum_rejected():
    bad = {**VALID, "evidence_level": "L9"}
    with pytest.raises(ValidationError):
        EvidenceAtom.model_validate(bad)
