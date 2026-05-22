"""End-to-end smoke tests against the real library.db — SC9.

Uses mocked embeddings so the test is deterministic (no Ollama required),
but asserts against the *real* atoms+patterns layout in the SQLite.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from hcc_compiler.sp2.compile import compile
from hcc_compiler.sp2.intake import load_intake
from hcc_compiler.sp2.render import render_markdown

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LIBRARY_DB = PROJECT_ROOT / "library.db"
INTAKES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "intakes"

# 768-dimensional fixed vector matching nomic-embed-text output size.
# All 1.0 → cosine similarity = 1.0 for any candidate with the same sign pattern,
# giving deterministic ranking by library content rather than embedding quality.
_FIXED_VEC = [1.0] * 768

PERSONAS = ["amy_runner", "carl_strength", "sam_recomp"]

_DOMAIN_HEADINGS = [
    "## Nutrition",
    "## Training",
    "## Conditioning",
    "## Supplements",
    "## Recovery",
    "## Behavioral",
]


# ---------------------------------------------------------------------------
# Library existence check
# ---------------------------------------------------------------------------

def test_library_db_exists() -> None:
    """library.db must exist at project root for smoke tests to run."""
    assert LIBRARY_DB.exists(), (
        f"library.db not found at {LIBRARY_DB}. "
        "Build it first: uv run python scripts/curation/build_index.py library library.db"
    )


# ---------------------------------------------------------------------------
# Parametrized smoke test — one per persona
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("persona", PERSONAS)
def test_persona_compiles_against_real_library(persona: str, tmp_path: Path) -> None:
    """Each persona intake compiles end-to-end against the real library.db.

    Assertions:
    1. No exceptions raised during compile() or render_markdown().
    2. >= 3 of 6 domains have >= 1 atom or pattern.
    3. Rendered markdown length > 500 characters (sanity check).
    4. All 6 domain ## headings are present in the rendered markdown.
    """
    if not LIBRARY_DB.exists():
        pytest.skip(f"library.db not found at {LIBRARY_DB} — cannot run smoke test")

    intake_path = INTAKES_DIR / f"intake_{persona}.yaml"
    assert intake_path.exists(), f"Intake fixture not found: {intake_path}"

    intake = load_intake(intake_path)

    # Patch embed at the import site inside hcc_compiler.retrieve so the test
    # is fully offline and deterministic.
    with patch("hcc_compiler.retrieve.embed") as mock_embed:
        mock_embed.return_value = _FIXED_VEC
        pack = compile(intake, LIBRARY_DB)

    # 1. Pack is returned without exceptions (implicit — we reached here).
    assert pack is not None
    assert pack.client_id == persona

    # 2. At least 3 of 6 domains have >= 1 atom or pattern.
    non_empty_domains = [
        domain
        for domain, block in pack.domain_recommendations.items()
        if block.atoms or block.patterns
    ]
    assert len(non_empty_domains) >= 3, (
        f"persona={persona}: only {len(non_empty_domains)} domains non-empty "
        f"(need >= 3). domains={[d.value for d in non_empty_domains]}"
    )

    # 3 & 4. Render markdown and check basic structure.
    md = render_markdown(pack)
    assert len(md) > 500, (
        f"persona={persona}: markdown too short ({len(md)} chars)"
    )
    for heading in _DOMAIN_HEADINGS:
        assert heading in md, (
            f"persona={persona}: missing domain heading '{heading}' in rendered markdown"
        )
