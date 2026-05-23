#!/usr/bin/env python3
"""Apply a tag-curation YAML diff to the SQLite library.

Usage:
    python scripts/apply_curation.py [--db PATH] [--dry-run] [--undo] [<yaml_path>]

Each YAML entry is a dict with keys: atom_id, field (dotted path into the
atom JSON), old, new, reason. The script reads each atom's JSON from the
`atoms` table, navigates `field`, confirms the current value matches `old`
(skips if mismatched — already applied or stale), sets the new value, and
writes the atom JSON back.

Idempotent: re-running without flags after a successful apply is a no-op
(all entries become "skipped" because `old` no longer matches).

--dry-run : print what would change, no DB writes.
--undo    : reverse the diff (treat `new` as the value to match, set back to `old`).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# YAML loader: prefer PyYAML, fall back to a tiny inline reader for our exact
# list-of-dicts format.
# --------------------------------------------------------------------------- #
try:
    import yaml  # type: ignore

    def load_yaml(path: Path) -> list[dict]:
        with path.open() as f:
            data = yaml.safe_load(f)
        if not isinstance(data, list):
            raise SystemExit(f"YAML root must be a list, got {type(data).__name__}")
        return data
except ImportError:  # pragma: no cover — PyYAML is in pyproject.toml

    def load_yaml(path: Path) -> list[dict]:
        # Minimal reader for "- key: value" lists (one dict per `-` block).
        entries: list[dict] = []
        cur: dict | None = None
        for raw in path.read_text().splitlines():
            line = raw.rstrip()
            if not line or line.lstrip().startswith("#"):
                continue
            if line.startswith("- "):
                if cur is not None:
                    entries.append(cur)
                cur = {}
                line = line[2:]
            if cur is None:
                continue
            if ":" not in line:
                continue
            key, _, val = line.lstrip().partition(":")
            val = val.strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            cur[key.strip()] = val
        if cur is not None:
            entries.append(cur)
        return entries


# --------------------------------------------------------------------------- #
# DB path auto-detection
# --------------------------------------------------------------------------- #
def detect_db(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.is_file():
            raise SystemExit(f"--db path not found: {p}")
        return p
    root = Path(__file__).resolve().parent.parent
    for cand in (root / "library.db", root / "library" / "library.db", root / "data" / "library.db"):
        if cand.is_file():
            return cand
    raise SystemExit(
        "Could not auto-detect library DB. Tried library.db, library/library.db, data/library.db.\n"
        "Pass --db <path>."
    )


# --------------------------------------------------------------------------- #
# Dotted-path navigation
# --------------------------------------------------------------------------- #
def get_at(obj: Any, dotted: str) -> Any:
    for part in dotted.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return None
        obj = obj[part]
    return obj


def set_at(obj: Any, dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    for part in parts[:-1]:
        obj = obj[part]
    obj[parts[-1]] = value


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("yaml_path", nargs="?", default="library/curation/2026-05-23-tag-fixes.yaml")
    ap.add_argument("--db", default=None, help="path to library SQLite (auto-detect if omitted)")
    ap.add_argument("--dry-run", action="store_true", help="print changes, do not write")
    ap.add_argument("--undo", action="store_true", help="reverse the diff (match `new`, set to `old`)")
    args = ap.parse_args()

    yaml_path = Path(args.yaml_path)
    if not yaml_path.is_file():
        raise SystemExit(f"YAML not found: {yaml_path}")
    entries = load_yaml(yaml_path)
    if len(entries) > 25:
        raise SystemExit(f"YAML has {len(entries)} entries; hard cap is 25 per PRD §2.1.")

    db_path = detect_db(args.db)
    direction = "UNDO" if args.undo else "APPLY"
    mode = "DRY-RUN" if args.dry_run else "WRITE"
    print(f"[{direction} {mode}] db={db_path} yaml={yaml_path} entries={len(entries)}")

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    applied = 0
    skipped_mismatch = 0
    missing = 0

    try:
        for ent in entries:
            aid = ent["atom_id"]
            field = ent["field"]
            old_val = ent["old"]
            new_val = ent["new"]
            if args.undo:
                # Swap: expect new in DB, set back to old.
                expected, target = new_val, old_val
            else:
                expected, target = old_val, new_val

            row = con.execute("SELECT json FROM atoms WHERE id=?", (aid,)).fetchone()
            if row is None:
                missing += 1
                print(f"  MISSING  {aid}  (atom not in DB)")
                continue

            atom = json.loads(row["json"])
            cur_val = get_at(atom, field)
            if cur_val != expected:
                skipped_mismatch += 1
                print(f"  SKIP     {aid}  {field}: cur={cur_val!r} expected={expected!r}")
                continue

            set_at(atom, field, target)
            print(f"  {direction:8}{aid}  {field}: {expected!r} -> {target!r}")

            if not args.dry_run:
                con.execute("UPDATE atoms SET json=? WHERE id=?", (json.dumps(atom), aid))
            applied += 1

        if not args.dry_run:
            con.commit()
    finally:
        con.close()

    print(f"\n{direction} {mode}: applied={applied} skipped_mismatch={skipped_mismatch} missing={missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
