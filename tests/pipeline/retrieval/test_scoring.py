"""Unit tests for ADR-018 D5 distance-to-similarity normalization."""

from __future__ import annotations

import pytest

from afterworlds.pipeline.retrieval.scoring import normalize_similarity


class TestNormalizeSimilarity:
    def test_zero_distance_is_full_similarity(self) -> None:
        assert normalize_similarity(0.0, "cosine") == 1.0

    def test_max_distance_clamped_to_zero(self) -> None:
        assert normalize_similarity(2.0, "cosine") == 0.0

    def test_mid_distance(self) -> None:
        assert normalize_similarity(0.4, "cosine") == pytest.approx(0.6)

    def test_unsupported_metric_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported distance metric"):
            normalize_similarity(0.1, "euclidean")
