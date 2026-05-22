from datetime import date
from unittest.mock import patch

from hcc_compiler.models import EvidenceAtom, Citation
from hcc_compiler.citation_gate.lookup import LookupResult
from hcc_compiler.citation_gate.orchestrator import verify_atom


GOOD_LOOKUP = LookupResult(
    title="International Society of Sports Nutrition Position Stand: protein and exercise",
    year=2017,
    doi="10.1186/s12970-017-0177-8",
    pmid="28642676",
    journal="J ISSN",
)


def _atom() -> EvidenceAtom:
    return EvidenceAtom(
        id="EA-NUT-9999",
        domain="nutrition",
        claim="Protein intakes of 2.3-3.1 g/kg/day may be needed.",
        evidence_level="L1",
        citations=[Citation(
            id="10.1186/s12970-017-0177-8",
            locator_quote="Higher protein intakes (2.3-3.1 g/kg/d) may be needed",
            existence="VERIFIED",
            faithfulness="VERIFIED",
            cited_title="International Society of Sports Nutrition Position Stand: protein and exercise",
        )],
        population_applicability=dict(
            age="18-55", sex="both", training_status="resistance-trained",
            dose_magnitude="2.3-3.1 g/kg/d", duration="8-16 wk",
        ),
        effect="…",
        tier="high-impact",
        approval="Dev Wiggins 2026-05-22",
        library_version="0.1.0",
        last_reviewed=date(2026, 5, 22),
        expiry=date(2027, 5, 22),
    )


def test_verify_atom_pass_with_notes_when_no_source_text():
    """No source_text → Layer 2 returns ACCESS_LIMITED → overall PASS_WITH_NOTES."""
    with patch("hcc_compiler.citation_gate.layer1.resolve_doi", return_value=GOOD_LOOKUP):
        result = verify_atom(_atom())
    assert result["overall"] == "PASS_WITH_NOTES"
    assert result["citations"][0]["existence"] == "VERIFIED"
    assert result["citations"][0]["faithfulness"] == "ACCESS_LIMITED"


def test_verify_atom_pass_when_source_text_supports_claim():
    src = "Higher protein intakes (2.3-3.1 g/kg/d) may be needed to maximize the retention of lean body mass."
    with patch("hcc_compiler.citation_gate.layer1.resolve_doi", return_value=GOOD_LOOKUP):
        result = verify_atom(_atom(), source_texts={"10.1186/s12970-017-0177-8": src})
    assert result["overall"] == "PASS"
    assert result["citations"][0]["existence"] == "VERIFIED"
    assert result["citations"][0]["faithfulness"] == "VERIFIED"


def test_verify_atom_fail_on_doi_mismatch():
    bad = LookupResult(title="Quantum entanglement", year=2017, doi="…", pmid=None, journal="…")
    with patch("hcc_compiler.citation_gate.layer1.resolve_doi", return_value=bad):
        result = verify_atom(_atom())
    assert result["overall"] == "FAIL"
    assert result["citations"][0]["existence"] == "DOI_MISMATCH"
