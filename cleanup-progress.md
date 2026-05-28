# Cleanup Progress

## 2026-05-28 18:37 — Phase 01 Isolate
- did: backup branch `backup/pre-cleanup-20260528-183724`; stashed `stash@{0}` containing modified `.claude/handoffs/nutrient-timing-expansion.md` + untracked `.claude/handoffs/post-cleanup-and-sp3-design.md`; created `cleanup/handoff-20260528` off `main` @ `9050339`.
- decisions: tree is cleaner than the user described — only handoff working state, no deleted YAMLs in queue (those landed in commit `f8b8f33`). Proceeded with auto-stash.

## 2026-05-28 18:39 — Phase 02 Map Codebase
- did: read `~/.codex/skills/cleanup-playbook/SKILL.md` + 10 step files; listed root; ran wc on src/ and scripts/; ran rg for TODO/FIXME/debug; ran git log for env/keys in history.
- findings:
  - Stack: Python (`uv` + `pyproject.toml`) + Next.js web sub-app + Supabase + FastAPI sidecar on Fly.
  - Entry points: `scripts/compile_plan.py` (CLI); `services/compiler-api/main.py` (HTTP); `web/app/` (Next.js); `Makefile` (curation pipeline).
  - 599 tracked files. `library.db` NOT tracked (in .gitignore via `*.db`).
  - Oversized files: `src/hcc_compiler/sp2/render.py` 354L; `sp2/score.py` 325L; `scripts/curation/wave_d_curate.py` 326L; `scripts/audit_derive_queries.py` 319L; `scripts/curation/tighten_tags.py` 316L. All marginal — no runaway concerns.
  - TODO/FIXME: only in `src/hcc_compiler/patterns/derive_prompt.md` (LLM prompt — intentional).
  - Debug logs: only in `web/scripts/smoke-schedule.ts` (smoke script — intentional).
  - No .env / .pem / .key / credentials in git history.
  - Gitignored: `harvest-output/`, `draft-output/`, `draft-output-archive/`, `verify-output/`, `*.db`, `.venv/`, `web/node_modules/`, `web/.next/`.
  - NOT gitignored but present in working dir: `scratch/` (contains `qa-smoke-intake.yaml`, 435 bytes).
- decisions: visible mess in working dir is gitignored runtime artifacts. Real cleanup surface is small — README staleness, `scratch/`, possible one-shot script archeology.

## 2026-05-28 18:42 — Phase 03 Ground deps
- did: skipped per playbook — no SDK / framework call signature changes planned in this cleanup. The compiler-api `slowapi`/`fastapi`/`fastembed` additions already landed in commit `be2bce9` and are documented in services/compiler-api/README.md.
- decisions: N/A — nothing to ground.

## 2026-05-28 18:43 — Phase 04 Audit + Plan
- did: produced own audit (Phase 02 findings); codex audit completed (exit 0, 6613-line output, 20 findings ranked H/M/L). Reconciled both into bundles below.
- codex: 4 HIGH (provision_saas readback bug, shared bearer = no per-coach authz, chunked body bypass, silent atom-skip), 10 MEDIUM (pytest discovery excludes services/, README mocking claim mismatch, missing 429 test, stale plan-doc auth refs, stale "zero runtime deps" claim, Z.AI mentions in stale docs, README atom counts, DB path duplication, test fixture duplication), 6 LOW (large explainer.html, large plan doc, render constraint table, wave_d_curate overlap, working-tree generated artifacts, dev-secret example).

