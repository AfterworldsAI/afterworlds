"""Turn provider binding, safety policy context, and conservative safety policy.

CRD Issue 14a/14b.  These types encode which provider surfaces are eligible for a
given turn and whether the Safety envelope may be skipped.

14b supersedes the 14a ``EligibleWriterRoute`` with ``EligibleModelRoute``.  The
safety-skip predicate is upgraded from a single ``trusted_for_safety_skip`` bool to
whitelist-status + capability evaluation.
"""

from __future__ import annotations

import enum
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.pipeline.writer.models import WriterResult


def _noop() -> None:
    pass


# ---------------------------------------------------------------------------
# Capability evidence source
# ---------------------------------------------------------------------------


class CapabilityEvidenceSource(enum.StrEnum):
    """Origin of a ``ModelRouteCapabilityProfile``.

    MANUAL_FIXTURE: hand-authored entry in a static fixture file.
    OPENROUTER_MODELS_API: sourced from the live OpenRouter /models endpoint.
    AFTERWORLDS_VERIFIED: Afterworlds-owned profile for a known-good route
        (e.g. Anthropic-direct).  Implicitly WHITELISTED.
    TEST_FIXTURE: in-memory entry constructed only in tests.
    """

    MANUAL_FIXTURE = "manual_fixture"
    OPENROUTER_MODELS_API = "openrouter_models_api"
    AFTERWORLDS_VERIFIED = "afterworlds_verified"
    TEST_FIXTURE = "test_fixture"


# ---------------------------------------------------------------------------
# Safety whitelist status
# ---------------------------------------------------------------------------


class SafetyWhitelistStatus(enum.StrEnum):
    """Whitelist resolution outcome for a model route.

    WHITELISTED: model id is on the explicit Safety-skip whitelist.
    NOT_WHITELISTED: model id is present in the catalog but not on the whitelist.
    UNKNOWN: model id was not found in the catalog (catalog miss).
    DISABLED: whitelist enforcement is administratively disabled.
    STALE: model was on the whitelist but is no longer seen in the catalog.

    Both UNKNOWN and STALE force Safety (identical to a catalog miss).
    """

    WHITELISTED = "whitelisted"
    NOT_WHITELISTED = "not_whitelisted"
    UNKNOWN = "unknown"
    DISABLED = "disabled"
    STALE = "stale"


# ---------------------------------------------------------------------------
# Model-route capability profile
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelRouteCapabilityProfile:
    """Capability facts for one exact-model-route, from catalog or fixture.

    All three supports_* fields use tri-state (True / False / None):
      - True:  provider catalog confirms support.
      - False: provider catalog confirms no support; route may be rejected.
      - None:  support status unknown (fail-safe: do not reject; Safety runs).

    ``context_length=None`` means unverified; route is not rejected but
    ``supports_required_capabilities`` is set False on the parent route.

    ``is_dynamic_router=True`` means this entry describes a routing alias, not
    a leaf model.  The registry rejects such entries at route construction.
    """

    model_identifier: str
    supports_text_output: bool | None
    supports_tool_use: bool | None
    supports_structured_output: bool | None
    context_length: int | None
    evidence_source: CapabilityEvidenceSource
    is_dynamic_router: bool = False
    verified_at: datetime | None = None
    catalog_seen_at: datetime | None = None


