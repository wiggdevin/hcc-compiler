# tests/test_models_pattern.py
import pytest
from pydantic import ValidationError
from hcc_compiler.models import RecommendationPattern

VALID = {
    "id": "RP-NUT-protein-band",
    "domain": "nutrition",
    "pattern": "protein target band",
    "parameterization": "1.6-2.2 g/kg/day; pick upper end in steeper deficits.",
    "backing_atom_ids": ["EA-NUT-0001"],
    "falsification_signal": "FFM drops >1%/wk over 3 wk at target intake.",
    "safety_bounds": "Do not exceed 2.5 g/kg/day; flag renal history.",
    "applies_because": "Trained adults in a deficit.",
    "doesnt_apply_if": "CKD or other renal contraindication.",
    "tier": "high-impact",
    "approval": "Dev Wiggins 2026-05-21",
    "version": "0.1.0",
}

def test_valid_pattern_parses():
    p = RecommendationPattern.model_validate(VALID)
    assert p.backing_atom_ids == ["EA-NUT-0001"]

def test_pattern_requires_backing_atom():
    with pytest.raises(ValidationError):
        RecommendationPattern.model_validate({**VALID, "backing_atom_ids": []})

def test_pattern_id_pattern_enforced():
    with pytest.raises(ValidationError):
        RecommendationPattern.model_validate({**VALID, "id": "protein"})
