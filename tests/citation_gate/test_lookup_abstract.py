from pathlib import Path
from unittest.mock import patch

from hcc_compiler.citation_gate.lookup import fetch_pubmed_abstract

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _fake_urlopen(payload_path: Path):
    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def read(self_inner): return payload_path.read_bytes()
    return lambda req, timeout=None: _Resp()


def test_fetch_pubmed_abstract_joins_structured_sections():
    with patch(
        "hcc_compiler.citation_gate.lookup.urlopen",
        new=_fake_urlopen(FIXTURES / "pubmed_efetch_jager2017.xml"),
    ):
        abstract = fetch_pubmed_abstract("28642676")
    assert "Protein intake supports muscle protein synthesis" in abstract
    assert "1.4-2.0 g protein/kg" in abstract
    # Sections joined by single space, in document order.
    assert "exercise. An overall daily" in abstract


def test_fetch_pubmed_abstract_returns_empty_when_missing():
    with patch(
        "hcc_compiler.citation_gate.lookup.urlopen",
        new=_fake_urlopen(FIXTURES / "pubmed_efetch_no_abstract.xml"),
    ):
        abstract = fetch_pubmed_abstract("99999999")
    assert abstract == ""
