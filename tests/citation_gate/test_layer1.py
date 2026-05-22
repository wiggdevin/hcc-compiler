from unittest.mock import patch

from hcc_compiler.models import Citation
from hcc_compiler.citation_gate.layer1 import verify_existence
from hcc_compiler.citation_gate.lookup import LookupResult


JAGER = LookupResult(
    title="International Society of Sports Nutrition Position Stand: protein and exercise",
    year=2017,
    doi="10.1186/s12970-017-0177-8",
    pmid="28642676",
    journal="Journal of the International Society of Sports Nutrition",
)

DIFFERENT_PAPER = LookupResult(
    title="Quantum entanglement in superconductors",
    year=2017,
    doi="10.1186/s12970-017-0177-8",
    pmid=None,
    journal="Random Journal",
)


def _cite(**kwargs) -> Citation:
    base = dict(
        id="10.1186/s12970-017-0177-8",
        locator_quote="…",
        existence="VERIFIED",
        faithfulness="VERIFIED",
        cited_title="International Society of Sports Nutrition Position Stand: protein and exercise",
    )
    base.update(kwargs)
    return Citation(**base)


def test_verified_when_doi_resolves_to_matching_title():
    with patch("hcc_compiler.citation_gate.layer1.resolve_doi", return_value=JAGER):
        outcome = verify_existence(_cite())
    assert outcome == "VERIFIED"


def test_doi_mismatch_when_resolved_title_diverges():
    with patch("hcc_compiler.citation_gate.layer1.resolve_doi", return_value=DIFFERENT_PAPER):
        outcome = verify_existence(_cite())
    assert outcome == "DOI_MISMATCH"


def test_unverifiable_when_lookup_returns_none():
    with patch("hcc_compiler.citation_gate.layer1.resolve_doi", side_effect=Exception("boom")):
        outcome = verify_existence(_cite())
    assert outcome == "UNVERIFIABLE"


def test_unverifiable_when_cited_title_missing():
    """Without a claimed title we cannot run the DOI_MISMATCH check."""
    outcome = verify_existence(_cite(cited_title=None))
    assert outcome == "UNVERIFIABLE"
