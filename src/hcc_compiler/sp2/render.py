from __future__ import annotations

import re

from hcc_compiler.models import Domain
from hcc_compiler.sp2.intake import ClientIntake, Constraint
from hcc_compiler.sp2.pack import EvidencePack, DomainBlock, PatternMatch, AtomMatch

_DOMAIN_ORDER = [
    Domain.NUTRITION,
    Domain.TRAINING,
    Domain.CONDITIONING,
    Domain.SUPPLEMENTS,
    Domain.RECOVERY,
    Domain.BEHAVIORAL,
]


# Keyword groups for matching intake constraints against pattern parameterization
# rows. Used by _persona_row_extract and _for_this_client_annotation.
_TRAINING_STATUS_TO_KEYWORDS = {
    "untrained": ["untrained", "sedentary", "novice", "recreational lifters (less than 1"],
    "recreational": ["recreational lifters", "untrained or moderately trained", "recreational"],
    "trained": ["resistance-trained", "trained adults", "trained athletes", "trained individuals", "trained females"],
    "competitive": ["powerlifting-style", "competition", "advanced athletes", "athletes preparing"],
}
_AGE_KEYWORDS = {
    "older": ["older adults", "older trained adults", "50+", "≥60", "60+", "postmenopausal"],
    "youth": ["youth athletes", "adolescents", "12-18"],
}
_SEX_KEYWORDS_F = ["females", "trained females", "active females", "postmenopausal", "perinatal", "perimenopausal"]


# Constraint detail substrings -> short coaching annotation per pattern domain.
# When a constraint is detected, the renderer surfaces a "FOR THIS CLIENT" note
# alongside the matching pattern. Keep notes brief and actionable.
_CONSTRAINT_ANNOTATIONS: dict[str, dict[Domain, str]] = {
    "spinal fusion": {
        Domain.TRAINING: "Post-lumbar-fusion: cap heavy axial loading; bias toward machine-supported variants, trap-bar / front-loaded squat, single-leg work. Require clinical clearance before any top-set above 70% 1RM.",
    },
    "lumbar fusion": {
        Domain.TRAINING: "Post-lumbar-fusion: cap heavy axial loading; bias toward machine-supported variants, trap-bar / front-loaded squat, single-leg work. Require clinical clearance before any top-set above 70% 1RM.",
    },
    "post-lumbar-spinal-fusion": {
        Domain.TRAINING: "Post-lumbar-fusion: cap heavy axial loading; bias toward machine-supported variants, trap-bar / front-loaded squat, single-leg work. Require clinical clearance before any top-set above 70% 1RM.",
    },
    "low-back sensitivity": {
        Domain.TRAINING: "Low-back sensitivity: substitute trap-bar / front squat / SSB for conventional back squat; chest-supported rows; anti-extension + anti-rotation core 2x/wk. Avoid heavy axial loading when fatigued.",
    },
    "low-back": {
        Domain.TRAINING: "Low-back constraint: substitute trap-bar / front squat / SSB for conventional back squat; chest-supported rows; anti-extension + anti-rotation core 2x/wk.",
    },
    "patellar tendinopathy": {
        Domain.TRAINING: "Patellar tendinopathy: emphasize slow eccentric tempo (3-5s down) on lower-body work; avoid plyometric volume escalation until pain-free; consider isometric loading for rehab phases.",
    },
    "knee": {
        Domain.TRAINING: "Knee constraint: reduce impact volume; emphasize controlled eccentric tempo; avoid jumping volume escalation in tendinopathy contexts.",
    },
    "armour thyroid": {
        Domain.NUTRITION: "NDT (Armour Thyroid) timing: maintain ≥4 h food-drug separation around dose. Iron, calcium, soy, and high-fiber meals are the highest-impact interactants — schedule those 4+ h post-dose.",
    },
    "ndt": {
        Domain.NUTRITION: "NDT (Armour Thyroid) timing: maintain ≥4 h food-drug separation around dose. Iron, calcium, soy, and high-fiber meals are the highest-impact interactants — schedule those 4+ h post-dose.",
    },
    "ckd": {
        Domain.NUTRITION: "CKD: cap protein at 1.2-1.4 g/kg/day or per nephrology guidance; monitor eGFR + serum creatinine 4-6 weekly during deficit; avoid the 2.3-3.1 g/kg/day band entirely until clinical clearance.",
        Domain.SUPPLEMENTS: "CKD: do NOT initiate creatine loading without nephrology clearance and baseline + 4-week eGFR + serum creatinine; standard creatine doses generally safe in CKD 1-2 but require monitoring.",
    },
    "menstrual": {
        Domain.NUTRITION: "Cycle-aware nutrition: follicular phase = baseline calories + standard macros; luteal phase = +150-300 kcal mostly carb (palatable carb timed around training); monitor for late-luteal craving + fluid retention.",
    },
    "luteal": {
        Domain.NUTRITION: "Cycle-aware nutrition: luteal phase += 150-300 kcal mostly carb, timed around training; monitor body composition only at consistent cycle phase (mid-follicular preferred).",
    },
    "compressed eating window": {
        Domain.NUTRITION: "Compressed eating window: front-load protein to 0.4-0.5 g/kg/meal across the window; consume the largest carbohydrate-protein meal within 90 min post-training; rule out chronic underfueling by tracking energy availability (target ≥40 kcal/kg FFM/day for active females).",
    },
    "underfueling": {
        Domain.NUTRITION: "Underfueling flag: target energy availability ≥40 kcal/kg FFM/day for active female athletes; lean mass loss despite high volume is a primary EA marker. Audit pre/intra/post-training carbohydrate exposure first.",
    },
    "metabolic inefficiency": {
        Domain.NUTRITION: "Measured metabolic inefficiency: derive all caloric prescriptions from MEASURED maintenance (effective TDEE), NOT predicted TDEE. Re-measure RMR every 8-12 weeks during sustained deficit.",
    },
    "mushroom allergy": {
        Domain.NUTRITION: "Mushroom allergy: exclude all fungi (button, portobello, shiitake, etc.) including hidden sources in broths, sauces, and umami flavorings. Verify cross-contamination with food prep service.",
    },
    "45-min session cap": {
        Domain.TRAINING: "45-min session cap: prioritize density via supersets, antagonist pairings, and minimal warm-up between compound lifts; cut redundant accessory work; bias toward 2-3 hard sets per movement at high RIR-quality.",
    },
    "45-minute session cap": {
        Domain.TRAINING: "45-min session cap: prioritize density via supersets, antagonist pairings, and minimal warm-up between compound lifts; cut redundant accessory work; bias toward 2-3 hard sets per movement at high RIR-quality.",
    },
}


