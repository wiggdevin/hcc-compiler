# HCC Compiler — Library Foundation (SP1 · Plan 1)

## Context

`hcc-compiler` is the greenfield engine for the Health Coach Council redesign: instead of
re-deriving sports science per client (the legacy ~2-hour council), it will select from a
pre-verified **evidence library** and personalize. This PRD covers **only the first build
unit — the Library Foundation**: the validated, versioned data model plus the tooling to
author it as files and compile it into a queryable index.

- Architecture & rationale: `docs/specs/sp1-evidence-library-design.md`
- Task-by-task plan (exact files, code, commands): `docs/plans/sp1-plan1-library-foundation.md`
- Visual overview: `docs/explainer.html`

**Execute the plan in `docs/plans/sp1-plan1-library-foundation.md` task-by-task.** It contains
the complete code and commands for every task. This PRD defines what "done" means and how each
piece is mechanically verified.

## In scope (this PRD)

A new repo at `~/projects/hcc-compiler/` containing:
- `EvidenceAtom` and `RecommendationPattern` pydantic v2 models.
- A YAML loader that validates records and reports per-file errors.
- A cross-record validator (duplicate IDs, dangling `backing_atom_ids`, and the tiered-sign-off
  rule: high-impact atoms may not be `auto`-approved) + a CLI.
- A build step compiling validated YAML records into a version-stamped SQLite index.
- At least 3 real, citation-verified seed atoms across ≥2 domains + 1 pattern, and a `Makefile`.

## Out of scope (do NOT build — later plans)

- The offline **curation pipeline** (harvest / extract / verify / cross-model critique / sign-off / release) — that is SP1 Plan 2.
- The **embeddings store / retrieval API** — SP1 Plan 3.
- The **per-client compiler runtime** (SP2) and **dynamic re-planning / Change Ledger** (SP3).
- Any web service, API server, CLI beyond the two curation scripts, logging, CI config, or Docker.

If tempted to add anything above, log a scope-creep flag and skip it.

## Constraints

- Python 3.11; dependencies limited to `pydantic>=2.6`, `pyyaml>=6.0`, and `pytest` (dev). No others.
- No network calls and no LLM/API calls in this plan — it is the deterministic foundation.
- Commit after each task (the plan specifies the messages).
- Records are YAML files of record under `library/`; the SQLite index is a derived build artifact.

## Success Criteria

Each criterion is verified by running its command from the repo root with the venv active
(`cd ~/projects/hcc-compiler && . .venv/bin/activate`) and capturing stdout + exit code as proof.

| # | Criterion | Verification command | Pass condition |
|---|---|---|---|
| SC1 | Repo scaffolds and the package imports | `python -c "import hcc_compiler; print('ok')"` | prints `ok`, exit 0 |
| SC2 | Atom + pattern models validate correctly | `pytest tests/test_models_atom.py tests/test_models_pattern.py -q` | exit 0 |
| SC3 | YAML loader loads valid records and reports invalid ones by path | `pytest tests/test_loader.py -q` | exit 0 |
| SC4 | Validator catches dup IDs, dangling refs, and high-impact `auto`-approval | `pytest tests/test_validate.py -q` | exit 0 |
| SC5 | Build compiles a version-stamped, queryable SQLite index | `pytest tests/test_build_index.py -q` | exit 0 |
| SC6 | Seeded library has ≥3 cross-domain atoms in the built index | `make build && sqlite3 library.db "SELECT COUNT(*) FROM atoms;"` | count ≥ 3 |
| SC7 | End-to-end: validate + build + full test suite all green | `make check` | exit 0 |

## Done when

Every success criterion SC1–SC7 has a captured proof artifact (command, output, exit code) and
the seed library validates, builds, and queries cleanly.
