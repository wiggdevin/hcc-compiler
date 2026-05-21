# HCC Redesign · SP1 · Plan 1 — Library Foundation (Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a new `hcc-compiler` repo with a validated, versioned evidence/recommendation library that can be authored as YAML files and compiled into a queryable SQLite index.

**Architecture:** Files-of-record in git (one YAML per atom/pattern, foldered by domain) → pydantic models validate each record → a validator CLI lints the whole library → a build step compiles validated records into a SQLite index (the derived artifact SP2 will read). No network, no LLM calls in this plan — this is the deterministic foundation the curation pipeline (Plan 2+) writes into.

**Tech Stack:** Python 3.11, pydantic v2 (schema + validation), PyYAML, SQLite (stdlib), pytest.

**Scope note:** This is Plan 1 of the SP1 sequence. Plan 2+ add the offline curation pipeline (harvest → extract → verify via the shipped citation gate → cross-model critique → tiered sign-off → derive patterns → release) and the embeddings store for SP2 retrieval. Those are out of scope here.

**Decisions locked for this plan:** new repo at `~/projects/hcc-compiler/`; YAML records; pydantic v2; SQLite index; pytest. The embeddings store is deferred to the retrieval plan.

---

### Task 1: Initialize the `hcc-compiler` repo

**Files:**
- Create: `~/projects/hcc-compiler/pyproject.toml`
- Create: `~/projects/hcc-compiler/.gitignore`
- Create: `~/projects/hcc-compiler/src/hcc_compiler/__init__.py` (empty)
- Create: `~/projects/hcc-compiler/library/VERSION`
- Create dirs: `library/atoms/`, `library/patterns/`, `tests/`, `scripts/curation/`

- [ ] **Step 1: Create the structure**

```bash
cd ~/projects
mkdir -p hcc-compiler/src/hcc_compiler hcc-compiler/library/atoms hcc-compiler/library/patterns hcc-compiler/tests hcc-compiler/scripts/curation
cd hcc-compiler
git init -q
printf '0.1.0\n' > library/VERSION
touch src/hcc_compiler/__init__.py tests/__init__.py
printf '__pycache__/\n*.pyc\n.venv/\n*.db\n.pytest_cache/\n' > .gitignore
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[project]
name = "hcc-compiler"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.6", "pyyaml>=6.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
pythonpath = ["src", "."]
testpaths = ["tests"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 3: Create venv and install**

```bash
cd ~/projects/hcc-compiler
python3 -m venv .venv && . .venv/bin/activate
pip install -q -e ".[dev]"
```
Expected: installs pydantic, pyyaml, pytest with no errors.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml .gitignore src library
git commit -m "chore: scaffold hcc-compiler repo (library foundation)"
```

---

### Task 2: `EvidenceAtom` model

**Files:**
- Create: `src/hcc_compiler/models.py`
- Test: `tests/test_models_atom.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models_atom.py
import pytest
from pydantic import ValidationError
from hcc_compiler.models import EvidenceAtom

VALID = {
    "id": "EA-NUT-0001",
    "domain": "nutrition",
    "claim": "1.6-2.2 g/kg/day protein maximizes lean mass retention in a deficit.",
    "evidence_level": "L1",
    "citations": [{
        "id": "10.1234/jissn.2023.001",
        "locator_quote": "protein intakes of 1.6-2.2 g/kg/day...",
        "existence": "VERIFIED",
        "faithfulness": "VERIFIED",
    }],
    "population_applicability": {
        "age": "18-55", "sex": "both", "training_status": "trained",
        "dose_magnitude": "moderate deficit", "duration": "8-16 wk",
    },
    "effect": "Preserves FFM vs lower intake (SMD ~0.3).",
    "tier": "high-impact",
    "approval": "Dev Wiggins 2026-05-21",
    "library_version": "0.1.0",
    "last_reviewed": "2026-05-21",
    "expiry": "2027-05-21",
}

def test_valid_atom_parses():
    a = EvidenceAtom.model_validate(VALID)
    assert a.id == "EA-NUT-0001"
    assert a.citations[0].existence == "VERIFIED"

def test_atom_requires_at_least_one_citation():
    bad = {**VALID, "citations": []}
    with pytest.raises(ValidationError):
        EvidenceAtom.model_validate(bad)

def test_atom_id_pattern_enforced():
    bad = {**VALID, "id": "NUT-1"}
    with pytest.raises(ValidationError):
        EvidenceAtom.model_validate(bad)

def test_bad_enum_rejected():
    bad = {**VALID, "evidence_level": "L9"}
    with pytest.raises(ValidationError):
        EvidenceAtom.model_validate(bad)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/projects/hcc-compiler && . .venv/bin/activate && pytest tests/test_models_atom.py -q`
