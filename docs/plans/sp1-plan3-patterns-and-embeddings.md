# SP1 Plan 3 — Patterns + Embeddings (implementation plan)

Companion to `docs/PRD-plan3.md`. Task-by-task TDD cadence, file targets, verification.

## Architectural decisions

| Decision | Choice | Why |
|---|---|---|
| Embedding model | `nomic-embed-text` via Ollama (`localhost:11434`) | Already in user's stack (mem0 uses it). 768-dim float vectors. Local, free, deterministic. |
| Storage | New SQLite table `embeddings(record_id PK, record_type, vector JSON-BLOB)` colocated with `library.db` | Orthogonal to Plan-1 schema; easy to drop+rebuild; brute-force cosine fits 200 rows in <1ms. |
| Similarity | In-process cosine via stdlib `math` | Zero deps. ~200 atoms × 768 dim = 154K floats per query — trivial. |
| Cluster method | Single-link agglomerative, threshold `cosine_distance < 0.30` (= similarity ≥ 0.70) | Stdlib only. Threshold tunable; 0.30 chosen as starting heuristic. |
| Min atoms per cluster | 3 backing atoms | Statistical confidence floor; below → drop. |
| Pattern auto-admit threshold | ASSUMED: cluster mean intra-similarity ≥ 0.80 → admit; else queue | Documented in PRD as an ASSUMED default; tune after first live run. |
| Pattern ID | `RP-<domain-code>-<slug>` where slug is LLM-suggested 1-3 word phrase (kebab-case, regex-clean) | Matches Plan-1 model's `RP-[A-Z]{2,4}-[a-z0-9-]+` pattern. |
| Live gates | `HCC_LIVE_EMBED=1` for Ollama; `HCC_LIVE_LLM=1` for the synthesis call | Mirrors Plan 2 pattern; tests stay offline by default. |
| Synthesis LLM | **Claude via `zs-anthropic-proxy`** (localhost:11455) by default; OpenAI GPT-5.5 via `zs-codex-proxy` (localhost:11456) as swap-in via `HCC_SYNTH_PROVIDER=openai`. **No Z.AI / GLM** (Devin's 2026-05-22 directive). | Both proxies expose an anthropic-compatible shape — same client code, different `BASE_URL` + auth header. zs-anthropic-proxy sunsets 2026-06-14; migrate to direct `claude -p` subprocess before then. |

## Task list (11 tasks)

### A — docs (1 task)

- **T0 — Author `docs/PRD-plan3.md` + `docs/plans/sp1-plan3-patterns-and-embeddings.md` + rename `glm_client.py` to `anthropic_client.py`.** Already done for the docs in this commit. The rename: move the file, drop the GLM-specific `glm-4.6` default model, set defaults to `claude-sonnet-4-6` (Anthropic) or `gpt-5.5` (OpenAI via codex proxy) per `HCC_SYNTH_PROVIDER` env. Keep the existing dual-header auth shape (works against both proxies). Update all importers (`extract.py`, future `derive.py`) accordingly. Commit prefix `docs:` + `refactor(llm):`.

### B — Embeddings (4 tasks)

- **T1 — Ollama embedding client.** `src/hcc_compiler/llm/embed_client.py` exposing `EmbedRequest(text: str, model: str = "nomic-embed-text")` + `embed(req) -> list[float]`. Stdlib `urllib.request`, POST `http://localhost:11434/api/embeddings` with `{"model": ..., "prompt": ...}`. Fake transport in tests verifies request shape; live mode gated by `HCC_LIVE_EMBED=1`. → **SC1** `pytest tests/llm/test_embed_client.py -q`.

- **T2 — Cosine similarity helper.** `src/hcc_compiler/retrieve/cosine.py: cosine(a: list[float], b: list[float]) -> float`. Handles zero-vector defensively (returns 0.0). Tests: identical → 1.0; orthogonal → 0.0; opposite → -1.0; magnitude-invariant. → **SC2** `pytest tests/retrieve/test_cosine.py -q`.

- **T3 — `build_index.py` extension.** Add `embeddings` table to the SQLite output. Schema: `record_id TEXT PRIMARY KEY, record_type TEXT NOT NULL CHECK (record_type IN ('atom', 'pattern')), vector TEXT NOT NULL` (JSON-serialized list of floats). During build, for each atom: embed the `claim` field. For each pattern: embed `pattern + " " + parameterization`. Tests use a mocked `embed()` that returns deterministic vectors per text hash so the test stays offline. → **SC3** `pytest tests/test_build_index_embeddings.py -q`.

- **T4 — `retrieve.query()`.** `src/hcc_compiler/retrieve/__init__.py: query(text: str, k: int = 10, domain: str | None = None, db_path: Path = Path("library.db")) -> list[tuple[str, float]]`. Embeds the query, loads all candidate vectors (filtered by domain if provided), computes cosine to each, returns top-k descending. Tests use canned vectors in a tmp SQLite. → **SC4** `pytest tests/retrieve/test_retrieve.py -q`.

### C — Retrieval CLI (1 task)

- **T5 — `scripts/retrieve.py`.** Argparse: positional `query_text`, `--k` (default 10), `--domain`, `--db` (default `library.db`). Prints `<atom_id>\t<similarity>\t<claim[:80]>` per line. Tests via subprocess capturing stdout against a tiny fixture SQLite. → **SC5** `pytest tests/retrieve/test_retrieve_cli.py -q`.

### D — Patterns (4 tasks)

- **T6 — Clustering helper.** `src/hcc_compiler/patterns/cluster.py: cluster(vectors: list[list[float]], distance_threshold: float = 0.30) -> list[list[int]]`. Single-link agglomerative on cosine distance (1 - cosine_similarity). Returns lists of indices, one per cluster. Stdlib only. Tests: 3 near-identical vectors + 2 unrelated → 2 clusters (size 3 and size 2). → **SC6** `pytest tests/patterns/test_cluster.py -q`.

- **T7 — Pattern derivation.** `src/hcc_compiler/patterns/derive.py: derive_pattern(atoms: list[EvidenceAtom]) -> RecommendationPattern`. Loads `src/hcc_compiler/patterns/derive_prompt.md`. Sends atoms' `claim` + `effect` + `domain` to **Claude via `zs-anthropic-proxy`** (default) or GPT-5.5 via `zs-codex-proxy` (selected by `HCC_SYNTH_PROVIDER=openai`), parses JSON, validates with pydantic. Reuses Plan 2's anthropic-compatible client (renamed from `glm_client.py` to `anthropic_client.py` in T0). Caller (the route CLI) decides admit-vs-queue based on cluster mean intra-similarity. Tests use fake transport returning a canned pattern JSON. → **SC7** `pytest tests/patterns/test_derive.py -q`.

- **T8 — Pattern routing CLI.** `scripts/curation/derive_patterns.py`. Loads all admitted atoms, computes embeddings (or reads from `library.db`), clusters by domain, derives one pattern per qualifying cluster, routes: mean intra-sim ≥ 0.80 → `library/patterns/<domain>/<id>.yaml`; else → `library/queue/<id>.yaml`. Idempotent: skips pattern IDs already in `library/patterns/<domain>/`. Tests: table-driven decision matrix using canned clusters + canned LLM responses. → **SC8** `pytest tests/patterns/test_route_patterns.py -q`.

- **T9 — Validator extension for patterns.** `validate_library` already checks pattern atoms for shape; extend to verify every `backing_atom_ids` entry resolves to an existing atom. Fail-fast with the offending pattern id + dangling reference. Tests: dangling reference triggers `LIBRARY INVALID`. → **SC9** `pytest tests/test_validate_patterns.py -q`.

### E — Integration + Makefile (2 tasks)

- **T10 — End-to-end smoke + 6 hand-crafted retrieval probes.** `tests/test_patterns_smoke.py` (or `make patterns-smoke`): builds embeddings against the current library, derives patterns, then issues these probes and asserts the top-1 atom is in an expected DOI/id set per probe:
  - "protein dose for older adults" → expect EA-NUT-* on protein in older adults
  - "creatine safety markers" → expect EA-SUP-9218 (serum creatinine)
  - "HIIT cardiac rehab" → expect EA-TRA-4779 or EA-TRA-4688
  - "sleep banking for athletes" → expect EA-REC-8071 or EA-REC-*
  - "habit formation physical activity" → expect EA-BEH-*
  - "VO2max endurance" → expect EA-CON-*

  Probes use mocked Ollama with deterministic vectors mapped from the actual text. → **SC10** `make patterns-smoke && make check`.

- **T11 — Makefile targets + idempotency check.** Add `make embed`, `make derive-patterns`, `make patterns` (= chain), `make retrieve QUERY="..."`. `make patterns` MUST be idempotent: a second run with no library mutations produces no new YAML files. Verified by `make patterns && git status --porcelain` having empty output on the second invocation. → **SC11** `make patterns && git status --porcelain | wc -l` returns 0 on second run.

## Verification (success criteria — captured proofs)

Each SC has a captured stdout/exit-code artifact under `~/Inbox/goal-proof-hcc-compiler-patterns-and-embeddings/SC{n}.txt`. Done = all 11 proofs exit 0 + `~/Inbox/goal-summary-hcc-compiler-patterns-and-embeddings.md` written + repo at HEAD has clean tree.

End-to-end real-world spot-check (manual, after /goal completes, with Ollama running locally):

```bash
cd ~/projects/hcc-compiler && . .venv/bin/activate
ollama serve &  # if not already
ollama pull nomic-embed-text
# Claude via zs-anthropic-proxy (Claude Max OAuth bridge, port 11455).
# Proxy ignores the token but anthropic-compat clients require the header.
export ANTHROPIC_AUTH_TOKEN=local-proxy
export ANTHROPIC_BASE_URL=http://localhost:11455

HCC_LIVE_EMBED=1 make embed
HCC_LIVE_EMBED=1 HCC_LIVE_LLM=1 make derive-patterns
python scripts/retrieve.py "best protein dose for older adults" --k 5

git status   # expect new library/patterns/<domain>/RP-*.yaml files + updated library.db
```

## Critical files to read / modify

**Read (canonical sources):**
- `~/projects/hcc-compiler/docs/specs/sp1-evidence-library-design.md` §6 (pattern derivation), §7 (retrieval surface).
- `~/projects/hcc-compiler/src/hcc_compiler/models.py` — `RecommendationPattern` model (regex constraints + required fields).

**Reuse / extend (Plan 1 + Plan 2 surface):**
- `src/hcc_compiler/llm/glm_client.py` → **rename in T0** to `anthropic_client.py`; same HTTP shape, new default model + provider routing. Pattern-synthesis call reuses the renamed client.
- `src/hcc_compiler/build_index.py` — extend to write the new `embeddings` table.
- `src/hcc_compiler/loader.py` — reuse for loading atoms in cluster step.
- `scripts/curation/validate_library.py` (i.e. `src/hcc_compiler/validate.py`) — extend dangling-reference check to patterns.
- `Makefile` — add 4 new targets.

**New (Plan 3 creates):**
- `docs/PRD-plan3.md`, `docs/plans/sp1-plan3-patterns-and-embeddings.md`.
- `src/hcc_compiler/llm/embed_client.py`.
- `src/hcc_compiler/retrieve/{__init__,cosine}.py`.
- `src/hcc_compiler/patterns/{cluster,derive,derive_prompt.md}.py`.
- `scripts/retrieve.py`, `scripts/curation/derive_patterns.py`.
- `tests/llm/test_embed_client.py`, `tests/retrieve/test_*.py`, `tests/patterns/test_*.py`, `tests/test_build_index_embeddings.py`, `tests/test_validate_patterns.py`, `tests/test_patterns_smoke.py`.

## Execution

Once this plan is committed:

1. Run `/goal docs/PRD-plan3.md`.
2. The PRD + plan doc are already on disk (T0 is "this commit you're reading"), so `/goal` starts at T1.
3. Worker-prompt template carries forward the Plan 1 + Plan 2 lessons: workers MUST NOT `git add` untracked-but-present files; every commit passes the author overrides.
4. Final push to `origin/main` after the run + manual end-to-end spot-check (which needs a live local Ollama).

Artifacts on completion:

- `~/Inbox/goal-state-hcc-compiler-patterns-and-embeddings.json`
- `~/Inbox/goal-log-hcc-compiler-patterns-and-embeddings.md`
- `~/Inbox/goal-proof-hcc-compiler-patterns-and-embeddings/SC{1..11}.txt`
- `~/Inbox/goal-summary-hcc-compiler-patterns-and-embeddings.md`
