# HCC Redesign · SP1 · Plan 2 — Curation Pipeline MVP (Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Plan 1's hard lessons apply: workers MUST pass `-c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins"` on every commit, and MUST NOT `git add` untracked files outside the explicit task file list.

**Goal:** Build the offline curation pipeline MVP — a deterministic citation gate (Layer 1 existence + Layer 2 faithfulness) plus harvest, LLM-extract, verify, and tier-routing scripts that turn published literature into validated `EvidenceAtom` YAML records ready for `library/`.

**Architecture (per `docs/specs/sp1-evidence-library-design.md` §3):**
```
PubMed/Crossref ──▶ harvest ──▶ extract (LLM) ──▶ draft.yaml ──▶ verify (deterministic gate) ──▶ route
                                                                                                  │
                                                                                  ┌───────────────┴────────────┐
                                                                                  ▼                            ▼
                                                                       library/atoms/<domain>/         library/queue/
                                                                       (routine + full PASS only)      (high-impact OR <PASS)
```

**Tech stack (locked from Plan 1):** Python 3.11, pydantic v2, PyYAML, SQLite stdlib, pytest. **Zero new runtime deps.** stdlib `urllib.request`, `difflib.SequenceMatcher`, `json`, `re`, `unittest.mock`.

**LLM route:** Z.AI GLM via anthropic-compatible endpoint (`https://api.z.ai/api/anthropic`). Token resolved from `zsvault get zai_api_key` → exported as `ANTHROPIC_AUTH_TOKEN` at run time. Tests use a fake transport; never hit the wire unless `HCC_LIVE_LLM=1`.

---

### Task 1: Title-similarity primitive

**Files:**
- Create: `src/hcc_compiler/citation_gate/__init__.py` (empty)
- Create: `src/hcc_compiler/citation_gate/text.py`
- Create: `tests/citation_gate/__init__.py` (empty)
- Create: `tests/citation_gate/test_text.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/citation_gate/test_text.py
from hcc_compiler.citation_gate.text import title_similarity, normalize_title


def test_identical_titles_score_one():
    assert title_similarity("Foo Bar", "Foo Bar") == 1.0


def test_casing_and_punctuation_ignored():
    a = "Dose-response relationship between RT volume and hypertrophy."
    b = "dose response relationship between rt volume and hypertrophy"
    assert title_similarity(a, b) >= 0.95


def test_minor_word_difference_above_threshold():
    a = "International Society of Sports Nutrition position stand: protein and exercise"
    b = "ISSN Position Stand: Protein and Exercise"
    # Different forms, but same content — should clear the 0.70 gate.
    assert title_similarity(a, b) >= 0.70


def test_unrelated_titles_below_threshold():
    a = "Effects of creatine supplementation on muscle"
    b = "Quantum entanglement in superconductors"
    assert title_similarity(a, b) < 0.50


def test_normalize_strips_punctuation_and_lowercases():
    assert normalize_title("Foo, Bar! Baz?") == "foo bar baz"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/projects/hcc-compiler && . .venv/bin/activate && pytest tests/citation_gate/test_text.py -q`
Expected: FAIL with `ModuleNotFoundError: hcc_compiler.citation_gate.text`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/hcc_compiler/citation_gate/text.py
from __future__ import annotations
import re
from difflib import SequenceMatcher

_PUNCT_RE = re.compile(r"[^a-z0-9\s]")
_WS_RE = re.compile(r"\s+")


def normalize_title(s: str) -> str:
    s = s.lower()
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/citation_gate/test_text.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" add src/hcc_compiler/citation_gate/__init__.py src/hcc_compiler/citation_gate/text.py tests/citation_gate/__init__.py tests/citation_gate/test_text.py
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" commit -m "feat(gate): title similarity primitive (difflib + normalize)"
```

---

### Task 2: Numeric-tolerance helper

**Files:**
- Modify (append): `src/hcc_compiler/citation_gate/text.py`
- Create: `tests/citation_gate/test_numbers.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/citation_gate/test_numbers.py
import pytest
from hcc_compiler.citation_gate.text import numbers_match, extract_numbers


def test_scalar_within_relative_tolerance():
    assert numbers_match(300.0, 300.0)
    assert numbers_match(305.0, 300.0)        # within 5% rel-tol
    assert not numbers_match(400.0, 300.0)    # outside


def test_range_membership_with_margin():
    assert numbers_match(2800.0, (2750.0, 2850.0))
    assert numbers_match(2750.0, (2750.0, 2850.0))
    assert not numbers_match(2000.0, (2750.0, 2850.0))


def test_percentage_mismatch_rejected():
    # spec example: "40% carbs" vs source "25%" — MAJOR
    assert not numbers_match(40.0, 25.0)


def test_extract_numbers_finds_floats_and_ints():
    assert extract_numbers("dose 2.5 g/kg/day for 12 weeks") == [2.5, 12.0]
    assert extract_numbers("no numbers here") == []


def test_extract_numbers_handles_ranges_and_commas():
    nums = extract_numbers("intake 2,800 kcal across 1.6-2.2 g/kg/d")
    # Range "1.6-2.2" yields both endpoints; thousands separators handled.
    assert 2800.0 in nums
    assert 1.6 in nums
    assert 2.2 in nums
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/citation_gate/test_numbers.py -q`
Expected: FAIL with `ImportError: cannot import name 'numbers_match'`.

- [ ] **Step 3: Append to `src/hcc_compiler/citation_gate/text.py`**

```python
# (append to text.py)
from __future__ import annotations
from typing import Iterable

