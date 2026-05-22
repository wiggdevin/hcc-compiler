from __future__ import annotations
import json
import os
import re
from dataclasses import dataclass
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


@dataclass
class LookupResult:
    title: str
    year: int | None
    doi: str | None
    pmid: str | None
    journal: str | None


def _email() -> str:
    return os.environ.get("HCC_CONTACT_EMAIL", "devin@zerosumsolutions.com")


def _ua_headers() -> dict[str, str]:
    return {"User-Agent": f"hcc-compiler/0.1 (mailto:{_email()})"}


def _get_json(url: str, timeout: float = 15.0) -> dict:
    req = Request(url, headers=_ua_headers())
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_pubmed_by_pmid(pmid: str) -> LookupResult:
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
        + urlencode({
            "db": "pubmed", "id": pmid, "retmode": "json",
            "tool": "hcc-compiler", "email": _email(),
        })
    )
    data = _get_json(url)
    rec = data.get("result", {}).get(pmid, {}) or {}
    pubdate = rec.get("pubdate", "")
    m = re.search(r"\d{4}", pubdate)
    year = int(m.group(0)) if m else None
    doi = None
    for aid in rec.get("articleids", []):
        if aid.get("idtype") == "doi":
            doi = aid.get("value")
    return LookupResult(
        title=rec.get("title", "").rstrip("."),
        year=year,
        doi=doi,
        pmid=pmid,
        journal=rec.get("fulljournalname"),
    )


def resolve_doi(doi: str) -> LookupResult:
    url = f"https://api.crossref.org/works/{quote(doi, safe='/')}"
    data = _get_json(url)
    msg = data.get("message", {})
    title_list = msg.get("title", []) or [""]
    issued = msg.get("issued", {}).get("date-parts", [[None]])
    year = issued[0][0] if issued and issued[0] else None
    journal_list = msg.get("container-title", []) or [None]
    return LookupResult(
        title=title_list[0],
        year=year,
        doi=msg.get("DOI"),
        pmid=None,
        journal=journal_list[0],
    )
