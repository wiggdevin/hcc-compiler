# HCC Compiler — Patterns + Embeddings (SP1 · Plan 3)

## Context

`hcc-compiler` shipped SP1 Plan 1 (Library Foundation) and Plan 2 (Curation Pipeline MVP) on 2026-05-22. Library is at 179 atoms across 6 domains (HEAD `8198622`). The curation pipeline is production-grade: deterministic citation gate, retry-on-paraphrase extract, dedup-safe routing, all subscription-billed LLM.

This PRD covers **SP1 Plan 3**: the **retrieval surface** — embeddings + `RecommendationPattern` derivation. Together they unlock SP2 (the downstream council consumer) and turn the seed library from a static YAML corpus into something the rest of the system can query.

- Architecture & rationale: `docs/specs/sp1-evidence-library-design.md` §6–§7 (patterns + retrieval).
- Pattern model: already defined in `src/hcc_compiler/models.py` (`RecommendationPattern`); this plan populates it.
- Task-by-task plan (exact files, code, commands): `docs/plans/sp1-plan3-patterns-and-embeddings.md`.

**Execute the plan in `docs/plans/sp1-plan3-patterns-and-embeddings.md` task-by-task.** This PRD defines what "done" means and how each piece is mechanically verified.

## In scope (this PRD)

A retrieval surface over the 179-atom library:

