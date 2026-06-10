"""Safety pass data models — CRD Issue 12b / 14a.

Issue 14a changes:
  - ``SafetyResult`` token fields normalized to flat ``*_token_count: int | None``
    (aligning with PlannerResult, WriterResult, ExtractorResult,
    ContradictionResult — all five pass results now use the same shape).
  - ``SafetyResult`` gains additive provider/model_identifier/model_tier fields.
  - ``TokenUsage`` is kept as an exported symbol for import compatibility
    but is no longer used by ``SafetyResult``.

Architecture Note: the spec states all five pass results "already carry"
flat token_count fields.  ``SafetyResult`` used ``TokenUsage`` (12b) with
differently-named fields.  Normalized here to unify the settlement path in
``entitlement/policy.py``'s ``_safety_snapshot``.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, computed_field, field_validator


class SafetyTarget(StrEnum):
    """Which text the safety pass is evaluating."""

    INPUT = "input"
    OUTPUT = "output"


class SafetyVerdict(StrEnum):
    """Computed safety decision derived from the concerns list."""

    ALLOW = "allow"
    BLOCK = "block"


class SafetyCategory(StrEnum):
    """Categories of safety concern the model can flag."""

    SEXUAL_MINOR = "SEXUAL_MINOR"
    REAL_PERSON_TARGETED_HARM = "REAL_PERSON_TARGETED_HARM"
    HATE_TARGETED = "HATE_TARGETED"
    SELF_HARM_INSTRUCTIONAL = "SELF_HARM_INSTRUCTIONAL"
    DANGEROUS_OPERATIONAL = "DANGEROUS_OPERATIONAL"
    OTHER = "OTHER"


class SafetyConcern(BaseModel):
    """A single flagged safety concern."""

    model_config = ConfigDict(extra="forbid")

    category: SafetyCategory
    description: str
    evidence_summary: str

    @field_validator("evidence_summary")
    @classmethod
    def _evidence_summary_max_300(cls, v: str) -> str:
        if len(v) > 300:
            raise ValueError(f"evidence_summary must be ≤ 300 characters; got {len(v)}")
        return v


class SafetyReport(BaseModel):
    """Parsed output from the safety model call."""

    model_config = ConfigDict(extra="forbid")

    concerns: list[SafetyConcern]


class TokenUsage(BaseModel):
    """Deprecated: use flat token_count fields on SafetyResult instead.

    Kept for import compatibility.  No longer used by SafetyResult (Issue 14a).
    """

    model_config = ConfigDict(extra="forbid")

    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_input_tokens: int | None = None
    cache_creation_input_tokens: int | None = None


class SafetyResult(BaseModel):
    """Typed result returned by SafetyService.check().

    Token counts use the same flat ``*_token_count: int | None`` shape as the
    other four pass results (Issue 14a normalization; see module docstring).
    Provider/model/tier fields are additive (default None).
    """

    model_config = ConfigDict(extra="forbid")

    report: SafetyReport
    target: SafetyTarget

    # Flat token count fields (aligned with Issue 9-12 pass result shape)
    input_token_count: int | None = None
    output_token_count: int | None = None
    cache_read_token_count: int | None = None
    cache_creation_token_count: int | None = None

    # Additive Issue 14a fields
    provider: str | None = None
    model_identifier: str | None = None
    model_tier: str | None = None  # ModelTier value as str to avoid circular import

    @computed_field  # type: ignore[prop-decorator]
    @property
    def verdict(self) -> SafetyVerdict:
        """Derived verdict: BLOCK if any concerns, ALLOW if none."""
        return SafetyVerdict.BLOCK if self.report.concerns else SafetyVerdict.ALLOW


class SafetyPassError(Exception):
    """Raised on any safety pass failure — fail-closed, never silent ALLOW."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause
