"""Typed payloads and exceptions for the Planner pass — CRD Issue 12a."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class PlannerOutput(BaseModel):
    """Structured output returned by the Planner pass model.

    Extra fields are forbidden so that schema drift is caught immediately
    rather than silently ignored.
    """

    model_config = ConfigDict(extra="forbid")

    scene_goal: str
    next_beat: str
    facts_needed: list[str]
    notes: str | None = None

    @field_validator("scene_goal", "next_beat")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must be a non-empty string after stripping whitespace")
        return v

    @field_validator("facts_needed")
    @classmethod
    def _facts_non_empty(cls, v: list[str]) -> list[str]:
        for i, fact in enumerate(v):
            if not fact or not fact.strip():
                raise ValueError(
                    f"facts_needed[{i}] must be a non-empty string after stripping"
                    " whitespace"
                )
        return v

    @field_validator("notes")
    @classmethod
    def _notes_non_empty_if_present(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError(
                "notes must be None (absent) or a non-empty string after stripping"
                " whitespace; use None to signal no notes rather than an empty string"
            )
        return v


class PlannerResult(BaseModel):
    """Complete result returned by PlannerService.plan()."""

    plan: PlannerOutput
    model_identifier: str
    latency_ms: int
    input_token_count: int | None
    output_token_count: int | None
    cache_read_token_count: int | None
    cache_creation_token_count: int | None


class PlannerPassError(Exception):
    """Fail-closed exception for the Planner pass.

    Covers: no tool_use block, tool name mismatch, malformed input, provider
    exception, and schema validation failure.  No DB state is committed when
    this is raised.
    """


__all__ = [
    "PlannerOutput",
    "PlannerResult",
    "PlannerPassError",
]
