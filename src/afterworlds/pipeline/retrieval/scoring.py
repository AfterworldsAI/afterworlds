"""Distance-to-similarity normalization — CRD Issue 18 / ADR-018 D5.

Chroma returns a raw, metric-specific distance. Comparison against the
configured threshold must never operate on that raw distance directly —
everything is normalized into one internal ``normalized_similarity`` value
first. Cutoff is inclusive: retained when ``normalized_similarity >=
minimum_similarity_threshold``.
"""

from __future__ import annotations

_SUPPORTED_METRICS = ("cosine",)


def normalize_similarity(distance: float, metric: str) -> float:
    """Convert a raw Chroma distance into a [0, 1] normalized similarity.

    Only "cosine" is supported in v1 (the only metric
    ``pipeline/retrieval/config.py`` configures for the story_memory
    collection). Cosine distance in Chroma is ``1 - cosine_similarity``;
    clamped to [0, 1] since embeddings are not guaranteed unit-normalized.
    """
    if metric not in _SUPPORTED_METRICS:
        raise ValueError(
            f"Unsupported distance metric {metric!r}; only {_SUPPORTED_METRICS} "
            "are normalized in v1"
        )
    return max(0.0, min(1.0, 1.0 - distance))
