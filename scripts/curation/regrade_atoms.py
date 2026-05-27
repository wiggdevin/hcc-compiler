"""Deterministic evidence-level reclassifier.

Walks `library/atoms/**/*.yaml`, inspects each citation's `cited_title`,
and assigns the strongest evidence level that matches the title:

- L1: systematic review / meta-analysis / umbrella review / network meta-analysis / scoping review
- L2: randomized / RCT / controlled trial / clinical trial   (only when no L1 hit)
- L3: cohort / cross-sectional / observational / prospective / longitudinal / retrospective / case-control
- L4: case report / case series / case study

For atoms with multiple citations, the atom takes the strongest grade
across all titles (the atom is only as strong as its best backing paper).

History: extract.py defaulted every atom to L1, producing a library
where 186/194 atoms (95.9%) carried L1 — implausible for a corpus that
includes single-RCT and observational papers.

Idempotent: re-running produces the same result. Atoms whose title
gives no signal stay at their current grade (no downgrade on uncertainty).
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]


# Precedence: L1 keywords beat L2 beat L3 beat L4. Order matters.
# Each pattern is matched case-insensitively against the citation title.
_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("L1", (
        "meta-analysis",
        "metaanalysis",
        "meta-analytic",
        "meta-regression",
        "metaregression",
        "meta-synthesis",
        "metasynthesis",
        "pooled analysis",
        "systematic review",
        "umbrella review",
        "network meta-analysis",
        "scoping review",
    )),
    ("L2", (
        "randomized",
        "randomised",
        "rct",
        "controlled trial",
        "clinical trial",
    )),
    ("L3", (
        "cohort",
        "cross-sectional",
        "crosssectional",
        "observational",
        "prospective",
        "longitudinal",
        "retrospective",
        "case-control",
        "case control",
    )),
    ("L4", (
        "case report",
        "case series",
        "case study",
    )),
)

_LEVELS = ("L1", "L2", "L3", "L4")


def classify_title(title: str) -> str | None:
    """Return the strongest matching level for `title`, or None on no match."""
    if not title:
        return None
    lower = title.lower()
    for level, keywords in _RULES:
        if any(kw in lower for kw in keywords):
            return level
    return None


def classify_atom(atom: dict) -> str | None:
    """Return the strongest level across all citations of an atom."""
    best: str | None = None
    for cit in atom.get("citations") or []:
        guess = classify_title(cit.get("cited_title") or "")
        if guess is None:
            continue
        if best is None or _LEVELS.index(guess) < _LEVELS.index(best):
            best = guess
    return best


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the diff but do not write YAMLs."
    )
    parser.add_argument(
        "--report",
        default=str(Path.home() / "Inbox" / "notes" / "phase-d-regrade-report.md"),
        help="Path to write the markdown report (default: ~/Inbox/notes/phase-d-regrade-report.md).",
    )
    args = parser.parse_args()

    atoms_root = REPO / "library" / "atoms"
    if not atoms_root.exists():
        print(f"ERROR: {atoms_root} not found", file=sys.stderr)
        return 2

    before_counts: Counter[str] = Counter()
    after_counts: Counter[str] = Counter()
    per_domain_before: dict[str, Counter[str]] = {}
    per_domain_after: dict[str, Counter[str]] = {}
    changed_rows: list[tuple[str, str, str, str]] = []
    no_signal: list[str] = []
    same: list[str] = []

    for path in sorted(atoms_root.rglob("*.yaml")):
        atom = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(atom, dict):
            continue
        domain = atom.get("domain", path.parent.name)
        current = atom.get("evidence_level") or "?"
        before_counts[current] += 1
        per_domain_before.setdefault(domain, Counter())[current] += 1

        guess = classify_atom(atom)
        if guess is None:
            after_counts[current] += 1
            per_domain_after.setdefault(domain, Counter())[current] += 1
            no_signal.append(str(path.relative_to(REPO)))
            continue

        if guess == current:
            after_counts[current] += 1
            per_domain_after.setdefault(domain, Counter())[current] += 1
            same.append(str(path.relative_to(REPO)))
            continue

        # Mutated.
        first_title = (atom.get("citations") or [{}])[0].get("cited_title") or ""
        after_counts[guess] += 1
        per_domain_after.setdefault(domain, Counter())[guess] += 1
        changed_rows.append((
            str(path.relative_to(REPO)),
            current,
            guess,
            first_title,
        ))

        if not args.dry_run:
            atom["evidence_level"] = guess
            path.write_text(
                yaml.safe_dump(atom, sort_keys=False, allow_unicode=False),
                encoding="utf-8",
            )

    # Stdout summary.
    print("=== Evidence regrade ===")
    print(f"Total atoms: {sum(before_counts.values())}")
    print(f"Changed:     {len(changed_rows)}")
    print(f"Unchanged:   {len(same)}")
    print(f"No signal:   {len(no_signal)}")
    print()
    print("Distribution before:", dict(sorted(before_counts.items())))
    print("Distribution after: ", dict(sorted(after_counts.items())))
    if args.dry_run:
        print("\n(dry-run — no files written)")

    # Markdown report.
    report = [
        "# Phase D — Evidence Regrade Report",
        "",
        f"Generated by `scripts/curation/regrade_atoms.py{' --dry-run' if args.dry_run else ''}`.",
        "",
        "## Summary",
        "",
        f"- Total atoms: {sum(before_counts.values())}",
        f"- Atoms changed: {len(changed_rows)}",
        f"- Atoms unchanged (classifier matched existing grade): {len(same)}",
        f"- Atoms with no signal (cited_title gave no match — grade preserved): {len(no_signal)}",
        "",
        "## Distribution",
        "",
        "| Level | Before | After |",
        "|---|---|---|",
    ]
    for level in _LEVELS + ("?",):
        b = before_counts.get(level, 0)
        a = after_counts.get(level, 0)
        if b == 0 and a == 0:
            continue
        report.append(f"| {level} | {b} | {a} |")

    report += ["", "## Per-domain (after)", "", "| Domain | L1 | L2 | L3 | L4 |", "|---|---|---|---|---|"]
    for domain in sorted(per_domain_after):
        counts = per_domain_after[domain]
        report.append(
            f"| {domain} | {counts.get('L1', 0)} | {counts.get('L2', 0)} | "
            f"{counts.get('L3', 0)} | {counts.get('L4', 0)} |"
        )

    if changed_rows:
        report += ["", "## Changed atoms", ""]
        for path, before, after, title in changed_rows:
            report.append(f"- `{path}`: **{before} → {after}** — {title!r}")

    if no_signal:
        report += [
            "",
            f"## No signal ({len(no_signal)})",
            "",
            "These atoms' cited_title produced no taxonomy match; grade preserved.",
            "",
        ]
        for path in no_signal:
            report.append(f"- `{path}`")

    report_path = Path(args.report).expanduser()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nReport: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
