"""SC1: orphan embedding rows are removed when their atom/pattern is deleted."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import yaml

from hcc_compiler.build_index import build_index
from tests.test_models_atom import VALID as ATOM
from tests.test_models_pattern import VALID as PATTERN


def _mock_embed(req):
    digest = hashlib.md5(req.text.encode()).hexdigest()
    return [int(digest[i : i + 2], 16) / 255.0 for i in range(0, 32, 2)]


def _setup(root: Path):
    (root / "atoms").mkdir(parents=True)
    (root / "patterns").mkdir(parents=True)
    (root / "VERSION").write_text("0.1.0\n")
    (root / "atoms" / "a.yaml").write_text(yaml.safe_dump(ATOM))
    (root / "patterns" / "p.yaml").write_text(yaml.safe_dump(PATTERN))


def test_deleted_atom_leaves_no_orphan_embedding(tmp_path):
    """After removing an atom and rebuilding, its embedding row is gone."""
    _setup(tmp_path)
    db = tmp_path / "library.db"

    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed):
        build_index(tmp_path, db)

    # Confirm the embedding exists after the first build.
    con = sqlite3.connect(db)
    count_before = con.execute(
        "SELECT COUNT(*) FROM embeddings WHERE record_id=?", (ATOM["id"],)
    ).fetchone()[0]
    con.close()
    assert count_before == 1, "Atom embedding should exist after first build"

    # Remove the atom file and rebuild.
    (tmp_path / "atoms" / "a.yaml").unlink()

    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed):
        build_index(tmp_path, db)

    con = sqlite3.connect(db)
    try:
        orphan_count = con.execute(
            "SELECT COUNT(*) FROM embeddings WHERE record_id=?", (ATOM["id"],)
        ).fetchone()[0]
        assert orphan_count == 0, (
            f"Orphan embedding row for deleted atom {ATOM['id']} still exists"
        )
    finally:
        con.close()


def test_deleted_pattern_leaves_no_orphan_embedding(tmp_path):
    """After removing a pattern and rebuilding, its embedding row is gone."""
    _setup(tmp_path)
    db = tmp_path / "library.db"

    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed):
        build_index(tmp_path, db)

    # Confirm the embedding exists after the first build.
    con = sqlite3.connect(db)
    count_before = con.execute(
        "SELECT COUNT(*) FROM embeddings WHERE record_id=?", (PATTERN["id"],)
    ).fetchone()[0]
    con.close()
    assert count_before == 1, "Pattern embedding should exist after first build"

    # Remove the pattern file and rebuild.
    (tmp_path / "patterns" / "p.yaml").unlink()

    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed):
        build_index(tmp_path, db)

    con = sqlite3.connect(db)
    try:
        orphan_count = con.execute(
            "SELECT COUNT(*) FROM embeddings WHERE record_id=?", (PATTERN["id"],)
        ).fetchone()[0]
        assert orphan_count == 0, (
            f"Orphan embedding row for deleted pattern {PATTERN['id']} still exists"
        )
    finally:
        con.close()


def test_no_orphans_after_full_rebuild(tmp_path):
    """After rebuild, every embeddings row has a matching atom or pattern."""
    _setup(tmp_path)
    db = tmp_path / "library.db"

    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed):
        build_index(tmp_path, db)
        # Remove atom and rebuild — embeddings should stay consistent.
        (tmp_path / "atoms" / "a.yaml").unlink()
        build_index(tmp_path, db)

    con = sqlite3.connect(db)
    try:
        orphan_atoms = con.execute(
            "SELECT COUNT(*) FROM embeddings e "
            "LEFT JOIN atoms a ON e.record_id=a.id "
            "WHERE e.record_type='atom' AND a.id IS NULL"
        ).fetchone()[0]
        orphan_patterns = con.execute(
            "SELECT COUNT(*) FROM embeddings e "
            "LEFT JOIN patterns p ON e.record_id=p.id "
            "WHERE e.record_type='pattern' AND p.id IS NULL"
        ).fetchone()[0]
        assert orphan_atoms == 0, f"{orphan_atoms} orphan atom embedding(s) remain"
        assert orphan_patterns == 0, f"{orphan_patterns} orphan pattern embedding(s) remain"
    finally:
        con.close()
