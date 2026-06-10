"""Cross-pass provider-refusal contract — CRD Issue 12c / 14a.

A provider refusal from one of the narrative or state passes (Planner,
Writer, Extractor, Contradiction) is a typed failure, not a Safety verdict.
This module defines the shared types so the orchestrator can catch by
exception class and surface refusal metadata in ``OrchestrationResult``.

Safety pass provider refusals remain ``SafetyPassError`` (Issue 12b) and
route to ``PIPELINE_ERROR`` per the 12c failure taxonomy.  They are NOT
``ProviderRefusalError``.

Issue 14a adds ``RefusalCategory`` enum and ``ProviderRefusal.refusal_category``
field (additive, optional).  Adapters set this when raising ``ProviderRefusalError``.
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


class RefusalCategory(StrEnum):
    """Classification of why a provider refused a request (Issue 14a).

    Used by adapters when raising ``ProviderRefusalError`` and stored in
    ``provider_refusal_log``.

    CONTENT_POLICY: explicit content-policy refusal message from the provider.
    UNKNOWN: policy-style refusal without a granular reason — still
        fallback-eligible per Design v11 (fallback must not depend on
        granular reasons).

    Operational failures (context length, auth, rate limit, network, empty
    response, timeout) are ``ProviderCallError``, never a ``RefusalCategory``.
    """

    CONTENT_POLICY = "content_policy"
    UNKNOWN = "unknown"


class ProviderRefusal(BaseModel):
    """Advisory metadata about a typed provider refusal.

    Fields are advisory.  The orchestrator must never treat ``coarse_reason``
    or ``refusal_category`` as authoritative policy signal.  Issue 14a adapters
    populate ``refusal_category``; fallback routing uses it but never depends
    on granular reasons.

    Attributes:
        provider: provider identifier reported by the pass that refused
            (e.g. ``"anthropic"``).
        model: model identifier reported by the pass (e.g. ``"claude-haiku-..."``).
        pass_identifier: which pass produced the refusal.
        coarse_reason: any short refusal phrase the provider supplied; may
            be ``None`` when the provider did not surface a reason.
        raw_response_excerpt: short in-memory-only excerpt (max 1024 chars)
            for audit context.  NEVER persisted, NEVER emitted to logs by
            default — DEBUG behind explicit opt-in, sanitized before any
            emission.
        refusal_category: Issue 14a additive field; ``None`` on 12c-era refusals.
    """

    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str | None = None
    pass_identifier: PassIdentifier
    coarse_reason: str | None = None
    raw_response_excerpt: str | None = Field(default=None, max_length=1024)
    refusal_category: RefusalCategory | None = None


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
    "RefusalCategory",
    "ProviderRefusal",
    "ProviderRefusalError",
]
