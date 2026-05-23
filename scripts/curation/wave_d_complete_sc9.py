"""Complete SC9 from existing draft-output/ (the Wave D background agent timed
out mid-pipeline after harvesting + extracting 19 drafts; this finishes the
verify → gate → route step). One-shot completion. Ok to be uncommitted."""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path("/Users/zero-suminc./projects/hcc-compiler")
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "curation"))

# Re-use the agent's helpers.
from wave_d_curate import (  # noqa: E402
    SC_PLANS,
    verify_drafts,
    filter_routable_drafts,
    route_survivors,
    _flush_proof,
)


def main() -> int:
    if not os.environ.get("HCC_LIVE_HTTP"):
        os.environ["HCC_LIVE_HTTP"] = "1"

    proof: list[str] = [
        "### SC9 — age-40+ anabolic resistance (resume from existing drafts) ###",
        "date: 2026-05-23",
        "(Background agent ran out of time mid-extract; this run completes",
        " verify → gate → route from whatever drafts are on disk in",
        " draft-output/. SC9's harvest of 52 candidates already happened.)",
        "",
    ]

    draft_paths = sorted((REPO / "draft-output").glob("*.yaml"))
    proof.append(f"=== Resume with {len(draft_paths)} drafts in draft-output ===")
    for p in draft_paths:
        proof.append(f"  {p.name}")
    proof.append("")

    verdicts = verify_drafts(draft_paths, proof)
    survivors = filter_routable_drafts(SC_PLANS["SC9"], draft_paths, verdicts, proof)

    if not survivors:
        proof.append("NO survivors after SC9 gate filter")
    else:
        route_survivors(proof)

    out_path = _flush_proof("SC9", proof)
    print(f"SC9 proof written to {out_path}")
    print("\n".join(proof[-20:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
