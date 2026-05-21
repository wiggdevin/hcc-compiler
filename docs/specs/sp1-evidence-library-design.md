# HCC Redesign — SP1: Evidence Library + Offline Curation Pipeline (Design)

Date: 2026-05-21
Status: approved design (pre-implementation)
Author: Dev Wiggins (with Claude Opus 4.7 + GPT-5.5 cross-model brainstorm)

## Context

The current Health Coach Council produces high-quality, evidence-traceable diet/exercise
plans but takes **~2 hours per client** — a sequential spine of four Claude-Opus passes
(R0→R2→R3→R5) that re-derives the same sports science for every client. At a commercial
target of ~13 new clients/day plus revisions, and a need for plans that **re-derive
dynamically** when something changes (plateau, injury, travel, lab result), 2 hours is
unsellable.

Claude and GPT-5.5 brainstormed a greenfield redesign independently and **converged on the
same architecture**: stop treating each client as a fresh research project; behave like a
*clinical-grade compiler with selective expert review*. The expensive reasoning and citation
verification move **offline into a reusable, versioned library**, paid once and amortized
across all clients. Per-client work becomes **selection + personalization**, not derivation.

Target after redesign: **~7–14 min for a fresh client; 10–90 s for a single-input change**,
with evidence rigor (real citations, population-match, safety screening, falsification
signals) preserved.

## The full target architecture (for context)

Three subsystems, built in dependency order:

| # | Sub-project | Role | Depends on |
|---|---|---|---|
| **SP1** | **Evidence Library + offline curation pipeline** *(this doc)* | The vetted Evidence Atom Bank + Recommendation Pattern Library and the offline pipeline that builds/verifies/versions them | — |
| SP2 | Per-client plan compiler runtime | ClientState → retrieval → plan-graph compilation → single strong-model arbitration → targeted critics → evidence-ledger → deterministic render | SP1 |
| SP3 | Dynamic re-planning / Change Ledger engine | DAG dependency tracking, node hashing, incremental invalidation | SP2 |

Each subsystem gets its own spec → plan → build cycle. **This document specifies SP1 only.**
SP2's plan-graph will be designed *aware* of SP3's DAG needs, but those are out of scope here.

## Locked decisions

- **Coverage (v1):** broad — all current council domains (nutrition, training, conditioning,
  supplements, recovery, behavioral), each shallower; expand depth in later versions.
- **Curation policy:** tiered sign-off — high-impact atoms require human approval; routine
  atoms auto-admit on passing deterministic verification + cross-model critique.
- **Provenance:** built fresh via an offline pipeline (not imported wholesale from an
  existing corpus).
- **Storage:** versioned structured files in git as source of truth; DB + embeddings are
  derived build artifacts.

---

## SP1 design

### 1. Two assets

**Evidence Atom Bank** — the *science*. One record per atom:

| Field | Notes |
|---|---|
| `id` | Stable, e.g. `EA-NUT-0042` |
| `domain` | nutrition / training / conditioning / supplements / recovery / behavioral |
| `claim` | One sentence |
| `evidence_level` | L1 (meta-analysis/SR) … L4 (expert opinion) |
| `citations[]` | DOI/PMID, each gate-verified |
| `locator_quotes[]` | Verbatim supporting passage + locator per citation |
| `population_applicability` | Ranges the evidence supports: age, sex, training-status, dose-magnitude, duration |
| `effect` | Size + CI + endpoint |
| `contraindications` | |
| `verification` | Existence + faithfulness outcomes (from the shipped citation gate) |
| `tier` | `high-impact` / `routine` |
| `approval` | Human approver + date, or `auto` |
| `library_version` | Version this atom was admitted/last-changed in |
| `freshness` | Last reviewed date + expiry |

**Recommendation Pattern Library** — how science *becomes a personalized rec*. One record per
pattern:

