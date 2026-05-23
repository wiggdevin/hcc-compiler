"""Wave B T6 — audit derive_queries() differentiation across 6 test_v2 intakes.

Standalone, read-only audit. Writes findings to
/Users/zero-suminc./Inbox/goal-proof-hcc-burndown/SC4.txt.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from hcc_compiler.models import Domain
from hcc_compiler.sp2.intake import load_intake
from hcc_compiler.sp2.queries import derive_queries

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTAKE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "intakes"
PROOF_PATH = Path(
    "/Users/zero-suminc./Inbox/goal-proof-hcc-burndown/SC4.txt"
)

CLIENT_SLUGS = [
    "bradley",
    "david",
    "jackson_white",
    "sarah_nutrition",
    "sebastian",
    "tori_shaw",
]


def main() -> None:
    intakes: dict[str, object] = {}
    queries_by_client: dict[str, dict[Domain, list[str]]] = {}
    load_errors: list[str] = []

    for slug in CLIENT_SLUGS:
        path = INTAKE_DIR / f"intake_test_v2_{slug}.yaml"
        try:
            intake = load_intake(path)
            intakes[slug] = intake
            queries_by_client[slug] = derive_queries(intake)
        except Exception as exc:  # surface failure, don't paper over
            load_errors.append(f"{slug}: {exc!r}")

    # Build per-domain inverted index: domain -> query_text -> [client_slugs]
    per_domain: dict[Domain, dict[str, list[str]]] = {d: defaultdict(list) for d in Domain}
    for slug, dq in queries_by_client.items():
        for domain, queries in dq.items():
            for q in queries:
                per_domain[domain][q].append(slug)

    # Compose human-readable output
    n_clients = len(queries_by_client)
    lines: list[str] = []
    lines.append("=== SC4 — derive_queries differentiation audit ===")
    lines.append("")
    lines.append(
        "For each domain (nutrition / supplements / training / conditioning / recovery / behavior),"
    )
    lines.append(
        "list per-domain duplicate queries (emitted by >=3 of 6 test_v2 clients)."
    )
    lines.append(
        "Also: per-client uniqueness count and total queries-per-domain stats."
    )
    lines.append("")
    lines.append(f"Clients audited ({n_clients}): {', '.join(CLIENT_SLUGS)}")
    if load_errors:
        lines.append("")
        lines.append("LOAD ERRORS:")
        for err in load_errors:
            lines.append(f"  {err}")
    lines.append("")
    lines.append("-" * 78)
    lines.append("Per-client raw query enumeration")
    lines.append("-" * 78)
    for slug in CLIENT_SLUGS:
        if slug not in queries_by_client:
            lines.append(f"\n[{slug}] FAILED TO LOAD")
            continue
        intake = intakes[slug]
        lines.append(f"\n[{slug}]")
        lines.append(
            f"  training_status={intake.training_status}  goals={intake.goals}"
        )
        lines.append(
            f"  constraints={[(c.type, c.detail[:60]) for c in intake.constraints]}"
        )
        regimen_preview = (intake.current_regimen or "").strip().replace("\n", " ")
        if len(regimen_preview) > 160:
            regimen_preview = regimen_preview[:160] + "..."
        lines.append(f"  current_regimen (preview): {regimen_preview}")
        for domain in Domain:
            qs = queries_by_client[slug].get(domain, [])
            lines.append(f"  {domain.value}: {qs}")

    lines.append("")
    lines.append("-" * 78)
    lines.append("Per-domain stats + duplicate queries (emitted by >=3 of 6 clients)")
    lines.append("-" * 78)

    dup_counts: dict[Domain, int] = {}
    unique_counts: dict[Domain, int] = {}
    total_query_counts: dict[Domain, int] = {}
    per_client_uniqueness: dict[str, int] = defaultdict(int)

    for domain in Domain:
        lines.append(f"\n### {domain.value.upper()}")
        query_map = per_domain[domain]
        total_queries = sum(len(slugs) for slugs in query_map.values())
        total_query_counts[domain] = total_queries
        unique_query_texts = len(query_map)
        avg_per_client = total_queries / n_clients if n_clients else 0
        lines.append(
            f"  total query emissions: {total_queries}  "
            f"distinct query texts: {unique_query_texts}  "
            f"avg per client: {avg_per_client:.2f}"
        )

        # Duplicates (>=3 of 6)
        duplicates = sorted(
            ((q, slugs) for q, slugs in query_map.items() if len(slugs) >= 3),
            key=lambda kv: (-len(kv[1]), kv[0]),
        )
        dup_counts[domain] = len(duplicates)
        if duplicates:
            lines.append(f"  DUPLICATES (>=3/{n_clients}):")
            for q, slugs in duplicates:
                lines.append(f"    [{len(slugs)}/{n_clients}] '{q}'")
                lines.append(f"        clients: {sorted(slugs)}")
        else:
            lines.append("  DUPLICATES (>=3): none")

        # Unique queries (emitted by exactly 1 client)
        uniques = sorted(
            ((q, slugs) for q, slugs in query_map.items() if len(slugs) == 1),
            key=lambda kv: (kv[1][0], kv[0]),
        )
        unique_counts[domain] = len(uniques)
        if uniques:
            lines.append(f"  UNIQUE-TO-ONE ({len(uniques)} total):")
            for q, slugs in uniques:
                per_client_uniqueness[slugs[0]] += 1
                lines.append(f"    [{slugs[0]}] '{q}'")
        else:
            lines.append("  UNIQUE-TO-ONE: none")

    lines.append("")
    lines.append("-" * 78)
    lines.append("Per-client uniqueness count (queries emitted by ONLY this client)")
    lines.append("-" * 78)
    for slug in CLIENT_SLUGS:
        lines.append(f"  {slug}: {per_client_uniqueness.get(slug, 0)} unique queries")

    lines.append("")
    lines.append("-" * 78)
    lines.append("Domain summary table")
    lines.append("-" * 78)
    lines.append(
        f"  {'domain':<14} {'total':>6} {'distinct':>9} {'dups(>=3)':>10} {'unique(=1)':>11}"
    )
    for domain in Domain:
        lines.append(
            f"  {domain.value:<14} "
            f"{total_query_counts[domain]:>6} "
            f"{len(per_domain[domain]):>9} "
            f"{dup_counts[domain]:>10} "
            f"{unique_counts[domain]:>11}"
        )

    # Differentiation analysis — search for regimen tokens NOT in queries
    lines.append("")
    lines.append("-" * 78)
    lines.append(
        "REGIMEN-KEYWORD GAP CHECK (does any query echo a distinctive regimen token?)"
    )
    lines.append("-" * 78)

    # Hand-picked distinctive tokens per client (drawn from the regimen text)
    regimen_signals: dict[str, list[str]] = {
        "bradley": [
            "kettlebell",
            "Peloton",
            "PowerBlocks",
            "rower",
            "Mediterranean",
            "HRV",
        ],
        "david": [
            "boxing",
            "Smith-machine",
            "machine",
            "cable",
            "metabolic inefficiency",
            "tempo",
        ],
        "jackson_white": [
            "trap-bar",
            "front squat",
            "SSB",
            "Bulgarian split squat",
            "landmine",
            "anti-rotation",
            "RPE",
        ],
        "sarah_nutrition": [
            "luteal",
            "cycle",
            "menstrual",
            "underfueling",
            "compressed eating window",
        ],
        "sebastian": [
            "LISS",
            "VO2max",
            "VT1",
            "VT2",
            "treadmill",
            "stairs",
            "refeed",
            "eccentric",
            "isometric",
        ],
        "tori_shaw": [
            "lumbar",
            "spinal-fusion",
            "corrective",
            "stability",
            "uphill walking",
            "NDT",
            "Armour",
        ],
    }

    for slug, tokens in regimen_signals.items():
        if slug not in queries_by_client:
            continue
        all_queries_blob = " ".join(
            q for qs in queries_by_client[slug].values() for q in qs
        ).lower()
        missing = [t for t in tokens if t.lower() not in all_queries_blob]
        present = [t for t in tokens if t.lower() in all_queries_blob]
        lines.append(f"\n  [{slug}]")
        lines.append(f"    regimen tokens PRESENT in queries: {present}")
        lines.append(f"    regimen tokens MISSING from queries: {missing}")

    lines.append("")
    lines.append("-" * 78)
    lines.append("T7 RECOMMENDATIONS")
    lines.append("-" * 78)
    lines.append(
        """
