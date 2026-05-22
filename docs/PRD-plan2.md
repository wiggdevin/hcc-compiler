# HCC Compiler — Curation Pipeline MVP (SP1 · Plan 2)

## Context

`hcc-compiler` shipped SP1 Plan 1 on 2026-05-22 (HEAD `4d2caba`): the Library Foundation — pydantic models, YAML loader, cross-record validator, SQLite build_index, 3 seed atoms. This PRD covers **SP1 Plan 2**: the **offline curation pipeline MVP** that turns published literature into validated evidence atoms ready for the library.

- Architecture & rationale: `docs/specs/sp1-evidence-library-design.md` §3 (the 7-step pipeline)
- Citation-gate spec: `~/projects/plugins/Health Coach Council Plugin/source/docs/plans/2026-05-21-citation-verification-upgrade.md` (Layer 1 + Layer 2 — defines the gate's behavior exactly)
- Task-by-task plan (exact files, code, commands): `docs/plans/sp1-plan2-curation-pipeline.md`

**Execute the plan in `docs/plans/sp1-plan2-curation-pipeline.md` task-by-task.** This PRD defines what "done" means and how each piece is mechanically verified.

## In scope (this PRD)

A curation pipeline MVP that consumes published literature and produces validated YAML atoms:

- **Deterministic citation gate** (Layer 1 existence + Layer 2 faithfulness) per the 2026-05-21 spec.
- **Per-domain harvest** of PubMed + Crossref using query templates ported from `sources_catalog.md`.
- **LLM extract** that turns a harvested candidate into a draft `EvidenceAtom` YAML via Z.AI GLM (anthropic-compatible endpoint).
- **Tier & route** that auto-admits routine atoms with full-PASS gate verdicts into `library/atoms/`, and queues all high-impact atoms (and anything below full-PASS) into `library/queue/` for human PR review.

Three new top-level dirs at runtime: `harvest-output/`, `draft-output/`, `verify-output/`, plus `library/queue/`. All four are gitignored except for committed records.

## Out of scope (do NOT build — later plans)

- **Cross-model critique** (Step 4 of the design spec) — stub the interface; full implementation is Plan 3.
- **Pattern derivation** (Step 6) — Plan 3.
- **Release-tag automation + embeddings store** (Step 7) — Plan 3 / SP1 Plan 3.
- **Scheduled re-harvest / `/schedule` routine** — operational concern, not Plan 2.
- Any web service, server, additional CLI beyond the four scripts (`harvest.py`, `extract.py`, `verify.py`, `route.py`).

If tempted to add anything above, log a scope-creep flag and skip it.

## Constraints

- **Zero new runtime dependencies.** Plan 1 locked deps to `pydantic>=2.6`, `pyyaml>=6.0`, `pytest>=8.0` (dev). Plan 2 stays inside that envelope: stdlib `urllib.request` for HTTP, stdlib `difflib.SequenceMatcher` for title similarity, stdlib `json` for LLM payloads. No `requests`, `anthropic` SDK, `python-Levenshtein`, or anything else.
- **Subscription-only LLM.** Extract step routes through Z.AI's anthropic-compatible endpoint (`ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic`) under GLM Coding Max subscription. Token from `ANTHROPIC_AUTH_TOKEN` (resolved from `zsvault get zai_api_key` at run time). Never the billed Anthropic SDK.
- **Tests must run offline + deterministically.** All HTTP calls mocked with `unittest.mock`; all LLM calls go through a fake transport. Live mode gated behind `HCC_LIVE_HTTP=1` / `HCC_LIVE_LLM=1`.
- **All commits authored by `Dev Wiggins <devin@zerosumsolutions.com>`** — every commit command in worker subagents MUST pass `-c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins"`.
- **Workers MUST NOT `git add` untracked-but-present files** outside the explicit file list of their task (Plan 1 hard lesson).
- Commits prefixed `feat(gate):` / `feat(harvest):` / `feat(extract):` / `feat(route):` / `feat(curation):` / `docs:`.

## Success Criteria

Each criterion is verified by running its command from the repo root with the venv active (`cd ~/projects/hcc-compiler && . .venv/bin/activate`) and capturing stdout + exit code as proof.

| # | Criterion | Verification command | Pass condition |
|---|---|---|---|
| SC1 | Title-similarity primitive (≥0.70 match, case/punct-insensitive) | `pytest tests/citation_gate/test_text.py -q` | exit 0 |
| SC2 | Numeric-tolerance helper (scalar / range / percentage) | `pytest tests/citation_gate/test_numbers.py -q` | exit 0 |
| SC3 | PubMed + Crossref lookup clients (mocked) | `pytest tests/citation_gate/test_lookup.py -q` | exit 0 |
| SC4 | Layer 1 existence verifier returns one of 5 outcome strings | `pytest tests/citation_gate/test_layer1.py -q` | exit 0 |
| SC5 | Layer 2 faithfulness verifier returns one of 5 verdict strings | `pytest tests/citation_gate/test_layer2.py -q` | exit 0 |
| SC6 | `verify_atom` orchestrator + CLI runs over all 3 Plan-1 seed atoms with no FAILs | `pytest tests/citation_gate/test_verify_atom.py -q` | exit 0 |
| SC7 | Per-domain harvest query registry + CLI (mocked PubMed) | `pytest tests/harvest/test_harvest.py -q` | exit 0 |
| SC8 | Z.AI GLM client (fake transport asserts request shape + auth header) | `pytest tests/llm/test_glm_client.py -q` | exit 0 |
| SC9 | Extract step turns harvested candidate into a draft atom that round-trips through `EvidenceAtom.model_validate` | `pytest tests/test_extract.py -q` | exit 0 |
| SC10 | Tier & route CLI (decision matrix table-tested) | `pytest tests/test_route.py -q` | exit 0 |
| SC11 | End-to-end pipeline smoke via `make curate-smoke && make check` (Plan-1 invariants still hold) | `make curate-smoke && make check` | exit 0 |

## Done when

Every success criterion SC1–SC11 has a captured proof artifact (command, output, exit code) under `~/Inbox/goal-proof-hcc-compiler-curation-pipeline/`, the citation gate clears all 3 Plan-1 seed atoms without `FAIL`, and the smoke pipeline routes the fixture candidate into `library/queue/` cleanly.