### Backlog (codex IDs in [brackets])
- BND-001 (LOW, NOW): doc staleness — README counts/test-count/personas [#12 #6], plan-doc auth refs [#8 #9], "zero runtime deps" claim [#10], Z.AI mentions [#11], supabase/README JWT mention. Files: README.md, docs/plans/2026-05-25-saas-pivot.md, docs/PRD-plan2.md, docs/PRD-plan3.md, docs/plans/sp1-plan2-curation-pipeline.md, supabase/README.md, services/compiler-api/README.md (dev-secret label [#20]).
- BND-002 (LOW-MED, NOW): integration tests not in `make check` — add `services/compiler-api` pytest invocation to Makefile [#5]. Files: Makefile.
- BND-003 (LOW, NOW): add structured warning logs for silent atom/pattern skip [#4] (additive, no behavior change). Files: src/hcc_compiler/sp2/compile.py + test.
- BND-DEF-001 (HIGH-RISK, DEFER): scripts/provision_saas.sh:84 readback bug — Fly redacts secrets, propagates empty token to Vercel [#1]. Touches auth secret pipeline → defer.
- BND-DEF-002 (HIGH-RISK, DEFER): chunked-body cap bypass in services/compiler-api/main.py:85 [#3]. Touches request-handling / DoS surface → defer.
- BND-NEXT-001 (NEXT tier): code/test dedup — _db_path between main.py:119 and compile_runner.py:15 [#13]; _atom_json between test_compile.py:29 and test_compile_cli.py:37 [#14]. Not blocking.

### Out of scope (logged, not actioned)
- [#2] shared bearer: by design per services/compiler-api/README.md:10 + matches saas-pivot decision. Architectural call.
- [#7] 429 rate-limit test missing: explicit decision in prior phase (flaky in CI, skipped).
- [#15] explainer.html size: self-contained marketing artifact, intentional.
- [#16] sp1-plan2 plan doc size: historical TDD plan; not a runbook.
- [#17] render.py constraint table: refactor candidate (data/presentation), not behavior bug — NEXT.
- [#18] wave_d_curate.py one-shot driver: documented archeology; covered by Z.AI doc fix in BND-001.
- [#19] .pytest_cache/__pycache__/library.db in WT: gitignored already; clean WT before push (operational, not a commit).

### Acceptance per bundle
- BND-001: every checkable claim verified against current code; `git grep -nE "(179 atoms|8 patterns|~475 tests|amy, carl, sam|SUPABASE_JWT_SECRET|zero new runtime|JWT verification)"` returns 0 hits in docs.
- BND-002: `make check` exits 0 AND collects ≥10 tests from services/compiler-api/tests/.
- BND-003: `make check` still 537+ tests green; new test asserts warning emitted on malformed row.

## 2026-05-28 19:01 — Bundle BND-001 SHIPPED
- did: 4 files modified (README.md, docs/plans/2026-05-25-saas-pivot.md, services/compiler-api/README.md, supabase/README.md); 2 commits on `cleanup/bnd-001-doc-staleness` (8895d69 + 816d4e0); merged to cleanup branch as 21181dd.
- codex: 3 review rounds. Round 1 → 3 VALID (SUPABASE_JWT_SECRET still in runbook, 215/22 stale example, "full pytest suite" overclaim). Round 2 → 1 VALID (saas-pivot:77 "signed JWT from Supabase"). Round 3 → 14 NEW findings outside original scope; 4 trivial single-line fixes folded in; rest deferred to BND-004.
- decisions: rejected scope-creep into web/public/intakes regen + web/README + main.py constants — those need a separate bundle (BND-004) since they touch new files / require build steps. Pytest 537 green throughout.

## 2026-05-28 19:01 — BND-002 RESCOPED → documentation-only (already done in BND-001)
- did: discovered during BND-002 prep that `services/compiler-api/tests` can't be added to root pytest discovery — fastapi/slowapi/fastembed aren't installed in the root venv (they're scoped to services/compiler-api/requirements.txt). The codex finding [#5] about `pyproject.toml:10` excluding services tests is technically correct but the fix isn't a pytest config change — it's a separate dependency environment.
- decisions: BND-001 already added a clarifying sentence to README ("compiler-API FastAPI service has its own test suite under services/compiler-api/tests/ ...") and a runner command. The deeper fix (separate venv management or Makefile target with uv) is operational tooling beyond cleanup scope. Logging as out-of-scope. Codex finding [#5] addressed via documentation.

### BND-004 follow-up (logged for next pass — not in this cleanup)
- web/public/intakes/*.yaml (9 files) — still library_version 0.1.0; need `cd web && pnpm prebuild` to refresh from tests/fixtures/intakes/ AND commit the refreshed copies.
- web/README.md L13 (data source: "../docs"/"../tests" vs actual web/public bundling), L57 (compile billing gate "needs to be added" but already shipped).
- services/compiler-api/main.py:112 — `_LIBRARY_VERSION` fallback const still "0.1.0".
- web/lib/intake-yaml.ts:79 — validation copy suggests "0.1.0".
- docs/plans/2026-05-25-saas-pivot.md:51 — storage path `intakes/<client_id>.yaml` vs code's `<coach_id>/intake_<client_id>.yaml`.

## 2026-05-28 19:14 — Bundle BND-003 SHIPPED
- did: src/hcc_compiler/sp2/compile.py — replaced silent `except: pass` for malformed atom/pattern rows with `logger.warning(...)` (added stdlib `import logging` + module logger). tests/sp2/test_compile.py — 2 new tests covering atom + pattern malformed-row warning emission.
- codex: round 1 → CLEAN, no findings ("Behavior is preserved", "Tests do exercise the new branches", "Log assertions are not flaky").
- decisions: used stdlib logging not custom infra (consistent with services/compiler-api/main.py which already uses logging.basicConfig). Behavior unchanged — still skips, doesn't raise. Pytest 537 → 539 green.

## 2026-05-28 19:18 — Bundle BND-DEF-001 OPEN PR (NOT MERGED)
- did: scripts/provision_saas.sh — generate COMPILER_API_TOKEN once in a shell var, reuse for both Fly + Vercel via the same value (and persist to zsvault). Removed the broken `fly secrets list | awk '{print $3}'` readback that returned the rotation-age column instead of the secret value.
- branched off: main @ 9050339. PR: https://github.com/wiggdevin/hcc-compiler/pull/1
- decisions: high-risk because it touches the COMPILER_API_TOKEN auth pipeline; user/operator must verify Fly+Vercel digests match before merging. Did NOT merge per playbook HIGH-RISK rule.

## 2026-05-28 19:20 — Bundle BND-DEF-002 OPEN PR (NOT MERGED)
- did: services/compiler-api/main.py — body_cap_and_log middleware now rejects POST/PUT/PATCH that lack a numeric Content-Length with 411 Length Required, closing the chunked-transfer bypass. The 256 KiB cap continues to fire on numeric CL > _MAX_BODY_BYTES (413).
- branched off: main @ 9050339. PR: https://github.com/wiggdevin/hcc-compiler/pull/2
- decisions: pragmatic Content-Length-required approach over the more complex ASGI receive wrapping (latter deferred to BND-DEF-002b if chunked uploads ever needed). High-risk because it changes the public API contract (POST without CL goes from 200 → 411). Did NOT merge.

## 2026-05-28 19:22 — Phase 09 Security Pass
- did: `git log --all --full-history -- '*.env'` empty; `git log -- '*.pem' '*.key' '*credentials*'` empty; rg for `sk_live|sk_test|ghp_|AKIA|xox[bp]` found only ONE hit in web/README.md as a placeholder example (not a real secret); RLS enabled on all 3 supabase/migrations/000{1,2,3}_*.sql; Stripe webhook handler at web/app/api/webhooks/stripe/route.ts uses `stripe.webhooks.constructEvent` (signature-verified).
- decisions: clean. No secret rotation needed. The codex audit also flagged shared bearer auth (codex #2) as an architectural choice (single token shared across all coaches → leak = total bypass), but it's documented in services/compiler-api/README.md:10 as intentional. Not a cleanup-pass fix.

## 2026-05-28 19:23 — Phase 10 Ship
- did: pushed cleanup/handoff-20260528 branch to origin. About to open rollup PR linking the 2 shipped bundles + 2 deferred PRs.
- decisions: this project has no customer-facing deploy that the cleanup branch needs to land into — the prior compiler-api deploy on Fly is unchanged. Final action is the rollup PR for human merge.



