from __future__ import annotations
import json
import os
import re
import time
import xml.etree.ElementTree as ET
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


_MIN_INTERVAL_S = 0.4
_last_call_at = 0.0


def _throttle() -> None:
    global _last_call_at
    now = time.monotonic()
    wait = _MIN_INTERVAL_S - (now - _last_call_at)
    if wait > 0:
        time.sleep(wait)
    _last_call_at = time.monotonic()


def _email() -> str:
    return os.environ.get("HCC_CONTACT_EMAIL", "devin@zerosumsolutions.com")


def _ua_headers() -> dict[str, str]:
    return {"User-Agent": f"hcc-compiler/0.1 (mailto:{_email()})"}


def _get_json(url: str, timeout: float = 15.0) -> dict:
    _throttle()
    req = Request(url, headers=_ua_headers())
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_text(url: str, timeout: float = 15.0) -> str:
    _throttle()
    req = Request(url, headers=_ua_headers())
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


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


def fetch_pubmed_abstract(pmid: str) -> str:
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
        + urlencode({
            "db": "pubmed", "id": pmid, "rettype": "abstract", "retmode": "xml",
            "tool": "hcc-compiler", "email": _email(),
        })
    )
    xml_text = _get_text(url)
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return ""
    parts: list[str] = []
    for node in root.iter("AbstractText"):
        text = "".join(node.itertext()).strip()
        if text:
            parts.append(text)
    return " ".join(parts)


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