Expected: FAIL with `ModuleNotFoundError: hcc_compiler.models` (or ImportError).

- [ ] **Step 3: Write minimal implementation**

```python
# src/hcc_compiler/models.py
from __future__ import annotations
from datetime import date
from enum import Enum
from pydantic import BaseModel, Field


class EvidenceLevel(str, Enum):
    L1 = "L1"; L2 = "L2"; L3 = "L3"; L4 = "L4"


class Tier(str, Enum):
    HIGH_IMPACT = "high-impact"
    ROUTINE = "routine"


class Domain(str, Enum):
    NUTRITION = "nutrition"
    TRAINING = "training"
    CONDITIONING = "conditioning"
    SUPPLEMENTS = "supplements"
    RECOVERY = "recovery"
    BEHAVIORAL = "behavioral"


class Citation(BaseModel):
    id: str                 # DOI or PMID
    locator_quote: str      # verbatim supporting passage
    existence: str          # VERIFIED / PLAUSIBLE / UNVERIFIABLE / DOI_MISMATCH / FABRICATED
    faithfulness: str       # VERIFIED / MINOR_DISTORTION / MAJOR_DISTORTION / UNSUPPORTED / ACCESS_LIMITED


class PopulationApplicability(BaseModel):
    age: str
    sex: str
    training_status: str
    dose_magnitude: str
    duration: str


class EvidenceAtom(BaseModel):
    id: str = Field(pattern=r"^EA-[A-Z]{2,4}-\d{4}$")
    domain: Domain
    claim: str
    evidence_level: EvidenceLevel
    citations: list[Citation] = Field(min_length=1)
    population_applicability: PopulationApplicability
    effect: str
    contraindications: list[str] = Field(default_factory=list)
    tier: Tier
    approval: str
    library_version: str
    last_reviewed: date
    expiry: date
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models_atom.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/hcc_compiler/models.py tests/test_models_atom.py
git commit -m "feat: EvidenceAtom model with validation"
```

---

### Task 3: `RecommendationPattern` model

**Files:**
- Modify: `src/hcc_compiler/models.py` (append)
- Test: `tests/test_models_pattern.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models_pattern.py
import pytest
from pydantic import ValidationError
from hcc_compiler.models import RecommendationPattern

VALID = {
    "id": "RP-NUT-protein-band",
    "domain": "nutrition",
    "pattern": "protein target band",
    "parameterization": "1.6-2.2 g/kg/day; pick upper end in steeper deficits.",
    "backing_atom_ids": ["EA-NUT-0001"],
    "falsification_signal": "FFM drops >1%/wk over 3 wk at target intake.",
    "safety_bounds": "Do not exceed 2.5 g/kg/day; flag renal history.",
    "applies_because": "Trained adults in a deficit.",
    "doesnt_apply_if": "CKD or other renal contraindication.",
    "tier": "high-impact",
    "approval": "Dev Wiggins 2026-05-21",
    "version": "0.1.0",
}

def test_valid_pattern_parses():
    p = RecommendationPattern.model_validate(VALID)
    assert p.backing_atom_ids == ["EA-NUT-0001"]

def test_pattern_requires_backing_atom():
    with pytest.raises(ValidationError):
        RecommendationPattern.model_validate({**VALID, "backing_atom_ids": []})

def test_pattern_id_pattern_enforced():
    with pytest.raises(ValidationError):
        RecommendationPattern.model_validate({**VALID, "id": "protein"})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models_pattern.py -q`
Expected: FAIL with `ImportError: cannot import name 'RecommendationPattern'`.

- [ ] **Step 3: Write minimal implementation** (append to `src/hcc_compiler/models.py`)

```python
class RecommendationPattern(BaseModel):
    id: str = Field(pattern=r"^RP-[A-Z]{2,4}-[a-z0-9-]+$")
    domain: Domain
    pattern: str
    parameterization: str
    backing_atom_ids: list[str] = Field(min_length=1)
    falsification_signal: str
    safety_bounds: str
    applies_because: str
    doesnt_apply_if: str
    tier: Tier
    approval: str
    version: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models_pattern.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add src/hcc_compiler/models.py tests/test_models_pattern.py
git commit -m "feat: RecommendationPattern model"
```

---

### Task 4: YAML loader

