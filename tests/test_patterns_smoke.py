"""T10: End-to-end patterns smoke — 6 retrieval probes + 6 derive probes.

Builds a SQLite index from the real 179-atom library using a cross-session-
deterministic bag-of-words fake embedder (hashlib SHA-256, NOT built-in hash()),
then issues 6 hand-crafted domain-filtered queries and asserts each top-1 result
falls in an acceptable set computed programmatically from the live library claims.

Also exercises derive_pattern() for each of the 6 domains by mocking call_llm
and asserting that ≥1 RecommendationPattern YAML is emitted per domain into a
tmp library dir (never touching the real library/patterns/ or library/queue/).

Design notes
------------
- Queries use domain= filtering to avoid cross-domain false positives from the
  sparse bag-of-words fake embedder.
- Acceptable sets are computed from the live library using the *primary* topic
  keyword(s) for each probe (e.g. any training atom with "hiit" in its claim).
  This is intentionally broader than requiring full semantic match — a bag-of-words
  cosine model will top-rank any atom in the domain that shares the primary keyword.
- Derive tests copy the real atoms into a tmp dir, build a real index there, then
  run derive_patterns.main() with sys.argv patched so no files touch the repo.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
LIBRARY_ROOT = REPO_ROOT / "library"

sys.path.insert(0, str(REPO_ROOT / "src"))

from hcc_compiler.build_index import build_index
from hcc_compiler.llm.embed_client import EmbedRequest
from hcc_compiler.llm.anthropic_client import LLMRequest
import hcc_compiler.retrieve as retrieve


# ---------------------------------------------------------------------------
# Fake embedder — cross-session deterministic via hashlib SHA-256
# ---------------------------------------------------------------------------

_DIM = 4096


def _fake_embed(req: EmbedRequest) -> list[float]:
    """Bag-of-words cosine-compatible fake.

    Deterministic across Python sessions because it uses hashlib (SHA-256),
    NOT the built-in hash() which depends on PYTHONHASHSEED.

    Word overlap between query and atom claim => shared non-zero dimensions =>
    cosine > 0.  Identical texts => cosine = 1.
    """
    tokens = re.findall(r"[a-z0-9]+", req.text.lower())
    vec = [0.0] * _DIM
    for t in tokens:
        if len(t) < 3:
            continue  # skip very-short stopword-ish tokens
        digest = hashlib.sha256(t.encode()).digest()
        idx = int.from_bytes(digest[:8], "big") % _DIM
        vec[idx] += 1.0
    return vec


# ---------------------------------------------------------------------------
# Helpers: compute acceptable sets from live library YAML claims
# ---------------------------------------------------------------------------

def _claims_in(domain: str) -> dict[str, str]:
    """Map atom_id -> lowercased claim for all atoms in *domain*."""
    d = LIBRARY_ROOT / "atoms" / domain
    result: dict[str, str] = {}
    for f in sorted(d.glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        atom_id = data.get("id", f.stem)
        result[atom_id] = data.get("claim", "").lower()
    return result


def _acceptable_protein_older_adults() -> set[str]:
    """Any nutrition atom whose claim mentions 'protein'."""
    claims = _claims_in("nutrition")
    return {aid for aid, claim in claims.items() if "protein" in claim}


def _acceptable_creatine_safety() -> set[str]:
    """Any supplements atom whose claim mentions 'creatine'."""
    claims = _claims_in("supplements")
    return {aid for aid, claim in claims.items() if "creatine" in claim}


def _acceptable_hiit_cardiac() -> set[str]:
    """Any training atom whose claim mentions HIIT (various spellings)."""
    claims = _claims_in("training")
    return {
        aid
        for aid, claim in claims.items()
        if "hiit" in claim
        or "high-intensity interval" in claim
        or "high intensity interval" in claim
    }


def _acceptable_sleep_banking() -> set[str]:
    """Any recovery atom whose claim mentions 'sleep'."""
    claims = _claims_in("recovery")
    return {aid for aid, claim in claims.items() if "sleep" in claim}


def _acceptable_habit_physical_activity() -> set[str]:
    """Any behavioral atom whose claim mentions 'physical activity' or 'exercise'."""
    claims = _claims_in("behavioral")
    return {
        aid
        for aid, claim in claims.items()
        if "physical activity" in claim or "exercise" in claim
    }


def _acceptable_vo2max_endurance() -> set[str]:
    """Any conditioning atom whose claim mentions VO2max, endurance, or aerobic."""
    claims = _claims_in("conditioning")
    return {
        aid
        for aid, claim in claims.items()
        if any(w in claim for w in ("vo2max", "vo2 max", "endurance", "aerobic"))
    }


# ---------------------------------------------------------------------------
# Session-scoped fixture: build index once into tmp SQLite
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def indexed_db(tmp_path_factory) -> Path:
    db = tmp_path_factory.mktemp("smoke_db") / "library.db"
    with patch("hcc_compiler.build_index.embed", side_effect=_fake_embed):
        build_index(LIBRARY_ROOT, db)
    return db


# ---------------------------------------------------------------------------
# Parametrized helper
# ---------------------------------------------------------------------------

def _top1(probe: str, domain: str, db: Path) -> str:
    with patch("hcc_compiler.retrieve.embed", side_effect=_fake_embed):
        results = retrieve.query(probe, k=5, domain=domain, db_path=db)
    assert results, f"No results returned for probe: {probe!r} (domain={domain})"
    return results[0][0]


# ---------------------------------------------------------------------------
# Probe tests
# ---------------------------------------------------------------------------

def test_probe_protein_older_adults(indexed_db):
    """Probe: 'protein dose for older adults' → top-1 must be a nutrition protein atom."""
    acceptable = _acceptable_protein_older_adults()
    assert acceptable, "No nutrition atoms mention protein — library may have changed"
    top1 = _top1("protein dose for older adults", "nutrition", indexed_db)
    assert top1 in acceptable, (
        f"top-1={top1!r} not in acceptable={acceptable}"
    )


def test_probe_creatine_safety_markers(indexed_db):
    """Probe: 'creatine safety markers' → top-1 must be a creatine supplements atom."""
    acceptable = _acceptable_creatine_safety()
    assert acceptable, "No supplements atoms mention creatine — library may have changed"
    top1 = _top1("creatine safety markers", "supplements", indexed_db)
    assert top1 in acceptable, (
        f"top-1={top1!r} not in acceptable={acceptable}"
    )


def test_probe_hiit_cardiac_rehab(indexed_db):
    """Probe: 'HIIT cardiac rehab' → top-1 must be a training HIIT atom."""
    acceptable = _acceptable_hiit_cardiac()
    assert acceptable, "No training atoms mention HIIT — library may have changed"
    top1 = _top1("HIIT cardiac rehab", "training", indexed_db)
    assert top1 in acceptable, (
        f"top-1={top1!r} not in acceptable={acceptable}"
    )


def test_probe_sleep_banking_athletes(indexed_db):
    """Probe: 'sleep banking for athletes' → top-1 must be a recovery sleep atom."""
    acceptable = _acceptable_sleep_banking()
    assert acceptable, "No recovery atoms mention sleep — library may have changed"
    top1 = _top1("sleep banking for athletes", "recovery", indexed_db)
    assert top1 in acceptable, (
        f"top-1={top1!r} not in acceptable={acceptable}"
    )


def test_probe_habit_formation_physical_activity(indexed_db):
    """Probe: 'habit formation physical activity' → top-1 must be a behavioral exercise/PA atom."""
    acceptable = _acceptable_habit_physical_activity()
    assert acceptable, "No behavioral atoms mention physical activity or exercise — library may have changed"
    top1 = _top1("habit formation physical activity", "behavioral", indexed_db)
    assert top1 in acceptable, (
        f"top-1={top1!r} not in acceptable={acceptable}"
    )


def test_probe_vo2max_endurance(indexed_db):
    """Probe: 'VO2max endurance' → top-1 must be a conditioning aerobic/endurance atom."""
    acceptable = _acceptable_vo2max_endurance()
    assert acceptable, "No conditioning atoms mention VO2max/endurance/aerobic — library may have changed"
    top1 = _top1("VO2max endurance", "conditioning", indexed_db)
    assert top1 in acceptable, (
        f"top-1={top1!r} not in acceptable={acceptable}"
    )


# ---------------------------------------------------------------------------
# Pattern derivation tests — mocked call_llm, isolated tmp library
# ---------------------------------------------------------------------------

# Domain-to-prefix map mirrors models.DOMAIN_PREFIX
_DOMAIN_PREFIX = {
    "nutrition": "NUT",
    "supplements": "SUP",
    "training": "TRA",
    "conditioning": "CON",
    "recovery": "REC",
    "behavioral": "BEH",
}

_DOMAINS = list(_DOMAIN_PREFIX.keys())


def _make_canned_pattern(domain: str) -> str:
    """Return a canned JSON string that derive_pattern will accept for *domain*."""
    prefix = _DOMAIN_PREFIX[domain]
    return json.dumps({
        "id": f"RP-{prefix}-test-pattern-smoke",
        "domain": domain,
        "pattern": f"Canned {domain} pattern for smoke test.",
        "parameterization": "Dose: standard; Duration: 8–12 wk.",
        "backing_atom_ids": [],      # will be overwritten by derive_pattern
        "falsification_signal": "No measurable outcome change at 12 wk.",
        "safety_bounds": "No known contraindications in healthy adults.",
        "applies_because": "Canned smoke-test value.",
        "doesnt_apply_if": "Canned smoke-test exclusion.",
        "tier": "routine",
        "approval": "smoke-test",
        "version": "0.0.0-smoke",
    })


def _fake_call_llm(req: LLMRequest) -> str:
    """Return a canned pattern JSON matching the domain mentioned in user_prompt."""
    for domain in _DOMAINS:
        if f"domain={domain}" in req.user_prompt:
            return _make_canned_pattern(domain)
    # Fallback: derive from the first atom id prefix (EA-NUT-… etc.)
    for prefix, domain in {v: k for k, v in _DOMAIN_PREFIX.items()}.items():
        if f"EA-{prefix}-" in req.user_prompt:
            return _make_canned_pattern(domain)
    return _make_canned_pattern("nutrition")


@pytest.fixture(scope="session")
def derive_tmp_library(tmp_path_factory) -> tuple[Path, Path]:
    """Copy real library atoms into a tmp dir and build a real index there.

    Returns (tmp_library_root, tmp_db_path).  The copy is isolated so derive
    tests never write into the repo's library/patterns/ or library/queue/.
    """
    tmp_lib = tmp_path_factory.mktemp("derive_lib")
    # Copy atoms tree + VERSION file (build_index requires it).
    shutil.copytree(LIBRARY_ROOT / "atoms", tmp_lib / "atoms")
    shutil.copy2(LIBRARY_ROOT / "VERSION", tmp_lib / "VERSION")
    # Build the index into the tmp dir.
    tmp_db = tmp_lib / "library.db"
    with patch("hcc_compiler.build_index.embed", side_effect=_fake_embed):
        build_index(tmp_lib, tmp_db)
    return tmp_lib, tmp_db


@pytest.mark.parametrize("domain", _DOMAINS)
def test_derive_pattern_per_domain(domain, derive_tmp_library):
    """derive_pattern emits ≥1 RecommendationPattern YAML for every domain.

    Uses a mocked call_llm so no real LLM call is made.  Writes only to the
    isolated tmp library — the real library/patterns/ and library/queue/ are
    never touched.
    """
    import scripts.curation.derive_patterns as dp

    tmp_lib, tmp_db = derive_tmp_library

    with (
        patch("hcc_compiler.patterns.derive.call_llm", side_effect=_fake_call_llm),
        patch("hcc_compiler.build_index.embed", side_effect=_fake_embed),
        patch(
            "sys.argv",
            [
                "derive_patterns.py",
                "--library", str(tmp_lib),
                "--db", str(tmp_db),
                "--min-atoms", "1",
            ],
        ),
    ):
        dp.main()

    prefix = _DOMAIN_PREFIX[domain]
    expected_id = f"RP-{prefix}-test-pattern-smoke"
    expected_fname = f"{expected_id}.yaml"

    patterns_dir = tmp_lib / "patterns" / domain
    queue_dir = tmp_lib / "queue"

    admitted = patterns_dir.exists() and (patterns_dir / expected_fname).exists()
    queued = queue_dir.exists() and (queue_dir / expected_fname).exists()

    assert admitted or queued, (
        f"No pattern YAML found for domain={domain!r}: "
        f"checked {patterns_dir / expected_fname} and {queue_dir / expected_fname}"
    )
