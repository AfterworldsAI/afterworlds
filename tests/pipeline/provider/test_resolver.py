"""Tests for ProviderResolver hosted-path routing — CRD Issue 14a.

Covers:
  - Fail-closed when openrouter_api_key is set without openrouter_fallback_model
  - Anthropic-only hosted path: single trusted eligible route
  - Anthropic + OpenRouter hosted path: two routes, OpenRouter not trusted
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.persistence.database import create_session_factory
from afterworlds.pipeline.provider._errors import ProviderConfigError
from afterworlds.pipeline.provider._resolver import (
    HostedRoutingConfig,
    ProviderResolver,
)
from afterworlds.pipeline.provider._route_config import ProviderRouteConfigORM
from afterworlds.pipeline.provider.credentials._metadata import (
    ProviderCredentialMetadata,
    ValidationStatus,
)


def _resolver(cfg: HostedRoutingConfig) -> ProviderResolver:
    store = MagicMock()
    return ProviderResolver(
        credential_store=store,
        hosted_config=cfg,
        session_factory=MagicMock(),
    )


# ---------------------------------------------------------------------------
# Fail-closed: key set but model absent
# ---------------------------------------------------------------------------


def test_hosted_with_key_but_no_model_raises() -> None:
    """openrouter_api_key set but fallback model absent → ProviderConfigError."""
    cfg = HostedRoutingConfig(
        anthropic_api_key="sk-ant-test",
        openrouter_api_key="sk-or-test",
        openrouter_fallback_model=None,
    )
    resolver = _resolver(cfg)
    with pytest.raises(ProviderConfigError, match="openrouter_fallback_model"):
        resolver.resolve_for_turn(
            access_path=RuntimeAccessPath.HOSTED,
            sojourner_id=uuid4(),
        )


def test_hosted_with_key_and_blank_model_raises() -> None:
    """openrouter_api_key set and fallback model blank → ProviderConfigError."""
    cfg = HostedRoutingConfig(
        anthropic_api_key="sk-ant-test",
        openrouter_api_key="sk-or-test",
        openrouter_fallback_model="   ",
    )
    resolver = _resolver(cfg)
    with pytest.raises(ProviderConfigError, match="openrouter_fallback_model"):
        resolver.resolve_for_turn(
            access_path=RuntimeAccessPath.HOSTED,
            sojourner_id=uuid4(),
        )


# ---------------------------------------------------------------------------
# Anthropic-only hosted path
# ---------------------------------------------------------------------------


def test_hosted_anthropic_only_returns_single_eligible_route() -> None:
    """No OpenRouter key → single Anthropic route WHITELISTED and capable."""
    cfg = HostedRoutingConfig(anthropic_api_key="sk-ant-test")
    binding = _resolver(cfg).resolve_for_turn(
        access_path=RuntimeAccessPath.HOSTED,
        sojourner_id=uuid4(),
    )
    assert len(binding.eligible_writer_routes) == 1
    route = binding.eligible_writer_routes[0]
    assert route.provider_name == "anthropic"
    from afterworlds.pipeline.provider._routing import SafetyWhitelistStatus

    assert route.whitelist_status is SafetyWhitelistStatus.WHITELISTED
    assert route.supports_required_capabilities is True


def test_hosted_anthropic_only_access_path_is_hosted() -> None:
    cfg = HostedRoutingConfig(anthropic_api_key="sk-ant-test")
    binding = _resolver(cfg).resolve_for_turn(
        access_path=RuntimeAccessPath.HOSTED,
        sojourner_id=uuid4(),
    )
    assert binding.access_path is RuntimeAccessPath.HOSTED


# ---------------------------------------------------------------------------
# Anthropic + OpenRouter hosted path
# ---------------------------------------------------------------------------


def test_hosted_with_key_and_model_returns_two_eligible_routes() -> None:
    """OpenRouter key + model → two eligible Writer routes."""
    cfg = HostedRoutingConfig(
        anthropic_api_key="sk-ant-test",
        openrouter_api_key="sk-or-test",
        openrouter_fallback_model="anthropic/claude-haiku-4-5",
    )
    binding = _resolver(cfg).resolve_for_turn(
        access_path=RuntimeAccessPath.HOSTED,
        sojourner_id=uuid4(),
    )
    assert len(binding.eligible_writer_routes) == 2
    providers = {r.provider_name for r in binding.eligible_writer_routes}
    assert providers == {"anthropic", "openrouter"}


def test_hosted_openrouter_route_without_registry_is_unknown() -> None:
    """OpenRouter route without registry → UNKNOWN status, not capable (fail-safe)."""
    cfg = HostedRoutingConfig(
        anthropic_api_key="sk-ant-test",
        openrouter_api_key="sk-or-test",
        openrouter_fallback_model="anthropic/claude-haiku-4-5",
    )
    binding = _resolver(cfg).resolve_for_turn(
        access_path=RuntimeAccessPath.HOSTED,
        sojourner_id=uuid4(),
    )
    from afterworlds.pipeline.provider._routing import SafetyWhitelistStatus

    or_route = next(
        r for r in binding.eligible_writer_routes if r.provider_name == "openrouter"
    )
    assert or_route.whitelist_status is SafetyWhitelistStatus.UNKNOWN
    assert or_route.supports_required_capabilities is False


# ---------------------------------------------------------------------------
# BYOK OpenRouter model-id validation (blank/whitespace → fail closed)
# ---------------------------------------------------------------------------


def _byok_resolver(session_factory: object) -> ProviderResolver:
    """BYOK resolver with OpenRouter-only credentials (no Anthropic key)."""
    store = MagicMock()
    store.get.side_effect = lambda _sid, provider: (
        "sk-or-test" if provider == "openrouter" else None
    )
    return ProviderResolver(
        credential_store=store,
        hosted_config=None,
        session_factory=session_factory,
    )


_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _add_metadata(
    sf: object,
    sid: UUID,
    provider: str,
    *,
    is_active: bool = True,
    validation_status: str = ValidationStatus.UNTESTED,
) -> None:
    """Insert a ProviderCredentialMetadata row for test setup."""
    assert callable(sf)
    sess = sf()
    sess.add(
        ProviderCredentialMetadata(
            sojourner_id=str(sid),
            provider_name=provider,
            is_active=is_active,
            validation_status=validation_status,
            created_at=_NOW,
            updated_at=_NOW,
        )
    )
    sess.commit()
    sess.close()


def test_byok_openrouter_no_row_raises(engine) -> None:  # type: ignore[no-untyped-def]
    """No ProviderRouteConfig row for Sojourner → ProviderConfigError."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "openrouter")
    resolver = _byok_resolver(sf)
    with pytest.raises(ProviderConfigError, match="preferred_model_identifier"):
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)