**Files:**
- Create: `src/hcc_compiler/loader.py`
- Test: `tests/test_loader.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_loader.py
from pathlib import Path
import yaml
from hcc_compiler.models import EvidenceAtom
from hcc_compiler.loader import load_dir
from tests.test_models_atom import VALID  # reuse the valid atom fixture

def _write(p: Path, data: dict):
    p.write_text(yaml.safe_dump(data))

def test_loads_valid_records(tmp_path):
    _write(tmp_path / "a1.yaml", VALID)
    _write(tmp_path / "a2.yaml", {**VALID, "id": "EA-NUT-0002"})
    records, errors = load_dir(tmp_path, EvidenceAtom)
    assert len(records) == 2
    assert errors == []

def test_invalid_file_reported_with_path(tmp_path):
    _write(tmp_path / "good.yaml", VALID)
    _write(tmp_path / "bad.yaml", {**VALID, "id": "nope"})
    records, errors = load_dir(tmp_path, EvidenceAtom)
    assert len(records) == 1
    assert len(errors) == 1
    assert "bad.yaml" in errors[0].path
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_loader.py -q`
Expected: FAIL with `ModuleNotFoundError: hcc_compiler.loader`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/hcc_compiler/loader.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml
from pydantic import BaseModel, ValidationError


@dataclass
class LoadError:
    path: str
    message: str


def load_dir(directory: Path, model: type[BaseModel]):
    """Load + validate every *.yaml under `directory`. Returns (records, errors)."""
    records, errors = [], []
    for f in sorted(Path(directory).rglob("*.yaml")):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            records.append(model.model_validate(data))
        except (yaml.YAMLError, ValidationError) as e:
            errors.append(LoadError(str(f), str(e)))
    return records, errors
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_loader.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add src/hcc_compiler/loader.py tests/test_loader.py
git commit -m "feat: YAML library loader with per-file error reporting"
```

---

### Task 5: Library validator (cross-record integrity) + CLI

**Files:**
- Create: `src/hcc_compiler/validate.py`
- Create: `scripts/curation/validate_library.py`
- Test: `tests/test_validate.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_validate.py
from pathlib import Path
import yaml
from hcc_compiler.validate import validate_library
from tests.test_models_atom import VALID as ATOM
from tests.test_models_pattern import VALID as PATTERN

def _setup(root: Path, atoms: list[dict], patterns: list[dict]):
    (root / "atoms").mkdir(parents=True)
    (root / "patterns").mkdir(parents=True)
    for i, a in enumerate(atoms):
        (root / "atoms" / f"a{i}.yaml").write_text(yaml.safe_dump(a))
    for i, p in enumerate(patterns):
        (root / "patterns" / f"p{i}.yaml").write_text(yaml.safe_dump(p))

def test_clean_library_has_no_problems(tmp_path):
    _setup(tmp_path, [ATOM], [PATTERN])
    assert validate_library(tmp_path) == []

def test_dangling_backing_ref_flagged(tmp_path):
    _setup(tmp_path, [ATOM], [{**PATTERN, "backing_atom_ids": ["EA-NUT-9999"]}])
    problems = validate_library(tmp_path)
    assert any("EA-NUT-9999" in p for p in problems)

def test_duplicate_atom_id_flagged(tmp_path):
    _setup(tmp_path, [ATOM, ATOM], [PATTERN])
    problems = validate_library(tmp_path)
    assert any("duplicate" in p.lower() for p in problems)

def test_high_impact_auto_approval_flagged(tmp_path):
    _setup(tmp_path, [{**ATOM, "approval": "auto"}], [PATTERN])
    problems = validate_library(tmp_path)
    assert any("high-impact" in p.lower() for p in problems)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_validate.py -q`
Expected: FAIL with `ModuleNotFoundError: hcc_compiler.validate`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/hcc_compiler/validate.py
from __future__ import annotations
from pathlib import Path
from hcc_compiler.models import EvidenceAtom, RecommendationPattern, Tier
from hcc_compiler.loader import load_dir


def validate_library(root: Path) -> list[str]:
    """Return a list of human-readable problems. Empty list = clean."""
    root = Path(root)
    problems: list[str] = []

    atoms, a_err = load_dir(root / "atoms", EvidenceAtom)
    patterns, p_err = load_dir(root / "patterns", RecommendationPattern)
    problems += [f"{e.path}: {e.message.splitlines()[0]}" for e in (*a_err, *p_err)]

    ids = [a.id for a in atoms]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"duplicate atom id: {dup}")

    atom_ids = set(ids)
    for p in patterns:
        for ref in p.backing_atom_ids:
            if ref not in atom_ids:
                problems.append(f"{p.id}: backing_atom_id {ref} not found in library")

    for a in atoms:
        if a.tier == Tier.HIGH_IMPACT and a.approval.strip().lower() == "auto":
            problems.append(f"{a.id}: high-impact atom requires human approval, not 'auto'")

    return problems
```

