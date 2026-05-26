from __future__ import annotations
from hcc_compiler.models import Citation
from hcc_compiler.citation_gate.lookup import resolve_doi
from hcc_compiler.citation_gate.text import title_similarity

EXISTENCE_OUTCOMES = {"VERIFIED", "PLAUSIBLE", "UNVERIFIABLE", "DOI_MISMATCH", "FABRICATED"}

_TITLE_GATE = 0.60


def verify_existence(citation: Citation) -> str:
    if not citation.cited_title:
        return "UNVERIFIABLE"
    if "/" not in citation.id:
        return "UNVERIFIABLE"
    try:
        resolved = resolve_doi(citation.id)
    except Exception:
        return "UNVERIFIABLE"
    if not resolved.title:
        return "UNVERIFIABLE"
    sim = title_similarity(resolved.title, citation.cited_title)
    if sim >= _TITLE_GATE:
        return "VERIFIED"
    return "DOI_MISMATCH"
