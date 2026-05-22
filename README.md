# hcc-compiler

The greenfield engine for the **Health Coach Council** redesign — a *library-first plan
compiler* that replaces the legacy ~2-hour multi-agent council. Instead of re-deriving sports
science for every client, it selects from a pre-verified evidence library and personalizes,
targeting **~7–14 min per fresh plan** and **near-instant re-planning** when a client's
situation changes.

Architecture independently converged on by Claude Opus 4.7 and GPT-5.5.

## Status

| Sub-project | What it is | Status |
|---|---|---|
| **SP1** | Evidence library + offline curation pipeline | **SHIPPED** (Plans 1+2+3, 179 atoms + 8 patterns across 6 domains) |
| **SP2** | Per-client compiler runtime (deterministic core) | **SHIPPED** — `compile(intake) -> EvidencePack` with applicability scoring, contraindication checks, markdown render, CLI |
| SP3 | Dynamic re-planning / Change Ledger engine | designed (future) |

## Quick start — compile a personalized plan

```bash
# 1. Build the library SQLite index (once, or whenever YAML changes)
make build

# 2. Compile a plan for a client intake
make compile INTAKE=tests/fixtures/intakes/intake_amy_runner.yaml
# → writes intake_amy_runner.json (full EvidencePack) + intake_amy_runner.md (coach-readable report)

# Or call the CLI directly with flags
uv run python scripts/compile_plan.py tests/fixtures/intakes/intake_carl_strength.yaml \
    --db library.db \
    --out-json out/carl.json \
    --out-md out/carl.md \
    --top-k 5
```

Example outputs for three persona intakes are checked in under `docs/examples/sp2/`.

### Client intake schema (minimal)

```yaml
client_id: amy_runner
library_version: "0.1.0"
demographics:
  age: 32
  sex: F
  weight_kg: 58.0
  height_cm: 168.0
training_status: recreational   # untrained | recreational | trained | competitive
goals:
  - endurance
  - performance
current_regimen: |
  Free-text description (≤2000 chars).
constraints:
  - type: injury
    detail: left knee mild patellar tendinopathy
contraindications: []   # e.g. ["renal insufficiency (CKD stage 2)"]
```

See `src/hcc_compiler/sp2/intake.py` for the full Pydantic schema.

## Documents

| Doc | Purpose |
|---|---|
| `docs/PRD.md` | SP1 Plan 1 PRD (library foundation) |
| `docs/PRD-plan2.md` | SP1 Plan 2 PRD (curation pipeline) |
| `docs/PRD-plan3.md` | SP1 Plan 3 PRD (patterns + embeddings) |
| `docs/PRD-sp2.md` | **SP2 PRD — per-client compiler runtime** |
| `docs/specs/sp1-evidence-library-design.md` | Full SP1 architecture & rationale |
| `docs/plans/sp2-compiler-runtime.md` | SP2 task-by-task implementation plan |
| `docs/explainer.html` | Visual overview of the whole redesign |
| `docs/examples/sp2/{amy,carl,sam}.{md,json}` | Real example outputs of `make compile` against the live library |

## Pipeline at a glance

```
SP1 (curation, offline):
  harvest (PubMed/Crossref) → extract (LLM) → verify (citation gate)
                                                 → route → library/atoms/<domain>/
                                                         → library/queue/    (held for human review)
  build_index → SQLite + Ollama embeddings
  derive_patterns (cluster + LLM synth) → library/patterns/<domain>/

SP2 (per client, online):
  intake YAML → derive_queries → retrieve (cosine over SQLite)
                                  → score_applicability + check_contraindications
                                  → EvidencePack → render_markdown / JSON
```

## Run a build autonomously

This build is driven by the `/goal` skill — an autonomous, task-by-task loop (route → execute via
a fresh subagent → mandatory adversary review → mechanical verification with proof on disk → next
task). From a terminal:

```bash
cd ~/projects/hcc-compiler
claude                  # start Claude Code in this repo
/goal docs/PRD-sp2.md   # drive the most recent PRD to mechanically-verified done
```

`/goal` writes its state, run log, and per-criterion proof artifacts under `~/Inbox/goal-*`.
Resume an interrupted run with `/goal --resume hcc-compiler-sp2`.

## Verify locally

```bash
make check   # validate library + build_index + run the full pytest suite
```

The suite is ~475 deterministic offline tests at SP2-shipped (HEAD). All HTTP / LLM / Ollama
calls are mocked in tests; live modes gated behind `HCC_LIVE_HTTP=1`, `HCC_LIVE_LLM=1`, and
`HCC_LIVE_EMBED=1`.
