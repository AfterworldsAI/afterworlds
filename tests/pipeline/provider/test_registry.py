"""Tests for OpenRouterCapabilityRegistry (CRD Issue 14b).

Coverage targets:
  - Resolution ladder: static deny-set, catalog miss, dynamic alias entry,
    positive-evidence rejection, capability evaluation, whitelist lookup.
  - UNKNOWN / STALE / WHITELISTED / NOT_WHITELISTED / DISABLED paths.
  - Fail-safe cases: text_output=None, context_length=None, below-floor.
  - _can_skip interaction: DISABLED + capable must NOT skip Safety.
  - Catalog caching: fetch_catalog called only once per registry instance.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.pipeline.provider._catalog import (
    FixtureOpenRouterCatalogProvider,
    OpenRouterCatalogModel,
)
from afterworlds.pipeline.provider._errors import ProviderConfigError
from afterworlds.pipeline.provider._registry import (
    _WRITER_CONTEXT_LENGTH_FLOOR,
    OpenRouterCapabilityRegistry,
    WhitelistConfig,
    WhitelistEntry,
)
from afterworlds.pipeline.provider._routing import (
    CapabilityEvidenceSource,
    CapabilityProfileAwareSafetyPolicy,
    EligibleModelRoute,
    SafetyPolicyContext,
    SafetyWhitelistStatus,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 6, 1, tzinfo=UTC)
_MODEL = "anthropic/claude-opus-4"
_MODEL_2 = "mistralai/mistral-7b-instruct"


def _catalog_entry(
    model_id: str = _MODEL,
    *,
    supports_text_output: bool | None = True,
    supports_tool_use: bool | None = True,
    supports_structured_output: bool | None = True,
    context_length: int | None = 200_000,
    is_dynamic_router: bool = False,
) -> OpenRouterCatalogModel:
    return OpenRouterCatalogModel(
        id=model_id,
        name=model_id,
        context_length=context_length,
        supports_text_output=supports_text_output,
        supports_tool_use=supports_tool_use,
        supports_structured_output=supports_structured_output,
        is_dynamic_router=is_dynamic_router,
        fetched_at=_NOW,
    )


def _whitelist(*model_ids: str) -> WhitelistConfig:
    return WhitelistConfig(
        enabled=True,
        entries={
            mid: WhitelistEntry(model_identifier=mid, approved_at=_NOW)
            for mid in model_ids
        },
    )


def _make_registry(
    entries: list[OpenRouterCatalogModel] | None = None,
    whitelist: WhitelistConfig | None = None,
) -> OpenRouterCapabilityRegistry:
    provider = FixtureOpenRouterCatalogProvider(entries or [])
    return OpenRouterCapabilityRegistry(
        whitelist_config=whitelist,
        catalog_provider=provider,
    )


def _eligible_route(
    whitelist_status: SafetyWhitelistStatus,
    capable: bool,
) -> EligibleModelRoute:
    return EligibleModelRoute(
        provider_name="openrouter",
        model_identifier=_MODEL,
        whitelist_status=whitelist_status,
        supports_required_capabilities=capable,
    )


def _ctx(*routes: EligibleModelRoute) -> SafetyPolicyContext:
    return SafetyPolicyContext(
        eligible_writer_routes=tuple(routes),
        request_risk_signal=False,
        access_path=RuntimeAccessPath.HOSTED,
    )


_policy = CapabilityProfileAwareSafetyPolicy()


# ---------------------------------------------------------------------------
# Step 1: static deny-set (dynamic alias rejected pre-catalog)
# ---------------------------------------------------------------------------


def test_dynamic_alias_rejected_before_catalog_lookup() -> None:
    """Dynamic alias raises ProviderConfigError without hitting the catalog."""
    # "openrouter/auto" is the canonical dynamic alias
    registry = _make_registry(
        entries=[_catalog_entry("openrouter/auto")],
    )
    with pytest.raises(ProviderConfigError, match="dynamic alias"):
        registry.resolve_route("openrouter/auto")


# ---------------------------------------------------------------------------
# Step 3: catalog miss
# ---------------------------------------------------------------------------


def test_catalog_miss_not_whitelisted_returns_unknown() -> None:
    """Catalog miss + not whitelisted → (UNKNOWN, None, False), no raise."""
    registry = _make_registry()  # empty catalog, no whitelist entries
    status, profile, capable = registry.resolve_route(_MODEL)
    assert status is SafetyWhitelistStatus.UNKNOWN
    assert profile is None
    assert capable is False


def test_catalog_miss_whitelisted_returns_stale() -> None:
    """Catalog miss + whitelisted → (STALE, None, False), no raise."""
    registry = _make_registry(whitelist=_whitelist(_MODEL))
    status, profile, capable = registry.resolve_route(_MODEL)
    assert status is SafetyWhitelistStatus.STALE
    assert profile is None
    assert capable is False


# ---------------------------------------------------------------------------
# Step 4: catalog-driven dynamic alias (defense-in-depth)
# ---------------------------------------------------------------------------


def test_catalog_entry_with_is_dynamic_router_raises() -> None:
    """Catalog entry marked is_dynamic_router=True raises ProviderConfigError."""
    entry = _catalog_entry(_MODEL, is_dynamic_router=True)
    registry = _make_registry(entries=[entry])
    with pytest.raises(ProviderConfigError, match="dynamic router alias"):
        registry.resolve_route(_MODEL)


# ---------------------------------------------------------------------------
# Step 5: positive-evidence rejection (text output explicitly False)
# ---------------------------------------------------------------------------


def test_text_output_false_raises() -> None:
    """supports_text_output=False → ProviderConfigError; route rejected."""
    entry = _catalog_entry(_MODEL, supports_text_output=False)
    registry = _make_registry(entries=[entry])
    with pytest.raises(ProviderConfigError, match="text output"):
        registry.resolve_route(_MODEL)


def test_text_output_none_does_not_raise() -> None:
    """supports_text_output=None → fail-safe; route not rejected."""
    entry = _catalog_entry(_MODEL, supports_text_output=None, context_length=200_000)
    registry = _make_registry(entries=[entry], whitelist=_whitelist(_MODEL))
    status, profile, capable = registry.resolve_route(_MODEL)
    assert capable is False  # unknown text_output → can't confirm capability
    assert profile is not None
    assert profile.supports_text_output is None


# ---------------------------------------------------------------------------
# Step 5 (context_length): below-floor is NOT a rejection
# ---------------------------------------------------------------------------


def test_context_length_below_floor_does_not_raise() -> None:
    """context_length below floor sets capable=False but does not reject route."""
    below_floor = _WRITER_CONTEXT_LENGTH_FLOOR - 1
    entry = _catalog_entry(_MODEL, context_length=below_floor)
    registry = _make_registry(entries=[entry], whitelist=_whitelist(_MODEL))
    status, profile, capable = registry.resolve_route(_MODEL)
    assert capable is False
    assert status is SafetyWhitelistStatus.WHITELISTED
    assert profile is not None
    assert profile.context_length == below_floor


def test_context_length_none_does_not_raise() -> None:
    """context_length=None → unverified; route not rejected, capable=False."""
    entry = _catalog_entry(_MODEL, context_length=None)
    registry = _make_registry(entries=[entry], whitelist=_whitelist(_MODEL))
    status, profile, capable = registry.resolve_route(_MODEL)
    assert capable is False
    assert profile is not None
    assert profile.context_length is None


# ---------------------------------------------------------------------------
# Step 6: capability evaluation (full positive confirmation → capable)
# ---------------------------------------------------------------------------


def test_capable_whitelisted_route() -> None:
    """text_output=True + context_length >= floor + whitelisted → capable."""
    entry = _catalog_entry(_MODEL)
    registry = _make_registry(entries=[entry], whitelist=_whitelist(_MODEL))
    status, profile, capable = registry.resolve_route(_MODEL)
    assert status is SafetyWhitelistStatus.WHITELISTED
    assert capable is True
    assert profile is not None
    assert profile.evidence_source is CapabilityEvidenceSource.OPENROUTER_MODELS_API


def test_capable_not_whitelisted_route() -> None:
    """Capable route not on whitelist → (NOT_WHITELISTED, profile, True)."""
    entry = _catalog_entry(_MODEL)
    registry = _make_registry(entries=[entry])  # no whitelist entries
    status, profile, capable = registry.resolve_route(_MODEL)
    assert status is SafetyWhitelistStatus.NOT_WHITELISTED
    assert capable is True
    assert profile is not None


def test_capability_floor_boundary_exactly_at_floor() -> None:
    """context_length exactly == floor → capable=True."""
    entry = _catalog_entry(_MODEL, context_length=_WRITER_CONTEXT_LENGTH_FLOOR)
    registry = _make_registry(entries=[entry], whitelist=_whitelist(_MODEL))
    _, _, capable = registry.resolve_route(_MODEL)
    assert capable is True


def test_profile_catalog_seen_at_is_set() -> None:
    """capability_profile.catalog_seen_at reflects the catalog entry's fetched_at."""
    entry = _catalog_entry(_MODEL)
    registry = _make_registry(entries=[entry])
    _, profile, _ = registry.resolve_route(_MODEL)
    assert profile is not None
    assert profile.catalog_seen_at == _NOW