```python
# scripts/curation/validate_library.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hcc_compiler.validate import validate_library  # noqa: E402

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("library")
    problems = validate_library(root)
    if problems:
        print(f"LIBRARY INVALID — {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("LIBRARY OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_validate.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/hcc_compiler/validate.py scripts/curation/validate_library.py tests/test_validate.py
git commit -m "feat: cross-record library validator + CLI"
```

---

### Task 6: Build the SQLite index

**Files:**
- Create: `src/hcc_compiler/build_index.py`
- Create: `scripts/curation/build_index.py`
- Test: `tests/test_build_index.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_build_index.py
import sqlite3
from pathlib import Path
import yaml
import pytest
from hcc_compiler.build_index import build_index
from tests.test_models_atom import VALID as ATOM
from tests.test_models_pattern import VALID as PATTERN

def _setup(root: Path):
    (root / "atoms").mkdir(parents=True)
    (root / "patterns").mkdir(parents=True)
    (root / "VERSION").write_text("0.1.0\n")
    (root / "atoms" / "a.yaml").write_text(yaml.safe_dump(ATOM))
    (root / "patterns" / "p.yaml").write_text(yaml.safe_dump(PATTERN))

def test_build_creates_queryable_index(tmp_path):
    _setup(tmp_path)
    db = tmp_path / "library.db"
    build_index(tmp_path, db)
    con = sqlite3.connect(db)
    assert con.execute("SELECT COUNT(*) FROM atoms WHERE domain='nutrition'").fetchone()[0] == 1
    assert con.execute("SELECT COUNT(*) FROM patterns").fetchone()[0] == 1
    assert con.execute("SELECT value FROM meta WHERE key='library_version'").fetchone()[0] == "0.1.0"
    con.close()

def test_build_refuses_invalid_library(tmp_path):
    (tmp_path / "atoms").mkdir(parents=True)
    (tmp_path / "patterns").mkdir(parents=True)
    (tmp_path / "VERSION").write_text("0.1.0\n")
    (tmp_path / "atoms" / "bad.yaml").write_text(yaml.safe_dump({**ATOM, "id": "nope"}))
    with pytest.raises(ValueError):
        build_index(tmp_path, tmp_path / "library.db")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_build_index.py -q`
Expected: FAIL with `ModuleNotFoundError: hcc_compiler.build_index`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/hcc_compiler/build_index.py
from __future__ import annotations
import sqlite3
from pathlib import Path
from hcc_compiler.models import EvidenceAtom, RecommendationPattern
from hcc_compiler.loader import load_dir

_SCHEMA = """
DROP TABLE IF EXISTS atoms;
DROP TABLE IF EXISTS patterns;
DROP TABLE IF EXISTS meta;
CREATE TABLE atoms (id TEXT PRIMARY KEY, domain TEXT, tier TEXT, evidence_level TEXT, json TEXT);
CREATE TABLE patterns (id TEXT PRIMARY KEY, domain TEXT, tier TEXT, json TEXT);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE INDEX idx_atoms_domain ON atoms(domain);
CREATE INDEX idx_atoms_tier ON atoms(tier);
CREATE INDEX idx_patterns_domain ON patterns(domain);
"""


def build_index(root: Path, out_db: Path) -> None:
    root = Path(root)
    atoms, a_err = load_dir(root / "atoms", EvidenceAtom)
    patterns, p_err = load_dir(root / "patterns", RecommendationPattern)
    if a_err or p_err:
        raise ValueError(
            f"library has {len(a_err) + len(p_err)} invalid record(s); "
            "run validate_library before building"
        )
    version = (root / "VERSION").read_text(encoding="utf-8").strip()

    con = sqlite3.connect(out_db)
    try:
        con.executescript(_SCHEMA)
        con.executemany(
            "INSERT INTO atoms VALUES (?,?,?,?,?)",
            [(a.id, a.domain.value, a.tier.value, a.evidence_level.value, a.model_dump_json()) for a in atoms],
        )
        con.executemany(
            "INSERT INTO patterns VALUES (?,?,?,?)",
            [(p.id, p.domain.value, p.tier.value, p.model_dump_json()) for p in patterns],
        )
        con.execute("INSERT INTO meta VALUES ('library_version', ?)", (version,))
        con.commit()
    finally:
        con.close()
