from __future__ import annotations
import json
import re
from pathlib import Path
from hcc_compiler.llm.glm_client import GLMRequest, call_llm

_PROMPT_PATH = Path(__file__).with_name("extract_prompt.md")
_JSON_RE = re.compile(r"\{[\s\S]*\}")


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def extract_atom(candidate: dict, model: str = "glm-4.6") -> dict:
    user_prompt = (
        "CANDIDATE:\n"
        f"title: {candidate.get('title')}\n"
        f"doi: {candidate.get('doi')}\n"
        f"pmid: {candidate.get('pmid')}\n"
        f"year: {candidate.get('year')}\n"
        f"journal: {candidate.get('journal')}\n"
        f"abstract: {candidate.get('abstract')}\n"
    )
    raw = call_llm(GLMRequest(
        model=model,
        system=_load_prompt(),
        user_prompt=user_prompt,
        max_tokens=2048,
        temperature=0.2,
    ))
    match = _JSON_RE.search(raw)
    if not match:
        raise ValueError(f"LLM did not return JSON: {raw[:200]}…")
    return json.loads(match.group(0))
