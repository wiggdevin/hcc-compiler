"""One-shot re-extract for atoms that previously FAILed layer-2.

Force the strict-locator nudge on the FIRST call (not just the retry) and
write fresh drafts to draft-output/ for subsequent verify + route.

Usage:
    HCC_LIVE_LLM=1 ANTHROPIC_AUTH_TOKEN=... \
      uv run python scripts/curation/reextract_fails.py harvest-output/fail-reextract.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import yaml  # noqa: E402

from hcc_compiler.extract import (  # noqa: E402
    _RETRY_NUDGE,
    _call_once,
    _load_prompt,
    _quote_is_verbatim,
    _stamp_ids,
)


def extract_strict(candidate: dict, model: str = "claude-sonnet-4-6") -> dict:
    user_prompt = (
        "CANDIDATE:\n"
        f"title: {candidate.get('title')}\n"
        f"doi: {candidate.get('doi')}\n"
        f"pmid: {candidate.get('pmid')}\n"
        f"year: {candidate.get('year')}\n"
        f"journal: {candidate.get('journal')}\n"
        f"abstract: {candidate.get('abstract')}\n"
    )
    system = _load_prompt() + _RETRY_NUDGE
    draft = _call_once(system, user_prompt, model)
    abstract = candidate.get("abstract") or ""
    if not _quote_is_verbatim(draft, abstract):
        draft = _call_once(system + _RETRY_NUDGE, user_prompt, model)
    return _stamp_ids(draft, candidate)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: reextract_fails.py <candidates.json>", file=sys.stderr)
        return 2
    candidates = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out_dir = Path("draft-output")
    out_dir.mkdir(parents=True, exist_ok=True)
    for cand in candidates:
        try:
            draft = extract_strict(cand)
        except Exception as e:
            print(f"skip {cand.get('pmid')}: {e}", file=sys.stderr)
            continue
        (out_dir / f"{draft['id']}.yaml").write_text(yaml.safe_dump(draft, sort_keys=False))
        print(f"wrote {draft['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