def _detect_age_bracket(age: int) -> str:
    if age >= 60:
        return "older"
    if age <= 18:
        return "youth"
    return "adult"


def _persona_row_extract(parameterization: str, intake: ClientIntake) -> str | None:
    """Extract the parameterization row most relevant to this persona, if any.

    Parameterization text is typically segmented as "Population A: ... Population B: ..."
    with semicolons separating rows. Returns the matched row (with its leading label)
    or None if no clear match found.
    """
    if not parameterization:
        return None
    # Split on period or semicolon followed by whitespace and a capitalized population label.
    # Use a lookbehind-style approach: keep the delimiter consumed but preserve row start.
    rows = re.split(r"(?<=[.;])\s+(?=[A-Z][a-z])", parameterization)
    if len(rows) < 2:
        return None  # not a structured-rows parameterization

    ts = intake.training_status
    age = intake.demographics.age
    age_bracket = _detect_age_bracket(age)
    sex = intake.demographics.sex
    ts_keywords = _TRAINING_STATUS_TO_KEYWORDS.get(ts, [])

    scored: list[tuple[int, str]] = []
    for row in rows:
        row_lower = row.lower()
        score = 0
        for kw in ts_keywords:
            if kw in row_lower:
                score += 3
        if age_bracket == "older":
            for kw in _AGE_KEYWORDS["older"]:
                if kw in row_lower:
                    score += 2
        elif age_bracket == "youth":
            for kw in _AGE_KEYWORDS["youth"]:
                if kw in row_lower:
                    score += 2
        if sex == "F":
            for kw in _SEX_KEYWORDS_F:
                if kw in row_lower:
                    score += 1
        scored.append((score, row))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_row = scored[0]
    if best_score < 2:
        return None  # no row matched strongly enough
    return best_row.strip()


