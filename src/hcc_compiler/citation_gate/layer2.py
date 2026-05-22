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
