"""D9 cache-interaction test — CRD Issue 18 / ADR-018.

The CRD Issue 12c structural-identity guarantee must hold even with a
populated Retrieval Memory block: retrieval sits inside the existing
StablePrefix envelope, under the existing single cache breakpoint, not as a
second cached block or a volatile suffix.
"""

from __future__ import annotations

from uuid import uuid4

from afterworlds.models.context import RetrievalMemoryPayload
from afterworlds.pipeline._stable_prefix_renderer import render_stable_prefix_blocks
from tests.pipeline.orchestrator.conftest import make_stable_prefix


class TestRetrievalMemoryCacheBreakpoint:
    def test_empty_retrieval_produces_no_extra_block(self) -> None:
        prefix = make_stable_prefix(uuid4())
        blocks = render_stable_prefix_blocks(prefix)
        assert sum(1 for b in blocks if b.has_cache_breakpoint) == 1

    def test_populated_retrieval_is_the_terminal_cache_breakpoint_block(self) -> None:
        prefix = make_stable_prefix(uuid4())
        populated = prefix.model_copy(
            update={
                "retrieval_memory": RetrievalMemoryPayload(
                    passages=("A relevant past scene.",)
                )
            }
        )
        blocks = render_stable_prefix_blocks(populated)

        # Exactly one cache breakpoint, still — never a second cached block.
        breakpoint_blocks = [b for b in blocks if b.has_cache_breakpoint]
        assert len(breakpoint_blocks) == 1
        # The breakpoint is on the LAST block, and it carries the retrieval text.
        assert blocks[-1].has_cache_breakpoint is True
        assert "A relevant past scene." in blocks[-1].text

    def test_populated_retrieval_does_not_change_preceding_blocks(self) -> None:
        """Byte-identical structural rendering for every block before retrieval."""
        prefix = make_stable_prefix(uuid4())
        empty_blocks = render_stable_prefix_blocks(prefix)

        populated = prefix.model_copy(
            update={
                "retrieval_memory": RetrievalMemoryPayload(
                    passages=("A relevant past scene.",)
                )
            }
        )
        populated_blocks = render_stable_prefix_blocks(populated)

        # One new block is added (retrieval); every earlier block is untouched
        # except that the previously-terminal block loses its breakpoint flag
        # (the new retrieval block inherits it instead).
        assert len(populated_blocks) == len(empty_blocks) + 1
        for empty_block, populated_block in zip(
            empty_blocks, populated_blocks[:-1], strict=True
        ):
            assert empty_block.text == populated_block.text
            assert populated_block.has_cache_breakpoint is False
