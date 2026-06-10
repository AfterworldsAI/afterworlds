"""Extractor pass result and error types — CRD Issue 10."""

from __future__ import annotations

from pydantic import BaseModel

from afterworlds.models.extractor import ExtractorProposalSet, ExtractorRoutingSummary


class ExtractorResult(BaseModel):
    """Typed return value from ExtractorService.extract().

    Attributes:
        proposal_set: All proposals extracted from the LLM response.
        routed: IDs of staged / created entries, grouped by proposal kind.
        input_token_count: Uncached input tokens consumed, when reported.
        output_token_count: Output tokens generated, when reported.
        cache_read_token_count: Cache-hit tokens, when reported.
        cache_creation_token_count: Cache-write tokens, when reported.
    """

    proposal_set: ExtractorProposalSet
    routed: ExtractorRoutingSummary
    input_token_count: int | None
    output_token_count: int | None
    cache_read_token_count: int | None
    cache_creation_token_count: int | None

    # Additive Issue 14a fields
    provider: str | None = None
    model_identifier: str | None = None
    model_tier: str | None = None  # ModelTier value as str to avoid circular import


class ExtractorPassError(Exception):
    """Raised when the Extractor pass cannot produce a usable result.

    Fail-closed: no silent fallback, no default stub.  Covers:
      - No tool_use block in the provider response.
      - Tool name mismatch or malformed tool input.
      - Underlying provider exception.
      - Natural-key resolution failure (EntityNotFoundError or ValueError
        from routing) — the entire turn is aborted with no DB state committed.

    The original cause is preserved as ``__cause__`` via standard Python
    exception chaining (``raise ExtractorPassError(...) from original``).
    """
