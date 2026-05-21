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
