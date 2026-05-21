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
