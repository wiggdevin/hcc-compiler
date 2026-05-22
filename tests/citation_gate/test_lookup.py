import json
from pathlib import Path
from unittest.mock import patch

from hcc_compiler.citation_gate.lookup import (
    LookupResult,
    fetch_pubmed_by_pmid,
    resolve_doi,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _fake_urlopen(payload_path: Path):
    """Return a context-manager-like object whose .read() returns the fixture."""
    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def read(self_inner): return payload_path.read_bytes()
    return lambda req, timeout=None: _Resp()


def test_fetch_pubmed_by_pmid_returns_title_and_year():
    with patch(
        "hcc_compiler.citation_gate.lookup.urlopen",
        new=_fake_urlopen(FIXTURES / "pubmed_jager2017_esummary.json"),
    ):
        r = fetch_pubmed_by_pmid("28642676")
    assert isinstance(r, LookupResult)
    assert "protein and exercise" in r.title.lower()
    assert r.year == 2017
    assert r.doi == "10.1186/s12970-017-0177-8"


def test_resolve_doi_returns_crossref_metadata():
    with patch(
        "hcc_compiler.citation_gate.lookup.urlopen",
        new=_fake_urlopen(FIXTURES / "crossref_jager2017.json"),
    ):
        r = resolve_doi("10.1186/s12970-017-0177-8")
    assert r.year == 2017
    assert "protein and exercise" in r.title.lower()
    assert r.journal == "Journal of the International Society of Sports Nutrition"


def test_request_carries_politeness_email(monkeypatch):
    """The PubMed and Crossref requests must include a User-Agent / email."""
    monkeypatch.setenv("HCC_CONTACT_EMAIL", "devin@zerosumsolutions.com")
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        class _Resp:
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def read(self_inner): return (FIXTURES / "crossref_jager2017.json").read_bytes()
        return _Resp()

    with patch("hcc_compiler.citation_gate.lookup.urlopen", new=fake_urlopen):
        resolve_doi("10.1186/s12970-017-0177-8")
    ua = captured["headers"].get("User-agent") or captured["headers"].get("User-Agent", "")
    assert "devin@zerosumsolutions.com" in ua or "devin@zerosumsolutions.com" in captured["url"]
