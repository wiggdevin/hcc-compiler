"""Semantic retrieval over the hcc-compiler SQLite library index."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from hcc_compiler.llm.embed_client import embed, EmbedRequest
from hcc_compiler.retrieve.cosine import cosine


def query(
    text: str,
    k: int = 10,
    domain: str | None = None,
    db_path: Path = Path("library.db"),
) -> list[tuple[str, float]]:
    """Return top-k (record_id, similarity) tuples for *text*.

    - Embeds *text* via the T1 embed client.
    - Loads candidates from the SQLite ``embeddings`` table.
    - When *domain* is given, filters by joining against the ``atoms`` or
      ``patterns`` table (both have a ``domain`` column keyed to ``record_type``).
    - Computes cosine similarity for each candidate.
    - Returns up to *k* results sorted descending by similarity.
    - Returns ``[]`` when the embeddings table is empty.
    """
    db_path = Path(db_path)
    query_vec = embed(EmbedRequest(text=text))

    con = sqlite3.connect(db_path)
    try:
        if domain is None:
            rows = con.execute(
                "SELECT record_id, vector FROM embeddings"
            ).fetchall()
        else:
            # JOIN atoms for record_type='atom', patterns for record_type='pattern'.
            # UNION so domain filter applies to both tables independently.
            rows = con.execute(
                """
                SELECT e.record_id, e.vector
                FROM embeddings e
                JOIN atoms a ON e.record_id = a.id
                WHERE e.record_type = 'atom' AND a.domain = ?
                UNION ALL
                SELECT e.record_id, e.vector
                FROM embeddings e
                JOIN patterns p ON e.record_id = p.id
                WHERE e.record_type = 'pattern' AND p.domain = ?
                """,
                (domain, domain),
            ).fetchall()
    finally:
        con.close()

    if not rows:
        return []

    scored: list[tuple[str, float]] = []
    for record_id, vector_json in rows:
        vec = json.loads(vector_json)
        sim = cosine(query_vec, vec)
        scored.append((record_id, sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
