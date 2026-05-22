import argparse
import json
import sqlite3
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import yaml  # noqa: E402

from hcc_compiler.loader import load_dir  # noqa: E402
from hcc_compiler.models import EvidenceAtom, RecommendationPattern  # noqa: E402
from hcc_compiler.patterns.cluster import cluster  # noqa: E402
from hcc_compiler.patterns.derive import derive_pattern  # noqa: E402
from hcc_compiler.retrieve.cosine import cosine  # noqa: E402


def _load_embeddings(db_path: Path, atom_ids: list[str]) -> dict[str, list[float]]:
    conn = sqlite3.connect(str(db_path))
    placeholders = ",".join("?" * len(atom_ids))
    rows = conn.execute(
        f"SELECT record_id, vector FROM embeddings WHERE record_id IN ({placeholders})",
        atom_ids,
    ).fetchall()
    conn.close()
    return {row[0]: json.loads(row[1]) for row in rows}


def _mean_intra_sim(vectors: list[list[float]]) -> float:
    pairs = list(combinations(range(len(vectors)), 2))
    if not pairs:
        return 1.0
    total = sum(cosine(vectors[i], vectors[j]) for i, j in pairs)
    return total / len(pairs)


def _pattern_id_exists(library_root: Path, pattern_id: str) -> bool:
    fname = f"{pattern_id}.yaml"
    # Check queue
    if (library_root / "queue" / fname).exists():
        return True
    # Check all patterns/<domain>/ subdirectories
    patterns_root = library_root / "patterns"
    if not patterns_root.exists():
        return False
    return any(
        (d / fname).exists()
        for d in patterns_root.iterdir()
        if d.is_dir()
    )


def main() -> dict:
    parser = argparse.ArgumentParser(description="Derive RecommendationPatterns from atom clusters.")
    parser.add_argument("--library", default="library")
    parser.add_argument("--db", default="library.db")
    parser.add_argument("--auto-admit-threshold", type=float, default=0.80)
    parser.add_argument("--min-atoms", type=int, default=3)
    args = parser.parse_args()

    library_root = Path(args.library)
    db_path = Path(args.db)
    threshold = args.auto_admit_threshold
    min_atoms = args.min_atoms

    tally = {"admitted": 0, "queued": 0, "skipped-too-small": 0, "skipped-existing": 0}

    atoms_root = library_root / "atoms"
    if not atoms_root.exists():
        print(f"admitted=0 queued=0 skipped-too-small=0 skipped-existing=0")
        return tally

    # Collect all admitted atoms grouped by domain directory name
    domain_dirs = sorted(d for d in atoms_root.iterdir() if d.is_dir())

    for domain_dir in domain_dirs:
        atoms, errors = load_dir(domain_dir, EvidenceAtom)
        if not atoms:
            continue

        atom_ids = [a.id for a in atoms]
        embedding_map = _load_embeddings(db_path, atom_ids)

        # Build ordered list of (atom, vector) for atoms that have embeddings
        indexed: list[tuple[EvidenceAtom, list[float]]] = []
        for atom in atoms:
            if atom.id in embedding_map:
                indexed.append((atom, embedding_map[atom.id]))

        if not indexed:
            continue

        vectors = [vec for _, vec in indexed]
        clusters = cluster(vectors, distance_threshold=0.30)

        for clust_indices in clusters:
            clust_atoms = [indexed[i][0] for i in clust_indices]
            clust_vecs = [indexed[i][1] for i in clust_indices]

            if len(clust_atoms) < min_atoms:
                print(
                    f"skipped-too-small cluster of {len(clust_atoms)} in {domain_dir.name}",
                    file=sys.stderr,
                )
                tally["skipped-too-small"] += 1
                continue

            pattern: RecommendationPattern = derive_pattern(clust_atoms)

            if _pattern_id_exists(library_root, pattern.id):
                print(f"skipped-existing {pattern.id}", file=sys.stderr)
                tally["skipped-existing"] += 1
                continue

            mean_sim = _mean_intra_sim(clust_vecs)

            if mean_sim >= threshold:
                dest_dir = library_root / "patterns" / domain_dir.name
                decision = "admitted"
            else:
                dest_dir = library_root / "queue"
                decision = "queued"

            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / f"{pattern.id}.yaml"
            dest_path.write_text(
                yaml.safe_dump(
                    pattern.model_dump(mode="json"),
                    sort_keys=False,
                    allow_unicode=True,
                    default_flow_style=False,
                ),
                encoding="utf-8",
            )
            print(f"{decision} {pattern.id}")
            tally[decision] += 1

    print(
        f"admitted={tally['admitted']} queued={tally['queued']} "
        f"skipped-too-small={tally['skipped-too-small']} skipped-existing={tally['skipped-existing']}"
    )
    return tally


if __name__ == "__main__":
    main()
