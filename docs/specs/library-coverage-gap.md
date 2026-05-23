# Library Coverage Gap — 2026-05-23

## Context
The v2 plan (`~/.claude/plans/no-i-want-everything-piped-bear.md`) targeted
Carl overall confidence ≥ 0.75 (stretch 0.85). After applying every planned
intervention — library tag curation, retrieval re-rank, top-k bump (5 → 10 →
15), formula refinement (geomean atom aggregation, sim_floor 0.6, atom_floor
0.55, evidence-weight tightening) — the realized result is:

| persona | v1 overall | v2 overall | delta |
| --- | --- | --- | --- |
| Carl   | 0.5766 | **0.6772** | +0.1006 |
| Tori   | (n/a)  | **0.6079** | — |
| Sarah  | (n/a)  | **0.6354** | — |

Carl moves from 0.5766 → 0.6772 (+10.1 pp). The 0.75 floor is **not** reached.

## Root cause
The evidence library is structurally undersized in three domains. Pattern
coverage (the only place pattern-similarity contributes to a domain score) is
one pattern per domain except behavioral (2) and nutrition (2):

| domain        | patterns | atoms |
| ---           | ---      | ---   |
| nutrition     | 2 | 35 |
| training      | 1 | 58 |
| conditioning  | 1 | 10 |
| supplements   | 1 | 50 |
| recovery      | 1 | 20 |
| behavioral    | 2 | 15 |

The supplements domain is the canonical example. It contains 50 atoms but
they collapse into just three real topical buckets:

| supplement topic     | atom count |
| ---                  | --- |
| creatine             | 21 |
| caffeine             | 16 |
| protein / amino acid | 7  |
| iron                 | 1  |
| beta-alanine         | 1 (lumped under "other") |
| omega-3 / fish oil   | 0  |
| vitamin D            | 0  |
| magnesium            | 0  |
| electrolytes         | 0  |
| B vitamins           | 0  |
| multivitamin         | 0  |

The single supplement pattern `RP-SUP-creatine-resistance-body-composition`
backs creatine-for-resistance-training only. For personas whose supplement
query embeddings do not point at creatine or caffeine (e.g. Tori, whose
supplements domain initially scored 0.4291 with zero patterns retrieved even at
top_k=15), the domain falls back to atoms-only. A subsequent fix to
`domainConfidence` removed the 0.65 atom-weight multiplier when patterns are
absent, lifting Tori's supplements to 0.6601 and her overall to 0.6368 — still
below the 0.65 floor by ~0.013. The remaining shortfall is genuine library
coverage: without omega-3 / vitamin D / magnesium / electrolyte / B-vitamin
patterns, no retrieval tuning can hit the floor.

Conditioning shows the same shape from the opposite direction: only 10 atoms
and 1 pattern (HIIT-VO2max). Recovery and behavioral are similarly thin.

## What it would take to hit 0.75 for Carl
A back-of-envelope projection from the current per-domain numbers:

Carl current per-domain (formula v2):
- nutrition    0.7072
- training     0.6916
- supplements  0.7276
- conditioning 0.6555
- recovery     0.6394
- behavioral   0.6427
- overall      0.6772

The four sub-0.70 domains are the bottleneck. To clear 0.75 overall while
keeping the v2 formula unchanged, each of conditioning / recovery /
behavioral needs to land ~0.72+. That in turn requires:

- **Add 3–5 supplement patterns** covering omega-3, vitamin D, beta-alanine,
  caffeine performance dose, protein timing — so non-creatine personas
  retrieve a pattern instead of falling back to atoms-only.
- **Add 2–3 conditioning patterns** (Z2 endurance, interval prescriptions
  beyond generic HIIT, sport-specific conditioning) and ~10 more atoms.
- **Add 1–2 recovery patterns** (sleep extension, deload, parasympathetic
  recovery) and ~10 more atoms.
- **Add 1–2 behavioral patterns** (habit-stacking, self-monitoring,
  adherence-prediction features) and ~5 more atoms.

Total: roughly **8–12 new patterns and 25–30 new atoms** — i.e. a 30 %
expansion of the current library, concentrated in the four undersupplied
domains.

## Recommendation
Library expansion is **out of scope for the v2 plan**, which explicitly
forbids broad library changes ("DO NOT add new library patterns or atoms").
Under current coverage, the realistic ceiling for the golden personas is
the numbers reported above:

- Carl  ≈ 0.68
- Sarah ≈ 0.64
- Tori  ≈ 0.61

Treat the 0.75 / 0.65 / 0.60 floors as a v3 goal contingent on the library
expansion outlined above. The v2 work successfully lifted Carl by +10 pp
and re-aligned the formula; the remaining gap is data, not code.

## Per-persona post-v2 confidence (formula v2, top_k=15, applicability_threshold=0.5)

| persona                  | overall | nut    | tra    | con    | sup    | rec    | beh    |
| ---                      | ---     | ---    | ---    | ---    | ---    | ---    | ---    |
| amy                      | 0.6117  | —      | —      | —      | —      | —      | —      |
| **carl**                 | **0.6772** | 0.7072 | 0.6916 | 0.6555 | 0.7276 | 0.6394 | 0.6427 |
| sam                      | 0.5902  | —      | —      | —      | —      | —      | —      |
| test_v2_bradley          | 0.6425  | —      | —      | —      | —      | —      | —      |
| test_v2_david            | 0.6446  | —      | —      | —      | —      | —      | —      |
| test_v2_jackson_white    | 0.6534  | —      | —      | —      | —      | —      | —      |
| **test_v2_sarah_nutrition** | **0.6354** | 0.6593 | 0.6837 | 0.6171 | 0.6382 | 0.6042 | 0.6104 |
| test_v2_sebastian        | 0.6472  | —      | —      | —      | —      | —      | —      |
| **test_v2_tori_shaw**    | **0.6079** | 0.6394 | 0.6963 | 0.5995 | 0.4291 | 0.6106 | 0.6225 |

Acceptance floors:
- Carl  ≥ 0.75 → **NOT MET** (0.6772, short by 0.0728)
- Tori  ≥ 0.65 → **NOT MET** (0.6079, short by 0.0421)
- Sarah ≥ 0.60 → **MET**     (0.6354, exceeds by 0.0354)
