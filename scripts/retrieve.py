"""CLI: semantic retrieval over the hcc-compiler SQLite library index.

Usage:
    python scripts/retrieve.py <query_text> [--k K] [--domain DOMAIN] [--db DB]

Output (one line per result):
    <record_id>\t<similarity:.4f>\t<excerpt:80>
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hcc_compiler.retrieve import query  # noqa: E402


def _get_excerpt(con: sqlite3.Connection, record_id: str) -> str:
    """Return claim (atoms) or pattern (patterns) text, truncated to 80 chars."""
    row = con.execute("SELECT json FROM atoms WHERE id = ?", (record_id,)).fetchone()
    if row:
        try:
            data = json.loads(row[0])
            text = data.get("claim", "")
        except (json.JSONDecodeError, TypeError):
            text = ""
        return text[:80]

    row = con.execute("SELECT json FROM patterns WHERE id = ?", (record_id,)).fetchone()
    if row:
        try:
            data = json.loads(row[0])
            text = data.get("pattern", "")
        except (json.JSONDecodeError, TypeError):
            text = ""
        return text[:80]

    return ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Semantic retrieval over the hcc-compiler SQLite library."
    )
    parser.add_argument("query_text", help="Query string to embed and search.")
    parser.add_argument("--k", type=int, default=10, help="Number of results (default: 10).")
    parser.add_argument("--domain", default=None, help="Filter by domain (e.g. nutrition).")
    parser.add_argument("--db", default="library.db", help="Path to SQLite DB (default: library.db).")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"error: database not found: {db_path}", file=sys.stderr)
        return 1

    results = query(
        text=args.query_text,
        k=args.k,
        domain=args.domain,
        db_path=db_path,
    )

    con = sqlite3.connect(db_path)
    try:
        for record_id, similarity in results:
            excerpt = _get_excerpt(con, record_id)
            print(f"{record_id}\t{similarity:.4f}\t{excerpt}")
    finally:
        con.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
