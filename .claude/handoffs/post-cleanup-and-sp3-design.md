# Handoff: post-nutrient-timing cleanup + SP3 design
status: done
date: 2026-05-28
branch: main   last-commit: 9050339 docs(sp3): change-ledger design — DAG, hashing, incremental invalidation

## Active Task
Resolve the six follow-ups from the nutrient-timing-expansion handoff (persona JSON skew, FAIL-atom triage, queued-pattern triage, compiler-API ops hygiene, web test infra + .env.example, SP3 design doc).

## Goal
Four phases, each as its own commit, all green; library version stays at 0.2.0; pytest at repo root green; `pnpm test` green; compiler-api integration suite green; SP3 design doc exists. All acceptance criteria in `~/.claude/plans/rustling-waddling-aurora.md` met.

## Decisions
- 18 NUT atoms + 1 SUP + 1 TRA stay admitted; library version stays `0.2.0`. **Why:** the FAIL recovery added 10 atoms without bumping library semantics — claims were already shape-valid; only the verify pipeline was wrong.
- `load_source_texts()` now concatenates abstract + full_text (was full_text-or-abstract). **Why:** meta-analytic quotes often live in the abstract but get rephrased in the PMC body; Layer-2 substring needs both. Replaces `test_prefers_full_text_when_present` with `test_concatenates_abstract_and_full_text`.
- Compiler-API auth pattern stays static-bearer (`COMPILER_API_TOKEN`), not JWT. **Why:** the JWT story in the README was fiction — `auth.py` only ever did `tok != _expected_token()`. Cleaned all docs + dropped PyJWT.
- `services/compiler-api/auth.py` made `Authorization` Optional so missing-auth returns 401, not 422. **Why:** semantics — "auth required" should be 401 across the board, not split between 401 and FastAPI's Header(...) validation 422.
- `fly.toml` `LIBRARY_DB_PATH` override removed. **Why:** entrypoint.sh seeds `/data/library.db` from `/data-seed/library.db` on container start; the override was bypassing the seed mechanism and reading directly from the baked image.
- Vitest with boundary mocks for web; no Playwright e2e in this round. **Why:** the "no mocks" rule is backend-specific (Postgres integration); web is a thin client where MSW + factory mocks for Supabase/Resend/LLM are standard.
- `normalizeFromAddress()` made a real export with explicit `raw` parameter. **Why:** previously private — couldn't be unit-tested without forcing module re-evaluation.
- `.gitignore` exception needed in BOTH root `.gitignore` AND `web/.gitignore`. **Why:** Next.js scaffold ships its own `.env*` rule that overrides parent.
- SP3 is design-only this round. **Why:** PRDs explicitly mark SP3 as post-SP2; SaaS launch must validate the per-tenant cost before we implement DAG tracking. Sliced into SP3.1/3.2/3.3 as future plans.
- ASSUMED: server-side UUID `pack_id` in `compile_metadata` is the right primary key for `pack_provenance` (Q1 in SP3 doc). Round-tripping through Supabase introduces a write-dep on the web edge; UUID lets the compiler stand alone.
- ASSUMED: pack-deletion handled via tombstone hash (Q2 in SP3 doc), not row delete. Provenance rows stay intact; tombstone flagged via `content_hash IS NULL`.

