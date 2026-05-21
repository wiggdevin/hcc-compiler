# hcc-compiler

The greenfield engine for the **Health Coach Council** redesign — a *library-first plan
compiler* that replaces the legacy ~2-hour multi-agent council. Instead of re-deriving sports
science for every client, it selects from a pre-verified evidence library and personalizes,
targeting **~7–14 min per fresh plan** and **near-instant re-planning** when a client's
situation changes.

Architecture independently converged on by Claude Opus 4.7 and GPT-5.5.

## The redesign at a glance

| Sub-project | What it is | Status |
|---|---|---|
| **SP1** | Evidence library + offline curation pipeline | **in progress** — Plan 1 (this repo's first build) |
| SP2 | Per-client plan compiler runtime | designed (future) |
| SP3 | Dynamic re-planning / Change Ledger engine | designed (future) |

## Documents

| Doc | Purpose |
|---|---|
| `docs/PRD.md` | **Product requirements + success criteria** for the current build unit (SP1 Plan 1). The `/goal` entry point. |
| `docs/specs/sp1-evidence-library-design.md` | Full SP1 architecture & rationale |
| `docs/plans/sp1-plan1-library-foundation.md` | Task-by-task implementation plan (exact files, code, commands) |
| `docs/explainer.html` | Visual overview of the whole redesign |

## Run it autonomously

This build is driven by the `/goal` skill — an autonomous, task-by-task loop (route → execute
via a fresh subagent → mandatory adversary review → mechanical verification with proof on disk →
next task). From a terminal:

```bash
cd ~/projects/hcc-compiler
claude            # start Claude Code in this repo
/goal docs/PRD.md # drive the PRD to mechanically-verified done
```

`/goal` writes its state, run log, and per-criterion proof artifacts under `~/Inbox/goal-*`.
Resume an interrupted run with `/goal --resume hcc-compiler-library-foundation`.

## After Plan 1

Plan 2 adds the offline curation pipeline (harvest → verify with the citation gate → cross-model
critique → tiered sign-off → release). Plan 3 adds the embeddings store + retrieval API that
SP2's per-client compiler consumes.
