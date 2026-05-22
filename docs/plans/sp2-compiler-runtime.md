# SP2 — Per-Client Compiler Runtime — Implementation Plan

> **PRD:** `docs/PRD-sp2.md`. Read it first.
> **Style reference:** `docs/plans/sp1-plan3-patterns-and-embeddings.md`.
> **Branch:** `main`. Each task lands as 1–2 commits.

## Task DAG

```
T1 (intake model) ─┬─► T3 (score) ─┐
                   ├─► T4 (safety) ─┼─► T6 (compile) ─► T8 (CLI) ─► T9 (smoke) ─► T10 (docs+proofs)
                   └─► T5 (queries)─┘                      ▲
T2 (pack model) ─────────────────► T7 (render) ───────────┘
```

**Parallel groups:** [T1, T2] → [T3, T4, T5, T7] → [T6] → [T8] → [T9] → [T10].
T7 has no dependency on T3–T5 because it only consumes `EvidencePack` (T2), so it can run in the same parallel batch as T3+T4+T5.

## Reuse map (read once, internalize, don't redefine)

| Existing module | How new code uses it |
|---|---|
| `hcc_compiler.models.{EvidenceAtom, RecommendationPattern, Domain, Tier, PopulationApplicability, Citation, EvidenceLevel}` | Import directly. Never redefine. |
| `hcc_compiler.loader.load_dir` | Pattern to copy for `intake.py` single-file YAML loader (`yaml.safe_load` + `ClientIntake.model_validate`). |
| `hcc_compiler.retrieve.query(text, k, domain, db_path)` | The **only** retrieval surface used by `compile()`. Returns `list[(record_id, similarity)]`. |
| `hcc_compiler.build_index._SCHEMA` + raw `sqlite3.connect` | `compile()` reads `meta.library_version`, hydrates `atoms.json` / `patterns.json` columns. Mirror `scripts/retrieve.py` lines 22–42. |
| `hcc_compiler.llm.embed_client.embed` | Transitively used via `retrieve.query()`. Tests mock at `hcc_compiler.retrieve.embed` (per SC4 import-site convention). |
| `tests/fixtures/` | Drop intakes under `tests/fixtures/intakes/`. |
| `Makefile` | Append `compile:` target mirroring `retrieve:` shape. |
| `pyproject.toml [tool.pytest.ini_options] pythonpath` | Already `["src", ".", "scripts"]` — `scripts/compile_plan.py` can `from hcc_compiler.sp2.compile import compile`. |

## Risk callouts (every worker brief includes these)

1. **`PopulationApplicability` fields are all strings, not enums.** `age: str` holds free-form values like "adult", "older adults", "65+". **T3 worker must first** run `grep -h "  age:" library/atoms/**/*.yaml | sort -u` to enumerate the universe (~10 values) before writing the age-band normalizer. Without this, scoring will mis-bucket.
2. **`retrieve.query()` returns `(record_id, similarity)` only — no payload.** T6 must hydrate full records by joining back to `atoms.json` / `patterns.json` columns in SQLite. Mirror `scripts/retrieve.py` lines 22–42. Load once into a dict keyed by id; don't re-validate per hit.
3. **Patterns return alongside atoms** in `retrieve.query()` because the `embeddings` table mixes both `record_type` values. T6 must post-partition by `record_type` (simpler than separate queries).
4. **`backing_atom_ids` can be 30+.** Creatine pattern has 47. T7 must render top 3–5 backing atoms per pattern by `population_match_score` only — otherwise the report is unreadable.
5. **Library-version mismatch in dev.** `library/VERSION` is `0.1.0`. Fixture intakes must specify `library_version: "0.1.0"`. CLI gets `--no-version-check` escape hatch for ad-hoc runs.

## Tasks

### T1 — ClientIntake model + loader

