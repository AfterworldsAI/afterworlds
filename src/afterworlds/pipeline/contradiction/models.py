"""Typed payloads and exceptions for the Contradiction pass — CRD Issue 11."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, field_validator


class ContradictionCategory(StrEnum):
    DEAD_CHARACTER_ACTING = "dead_character_acting"
    ITEM_NEVER_ACQUIRED = "item_never_acquired"
    LOCKED_FACT_VIOLATED = "locked_fact_violated"
    LOCATION_DRIFT = "location_drift"
    NAME_DRIFT = "name_drift"
    POV_TENSE_SHIFT = "pov_tense_shift"
    OTHER = "other"


class ContradictionVerdict(StrEnum):
    CLEAR = "clear"
    BLOCKED = "blocked"


class ContradictionViolation(BaseModel):
    category: ContradictionCategory
    description: str
    canon_reference: str

    @field_validator("description", "canon_reference")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must be a non-empty string after stripping whitespace")
        return v


class ContradictionReport(BaseModel):
    violations: list[ContradictionViolation]


class ContradictionResult(BaseModel):
    verdict: ContradictionVerdict
    violations: list[ContradictionViolation]
    model_identifier: str
    latency_ms: int
    input_token_count: int | None
    output_token_count: int | None
    cache_read_token_count: int | None
    cache_creation_token_count: int | None

    # Additive Issue 14a fields
    provider: str | None = None
    model_tier: str | None = None  # ModelTier value as str to avoid circular import


class ContradictionPassError(Exception):
    """Fail-closed exception for the Contradiction pass.

    Covers: no tool_use block, tool name mismatch, malformed input, provider
    exception, and schema validation failure.  No DB state is committed when
    this is raised.
    """


__all__ = [
    "ContradictionCategory",
    "ContradictionVerdict",
    "ContradictionViolation",
    "ContradictionReport",
    "ContradictionResult",
    "ContradictionPassError",
]
