"""Cross-pass provider-refusal contract — CRD Issue 12c.

A provider refusal from one of the narrative or state passes (Planner,
Writer, Extractor, Contradiction) is a typed failure, not a Safety verdict.
This module defines the shared types so the orchestrator can catch by
exception class and surface refusal metadata in ``OrchestrationResult``.

Safety pass provider refusals remain ``SafetyPassError`` (Issue 12b) and
route to ``PIPELINE_ERROR`` per the 12c failure taxonomy.  They are NOT
``ProviderRefusalError``.

v1 scope notes (Issue 12c):
  - Pass services do not synthesize ``ProviderRefusalError`` from coarse
    provider exceptions in v1.  Automatic refusal-classification heuristics
    belong to Issue 14 (provider routing).
  - Test callers raise ``ProviderRefusalError`` directly to exercise the
    refusal path; pass services let it propagate unchanged from their
    except branches.
  - The carried ``ProviderRefusal`` is advisory — orchestration does not
    route on it; Issue 14 may use it later for refusal-aware fallback.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PassIdentifier(StrEnum):
    """Identifier for which provider-backed pass produced a refusal."""

    PLANNER = "planner"
    WRITER = "writer"
    EXTRACTOR = "extractor"
    CONTRADICTION = "contradiction"


class ProviderRefusal(BaseModel):
    """Advisory metadata about a typed provider refusal.

    Fields are advisory.  Per Known Unknown "Provider refusal reason
    opacity" (resolved in Issue 12c), the orchestrator must never treat
    ``coarse_reason`` as authoritative policy signal.  Issue 14 may improve
    routing based on observed refusal patterns but routing must not depend
    on granular refusal reasons being available.

    Attributes:
        provider: provider identifier reported by the pass that refused
            (e.g. ``"anthropic"``).
        model: model identifier reported by the pass (e.g. ``"claude-haiku-..."``).
        pass_identifier: which pass produced the refusal.
        coarse_reason: any short refusal phrase the provider supplied; may
            be ``None`` when the provider did not surface a reason.  Treated
            as advisory only — the v1 orchestrator does not route on it.
        raw_response_excerpt: short excerpt of the underlying provider
            response sufficient for audit (truncated by the caller; the
            orchestrator does not re-truncate).
    """

    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str | None = None
    pass_identifier: PassIdentifier
    coarse_reason: str | None = None
    raw_response_excerpt: str | None = Field(default=None, max_length=1024)


class ProviderRefusalError(Exception):
    """Raised by a narrative / state pass when the provider refuses the call.

    Distinct from each pass's ``*PassError`` operational-failure class.
    Pass services must let ``ProviderRefusalError`` propagate from their
    error-handling branches (do not wrap into the pass-specific exception).
    The orchestrator catches this by class and routes the turn to
    ``REFUSED_BY_PROVIDER`` after rolling back the outer transaction if one
    is open.

    Attributes:
        refusal: typed ``ProviderRefusal`` metadata.
    """

    def __init__(self, refusal: ProviderRefusal) -> None:
        super().__init__(
            f"Provider {refusal.provider} refused "
            f"{refusal.pass_identifier.value} pass"
            + (f": {refusal.coarse_reason}" if refusal.coarse_reason else "")
        )
        self.refusal = refusal


__all__ = [
    "PassIdentifier",
    "ProviderRefusal",
    "ProviderRefusalError",
]