**Maps to SC1.**
**Files (new):**
- `src/hcc_compiler/sp2/__init__.py` (empty)
- `src/hcc_compiler/sp2/intake.py`
- `tests/sp2/__init__.py` (empty)
- `tests/sp2/test_intake_model.py`

**Schema (intake.py):**

```python
from __future__ import annotations
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, Field, field_validator

Sex = Literal["M", "F", "other"]
TrainingStatus = Literal["untrained", "recreational", "trained", "competitive"]
Goal = Literal[
    "hypertrophy", "strength", "endurance", "weight_loss",
    "recomposition", "performance", "longevity",
]


class Demographics(BaseModel):
    age: int = Field(ge=14, le=100)
    sex: Sex
    weight_kg: float = Field(gt=0, le=300)
    height_cm: float = Field(gt=0, le=250)


class Constraint(BaseModel):
    type: str  # e.g. "injury", "schedule", "equipment"
    detail: str


class ClientIntake(BaseModel):
    client_id: str
    library_version: str
    demographics: Demographics
    training_status: TrainingStatus
    goals: list[Goal] = Field(min_length=1)
    current_regimen: str = Field(max_length=2000, default="")
    constraints: list[Constraint] = Field(default_factory=list)
    contraindications: list[str] = Field(default_factory=list)


def load_intake(path: Path) -> ClientIntake:
    """Parse an intake YAML file into a validated ClientIntake."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return ClientIntake.model_validate(raw)
```

**Tests:** valid intake parses, bad demographics (age 5, sex "X", negative weight) rejected, missing goals rejected, contraindications list optional, YAML roundtrip works.

**Verify:** `uv run pytest tests/sp2/test_intake_model.py -q` exits 0.

**Commit:** `feat(sp2-intake): ClientIntake pydantic model + YAML loader`

---

### T2 — EvidencePack model

**Maps to SC2.**
**Files (new):**
- `src/hcc_compiler/sp2/pack.py`
- `tests/sp2/test_pack_model.py`

**Schema (pack.py):**

```python
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field

from hcc_compiler.models import Domain, EvidenceLevel, Citation


class AtomMatch(BaseModel):
    atom_id: str
    similarity: float = Field(ge=-1.0, le=1.0)
    claim: str
    citations: list[Citation]
    evidence_level: EvidenceLevel
    population_match_score: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)


class PatternMatch(BaseModel):
    pattern_id: str
    similarity: float = Field(ge=-1.0, le=1.0)
    applies_because: str
    parameterization: str
    safety_bounds: str
    backing_atom_ids: list[str]
    warnings: list[str] = Field(default_factory=list)


class DomainBlock(BaseModel):
    patterns: list[PatternMatch] = Field(default_factory=list)
    atoms: list[AtomMatch] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)  # domains/queries with no hits


class CompileMetadata(BaseModel):
    top_k_per_domain: int
    applicability_threshold: float
    contraindication_hits: list[str] = Field(default_factory=list)
    queries_issued: dict[str, list[str]] = Field(default_factory=dict)  # domain -> queries


class EvidencePack(BaseModel):
    client_id: str
    library_version: str
    compiled_at: datetime
    domain_recommendations: dict[Domain, DomainBlock] = Field(default_factory=dict)
    compile_metadata: CompileMetadata
```

**Tests:** all sub-models validate, JSON round-trip (`.model_dump_json()` → `.model_validate_json(...)` is symmetric), similarity bounds enforced, empty pack is valid.

**Verify:** `uv run pytest tests/sp2/test_pack_model.py -q` exits 0.

**Commit:** `feat(sp2-pack): EvidencePack + sub-models with JSON round-trip`

---

### T3 — Applicability scoring

**Maps to SC3.** Depends on T1.

**Files (new):**
- `src/hcc_compiler/sp2/score.py`
- `tests/sp2/test_score.py`

**Steps:**

1. **First** run `grep -h "  age:" library/atoms/**/*.yaml | sort -u` and similarly for `  sex:` and `  training_status:` — the worker writes down the actual values present in the library and builds the normalization lookups against those values.