# ---------------------------------------------------------------------------
# Step 7: whitelist disabled → DISABLED
# ---------------------------------------------------------------------------


def test_whitelist_disabled_returns_disabled_status() -> None:
    """WhitelistConfig(enabled=False) → DISABLED, capable evaluated normally."""
    disabled_wl = WhitelistConfig(enabled=False)
    entry = _catalog_entry(_MODEL)
    registry = _make_registry(entries=[entry], whitelist=disabled_wl)
    status, profile, capable = registry.resolve_route(_MODEL)
    assert status is SafetyWhitelistStatus.DISABLED
    assert capable is True  # model is capable even though whitelist is disabled


def test_disabled_whitelist_capable_route_cannot_skip_safety() -> None:
    """DISABLED + capable → _can_skip returns False (DISABLED ≠ WHITELISTED)."""
    route = _eligible_route(SafetyWhitelistStatus.DISABLED, capable=True)
    assert _policy._can_skip(_ctx(route)) is False


# ---------------------------------------------------------------------------
# _can_skip integration (whitelist + capability both required)
# ---------------------------------------------------------------------------


def test_can_skip_requires_whitelisted_and_capable() -> None:
    """_can_skip is True only when every route is WHITELISTED + capable."""
    whitelisted_capable = _eligible_route(SafetyWhitelistStatus.WHITELISTED, True)
    assert _policy._can_skip(_ctx(whitelisted_capable)) is True


