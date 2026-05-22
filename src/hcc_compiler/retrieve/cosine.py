"""Cosine similarity between two float vectors (stdlib only)."""
import math


def cosine(a: list[float], b: list[float]) -> float:
    """Return the cosine similarity of vectors *a* and *b*.

    Returns 0.0 when either vector has zero magnitude (defensive — no
    ZeroDivisionError).
    """
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)
