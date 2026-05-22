from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from hcc_compiler.models import EvidenceAtom, RecommendationPattern
from hcc_compiler.loader import load_dir
from hcc_compiler.llm.embed_client import embed, EmbedRequest

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

_EMBEDDINGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS embeddings (
  record_id TEXT PRIMARY KEY,
  record_type TEXT NOT NULL CHECK (record_type IN ('atom', 'pattern')),
  vector TEXT NOT NULL
);
"""


def build_index(root: Path, out_db: Path) -> None:
    root = Path(root)
    atoms, a_err = load_dir(root / "atoms", EvidenceAtom)

    patterns_dir = root / "patterns"
    if patterns_dir.exists():
        patterns, p_err = load_dir(patterns_dir, RecommendationPattern)
    else:
        patterns, p_err = [], []

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

        con.executescript(_EMBEDDINGS_SCHEMA)

        for a in atoms:
            vec = embed(EmbedRequest(text=a.claim))
            con.execute(
                "INSERT OR REPLACE INTO embeddings VALUES (?,?,?)",
                (a.id, "atom", json.dumps(vec)),
            )

        for p in patterns:
            text = f"{p.pattern} {p.parameterization}"
            vec = embed(EmbedRequest(text=text))
            con.execute(
                "INSERT OR REPLACE INTO embeddings VALUES (?,?,?)",
                (p.id, "pattern", json.dumps(vec)),
            )

        con.commit()
    finally:
        con.close()
