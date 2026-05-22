from __future__ import annotations
import os
from urllib.parse import urlencode

from hcc_compiler.citation_gate.lookup import _get_json

DOMAIN_QUERIES: dict[str, list[str]] = {
    "nutrition": [
        '("protein intake" OR "dietary proteins"[MeSH]) AND ("resistance training" OR athletes) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("energy deficit" OR "caloric restriction") AND ("lean body mass" OR "fat-free mass") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
    ],
    "supplements": [
        '(creatine[MeSH] OR "creatine monohydrate") AND ("athletic performance" OR "exercise") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '(caffeine[MeSH] OR "caffeine supplementation") AND ("athletic performance" OR exercise) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
    ],
    "training": [
        '("resistance training"[MeSH] OR "strength training") AND (hypertrophy OR "lean body mass") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("training volume" OR "weekly sets") AND ("muscle hypertrophy" OR strength) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
    ],
    "conditioning": [
        '("endurance training" OR "aerobic exercise"[MeSH]) AND ("VO2 max" OR "cardiorespiratory fitness") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("high-intensity interval training"[MeSH] OR HIIT) AND ("aerobic capacity" OR "endurance performance") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
    ],
    "recovery": [
        '("sleep"[MeSH] OR "sleep quality") AND (athletes OR "athletic performance") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("cold water immersion" OR "cryotherapy"[MeSH] OR sauna) AND ("muscle recovery" OR "exercise recovery") AND ("meta-analysis"[pt] OR "systematic review"[pt])',
    ],
    "behavioral": [
        '("exercise adherence" OR "physical activity adherence") AND ("behavior change" OR motivation) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
        '("goal setting" OR "self-monitoring" OR "habit formation") AND ("physical activity" OR exercise) AND ("meta-analysis"[pt] OR "systematic review"[pt])',
    ],
}


def build_query(base: str, since: int) -> str:
    return f'({base}) AND ("{since}"[dp]:"2030"[dp])'


def _email() -> str:
    return os.environ.get("HCC_CONTACT_EMAIL", "devin@zerosumsolutions.com")


def _esearch(query: str) -> list[str]:
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
        + urlencode({"db": "pubmed", "term": query, "retmode": "json",
                     "retmax": "20", "tool": "hcc-compiler", "email": _email()})
    )
    data = _get_json(url)
    return data.get("esearchresult", {}).get("idlist", [])


def _summary(pmid: str) -> dict:
    from hcc_compiler.citation_gate.lookup import fetch_pubmed_abstract, fetch_pubmed_by_pmid
    r = fetch_pubmed_by_pmid(pmid)
    abstract = fetch_pubmed_abstract(pmid)
    return {
        "pmid": pmid, "doi": r.doi, "title": r.title,
        "year": r.year, "journal": r.journal, "abstract": abstract,
    }


def run_harvest(domain: str, since: int) -> list[dict]:
    queries = DOMAIN_QUERIES[domain]
    seen: set[str] = set()
    out: list[dict] = []
    for base in queries:
        for pmid in _esearch(build_query(base, since)):
            if pmid in seen:
                continue
            seen.add(pmid)
            out.append(_summary(pmid))
    return out