# ---------------------------------------------------------------------------
# Eligible model route (replaces 14a EligibleWriterRoute)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EligibleModelRoute:
    """One candidate route that could serve the Writer pass for a given turn.

    Supersedes the 14a ``EligibleWriterRoute``.  Safety-skip eligibility is now
    determined by ``whitelist_status`` and ``supports_required_capabilities``
    rather than a single ``trusted_for_safety_skip`` bool.

    ``whitelist_status`` is WHITELISTED only when the model id appears on the
    explicit Safety-skip whitelist.  Anthropic-direct routes are always WHITELISTED
    via the AFTERWORLDS_VERIFIED profile (AC 15/18).

    ``supports_required_capabilities`` is True only when the catalog positively
    confirms the route can serve the Writer pass (``supports_text_output=True`` AND
    context_length known and above the minimum floor).  Catalog miss, None fields,
    and context_length=None all collapse to False (fail-safe; Safety runs).

    ``capability_profile`` is None for catalog misses; populated when a profile
    was found in the catalog or fixture.
    """

    provider_name: str
    model_identifier: str
    whitelist_status: SafetyWhitelistStatus
    supports_required_capabilities: bool
    capability_profile: ModelRouteCapabilityProfile | None = None


# ---------------------------------------------------------------------------
# Turn-scoped binding
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TurnProviderBinding:
    """Result of ``ProviderResolver.resolve_for_turn`` — valid for one turn.

    ``adapter`` is the (possibly fallback-wrapped) adapter that all pass calls
    for this turn must use.  ``eligible_writer_routes`` is the full set
    (primary + fallback) that feeds the safety-skip predicate.
    """

    adapter: object  # ProviderAdapter — typed as object to avoid circular import
    primary_writer_route: EligibleModelRoute
    eligible_writer_routes: tuple[EligibleModelRoute, ...]
    access_path: RuntimeAccessPath
    pre_transaction_fn: Callable[[], None] = field(default=_noop)
    post_transaction_fn: Callable[[], None] = field(default=_noop)


# ---------------------------------------------------------------------------
# Safety policy context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SafetyPolicyContext:
    """Context object passed to ``CapabilityProfileAwareSafetyPolicy`` methods.

    Replaces the 12c ``should_run_*(..., writer_provider: str, ...)`` signature.
    This is the one non-additive 12c contract change introduced in Issue 14a and
    extended in 14b.

    ``writer_result`` is None for input-preflight decisions; populated for
    output-audit decisions.
    """

    eligible_writer_routes: tuple[EligibleModelRoute, ...]
    request_risk_signal: bool
    access_path: RuntimeAccessPath
    writer_result: WriterResult | None = field(default=None)


# ---------------------------------------------------------------------------
# Conservative safety policy — upgraded in 14b to whitelist + capability eval
# ---------------------------------------------------------------------------


class CapabilityProfileAwareSafetyPolicy:
    """Issue 14b upgrade: Safety-skip requires WHITELISTED + capable on every route.

    Rule: Safety may be skipped only when EVERY eligible Writer route is
    explicitly WHITELISTED AND confirms it supports the required capabilities,
    AND there is no risk signal.  An empty eligible set forces Safety.

    Consequences (14b):
      - Anthropic-direct only       → WHITELISTED + capable → may skip
      - Anthropic + OR fallback     → OR route NOT_WHITELISTED or UNKNOWN → Safety runs
      - BYOK OR WHITELISTED+capable → may skip
      - BYOK OR UNKNOWN (miss)      → Safety runs
      - Any risk signal             → Safety runs
    """

    def _can_skip(self, ctx: SafetyPolicyContext) -> bool:
        if ctx.request_risk_signal or not ctx.eligible_writer_routes:
            return False
        return all(
            r.whitelist_status is SafetyWhitelistStatus.WHITELISTED
            and r.supports_required_capabilities
            for r in ctx.eligible_writer_routes
        )

    def should_run_input_preflight(self, ctx: SafetyPolicyContext) -> bool:
        return not self._can_skip(ctx)

    def should_run_output_audit(self, ctx: SafetyPolicyContext) -> bool:
        return not self._can_skip(ctx)


__all__ = [
    "CapabilityEvidenceSource",
    "CapabilityProfileAwareSafetyPolicy",
    "EligibleModelRoute",
    "ModelRouteCapabilityProfile",
    "SafetyPolicyContext",
    "SafetyWhitelistStatus",
    "TurnProviderBinding",
]
