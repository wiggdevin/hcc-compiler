# HCC Compiler — Per-Client Compiler Runtime (SP2)

## Context

`hcc-compiler` shipped SP1 (Plans 1+2+3) on 2026-05-22. The library is at 179 atoms + 8 patterns across 6 domains, with a working retrieval surface (`scripts/retrieve.py`, cosine over Ollama embeddings, SQLite index, ~200 vectors brute-force sub-millisecond). 148 deterministic offline tests, all green at HEAD `b446575`.

This PRD covers **SP2 — the per-client compiler runtime**. SP1 built the library substrate; SP2 turns it into a product. Given a structured client intake (their goals, current regimen, demographics, constraints), the compiler emits a personalized evidence pack: which atoms/patterns apply, with citations, safety bounds, and applicability warnings.

- Architecture & rationale: `docs/specs/sp1-evidence-library-design.md` §8 sketches the SP2 input/output flow ("ClientState → retrieval → plan-graph compilation → single strong-model arbitration → targeted critics → evidence-ledger → deterministic render"). This PRD ships the **deterministic core** of that flow: intake → retrieval → applicability → safety → render. LLM arbitration and critics are deferred to SP2-full / SP3.
- Task-by-task plan (exact files, code, commands): `docs/plans/sp2-compiler-runtime.md`.
- All commits authored by `Dev Wiggins <devin@zerosumsolutions.com>`.

**Execute the plan in `docs/plans/sp2-compiler-runtime.md` task-by-task.** This PRD defines what "done" means and how each piece is mechanically verified.

## In scope (this PRD)

A deterministic per-client compiler runtime:

- **`ClientIntake` Pydantic model** at `src/hcc_compiler/sp2/intake.py` — structured intake with demographics, goals, training status, current regimen, constraints, contraindications, library_version. YAML loader `load_intake(path) -> ClientIntake` mirroring the `loader.load_dir` pattern.
- **`EvidencePack` Pydantic model** at `src/hcc_compiler/sp2/pack.py` — output container with per-domain blocks (PatternMatch + AtomMatch lists), compile metadata, and JSON round-trip.
- **Applicability scoring** at `src/hcc_compiler/sp2/score.py` — `score_applicability(atom, intake) -> float` in `[0, 1]`. Weighted rubric: age band (0.4), sex (0.2), training_status (0.4). Age-band normalizer built from the actual values present in `library/atoms/` (workers will enumerate via `grep -h "  age:" library/atoms/**/*.yaml | sort -u` before writing the rubric).
- **Safety / contraindication checking** at `src/hcc_compiler/sp2/safety.py` — `check_contraindications(record, intake) -> list[str]`. Case-insensitive substring match over `atom.contraindications` and `pattern.doesnt_apply_if` against `intake.contraindications` + constraint details. Hits become warnings.
- **Query derivation** at `src/hcc_compiler/sp2/queries.py` — `derive_queries(intake) -> dict[Domain, list[str]]`. Maps goals + training_status + constraints to per-domain text queries.
- **`compile()` orchestrator** at `src/hcc_compiler/sp2/compile.py` — version-guard → derive_queries → per-domain `retrieve.query()` → hydrate full records from SQLite → score → filter → pack. Raises `LibraryVersionMismatch` on version drift. Pure function (no LLM calls).
- **Markdown renderer** at `src/hcc_compiler/sp2/render.py` — `render_markdown(pack) -> str`. Six-domain template, top-3 backing atoms per pattern (by `population_match_score`), inline `[claim — DOI/PMID]` citations, warnings block.
- **CLI** at `scripts/compile_plan.py` — `python scripts/compile_plan.py <intake.yaml> [--db library.db] [--out-json path] [--out-md path] [--top-k 5] [--no-version-check]`. Makefile `compile:` target wired.
- **Fixtures + smoke** — 3 persona intakes at `tests/fixtures/intakes/intake_{amy_runner,carl_strength,sam_recomp}.yaml` covering different goals / training statuses / contraindications. End-to-end smoke test exercises the full pipeline against the real `library.db` and asserts ≥3 of 6 domains return content per persona.
- **Committed examples** — rendered packs (`.md` + `.json`) under `docs/examples/sp2/{amy,carl,sam}.{md,json}` so a coach reading the repo sees what the output looks like.

## Out of scope (do NOT build — SP2-full / SP3)