2. Implement `_age_band(age: int) -> str` mapping intake int age to the string buckets used in atoms (e.g., 14–17 "adolescent", 18–34 "young adult", 35–54 "adult", 55–64 "older adult", 65+ "65+").

3. Implement `score_applicability(atom: EvidenceAtom, intake: ClientIntake) -> float`:
   - Default 1.0; multiply by per-axis penalties.
   - Age axis (weight 0.4): exact bucket match = 1.0; adjacent bucket = 0.5; mismatch = 0.2. Atom "any" / "all adults" → 1.0 regardless.
   - Sex axis (weight 0.2): exact match = 1.0; atom "both" / "any" → 1.0; opposite → 0.3.
   - Training-status axis (weight 0.4): exact = 1.0; one rank apart (recreational ↔ trained) = 0.7; two apart = 0.4; three apart = 0.2; "any" = 1.0.
   - Final score = `0.4 * age + 0.2 * sex + 0.4 * training`. Clamp to `[0, 1]`.

**Tests:** exact-match intake gets ~1.0, totally-wrong intake gets <0.4, "any" atoms always score 1.0 on that axis, every value in the library's actual `age` / `sex` / `training_status` fields is handled (no `KeyError`).

**Verify:** `uv run pytest tests/sp2/test_score.py -q` exits 0.

**Commit:** `feat(sp2-score): deterministic applicability rubric (age/sex/training)`

---

### T4 — Safety / contraindication checker

**Maps to SC4.** Depends on T1.

**Files (new):**
- `src/hcc_compiler/sp2/safety.py`
- `tests/sp2/test_safety.py`

**Function:**

```python
def check_contraindications(
    record: EvidenceAtom | RecommendationPattern,
    intake: ClientIntake,
) -> list[str]:
    """Return warnings describing each contraindication hit."""
```

- Build a haystack from the intake: `intake.contraindications` (strings) + `c.detail for c in intake.constraints`. Lowercase + concatenate.
- Build needles from the record: `atom.contraindications` (list[str]) OR `pattern.doesnt_apply_if` (str — split on `,` / `;` / `\n`). Lowercase each.
- For each needle, do a case-insensitive substring check against the haystack. If hit, emit `f"⚠ {needle_phrase} (matches intake: {matched_substring})"`.
- Return list (possibly empty).

**Tests:** CKD intake vs creatine atom (contraindication "renal insufficiency") → warning; knee-injury constraint vs deep-squat pattern (doesnt_apply_if "acute knee injury") → warning; healthy intake vs same records → empty list; case mismatch ("CKD" vs "ckd") → still hits.

**Verify:** `uv run pytest tests/sp2/test_safety.py -q` exits 0.

**Commit:** `feat(sp2-safety): substring contraindication matcher`

---

### T5 — Query derivation

**Maps to (SC5 partial).** Depends on T1.

**Files (new):**
- `src/hcc_compiler/sp2/queries.py`
- `tests/sp2/test_queries.py`

**Function:**

```python
def derive_queries(intake: ClientIntake) -> dict[Domain, list[str]]:
    """Per-domain text queries derived from intake."""
```

- Each domain gets 1–3 query strings. Compose from goals + training_status + constraint summary.
- Examples:
  - `Domain.NUTRITION`: `f"protein intake for {goal} in {training_status} {age_band}"` for each goal; plus 1 generic `f"nutrition for {goal}"`.
  - `Domain.TRAINING`: `f"resistance training program for {goal}"`, `f"training volume {training_status}"`.
  - `Domain.CONDITIONING`: `f"cardiovascular conditioning {goal}"`, `f"HIIT for {goal}"`.
  - `Domain.SUPPLEMENTS`: `f"supplements for {goal} {training_status}"`.
  - `Domain.RECOVERY`: `f"recovery between sessions {training_status}"`, `f"sleep for {goal}"`.
  - `Domain.BEHAVIORAL`: `f"adherence in {training_status} adults pursuing {goal}"`.
