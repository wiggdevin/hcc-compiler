from __future__ import annotations
import re
from hcc_compiler.models import EvidenceAtom, RecommendationPattern
from hcc_compiler.sp2.intake import ClientIntake

_SPLIT_RE = re.compile(r"[,;\n]")


def check_contraindications(
    record: EvidenceAtom | RecommendationPattern,
    intake: ClientIntake,
) -> list[str]:
    """Return list of warning strings, one per matched contraindication."""
    # Build lowercased haystack from intake
    haystack_parts = list(intake.contraindications) + [c.detail for c in intake.constraints]
    haystack = " ".join(haystack_parts).lower()

    # Build needles (original-case + lowercased) from record
    if isinstance(record, EvidenceAtom):
        originals = list(record.contraindications)
    else:
        parts = _SPLIT_RE.split(record.doesnt_apply_if)
        originals = [p.strip() for p in parts if p.strip()]

    warnings: list[str] = []
    for original in originals:
        needle = original.lower().strip()
        if not needle:
            continue
        if needle in haystack:
            warnings.append(f"⚠ {original} (matches intake)")

    return warnings