def test_byok_openrouter_none_model_id_raises(engine) -> None:  # type: ignore[no-untyped-def]
    """Row exists but preferred_model_identifier is NULL → ProviderConfigError."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "openrouter")
    sess = sf()
    sess.add(
        ProviderRouteConfigORM(
            sojourner_id=str(sid),
            provider_name="openrouter",
            preferred_model_identifier=None,
            is_active=True,
        )
    )
    sess.commit()
    sess.close()
    resolver = _byok_resolver(sf)
    with pytest.raises(ProviderConfigError, match="preferred_model_identifier"):
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)


def test_byok_openrouter_empty_model_id_raises(engine) -> None:  # type: ignore[no-untyped-def]
    """preferred_model_identifier='' → ProviderConfigError."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "openrouter")
    sess = sf()
    sess.add(
        ProviderRouteConfigORM(
            sojourner_id=str(sid),
            provider_name="openrouter",
            preferred_model_identifier="",
            is_active=True,
        )
    )
    sess.commit()
    sess.close()
    resolver = _byok_resolver(sf)
    with pytest.raises(ProviderConfigError, match="preferred_model_identifier"):
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)


def test_byok_openrouter_whitespace_model_id_raises(engine) -> None:  # type: ignore[no-untyped-def]
    """preferred_model_identifier='   ' → ProviderConfigError."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "openrouter")
    sess = sf()
    sess.add(
        ProviderRouteConfigORM(
            sojourner_id=str(sid),
            provider_name="openrouter",
            preferred_model_identifier="   ",
            is_active=True,
        )
    )
    sess.commit()
    sess.close()
    resolver = _byok_resolver(sf)
    with pytest.raises(ProviderConfigError, match="preferred_model_identifier"):
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)


def test_byok_openrouter_padded_model_id_returns_stripped(engine) -> None:  # type: ignore[no-untyped-def]
    """Whitespace-padded valid id → stripped model_identifier in binding."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "openrouter")
    sess = sf()
    sess.add(
        ProviderRouteConfigORM(
            sojourner_id=str(sid),
            provider_name="openrouter",
            preferred_model_identifier="  anthropic/claude-haiku-4-5  ",
            is_active=True,
        )
    )
    sess.commit()
    sess.close()
    resolver = _byok_resolver(sf)
    binding = resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)
    or_route = next(
        r for r in binding.eligible_writer_routes if r.provider_name == "openrouter"
    )
    assert or_route.model_identifier == "anthropic/claude-haiku-4-5"


