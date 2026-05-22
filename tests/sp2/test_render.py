"""Tests for sp2/render.py — render_markdown(pack: EvidencePack) -> str."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from hcc_compiler.models import Domain, EvidenceLevel, Citation
from hcc_compiler.sp2.pack import (
    AtomMatch,
    CompileMetadata,
    DomainBlock,
    EvidencePack,
    PatternMatch,
    PreemptiveHit,
)
from hcc_compiler.sp2.render import render_markdown


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _citation(doi: str = "10.1234/test.doi") -> Citation:
    return Citation(
        id=doi,
        locator_quote="verbatim passage",
        existence="VERIFIED",
        faithfulness="VERIFIED",
        cited_title="Test Paper",
    )


def _atom(atom_id: str, claim: str = "Test claim", pop_score: float = 0.8, sim: float = 0.75) -> AtomMatch:
    return AtomMatch(
        atom_id=atom_id,
        similarity=sim,
        claim=claim,
        citations=[_citation()],
        evidence_level=EvidenceLevel.L1,
        population_match_score=pop_score,
        warnings=[],
    )


def _pattern(
    pattern_id: str,
    backing_ids: list[str],
    sim: float = 0.84,
    warnings: list[str] | None = None,
) -> PatternMatch:
    return PatternMatch(
        pattern_id=pattern_id,
        similarity=sim,
        applies_because="Strong evidence for this population",
        parameterization="3×10 at 70% 1RM",
        safety_bounds="Stop if pain >3/10",
        backing_atom_ids=backing_ids,
        warnings=warnings or [],
    )


def _empty_meta() -> CompileMetadata:
    return CompileMetadata(
        top_k_per_domain=5,
        applicability_threshold=0.4,
        contraindication_hits=[],
        queries_issued={},
    )


def _pack(domain_recommendations: dict | None = None) -> EvidencePack:
    return EvidencePack(
        client_id="test-client",
        library_version="0.1.0",
        compiled_at=datetime(2026, 5, 22, 12, 0, 0, tzinfo=timezone.utc),
        domain_recommendations=domain_recommendations or {},
        compile_metadata=_empty_meta(),
    )


# ---------------------------------------------------------------------------
# Test: all 6 domain headings appear even if pack is empty
# ---------------------------------------------------------------------------

def test_all_six_domain_headings_in_empty_pack():
    md = render_markdown(_pack())
    for domain in Domain:
        assert f"## {domain.value.title()}" in md, f"Missing heading for {domain.value}"


def test_empty_pack_no_matches_placeholder():
    md = render_markdown(_pack())
    # Each empty domain should show the placeholder
    assert md.count("_(no matches)_") == 6


def test_empty_pack_renders_without_exception():
    # Should not raise
    md = render_markdown(_pack())
    assert isinstance(md, str)
    assert len(md) > 0


# ---------------------------------------------------------------------------
# Test: header content
# ---------------------------------------------------------------------------

def test_header_contains_client_id():
    md = render_markdown(_pack())
    assert "test-client" in md


def test_header_contains_library_version():
    md = render_markdown(_pack())
    assert "0.1.0" in md


# ---------------------------------------------------------------------------
# Test: inline citation format ([doi])
# ---------------------------------------------------------------------------

def test_inline_citation_format():
    atom = _atom("EA-NUT-0001", claim="Protein enhances MPS")
    atom.citations[0] = _citation("10.1234/some.doi")
    block = DomainBlock(atoms=[atom])
    md = render_markdown(_pack({Domain.NUTRITION: block}))
    assert "([10.1234/some.doi])" in md


def test_citation_inside_brackets():
    atom = _atom("EA-TRA-0001")
    atom.citations = [_citation("10.5678/training.doi")]
    block = DomainBlock(atoms=[atom])
    md = render_markdown(_pack({Domain.TRAINING: block}))
    assert "[10.5678/training.doi]" in md


# ---------------------------------------------------------------------------
# Test: warnings render with > blockquote prefix
# ---------------------------------------------------------------------------

def test_warnings_render_with_blockquote_prefix():
    p = _pattern("RP-NUT-protein", ["EA-NUT-0001"], warnings=["High protein risky for CKD"])
    atom = _atom("EA-NUT-0001")
    block = DomainBlock(patterns=[p], atoms=[atom])
    md = render_markdown(_pack({Domain.NUTRITION: block}))
    assert "> ⚠ High protein risky for CKD" in md


def test_multiple_warnings_each_get_blockquote():
    p = _pattern(
        "RP-NUT-protein",
        ["EA-NUT-0001"],
        warnings=["Warning one", "Warning two"],
    )
    atom = _atom("EA-NUT-0001")
    block = DomainBlock(patterns=[p], atoms=[atom])
    md = render_markdown(_pack({Domain.NUTRITION: block}))
    assert "> ⚠ Warning one" in md
    assert "> ⚠ Warning two" in md


# ---------------------------------------------------------------------------
# Test: creatine-style stress test — 47 backing atoms, expect exactly 3 rendered
# ---------------------------------------------------------------------------

def test_backing_atoms_capped_at_3_with_47_ids():
    """Pattern with 47 backing_atom_ids + 47 atoms in block.atoms — only top 3 rendered."""
    atom_ids = [f"EA-SUP-{i:04d}" for i in range(47)]
    # Vary population_match_score so top-3 is deterministic
    atoms = [
        _atom(aid, claim=f"Claim {i}", pop_score=round((47 - i) / 47, 3), sim=0.8)
        for i, aid in enumerate(atom_ids)
    ]
    pattern = _pattern("RP-SUP-creatine", atom_ids, sim=0.91)
    block = DomainBlock(patterns=[pattern], atoms=atoms)
    md = render_markdown(_pack({Domain.SUPPLEMENTS: block}))

    # Locate the backing-evidence section
    backing_start = md.find("**Backing evidence (top 3 by population match):**")
    assert backing_start != -1, "Backing evidence header not found"

    # Count bullet lines (- ) between backing header and next blank line / section
    section = md[backing_start:]
    # Find backing section lines up to the next blank line or pattern/section heading
    backing_lines = []
    in_backing = False
    for line in section.splitlines():
        if "**Backing evidence" in line:
            in_backing = True
            continue
        if in_backing:
            if line.startswith("- "):
                backing_lines.append(line)
            elif line == "" and backing_lines:
                # End of backing list
                break
            elif line.startswith("#") or line.startswith("**") or line.startswith(">"):
                break

    assert len(backing_lines) == 3, (
        f"Expected exactly 3 backing bullets, got {len(backing_lines)}: {backing_lines}"
    )


# ---------------------------------------------------------------------------
# Test: domain order (fixed: nutrition, training, conditioning, supplements, recovery, behavioral)
# ---------------------------------------------------------------------------

def test_domain_sections_in_fixed_order():
    expected = [
        "## Nutrition",
        "## Training",
        "## Conditioning",
        "## Supplements",
        "## Recovery",
        "## Behavioral",
    ]
    md = render_markdown(_pack())
    positions = [md.find(heading) for heading in expected]
    assert all(p != -1 for p in positions), "A domain heading is missing"
    assert positions == sorted(positions), "Domain headings not in expected order"


# ---------------------------------------------------------------------------
# Test: non-backing atoms appear below patterns
# ---------------------------------------------------------------------------

def test_non_backing_atoms_rendered_separately():
    p = _pattern("RP-NUT-protein", ["EA-NUT-0001"])
    backing = _atom("EA-NUT-0001")
    standalone = _atom("EA-NUT-0002", claim="Standalone atom claim")
    block = DomainBlock(patterns=[p], atoms=[backing, standalone])
    md = render_markdown(_pack({Domain.NUTRITION: block}))
    # Standalone should appear in the non-backing atom list
    assert "EA-NUT-0002" in md
    assert "Standalone atom claim" in md


def test_backing_atoms_not_duplicated_in_standalone_list():
    p = _pattern("RP-NUT-protein", ["EA-NUT-0001"])
    backing = _atom("EA-NUT-0001", claim="Backing claim")
    block = DomainBlock(patterns=[p], atoms=[backing])
    md = render_markdown(_pack({Domain.NUTRITION: block}))
    # EA-NUT-0001 should only appear once (in the backing section, not standalone list)
    # The standalone list format is "- **{atom_id}** ..."
    standalone_marker = "- **EA-NUT-0001**"
    assert standalone_marker not in md


# ---------------------------------------------------------------------------
# Test: metadata footer
# ---------------------------------------------------------------------------

def test_metadata_footer_present():
    meta = CompileMetadata(
        top_k_per_domain=7,
        applicability_threshold=0.5,
        contraindication_hits=["CKD vs creatine"],
        queries_issued={"nutrition": ["protein intake"], "training": ["resistance training"]},
    )
    pack = EvidencePack(
        client_id="meta-test",
        library_version="0.1.0",
        compiled_at=datetime(2026, 5, 22, tzinfo=timezone.utc),
        compile_metadata=meta,
    )
    md = render_markdown(pack)
    assert "## Metadata" in md
    assert "top_k_per_domain: 7" in md
    assert "applicability_threshold: 0.5" in md
    assert "total queries issued: 2" in md
    assert "total contraindication hits: 1" in md


def test_safety_preflight_section_renders():
    """When preemptive_contraindications is non-empty, '## Safety preflight'
    appears in the markdown BEFORE the first domain heading."""
    meta = CompileMetadata(
        top_k_per_domain=5,
        applicability_threshold=0.4,
        preemptive_contraindications=[
            PreemptiveHit(
                record_id="EA-NUT-9999",
                record_type="atom",
                claim_or_summary="Risky claim for nutrition",
                matched_needle="CKD or other renal contraindication",
            ),
        ],
    )
    pack = EvidencePack(
        client_id="preflight-test",
        library_version="0.1.0",
        compiled_at=datetime(2026, 5, 22, tzinfo=timezone.utc),
        compile_metadata=meta,
    )
    md = render_markdown(pack)
    assert "## Safety preflight" in md
    preflight_pos = md.find("## Safety preflight")
    first_domain_pos = md.find("## Nutrition")
    assert preflight_pos != -1 and first_domain_pos != -1
    assert preflight_pos < first_domain_pos
    assert "EA-NUT-9999" in md
    assert "CKD or other renal contraindication" in md


def test_safety_preflight_section_absent_when_no_preemptive_hits():
    """When preemptive_contraindications is empty, the section is omitted."""
    md = render_markdown(_pack())
    assert "## Safety preflight" not in md


def test_total_queries_sums_across_domains():
    meta = CompileMetadata(
        top_k_per_domain=5,
        applicability_threshold=0.4,
        queries_issued={
            "nutrition": ["q1", "q2", "q3"],
            "training": ["q4"],
            "supplements": ["q5", "q6"],
        },
    )
    pack = EvidencePack(
        client_id="sum-test",
        library_version="0.1.0",
        compiled_at=datetime(2026, 5, 22, tzinfo=timezone.utc),
        compile_metadata=meta,
    )
    md = render_markdown(pack)
    assert "total queries issued: 6" in md
