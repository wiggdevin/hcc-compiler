from pathlib import Path
from unittest.mock import patch

from hcc_compiler.harvest.queries import build_query, DOMAIN_QUERIES, run_harvest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_known_domains_registered():
    for d in ("nutrition", "supplements", "training", "conditioning", "recovery", "behavioral"):
        assert d in DOMAIN_QUERIES, f"missing domain {d}"
        assert isinstance(DOMAIN_QUERIES[d], list)
        assert DOMAIN_QUERIES[d]


def test_build_query_includes_since_year():
    q = build_query(DOMAIN_QUERIES["nutrition"][0], since=2022)
    assert "2022" in q


def test_run_harvest_returns_pmids_from_mocked_pubmed():
    def fake_esearch(query: str):
        return ["28642676", "28615996"]

    def fake_summary(pmid: str):
        return {"pmid": pmid, "doi": f"10.x/{pmid}", "title": f"Paper {pmid}", "year": 2017, "abstract": "", "journal": "J"}

    with patch("hcc_compiler.harvest.queries._esearch", new=fake_esearch), \
         patch("hcc_compiler.harvest.queries._summary", new=fake_summary):
        out = run_harvest(domain="nutrition", since=2022)
    assert len(out) >= 1
    assert all("pmid" in r and "title" in r for r in out)
