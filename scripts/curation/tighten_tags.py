"""Deterministic tag tightener — fill vague population_applicability fields.

For each atom in `library/atoms/`, look at its citation IDs (DOI / PMID),
find the matching record in `harvest-output/*.json`, then regex-scan the
abstract for population markers and overwrite *only* fields whose entire
value is a known vague phrase ("unspecified", "not specified", "varied",
etc.). Never overwrites a field that carries actual content.

Coverage:
- sex             — counts male/female mentions in abstract
- training_status — keyword match (trained / untrained / athletes / sedentary / recreational / novice)
- age             — regex for "aged X-Y years", "older adults", etc.
- duration        — regex for "N weeks", "N months", "acute"
- dose_magnitude  — SKIPPED (too domain-specific for reliable regex)

Idempotent. Re-running produces the same result.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]


VAGUE_EXACT = {
    "unspecified",
    "not specified",
    "not stated",
    "not reported",
    "varied",
    "various",
    "not applicable",
    "n/a",
    "not available",
    "not available in abstract",
    "not provided",
    "none specified",
    "none reported",
}


def is_vague(value: object) -> bool:
    """A field is vague if its trimmed lowercase value is a known vague phrase."""
    if not isinstance(value, str):
        return False
    return value.strip().lower() in VAGUE_EXACT


# ---- regex extractors ----------------------------------------------------

_RE_MALE = re.compile(r"\b(men|male|males)\b", re.IGNORECASE)
_RE_FEMALE = re.compile(r"\b(women|female|females)\b", re.IGNORECASE)


def extract_sex(abstract: str) -> str | None:
    """At least 1 male AND 1 female mention → 'both'; ≥2 of one + 0 of the other → that gender."""
    m = len(_RE_MALE.findall(abstract))
    f = len(_RE_FEMALE.findall(abstract))
    if m >= 1 and f >= 1:
        return "both"
    if m >= 2 and f == 0:
        return "male"
    if f >= 2 and m == 0:
        return "female"
    return None


# Order matters — more specific patterns first (longest wins).
_TRAINING_STATUS_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\belite\s+athletes?\b", re.IGNORECASE), "elite athletes"),
    (re.compile(r"\bprofessional\s+athletes?\b", re.IGNORECASE), "professional athletes"),
    (re.compile(r"\bcompetitive\s+athletes?\b", re.IGNORECASE), "competitive athletes"),
    (re.compile(
        r"\b(strength-?trained|resistance-?trained|well-?trained|highly\s+trained)\s+"
        r"(men|women|adults|subjects|individuals|participants|athletes)\b",
        re.IGNORECASE), "trained"),
    (re.compile(r"\brecreationally\s+(active|trained)\b", re.IGNORECASE), "recreational"),
    (re.compile(
        r"\btrained\s+(men|women|adults|subjects|individuals|participants|athletes)\b",
        re.IGNORECASE), "trained"),
    (re.compile(
        r"\buntrained\s+(men|women|adults|subjects|individuals|participants)\b",
        re.IGNORECASE), "untrained"),
    (re.compile(
        r"\bsedentary\s+(men|women|adults|subjects|individuals|participants)\b",
        re.IGNORECASE), "sedentary"),
    (re.compile(r"\bnovice\s+(lifters?|trainees?|athletes?)\b", re.IGNORECASE), "novice"),
)


def extract_training_status(abstract: str) -> str | None:
    for pattern, label in _TRAINING_STATUS_RULES:
        if pattern.search(abstract):
            return label
    return None


_RE_AGE_RANGE = re.compile(r"\baged?\s+(\d{1,3})\s*[-––to]+\s*(\d{1,3})(?:\s*(?:years?|y(?:rs?)?))?\b", re.IGNORECASE)
_RE_AGE_GTE = re.compile(r"\baged?\s*(?:≥|>|over)\s*(\d{1,3})\b", re.IGNORECASE)
_RE_AGE_PLUS = re.compile(r"\b(\d{1,3})\s+years?\s+(?:and\s+)?(?:older|or\s+older)\b", re.IGNORECASE)


def extract_age(abstract: str) -> str | None:
    for m in _RE_AGE_RANGE.finditer(abstract):
        lo, hi = int(m.group(1)), int(m.group(2))
        # Plausibility filter — must look like a human age range.
        if 5 <= lo <= 100 and 5 <= hi <= 100 and lo < hi:
            return f"{lo}-{hi} years"
    m = _RE_AGE_GTE.search(abstract)
    if m and 18 <= int(m.group(1)) <= 100:
        return f"≥{m.group(1)} years"
    m = _RE_AGE_PLUS.search(abstract)
    if m and 18 <= int(m.group(1)) <= 100:
        return f"≥{m.group(1)} years"
    lower = abstract.lower()
    # Coarse age-band fallbacks (only when no specific range was found).
    if "older adults" in lower or "elderly" in lower:
        return "older adults"
    if "young adults" in lower:
        return "young adults"
    if "middle-aged" in lower:
        return "middle-aged adults"
    if "adolescents" in lower or "adolescence" in lower:
        return "adolescents"
    return None


_RE_DURATION_WEEK = re.compile(r"\b(\d{1,3})\s*-?\s*(?:week|wk)s?\b", re.IGNORECASE)
_RE_DURATION_MONTH = re.compile(r"\b(\d{1,3})\s*-?\s*months?\b", re.IGNORECASE)


def extract_duration(abstract: str) -> str | None:
    weeks: list[int] = []
    for m in _RE_DURATION_WEEK.finditer(abstract):
        weeks.append(int(m.group(1)))
    months: list[int] = []
    for m in _RE_DURATION_MONTH.finditer(abstract):
        months.append(int(m.group(1)))
    if weeks:
        # Pick the longest mentioned (typical study length is the longest).
        # Filter out absurd: 1-week is too short to be meaningful; 100+ is noise.
        weeks = [w for w in weeks if 2 <= w <= 78]
        if weeks:
            return f"{max(weeks)} weeks"
    if months:
        months = [m for m in months if 1 <= m <= 24]
        if months:
            return f"{max(months)} months"
    lower = abstract.lower()
    if "acute" in lower and ("intake" in lower or "dose" in lower or "supplementation" in lower or "administration" in lower or "ingestion" in lower):
        return "acute"
    return None


# ---- main driver ----------------------------------------------------------


def build_harvest_index(harvest_dir: Path) -> dict[str, dict]:
    """Build a lookup keyed by BOTH pmid and doi (lowercased)."""
    index: dict[str, dict] = {}
    for jf in sorted(harvest_dir.glob("*.json")):
        try:
            records = json.loads(jf.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(records, list):
            continue
        for rec in records:
            if not isinstance(rec, dict):
                continue
            pmid = rec.get("pmid")
            doi = rec.get("doi")
            if pmid:
                index.setdefault(str(pmid).lower(), rec)
            if doi:
                index.setdefault(str(doi).lower(), rec)
    return index


def find_record(atom: dict, harvest_index: dict[str, dict]) -> dict | None:
    """Return the first matching harvest record across all of an atom's citations."""
    for cit in atom.get("citations") or []:
        cid = cit.get("id")
        if not cid:
            continue
        rec = harvest_index.get(str(cid).lower())
        if rec is not None:
            return rec
    return None


