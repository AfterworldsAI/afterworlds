"""Safety pass data models — CRD Issue 12b."""

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
    """Token usage metrics from the safety provider call."""

    model_config = ConfigDict(extra="forbid")

    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_input_tokens: int | None = None
    cache_creation_input_tokens: int | None = None


class SafetyResult(BaseModel):
    """Typed result returned by SafetyService.check()."""

    model_config = ConfigDict(extra="forbid")

    report: SafetyReport
    target: SafetyTarget
    usage: TokenUsage | None = None

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