- **Local-embeddings client** that turns text into a fixed-dimension vector via Ollama (`nomic-embed-text`, already in user's stack). Stdlib `urllib.request`; zero new runtime deps.
- **`build_index.py` extension** that computes one embedding per atom (the `claim` field) and per pattern, storing the vector as a JSON-encoded blob in the existing SQLite library index alongside the existing rows.
- **`retrieve.py`** — `query(text, k=10, domain=None) -> list[(atom_id, similarity)]` doing in-process cosine similarity over the SQLite blobs. Brute-force is fine at this scale (~200 atoms; sub-millisecond).
- **Pattern derivation pipeline** — agglomerative-clustering on atom embeddings (cosine distance, stdlib only — no sklearn), one LLM call per cluster to synthesize a `RecommendationPattern` per the existing pydantic model, true-move output to `library/patterns/<domain>/<id>.yaml`. Reuses Plan-2's `glm_client.py`.
- **Pattern-PR queue** — same tier-aware routing semantics as atoms: clusters below a confidence threshold (or with <3 backing atoms) → `library/queue/RP-*.yaml`; above-threshold → admit directly.
- **CLI surfaces:** `scripts/curation/embed.py`, `scripts/curation/derive_patterns.py`, `scripts/retrieve.py "query text"`.

## Out of scope (do NOT build — Plan 4+)

- **Cross-model critique** (GPT-5.5 / Gemini second-opinion at verify time) — deferred. Z.AI single-pass was 79/79 PASS in the final live run; not urgent.
- **Release-tag automation** (semver bump + git-tag on library mutations) — deferred.
- **Scheduled re-harvest** (`/schedule` routine that auto-runs `make curate` weekly per domain) — operational concern, not Plan 3.
- **Web service / HTTP API surface** — Plan 3 ships Python functions + CLIs only; the council consumes them in-process via SP2.
- **Re-embedding on every change** — `make embed` is manual / on-commit; auto-incremental is later.
- Any pattern beyond what the LLM synthesizes from a single atom cluster (no multi-hop reasoning, no contradiction detection, no temporal-trend derivation).

If tempted to add anything above, log a scope-creep flag and skip it.

## Constraints

- **Zero new runtime dependencies.** Embedding client is stdlib `urllib.request` against `localhost:11434/api/embeddings`. Cosine similarity is `numpy`-free — math via `math.sqrt` + zip-sum-product. Vector storage is JSON blob in SQLite. No `numpy`, `sentence-transformers`, `sklearn`, `sqlite-vec`, `faiss`, `chromadb`, or any other vector-DB dependency.
- **Subscription-only LLM, Anthropic or OpenAI only.** Pattern-synthesis prompts route through **Claude via `zs-anthropic-proxy`** (localhost:11455, Claude Max OAuth bridge) by default, with **OpenAI GPT-5.5 via `zs-codex-proxy`** (localhost:11456, ChatGPT OAuth bridge) as a swap-in alternative selected via env. Plan 2's `glm_client.py` is renamed to `anthropic_client.py` and **Z.AI GLM is removed from this plan** — Devin's 2026-05-22 directive: only Anthropic + OpenAI models going forward for this project (Z.AI rate-limit + reliability issues + no vision). Embedding model stays Ollama-local (no API key, no metered cost). Never billed Anthropic / OpenAI SDK.
- **Tests must run offline + deterministically.** Ollama HTTP calls mocked with `unittest.mock`; LLM calls go through the existing `tests/llm/` fake transport. Live mode gated behind `HCC_LIVE_LLM=1` (LLM) and `HCC_LIVE_EMBED=1` (Ollama). The live Ollama gate is new in this plan.
- **All commits authored by `Dev Wiggins <devin@zerosumsolutions.com>`** — every commit command in worker subagents MUST pass `-c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins"`.
- **Workers MUST NOT `git add` untracked-but-present files** outside the explicit file list of their task (Plan 1 + Plan 2 hard lesson).
- Commits prefixed `feat(embed):` / `feat(patterns):` / `feat(retrieve):` / `feat(curation):` / `docs:`.

## Success Criteria

Each criterion is verified by running its command from the repo root with the venv active (`cd ~/projects/hcc-compiler && . .venv/bin/activate`) and capturing stdout + exit code as proof under `~/Inbox/goal-proof-hcc-compiler-patterns-and-embeddings/SC{n}.txt`.

| # | Criterion | Verification command | Pass condition |
|---|---|---|---|
| SC1 | Ollama embedding client (request shape + 768-dim float vector + fake transport) | `pytest tests/llm/test_embed_client.py -q` | exit 0 |
| SC2 | Cosine similarity helper (orthogonal=0, identical=1, opposite=-1, normalizes) | `pytest tests/retrieve/test_cosine.py -q` | exit 0 |
| SC3 | `build_index.py` writes one embedding row per atom + pattern (vector stored as JSON blob; row count matches input) | `pytest tests/test_build_index_embeddings.py -q` | exit 0 |
| SC4 | `retrieve.query(text, k)` returns top-k atoms ordered by descending similarity, with optional domain filter | `pytest tests/retrieve/test_retrieve.py -q` | exit 0 |
| SC5 | Retrieve CLI prints atom IDs + scores for a sample query (against a tiny SQLite fixture, mocked Ollama) | `pytest tests/retrieve/test_retrieve_cli.py -q` | exit 0 |
| SC6 | Agglomerative clustering helper (stdlib only) groups N atoms into K clusters by cosine distance threshold | `pytest tests/patterns/test_cluster.py -q` | exit 0 |
| SC7 | Pattern-synthesis prompt + LLM round-trip produces a valid `RecommendationPattern` (mocked Z.AI GLM) | `pytest tests/patterns/test_derive.py -q` | exit 0 |
| SC8 | Pattern routing CLI: above-threshold cluster → `library/patterns/<domain>/<id>.yaml`; below-threshold → `library/queue/RP-*.yaml` | `pytest tests/patterns/test_route_patterns.py -q` | exit 0 |
| SC9 | Cross-record validator extension: every pattern's `backing_atom_ids` must reference existing atoms; fails if dangling | `pytest tests/test_validate_patterns.py -q` | exit 0 |
| SC10 | End-to-end smoke: build embeddings for current library, derive ≥1 pattern in each of 6 domains, retrieve at least one expected atom for each of 6 hand-crafted queries, `make check` stays green | `make patterns-smoke && make check` | exit 0 |
| SC11 | `make patterns` Makefile target chains `embed → derive_patterns → route_patterns` and is idempotent (re-run produces no new commits) | `make patterns && git status --porcelain` | empty diff after second run |

## Done when

Every success criterion SC1–SC11 has a captured proof artifact (command, output, exit code) under `~/Inbox/goal-proof-hcc-compiler-patterns-and-embeddings/`. Library has at least 6 patterns (≥1 per domain) committed. `make check` exits 0 with the new patterns + embeddings table in `library.db`. No new runtime deps in `pyproject.toml`. All commits authored by Dev Wiggins.
