# Cleanup Final Report

> Branch: `cleanup/handoff-20260528` · Backup: `backup/pre-cleanup-20260528-183724` · Stash: `stash@{0}` (handoff working state).
>
> Tested at: 537 → 539 library tests green; codex read-only review on every bundle.

## Bundles

### Shipped (merged to cleanup branch)
| ID | Risk | Commit(s) | Summary |
|---|---|---|---|
| BND-001 | low | 8895d69 + 816d4e0 → merged 21181dd | Doc-staleness sync: README atom/pattern counts 179/8 → 225/23, test count ~475 → 537, persona examples 3 → 9, plan-doc + supabase + compiler-api/README auth refs corrected (SUPABASE_JWT_SECRET removed from runbook+inventory). 3 rounds of codex review. |
| BND-003 | low | b0ebd4e → merged 30cd293 | src/hcc_compiler/sp2/compile.py — replaced silent `except: pass` for malformed atom/pattern rows with `logger.warning(...)`. 2 new tests verify warning emission + behavior preservation. 1 round of codex review (CLEAN). |

### Rescoped (already covered)
| ID | Reason |
|---|---|
| BND-002 | The codex finding (root `pyproject.toml:10` excludes `services/compiler-api/tests` from `make check`) cannot be fixed by a pytest config change — fastapi/uvicorn/slowapi/fastembed aren't installed in the root venv. BND-001's README change already documents the manual `cd services/compiler-api && pytest -q` runner. Automating it via Makefile + uv venv mgmt is out of cleanup scope. |

### Deferred (open PRs, NOT merged — human review required)
| ID | Risk | PR | Summary |
|---|---|---|---|
| BND-DEF-001 | high | https://github.com/wiggdevin/hcc-compiler/pull/1 | scripts/provision_saas.sh:84 read `COMPILER_API_TOKEN` back via `fly secrets list | awk '{print $3}'` — Fly returns digest+age, not the value, so Vercel ended up with garbage and `/compile` would 401. Fix: generate the token once in a shell var, reuse for Fly + Vercel + zsvault. Touches deployment auth secret pipeline → flagged HIGH-RISK. |
| BND-DEF-002 | high | https://github.com/wiggdevin/hcc-compiler/pull/2 | services/compiler-api/main.py:85 — body cap only fires on numeric Content-Length, leaving chunked uploads / missing-CL POSTs to stream past the 256 KiB cap. Fix: require numeric Content-Length on POST/PUT/PATCH (411 if missing). Touches request handling / DoS surface → flagged HIGH-RISK. |

### NEXT-tier follow-up (logged, not actioned)
- **BND-004 doc staleness sweep round 2** — codex round-3 review surfaced more stale items outside BND-001's original scope: 9 bundled web/public/intakes/*.yaml files still at library_version 0.1.0 (need `pnpm prebuild` regen + commit); web/README.md L13 + L57; services/compiler-api/main.py:112 `_LIBRARY_VERSION` fallback "0.1.0"; web/lib/intake-yaml.ts:79; docs/plans/2026-05-25-saas-pivot.md:51 storage-path drift.
- **BND-007 code dedup** — _db_path between services/compiler-api/main.py:119 and compile_runner.py:15; _atom_json between tests/sp2/test_compile.py:29 and test_compile_cli.py:37. Logged for a future pass.

## Files

### Deleted
None.

### Modified
- `README.md` (atom counts, test count, personas, make-check scope, intake example version)
- `docs/plans/2026-05-25-saas-pivot.md` (auth refs, env inventory, runbook, architecture comment, migrations listing)
- `supabase/README.md` (COMPILER_API_TOKEN description, multi-migration paste fallback)
- `services/compiler-api/README.md` (verify example 215/22 → 225/23, dev-secret token renamed)
- `src/hcc_compiler/sp2/compile.py` (added `import logging` + `logger`; replaced silent `except: pass` with `logger.warning(...)` for atoms + patterns)
- `tests/sp2/test_compile.py` (added 2 tests for warning emission on malformed rows)

### Added (this cleanup run)
- `cleanup-progress.md` — running log per phase + bundle
- `cleanup-final-report.md` — this file

### Untouched (in working dir, not modified)
- `.claude/handoffs/nutrient-timing-expansion.md` (modified) + `.claude/handoffs/post-cleanup-and-sp3-design.md` (untracked) — preserved in `stash@{0}` for user to restore at their discretion. Both predate this cleanup.

## Tests + gates

- `uv run pytest tests/ -q` from repo root: 537 → 539 (BND-003 adds 2). All green.
- `make check` would also pass (validate + build + pytest).
- `cd web && pnpm test` not re-run in this round (no web/ changes). The 13 cases from the prior round still pass per HEAD baseline.
- Compiler-api integration tests (`services/compiler-api/tests/`) not re-run in this round — they need their own Python 3.11/3.12 venv with `requirements.txt` because pinned pydantic-core 2.27.1 doesn't build on the root venv's Python 3.14. The DEF-002 PR notes this and includes a test plan.

## Security findings + actions

| Check | Result |
|---|---|
| `.env` ever committed | NO — `git log --all -- '*.env'` empty |
| `.pem` / `.key` / `*credentials*` in history | NO — `git log --all -- '*.pem' '*.key' '*credentials*'` empty |
| Hardcoded `sk_live|sk_test|ghp_|AKIA|xox[bp]` in source | NO — only one hit in `web/README.md` as a placeholder example |
| Supabase RLS | YES — `enable row level security` set on all 3 migrations (0001, 0002, 0003) |
| Stripe webhook signature | YES — `stripe.webhooks.constructEvent` at web/app/api/webhooks/stripe/route.ts:30 |
| Recent deps (<14 days) | Not audited (manual gate; this run did not add deps) |

No active secret leaks, no rotations required.

## Stash + backup branch (user restore)

```bash
# Restore the auto-stashed handoff files when ready
git stash pop stash@{0}

# Roll back the entire cleanup if needed (nukes cleanup branches)
git switch main
git reset --hard backup/pre-cleanup-20260528-183724

# Or just abandon the cleanup branch but keep main
git branch -D cleanup/handoff-20260528
git branch -D cleanup/bnd-001-doc-staleness
git branch -D cleanup/bnd-003-skip-warnings
```

## Outstanding decisions for the operator

1. **Merge BND-001 + BND-003 (rollup PR)** — both are low-risk, codex-clean. Doc fixes + observability for silent atom/pattern skip.
2. **Review PR #1 (BND-DEF-001)** — provisioning-script bug. Verify Fly + Vercel `COMPILER_API_TOKEN` are not already mismatched in the live deployment before merging the fix.
3. **Review PR #2 (BND-DEF-002)** — body cap chunked bypass. Decide whether to land the pragmatic Content-Length-required fix now, or hold for the fuller ASGI receive-wrapping approach (BND-DEF-002b in the deferred backlog).
4. **Schedule BND-004 doc sweep round 2** — round-3 staleness items deferred from BND-001 (web/public/intakes regen + web/README + saas-pivot storage path + compiler-api _LIBRARY_VERSION fallback).
5. **Cleanup branches** — `backup/pre-cleanup-20260528-183724` can be deleted after the rollup PR merges and you've confirmed `stash@{0}` is popped/squashed where you want it.
