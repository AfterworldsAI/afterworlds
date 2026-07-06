"""Unit tests for the ADR-018 D3 chunking policy."""

from __future__ import annotations

from afterworlds.pipeline.retrieval.chunking import chunk_turn_prose


class TestChunkTurnProse:
    def test_short_text_single_chunk(self) -> None:
        text = "A short beat of prose."
        assert chunk_turn_prose(text, ceiling=4000) == [text]

    def test_exactly_at_ceiling_single_chunk(self) -> None:
        text = "x" * 100
        assert chunk_turn_prose(text, ceiling=100) == [text]

    def test_splits_on_paragraph_boundary_above_ceiling(self) -> None:
        para_a = "a" * 60
        para_b = "b" * 60
        text = f"{para_a}\n\n{para_b}"
        chunks = chunk_turn_prose(text, ceiling=60)
        assert len(chunks) == 2
        assert chunks[0] == para_a
        assert chunks[1] == para_b

    def test_groups_small_paragraphs_under_ceiling(self) -> None:
        paragraphs = ["short one.", "short two.", "short three."]
        text = "\n\n".join(paragraphs)
        chunks = chunk_turn_prose(text, ceiling=1000)
        assert chunks == [text]

    def test_oversized_single_paragraph_kept_whole(self) -> None:
        huge_paragraph = "x" * 500
        chunks = chunk_turn_prose(huge_paragraph, ceiling=100)
        assert chunks == [huge_paragraph]

    def test_empty_text(self) -> None:
        assert chunk_turn_prose("", ceiling=4000) == [""]
