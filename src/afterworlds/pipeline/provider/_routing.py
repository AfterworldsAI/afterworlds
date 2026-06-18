"""Turn provider binding, safety policy context, and conservative safety policy.

CRD Issue 14a.  These types encode which provider surfaces are eligible for a
given turn and whether the Safety envelope may be skipped.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.pipeline.writer.models import WriterResult


def _noop() -> None:
    pass


# ---------------------------------------------------------------------------
# Eligible Writer route
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EligibleWriterRoute:
    """One candidate route that could serve the Writer pass for a given turn.

    ``trusted_for_safety_skip`` is True ONLY for Anthropic-direct routes in
    14a.  OpenRouter routes are always False.  14b will upgrade this predicate
    to whitelist evaluation without changing this dataclass shape.
    """

    provider_name: str
    model_identifier: str
    is_openrouter: bool
    trusted_for_safety_skip: bool


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
    primary_writer_route: EligibleWriterRoute
    eligible_writer_routes: tuple[EligibleWriterRoute, ...]
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
    This is the one non-additive 12c contract change in Issue 14a.

    ``writer_result`` is None for input-preflight decisions; populated for
    output-audit decisions.
    """

    eligible_writer_routes: tuple[EligibleWriterRoute, ...]
    request_risk_signal: bool
    access_path: RuntimeAccessPath
    writer_result: WriterResult | None = field(default=None)


# ---------------------------------------------------------------------------
# Conservative safety policy (replaces 12c SafetyPolicy)
# ---------------------------------------------------------------------------


class CapabilityProfileAwareSafetyPolicy:
    """Issue 14a replacement for the Issue 12c ``SafetyPolicy``.

    Rule: Safety may be skipped only when EVERY eligible Writer route — primary
    AND fallback — is a trusted Anthropic-direct route AND there is no risk
    signal.  An empty eligible set forces Safety.

    Consequences:
      - Hosted Anthropic-only → may skip
      - Hosted Anthropic + OpenRouter fallback → runs Safety (fallback is OR)
      - BYOK OpenRouter → runs Safety
      - BYOK Anthropic-only → may skip

    The "every eligible route" rule prevents the fallback from becoming a tunnel
    around Safety.  14b upgrades ``_can_skip`` to whitelist evaluation without
    changing this class shape.
    """

    def _can_skip(self, ctx: SafetyPolicyContext) -> bool:
        if ctx.request_risk_signal or not ctx.eligible_writer_routes:
            return False
        return all(r.trusted_for_safety_skip for r in ctx.eligible_writer_routes)

    def should_run_input_preflight(self, ctx: SafetyPolicyContext) -> bool:
        return not self._can_skip(ctx)

    def should_run_output_audit(self, ctx: SafetyPolicyContext) -> bool:
        return not self._can_skip(ctx)


__all__ = [
    "EligibleWriterRoute",
    "TurnProviderBinding",
    "SafetyPolicyContext",
    "CapabilityProfileAwareSafetyPolicy",
]
