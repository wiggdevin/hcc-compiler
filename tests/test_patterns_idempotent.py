"""T11: Idempotency test for derive_patterns.main().

Runs derive_patterns.main() twice against the same isolated tmp library with
mocked embed() and call_llm().  Asserts that the second run writes zero new
pattern files (every cluster is already covered by the first run's output).

This serves as the offline proxy for SC11's "make patterns && git status
--porcelain empty after second run" acceptance criterion.  Live verification
requires HCC_LIVE_LLM=1 + HCC_LIVE_EMBED=1 and is documented as a manual
spot-check in docs/plans/sp1-plan3-patterns-and-embeddings.md.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from hcc_compiler.llm.embed_client import EmbedRequest  # noqa: E402
from hcc_compiler.llm.anthropic_client import LLMRequest  # noqa: E402
from hcc_compiler.build_index import build_index  # noqa: E402

# ---------------------------------------------------------------------------
# Fake embedder (same bag-of-words approach as smoke test)
# ---------------------------------------------------------------------------

_DIM = 64  # smaller dim is fine for a unit test


def _fake_embed(req: EmbedRequest) -> list[float]:
    tokens = re.findall(r"[a-z0-9]+", req.text.lower())
    vec = [0.0] * _DIM
    for t in tokens:
        if len(t) < 3:
            continue
        digest = hashlib.sha256(t.encode()).digest()
        idx = int.from_bytes(digest[:8], "big") % _DIM
        vec[idx] += 1.0
    return vec


# ---------------------------------------------------------------------------
# Fake LLM: returns a fixed canned pattern JSON for nutrition domain
# ---------------------------------------------------------------------------

_CANNED_PATTERN = json.dumps({
    "id": "RP-NUT-idempotent-test-pattern",
    "domain": "nutrition",
    "pattern": "Test pattern for idempotency verification.",
    "parameterization": "Dose: standard; Duration: 8 wk.",
    "backing_atom_ids": [],
    "falsification_signal": "No measurable change at 8 wk.",
    "safety_bounds": "No known contraindications in healthy adults.",
    "applies_because": "Test applies-because value.",
    "doesnt_apply_if": "Test doesnt-apply-if value.",
    "tier": "routine",
    "approval": "test",
    "version": "0.0.0-test",
})


def _fake_call_llm(req: LLMRequest) -> str:
    return _CANNED_PATTERN


# ---------------------------------------------------------------------------
# Fixture: isolated tmp library with 3 nutrition atoms + built index
# ---------------------------------------------------------------------------

_ATOM_TEMPLATE = """\
id: EA-NUT-990{n}
domain: nutrition
claim: "Protein intake of {n}g/kg improves lean mass retention in older adults."
evidence_level: L1
citations:
  - id: "10.0000/idempotent.test.0{n}"
    locator_quote: "Test quote {n}."
    existence: VERIFIED
    faithfulness: VERIFIED
population_applicability:
  age: "50-70"
  sex: both
  training_status: untrained
  dose_magnitude: "{n}g/kg/day"
  duration: "8 wk"
effect: "Improves lean mass retention."
contraindications:
  - "CKD"
tier: routine
approval: "test 2026-05-22"
library_version: "0.1.0"
last_reviewed: "2026-05-22"
expiry: "2027-05-22"
"""


@pytest.fixture()
def idempotent_library(tmp_path: Path) -> tuple[Path, Path]:
    """Create 3 nutrition atoms in a tmp library, build the index, return (lib, db)."""
    atoms_dir = tmp_path / "atoms" / "nutrition"
    atoms_dir.mkdir(parents=True)

    for n in range(1, 4):
        atom_text = _ATOM_TEMPLATE.format(n=n)
        (atoms_dir / f"EA-NUT-990{n}.yaml").write_text(atom_text, encoding="utf-8")

    # Write required VERSION file
    (tmp_path / "VERSION").write_text("test-idempotent\n", encoding="utf-8")

    db_path = tmp_path / "library.db"
    with patch("hcc_compiler.build_index.embed", side_effect=_fake_embed):
        build_index(tmp_path, db_path)

    return tmp_path, db_path


# ---------------------------------------------------------------------------
# Helper: count pattern files written across patterns/<domain>/ and queue/
# ---------------------------------------------------------------------------

def _count_pattern_files(library_root: Path) -> int:
    total = 0
    patterns_root = library_root / "patterns"
    if patterns_root.exists():
        total += sum(1 for _ in patterns_root.rglob("*.yaml"))
    queue_dir = library_root / "queue"
    if queue_dir.exists():
        total += sum(1 for _ in queue_dir.glob("*.yaml"))
    return total


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

def test_derive_patterns_idempotent(idempotent_library):
    """Second invocation of derive_patterns.main() writes zero new pattern files.

    This verifies that the _pattern_id_exists() collision check in
    derive_patterns.py causes every cluster to be skipped on repeat runs,
    and that the tally reflects skipped-existing for all non-trivial clusters.
    """
    import scripts.curation.derive_patterns as dp

    tmp_lib, tmp_db = idempotent_library

    shared_argv = [
        "derive_patterns.py",
        "--library", str(tmp_lib),
        "--db", str(tmp_db),
        "--min-atoms", "1",
    ]

    # --- First run ---
    with (
        patch("hcc_compiler.patterns.derive.call_llm", side_effect=_fake_call_llm),
        patch("sys.argv", shared_argv),
    ):
        tally1 = dp.main()

    count_after_run1 = _count_pattern_files(tmp_lib)
    assert count_after_run1 >= 1, "First run should have written at least 1 pattern file"

    # --- Second run ---
    with (
        patch("hcc_compiler.patterns.derive.call_llm", side_effect=_fake_call_llm),
        patch("sys.argv", shared_argv),
    ):
        tally2 = dp.main()

    count_after_run2 = _count_pattern_files(tmp_lib)

    # Core assertion: no new files written
    assert count_after_run2 == count_after_run1, (
        f"Second run wrote new files: before={count_after_run1}, after={count_after_run2}"
    )

    # Tally assertion: second run admitted/queued nothing new
    assert tally2.get("admitted", 0) == 0, (
        f"Second run admitted {tally2['admitted']} patterns — expected 0"
    )
    assert tally2.get("queued", 0) == 0, (
        f"Second run queued {tally2['queued']} patterns — expected 0"
    )

    # The clusters that were processed the first time should now be skipped-existing
    # (they may have been admitted or queued, not too-small)
    first_run_written = tally1.get("admitted", 0) + tally1.get("queued", 0)
    assert tally2.get("skipped-existing", 0) >= first_run_written, (
        f"Expected skipped-existing >= {first_run_written}, got {tally2.get('skipped-existing', 0)}"
    )
