from __future__ import annotations
import re
from hcc_compiler.models import EvidenceAtom, RecommendationPattern
from hcc_compiler.sp2.intake import ClientIntake

_SPLIT_RE = re.compile(r"[,;\n]")
_TOKEN_SPLIT_RE = re.compile(r"[\W_]+")

# Words too generic to anchor a contraindication match. Tokens kept must convey
# a clinical / domain-specific signal (e.g., "renal", "ckd"), not connective
# tissue ("or", "with") or generic descriptors ("active", "history").
_STOPWORDS = frozenset({
    "or", "and", "the", "of", "with", "if", "in", "to", "for", "by", "on", "at",
    "is", "are", "as", "an", "a", "be", "any", "other",
    "pre", "existing", "contraindication", "contraindications",
    "active", "type", "history", "current", "recent", "chronic", "acute",
})


def _significant_tokens(text: str) -> set[str]:
    """Lowercased tokens ≥3 chars, excluding stopwords. Used as fallback
    matching when direct substring fails (e.g., atom 'CKD or other renal
    contraindication' vs intake 'renal insufficiency (CKD stage 2)')."""
    return {
        tok
        for tok in _TOKEN_SPLIT_RE.split(text.lower())
        if len(tok) >= 3 and tok not in _STOPWORDS
    }


def check_contraindications(
    record: EvidenceAtom | RecommendationPattern,
    intake: ClientIntake,
) -> list[str]:
    """Return list of warning strings, one per matched contraindication."""
    haystack_parts = list(intake.contraindications) + [c.detail for c in intake.constraints]
    haystack = " ".join(haystack_parts).lower()
    haystack_tokens = _significant_tokens(haystack)

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
            continue
        # Fallback: significant-token overlap catches phrase variants like
        # "CKD or other renal contraindication" against "renal insufficiency
        # (CKD stage 2)" — shared tokens {"ckd", "renal"}.
        if _significant_tokens(needle) & haystack_tokens:
            warnings.append(f"⚠ {original} (matches intake)")

    return warnings