- **LLM arbitration inside the compiler.** No "strong model picks the right pattern" step. Today: deterministic scoring + retrieval.
- **Targeted critic agents.** No cross-model second-opinion on the compiled pack. Today: produce the pack, render it, done.
- **Change Ledger / dynamic re-planning.** SP3. No event ingestion, no diff detection, no auto re-route.
- **Multi-pass plan-graph.** Today: one pass, per-domain, independent. No cross-domain reasoning (e.g., "your protein dose conflicts with your CKD constraint" — that's a critic, deferred).
- **Web UI / HTTP API.** CLI + JSON/Markdown output is the entire surface tonight.
- **Scheduled re-harvest, semver release-tag automation, web dashboards** — operational concerns, not SP2 core.

If tempted to add any of the above, log a scope-creep flag and skip.

## Constraints

- **Zero new runtime dependencies.** Pydantic and PyYAML are already in `pyproject.toml`. No new packages (no scikit-learn, no numpy, no anything).
- **Pure deterministic — no LLM calls in `compile()`.** All scoring, filtering, and ranking is algorithmic. LLM-based arbitration is explicitly out of scope per above.
- **Reuse existing models.** Workers MUST import `EvidenceAtom`, `RecommendationPattern`, `Domain`, `Tier`, `PopulationApplicability` from `hcc_compiler.models`. Do not redefine.
- **Reuse `retrieve.query()`.** Workers MUST use `hcc_compiler.retrieve.query(text, k, domain, db_path)` as the only retrieval surface. Do not build a parallel search path.
- **Tests must run offline + deterministically.** Mock `hcc_compiler.llm.embed_client.embed` like `tests/retrieve/test_retrieve.py` already does. No real Ollama, no network.
- **Match commit authorship.** All commits authored by `Dev Wiggins <devin@zerosumsolutions.com>`. Workers pass `-c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins"` when committing.
- **No `git add` of untracked-but-present files** outside the explicit task file list.
- **Commits prefixed** `feat(sp2-intake):` / `feat(sp2-pack):` / `feat(sp2-score):` / `feat(sp2-safety):` / `feat(sp2-queries):` / `feat(sp2-compile):` / `feat(sp2-render):` / `feat(sp2-cli):` / `test(sp2):` / `docs(sp2):`.

## Success Criteria

Each criterion is verified by running its command from the repo root with `uv run` and capturing stdout + exit code as proof under `~/Inbox/goal-proof-hcc-compiler-sp2/SC{n}.txt`.

| # | Criterion | Verification command | Pass condition |
|---|---|---|---|
| SC1 | `ClientIntake` + `Demographics` + `Constraint` pydantic models validate good inputs and reject bad demographics (negative age, unknown sex enum, etc.). YAML loader works. | `uv run pytest tests/sp2/test_intake_model.py -q` | exit 0 |
| SC2 | `EvidencePack`, `DomainBlock`, `PatternMatch`, `AtomMatch`, `CompileMetadata` models round-trip JSON cleanly | `uv run pytest tests/sp2/test_pack_model.py -q` | exit 0 |
| SC3 | `score_applicability(atom, intake)` returns a deterministic `[0, 1]` score; age band / sex / training_status drive the score; age normalizer covers all values present in `library/atoms/` | `uv run pytest tests/sp2/test_score.py -q` | exit 0 |
| SC4 | `check_contraindications(record, intake)` flags real conflicts (e.g., CKD vs creatine, knee injury vs deep squat). Case-insensitive substring match. | `uv run pytest tests/sp2/test_safety.py -q` | exit 0 |
| SC5 | `compile()` returns a full `EvidencePack` for a fixture intake against a fixture SQLite library (mocked embeddings). Per-domain blocks populated; metadata fields filled. | `uv run pytest tests/sp2/test_compile.py -q` | exit 0 |
| SC6 | `compile()` raises `LibraryVersionMismatch` when `intake.library_version != meta.library_version` in the SQLite | `uv run pytest tests/sp2/test_version_guard.py -q` | exit 0 |
| SC7 | `render_markdown(pack)` produces markdown with all 6 domain sections, inline citations (DOI/PMID), and warnings block where contraindications hit | `uv run pytest tests/sp2/test_render.py -q` | exit 0 |
| SC8 | `scripts/compile_plan.py` CLI: given an intake YAML + db path, writes JSON pack + markdown pack to disk; `--no-version-check` works | `uv run pytest tests/sp2/test_compile_cli.py -q` | exit 0 |
| SC9 | End-to-end smoke: 3 persona intakes (amy_runner, carl_strength, sam_recomp) compile against the **real** `library.db`; each pack has ≥3 of 6 domains non-empty; persona example outputs committed under `docs/examples/sp2/` | `uv run pytest tests/sp2/test_compile_smoke.py -q` | exit 0 |
| SC10 | SP1 regression intact + new SP2 docs in place | `make check && test -f docs/PRD-sp2.md && test -f docs/plans/sp2-compiler-runtime.md` | exit 0, 148+N tests pass (N = new SP2 tests, expected ~20-25) |

## Done when

Every success criterion SC1–SC10 has a captured proof artifact (command, output, exit code) under `~/Inbox/goal-proof-hcc-compiler-sp2/`. Three persona evidence packs committed under `docs/examples/sp2/`. `make compile INTAKE=tests/fixtures/intakes/intake_amy_runner.yaml` works end-to-end. `make check` exits 0 at the new test count (148 baseline + ~20–25 new SP2 tests). No new runtime deps in `pyproject.toml`. All commits authored by Dev Wiggins.