_NUM_RE = re.compile(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?")


def extract_numbers(text: str) -> list[float]:
    out: list[float] = []
    for m in _NUM_RE.finditer(text):
        out.append(float(m.group(0).replace(",", "")))
    return out


def numbers_match(
    claim: float,
    source: float | tuple[float, float],
    rel_tol: float = 0.05,
) -> bool:
    """True if `claim` matches `source` within `rel_tol` relative tolerance.
    `source` may be a scalar or a (lo, hi) range tuple."""
    if isinstance(source, tuple):
        lo, hi = source
        margin = max(abs(lo), abs(hi)) * rel_tol
        return (lo - margin) <= claim <= (hi + margin)
    if source == 0:
        return claim == 0
    return abs(claim - source) <= abs(source) * rel_tol
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/citation_gate/test_numbers.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" add src/hcc_compiler/citation_gate/text.py tests/citation_gate/test_numbers.py
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" commit -m "feat(gate): numeric tolerance helper + number extraction"
```

---

### Task 3: PubMed + Crossref lookup clients (recorded fixtures)

**Files:**
- Create: `src/hcc_compiler/citation_gate/lookup.py`
- Create: `tests/citation_gate/test_lookup.py`
- Create: `tests/fixtures/__init__.py` (empty)
- Create: `tests/fixtures/crossref_jager2017.json`
- Create: `tests/fixtures/pubmed_jager2017_esummary.json`

- [ ] **Step 1: Capture fixtures (one-off, no commit yet)** — use the canned JSON below verbatim:

`tests/fixtures/crossref_jager2017.json`:
```json
{
  "status": "ok",
  "message": {
    "DOI": "10.1186/s12970-017-0177-8",
    "title": ["International Society of Sports Nutrition Position Stand: protein and exercise"],
    "issued": {"date-parts": [[2017, 6, 20]]},
    "container-title": ["Journal of the International Society of Sports Nutrition"],
    "author": [{"family": "Jäger", "given": "Ralf"}]
  }
}
```

`tests/fixtures/pubmed_jager2017_esummary.json`:
```json
{
  "header": {"type": "esummary", "version": "0.3"},
  "result": {
    "uids": ["28642676"],
    "28642676": {
      "uid": "28642676",
      "pubdate": "2017 Jun 20",
      "title": "International Society of Sports Nutrition Position Stand: protein and exercise.",
      "fulljournalname": "Journal of the International Society of Sports Nutrition",
      "elocationid": "doi: 10.1186/s12970-017-0177-8",
      "articleids": [{"idtype": "doi", "value": "10.1186/s12970-017-0177-8"}, {"idtype": "pmid", "value": "28642676"}]
    }
  }
}
```

- [ ] **Step 2: Write the failing test**

```python
# tests/citation_gate/test_lookup.py
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/citation_gate/test_lookup.py -q`
Expected: FAIL with `ModuleNotFoundError: hcc_compiler.citation_gate.lookup`.

- [ ] **Step 4: Write minimal implementation**

```python
# src/hcc_compiler/citation_gate/lookup.py
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/citation_gate/test_lookup.py -q`
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" add src/hcc_compiler/citation_gate/lookup.py tests/citation_gate/test_lookup.py tests/fixtures/__init__.py tests/fixtures/crossref_jager2017.json tests/fixtures/pubmed_jager2017_esummary.json
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" commit -m "feat(gate): PubMed + Crossref lookup clients (stdlib urllib)"
```

---

### Task 4: Layer 1 existence verifier + Citation.cited_title

**Files:**
- Modify: `src/hcc_compiler/models.py` (add `cited_title` to `Citation`)
- Create: `src/hcc_compiler/citation_gate/layer1.py`
- Create: `tests/citation_gate/test_layer1.py`

- [ ] **Step 1: Extend the `Citation` model**

Add a new optional field `cited_title: str | None = None` to `Citation` in `src/hcc_compiler/models.py`. Keep the existing fields and ordering. (Optional default → no migration needed for Plan-1 seed YAML.)

```python
# In src/hcc_compiler/models.py, modify Citation:
class Citation(BaseModel):
    id: str
    locator_quote: str
    existence: str
    faithfulness: str
    cited_title: str | None = None  # NEW: the title the citation claims, used for L1 DOI_MISMATCH detection
```

- [ ] **Step 2: Write the failing test**

```python
# tests/citation_gate/test_layer1.py
from unittest.mock import patch

from hcc_compiler.models import Citation
from hcc_compiler.citation_gate.layer1 import verify_existence
from hcc_compiler.citation_gate.lookup import LookupResult


JAGER = LookupResult(
    title="International Society of Sports Nutrition Position Stand: protein and exercise",
    year=2017,
    doi="10.1186/s12970-017-0177-8",
    pmid="28642676",
    journal="Journal of the International Society of Sports Nutrition",
)

DIFFERENT_PAPER = LookupResult(
    title="Quantum entanglement in superconductors",
    year=2017,
    doi="10.1186/s12970-017-0177-8",
    pmid=None,
    journal="Random Journal",
)


def _cite(**kwargs) -> Citation:
    base = dict(
        id="10.1186/s12970-017-0177-8",
        locator_quote="…",
        existence="VERIFIED",
        faithfulness="VERIFIED",
        cited_title="International Society of Sports Nutrition Position Stand: protein and exercise",
    )
    base.update(kwargs)
    return Citation(**base)


def test_verified_when_doi_resolves_to_matching_title():
    with patch("hcc_compiler.citation_gate.layer1.resolve_doi", return_value=JAGER):
        outcome = verify_existence(_cite())
    assert outcome == "VERIFIED"


def test_doi_mismatch_when_resolved_title_diverges():
    with patch("hcc_compiler.citation_gate.layer1.resolve_doi", return_value=DIFFERENT_PAPER):
        outcome = verify_existence(_cite())
    assert outcome == "DOI_MISMATCH"


def test_unverifiable_when_lookup_returns_none():
    with patch("hcc_compiler.citation_gate.layer1.resolve_doi", side_effect=Exception("boom")):
        outcome = verify_existence(_cite())
    assert outcome == "UNVERIFIABLE"


def test_unverifiable_when_cited_title_missing():
    """Without a claimed title we cannot run the DOI_MISMATCH check."""
    outcome = verify_existence(_cite(cited_title=None))
    assert outcome == "UNVERIFIABLE"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/citation_gate/test_layer1.py -q`
Expected: FAIL with `ModuleNotFoundError: hcc_compiler.citation_gate.layer1`.

- [ ] **Step 4: Write minimal implementation**

```python
# src/hcc_compiler/citation_gate/layer1.py
from __future__ import annotations
from hcc_compiler.models import Citation
from hcc_compiler.citation_gate.lookup import resolve_doi
from hcc_compiler.citation_gate.text import title_similarity

EXISTENCE_OUTCOMES = {"VERIFIED", "PLAUSIBLE", "UNVERIFIABLE", "DOI_MISMATCH", "FABRICATED"}

_TITLE_GATE = 0.70


def verify_existence(citation: Citation) -> str:
    if not citation.cited_title:
        return "UNVERIFIABLE"
    if "/" not in citation.id:
        return "UNVERIFIABLE"
    try:
        resolved = resolve_doi(citation.id)
    except Exception:
        return "UNVERIFIABLE"
    if not resolved.title:
        return "UNVERIFIABLE"
    sim = title_similarity(resolved.title, citation.cited_title)
    if sim >= _TITLE_GATE:
        return "VERIFIED"
    return "DOI_MISMATCH"
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/citation_gate/test_layer1.py -q`
Expected: PASS (4 passed).

- [ ] **Step 6: Commit**

```bash
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" add src/hcc_compiler/models.py src/hcc_compiler/citation_gate/layer1.py tests/citation_gate/test_layer1.py
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" commit -m "feat(gate): Layer 1 existence verifier + Citation.cited_title"
```

---

### Task 5: Layer 2 faithfulness verifier

**Files:**
- Create: `src/hcc_compiler/citation_gate/layer2.py`
- Create: `tests/citation_gate/test_layer2.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/citation_gate/test_layer2.py
from hcc_compiler.models import Citation
from hcc_compiler.citation_gate.layer2 import verify_faithfulness


def _cite(quote: str) -> Citation:
    return Citation(
        id="10.1186/s12970-017-0177-8",
        locator_quote=quote,
        existence="VERIFIED",
        faithfulness="VERIFIED",
        cited_title="ISSN Position Stand: protein and exercise",
    )


SOURCE = (
    "Higher protein intakes (2.3-3.1 g/kg/d) may be needed to maximize the retention of "
    "lean body mass in resistance-trained subjects during hypocaloric periods."
)


def test_verified_when_quote_in_source_and_numbers_match():
    quote = "Higher protein intakes (2.3-3.1 g/kg/d) may be needed"
    claim = "Protein intakes of 2.3-3.1 g/kg/day may be needed"
    assert verify_faithfulness(claim, _cite(quote), source_text=SOURCE) == "VERIFIED"


def test_unsupported_when_quote_not_in_source():
    quote = "completely different sentence not present anywhere"
    claim = "Protein intakes of 2.3-3.1 g/kg/day may be needed"
    assert verify_faithfulness(claim, _cite(quote), source_text=SOURCE) == "UNSUPPORTED"


def test_major_distortion_when_claim_number_off():
    quote = "Higher protein intakes (2.3-3.1 g/kg/d) may be needed"
    claim = "Protein intakes of 5.0 g/kg/day may be needed"  # wildly different
    assert verify_faithfulness(claim, _cite(quote), source_text=SOURCE) == "MAJOR_DISTORTION"


def test_access_limited_when_source_text_none():
    quote = "Higher protein intakes"
    assert verify_faithfulness("anything", _cite(quote), source_text=None) == "ACCESS_LIMITED"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/citation_gate/test_layer2.py -q`
Expected: FAIL with `ModuleNotFoundError: hcc_compiler.citation_gate.layer2`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/hcc_compiler/citation_gate/layer2.py
from __future__ import annotations
from hcc_compiler.models import Citation
from hcc_compiler.citation_gate.text import extract_numbers, normalize_title, numbers_match

FAITHFULNESS_VERDICTS = {
    "VERIFIED", "MINOR_DISTORTION", "MAJOR_DISTORTION", "UNSUPPORTED", "ACCESS_LIMITED",
}


def _contains_quote(source_norm: str, quote_norm: str) -> bool:
    return quote_norm in source_norm if quote_norm else False


def verify_faithfulness(
    claim_text: str,
    citation: Citation,
    source_text: str | None = None,
) -> str:
    if source_text is None:
        return "ACCESS_LIMITED"

    source_norm = normalize_title(source_text)
    quote_norm = normalize_title(citation.locator_quote or "")

    if not _contains_quote(source_norm, quote_norm):
        return "UNSUPPORTED"

    claim_nums = extract_numbers(claim_text)
    source_nums = extract_numbers(source_text)

    if not claim_nums:
        return "VERIFIED"

    # Each claim number must match at least one source number within tolerance.
    for cn in claim_nums:
        if not any(numbers_match(cn, sn) for sn in source_nums):
            return "MAJOR_DISTORTION"
    return "VERIFIED"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/citation_gate/test_layer2.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" add src/hcc_compiler/citation_gate/layer2.py tests/citation_gate/test_layer2.py
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" commit -m "feat(gate): Layer 2 faithfulness verifier (locator + numeric tolerance)"
```

---

### Task 6: `verify_atom` orchestrator + CLI

**Files:**
- Modify: `src/hcc_compiler/citation_gate/__init__.py` (add orchestrator export)
- Create: `src/hcc_compiler/citation_gate/orchestrator.py`
- Create: `scripts/curation/verify.py`
- Create: `tests/citation_gate/test_verify_atom.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/citation_gate/test_verify_atom.py
from datetime import date
from unittest.mock import patch

from hcc_compiler.models import EvidenceAtom, Citation
from hcc_compiler.citation_gate.lookup import LookupResult
from hcc_compiler.citation_gate.orchestrator import verify_atom


GOOD_LOOKUP = LookupResult(
    title="International Society of Sports Nutrition Position Stand: protein and exercise",
    year=2017,
    doi="10.1186/s12970-017-0177-8",
    pmid="28642676",
    journal="J ISSN",
)


def _atom() -> EvidenceAtom:
    return EvidenceAtom(
        id="EA-NUT-9999",
        domain="nutrition",
        claim="Protein intakes of 2.3-3.1 g/kg/day may be needed.",
        evidence_level="L1",
        citations=[Citation(
            id="10.1186/s12970-017-0177-8",
            locator_quote="Higher protein intakes (2.3-3.1 g/kg/d) may be needed",
            existence="VERIFIED",
            faithfulness="VERIFIED",
            cited_title="International Society of Sports Nutrition Position Stand: protein and exercise",
        )],
        population_applicability=dict(
            age="18-55", sex="both", training_status="resistance-trained",
            dose_magnitude="2.3-3.1 g/kg/d", duration="8-16 wk",
        ),
        effect="…",
        tier="high-impact",
        approval="Dev Wiggins 2026-05-22",
        library_version="0.1.0",
        last_reviewed=date(2026, 5, 22),
        expiry=date(2027, 5, 22),
    )


def test_verify_atom_pass_with_notes_when_no_source_text():
    """No source_text → Layer 2 returns ACCESS_LIMITED → overall PASS_WITH_NOTES."""
    with patch("hcc_compiler.citation_gate.layer1.resolve_doi", return_value=GOOD_LOOKUP):
        result = verify_atom(_atom())
    assert result["overall"] == "PASS_WITH_NOTES"
    assert result["citations"][0]["existence"] == "VERIFIED"
    assert result["citations"][0]["faithfulness"] == "ACCESS_LIMITED"


def test_verify_atom_pass_when_source_text_supports_claim():
    src = "Higher protein intakes (2.3-3.1 g/kg/d) may be needed to maximize the retention of lean body mass."
    with patch("hcc_compiler.citation_gate.layer1.resolve_doi", return_value=GOOD_LOOKUP):
        result = verify_atom(_atom(), source_texts={"10.1186/s12970-017-0177-8": src})
    assert result["overall"] == "PASS"
    assert result["citations"][0]["existence"] == "VERIFIED"
    assert result["citations"][0]["faithfulness"] == "VERIFIED"


def test_verify_atom_fail_on_doi_mismatch():
    bad = LookupResult(title="Quantum entanglement", year=2017, doi="…", pmid=None, journal="…")
    with patch("hcc_compiler.citation_gate.layer1.resolve_doi", return_value=bad):
        result = verify_atom(_atom())
    assert result["overall"] == "FAIL"
    assert result["citations"][0]["existence"] == "DOI_MISMATCH"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/citation_gate/test_verify_atom.py -q`
Expected: FAIL with `ModuleNotFoundError: hcc_compiler.citation_gate.orchestrator`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/hcc_compiler/citation_gate/orchestrator.py
from __future__ import annotations
from typing import Mapping
from hcc_compiler.models import EvidenceAtom
from hcc_compiler.citation_gate.layer1 import verify_existence
from hcc_compiler.citation_gate.layer2 import verify_faithfulness

_FAIL_EXISTENCE = {"DOI_MISMATCH", "FABRICATED"}
_FAIL_FAITHFULNESS = {"MAJOR_DISTORTION", "UNSUPPORTED"}
_NOTE_VALUES = {"ACCESS_LIMITED", "MINOR_DISTORTION", "PLAUSIBLE", "UNVERIFIABLE"}


def verify_atom(atom: EvidenceAtom, source_texts: Mapping[str, str] | None = None) -> dict:
    source_texts = source_texts or {}
    citation_results = []
    has_fail = False
    has_note = False
    for c in atom.citations:
        existence = verify_existence(c)
        faithfulness = verify_faithfulness(atom.claim, c, source_text=source_texts.get(c.id))
        citation_results.append({
            "id": c.id,
            "existence": existence,
            "faithfulness": faithfulness,
        })
        if existence in _FAIL_EXISTENCE or faithfulness in _FAIL_FAITHFULNESS:
            has_fail = True
        if existence in _NOTE_VALUES or faithfulness in _NOTE_VALUES:
            has_note = True

    if has_fail:
        overall = "FAIL"
    elif has_note:
        overall = "PASS_WITH_NOTES"
    else:
        overall = "PASS"

    return {"atom_id": atom.id, "overall": overall, "citations": citation_results}
```

```python
# scripts/curation/verify.py
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import yaml  # noqa: E402
from hcc_compiler.models import EvidenceAtom  # noqa: E402
from hcc_compiler.citation_gate.orchestrator import verify_atom  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: verify.py <draft.yaml | dir>", file=sys.stderr)
        return 2
    target = Path(sys.argv[1])
    paths = sorted(target.rglob("*.yaml")) if target.is_dir() else [target]
    out_dir = Path("verify-output")
    out_dir.mkdir(parents=True, exist_ok=True)
    any_fail = False
    for p in paths:
        atom = EvidenceAtom.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")))
        result = verify_atom(atom)
        (out_dir / f"{atom.id}.json").write_text(json.dumps(result, indent=2))
        print(f"{atom.id}: {result['overall']}")
        if result["overall"] == "FAIL":
            any_fail = True
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Also expose the orchestrator from the package init:

```python
# src/hcc_compiler/citation_gate/__init__.py
from hcc_compiler.citation_gate.orchestrator import verify_atom  # noqa: F401
```

- [ ] **Step 4: Run test + run CLI smoke**

Run: `pytest tests/citation_gate/test_verify_atom.py -q`
Expected: PASS (3 passed).

(Optional live smoke — skip if Crossref isn't reachable; tests don't require it.)
`HCC_CONTACT_EMAIL=devin@zerosumsolutions.com python scripts/curation/verify.py library/atoms` → should print three lines (one per seed atom) with `PASS_WITH_NOTES` (no source text supplied).

- [ ] **Step 5: Commit**

```bash
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" add src/hcc_compiler/citation_gate/__init__.py src/hcc_compiler/citation_gate/orchestrator.py scripts/curation/verify.py tests/citation_gate/test_verify_atom.py
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" commit -m "feat(gate): verify_atom orchestrator + verify.py CLI"
```

---

### Task 7: Per-domain harvest query registry + CLI

**Files:**
- Create: `src/hcc_compiler/harvest/__init__.py` (empty)
- Create: `src/hcc_compiler/harvest/queries.py`
- Create: `scripts/curation/harvest.py`
- Create: `tests/harvest/__init__.py` (empty)
- Create: `tests/harvest/test_harvest.py`
- Create: `tests/fixtures/pubmed_esearch_nutrition.json`

- [ ] **Step 1: Capture fixture**

`tests/fixtures/pubmed_esearch_nutrition.json`:
```json
{
  "header": {"type": "esearch", "version": "0.3"},
  "esearchresult": {
    "count": "2",
    "retmax": "10",
    "idlist": ["28642676", "28615996"]
  }
}
```

- [ ] **Step 2: Write the failing test**

```python
# tests/harvest/test_harvest.py
from pathlib import Path
from unittest.mock import patch

from hcc_compiler.harvest.queries import build_query, DOMAIN_QUERIES, run_harvest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_known_domains_registered():
    for d in ("nutrition", "supplements", "training"):
        assert d in DOMAIN_QUERIES
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/harvest/test_harvest.py -q`
Expected: FAIL with `ModuleNotFoundError: hcc_compiler.harvest.queries`.

- [ ] **Step 4: Write minimal implementation**

```python
# src/hcc_compiler/harvest/queries.py
from __future__ import annotations
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

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
    req = Request(url, headers={"User-Agent": f"hcc-compiler/0.1 (mailto:{_email()})"})
    with urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("esearchresult", {}).get("idlist", [])


def _summary(pmid: str) -> dict:
    from hcc_compiler.citation_gate.lookup import fetch_pubmed_by_pmid
    r = fetch_pubmed_by_pmid(pmid)
    return {
        "pmid": pmid, "doi": r.doi, "title": r.title,
        "year": r.year, "journal": r.journal, "abstract": "",
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
```

```python
# scripts/curation/harvest.py
import argparse
import json
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hcc_compiler.harvest.queries import DOMAIN_QUERIES, run_harvest  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--domain", required=True, choices=sorted(DOMAIN_QUERIES.keys()))
    p.add_argument("--since", type=int, default=2022)
    args = p.parse_args()
    results = run_harvest(args.domain, args.since)
    out_dir = Path("harvest-output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.domain}-{date.today().isoformat()}.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"Wrote {len(results)} candidates to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/harvest/test_harvest.py -q`
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" add src/hcc_compiler/harvest/__init__.py src/hcc_compiler/harvest/queries.py scripts/curation/harvest.py tests/harvest/__init__.py tests/harvest/test_harvest.py tests/fixtures/pubmed_esearch_nutrition.json
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" commit -m "feat(harvest): per-domain PubMed harvest registry + CLI"
```

---

### Task 8: Z.AI GLM client (anthropic-compatible)

**Files:**
- Create: `src/hcc_compiler/llm/__init__.py` (empty)
- Create: `src/hcc_compiler/llm/glm_client.py`
- Create: `tests/llm/__init__.py` (empty)
- Create: `tests/llm/test_glm_client.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/llm/test_glm_client.py
import json
from unittest.mock import patch
from hcc_compiler.llm.glm_client import call_llm, GLMRequest


def test_call_llm_posts_anthropic_messages_payload(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")
    captured = {}

    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def read(self_inner):
            return json.dumps({
                "id": "msg_1",
                "content": [{"type": "text", "text": "ok"}],
                "model": "glm-4.6",
            }).encode("utf-8")

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _Resp()

    with patch("hcc_compiler.llm.glm_client.urlopen", new=fake_urlopen):
        out = call_llm(GLMRequest(
            model="glm-4.6",
            system="you are helpful",
            user_prompt="say ok",
            max_tokens=64,
        ))

    assert captured["url"].rstrip("/").endswith("/v1/messages")
    assert captured["headers"].get("X-api-key") == "test-token" \
        or captured["headers"].get("Authorization") == "Bearer test-token"
    assert captured["body"]["model"] == "glm-4.6"
    assert captured["body"]["max_tokens"] == 64
    assert captured["body"]["messages"][0]["role"] == "user"
    assert out == "ok"


def test_call_llm_raises_without_token(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    import pytest
    with pytest.raises(RuntimeError):
        call_llm(GLMRequest(model="glm-4.6", system="", user_prompt="x", max_tokens=1))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/llm/test_glm_client.py -q`
Expected: FAIL with `ModuleNotFoundError: hcc_compiler.llm.glm_client`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/hcc_compiler/llm/glm_client.py
from __future__ import annotations
import json
import os
from dataclasses import dataclass
from urllib.request import Request, urlopen


@dataclass
class GLMRequest:
    model: str
    system: str
    user_prompt: str
    max_tokens: int = 1024
    temperature: float = 0.2


def call_llm(req: GLMRequest, timeout: float = 90.0) -> str:
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not token:
        raise RuntimeError("ANTHROPIC_AUTH_TOKEN not set — refusing live LLM call")
    base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic").rstrip("/")
    url = f"{base}/v1/messages"
    body = {
        "model": req.model,
        "max_tokens": req.max_tokens,
        "temperature": req.temperature,
        "system": req.system,
        "messages": [{"role": "user", "content": req.user_prompt}],
    }
    payload = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "X-api-key": token,
        "Authorization": f"Bearer {token}",
    }
    request = Request(url, data=payload, headers=headers, method="POST")
    with urlopen(request, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
    return "".join(parts).strip()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/llm/test_glm_client.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" add src/hcc_compiler/llm/__init__.py src/hcc_compiler/llm/glm_client.py tests/llm/__init__.py tests/llm/test_glm_client.py
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" commit -m "feat(extract): Z.AI GLM anthropic-compatible client (stdlib urllib)"
```

---

### Task 9: Extract step + CLI

**Files:**
- Create: `src/hcc_compiler/extract.py`
- Create: `src/hcc_compiler/extract_prompt.md`
- Create: `scripts/curation/extract.py`
- Create: `tests/test_extract.py`
- Create: `tests/fixtures/llm_extract_nutrition.json`

- [ ] **Step 1: Capture fixture (canned LLM response)**

`tests/fixtures/llm_extract_nutrition.json`:
```json
{
  "id": "EA-NUT-0042",
  "domain": "nutrition",
  "claim": "Protein intakes of 2.3-3.1 g/kg/day may be needed to maximize retention of lean body mass in resistance-trained subjects during hypocaloric periods.",
  "evidence_level": "L1",
  "citations": [{
    "id": "10.1186/s12970-017-0177-8",
    "locator_quote": "Higher protein intakes (2.3-3.1 g/kg/d) may be needed to maximize the retention of lean body mass in resistance-trained subjects during hypocaloric periods.",
    "existence": "UNVERIFIABLE",
    "faithfulness": "ACCESS_LIMITED",
    "cited_title": "International Society of Sports Nutrition Position Stand: protein and exercise"
  }],
  "population_applicability": {
    "age": "18-55", "sex": "both", "training_status": "resistance-trained",
    "dose_magnitude": "2.3-3.1 g/kg/d during hypocaloric periods", "duration": "8-16 wk"
  },
  "effect": "Maximizes retention of lean body mass during an energy deficit vs lower intakes.",
  "contraindications": ["CKD or other renal contraindication"],
  "tier": "high-impact",
  "approval": "auto",
  "library_version": "0.1.0",
  "last_reviewed": "2026-05-22",
  "expiry": "2027-05-22"
}
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_extract.py
import json
from pathlib import Path
from unittest.mock import patch

from hcc_compiler.extract import extract_atom
from hcc_compiler.models import EvidenceAtom

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_extract_atom_round_trips_through_model():
    canned = (FIXTURES / "llm_extract_nutrition.json").read_text()
    candidate = {
        "pmid": "28642676",
        "doi": "10.1186/s12970-017-0177-8",
        "title": "International Society of Sports Nutrition Position Stand: protein and exercise",
        "year": 2017,
        "abstract": "Higher protein intakes (2.3-3.1 g/kg/d) may be needed…",
        "journal": "J ISSN",
    }

    with patch("hcc_compiler.extract.call_llm", return_value=canned):
        draft = extract_atom(candidate)
    atom = EvidenceAtom.model_validate(draft)
    assert atom.id.startswith("EA-")
    assert atom.tier in ("high-impact", "routine")
    assert atom.citations[0].id == candidate["doi"]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_extract.py -q`
Expected: FAIL with `ModuleNotFoundError: hcc_compiler.extract`.

- [ ] **Step 4: Write prompt template + implementation**

`src/hcc_compiler/extract_prompt.md`:
```markdown
You are an evidence-extraction assistant for the HCC compiler. Given one
research paper candidate (title, abstract, DOI/PMID, year, journal), produce
a single JSON object matching the `EvidenceAtom` schema below.

Rules:
- Use ONE atom per paper.
- The `claim` must be supportable by a verbatim passage from the abstract.
- The `locator_quote` in `citations[0]` MUST be a verbatim passage from the
  abstract — copy it character-for-character. No paraphrasing.
- Set `citations[0].cited_title` to the paper's title verbatim.
- Set `existence` to "UNVERIFIABLE" and `faithfulness` to "ACCESS_LIMITED" —
  these are filled in by the deterministic verify step downstream. Do NOT
  pre-fill them as VERIFIED.
- `approval` MUST be the string "auto"; the human-PR queue assigns approval
  later.
- `tier` is "high-impact" if the claim governs safety, doses, calorie/macro
  targets, or contraindications; otherwise "routine".
- Use `evidence_level` L1 for meta-analyses / systematic reviews, L2 for RCTs,
  L3 for cohort/observational, L4 for expert opinion.

Schema (output JSON only, no markdown fences):
{
  "id": "EA-<DOMAIN3>-<4-DIGIT>",
  "domain": "<nutrition|supplements|training|conditioning|recovery|behavioral>",
  "claim": "<one-sentence verifiable claim>",
  "evidence_level": "L1|L2|L3|L4",
  "citations": [{
    "id": "<DOI or PMID>",
    "locator_quote": "<verbatim abstract passage>",
    "existence": "UNVERIFIABLE",
    "faithfulness": "ACCESS_LIMITED",
    "cited_title": "<paper title verbatim>"
  }],
  "population_applicability": {"age":"…","sex":"…","training_status":"…","dose_magnitude":"…","duration":"…"},
  "effect": "…",
  "contraindications": [],
  "tier": "high-impact|routine",
  "approval": "auto",
  "library_version": "0.1.0",
  "last_reviewed": "YYYY-MM-DD",
  "expiry": "YYYY-MM-DD"
}
```

```python
# src/hcc_compiler/extract.py
from __future__ import annotations
import json
import re
from pathlib import Path
from hcc_compiler.llm.glm_client import GLMRequest, call_llm

_PROMPT_PATH = Path(__file__).with_name("extract_prompt.md")
_JSON_RE = re.compile(r"\{[\s\S]*\}")


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def extract_atom(candidate: dict, model: str = "glm-4.6") -> dict:
    user_prompt = (
        "CANDIDATE:\n"
        f"title: {candidate.get('title')}\n"
        f"doi: {candidate.get('doi')}\n"
        f"pmid: {candidate.get('pmid')}\n"
        f"year: {candidate.get('year')}\n"
        f"journal: {candidate.get('journal')}\n"
        f"abstract: {candidate.get('abstract')}\n"
    )
    raw = call_llm(GLMRequest(
        model=model,
        system=_load_prompt(),
        user_prompt=user_prompt,
        max_tokens=2048,
        temperature=0.2,
    ))
    match = _JSON_RE.search(raw)
    if not match:
        raise ValueError(f"LLM did not return JSON: {raw[:200]}…")
    return json.loads(match.group(0))
```

```python
# scripts/curation/extract.py
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import yaml  # noqa: E402
from hcc_compiler.extract import extract_atom  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: extract.py <harvest-output.json>", file=sys.stderr)
        return 2
    candidates = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out_dir = Path("draft-output")
    out_dir.mkdir(parents=True, exist_ok=True)
    for cand in candidates:
        try:
            draft = extract_atom(cand)
        except Exception as e:
            print(f"skip {cand.get('pmid')}: {e}", file=sys.stderr)
            continue
        (out_dir / f"{draft['id']}.yaml").write_text(yaml.safe_dump(draft, sort_keys=False))
        print(f"wrote {draft['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_extract.py -q`
Expected: PASS (1 passed).

- [ ] **Step 6: Commit**

```bash
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" add src/hcc_compiler/extract.py src/hcc_compiler/extract_prompt.md scripts/curation/extract.py tests/test_extract.py tests/fixtures/llm_extract_nutrition.json
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" commit -m "feat(extract): LLM extract step + prompt template + CLI"
```

---

### Task 10: Tier & route CLI

**Files:**
- Create: `src/hcc_compiler/route.py`
- Create: `scripts/curation/route.py`
- Create: `tests/test_route.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_route.py
import json
from pathlib import Path

import yaml
from hcc_compiler.route import route_draft


def _atom_yaml(atom_id: str, tier: str) -> dict:
    return {
        "id": atom_id, "domain": "nutrition",
        "claim": "x", "evidence_level": "L1",
        "citations": [{"id": "10.x/y", "locator_quote": "q", "existence": "VERIFIED", "faithfulness": "VERIFIED", "cited_title": "t"}],
        "population_applicability": {"age": "18-55", "sex": "both", "training_status": "trained", "dose_magnitude": "x", "duration": "x"},
        "effect": "x", "tier": tier, "approval": "auto",
        "library_version": "0.1.0", "last_reviewed": "2026-05-22", "expiry": "2027-05-22",
    }


def test_routine_pass_goes_to_library_atoms(tmp_path):
    draft = tmp_path / "draft-output"
    verify = tmp_path / "verify-output"
    library = tmp_path / "library"
    draft.mkdir(); verify.mkdir()
    (draft / "EA-NUT-0099.yaml").write_text(yaml.safe_dump(_atom_yaml("EA-NUT-0099", "routine")))
    (verify / "EA-NUT-0099.json").write_text(json.dumps({"atom_id": "EA-NUT-0099", "overall": "PASS"}))
    out = route_draft(draft, verify, library)
    assert (library / "atoms" / "nutrition" / "EA-NUT-0099.yaml").exists()
    assert out["EA-NUT-0099"] == "admitted"


def test_high_impact_pass_goes_to_queue(tmp_path):
    draft = tmp_path / "draft-output"
    verify = tmp_path / "verify-output"
    library = tmp_path / "library"
    draft.mkdir(); verify.mkdir()
    (draft / "EA-NUT-0100.yaml").write_text(yaml.safe_dump(_atom_yaml("EA-NUT-0100", "high-impact")))
    (verify / "EA-NUT-0100.json").write_text(json.dumps({"atom_id": "EA-NUT-0100", "overall": "PASS"}))
    out = route_draft(draft, verify, library)
    assert (library / "queue" / "EA-NUT-0100.yaml").exists()
    assert out["EA-NUT-0100"] == "queued"


def test_fail_verdict_routes_to_queue_even_for_routine(tmp_path):
    draft = tmp_path / "draft-output"
    verify = tmp_path / "verify-output"
    library = tmp_path / "library"
    draft.mkdir(); verify.mkdir()
    (draft / "EA-NUT-0101.yaml").write_text(yaml.safe_dump(_atom_yaml("EA-NUT-0101", "routine")))
    (verify / "EA-NUT-0101.json").write_text(json.dumps({"atom_id": "EA-NUT-0101", "overall": "FAIL"}))
    out = route_draft(draft, verify, library)
    assert (library / "queue" / "EA-NUT-0101.yaml").exists()
    assert out["EA-NUT-0101"] == "queued"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_route.py -q`
Expected: FAIL with `ModuleNotFoundError: hcc_compiler.route`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/hcc_compiler/route.py
from __future__ import annotations
import json
from pathlib import Path
import yaml


def route_draft(draft_dir: Path, verify_dir: Path, library_root: Path) -> dict[str, str]:
    """Move each draft YAML into library/atoms/<domain>/ (admitted) or library/queue/ (queued)."""
    decisions: dict[str, str] = {}
    for draft_path in sorted(draft_dir.glob("*.yaml")):
        atom = yaml.safe_load(draft_path.read_text(encoding="utf-8"))
        atom_id = atom["id"]
        verify_path = verify_dir / f"{atom_id}.json"
        if not verify_path.exists():
            decisions[atom_id] = "skipped-no-verify"
            continue
        verdict = json.loads(verify_path.read_text(encoding="utf-8")).get("overall")
        tier = atom.get("tier")
        if tier == "routine" and verdict == "PASS":
            dest_dir = library_root / "atoms" / atom["domain"]
            decisions[atom_id] = "admitted"
        else:
            dest_dir = library_root / "queue"
            decisions[atom_id] = "queued"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_dir.joinpath(f"{atom_id}.yaml").write_text(yaml.safe_dump(atom, sort_keys=False))
    return decisions
```

```python
# scripts/curation/route.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hcc_compiler.route import route_draft  # noqa: E402


def main() -> int:
    draft_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("draft-output")
    verify_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("verify-output")
    library_root = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("library")
    decisions = route_draft(draft_dir, verify_dir, library_root)
    for aid, decision in decisions.items():
        print(f"{aid}: {decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_route.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" add src/hcc_compiler/route.py scripts/curation/route.py tests/test_route.py
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" commit -m "feat(route): tier-aware draft routing CLI"
```

---

### Task 11: Pipeline smoke + Makefile targets + .gitignore

**Files:**
- Modify: `Makefile` (add `harvest`, `extract`, `verify`, `route`, `curate`, `curate-smoke` targets)
- Modify: `.gitignore` (add `harvest-output/`, `draft-output/`, `verify-output/`)
- Create: `tests/test_pipeline_smoke.py`

- [ ] **Step 1: Append to `.gitignore`**

```
harvest-output/
draft-output/
verify-output/
```

- [ ] **Step 2: Extend `Makefile`**

```makefile
harvest:
	HCC_LIVE_HTTP=1 python scripts/curation/harvest.py --domain nutrition --since 2022

extract:
	HCC_LIVE_LLM=1 python scripts/curation/extract.py $(shell ls -t harvest-output/*.json | head -1)

verify:
	python scripts/curation/verify.py draft-output

route:
	python scripts/curation/route.py draft-output verify-output library

curate: harvest extract verify route

curate-smoke:
	python -m pytest tests/test_pipeline_smoke.py -q
```

- [ ] **Step 3: Write the failing test (end-to-end smoke against fixtures)**

```python
# tests/test_pipeline_smoke.py
import json
import shutil
from pathlib import Path
from unittest.mock import patch

import yaml
from hcc_compiler.extract import extract_atom
from hcc_compiler.citation_gate.orchestrator import verify_atom
from hcc_compiler.models import EvidenceAtom
from hcc_compiler.route import route_draft

FIXTURES = Path(__file__).parent / "fixtures"


def test_pipeline_routes_fixture_candidate_into_queue(tmp_path):
    candidate = {
        "pmid": "28642676",
        "doi": "10.1186/s12970-017-0177-8",
        "title": "International Society of Sports Nutrition Position Stand: protein and exercise",
        "year": 2017,
        "abstract": "Higher protein intakes (2.3-3.1 g/kg/d) may be needed…",
        "journal": "JISSN",
    }
    canned_llm = (FIXTURES / "llm_extract_nutrition.json").read_text()

    draft_dir = tmp_path / "draft-output"
    verify_dir = tmp_path / "verify-output"
    library_root = tmp_path / "library"
    draft_dir.mkdir(); verify_dir.mkdir()

    with patch("hcc_compiler.extract.call_llm", return_value=canned_llm):
        draft = extract_atom(candidate)
    atom = EvidenceAtom.model_validate(draft)
    (draft_dir / f"{atom.id}.yaml").write_text(yaml.safe_dump(draft, sort_keys=False))

    # verify atom (no source text → PASS_WITH_NOTES; existence cannot run live without network → UNVERIFIABLE)
    from hcc_compiler.citation_gate import layer1 as l1
    with patch.object(l1, "resolve_doi", side_effect=Exception("offline")):
        result = verify_atom(atom)
    (verify_dir / f"{atom.id}.json").write_text(json.dumps(result))

    decisions = route_draft(draft_dir, verify_dir, library_root)
    # High-impact tier → always queued.
    assert decisions[atom.id] == "queued"
    assert (library_root / "queue" / f"{atom.id}.yaml").exists()
```

- [ ] **Step 4: Run smoke + Plan-1 invariants**

```bash
cd ~/projects/hcc-compiler && . .venv/bin/activate
make curate-smoke   # the new test
make check          # Plan-1 invariants still hold (validate library, build, all tests)
```

Expected: both exit 0; total test count should be Plan-1 (15) + Plan-2 tests.

- [ ] **Step 5: Commit**

```bash
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" add Makefile .gitignore tests/test_pipeline_smoke.py
git -c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins" commit -m "feat(curation): pipeline smoke + Makefile curate targets"
```

---

## What this plan delivers

A working offline curation pipeline that takes published papers from PubMed/Crossref through LLM-drafted atoms through a deterministic two-layer citation gate to either auto-admit (routine + full PASS) or PR-queue (high-impact or below full PASS). The gate is now real, deterministic, and unit-tested — no more "verified" claims based on model judgment alone.

## Plan-2-deferred (Plan 3 candidates)

- Cross-model critique (different model family re-checks faithfulness / population applicability).
- Pattern derivation from approved atoms (`RecommendationPattern` generators).
- Embeddings store + retrieval API for SP2.
- Release-tag automation + scheduled re-harvest routine.

## End-to-end live spot-check (manual, after /goal completes)

```bash
cd ~/projects/hcc-compiler && . .venv/bin/activate
export ANTHROPIC_AUTH_TOKEN=$(zsvault get zai_api_key)
export ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
export HCC_CONTACT_EMAIL=devin@zerosumsolutions.com
HCC_LIVE_HTTP=1 python scripts/curation/harvest.py --domain nutrition --since 2024
HCC_LIVE_LLM=1 python scripts/curation/extract.py harvest-output/nutrition-*.json
python scripts/curation/verify.py draft-output
python scripts/curation/route.py draft-output verify-output library
git status   # expect new files under library/queue/ (high-impact atoms)
```