- Constraints with `type == "injury"` should append `f"avoiding {detail}"` to the most-relevant domain's query list (training / conditioning for injuries, nutrition for dietary, etc.).
- Total query count per intake: capped at ~15 (3 per domain max).

**Tests:** every Domain key present in output, each value is `list[str]` with ≥1 query, queries reference the goals literally, injury constraint surfaces in training domain.

**Verify:** `uv run pytest tests/sp2/test_queries.py -q` exits 0.

**Commit:** `feat(sp2-queries): derive_queries from ClientIntake`

---

### T6 — compile() orchestrator

**Maps to SC5 + SC6.** Depends on T2, T3, T4, T5.

**Files (new):**
- `src/hcc_compiler/sp2/compile.py`
- `tests/sp2/test_compile.py`
- `tests/sp2/test_version_guard.py`

**Function signature:**

```python
class LibraryVersionMismatch(RuntimeError):
    """Raised when intake.library_version != meta.library_version in the SQLite."""


def compile(
    intake: ClientIntake,
    db_path: Path,
    top_k: int = 5,
    applicability_threshold: float = 0.4,
    *,
    version_check: bool = True,
) -> EvidencePack:
    ...
```

**Algorithm:**

1. Open SQLite read-only via `sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)`.
2. Read `meta.library_version`. If `version_check` and mismatch → raise `LibraryVersionMismatch`.
3. Hydrate atoms and patterns once into two dicts keyed by id:
   ```python
   atoms_by_id: dict[str, EvidenceAtom] = {
       row["id"]: EvidenceAtom.model_validate_json(row["json"])
       for row in con.execute("SELECT id, json FROM atoms").fetchall()
   }
   ```
   (Use the actual column name from `build_index._SCHEMA` — worker checks.)
4. Call `derive_queries(intake)` → `dict[Domain, list[str]]`.
5. For each `(domain, queries)`: per query, call `retrieve.query(text=q, k=top_k, domain=domain.value, db_path=db_path)`. Collect all returned `(record_id, similarity)` tuples into a per-domain dict, taking the **max** similarity per record_id across queries.
6. Partition results by id prefix (`EA-` vs `RP-`) or by looking up in the two dicts — pattern matches go into `PatternMatch`, atom matches into `AtomMatch`.
7. For each atom match: `population_match_score = score_applicability(atom, intake)`. Drop if below `applicability_threshold`. Compute warnings via `check_contraindications(atom, intake)`.
8. For each pattern match: warnings via `check_contraindications(pattern, intake)`. Resolve `parameterization` as a passthrough string (no LLM today).
9. Sort each domain's atoms by `population_match_score` descending, then `similarity` descending. Patterns sorted by `similarity` descending.
10. Build `EvidencePack(...)` with `compile_metadata.queries_issued = {d.value: qs for d, qs in derived.items()}`, `contraindication_hits = list({w for block in blocks for r in (block.patterns + block.atoms) for w in r.warnings})`.

**Tests:**
- `test_compile.py`: fixture intake + fixture SQLite (build a tiny one in `tmp_path` with 6 atoms + 2 patterns across domains) → pack has ≥1 domain block populated, metadata fields filled, warnings list present.
- `test_version_guard.py`: intake `library_version="0.99.0"` against fixture with `meta.library_version="0.1.0"` → raises `LibraryVersionMismatch`. Same intake with `version_check=False` → succeeds (no raise).

**Verify:** `uv run pytest tests/sp2/test_compile.py tests/sp2/test_version_guard.py -q` exits 0.

**Commit:** `feat(sp2-compile): deterministic compile() orchestrator + version guard`

---

### T7 — Markdown renderer

**Maps to SC7.** Depends on T2 (independent of T3–T6).

