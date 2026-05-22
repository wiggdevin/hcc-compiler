from __future__ import annotations

from hcc_compiler.models import Domain
from hcc_compiler.sp2.pack import EvidencePack, DomainBlock, PatternMatch, AtomMatch

_DOMAIN_ORDER = [
    Domain.NUTRITION,
    Domain.TRAINING,
    Domain.CONDITIONING,
    Domain.SUPPLEMENTS,
    Domain.RECOVERY,
    Domain.BEHAVIORAL,
]


def _render_pattern(pattern: PatternMatch, block: DomainBlock) -> list[str]:
    lines: list[str] = []
    lines.append(f"### Pattern: {pattern.pattern_id} (sim={pattern.similarity:.2f})")
    lines.append("")
    lines.append(f"**Applies because:** {pattern.applies_because}")
    lines.append(f"**Parameterization:** {pattern.parameterization}")
    lines.append(f"**Safety bounds:** {pattern.safety_bounds}")
    lines.append("")

    # Top 3 backing atoms by population_match_score
    backing_set = set(pattern.backing_atom_ids)
    backing_atoms = [a for a in block.atoms if a.atom_id in backing_set]
    backing_atoms.sort(key=lambda a: a.population_match_score, reverse=True)
    top3 = backing_atoms[:3]

    lines.append("**Backing evidence (top 3 by population match):**")
    for atom in top3:
        citation_id = atom.citations[0].id if atom.citations else ""
        lines.append(f"- {atom.claim} ([{citation_id}])")
    lines.append("")

    for warning in pattern.warnings:
        lines.append(f"> ⚠ {warning}")
    if pattern.warnings:
        lines.append("")

    return lines


def _render_domain(domain: Domain, block: DomainBlock | None) -> list[str]:
    lines: list[str] = []
    lines.append(f"## {domain.value.title()}")
    lines.append("")

    if block is None or (not block.patterns and not block.atoms):
        lines.append("_(no matches)_")
        lines.append("")
        return lines

    # Track atom_ids shown as backing so we don't repeat them below
    shown_as_backing: set[str] = set()

    # Patterns sorted by similarity desc
    sorted_patterns = sorted(block.patterns, key=lambda p: p.similarity, reverse=True)
    for pattern in sorted_patterns:
        lines.extend(_render_pattern(pattern, block))
        shown_as_backing.update(pattern.backing_atom_ids)

    # Remaining atoms (not shown as backing), top 5 by population_match_score
    remaining = [a for a in block.atoms if a.atom_id not in shown_as_backing]
    remaining.sort(key=lambda a: a.population_match_score, reverse=True)
    for atom in remaining[:5]:
        citation_id = atom.citations[0].id if atom.citations else ""
        lines.append(
            f"- **{atom.atom_id}** (sim {atom.similarity:.2f}, pop-match {atom.population_match_score:.2f}): "
            f"{atom.claim} ([{citation_id}])"
        )
    if remaining:
        lines.append("")

    return lines


def render_markdown(pack: EvidencePack) -> str:
    lines: list[str] = []

    # Header
    lines.append(f"# Personalized Evidence Pack — {pack.client_id}")
    lines.append("")
    lines.append(f"- Compiled at: {pack.compiled_at.isoformat()}")
    lines.append(f"- Library version: {pack.library_version}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Safety preflight — library-wide preemptive contraindication hits
    preemptive = pack.compile_metadata.preemptive_contraindications
    if preemptive:
        lines.append("## Safety preflight")
        lines.append("")
        for hit in preemptive:
            lines.append(
                f"- **{hit.record_id}** ({hit.record_type}): "
                f"{hit.claim_or_summary} — matched: *{hit.matched_needle}*"
            )
        lines.append("")

    # Domain sections
    for domain in _DOMAIN_ORDER:
        block = pack.domain_recommendations.get(domain)
        lines.extend(_render_domain(domain, block))

    # Metadata footer
    meta = pack.compile_metadata
    total_queries = sum(len(qs) for qs in meta.queries_issued.values())
    lines.append("## Metadata")
    lines.append("")
    lines.append(f"- top_k_per_domain: {meta.top_k_per_domain}")
    lines.append(f"- applicability_threshold: {meta.applicability_threshold}")
    lines.append(f"- total queries issued: {total_queries}")
    lines.append(f"- total contraindication hits: {len(meta.contraindication_hits)}")
    lines.append("")

    return "\n".join(lines)
