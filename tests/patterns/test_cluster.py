"""Tests for single-link agglomerative clustering (SC6)."""
import pytest
from hcc_compiler.patterns.cluster import cluster


def _unit(components: list[float]) -> list[float]:
    """Normalize a vector to unit length."""
    import math
    mag = math.sqrt(sum(x * x for x in components))
    return [x / mag for x in components]


# ---------------------------------------------------------------------------
# Test 1: 3 near-identical + 2 unrelated → 2 clusters
# ---------------------------------------------------------------------------

def test_two_groups():
    """3 near-identical vectors cluster together; 2 unrelated form a second cluster."""
    # Group A: nearly identical — cosine distance ~ 0
    a1 = _unit([1.0, 0.0, 0.0, 0.0])
    a2 = _unit([1.0, 0.01, 0.0, 0.0])
    a3 = _unit([1.0, 0.02, 0.0, 0.0])
    # Group B: orthogonal direction — cosine distance to group A ~ 1
    b1 = _unit([0.0, 0.0, 1.0, 0.0])
    b2 = _unit([0.0, 0.0, 1.0, 0.01])

    result = cluster([a1, a2, a3, b1, b2], distance_threshold=0.30)

    assert len(result) == 2
    sizes = sorted(len(c) for c in result)
    assert sizes == [2, 3]

    # Group A indices are 0,1,2; group B are 3,4
    flat_a = next(c for c in result if 0 in c)
    flat_b = next(c for c in result if 3 in c)
    assert set(flat_a) == {0, 1, 2}
    assert set(flat_b) == {3, 4}


# ---------------------------------------------------------------------------
# Test 2: All mutually distant → N singleton clusters
# ---------------------------------------------------------------------------

def test_all_singletons():
    """Orthogonal unit vectors are maximally distant — each is its own cluster."""
    v0 = [1.0, 0.0, 0.0, 0.0]
    v1 = [0.0, 1.0, 0.0, 0.0]
    v2 = [0.0, 0.0, 1.0, 0.0]
    v3 = [0.0, 0.0, 0.0, 1.0]

    result = cluster([v0, v1, v2, v3], distance_threshold=0.30)

    assert len(result) == 4
    assert all(len(c) == 1 for c in result)
    # Verify singletons contain expected indices
    flat = [c[0] for c in result]
    assert sorted(flat) == [0, 1, 2, 3]


# ---------------------------------------------------------------------------
# Test 3: Chain — single-link must merge A-B-C even though A far from C
# ---------------------------------------------------------------------------

def test_chain_single_link():
    """
    Single-link semantics: A close to B (dist 0.2), B close to C (dist 0.2),
    A far from C (dist ~0.5). All three should merge into one cluster via the chain.
    """
    import math

    # Construct vectors where cosine distances match the spec.
    # A = [1, 0], B = [cos(theta_AB), sin(theta_AB)] with dist(A,B) = 1 - cos(theta_AB) = 0.2
    # => cos(theta_AB) = 0.8, so theta_AB = arccos(0.8)
    # C is placed so dist(B,C) = 0.2, and dist(A,C) ~ 0.5
    # => angle from A to B: arccos(0.8) ≈ 36.87°
    # => angle from B to C: arccos(0.8) ≈ 36.87° further from A
    # => angle from A to C: 2 * arccos(0.8) ≈ 73.74°, cos ≈ 0.2801 (but we want ~0.5)
    # Use 3D to get exact distances while keeping things controlled.

    # A, B, C embedded in 3D so pairwise cosine distances are exactly as desired.
    theta_AB = math.acos(0.8)   # dist(A,B) = 0.2
    theta_BC = math.acos(0.8)   # dist(B,C) = 0.2

    a = [1.0, 0.0, 0.0]
    b = [math.cos(theta_AB), math.sin(theta_AB), 0.0]
    # Place C at angle theta_BC from B in the AB-plane (same side)
    angle_c = theta_AB + theta_BC
    c = [math.cos(angle_c), math.sin(angle_c), 0.0]

    # Verify constructed distances
    from hcc_compiler.retrieve.cosine import cosine
    dist_ab = 1.0 - cosine(a, b)
    dist_bc = 1.0 - cosine(b, c)
    dist_ac = 1.0 - cosine(a, c)

    assert dist_ab < 0.30, f"dist(A,B)={dist_ab} should be < 0.30"
    assert dist_bc < 0.30, f"dist(B,C)={dist_bc} should be < 0.30"
    assert dist_ac > 0.30, f"dist(A,C)={dist_ac} should be > 0.30 (they are far)"

    # Add a distant outlier D
    d = [0.0, 0.0, 1.0]

    result = cluster([a, b, c, d], distance_threshold=0.30)

    assert len(result) == 2
    abc_cluster = next(c_ for c_ in result if 0 in c_)
    d_cluster = next(c_ for c_ in result if 3 in c_)
    assert set(abc_cluster) == {0, 1, 2}, f"A,B,C should be in one cluster via chain; got {result}"
    assert set(d_cluster) == {3}


# ---------------------------------------------------------------------------
# Test 4: Empty input → empty result
# ---------------------------------------------------------------------------

def test_empty():
    result = cluster([], distance_threshold=0.30)
    assert result == []


# ---------------------------------------------------------------------------
# Test 5: Single vector → single singleton cluster
# ---------------------------------------------------------------------------

def test_single_vector():
    result = cluster([[1.0, 0.0, 0.0]], distance_threshold=0.30)
    assert result == [[0]]


# ---------------------------------------------------------------------------
# Test 6: Returns indices, not vectors
# ---------------------------------------------------------------------------

def test_returns_indices():
    """Result elements are ints, not floats/lists — caller can map back to atom IDs."""
    v0 = [1.0, 0.0]
    v1 = [0.0, 1.0]
    result = cluster([v0, v1], distance_threshold=0.30)

    # Each cluster is a list of ints
    for c in result:
        assert isinstance(c, list)
        for idx in c:
            assert isinstance(idx, int), f"Expected int index, got {type(idx)}: {idx}"
