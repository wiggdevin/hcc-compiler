#!/usr/bin/env python3
"""Python truth-oracle for confidence acceptance.

Ports the math from web/lib/scoring.ts so CI/automation can verify pack
confidence without booting the TS runtime. Two formula variants:

  v1 — current TS values (baseline)
  v2 — Phase 2 formula tweaks

CLI:
  python scripts/verify_confidence.py <pack.json>
      [--min-overall FLOAT] [--min-domain FLOAT]
      [--print-medians] [--formula v1|v2]
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import Counter
from typing import Any

DOMAIN_ORDER = [
    "nutrition",
    "training",
    "conditioning",
    "supplements",
    "recovery",
    "behavioral",
]

FORMULAS = {
    "v1": {
        "evidence_weight": {"L1": 1.0, "L2": 0.85, "L3": 0.7, "L4": 0.55},
        "sim_floor": 0.5,
        "atom_floor": None,            # no per-atom floor
        "atom_aggregator": "mean",     # arithmetic
        "atom_share": 0.7,
        "pattern_share": 0.3,
    },
    "v2": {
        "evidence_weight": {"L1": 1.0, "L2": 0.92, "L3": 0.78, "L4": 0.65},
        "sim_floor": 0.6,
        "atom_floor": 0.55,
        "atom_aggregator": "geomean",
        "atom_share": 0.65,
        "pattern_share": 0.35,
    },
}


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def geomean(xs: list[float]) -> float:
    if not xs:
        return 0.0
    # Guard zeros — TS Math.max(floor, ...) prevents this in v2, but be safe.
    safe = [max(x, 1e-9) for x in xs]
    return math.exp(sum(math.log(x) for x in safe) / len(safe))


def atom_confidence(atom: dict[str, Any], cfg: dict[str, Any]) -> float:
    ev = cfg["evidence_weight"].get(atom.get("evidence_level"), 0.55)
    sim = max(cfg["sim_floor"], atom.get("similarity", 0.0))
    base = atom.get("population_match_score", 0.0) * ev * sim
    if cfg["atom_floor"] is not None:
        base = max(cfg["atom_floor"], base)
    return base


def domain_confidence(block: dict[str, Any], cfg: dict[str, Any]) -> float:
    atoms = block.get("atoms", []) or []
    patterns = block.get("patterns", []) or []
    atom_scores = [atom_confidence(a, cfg) for a in atoms]
    pattern_score = mean([p.get("similarity", 0.0) for p in patterns])
    if not atom_scores and not patterns:
        return 0.0
    if not atom_scores:
        return pattern_score
    agg = geomean(atom_scores) if cfg["atom_aggregator"] == "geomean" else mean(atom_scores)
    if not patterns:
        return agg
    return agg * cfg["atom_share"] + pattern_score * cfg["pattern_share"]


def overall_confidence(rows: list[dict[str, Any]]) -> float:
    weighted_sum = 0.0
    total_weight = 0.0
    for r in rows:
        w = r["atomCount"] + r["patternCount"] * 2
        weighted_sum += r["confidence"] * w
        total_weight += w
    return weighted_sum / total_weight if total_weight else 0.0


def compute(pack: dict[str, Any], cfg: dict[str, Any]) -> tuple[list[dict[str, Any]], float]:
    dr = pack.get("domain_recommendations", {})
    rows = []
    for d in DOMAIN_ORDER:
        block = dr.get(d, {"atoms": [], "patterns": []})
        atoms = block.get("atoms", []) or []
        patterns = block.get("patterns", []) or []
        rows.append({
            "domain": d,
            "confidence": domain_confidence(block, cfg),
            "atomCount": len(atoms),
            "patternCount": len(patterns),
        })
    return rows, overall_confidence(rows)


def collect_atoms(pack: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for block in pack.get("domain_recommendations", {}).values():
        out.extend(block.get("atoms", []) or [])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify pack confidence (Python oracle).")
    ap.add_argument("pack", help="path to pack JSON")
    ap.add_argument("--min-overall", type=float, default=None)
    ap.add_argument("--min-domain", type=float, default=None)
    ap.add_argument("--print-medians", action="store_true")
    ap.add_argument("--formula", choices=list(FORMULAS), default="v1")
    args = ap.parse_args()

    with open(args.pack) as f:
        pack = json.load(f)
    cfg = FORMULAS[args.formula]

    rows, overall = compute(pack, cfg)

    print("domain\tconfidence\tatomCount\tpatternCount")
    for r in rows:
        print(f"{r['domain']}\t{r['confidence']:.4f}\t{r['atomCount']}\t{r['patternCount']}")
    print(f"overall\t{overall:.4f}\tformula={args.formula}")

    if args.print_medians:
        atoms = collect_atoms(pack)
        sims = [a.get("similarity", 0.0) for a in atoms]
        pops = [a.get("population_match_score", 0.0) for a in atoms]
        ev_dist = Counter(a.get("evidence_level") for a in atoms)
        print("--- medians ---")
        print(f"atoms_total\t{len(atoms)}")
        print(f"median_similarity\t{statistics.median(sims) if sims else 0:.4f}")
        print(f"median_pop_match\t{statistics.median(pops) if pops else 0:.4f}")
        for lvl in ("L1", "L2", "L3", "L4"):
            print(f"evidence_{lvl}\t{ev_dist.get(lvl, 0)}")

    failed = False
    if args.min_overall is not None and overall < args.min_overall:
        print(f"FAIL: overall {overall:.4f} < min-overall {args.min_overall}", file=sys.stderr)
        failed = True
    if args.min_domain is not None:
        for r in rows:
            if (r["atomCount"] or r["patternCount"]) and r["confidence"] < args.min_domain:
                print(
                    f"FAIL: domain {r['domain']} {r['confidence']:.4f} < min-domain {args.min_domain}",
                    file=sys.stderr,
                )
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
