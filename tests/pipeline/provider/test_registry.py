"""Tests for OpenRouterCapabilityRegistry (CRD Issue 14b).

Coverage targets:
  - Resolution ladder: static deny-set, catalog miss, dynamic alias entry,
    positive-evidence rejection (AC 11/12 + context floor), capability evaluation,
    whitelist lookup.
  - UNKNOWN / STALE / WHITELISTED / NOT_WHITELISTED / DISABLED paths.
  - Fail-safe cases: text_output=None, context_length=None.
  - Time-based STALE (max_evidence_age).
  - _can_skip interaction: DISABLED + capable must NOT skip Safety.
  - Catalog caching: fetch_catalog called only once per registry instance.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

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
_OLD = datetime(2025, 1, 1, tzinfo=UTC)
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


def _whitelist(*model_ids: str, verified_at: datetime = _NOW) -> WhitelistConfig:
    return WhitelistConfig(
        enabled=True,
        entries={
            mid: WhitelistEntry(model_identifier=mid, verified_at=verified_at)
            for mid in model_ids
        },
    )


def _make_registry(
    entries: list[OpenRouterCatalogModel] | None = None,
    whitelist: WhitelistConfig | None = None,
    max_evidence_age: timedelta | None = None,
    clock: None = None,
) -> OpenRouterCapabilityRegistry:
    provider = FixtureOpenRouterCatalogProvider(entries or [])
    return OpenRouterCapabilityRegistry(
        whitelist_config=whitelist,
        catalog_provider=provider,
        max_evidence_age=max_evidence_age,
        clock=clock,
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
    registry = _make_registry(
        entries=[_catalog_entry("openrouter/auto")],
    )
    with pytest.raises(ProviderConfigError, match="dynamic alias"):
        registry.resolve_route("openrouter/auto")


def test_dynamic_alias_rejected_with_disabled_whitelist() -> None:
    """Dynamic alias raises ProviderConfigError even when whitelist is disabled."""
    disabled_wl = WhitelistConfig(enabled=False)
    registry = _make_registry(whitelist=disabled_wl)
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


def test_catalog_miss_disabled_whitelist_returns_disabled() -> None:
    """Catalog miss + disabled whitelist → DISABLED, not UNKNOWN."""
    disabled_wl = WhitelistConfig(enabled=False)
    registry = _make_registry(whitelist=disabled_wl)  # empty catalog
    status, profile, capable = registry.resolve_route(_MODEL)
    assert status is SafetyWhitelistStatus.DISABLED
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
# Step 5: AC 11 — structured-pass incapability rejection
# ---------------------------------------------------------------------------


def test_tool_use_false_and_structured_false_raises() -> None:
    """tool_use=False AND structured_output=False → ProviderConfigError."""
    entry = _catalog_entry(
        _MODEL, supports_tool_use=False, supports_structured_output=False
    )
    registry = _make_registry(entries=[entry])
    with pytest.raises(ProviderConfigError, match="structured"):
        registry.resolve_route(_MODEL)


def test_tool_use_false_structured_output_none_does_not_raise() -> None:
    """tool_use=False but structured_output=None: unverified → no reject."""
    entry = _catalog_entry(
        _MODEL, supports_tool_use=False, supports_structured_output=None
    )
    registry = _make_registry(entries=[entry], whitelist=_whitelist(_MODEL))
    status, profile, capable = registry.resolve_route(_MODEL)
    assert profile is not None
    assert status is SafetyWhitelistStatus.WHITELISTED


def test_tool_use_none_structured_output_false_does_not_raise() -> None:
    """structured_output=False but tool_use=None: unverified → no reject."""
    entry = _catalog_entry(
        _MODEL, supports_tool_use=None, supports_structured_output=False
    )
    registry = _make_registry(entries=[entry], whitelist=_whitelist(_MODEL))
    status, profile, capable = registry.resolve_route(_MODEL)
    assert profile is not None
    assert status is SafetyWhitelistStatus.WHITELISTED


def test_both_structured_fields_none_does_not_raise() -> None:
    """tool_use=None + structured_output=None: unverified → no reject, capable=False."""
    entry = _catalog_entry(
        _MODEL, supports_tool_use=None, supports_structured_output=None
    )
    registry = _make_registry(entries=[entry], whitelist=_whitelist(_MODEL))
    status, profile, capable = registry.resolve_route(_MODEL)
    assert profile is not None
    assert capable is False  # unverified structured → Safety must run


def test_tool_use_true_structured_none_is_capable() -> None:
    """tool_use=True satisfies structured requirement even if structured_output=None."""
    entry = _catalog_entry(
        _MODEL, supports_tool_use=True, supports_structured_output=None
    )
    registry = _make_registry(entries=[entry], whitelist=_whitelist(_MODEL))
    _, _, capable = registry.resolve_route(_MODEL)
    assert capable is True


def test_tool_use_none_structured_output_true_is_not_capable() -> None:
    """structured_output=True, tool_use=None → not capable (adapter: tools only)."""
    entry = _catalog_entry(
        _MODEL, supports_tool_use=None, supports_structured_output=True
    )
    registry = _make_registry(entries=[entry], whitelist=_whitelist(_MODEL))
    _, _, capable = registry.resolve_route(_MODEL)
    assert capable is False


def test_tool_use_true_structured_output_false_is_capable() -> None:
    """tool_use=True, structured_output=False → capable (adapter path confirmed)."""
    entry = _catalog_entry(
        _MODEL, supports_tool_use=True, supports_structured_output=False
    )
    registry = _make_registry(entries=[entry], whitelist=_whitelist(_MODEL))
    _, _, capable = registry.resolve_route(_MODEL)
    assert capable is True


def test_tool_use_false_structured_output_true_is_not_capable() -> None:
    """tool_use=False + structured_output=True → not capable, not rejected."""
    entry = _catalog_entry(
        _MODEL, supports_tool_use=False, supports_structured_output=True
    )
    registry = _make_registry(entries=[entry], whitelist=_whitelist(_MODEL))
    status, profile, capable = registry.resolve_route(_MODEL)
    assert capable is False
    assert profile is not None  # route is live; AC 11 did not fire
    assert status is SafetyWhitelistStatus.WHITELISTED


# ---------------------------------------------------------------------------
# Step 5: context_length floor — rejection for known below-floor length
# ---------------------------------------------------------------------------


def test_context_length_below_floor_raises() -> None:
    """context_length below floor raises ProviderConfigError (Writer context floor)."""
    below_floor = _WRITER_CONTEXT_LENGTH_FLOOR - 1
    entry = _catalog_entry(_MODEL, context_length=below_floor)
    registry = _make_registry(entries=[entry], whitelist=_whitelist(_MODEL))
    with pytest.raises(ProviderConfigError, match="context length"):
        registry.resolve_route(_MODEL)


def test_context_length_none_does_not_raise() -> None:
    """context_length=None → unverified; route not rejected, capable=False."""
    entry = _catalog_entry(_MODEL, context_length=None)
    registry = _make_registry(entries=[entry], whitelist=_whitelist(_MODEL))
    status, profile, capable = registry.resolve_route(_MODEL)
    assert capable is False
    assert profile is not None
    assert profile.context_length is None


def test_custom_floor_applies() -> None:
    """writer_context_length_floor constructor param overrides default."""
    low_floor = 1000
    entry = _catalog_entry(_MODEL, context_length=2000)
    # With a custom floor of 1000, context_length=2000 should NOT raise.
    registry = OpenRouterCapabilityRegistry(
        whitelist_config=_whitelist(_MODEL),
        catalog_provider=FixtureOpenRouterCatalogProvider([entry]),
        writer_context_length_floor=low_floor,
    )
    status, profile, capable = registry.resolve_route(_MODEL)
    assert capable is True
    assert status is SafetyWhitelistStatus.WHITELISTED


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
    """context_length exactly == floor → capable=True (not rejected)."""
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
# Step 7: time-based STALE (max_evidence_age)
# ---------------------------------------------------------------------------


def test_stale_by_age_returns_stale_with_profile() -> None:
    """Whitelist entry with verified_at older than max_evidence_age → STALE."""
    entry = _catalog_entry(_MODEL)
    old_wl = WhitelistConfig(
        enabled=True,
        entries={_MODEL: WhitelistEntry(model_identifier=_MODEL, verified_at=_OLD)},
    )
    # max_evidence_age=1 day; _OLD is 2025-01-01, _NOW is 2026-06-01 → stale
    registry = OpenRouterCapabilityRegistry(
        whitelist_config=old_wl,
        catalog_provider=FixtureOpenRouterCatalogProvider([entry]),
        max_evidence_age=timedelta(days=1),
        clock=lambda: _NOW,
    )
    status, profile, capable = registry.resolve_route(_MODEL)
    assert status is SafetyWhitelistStatus.STALE
    assert profile is not None
    assert capable is True  # model IS capable; only the whitelist evidence is stale


def test_fresh_whitelist_entry_not_stale() -> None:
    """Whitelist entry with verified_at within max_evidence_age → WHITELISTED."""
    entry = _catalog_entry(_MODEL)
    # verified_at = _NOW; clock = _NOW + 12h; age = 1 day → NOT stale
    clock_time = datetime(2026, 6, 1, 12, tzinfo=UTC)
    registry = OpenRouterCapabilityRegistry(
        whitelist_config=_whitelist(_MODEL, verified_at=_NOW),
        catalog_provider=FixtureOpenRouterCatalogProvider([entry]),
        max_evidence_age=timedelta(days=1),
        clock=lambda: clock_time,
    )
    status, profile, capable = registry.resolve_route(_MODEL)
    assert status is SafetyWhitelistStatus.WHITELISTED
    assert capable is True


def test_no_max_evidence_age_never_stale_by_age() -> None:
    """max_evidence_age=None → old verified_at does not trigger STALE."""
    entry = _catalog_entry(_MODEL)
    old_wl = WhitelistConfig(
        enabled=True,
        entries={_MODEL: WhitelistEntry(model_identifier=_MODEL, verified_at=_OLD)},
    )
    registry = OpenRouterCapabilityRegistry(
        whitelist_config=old_wl,
        catalog_provider=FixtureOpenRouterCatalogProvider([entry]),
        max_evidence_age=None,
    )
    status, profile, capable = registry.resolve_route(_MODEL)
    assert status is SafetyWhitelistStatus.WHITELISTED


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
