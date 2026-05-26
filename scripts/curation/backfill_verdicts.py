"""Merge per-citation gate verdicts from verify-output/ into library/atoms/.

History: the extract LLM stamps `existence="UNVERIFIABLE"` and
`faithfulness="ACCESS_LIMITED"` as placeholders (see extract_prompt.md).
The deterministic gate (`citation_gate.verify_atom`) writes the real
verdicts to `verify-output/<atom_id>.json`, but `route.py` historically
moved the unmutated draft YAML into `library/atoms/<domain>/`, so the
library carries the placeholders and the compiled pack's
`citation_integrity` % is a floor, not a true measurement.

This script walks `library/atoms/**/*.yaml`, finds each atom's matching
`verify-output/<atom_id>.json`, and merges per-citation verdicts in place.
Idempotent: atoms whose verdicts already match the verify cache are no-ops.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]


def merge_atom(atom_path: Path, verify_path: Path) -> bool:
    """Return True if the YAML was mutated."""
    atom = yaml.safe_load(atom_path.read_text(encoding="utf-8"))
    verify = json.loads(verify_path.read_text(encoding="utf-8"))
    if verify.get("atom_id") != atom.get("id"):
        return False
    verdicts_by_id = {
        c["id"]: (c["existence"], c["faithfulness"])
        for c in verify.get("citations", [])
        if "id" in c
    }
    changed = False
    for cit in atom.get("citations", []):
        cid = cit.get("id")
        if cid not in verdicts_by_id:
            continue
        new_ex, new_fa = verdicts_by_id[cid]
        if cit.get("existence") != new_ex or cit.get("faithfulness") != new_fa:
            cit["existence"] = new_ex
            cit["faithfulness"] = new_fa
            changed = True
    if changed:
        atom_path.write_text(yaml.safe_dump(atom, sort_keys=False))
    return changed


def main() -> int:
    atoms_root = REPO / "library" / "atoms"
    verify_root = REPO / "verify-output"
    if not atoms_root.is_dir():
        print(f"ERROR: {atoms_root} does not exist", file=sys.stderr)
        return 2
    if not verify_root.is_dir():
        print(f"ERROR: {verify_root} does not exist", file=sys.stderr)
        return 2

    n_merged = 0
    n_noop = 0
    n_skipped = 0
    for atom_path in sorted(atoms_root.rglob("*.yaml")):
        atom_id = atom_path.stem
        verify_path = verify_root / f"{atom_id}.json"
        if not verify_path.exists():
            n_skipped += 1
            continue
        if merge_atom(atom_path, verify_path):
            n_merged += 1
        else:
            n_noop += 1
    print(f"merged: {n_merged}")
    print(f"no-op:  {n_noop}")
    print(f"skipped (no verify-output): {n_skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
