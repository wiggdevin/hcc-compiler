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


_NUM_RE = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")


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
