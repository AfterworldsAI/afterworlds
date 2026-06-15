"""Tests for ProviderResolver hosted-path routing — CRD Issue 14a.

Covers:
  - Fail-closed when openrouter_api_key is set without openrouter_fallback_model
  - Anthropic-only hosted path: single trusted eligible route
  - Anthropic + OpenRouter hosted path: two routes, OpenRouter not trusted
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.pipeline.provider._errors import ProviderConfigError
from afterworlds.pipeline.provider._resolver import (
    HostedRoutingConfig,
    ProviderResolver,
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
    """No OpenRouter key → single Anthropic route with trusted_for_safety_skip=True."""
    cfg = HostedRoutingConfig(anthropic_api_key="sk-ant-test")
    binding = _resolver(cfg).resolve_for_turn(
        access_path=RuntimeAccessPath.HOSTED,
        sojourner_id=uuid4(),
    )
    assert len(binding.eligible_writer_routes) == 1
    route = binding.eligible_writer_routes[0]
    assert route.provider_name == "anthropic"
    assert route.trusted_for_safety_skip is True
    assert route.is_openrouter is False


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


def test_hosted_openrouter_route_is_not_trusted_for_safety_skip() -> None:
    """OpenRouter eligible route always has trusted_for_safety_skip=False."""
    cfg = HostedRoutingConfig(
        anthropic_api_key="sk-ant-test",
        openrouter_api_key="sk-or-test",
        openrouter_fallback_model="anthropic/claude-haiku-4-5",
    )
    binding = _resolver(cfg).resolve_for_turn(
        access_path=RuntimeAccessPath.HOSTED,
        sojourner_id=uuid4(),
    )
    or_route = next(r for r in binding.eligible_writer_routes if r.is_openrouter)
    assert or_route.trusted_for_safety_skip is False