```

```python
# scripts/curation/build_index.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hcc_compiler.build_index import build_index  # noqa: E402

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("library")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("library.db")
    build_index(root, out)
    print(f"Built {out} from {root}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_build_index.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add src/hcc_compiler/build_index.py scripts/curation/build_index.py tests/test_build_index.py
git commit -m "feat: compile validated library into SQLite index"
```

---

### Task 7: Seed initial content + end-to-end smoke

**Files:**
- Create: `library/atoms/nutrition/EA-NUT-0001.yaml` (and 2-3 more real atoms across nutrition/supplements/training)
- Create: `library/patterns/nutrition/RP-NUT-protein-band.yaml`
- Create: `Makefile`

- [ ] **Step 1: Author seed atoms** (use the Task-2 `VALID` shape with real, citation-verified content). Example:

```yaml
# library/atoms/nutrition/EA-NUT-0001.yaml
id: EA-NUT-0001
domain: nutrition
claim: "1.6-2.2 g/kg/day protein maximizes lean mass retention during an energy deficit."
evidence_level: L1
citations:
  - id: "10.1186/s12970-017-0177-8"
    locator_quote: "protein intakes of 1.6 to 2.2 g/kg/day..."
    existence: VERIFIED
    faithfulness: VERIFIED
population_applicability:
  age: "18-55"
  sex: "both"
  training_status: "trained"
  dose_magnitude: "moderate deficit"
  duration: "8-16 wk"
effect: "Preserves fat-free mass vs lower intake (SMD ~0.3)."
contraindications: ["CKD or other renal contraindication"]
tier: high-impact
approval: "Dev Wiggins 2026-05-21"
library_version: "0.1.0"
last_reviewed: "2026-05-21"
expiry: "2027-05-21"
```

```yaml
# library/patterns/nutrition/RP-NUT-protein-band.yaml
id: RP-NUT-protein-band
domain: nutrition
pattern: "protein target band"
parameterization: "1.6-2.2 g/kg/day; pick the upper end in steeper deficits or higher training volume."
backing_atom_ids: ["EA-NUT-0001"]
falsification_signal: "Fat-free mass drops >1%/week over 3 weeks at target intake."
safety_bounds: "Do not exceed 2.5 g/kg/day; flag renal history before recommending."
applies_because: "Trained adults in an energy deficit."
doesnt_apply_if: "CKD or other renal contraindication present."
tier: high-impact
approval: "Dev Wiggins 2026-05-21"
version: "0.1.0"
```

> Author at least 3 atoms (e.g. `EA-NUT-0001`, `EA-SUP-0001` creatine, `EA-TRA-0001` resistance volume) so the index has cross-domain content. Each citation must be real and verified — reuse the shipped citation gate's discipline (DOI resolves, locator quote supports the claim).

- [ ] **Step 2: Write the `Makefile`**

```makefile
validate:
	python scripts/curation/validate_library.py library

build:
	python scripts/curation/build_index.py library library.db

check: validate build
	pytest -q
```

- [ ] **Step 3: Run the end-to-end smoke**

Run: `cd ~/projects/hcc-compiler && . .venv/bin/activate && make check`
Expected: `LIBRARY OK`, then `Built library.db from library`, then all pytest tests pass.

- [ ] **Step 4: Verify the index by hand**

Run: `sqlite3 library.db "SELECT id, domain, tier FROM atoms;"`
Expected: the 3 seeded atoms listed with correct domain/tier.

- [ ] **Step 5: Commit**

```bash
git add library Makefile
git commit -m "feat: seed initial cross-domain library content + make check"
```

---

## What this plan delivers

A working `hcc-compiler` repo where: anyone can add a YAML atom/pattern, `make validate` lints the whole library (schema + dup IDs + dangling refs + high-impact human-approval), and `make build` compiles it into a queryable SQLite index stamped with the library version. This is the foundation the curation pipeline (Plan 2) populates and the SP2 compiler reads.

## Next plans (SP1 sequence, not in this plan)

- **Plan 2 — Curation pipeline:** harvest (PubMed/Crossref/OpenAlex) → strong-model extract → deterministic verify (port the shipped citation gate) → cross-model critique → tiered sign-off (PR review) → derive patterns → versioned release.
- **Plan 3 — Embeddings + retrieval API:** build the embeddings store from the index and expose the select/filter interface SP2's compiler consumes.