_EXTRACTORS: tuple[tuple[str, callable], ...] = (
    ("sex", extract_sex),
    ("training_status", extract_training_status),
    ("age", extract_age),
    ("duration", extract_duration),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print diff but do not write YAMLs.")
    parser.add_argument(
        "--report",
        default=str(Path.home() / "Inbox" / "notes" / "phase-d-tighten-report.md"),
    )
    args = parser.parse_args()

    atoms_root = REPO / "library" / "atoms"
    harvest_root = REPO / "harvest-output"
    if not atoms_root.exists() or not harvest_root.exists():
        print("ERROR: library/atoms or harvest-output not found", file=sys.stderr)
        return 2

    harvest_index = build_harvest_index(harvest_root)
    print(f"Harvest index: {len(harvest_index)} keyed records loaded from {harvest_root}/")

    overrides_by_field: Counter[str] = Counter()
    atoms_changed = 0
    atoms_inspected = 0
    atoms_no_harvest_match = 0
    rows: list[tuple[str, str, str, str]] = []  # (atom_path, field, before, after)

    for path in sorted(atoms_root.rglob("*.yaml")):
        atom = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(atom, dict):
            continue
        pop = atom.get("population_applicability") or {}
        vague_fields = [name for name, _ in _EXTRACTORS if is_vague(pop.get(name))]
        if not vague_fields:
            continue
        atoms_inspected += 1

        rec = find_record(atom, harvest_index)
        if rec is None:
            atoms_no_harvest_match += 1
            continue

        source_text = (rec.get("full_text") or "") + " " + (rec.get("abstract") or "")
        source_text = source_text.strip()
        if not source_text:
            continue

        changed = False
        for field in vague_fields:
            extractor = dict(_EXTRACTORS)[field]
            new_val = extractor(source_text)
            if not new_val:
                continue
            before = pop[field]
            pop[field] = new_val
            overrides_by_field[field] += 1
            rows.append((str(path.relative_to(REPO)), field, str(before), new_val))
            changed = True

        if changed:
            atoms_changed += 1
            atom["population_applicability"] = pop
            if not args.dry_run:
                path.write_text(
                    yaml.safe_dump(atom, sort_keys=False, allow_unicode=False),
                    encoding="utf-8",
                )

    # Summary.
    print("=== Tag tighten ===")
    print(f"Atoms with ≥1 strictly-vague field: {atoms_inspected}")
    print(f"Atoms with no harvest cache match:  {atoms_no_harvest_match}")
    print(f"Atoms changed:                      {atoms_changed}")
    print(f"Field overrides: {dict(overrides_by_field)}")
    print(f"Total field overrides:              {sum(overrides_by_field.values())}")
    if args.dry_run:
        print("\n(dry-run — no files written)")

    # Report.
    report = [
        "# Phase D — Tag Tighten Report",
        "",
        f"Generated by `scripts/curation/tighten_tags.py{' --dry-run' if args.dry_run else ''}`.",
        "",
        "## Summary",
        "",
        f"- Atoms with ≥1 strictly-vague field: {atoms_inspected}",
        f"- Atoms with no harvest cache match: {atoms_no_harvest_match} (skipped — pre-cache admissions)",
        f"- Atoms changed: {atoms_changed}",
        f"- Field overrides total: {sum(overrides_by_field.values())}",
        "",
        "## Overrides per field",
        "",
        "| Field | Count |",
        "|---|---|",
    ]
    for field, _ in _EXTRACTORS:
        report.append(f"| {field} | {overrides_by_field.get(field, 0)} |")

    if rows:
        report += ["", "## Diff", ""]
        for atom_path, field, before, after in rows:
            report.append(f"- `{atom_path}` · **{field}**: `{before}` → `{after}`")

    report_path = Path(args.report).expanduser()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nReport: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
