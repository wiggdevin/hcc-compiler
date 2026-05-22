"""compile() orchestrator: intake → retrieval → applicability → safety → EvidencePack."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from hcc_compiler.models import Domain, EvidenceAtom, RecommendationPattern
from hcc_compiler.retrieve import query as retrieve_query
from hcc_compiler.sp2.intake import ClientIntake
from hcc_compiler.sp2.pack import (
    AtomMatch,
    CompileMetadata,
    DomainBlock,
    EvidencePack,
    PatternMatch,
)
from hcc_compiler.sp2.queries import derive_queries
from hcc_compiler.sp2.safety import check_contraindications
from hcc_compiler.sp2.score import score_applicability


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
    """Compile a ClientIntake against a SQLite library index into an EvidencePack.

    Pure deterministic function — no LLM calls.
    """
    db_path = Path(db_path)

    # ------------------------------------------------------------------
    # 1. Open SQLite read-only and read library_version from meta table.
    # ------------------------------------------------------------------
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute("SELECT value FROM meta WHERE key='library_version'").fetchone()
        db_version: str = row["value"] if row else ""

        # ------------------------------------------------------------------
        # 2. Version guard.
        # ------------------------------------------------------------------
        if version_check and intake.library_version != db_version:
            raise LibraryVersionMismatch(
                f"intake says {intake.library_version!r}, DB says {db_version!r}"
            )

        # ------------------------------------------------------------------
        # 3. Hydrate atoms and patterns once into dicts keyed by id.
        # ------------------------------------------------------------------
        atoms_by_id: dict[str, EvidenceAtom] = {}
        for row in con.execute("SELECT id, json FROM atoms").fetchall():
            try:
                atoms_by_id[row["id"]] = EvidenceAtom.model_validate_json(row["json"])
            except Exception:
                pass  # skip malformed rows defensively

        patterns_by_id: dict[str, RecommendationPattern] = {}
        for row in con.execute("SELECT id, json FROM patterns").fetchall():
            try:
                patterns_by_id[row["id"]] = RecommendationPattern.model_validate_json(row["json"])
            except Exception:
                pass
    finally:
        con.close()

    # ------------------------------------------------------------------
    # 4. Derive per-domain queries.
    # ------------------------------------------------------------------
    queries_by_domain = derive_queries(intake)

    # ------------------------------------------------------------------
    # 5-6. Retrieve per domain; aggregate max similarity per record_id.
    # ------------------------------------------------------------------
    # domain -> {record_id -> max_similarity}
    domain_hits: dict[Domain, dict[str, float]] = {d: {} for d in Domain}

    for domain, queries in queries_by_domain.items():
        agg = domain_hits[domain]
        for q in queries:
            hits = retrieve_query(text=q, k=top_k, domain=domain.value, db_path=db_path)
            for record_id, sim in hits:
                if record_id not in agg or sim > agg[record_id]:
                    agg[record_id] = sim

    # ------------------------------------------------------------------
    # 7-10. Build domain blocks.
    # ------------------------------------------------------------------
    domain_blocks: dict[Domain, DomainBlock] = {}
    all_warnings: set[str] = set()

    for domain in Domain:
        agg = domain_hits[domain]
        atom_hits: list[tuple[str, float]] = []
        pattern_hits: list[tuple[str, float]] = []

        # 7. Partition by id prefix.
        for record_id, sim in agg.items():
            if record_id in atoms_by_id:
                atom_hits.append((record_id, sim))
            elif record_id in patterns_by_id:
                pattern_hits.append((record_id, sim))

        # 8. Process atom hits.
        atom_matches: list[AtomMatch] = []
        for record_id, sim in atom_hits:
            atom = atoms_by_id.get(record_id)
            if atom is None:
                continue
            pop_score = score_applicability(atom, intake)
            if pop_score < applicability_threshold:
                continue
            warnings = check_contraindications(atom, intake)
            for w in warnings:
                all_warnings.add(w)
            atom_matches.append(AtomMatch(
                atom_id=record_id,
                similarity=sim,
                claim=atom.claim,
                citations=atom.citations,
                evidence_level=atom.evidence_level,
                population_match_score=pop_score,
                warnings=warnings,
            ))

        # 9. Process pattern hits.
        pattern_matches: list[PatternMatch] = []
        for record_id, sim in pattern_hits:
            pattern = patterns_by_id.get(record_id)
            if pattern is None:
                continue
            warnings = check_contraindications(pattern, intake)
            for w in warnings:
                all_warnings.add(w)
            pattern_matches.append(PatternMatch(
                pattern_id=record_id,
                similarity=sim,
                applies_because=pattern.applies_because,
                parameterization=pattern.parameterization,
                safety_bounds=pattern.safety_bounds,
                backing_atom_ids=pattern.backing_atom_ids,
                warnings=warnings,
            ))

        # 10. Sort: atoms by (pop_score desc, sim desc); patterns by sim desc.
        atom_matches.sort(key=lambda x: (x.population_match_score, x.similarity), reverse=True)
        pattern_matches.sort(key=lambda x: x.similarity, reverse=True)

        # 11. Build DomainBlock (gaps empty for now).
        domain_blocks[domain] = DomainBlock(
            patterns=pattern_matches,
            atoms=atom_matches,
            gaps=[],
        )

    # ------------------------------------------------------------------
    # 12. Build EvidencePack.
    # ------------------------------------------------------------------
    compile_metadata = CompileMetadata(
        top_k_per_domain=top_k,
        applicability_threshold=applicability_threshold,
        contraindication_hits=sorted(all_warnings),
        queries_issued={d.value: qs for d, qs in queries_by_domain.items()},
    )

    return EvidencePack(
        client_id=intake.client_id,
        library_version=db_version,
        compiled_at=datetime.now(timezone.utc),
        domain_recommendations=domain_blocks,
        compile_metadata=compile_metadata,
    )
