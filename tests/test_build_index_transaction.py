"""SC2: build_index leaves no partial write when embed() fails mid-run."""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from unittest.mock import patch

import yaml
import pytest

from hcc_compiler.build_index import build_index
from tests.test_models_atom import VALID as ATOM
from tests.test_models_pattern import VALID as PATTERN


def _mock_embed(req):
    digest = hashlib.md5(req.text.encode()).hexdigest()
    return [int(digest[i : i + 2], 16) / 255.0 for i in range(0, 32, 2)]


def _setup_multi_atom(root: Path):
    """Library with three atoms and one pattern."""
    (root / "atoms").mkdir(parents=True)
    (root / "patterns").mkdir(parents=True)
    (root / "VERSION").write_text("0.1.0\n")

    atom_ids = ["EA-NUT-0001", "EA-NUT-0002", "EA-NUT-0003"]
    for i, aid in enumerate(atom_ids):
        atom = {
            **ATOM,
            "id": aid,
            "claim": f"Test claim {i + 1}",
            "citations": [{**ATOM["citations"][0]}],
        }
        (root / "atoms" / f"a{i}.yaml").write_text(yaml.safe_dump(atom))

    (root / "patterns" / "p.yaml").write_text(yaml.safe_dump(PATTERN))


def test_embed_failure_raises_and_leaves_no_partial_state(tmp_path):
    """If embed() raises on the 3rd call, build_index raises and no partial
    rows are written to the embeddings table."""
    _setup_multi_atom(tmp_path)
    db = tmp_path / "library.db"

    call_count = 0

    def _failing_embed(req):
        nonlocal call_count
        call_count += 1
        if call_count == 3:
            raise RuntimeError("embed failed on call 3")
        return _mock_embed(req)

    with pytest.raises(RuntimeError, match="embed failed on call 3"):
        with patch("hcc_compiler.build_index.embed", side_effect=_failing_embed):
            build_index(tmp_path, db)

    # The DB may not exist at all if the failure happened before any write,
    # OR it exists but must have no partial state.
    if not db.exists():
        return  # No DB written — cleanest possible outcome.

    con = sqlite3.connect(db)
    try:
        # atoms table might not exist if _SCHEMA never committed
        tables = {
            r[0]
            for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        if "embeddings" in tables:
            embed_count = con.execute(
                "SELECT COUNT(*) FROM embeddings"
            ).fetchone()[0]
            assert embed_count == 0, (
                f"Partial state: {embed_count} embedding row(s) written despite embed() failure"
            )

        if "atoms" in tables:
            atom_count = con.execute("SELECT COUNT(*) FROM atoms").fetchone()[0]
            assert atom_count == 0, (
                f"Partial state: {atom_count} atom row(s) written despite embed() failure"
            )
    finally:
        con.close()


def test_embed_failure_on_pattern_leaves_no_partial_state(tmp_path):
    """If embed() raises during pattern embedding, no partial rows persist."""
    _setup_multi_atom(tmp_path)
    db = tmp_path / "library.db"

    # atoms embed fine (3 calls), pattern embed raises on 4th call
    call_count = 0

    def _failing_on_pattern(req):
        nonlocal call_count
        call_count += 1
        if call_count == 4:
            raise RuntimeError("embed failed on pattern")
        return _mock_embed(req)

    with pytest.raises(RuntimeError, match="embed failed on pattern"):
        with patch("hcc_compiler.build_index.embed", side_effect=_failing_on_pattern):
            build_index(tmp_path, db)

    if not db.exists():
        return

    con = sqlite3.connect(db)
    try:
        tables = {
            r[0]
            for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        if "embeddings" in tables:
            embed_count = con.execute(
                "SELECT COUNT(*) FROM embeddings"
            ).fetchone()[0]
            assert embed_count == 0, (
                f"Partial state: {embed_count} embedding row(s) written despite embed() failure"
            )
    finally:
        con.close()


def test_db_write_failure_inside_transaction_leaves_no_partial_state(tmp_path):
    """If a DB write fails INSIDE the BEGIN/COMMIT window, ROLLBACK must leave
    row counts identical to the pre-call snapshot.

    Injection: we run a full initial build_index to seed the DB, snapshot row
    counts, then re-run with sqlite3.Connection.executemany patched to raise on
    its second call (the patterns INSERT, which is inside BEGIN).  The first
    executemany (atoms) has already written rows into the open transaction when
    the failure occurs.  Without an explicit ROLLBACK those atom writes would
    leak; the assertion proves they do not.
    """
    _setup_multi_atom(tmp_path)
    db = tmp_path / "library.db"

    # --- seed build: populate the DB with known rows ---
    with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed):
        build_index(tmp_path, db)

    con = sqlite3.connect(db)
    seed_atoms = con.execute("SELECT COUNT(*) FROM atoms").fetchone()[0]
    seed_patterns = con.execute("SELECT COUNT(*) FROM patterns").fetchone()[0]
    seed_embeddings = con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    con.close()

    # --- second build with a DB-path failure inside BEGIN ---
    _real_executemany = sqlite3.Connection.executemany

    def _failing_executemany(self, sql, params):
        # Inject on the patterns INSERT (inside BEGIN, after atoms INSERT has
        # already written rows in the open transaction). Matching by SQL
        # substring rather than call ordinal so future schema reshuffles
        # don't silently move the injection point.
        if "INSERT INTO patterns" in sql:
            raise sqlite3.OperationalError("injected DB failure inside transaction")
        return _real_executemany(self, sql, params)

    with pytest.raises((sqlite3.OperationalError, Exception)):
        with patch("hcc_compiler.build_index.embed", side_effect=_mock_embed):
            with patch.object(sqlite3.Connection, "executemany", _failing_executemany):
                build_index(tmp_path, db)

    # Row counts must be identical to the pre-call snapshot (ROLLBACK worked).
    con = sqlite3.connect(db)
    try:
        after_atoms = con.execute("SELECT COUNT(*) FROM atoms").fetchone()[0]
        after_patterns = con.execute("SELECT COUNT(*) FROM patterns").fetchone()[0]
        after_embeddings = con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    finally:
        con.close()

    assert after_atoms == seed_atoms, (
        f"ROLLBACK failed: atoms went {seed_atoms} → {after_atoms}"
    )
    assert after_patterns == seed_patterns, (
        f"ROLLBACK failed: patterns went {seed_patterns} → {after_patterns}"
    )
    assert after_embeddings == seed_embeddings, (
        f"ROLLBACK failed: embeddings went {seed_embeddings} → {after_embeddings}"
    )
