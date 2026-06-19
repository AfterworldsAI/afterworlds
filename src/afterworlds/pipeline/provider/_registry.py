"""OpenRouter model-route capability registry and Safety whitelist — CRD Issue 14b.

The ``OpenRouterCapabilityRegistry`` is the single authority on whether an
OpenRouter model route is whitelisted for Safety skip and whether it is capable
of serving the core narrative passes (Writer + structured passes).

Resolution ladder (``resolve_route``):

  1. Static deny-set (pre-catalog fast-path): dynamic aliases are rejected
     immediately as ``ProviderConfigError``, matching the 14a adapter guard.
  2. Catalog lookup: fetch_catalog() is called once per registry instance
     (result is cached on first call).
  3. Catalog miss:
       - model NOT in whitelist → (UNKNOWN, None, False)
       - model IN whitelist     → (STALE, None, False)
     Both force Safety without rejecting the route.
  4. Catalog entry with is_dynamic_router=True → ``ProviderConfigError``
     (catalog-authoritative dynamic alias; defense-in-depth after step 1).
  5. Catalog entry — positive-evidence rejection:
       - ``supports_text_output is False`` → ``ProviderConfigError`` (Writer pass)
       - ``supports_tool_use is False AND supports_structured_output is False``
         → ``ProviderConfigError`` (structured passes: Planner, Extractor)
       - ``context_length is not None AND context_length < writer_context_length_floor``
         → ``ProviderConfigError`` (Writer pass context floor)
       - ``context_length=None``: unverified; does not reject — Safety runs.
  6. Catalog entry — capability evaluation:
       - ``supports_required_capabilities=True`` only when
         ``supports_text_output is True`` AND context_length is known and >= floor
         AND ``supports_tool_use is True`` (adapter constraint: the 14b
         ``OpenRouterAdapter`` uses ``tools``/``tool_choice`` only; catalog
         ``structured_outputs`` support is recorded in the profile but is not
         sufficient for Safety-skip until an adapter path exists).
       - All other cases → False (fail-safe; Safety runs, route not rejected).
  7. Whitelist lookup:
       - whitelist disabled → DISABLED
       - model in whitelist + fresh (verified_at within max_evidence_age) → WHITELISTED
       - model in whitelist + stale (verified_at older than max_evidence_age) → STALE
       - model not in whitelist → NOT_WHITELISTED

Capability and whitelist status are independent:
  - WHITELISTED + not capable → route is live but ``supports_required_capabilities``
    is False, so Safety still runs (no skip).
  - NOT_WHITELISTED + capable → Safety still runs (whitelist gate fails).
  - UNKNOWN / STALE → Safety runs regardless.

Reject only on positive evidence of incapability.  Absence/unknown drives Safety,
never route rejection.  The one exception: a known context_length below the
configured floor rejects because accepting an inadequate context window is not
fail-safe for the Writer pass.

Anthropic-direct routes always resolve WHITELISTED + capable; this is handled by
the resolver, not this registry.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from afterworlds.pipeline.provider._catalog import (
    FixtureOpenRouterCatalogProvider,
    OpenRouterCatalogModel,
    OpenRouterModelCatalogProvider,
)
from afterworlds.pipeline.provider._errors import ProviderConfigError
from afterworlds.pipeline.provider._routing import (
    CapabilityEvidenceSource,
    ModelRouteCapabilityProfile,
    SafetyWhitelistStatus,
)
from afterworlds.pipeline.provider.adapters._openrouter import _is_dynamic_alias

# Minimum context length (tokens) for the Writer pass.
# This is the default floor; operators can override via writer_context_length_floor.
# Provisional value — see ADR-014b.
_WRITER_CONTEXT_LENGTH_FLOOR = 8192


# ---------------------------------------------------------------------------
# Whitelist configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WhitelistEntry:
    """One approved model on the Safety-skip whitelist."""

    model_identifier: str
    verified_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class WhitelistConfig:
    """Set of model identifiers approved for Safety-skip on the Writer pass.

    ``enabled=False`` disables whitelist enforcement entirely; all routes get
    ``SafetyWhitelistStatus.DISABLED`` and Safety always runs.

    ``entries`` maps exact model identifiers to their ``WhitelistEntry``.
    Dynamic aliases must never appear in this set; they are caught by the
    static deny-set before reaching the whitelist lookup.
    """

    enabled: bool = True
    entries: dict[str, WhitelistEntry] = field(default_factory=dict)

    def is_whitelisted(self, model_identifier: str) -> bool:
        """Return True when the whitelist is enabled and the model has an entry."""
        return self.enabled and model_identifier in self.entries


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class OpenRouterCapabilityRegistry:
    """Registry for OpenRouter model-route capability and Safety whitelist.

    Injected into ``ProviderResolver`` to upgrade OpenRouter route construction
    from the 14a ``trusted_for_safety_skip=False`` default to full whitelist +
    capability evaluation.

    The catalog is fetched once per instance on first ``resolve_route`` call and
    cached.  Construct a new registry per process/worker startup or after a
    catalog refresh interval.

    Args:
        whitelist_config: Set of approved model identifiers.
        catalog_provider: Source of model capability data.  Defaults to an empty
            ``FixtureOpenRouterCatalogProvider`` (all misses; Safety always runs).
        max_evidence_age: Maximum age of a whitelist entry's ``verified_at`` before
            it is considered STALE.  ``None`` means entries never expire by age
            (the "no longer in catalog" branch of STALE still applies).
        clock: Callable returning the current UTC datetime.  Injected for testing.
        writer_context_length_floor: Minimum context length (tokens) for the Writer
            pass.  Routes with a known context_length below this value are rejected
            with ``ProviderConfigError``.  Defaults to ``_WRITER_CONTEXT_LENGTH_FLOOR``.
    """

    def __init__(
        self,
        whitelist_config: WhitelistConfig | None = None,
        catalog_provider: OpenRouterModelCatalogProvider | None = None,
        max_evidence_age: timedelta | None = None,
        clock: Callable[[], datetime] | None = None,
        writer_context_length_floor: int = _WRITER_CONTEXT_LENGTH_FLOOR,
    ) -> None:
        self._whitelist = whitelist_config or WhitelistConfig()
        self._catalog_provider: OpenRouterModelCatalogProvider = (
            catalog_provider or FixtureOpenRouterCatalogProvider()
        )
        self._max_evidence_age = max_evidence_age
        self._clock: Callable[[], datetime] = clock or (lambda: datetime.now(UTC))
        self._floor = writer_context_length_floor
        self._catalog_cache: dict[str, OpenRouterCatalogModel] | None = None

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def resolve_route(
        self,
        model_identifier: str,
    ) -> tuple[SafetyWhitelistStatus, ModelRouteCapabilityProfile | None, bool]:
        """Resolve whitelist status and capability for an OpenRouter model route.

        Returns:
            (whitelist_status, capability_profile, supports_required_capabilities)

        Raises:
            ProviderConfigError: if the model is a dynamic alias; lacks text output
                (supports_text_output=False); lacks both structured-pass capabilities
                (supports_tool_use=False AND supports_structured_output=False); or has
                a known context_length below the configured floor.
        """
        # Step 1: static deny-set (pre-catalog fast-path)
        if _is_dynamic_alias(model_identifier):
            raise ProviderConfigError(
                f"OpenRouterCapabilityRegistry: dynamic alias '{model_identifier}' "
                f"is not permitted as an exact model route"
            )

        # Step 2: catalog lookup (fetched once, cached)
        catalog = self._get_catalog()
        entry = catalog.get(model_identifier)

        # Step 3: catalog miss
        if entry is None:
            if self._whitelist.is_whitelisted(model_identifier):
                return SafetyWhitelistStatus.STALE, None, False
            return SafetyWhitelistStatus.UNKNOWN, None, False

        # Step 4: catalog-driven dynamic alias (defense-in-depth)
        if entry.is_dynamic_router:
            raise ProviderConfigError(
                f"OpenRouterCapabilityRegistry: catalog marks '{model_identifier}' "
                f"as a dynamic router alias — rejected"
            )

        # Step 5: positive-evidence rejection
        # Reject only when capability is explicitly False — None/unknown fails safe.
        if entry.supports_text_output is False:
            raise ProviderConfigError(
                f"OpenRouterCapabilityRegistry: model '{model_identifier}' "
                f"does not support text output — cannot serve Writer pass"
            )
        if (
            entry.supports_tool_use is False
            and entry.supports_structured_output is False
        ):
            raise ProviderConfigError(
                f"OpenRouterCapabilityRegistry: model '{model_identifier}' "
                f"lacks both structured-pass capabilities (tool_use=False, "
                f"structured_output=False) — cannot serve Planner/Extractor passes"
            )
        if entry.context_length is not None and entry.context_length < self._floor:
            raise ProviderConfigError(
                f"OpenRouterCapabilityRegistry: model '{model_identifier}' "
                f"context length {entry.context_length} is below the Writer floor "
                f"of {self._floor} tokens"
            )

        # Step 6: capability evaluation (fail-safe: unknown → False)
        # Adapter constraint: OpenRouterAdapter uses tools/tool_choice only.
        # Catalog structured_outputs is recorded in the profile but is not
        # sufficient for Safety-skip until an adapter path exists.
        supports_required = (
            entry.supports_text_output is True
            and entry.context_length is not None
            and entry.context_length >= self._floor
            and entry.supports_tool_use is True
        )

        # Step 7: whitelist lookup (with time-based staleness check)
        whitelist_status: SafetyWhitelistStatus
        if not self._whitelist.enabled:
            whitelist_status = SafetyWhitelistStatus.DISABLED
        elif model_identifier in self._whitelist.entries:
            wl_entry = self._whitelist.entries[model_identifier]
            if (
                self._max_evidence_age is not None
                and self._clock() - wl_entry.verified_at > self._max_evidence_age
            ):
                whitelist_status = SafetyWhitelistStatus.STALE
            else:
                whitelist_status = SafetyWhitelistStatus.WHITELISTED
        else:
            whitelist_status = SafetyWhitelistStatus.NOT_WHITELISTED

        profile = ModelRouteCapabilityProfile(
            model_identifier=model_identifier,
            supports_text_output=entry.supports_text_output,
            supports_tool_use=entry.supports_tool_use,
            supports_structured_output=entry.supports_structured_output,
            context_length=entry.context_length,
            evidence_source=CapabilityEvidenceSource.OPENROUTER_MODELS_API,
            is_dynamic_router=False,
            catalog_seen_at=entry.fetched_at,
        )
        return whitelist_status, profile, supports_required

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _get_catalog(self) -> dict[str, OpenRouterCatalogModel]:
        if self._catalog_cache is None:
            entries: Sequence[OpenRouterCatalogModel] = (
                self._catalog_provider.fetch_catalog()
            )
            self._catalog_cache = {e.id: e for e in entries}
        return self._catalog_cache


# ---------------------------------------------------------------------------
# Anthropic-direct capability profile (AFTERWORLDS_VERIFIED)
# ---------------------------------------------------------------------------


def make_anthropic_capability_profile(
    model_identifier: str,
) -> ModelRouteCapabilityProfile:
    """Build the AFTERWORLDS_VERIFIED capability profile for an Anthropic-direct model.

    Anthropic-direct routes are always trusted — this is the profile that encodes
    that trust.  Context length 200_000 reflects Claude's maximum window.
    """
    return ModelRouteCapabilityProfile(
        model_identifier=model_identifier,
        supports_text_output=True,
        supports_tool_use=True,
        supports_structured_output=True,
        context_length=200_000,
        evidence_source=CapabilityEvidenceSource.AFTERWORLDS_VERIFIED,
        is_dynamic_router=False,
        verified_at=datetime.now(UTC),
    )


__all__ = [
    "OpenRouterCapabilityRegistry",
    "WhitelistConfig",
    "WhitelistEntry",
    "_WRITER_CONTEXT_LENGTH_FLOOR",
    "make_anthropic_capability_profile",
]
