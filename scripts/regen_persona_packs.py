"""Regenerate the 9 demo persona packs against the current library.db.

Demo persona packs (`web/public/sp2/*.{json,md}`) are static files
generated at curation time. When library.db changes (atoms admitted,
verdicts re-merged), the demo packs go stale — coaches viewing
/clients/{carl,tori,…}/literature see the old citation_integrity %.

This script compiles each persona intake against the current library
and overwrites BOTH `docs/examples/sp2/` (canonical) and
`web/public/sp2/` (Vercel-bundled mirror). It is idempotent.

Run after rebuilding library.db. Then `git add docs/examples/sp2
web/public/sp2 && git commit && git push` so Vercel redeploys.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from hcc_compiler.sp2.compile import compile  # noqa: E402
from hcc_compiler.sp2.intake import load_intake  # noqa: E402
from hcc_compiler.sp2.render import render_markdown  # noqa: E402


# Mirrored from web/lib/data/personas.ts. Keep in sync — single source of
# truth for the slug ↔ packFile ↔ intakeFile mapping lives there.
PERSONAS = [
    ("amy",       "amy.json",                       "intake_amy_runner.yaml"),
    ("carl",      "carl.json",                      "intake_carl_strength.yaml"),
    ("sam",       "sam.json",                       "intake_sam_recomp.yaml"),
    ("bradley",   "test_v2_bradley.json",           "intake_test_v2_bradley.yaml"),
    ("david",     "test_v2_david.json",             "intake_test_v2_david.yaml"),
    ("jackson",   "test_v2_jackson_white.json",     "intake_test_v2_jackson_white.yaml"),
    ("sarah",     "test_v2_sarah_nutrition.json",   "intake_test_v2_sarah_nutrition.yaml"),
    ("sebastian", "test_v2_sebastian.json",         "intake_test_v2_sebastian.yaml"),
    ("tori",      "test_v2_tori_shaw.json",         "intake_test_v2_tori_shaw.yaml"),
]


def _integrity(data: dict) -> tuple[int, int]:
    cits = [
        c
        for block in data["domain_recommendations"].values()
        for atom in block["atoms"]
        for c in atom["citations"]
    ]
    fully_verified = sum(
        1 for c in cits
        if c["existence"] == "VERIFIED" and c["faithfulness"] == "VERIFIED"
    )
    return fully_verified, len(cits)


def main() -> int:
    library_db = REPO / "library.db"
    docs_dir = REPO / "docs" / "examples" / "sp2"
    web_dir = REPO / "web" / "public" / "sp2"
    intake_dir = REPO / "tests" / "fixtures" / "intakes"

    if not library_db.exists():
        print(f"ERROR: {library_db} not found — run scripts/curation/build_index.py first",
              file=sys.stderr)
        return 2

    docs_dir.mkdir(parents=True, exist_ok=True)
    web_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'persona':<11} {'integrity':>10}  {'atoms':>6}  {'patterns':>9}")
    print("-" * 44)

    for slug, pack_file, intake_file in PERSONAS:
        intake_path = intake_dir / intake_file
        intake = load_intake(intake_path)
        pack = compile(intake, library_db, top_k=30, applicability_threshold=0.5)
        pack_json = json.loads(pack.model_dump_json())
        md = render_markdown(pack, intake=intake)

        # Write to both locations. The web/package.json prebuild does the
        # same copy at Vercel build time; we duplicate here so commits
        # capture the post-compile state on disk for both.
        json_text = json.dumps(pack_json, indent=2)
        md_basename = pack_file.replace(".json", ".md")
        for target_dir in (docs_dir, web_dir):
            (target_dir / pack_file).write_text(json_text, encoding="utf-8")
            (target_dir / md_basename).write_text(md, encoding="utf-8")

        fv, total = _integrity(pack_json)
        n_atoms = sum(len(b["atoms"]) for b in pack_json["domain_recommendations"].values())
        n_patterns = sum(len(b["patterns"]) for b in pack_json["domain_recommendations"].values())
        pct = (fv / total * 100) if total else 0
        print(f"{slug:<11} {pct:>8.1f}%  {n_atoms:>6}  {n_patterns:>9}  ({fv}/{total} verified)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
