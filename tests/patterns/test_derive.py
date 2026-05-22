"""Tests for patterns/derive.py — T7 TDD suite."""
from __future__ import annotations
import json
import re
from datetime import date
from unittest.mock import patch, MagicMock

import pytest

from hcc_compiler.models import Domain, EvidenceAtom, EvidenceLevel, Tier, Citation, PopulationApplicability


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_atom(atom_id: str, domain: Domain, claim: str, effect: str) -> EvidenceAtom:
    return EvidenceAtom(
        id=atom_id,
        domain=domain,
        claim=claim,
        evidence_level=EvidenceLevel.L2,
        citations=[Citation(
            id="10.1000/test",
            locator_quote="test quote",
            existence="VERIFIED",
            faithfulness="VERIFIED",
            cited_title="Test Study",
        )],
        population_applicability=PopulationApplicability(
            age="adults",
            sex="all",
            training_status="active",
            dose_magnitude="moderate",
            duration="12 weeks",
        ),
        effect=effect,
        contraindications=[],
        tier=Tier.ROUTINE,
        approval="approved",
        library_version="0.1.0",
        last_reviewed=date(2026, 1, 1),
        expiry=date(2027, 1, 1),
    )


_ATOMS = [
    _make_atom("EA-NUT-0001", Domain.NUTRITION, "Protein intake ≥1.6g/kg increases lean mass.", "Significant lean mass gains over 12 weeks."),
    _make_atom("EA-NUT-0002", Domain.NUTRITION, "Higher protein preserves muscle during caloric deficit.", "Reduced muscle loss in deficit."),
    _make_atom("EA-NUT-0003", Domain.NUTRITION, "Protein timing post-workout enhances recovery.", "Improved recovery markers."),
]

_GOOD_PATTERN_JSON = {
    "id": "RP-NUT-protein-target-older-adults",
    "domain": "nutrition",
    "pattern": "Target ≥1.6g/kg/day protein for lean mass gain.",
    "parameterization": "Adjust upward (1.8–2.0g/kg) during caloric deficit.",
    "backing_atom_ids": ["EA-NUT-0001"],  # LLM may emit wrong ids; caller overwrites
    "falsification_signal": "No lean mass change after 8+ weeks at target intake.",
    "safety_bounds": "Do not exceed 2.5g/kg without clinical supervision.",
    "applies_because": "Multiple RCTs confirm dose-response relationship.",
    "doesnt_apply_if": "Renal impairment; clinician review required.",
    "tier": "routine",
    "approval": "auto",
    "version": "0.1.0",
}


# ---------------------------------------------------------------------------
# Test 1 – happy path: valid pydantic instance returned
# ---------------------------------------------------------------------------

def test_derive_pattern_returns_valid_instance():
    from hcc_compiler.patterns.derive import derive_pattern

    with patch("hcc_compiler.patterns.derive.call_llm", return_value=json.dumps(_GOOD_PATTERN_JSON)):
        result = derive_pattern(_ATOMS)

    from hcc_compiler.models import RecommendationPattern
    assert isinstance(result, RecommendationPattern)
    assert re.match(r"^RP-[A-Z]{2,4}-[a-z0-9-]+$", result.id)


# ---------------------------------------------------------------------------
# Test 2 – prompt includes each atom's id, claim, and effect
# ---------------------------------------------------------------------------

def test_derive_pattern_prompt_contains_atom_fields():
    from hcc_compiler.patterns.derive import derive_pattern
    from hcc_compiler.llm.anthropic_client import LLMRequest

    captured: list[LLMRequest] = []

    def fake_call_llm(req: LLMRequest) -> str:
        captured.append(req)
        return json.dumps(_GOOD_PATTERN_JSON)

    with patch("hcc_compiler.patterns.derive.call_llm", side_effect=fake_call_llm):
        derive_pattern(_ATOMS)

    assert len(captured) == 1
    prompt = captured[0].user_prompt
    for atom in _ATOMS:
        assert atom.id in prompt
        assert atom.claim in prompt
        assert atom.effect in prompt


# ---------------------------------------------------------------------------
# Test 3 – backing_atom_ids is force-set to input atom IDs
# ---------------------------------------------------------------------------

def test_derive_pattern_stamps_backing_atom_ids():
    from hcc_compiler.patterns.derive import derive_pattern

    # LLM emits wrong/partial ids — caller must overwrite
    bad_json = dict(_GOOD_PATTERN_JSON)
    bad_json["backing_atom_ids"] = ["wrong-id"]

    with patch("hcc_compiler.patterns.derive.call_llm", return_value=json.dumps(bad_json)):
        result = derive_pattern(_ATOMS)

    expected_ids = [a.id for a in _ATOMS]
    assert result.backing_atom_ids == expected_ids


# ---------------------------------------------------------------------------
# Test 4 – malformed JSON raises ValueError
# ---------------------------------------------------------------------------

def test_derive_pattern_raises_on_malformed_json():
    from hcc_compiler.patterns.derive import derive_pattern

    with patch("hcc_compiler.patterns.derive.call_llm", return_value="no json here at all"):
        with pytest.raises(ValueError):
            derive_pattern(_ATOMS)


# ---------------------------------------------------------------------------
# Test 5 – pydantic ValidationError propagates on bad id regex
# ---------------------------------------------------------------------------

def test_derive_pattern_propagates_validation_error():
    from hcc_compiler.patterns.derive import derive_pattern
    from pydantic import ValidationError

    bad_json = dict(_GOOD_PATTERN_JSON)
    bad_json["id"] = "INVALID_ID_FORMAT"

    with patch("hcc_compiler.patterns.derive.call_llm", return_value=json.dumps(bad_json)):
        with pytest.raises(ValidationError):
            derive_pattern(_ATOMS)
