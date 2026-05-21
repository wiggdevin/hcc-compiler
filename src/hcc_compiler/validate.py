# src/hcc_compiler/validate.py
from __future__ import annotations
from pathlib import Path
from hcc_compiler.models import EvidenceAtom, RecommendationPattern, Tier
from hcc_compiler.loader import load_dir


def validate_library(root: Path) -> list[str]:
    """Return a list of human-readable problems. Empty list = clean."""
    root = Path(root)
    problems: list[str] = []

    atoms, a_err = load_dir(root / "atoms", EvidenceAtom)
    patterns, p_err = load_dir(root / "patterns", RecommendationPattern)
    problems += [f"{e.path}: {e.message.splitlines()[0]}" for e in (*a_err, *p_err)]

    ids = [a.id for a in atoms]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"duplicate atom id: {dup}")

    atom_ids = set(ids)
    for p in patterns:
        for ref in p.backing_atom_ids:
            if ref not in atom_ids:
                problems.append(f"{p.id}: backing_atom_id {ref} not found in library")

    for a in atoms:
        if a.tier == Tier.HIGH_IMPACT and a.approval.strip().lower() == "auto":
            problems.append(f"{a.id}: high-impact atom requires human approval, not 'auto'")

    return problems