def _for_this_client_annotation(intake: ClientIntake, domain: Domain) -> list[str]:
    """Generate 'FOR THIS CLIENT' annotations based on intake constraints + contraindications for the given domain."""
    notes: list[str] = []
    # Combine constraints and contraindications into a single haystack of detail strings.
    haystacks: list[str] = []
    for c in intake.constraints:
        haystacks.append((c.detail or "").lower())
    for c in intake.contraindications:
        haystacks.append(c.lower())
    # Also check current_regimen for cycle-aware or metabolic context.
    regimen = (intake.current_regimen or "").lower()
    if "luteal" in regimen or "menstrual" in regimen or "cycle-aware" in regimen:
        haystacks.append("luteal menstrual cycle-aware")
    if "metabolic inefficiency" in regimen or "metabolic calibration" in regimen:
        haystacks.append("metabolic inefficiency")
    if "compressed eating window" in regimen or "compressed window" in regimen:
        haystacks.append("compressed eating window")
    if "underfueling" in regimen or "underfueled" in regimen:
        haystacks.append("underfueling")

    haystack_blob = " | ".join(haystacks)
    seen_content: set[str] = set()
    for keyword, by_domain in _CONSTRAINT_ANNOTATIONS.items():
        if domain not in by_domain:
            continue
        if keyword.lower() in haystack_blob:
            note = by_domain[domain]
            # Dedupe by first 60 chars to catch near-duplicates from synonym keywords.
            content_key = note[:60]
            if content_key not in seen_content:
                notes.append(note)
                seen_content.add(content_key)
    return notes


def _render_pattern(
    pattern: PatternMatch,
    block: DomainBlock,
    intake: ClientIntake | None = None,
) -> list[str]:
    lines: list[str] = []
    lines.append(f"### Pattern: {pattern.pattern_id} (sim={pattern.similarity:.2f})")
    lines.append("")
    lines.append(f"**Applies because:** {pattern.applies_because}")

    # Persona-matched parameterization row (if intake given and parameterization is row-structured).
    if intake is not None:
        matched_row = _persona_row_extract(pattern.parameterization, intake)
        if matched_row:
            lines.append(f"**For this client ({intake.demographics.sex}, {intake.demographics.age}y, {intake.training_status}):** {matched_row}")
            lines.append(f"<details><summary>All populations covered by this pattern</summary>\n\n{pattern.parameterization}\n\n</details>")
        else:
            lines.append(f"**Parameterization:** {pattern.parameterization}")
    else:
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


def _render_domain(
    domain: Domain,
    block: DomainBlock | None,
    intake: ClientIntake | None = None,
) -> list[str]:
    lines: list[str] = []
    lines.append(f"## {domain.value.title()}")
    lines.append("")

    if block is None or (not block.patterns and not block.atoms):
        lines.append("_(no matches)_")
        lines.append("")
        return lines

    # Constraint-aware annotations for this domain (one-time, before patterns).
    if intake is not None:
        annotations = _for_this_client_annotation(intake, domain)
        if annotations:
            lines.append("**For this client — constraint-aware notes:**")
            for note in annotations:
                lines.append(f"- {note}")
            lines.append("")

    # Track atom_ids shown as backing so we don't repeat them below
    shown_as_backing: set[str] = set()

    # Patterns sorted by similarity desc
    sorted_patterns = sorted(block.patterns, key=lambda p: p.similarity, reverse=True)
    for pattern in sorted_patterns:
        lines.extend(_render_pattern(pattern, block, intake))
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


def _render_client_context(intake: ClientIntake) -> list[str]:
    lines: list[str] = []
    lines.append("## Client context")
    lines.append("")
    d = intake.demographics
    lines.append(
        f"- **Profile:** {d.sex}, {d.age}y, {d.weight_kg:.1f} kg, {d.height_cm:.0f} cm, training status: {intake.training_status}"
    )
    lines.append(f"- **Goals:** {', '.join(intake.goals)}")
    if intake.constraints:
        lines.append("- **Constraints:**")
        for c in intake.constraints:
            lines.append(f"  - *{c.type}*: {c.detail}")
    if intake.contraindications:
        lines.append("- **Contraindications:** " + "; ".join(intake.contraindications))
    if intake.metabolic_calibration is not None:
        lines.append(
            f"- **Metabolic calibration:** {intake.metabolic_calibration:.2f} (measured maintenance = predicted_TDEE × this factor)"
        )
    lines.append("")
    return lines


def render_markdown(pack: EvidencePack, intake: ClientIntake | None = None) -> str:
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

    # Client context — surface goals, constraints, contraindications upfront
    if intake is not None:
        lines.extend(_render_client_context(intake))

    # Domain sections
    for domain in _DOMAIN_ORDER:
        block = pack.domain_recommendations.get(domain)
        lines.extend(_render_domain(domain, block, intake))

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