## Files
- `~/.claude/plans/rustling-waddling-aurora.md` — the approved 4-phase plan for this batch.
- `library/atoms/{nutrition,supplements,training}/EA-*.yaml` — 10 ex-FAIL atoms now admitted with `approval: "Devin Wiggins 2026-05-28"` and `library_version: 0.2.0`.
- `library/patterns/recovery/RP-REC-cold-water-immersion-post-exercise.yaml` — admitted from queue.
- `library/queue/_PATTERN_NOTES.md` — discard log for 5 duplicate patterns.
- `src/hcc_compiler/harvest/abstracts.py` — `load_source_texts` rewritten to concatenate.
- `tests/harvest/test_abstracts.py` — updated to assert concat semantics.
- `scripts/curation/reextract_fails.py` — strict-prompt re-extract helper (kept for future FAIL triage).
- `services/compiler-api/main.py` — slowapi limiter + body-size middleware + per-request log middleware.
- `services/compiler-api/auth.py` — Optional Authorization header so missing → 401.
- `services/compiler-api/requirements.txt` — slowapi==0.1.9 added, PyJWT dropped.
- `services/compiler-api/fly.toml` — `LIBRARY_DB_PATH` override removed.
- `services/compiler-api/tests/test_app_integration.py` — 10 FastAPI TestClient cases.
- `services/compiler-api/README.md` — full rewrite reflecting actual auth + env vars.
- `web/.env.example` — 16 active + 3 optional env vars, grouped by service.
- `web/.gitignore` + root `.gitignore` — `!.env.example` exceptions.
- `web/vitest.config.ts`, `web/vitest.setup.ts`, `web/package.json` (test scripts + deps).
- `web/lib/schedule/types.test.ts`, `web/lib/resend.test.ts` — 13 test cases.
- `web/lib/resend.ts` — `normalizeFromAddress` exported with `raw?: string | null` parameter.
- `docs/specs/sp3-change-ledger.md` — 231-line design spec.
- `docs/examples/sp2/*.json` + `web/public/sp2/*.json` — 9 personas regenerated against 0.2.0.

## Evidence
- pytest at repo root: `537 passed in 21.47s` (after the abstracts test update).
- compiler-api pytest: `16 passed, 2 warnings in 3.11s` (6 existing smoke + 10 new integration).
- `cd web && pnpm test`: `Test Files 2 passed (2)`, `Tests 13 passed (13)`, duration `2.17s`.
- Fly live health: `https://hcc-compiler-api.fly.dev/library/version` returns `{"library_version":"0.2.0","pattern_count":23,"atom_count":225}` after deploy.
- Fly machine ID: `825472f7902768`, redeployed `--strategy immediate`.
- Vercel web: no separate deploy needed for Phase 3 (vitest + .env.example don't change runtime). The earlier Phase 2 of the nutrient-timing branch left web at deployment `hcc-compiler-lprwe2gvw-devin-wiggins-projects.vercel.app`.
- Resend most-recent send IDs (kept from nutrient-timing smoke; not re-fired this round): `8076c50a-6ad2-42a9-a2c9-61d5a227abdd` (timing-visible) and `8c0cb62a-131c-4d51-a14c-11e3b2c4ecc6` (pre-fix).
- Commits this round, in order: `7fe3473`, `82301f6`, `f8b8f33`, `be2bce9`, `b2bf9db`, `d1f6648`, `9050339`. All on `origin/main`.
- Pack provenance for qa-smoke (kept for SP3 reference): pack_id `8e316374-6739-4996-ae44-cdbbbe2a20e3`, intake_id `59bc4f1e-5043-472d-ac81-e3eab7de3e6d`, coach_id `27fdab0e-a889-4e20-a06d-f61797153b3b`.

## Open Questions
- QUESTION: should we add Phase 3 follow-up tests for `share-loader.ts` and `share/route.ts`? They need MSW + Supabase factory mocks. Acceptance bar (≥10 cases) is already hit at 13, so this is enhancement not blocker.
- QUESTION: do the regenerated persona JSONs (Phase 1a) need a Playwright visual diff against `/clients/{slug}/overview` to catch layout regressions from changed atom/pattern counts? Personas all came back at 100% integrity, but counts shifted (11 patterns now vs 9 baseline).
- QUESTION: SP3 implementation timing — when does SaaS launch validate the cost enough to start SP3.1 (hashing)? Plan defers indefinitely; revisit after first paying coach.

## Next Action
Delete this handoff file — work is shipped, all four phases green, library 0.2.0 live on Fly + qa-smoke pack. If SP3.1 or the two QUESTION enhancements come up, open a new plan.