1. INJECT REGIMEN KEYWORDS INTO derive_queries()
   None of the 6 test_v2 clients' regimen-distinctive tokens (kettlebell, boxing,
   trap-bar, luteal, LISS/VO2/VT1, lumbar-fusion, etc.) appear in ANY derived
   query. The current template only mixes `goals[0..n]` + `training_status`. Two
   clients with identical (goals, training_status) get IDENTICAL queries in every
   domain except for constraint-derived "avoiding {detail}" tails — meaning
   harvest evidence is non-personalized.

2. CONCRETE T7 PATCHES (anchored in observed data)
   - CONDITIONING: Bradley's regimen mentions "kettlebell 4-week cycle" yet his
     CONDITIONING queries are the generic ["cardiovascular conditioning for
     weight_loss", "HIIT for weight_loss"]. derive_queries should detect
     "kettlebell" in current_regimen and append "kettlebell circuit conditioning"
     (or "kettlebell complex for weight_loss"). Same applies to Sebastian's
     "LISS treadmill" / "HIIT VO2max" exposures and David's "boxing".
   - TRAINING: Jackson White's regimen explicitly LISTS preferred lifts
     (trap-bar DL, front squat, SSB, Bulgarian split squat, landmine press) and
     contraindicates back squat/deadlift/bent-over row. derive_queries currently
     emits "resistance training program for hypertrophy" — should inject
     "trap-bar deadlift hypertrophy" / "Bulgarian split squat hypertrophy".
   - NUTRITION: Sarah Nutrition's regimen flags "luteal phase +150–200 kcal" but
     queries only emit "protein intake for recomposition in trained adults".
     derive_queries should detect "luteal"/"menstrual"/"cycle" and inject
     "luteal phase nutrition trained females" / "menstrual cycle macros".
   - RECOVERY: Tori Shaw is post-lumbar-fusion + NDT-treated hypothyroid;
     queries are stock ["recovery between sessions recreational", "sleep for
     weight_loss"]. Inject "post-lumbar-fusion recovery" / "hypothyroid recovery
     training".
   - SUPPLEMENTS: every client gets ONE supplements query of form
     "supplements for {primary} {ts}". For Jackson (omega-3 supplemented),
     Sebastian (bloodwork ferritin halved 248->130), Tori (suspected iron
     deficiency), regimen/contraindications carry concrete supplement signals
     (omega-3, iron, ferritin) that are dropped on the floor. Inject those.

3. WHY THIS MATTERS FOR HARVEST
   Identical queries -> identical PubMed/Crossref result sets across clients ->
   downstream tier-aware routing has no client-specific evidence to choose from.
   Differentiation must originate at the query layer; no amount of downstream
   filtering can recover signal that was never harvested.

4. SUGGESTED MECHANISM
   Add a `_REGIMEN_KEYWORDS: dict[str, dict[Domain, list[str]]]` lookup
   (keyword -> domain -> query template) inside queries.py. Before the per-
   domain cap, scan `intake.current_regimen` (case-insensitive) for each
   keyword and append the corresponding domain-scoped query. The existing
   `result[domain] = result[domain][:3]` cap already enforces the budget,
   so worst case some generic queries get bumped — which is the goal.
"""
    )

    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROOF_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {PROOF_PATH}")
    print(f"Total clients audited: {n_clients}")
    print(
        "Per-domain duplicate counts (>=3): "
        + ", ".join(f"{d.value}={dup_counts[d]}" for d in Domain)
    )
    print(
        "Per-domain unique counts (==1):   "
        + ", ".join(f"{d.value}={unique_counts[d]}" for d in Domain)
    )


if __name__ == "__main__":
    main()