# ---------------------------------------------------------------------------
# BYOK credential metadata activation (P2 #2)
# ---------------------------------------------------------------------------


def _byok_resolver_two_keys(session_factory: object) -> ProviderResolver:
    """BYOK resolver with both Anthropic and OpenRouter credentials."""
    store = MagicMock()
    store.get.side_effect = lambda _sid, provider: {
        "anthropic": "sk-ant-test",
        "openrouter": "sk-or-test",
    }.get(provider)
    return ProviderResolver(
        credential_store=store,
        hosted_config=None,
        session_factory=session_factory,
    )


def _byok_resolver_anthropic_only(session_factory: object) -> ProviderResolver:
    """BYOK resolver with Anthropic-only credentials."""
    store = MagicMock()
    store.get.side_effect = lambda _sid, provider: (
        "sk-ant-test" if provider == "anthropic" else None
    )
    return ProviderResolver(
        credential_store=store,
        hosted_config=None,
        session_factory=session_factory,
    )


def test_byok_active_anthropic_metadata_and_key_returns_binding(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """Active Anthropic metadata + key → Anthropic route in binding."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic")
    resolver = _byok_resolver_anthropic_only(sf)
    binding = resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)
    provider_names = {r.provider_name for r in binding.eligible_writer_routes}
    assert "anthropic" in provider_names


def test_byok_inactive_anthropic_metadata_key_present_raises(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """Inactive Anthropic metadata + key in keychain → ProviderConfigError."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic", is_active=False)
    resolver = _byok_resolver_anthropic_only(sf)
    with pytest.raises(ProviderConfigError, match="no configured credentials"):
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)


def test_byok_active_openrouter_metadata_and_key_returns_binding(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """Active OpenRouter metadata + key + valid route config → OpenRouter in binding."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "openrouter")
    sess = sf()
    sess.add(
        ProviderRouteConfigORM(
            sojourner_id=str(sid),
            provider_name="openrouter",
            preferred_model_identifier="anthropic/claude-haiku-4-5",
            is_active=True,
        )
    )
    sess.commit()
    sess.close()
    resolver = _byok_resolver(sf)
    binding = resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)
    provider_names = {r.provider_name for r in binding.eligible_writer_routes}
    assert "openrouter" in provider_names


def test_byok_inactive_openrouter_metadata_key_present_raises(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """Inactive OpenRouter metadata + key → ProviderConfigError."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "openrouter", is_active=False)
    sess = sf()
    sess.add(
        ProviderRouteConfigORM(
            sojourner_id=str(sid),
            provider_name="openrouter",
            preferred_model_identifier="anthropic/claude-haiku-4-5",
            is_active=True,
        )
    )
    sess.commit()
    sess.close()
    resolver = _byok_resolver(sf)
    with pytest.raises(ProviderConfigError, match="no configured credentials"):
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)


def test_byok_one_active_one_inactive_only_active_participates(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """Active Anthropic + inactive OpenRouter → only Anthropic in eligible routes."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic", is_active=True)
    _add_metadata(sf, sid, "openrouter", is_active=False)
    resolver = _byok_resolver_two_keys(sf)
    binding = resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)
    provider_names = {r.provider_name for r in binding.eligible_writer_routes}
    assert provider_names == {"anthropic"}


def test_byok_all_credentials_inactive_raises(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """All credential metadata inactive → ProviderConfigError."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic", is_active=False)
    _add_metadata(sf, sid, "openrouter", is_active=False)
    resolver = _byok_resolver_two_keys(sf)
    with pytest.raises(ProviderConfigError, match="no configured credentials"):
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)


