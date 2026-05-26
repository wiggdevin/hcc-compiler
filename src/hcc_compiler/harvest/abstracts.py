"""Load harvested source texts from disk for downstream verification.

The harvest stage writes one JSON file per domain run to ``harvest-output/``,
each containing a list of candidate dicts. Each candidate carries at least
an ``abstract`` (PubMed efetch) and — when the article has been deposited
in PubMed Central — a ``full_text`` (PMC efetch JATS body, joined paragraph
text). The Layer-2 faithfulness check substring-matches the locator quote
against this text, so the longer the text, the more atoms can clear the
gate.

``load_source_texts()`` returns ``full_text`` when present, else the
abstract. ``load_abstracts()`` is preserved as a backward-compatible alias.
"""
from __future__ import annotations

import json
from pathlib import Path


def load_source_texts(harvest_dir: str | Path) -> dict[str, str]:
    """Return a mapping from DOI **and** PMID to the candidate's best
    available source text.

    Both identifiers map to the same string when both are present, so callers
    can look up a citation by whichever id form it has. Preference order:

        1. ``candidate["full_text"]`` (PMC JATS body when deposited)
        2. ``candidate["abstract"]`` (PubMed efetch)
        3. nothing — entry skipped

    Missing identifiers are silently skipped.
    """
    root = Path(harvest_dir)
    out: dict[str, str] = {}
    if not root.is_dir():
        return out
    for path in sorted(root.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, list):
            continue
        for entry in data:
            if not isinstance(entry, dict):
                continue
            source = entry.get("full_text") or entry.get("abstract")
            if not source:
                continue
            doi = entry.get("doi")
            pmid = entry.get("pmid")
            if doi:
                out[str(doi)] = source
            if pmid:
                out[str(pmid)] = source
    return out


def load_abstracts(harvest_dir: str | Path) -> dict[str, str]:
    """Backward-compatible alias. Returns full_text-or-abstract per id.

    Kept so existing callers continue to work after the rename to
    ``load_source_texts``.
    """
    return load_source_texts(harvest_dir)
