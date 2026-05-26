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


_MIN_INTERVAL_S = 0.5
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


def fetch_pmc_full_text(pmid: str) -> str:
    """Return the full-text body of the PMC article linked to ``pmid``.

    Two hops:
        1. ``elink dbfrom=pubmed db=pmc`` — map PMID → PMCID.
        2. ``efetch db=pmc retmode=xml`` — fetch the JATS XML.

    Returns the concatenation of every ``<p>`` under ``<body>`` (i.e. the
    article narrative, excluding metadata, references and figure captions).
    Empty string when:
        - no PMC equivalent exists (paywall, not deposited),
        - either eutils call fails or returns malformed XML.

    The Layer 2 faithfulness check normalises and substring-matches against
    whatever text is here, so a slightly noisy concatenation is fine; missing
    text just falls through to ``ACCESS_LIMITED``.
    """
    elink_url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?"
        + urlencode({
            "dbfrom": "pubmed", "db": "pmc", "id": pmid, "retmode": "json",
            "tool": "hcc-compiler", "email": _email(),
        })
    )
    try:
        data = _get_json(elink_url)
    except Exception:
        return ""

    pmcid: str | None = None
    for linkset in data.get("linksets") or []:
        for dbs in linkset.get("linksetdbs") or []:
            if dbs.get("dbto") == "pmc":
                links = dbs.get("links") or []
                if links:
                    pmcid = str(links[0])
                    break
        if pmcid:
            break
    if not pmcid:
        return ""

    efetch_url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
        + urlencode({
            "db": "pmc", "id": pmcid, "retmode": "xml",
            "tool": "hcc-compiler", "email": _email(),
        })
    )
    try:
        xml_text = _get_text(efetch_url)
        root = ET.fromstring(xml_text)
    except Exception:
        return ""

    parts: list[str] = []
    for body in root.iter("body"):
        for p in body.iter("p"):
            text = " ".join("".join(p.itertext()).split()).strip()
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
