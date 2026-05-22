"""Load harvested abstracts from disk for downstream verification.

The harvest stage writes one JSON file per domain run to ``harvest-output/``,
each containing a list of candidate dicts (``pmid``, ``doi``, ``abstract``,
``title``, ...).  The Layer-2 faithfulness check in the citation gate needs
the abstract text keyed by whatever identifier the draft atom uses
(DOI *or* PMID), so this module flattens every JSON in a directory into one
``{identifier: abstract}`` dict.
"""
from __future__ import annotations

import json
from pathlib import Path


def load_abstracts(harvest_dir: str | Path) -> dict[str, str]:
    """Return a mapping from DOI **and** PMID to the candidate's abstract.

    Both identifiers point at the same string when both are present, so the
    caller can look up a citation by whichever id form it has.  Missing
    abstracts and missing identifiers are skipped silently.
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
            abstract = entry.get("abstract")
            if not abstract:
                continue
            doi = entry.get("doi")
            pmid = entry.get("pmid")
            if doi:
                out[str(doi)] = abstract
            if pmid:
                out[str(pmid)] = abstract
    return out