def test_can_skip_false_when_not_whitelisted() -> None:
    not_wl = _eligible_route(SafetyWhitelistStatus.NOT_WHITELISTED, True)
    assert _policy._can_skip(_ctx(not_wl)) is False


def test_can_skip_false_when_unknown() -> None:
    unknown = _eligible_route(SafetyWhitelistStatus.UNKNOWN, False)
    assert _policy._can_skip(_ctx(unknown)) is False


def test_can_skip_false_when_stale() -> None:
    stale = _eligible_route(SafetyWhitelistStatus.STALE, False)
    assert _policy._can_skip(_ctx(stale)) is False


def test_can_skip_false_when_whitelisted_but_not_capable() -> None:
    wl_not_capable = _eligible_route(SafetyWhitelistStatus.WHITELISTED, False)
    assert _policy._can_skip(_ctx(wl_not_capable)) is False


def test_can_skip_false_when_one_route_not_whitelisted() -> None:
    """Mixed eligible set: one WHITELISTED, one NOT_WHITELISTED → Safety runs."""
    primary = _eligible_route(SafetyWhitelistStatus.WHITELISTED, True)
    fallback = EligibleModelRoute(
        provider_name="openrouter",
        model_identifier=_MODEL_2,
        whitelist_status=SafetyWhitelistStatus.NOT_WHITELISTED,
        supports_required_capabilities=True,
    )
    assert _policy._can_skip(_ctx(primary, fallback)) is False


# ---------------------------------------------------------------------------
# Catalog caching: fetch_catalog called only once
# ---------------------------------------------------------------------------


class _CountingCatalogProvider:
    """Catalog provider that counts fetch_catalog calls."""

    def __init__(self, entries: list[OpenRouterCatalogModel]) -> None:
        self._entries = entries
        self.call_count = 0

    def fetch_catalog(self) -> list[OpenRouterCatalogModel]:
        self.call_count += 1
        return self._entries


def test_catalog_fetched_only_once() -> None:
    """Catalog is cached after the first resolve_route call."""
    counter = _CountingCatalogProvider([_catalog_entry(_MODEL)])
    registry = OpenRouterCapabilityRegistry(
        whitelist_config=_whitelist(_MODEL),
        catalog_provider=counter,
    )
    registry.resolve_route(_MODEL)
    registry.resolve_route(_MODEL)
    assert counter.call_count == 1


# ---------------------------------------------------------------------------
# No-registry fail-safe (tested via resolver; here via direct construction)
# ---------------------------------------------------------------------------


def test_default_registry_empty_catalog_returns_unknown() -> None:
    """Default (no args) registry has empty catalog → all misses → UNKNOWN."""
    registry = OpenRouterCapabilityRegistry()
    status, profile, capable = registry.resolve_route(_MODEL)
    assert status is SafetyWhitelistStatus.UNKNOWN
    assert profile is None
    assert capable is False