**Files (new):**
- `src/hcc_compiler/sp2/render.py`
- `tests/sp2/test_render.py`

**Function:**

```python
def render_markdown(pack: EvidencePack) -> str:
    """Render an EvidencePack as a coach-readable markdown report."""
```

- Header: `# Personalized Evidence Pack — {client_id}` + compiled_at, library_version.
- Per domain section (6 sections, in fixed order: nutrition, training, conditioning, supplements, recovery, behavioral):
  - `## {Domain.title()}`
  - For each `PatternMatch` in `block.patterns` (top 3 by similarity):
    - `### Pattern: {pattern_id} (sim={similarity:.2f})`
    - `**Applies because:** {applies_because}`
    - `**Parameterization:** {parameterization}`
    - `**Safety bounds:** {safety_bounds}`
    - `**Backing evidence (top 3 by population match):**` — list 3 atoms from `block.atoms` filtered to `atom_id in pattern.backing_atom_ids`, sorted by `population_match_score`. Format: `- {claim} ([{citation.id}])`.
    - If `pattern.warnings`: `> ⚠ {warning}` block-quote each.
  - For each `AtomMatch` in `block.atoms` (top 5 by `population_match_score`, that are NOT already shown as backing for a pattern above):
    - `- **{atom_id}** ({similarity:.2f}, pop-match {population_match_score:.2f}): {claim} ([{citation.id}])`
  - If `block.gaps`: `**Gaps:** {comma-joined}` italic.
- Footer: `## Metadata` block — top_k_per_domain, applicability_threshold, total queries issued, total contraindication hits.

**Tests:**
- All 6 domain headings appear (even if a domain block is empty — show "_(no matches)_").
- Inline citations present in the format `[doi-or-pmid]`.
- Warnings block-quotes render with `>` prefix.
- Backing atoms only render top 3 even when pattern lists 47 (creatine case — mock the data).
- Empty pack renders cleanly (no exceptions).

**Verify:** `uv run pytest tests/sp2/test_render.py -q` exits 0.

**Commit:** `feat(sp2-render): markdown renderer for EvidencePack`

---

### T8 — CLI + Makefile target

**Maps to SC8.** Depends on T6, T7.

**Files (new):**
- `scripts/compile_plan.py`
- `tests/sp2/test_compile_cli.py`

**Files (modified):**
- `Makefile` — append `compile:` target

**CLI usage:**

```bash
python scripts/compile_plan.py <intake.yaml> \
    [--db library.db] \
    [--out-json path] \
    [--out-md path] \
    [--top-k 5] \
    [--applicability-threshold 0.4] \
    [--no-version-check]
```

- Reads intake via `load_intake(path)`.
- Calls `compile(intake, db, top_k, applicability_threshold, version_check=not no_version_check)`.
- Writes JSON via `pack.model_dump_json(indent=2)` to `--out-json` (default `<intake_basename>.json` in cwd).
- Writes MD via `render_markdown(pack)` to `--out-md` (default `<intake_basename>.md` in cwd).
- Prints both paths + a one-line summary (`compiled {client_id} → {n_patterns} patterns, {n_atoms} atoms, {n_warnings} warnings`).
- Exit code 0 on success; 1 on `LibraryVersionMismatch`; 2 on file/parse errors.

**Makefile target:**

```make
compile:
	$(if $(INTAKE),,$(error Usage: make compile INTAKE=path/to/intake.yaml))
	uv run python scripts/compile_plan.py "$(INTAKE)"
```

Add `compile` to the `.PHONY` line.

**Tests:**
- Smoke: write a tiny intake YAML + tiny SQLite fixture in `tmp_path`, run CLI via `subprocess` OR direct call to `_cli_main()` (per SC6 convention), assert both output files exist + parse.
- Version-mismatch returns exit 1.

**Verify:** `uv run pytest tests/sp2/test_compile_cli.py -q` exits 0.

**Commit:** `feat(sp2-cli): scripts/compile_plan.py + make compile target`

