"""CLI: compile a ClientIntake YAML into an EvidencePack (JSON + Markdown).

Usage:
    python scripts/compile_plan.py <intake.yaml> \
        [--db library.db] \
        [--out-json path] \
        [--out-md path] \
        [--top-k 5] \
        [--applicability-threshold 0.4] \
        [--no-version-check]

Exit codes:
    0 — success
    1 — LibraryVersionMismatch
    2 — file / parse errors
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hcc_compiler.sp2.compile import LibraryVersionMismatch, compile  # noqa: E402
from hcc_compiler.sp2.intake import load_intake  # noqa: E402
from hcc_compiler.sp2.render import render_markdown  # noqa: E402


def _cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compile a ClientIntake YAML into an EvidencePack."
    )
    parser.add_argument("intake_path", help="Path to the intake YAML file.")
    parser.add_argument(
        "--db", default=Path("library.db"), type=Path,
        help="Path to SQLite library DB (default: library.db).",
    )
    parser.add_argument(
        "--out-json", default=None, type=Path,
        help="Output JSON path (default: <intake_basename>.json in cwd).",
    )
    parser.add_argument(
        "--out-md", default=None, type=Path,
        help="Output markdown path (default: <intake_basename>.md in cwd).",
    )
    parser.add_argument(
        "--top-k", type=int, default=5,
        help="Number of results per domain query (default: 5).",
    )
    parser.add_argument(
        "--applicability-threshold", type=float, default=0.4,
        help="Minimum population_match_score to include an atom (default: 0.4).",
    )
    parser.add_argument(
        "--no-version-check", action="store_true",
        help="Skip library version guard.",
    )

    args = parser.parse_args(argv)

    # Resolve default output paths from intake basename.
    intake_path = Path(args.intake_path)
    basename = intake_path.stem
    out_json: Path = args.out_json if args.out_json is not None else Path(f"{basename}.json")
    out_md: Path = args.out_md if args.out_md is not None else Path(f"{basename}.md")

    # Step 2: load intake.
    try:
        intake = load_intake(intake_path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"error loading intake: {exc}", file=sys.stderr)
        return 2

    # Step 3: compile.
    try:
        pack = compile(
            intake,
            args.db,
            top_k=args.top_k,
            applicability_threshold=args.applicability_threshold,
            version_check=not args.no_version_check,
        )
    except LibraryVersionMismatch as exc:
        print(f"error: version mismatch — {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"error during compile: {exc}", file=sys.stderr)
        return 2

    # Step 4: write JSON.
    try:
        out_json.write_text(pack.model_dump_json(indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"error writing JSON: {exc}", file=sys.stderr)
        return 2

    # Step 5: write markdown.
    try:
        out_md.write_text(render_markdown(pack, intake=intake), encoding="utf-8")
    except Exception as exc:
        print(f"error writing markdown: {exc}", file=sys.stderr)
        return 2

    # Step 6: print one-line summary.
    n_patterns = sum(len(b.patterns) for b in pack.domain_recommendations.values())
    n_atoms = sum(len(b.atoms) for b in pack.domain_recommendations.values())
    n_warnings = len(pack.compile_metadata.contraindication_hits)
    print(
        f"compiled {pack.client_id} -> {n_patterns} patterns, "
        f"{n_atoms} atoms, {n_warnings} warnings "
        f"(json={out_json}, md={out_md})"
    )

    return 0


if __name__ == "__main__":
    sys.exit(_cli_main())
