from __future__ import annotations
from typing import Mapping
from hcc_compiler.models import EvidenceAtom
from hcc_compiler.citation_gate.layer1 import verify_existence
from hcc_compiler.citation_gate.layer2 import verify_faithfulness

_FAIL_EXISTENCE = {"DOI_MISMATCH", "FABRICATED"}
_FAIL_FAITHFULNESS = {"MAJOR_DISTORTION", "UNSUPPORTED"}
_NOTE_VALUES = {"ACCESS_LIMITED", "MINOR_DISTORTION", "PLAUSIBLE", "UNVERIFIABLE"}


def verify_atom(atom: EvidenceAtom, source_texts: Mapping[str, str] | None = None) -> dict:
    source_texts = source_texts or {}
    citation_results = []
    has_fail = False
    has_note = False
    for c in atom.citations:
        existence = verify_existence(c)
        faithfulness = verify_faithfulness(atom.claim, c, source_text=source_texts.get(c.id))
        citation_results.append({
            "id": c.id,
            "existence": existence,
            "faithfulness": faithfulness,
        })
        if existence in _FAIL_EXISTENCE or faithfulness in _FAIL_FAITHFULNESS:
            has_fail = True
        if existence in _NOTE_VALUES or faithfulness in _NOTE_VALUES:
            has_note = True

    if has_fail:
        overall = "FAIL"
    elif has_note:
        overall = "PASS_WITH_NOTES"
    else:
        overall = "PASS"

    return {"atom_id": atom.id, "overall": overall, "citations": citation_results}
