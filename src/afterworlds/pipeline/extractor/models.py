"""Extractor pass result and error types — CRD Issue 10."""

from __future__ import annotations

from pydantic import BaseModel

from afterworlds.models.story_bible import ProvisionalProposal


class ExtractorResult(BaseModel):
    """Typed return value from ExtractorService.extract().

    Attributes:
        proposals: All proposals staged during this pass (both pending and
            auto-committed).
        pending_proposals: Subset of proposals still in PENDING status —
            locked-fact proposals that require Sojourner confirmation.
        auto_committed: Proposals that were staged and immediately ratified
            (soft facts, transient states, events, unresolved threads).
        pass_forward_content: Text summary of Extractor findings, added to the
            PassForwardLedger by the pipeline (Issue 12) for downstream passes.
        model_identifier: Provider and model string, e.g.
            ``"anthropic:claude-haiku-4-5-20251001"``.
        latency_ms: Wall-clock latency of the provider call in milliseconds.
        input_token_count: Uncached input tokens consumed, when reported.
        output_token_count: Output tokens generated, when reported.
        cache_read_token_count: Cache-hit tokens, when reported.
        cache_creation_token_count: Cache-write tokens, when reported.
    """

    proposals: list[ProvisionalProposal]
    pending_proposals: list[ProvisionalProposal]
    auto_committed: list[ProvisionalProposal]
    pass_forward_content: str
    model_identifier: str
    latency_ms: int
    input_token_count: int | None
    output_token_count: int | None
    cache_read_token_count: int | None
    cache_creation_token_count: int | None


class ExtractorPassError(Exception):
    """Raised when the Extractor pass cannot produce a usable result.

    Fail-closed: no silent fallback, no default stub.  Covers:
      - No tool_use block in the provider response.
      - Tool name mismatch or malformed tool input.
      - Underlying provider exception.

    The original cause is preserved as ``__cause__`` via standard Python
    exception chaining (``raise ExtractorPassError(...) from original``).
    """
