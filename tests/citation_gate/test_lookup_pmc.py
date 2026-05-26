"""Tests for the PMC full-text fetcher.

Two hops to mock per call:
    1. elink (db=pubmed → db=pmc) returns a JSON envelope with the PMCID
    2. efetch (db=pmc, retmode=xml) returns JATS XML
"""
from pathlib import Path
from unittest.mock import patch

from hcc_compiler.citation_gate.lookup import fetch_pmc_full_text

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _make_urlopen(routes: dict[str, Path]):
    """Build a fake urlopen that picks the fixture by URL substring.

    ``routes`` maps URL-substring -> fixture path. The first match wins.
    """

    class _Resp:
        def __init__(self, body: bytes):
            self._body = body

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return self._body

    def fake(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        for needle, fixture in routes.items():
            if needle in url:
                return _Resp(fixture.read_bytes())
        raise AssertionError(f"unexpected URL in test: {url}")

    return fake


def test_returns_body_paragraphs_joined_when_pmcid_resolves():
    fake = _make_urlopen({
        "elink.fcgi": FIXTURES / "pmc_elink_with_pmcid.json",
        "efetch.fcgi": FIXTURES / "pmc_efetch_full_text.xml",
    })
    with patch("hcc_compiler.citation_gate.lookup.urlopen", new=fake):
        text = fetch_pmc_full_text("28642676")

    assert "muscle protein synthesis" in text
    assert "0.3 to 0.4 g per kg" in text
    assert "searched the literature" in text
    # References belong to <back>, must not bleed in.
    assert "cited reference" not in text


def test_returns_empty_string_when_no_pmcid_link():
    fake = _make_urlopen({
        "elink.fcgi": FIXTURES / "pmc_elink_no_pmcid.json",
    })
    with patch("hcc_compiler.citation_gate.lookup.urlopen", new=fake):
        text = fetch_pmc_full_text("12345678")
    assert text == ""


def test_returns_empty_string_when_elink_raises():
    def raises(*args, **kwargs):
        raise RuntimeError("network down")

    with patch("hcc_compiler.citation_gate.lookup.urlopen", new=raises):
        text = fetch_pmc_full_text("28642676")
    assert text == ""