def test_byok_error_message_contains_no_key_material(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """ProviderConfigError on inactive credentials contains no key material."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic", is_active=False)
    resolver = _byok_resolver_anthropic_only(sf)
    with pytest.raises(ProviderConfigError) as exc_info:
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)
    error_text = str(exc_info.value)
    assert "sk-ant" not in error_text
    assert "sk-or" not in error_text


# ---------------------------------------------------------------------------
# BYOK validation_status eligibility gate (P2 #2)
# ---------------------------------------------------------------------------


def test_byok_anthropic_valid_status_eligible(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """Active Anthropic metadata with VALID status → eligible route."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic", validation_status=ValidationStatus.VALID)
    resolver = _byok_resolver_anthropic_only(sf)
    binding = resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)
    provider_names = {r.provider_name for r in binding.eligible_writer_routes}
    assert "anthropic" in provider_names


def test_byok_anthropic_untested_status_eligible(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """Active Anthropic UNTESTED status → eligible (permissive default)."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic", validation_status=ValidationStatus.UNTESTED)
    resolver = _byok_resolver_anthropic_only(sf)
    binding = resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)
    provider_names = {r.provider_name for r in binding.eligible_writer_routes}
    assert "anthropic" in provider_names


def test_byok_anthropic_invalid_status_raises(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """Active Anthropic metadata with INVALID status → ProviderConfigError."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic", validation_status=ValidationStatus.INVALID)
    resolver = _byok_resolver_anthropic_only(sf)
    with pytest.raises(ProviderConfigError, match="no configured credentials"):
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)


def test_byok_anthropic_error_status_raises(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """Active Anthropic metadata with ERROR status → ProviderConfigError."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic", validation_status=ValidationStatus.ERROR)
    resolver = _byok_resolver_anthropic_only(sf)
    with pytest.raises(ProviderConfigError, match="no configured credentials"):
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)


def test_byok_openrouter_invalid_status_raises(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """Active OpenRouter metadata with INVALID status → ProviderConfigError."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "openrouter", validation_status=ValidationStatus.INVALID)
    sess = sf()
    sess.add(
        ProviderRouteConfigORM(
            sojourner_id=str(sid),
            provider_name="openrouter",
            preferred_model_identifier="anthropic/claude-haiku-4-5",
            is_active=True,
        )
    )
    sess.commit()
    sess.close()
    resolver = _byok_resolver(sf)
    with pytest.raises(ProviderConfigError, match="no configured credentials"):
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)


def test_byok_openrouter_error_status_raises(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """Active OpenRouter metadata with ERROR status → ProviderConfigError."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "openrouter", validation_status=ValidationStatus.ERROR)
    sess = sf()
    sess.add(
        ProviderRouteConfigORM(
            sojourner_id=str(sid),
            provider_name="openrouter",
            preferred_model_identifier="anthropic/claude-haiku-4-5",
            is_active=True,
        )
    )
    sess.commit()
    sess.close()
    resolver = _byok_resolver(sf)
    with pytest.raises(ProviderConfigError, match="no configured credentials"):
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)


def test_byok_one_invalid_one_valid_only_valid_participates(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """Active Anthropic INVALID + OpenRouter VALID → only OpenRouter eligible.

    (Uses the two-key resolver; OpenRouter has a valid route config.)
    """
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic", validation_status=ValidationStatus.INVALID)
    _add_metadata(sf, sid, "openrouter", validation_status=ValidationStatus.VALID)
    sess = sf()
    sess.add(
        ProviderRouteConfigORM(
            sojourner_id=str(sid),
            provider_name="openrouter",
            preferred_model_identifier="anthropic/claude-haiku-4-5",
            is_active=True,
        )
    )
    sess.commit()
    sess.close()
    resolver = _byok_resolver_two_keys(sf)
    binding = resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)
    provider_names = {r.provider_name for r in binding.eligible_writer_routes}
    assert provider_names == {"openrouter"}
    assert "anthropic" not in provider_names


def test_byok_all_credentials_invalid_raises(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """All credentials INVALID → ProviderConfigError."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic", validation_status=ValidationStatus.INVALID)
    _add_metadata(sf, sid, "openrouter", validation_status=ValidationStatus.INVALID)
    resolver = _byok_resolver_two_keys(sf)
    with pytest.raises(ProviderConfigError, match="no configured credentials"):
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)


def test_byok_invalid_status_error_contains_no_key_material(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """ProviderConfigError on INVALID credential contains no key material."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic", validation_status=ValidationStatus.INVALID)
    resolver = _byok_resolver_anthropic_only(sf)
    with pytest.raises(ProviderConfigError) as exc_info:
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)
    error_text = str(exc_info.value)
    assert "sk-ant" not in error_text
    assert "sk-or" not in error_text
