"""Writer pass result and error types — CRD Issue 9."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class WriterResult(BaseModel):
    """Typed return value from WriterService.write().

    All token counts are advisory in v1 — they exist so downstream
    orchestration (Issue 12) and entitlement routing (Issue 13) can consume
    them without reopening the Writer contract.  Fields are None when the
    provider did not report them, not 0.

    Attributes:
        turn_id: UUID of the persisted Turn row.
        assistant_output: Parsed prose from the Writer response.
        model_identifier: Provider and model string, e.g.
            ``"anthropic:claude-sonnet-4-5"``.
        latency_ms: Wall-clock latency of the provider call in milliseconds.
        input_token_count: Uncached input tokens consumed, when reported.
        output_token_count: Output tokens generated, when reported.
        cache_read_token_count: Cache-hit tokens, when reported.
        cache_creation_token_count: Cache-write tokens, when reported.
            Distinct from cache_read_token_count — the first turn of a session
            pays the cache-write cost; Issue 13 accounting needs both.
    """

    turn_id: UUID
    assistant_output: str
    model_identifier: str
    latency_ms: int
    input_token_count: int | None
    output_token_count: int | None
    cache_read_token_count: int | None
    cache_creation_token_count: int | None

    # Additive Issue 14a fields
    provider: str | None = None
    model_tier: str | None = None  # ModelTier value as str to avoid circular import


class WriterPassError(Exception):
    """Raised when the Writer pass cannot produce a usable result.

    Fail-closed: no silent fallback, no default stub text.  Covers three
    failure modes:
      - Empty or whitespace-only response from the provider.
      - Malformed response envelope (missing required fields).
      - Underlying provider exception.

    The original cause is preserved as ``__cause__`` via standard Python
    exception chaining (``raise WriterPassError(...) from original``).
    """
