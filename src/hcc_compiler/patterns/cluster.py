"""Single-link agglomerative clustering on cosine distance (stdlib only)."""
from hcc_compiler.retrieve.cosine import cosine


def cluster(
    vectors: list[list[float]],
    distance_threshold: float = 0.30,
) -> list[list[int]]:
    """Cluster *vectors* by single-link agglomerative clustering on cosine distance.

    Two vectors are "close" when ``1 - cosine_similarity(a, b) < distance_threshold``.
    Two clusters merge when their *closest* pair (single-link) is below the threshold.

    Returns a list of clusters, each cluster being a sorted list of input indices.
    Clusters are sorted by their first (lowest) index.  Result is deterministic.

    No external dependencies — stdlib only.
    """
    n = len(vectors)
    if n == 0:
        return []

    # Union-Find with path compression + union by rank.
    parent = list(range(n))
    rank = [0] * n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path halving
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx == ry:
            return
        if rank[rx] < rank[ry]:
            rx, ry = ry, rx
        parent[ry] = rx
        if rank[rx] == rank[ry]:
            rank[rx] += 1

    # O(n²) pairwise check — acceptable for ~200-atom scale.
    for i in range(n):
        for j in range(i + 1, n):
            dist = 1.0 - cosine(vectors[i], vectors[j])
            if dist < distance_threshold:
                union(i, j)

    # Collect indices by root, then sort for determinism.
    groups: dict[int, list[int]] = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(i)

    # Sort each cluster (already ascending because we iterated 0..n-1).
    # Sort clusters by their first element.
    return sorted(groups.values(), key=lambda c: c[0])