---

### T9 — End-to-end smoke + persona fixtures

**Maps to SC9.** Depends on T8.

**Files (new):**
- `tests/fixtures/intakes/intake_amy_runner.yaml`
- `tests/fixtures/intakes/intake_carl_strength.yaml`
- `tests/fixtures/intakes/intake_sam_recomp.yaml`
- `tests/sp2/test_compile_smoke.py`
- `docs/examples/sp2/amy.md`, `amy.json`
- `docs/examples/sp2/carl.md`, `carl.json`
- `docs/examples/sp2/sam.md`, `sam.json`

**Personas:**

- **amy_runner**: 32F, recreational, goal=["endurance", "performance"], current_regimen describes 5 runs/week + 2 strength sessions, constraints=[injury: left knee mild patellar tendinopathy], contraindications=[].
- **carl_strength**: 45M, trained, goal=["strength", "hypertrophy"], current_regimen 4x/week heavy lifting, constraints=[], contraindications=["renal insufficiency (CKD stage 2)"].
- **sam_recomp**: 28other, recreational, goal=["recomposition", "longevity"], current_regimen 3x/week mixed + cardio, constraints=[schedule: 45-min cap], contraindications=[].

All three set `library_version: "0.1.0"`.

**Smoke test:**

1. For each persona: `pack = compile(load_intake(path), Path("library.db"))`.
2. Assert ≥3 of 6 domains have ≥1 atom or pattern.
3. Assert no exceptions on render.
4. Render to `tests/output/<persona>.md` and assert basic structure (heading present, ≥3 `##` sections).

**Committed examples:** During T9 execution, the worker runs the CLI against `library.db` for each persona and commits the resulting `.md` + `.json` under `docs/examples/sp2/`. These are committed artifacts that double as documentation.

**Verify:** `uv run pytest tests/sp2/test_compile_smoke.py -q` exits 0.

**Commit:** `test(sp2): persona smoke fixtures + e2e compile coverage`
**Second commit (examples):** `docs(sp2): committed example evidence packs for 3 personas`

---

### T10 — Final docs + proof capture

**Maps to SC10.** Depends on T9.

**Files (modified):**
- `docs/README.md` — add SP2 to "Shipped" section + a "Quick start: compile a plan" snippet using `make compile INTAKE=tests/fixtures/intakes/intake_amy_runner.yaml`.

**Steps:**

1. Verify `make check` exits 0 at full count (148 + ~20–25 SP2 = ~170–175).
2. Confirm all 10 SC proofs exist under `~/Inbox/goal-proof-hcc-compiler-sp2/SC{1..10}.txt`.
3. Update `docs/README.md`.
4. Write `~/Inbox/goal-summary-hcc-compiler-sp2.md`.

**Verify:** `make check` exits 0 + `ls ~/Inbox/goal-proof-hcc-compiler-sp2/ | wc -l` ≥ 10.

**Commit:** `docs(sp2): mark SP2 shipped in README + quick-start snippet`

---

## Per-task discipline (every task)

1. Dispatch Sonnet `general-purpose` worker with self-contained brief (this plan section + the relevant risk callouts + the reuse map snippet for the modules used).
2. Worker commits with `-c user.email=devin@zerosumsolutions.com -c user.name="Dev Wiggins"`.
3. Dispatch `agent-skills:code-reviewer` against the new commit ref (pass ref, NOT diff payload).
4. Capture verify-cmd stdout/stderr/exit to `~/Inbox/goal-proof-hcc-compiler-sp2/SC<n>.txt`.
5. Pass → next task. Important-finding → retry (max 2/task). Disagreement → codex tiebreaker (one round).

## Done when (matches PRD)

10 SC proofs on disk, three persona packs committed under `docs/examples/sp2/`, `make compile INTAKE=...` works, `make check` green at the new test count. All commits authored by Dev Wiggins. No new runtime deps.
