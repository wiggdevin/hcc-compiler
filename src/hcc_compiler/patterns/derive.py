from __future__ import annotations
import json
import re
from pathlib import Path

from hcc_compiler.llm.anthropic_client import LLMRequest, call_llm
from hcc_compiler.models import EvidenceAtom, RecommendationPattern

_PROMPT_PATH = Path(__file__).with_name("derive_prompt.md")
_JSON_RE = re.compile(r"\{[\s\S]*\}")


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def derive_pattern(atoms: list[EvidenceAtom]) -> RecommendationPattern:
    """Derive a RecommendationPattern from a cluster of EvidenceAtoms via LLM."""
    system = _load_prompt()

    lines = ["ATOMS:"]
    for atom in atoms:
        lines.append(f"- id={atom.id} domain={atom.domain.value} claim={atom.claim!r} effect={atom.effect!r}")
    user_prompt = "\n".join(lines)

    raw = call_llm(LLMRequest(
        system=system,
        user_prompt=user_prompt,
        model="claude-sonnet-4-6",
        max_tokens=2048,
        temperature=0.2,
    ))

    match = _JSON_RE.search(raw)
    if not match:
        raise ValueError(f"LLM did not return JSON: {raw[:200]}…")

    draft = json.loads(match.group(0))

    # Force-set backing_atom_ids from caller input — never trust LLM (mirrors Plan 2 _stamp_ids).
    draft["backing_atom_ids"] = [a.id for a in atoms]

    return RecommendationPattern.model_validate(draft)
