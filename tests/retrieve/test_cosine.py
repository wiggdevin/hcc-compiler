"""Tests for cosine similarity helper (SC2)."""
import pytest
from hcc_compiler.retrieve.cosine import cosine


def test_identical_vectors():
    assert cosine([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_orthogonal_vectors():
    assert cosine([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_opposite_vectors():
    assert cosine([1.0, 0.0], [-1.0, 0.0]) == -1.0


def test_magnitude_invariance():
    """Longer vector in same direction should still give 1.0."""
    assert cosine([3.0, 0.0], [1.0, 0.0]) == 1.0


def test_zero_vector_defensive():
    """Zero-magnitude vector returns 0.0 instead of raising ZeroDivisionError."""
    assert cosine([0.0, 0.0], [1.0, 0.0]) == 0.0


def test_high_dimensional_self_similarity():
    """768-dim vector vs itself should return 1.0."""
    v = [float(i) for i in range(768)]
    result = cosine(v, v)
    assert abs(result - 1.0) < 1e-9