| Field | Notes |
|---|---|
| `id` | e.g. `RP-NUT-protein-band` |
| `pattern` | e.g. "protein target band" |
| `parameterization` | Variable bands + rules mapping ClientState → a point (e.g. 1.6–2.2 g/kg) |
| `backing_atom_ids[]` | Evidence atoms this pattern rests on |
| `falsification_signal` | Observable + check-date template |
| `safety_bounds` | Hard limits the personalization may not cross |
| `applies_because` / `doesnt_apply_if` | Applicability conditions |
| `tier`, `approval`, `version` | As above |

SP2 *selects* patterns, fills parameters from `ClientState`, and cites backing atoms — it
never re-derives science.

### 2. Storage & versioning

**Source of truth:** versioned structured files in git — one YAML/JSON record per atom/pattern,
foldered by domain. A **build step** compiles them into (a) a queryable index/DB and (b) an
embeddings store for SP2 retrieval.

Rationale:
- Human-reviewable **diffs are the tiered sign-off mechanism** — high-impact atoms approved via
  PR review.
- Free version history; a plan cites a library **git tag/version**.
- Deprecation = a flag in the file.
- The DB + embeddings are **derived artifacts**, regenerated per release, never hand-edited.

Rejected: DB-as-source-of-truth — weaker provenance and review ergonomics for a
quality-critical, human-approved asset.

### 3. Offline curation pipeline (tiered sign-off)

Runs offline, amortized across all clients. This is where the slow strong-model reasoning +
citation verification now lives (paid once, not per client):

1. **Harvest** — per-domain literature scan (PubMed / Crossref / OpenAlex; reuse the
   `sources_catalog` query templates) → candidate sources.
2. **Extract** — strong model (Opus / GPT-5.5) drafts candidate atoms (claim, population,
   effect, citations).
3. **Verify (deterministic)** — the shipped citation gate: existence (title-similarity ≥0.70 +
   year ±1, DOI_MISMATCH detection) + claim-faithfulness (locator quotes, numeric tolerance).
   Fail → reject.
4. **Cross-model critique** — a *different* model family (GPT-5.5 or Gemini) re-checks
   faithfulness + population applicability. Disagreement → escalate to human.
5. **Tier & route** — high-impact (safety, doses, calorie/macro targets, contraindications) →
   human approval queue (PR sign-off); routine → auto-admit if steps 3+4 pass.
6. **Derive patterns** — approved atoms → parameterized Recommendation Patterns with
   falsification signals + safety bounds (high-impact patterns also human-approved).
7. **Release** — version bump, regenerate DB + embeddings, tag.

### 4. Staying current

Scheduled per-domain re-harvest (≈monthly) re-runs harvest→verify; newer systematic
reviews/meta-analyses supersede existing atoms (deprecate or downgrade); the freshness gate
flags atoms past expiry. Suitable for a `/schedule` routine.

### 5. Success criteria

- A versioned library covering all current council domains; every atom carries verified
  citations + locator quotes + population applicability + tier + approval state.
- Every high-impact atom is human-approved; every routine atom passed the deterministic gate +
  cross-model critique.
- SP2 can retrieve and cite atoms with **zero live literature lookups**.
- Any produced plan can name the exact library version it was built against.

## Risks & mitigations

- **Broad scope → large curation effort up front.** Mitigate: prioritize high-impact atoms
  first; routine atoms flow through automation; coverage can deepen in later versions.
- **Fast models misapply evidence.** Mitigate: fast models may select/summarize/render but may
  not invent citations or override atom constraints (enforced at SP2).
- **Library staleness / over-generic patterns.** Mitigate: versioned releases, scheduled
  re-harvest, deprecation flags, human approval for high-impact rules.
- **Curation pipeline cost.** It is real and recurring, but offline and amortized across all
  clients — the entire point of the redesign.

## Out of scope (this doc)

SP2 (per-client compiler runtime) and SP3 (dynamic re-planning / Change Ledger) — referenced
for context only. The current council pipeline remains in place until SP1+SP2 can replace it.

## Provenance

Architecture independently proposed by Claude Opus 4.7 and GPT-5.5 (via Codex), which converged
on the same library-first compiler design. Builds on the citation existence + claim-faithfulness
gate shipped 2026-05-21 (see `2026-05-21-citation-verification-upgrade.md`).
