"""Typed payloads and exceptions for the RPG Adjudication pass — CRD Issue 15."""

from __future__ import annotations

from pydantic import BaseModel

from afterworlds.models.rpg import (
    PendingRollRequest,
    ResolvedAdjudicationRecord,
    WriterAdjudicationView,
)


class AdjudicationPassResult(BaseModel):
    """Complete result returned by ``RpgAdjudicationPassService.adjudicate()``.

    ``proposals`` and ``writer_views`` are parallel sequences: each proposal
    at index i has a corresponding writer view at index i.  The Orchestrator
    appends ``writer_views`` to the ``PassForwardLedger`` for the Writer pass.

    ``pending_roll_request`` is populated for turns that announce a PLAYER
    roll; it is None for AI/hidden roll turns and for turns where no roll is
    required.

    Token counts follow the ``PlannerResult`` convention: the pass service
    populates them from the provider call result; they may be None if the
    adjudication pass did not call the provider (e.g., consume-only turns).
    """

    proposals: tuple[ResolvedAdjudicationRecord, ...]
    writer_views: tuple[WriterAdjudicationView, ...]
    pending_roll_request: PendingRollRequest | None = None

    provider: str | None = None
    model_identifier: str | None = None
    model_tier: str | None = None
    latency_ms: int = 0
    input_token_count: int | None = None
    output_token_count: int | None = None
    cache_read_token_count: int | None = None
    cache_creation_token_count: int | None = None


class AdjudicationPassError(Exception):
    """Fail-closed exception for the RPG Adjudication pass.

    Covers: no tool_use block, tool name mismatch, malformed proposal output,
    provider exception, and schema validation failure.  No DB state is committed
    when this is raised.
    """


__all__ = [
    "AdjudicationPassError",
    "AdjudicationPassResult",
]
