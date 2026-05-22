from __future__ import annotations
import json
import re
from pathlib import Path
from hcc_compiler.llm.glm_client import GLMRequest, call_llm
from hcc_compiler.models import DOMAIN_PREFIX, Domain

_PROMPT_PATH = Path(__file__).with_name("extract_prompt.md")
_JSON_RE = re.compile(r"\{[\s\S]*\}")


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _pmid_suffix(pmid: str | None) -> str:
    digits = re.sub(r"\D", "", str(pmid or ""))
    if not digits:
        return "0000"
    return digits[-4:].zfill(4)


def _stamp_ids(draft: dict, candidate: dict) -> dict:
    """Force-rewrite LLM-assigned id fields with deterministic values.

    - draft["id"] becomes EA-<canonical prefix>-<last 4 PMID digits>.
    - citations[0].id becomes the candidate DOI (falling back to PMID).
    - citations[0].cited_title becomes the candidate title (defensive).
    """
    try:
        domain = Domain(draft["domain"])
    except (KeyError, ValueError) as exc:
        raise ValueError(f"draft missing valid domain: {draft.get('domain')!r}") from exc
    domain_code = DOMAIN_PREFIX[domain]
    draft["id"] = f"EA-{domain_code}-{_pmid_suffix(candidate.get('pmid'))}"

    citations = draft.get("citations") or []
    if citations:
        first = citations[0]
        citation_id = candidate.get("doi") or candidate.get("pmid")
        if citation_id:
            first["id"] = str(citation_id)
        title = candidate.get("title")
        if title:
            first["cited_title"] = title
    return draft


_RETRY_NUDGE = (
    "\nYour previous response had a locator_quote that was NOT a verbatim "
    "substring of the abstract. You MUST copy the locator_quote character-for-"
    "character from the abstract — no paraphrasing, no edits, no ellipses. "
    "Pick a different verbatim span if needed."
)


def _quote_is_verbatim(draft: dict, abstract: str) -> bool:
    if not abstract:
        return True  # can't verify; trust LLM
    citations = draft.get("citations") or []
    if not citations:
        return True
    quote = (citations[0].get("locator_quote") or "").strip()
    return bool(quote) and quote.lower() in abstract.lower()


def _call_once(system: str, user_prompt: str, model: str) -> dict:
    raw = call_llm(GLMRequest(
        model=model, system=system, user_prompt=user_prompt,
        max_tokens=2048, temperature=0.2,
    ))
    match = _JSON_RE.search(raw)
    if not match:
        raise ValueError(f"LLM did not return JSON: {raw[:200]}…")
    return json.loads(match.group(0))


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
    system = _load_prompt()
    draft = _call_once(system, user_prompt, model)
    abstract = candidate.get("abstract") or ""
    if not _quote_is_verbatim(draft, abstract):
        draft = _call_once(system + _RETRY_NUDGE, user_prompt, model)
    return _stamp_ids(draft, candidate)
