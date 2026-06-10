"""Unit tests for provider adapter utilities — no HTTP calls required.

Covers:
  - RefusalFallbackRouter: all call paths, construction invariant
  - CapabilityProfileAwareSafetyPolicy: safety-skip logic
  - normalization.py: ValueError branches
  - ProviderCallError.detail attribute
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from afterworlds.entitlement.enums import ModelTier, PipelinePassId, RuntimeAccessPath
from afterworlds.pipeline._refusal import (
    PassIdentifier,
    ProviderRefusal,
    ProviderRefusalError,
    RefusalCategory,
)
from afterworlds.pipeline._stable_prefix_renderer import RenderedBlock
from afterworlds.pipeline.provider._errors import (
    CredentialValidationError,
    ProviderCallError,
    ProviderConfigError,
)
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderTextPart,
)
from afterworlds.pipeline.provider._routing import (
    CapabilityProfileAwareSafetyPolicy,
    EligibleWriterRoute,
    SafetyPolicyContext,
)
from afterworlds.pipeline.provider.adapters._fallback import RefusalFallbackRouter
from afterworlds.pipeline.provider.normalization import (
    AnthropicNormalizationFactorProvider,
    OpenRouterNormalizationFactorProvider,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request() -> ProviderCallRequest:
    return ProviderCallRequest(
        pass_id=PipelinePassId.WRITER,
        rendered_blocks=[RenderedBlock(text="Write the next scene.")],
        max_output_tokens=512,
    )


def _make_result(provider: str = "anthropic") -> ProviderCallResult:
    return ProviderCallResult(
        pass_id=PipelinePassId.WRITER,
        provider_name=provider,
        model_identifier="claude-sonnet-4-6",
        model_tier=ModelTier.SONNET,
        content_parts=[ProviderTextPart(text="The scene begins.")],
        input_token_count=100,
        output_token_count=50,
        cache_read_token_count=None,
        cache_creation_token_count=None,
        cache_warmed=False,
        latency_ms=200,
    )


def _make_refusal(provider: str = "anthropic") -> ProviderRefusalError:
    return ProviderRefusalError(
        ProviderRefusal(
            provider=provider,
            model="claude-sonnet-4-6",
            pass_identifier=PassIdentifier.WRITER,
            refusal_category=RefusalCategory.CONTENT_POLICY,
        )
    )


def _route(
    trusted: bool = True,
    provider: str = "anthropic",
    is_openrouter: bool = False,
) -> EligibleWriterRoute:
    return EligibleWriterRoute(
        provider_name=provider,
        model_identifier="claude-sonnet-4-6",
        is_openrouter=is_openrouter,
        trusted_for_safety_skip=trusted,
    )


def _ctx(
    routes: tuple[EligibleWriterRoute, ...],
    risk: bool = False,
    writer_result: object = None,
) -> SafetyPolicyContext:
    return SafetyPolicyContext(
        eligible_writer_routes=routes,
        request_risk_signal=risk,
        access_path=RuntimeAccessPath.HOSTED,
        writer_result=writer_result,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# ProviderCallError
# ---------------------------------------------------------------------------


def test_provider_call_error_detail() -> None:
    err = ProviderCallError("context limit exceeded")
    assert err.detail == "context limit exceeded"
    assert str(err) == "context limit exceeded"


def test_provider_config_error() -> None:
    with pytest.raises(ProviderConfigError):
        raise ProviderConfigError("no credentials configured")


def test_credential_validation_error() -> None:
    with pytest.raises(CredentialValidationError):
        raise CredentialValidationError("key must be non-empty")


# ---------------------------------------------------------------------------
# Normalization factor providers
# ---------------------------------------------------------------------------


def test_anthropic_normalization_factor_happy() -> None:
    p = AnthropicNormalizationFactorProvider()
    assert p.get_factor("anthropic") == Decimal("1.0")


def test_anthropic_normalization_factor_wrong_provider() -> None:
    p = AnthropicNormalizationFactorProvider()
    with pytest.raises(ValueError, match="unexpected provider"):
        p.get_factor("openrouter")


def test_openrouter_normalization_factor_happy() -> None:
    p = OpenRouterNormalizationFactorProvider()
    assert p.get_factor("openrouter") == Decimal("1.0")


def test_openrouter_normalization_factor_wrong_provider() -> None:
    p = OpenRouterNormalizationFactorProvider()
    with pytest.raises(ValueError, match="unexpected provider"):
        p.get_factor("anthropic")


# ---------------------------------------------------------------------------
# CapabilityProfileAwareSafetyPolicy
# ---------------------------------------------------------------------------


def test_safety_policy_skips_when_all_routes_trusted() -> None:
    policy = CapabilityProfileAwareSafetyPolicy()
    ctx = _ctx((_route(trusted=True), _route(trusted=True)))
    assert not policy.should_run_input_preflight(ctx)
    assert not policy.should_run_output_audit(ctx)


def test_safety_policy_runs_when_any_route_untrusted() -> None:
    policy = CapabilityProfileAwareSafetyPolicy()
    ctx = _ctx(
        (
            _route(trusted=True),
            _route(trusted=False, provider="openrouter", is_openrouter=True),
        )
    )
    assert policy.should_run_input_preflight(ctx)
    assert policy.should_run_output_audit(ctx)


def test_safety_policy_runs_when_all_routes_untrusted() -> None:
    policy = CapabilityProfileAwareSafetyPolicy()
    ctx = _ctx((_route(trusted=False, provider="openrouter", is_openrouter=True),))
    assert policy.should_run_input_preflight(ctx)


def test_safety_policy_forces_safety_on_empty_routes() -> None:
    policy = CapabilityProfileAwareSafetyPolicy()
    ctx = _ctx(())
    assert policy.should_run_input_preflight(ctx)


def test_safety_policy_forces_safety_on_risk_signal() -> None:
    policy = CapabilityProfileAwareSafetyPolicy()
    ctx = _ctx((_route(trusted=True),), risk=True)
    assert policy.should_run_input_preflight(ctx)
    assert policy.should_run_output_audit(ctx)


# ---------------------------------------------------------------------------
# RefusalFallbackRouter — construction invariants
# ---------------------------------------------------------------------------


def test_nested_router_rejected_at_construction() -> None:
    primary = MagicMock()
    primary.provider_name = "anthropic"
    fallback = RefusalFallbackRouter(primary=primary)

    with pytest.raises(ProviderConfigError, match="nested RefusalFallbackRouter"):
        RefusalFallbackRouter(primary=primary, fallback=fallback)


def test_construction_with_valid_fallback() -> None:
    primary = MagicMock()
    primary.provider_name = "anthropic"
    fallback = MagicMock()
    fallback.provider_name = "openrouter"

    router = RefusalFallbackRouter(primary=primary, fallback=fallback)
    assert router.provider_name == "anthropic"


def test_construction_without_fallback() -> None:
    primary = MagicMock()
    primary.provider_name = "anthropic"
    router = RefusalFallbackRouter(primary=primary)
    assert router.provider_name == "anthropic"


# ---------------------------------------------------------------------------
# RefusalFallbackRouter — call() paths
# ---------------------------------------------------------------------------


def test_router_returns_primary_result_on_success() -> None:
    request = _make_request()
    expected = _make_result()
    primary = MagicMock()
    primary.call.return_value = expected
    primary.provider_name = "anthropic"

    router = RefusalFallbackRouter(primary=primary)
    result = router.call(request)

    assert result is expected
    primary.call.assert_called_once_with(request)


def test_router_propagates_provider_call_error_without_fallback() -> None:
    """ProviderCallError from primary re-raises; fallback is NOT tried."""
    request = _make_request()
    primary = MagicMock()
    primary.provider_name = "anthropic"
    primary.call.side_effect = ProviderCallError("rate limit")
    fallback = MagicMock()
    fallback.provider_name = "openrouter"

    router = RefusalFallbackRouter(primary=primary, fallback=fallback)
    with pytest.raises(ProviderCallError, match="rate limit"):
        router.call(request)

    fallback.call.assert_not_called()


def test_router_reraises_when_no_fallback_configured() -> None:
    request = _make_request()
    primary = MagicMock()
    primary.provider_name = "anthropic"
    primary.call.side_effect = _make_refusal()

    router = RefusalFallbackRouter(primary=primary, fallback=None)
    with pytest.raises(ProviderRefusalError):
        router.call(request)


def test_router_logs_no_fallback_configured() -> None:
    request = _make_request()
    primary = MagicMock()
    primary.provider_name = "anthropic"
    primary.call.side_effect = _make_refusal()
    log_fn = MagicMock()

    router = RefusalFallbackRouter(
        primary=primary, fallback=None, refusal_log_fn=log_fn
    )
    with pytest.raises(ProviderRefusalError):
        router.call(request)

    log_fn.assert_called_once()
    call_kwargs = log_fn.call_args.kwargs
    assert call_kwargs["outcome"] == "NO_FALLBACK_CONFIGURED"
    assert call_kwargs["fallback_provider"] is None
    assert call_kwargs["fallback_model"] is None


def test_router_returns_fallback_result_on_primary_refusal() -> None:
    request = _make_request()
    fallback_result = _make_result(provider="openrouter")
    primary = MagicMock()
    primary.provider_name = "anthropic"
    primary.call.side_effect = _make_refusal()
    fallback = MagicMock()
    fallback.provider_name = "openrouter"
    fallback.call.return_value = fallback_result

    router = RefusalFallbackRouter(primary=primary, fallback=fallback)
    result = router.call(request)

    assert result is fallback_result


def test_router_logs_fallback_succeeded() -> None:
    request = _make_request()
    fallback_result = _make_result(provider="openrouter")
    primary = MagicMock()
    primary.provider_name = "anthropic"
    primary.call.side_effect = _make_refusal()
    fallback = MagicMock()
    fallback.provider_name = "openrouter"
    fallback.call.return_value = fallback_result
    log_fn = MagicMock()

    router = RefusalFallbackRouter(
        primary=primary, fallback=fallback, refusal_log_fn=log_fn
    )
    router.call(request)

    log_fn.assert_called_once()
    call_kwargs = log_fn.call_args.kwargs
    assert call_kwargs["outcome"] == "FALLBACK_SUCCEEDED"
    assert call_kwargs["fallback_provider"] == "openrouter"


def test_router_raises_fallback_refusal_when_fallback_also_refuses() -> None:
    request = _make_request()
    primary = MagicMock()
    primary.provider_name = "anthropic"
    primary.call.side_effect = _make_refusal("anthropic")
    fallback = MagicMock()
    fallback.provider_name = "openrouter"
    fallback.call.side_effect = _make_refusal("openrouter")

    router = RefusalFallbackRouter(primary=primary, fallback=fallback)
    with pytest.raises(ProviderRefusalError) as exc_info:
        router.call(request)

    assert exc_info.value.refusal.provider == "openrouter"


def test_router_logs_fallback_also_refused() -> None:
    request = _make_request()
    primary = MagicMock()
    primary.provider_name = "anthropic"
    primary.call.side_effect = _make_refusal()
    fallback = MagicMock()
    fallback.provider_name = "openrouter"
    fallback.call.side_effect = _make_refusal("openrouter")
    log_fn = MagicMock()

    router = RefusalFallbackRouter(
        primary=primary, fallback=fallback, refusal_log_fn=log_fn
    )
    with pytest.raises(ProviderRefusalError):
        router.call(request)

    call_kwargs = log_fn.call_args.kwargs
    assert call_kwargs["outcome"] == "FALLBACK_ALSO_REFUSED"
    assert call_kwargs["fallback_provider"] == "openrouter"


def test_router_raises_call_error_when_fallback_errors() -> None:
    request = _make_request()
    primary = MagicMock()
    primary.provider_name = "anthropic"
    primary.call.side_effect = _make_refusal()
    fallback = MagicMock()
    fallback.provider_name = "openrouter"
    fallback.call.side_effect = ProviderCallError("timeout")

    router = RefusalFallbackRouter(primary=primary, fallback=fallback)
    with pytest.raises(ProviderCallError, match="timeout"):
        router.call(request)


def test_router_logs_fallback_error() -> None:
    request = _make_request()
    primary = MagicMock()
    primary.provider_name = "anthropic"
    primary.call.side_effect = _make_refusal()
    fallback = MagicMock()
    fallback.provider_name = "openrouter"
    fallback.call.side_effect = ProviderCallError("timeout")
    log_fn = MagicMock()

    router = RefusalFallbackRouter(
        primary=primary, fallback=fallback, refusal_log_fn=log_fn
    )
    with pytest.raises(ProviderCallError):
        router.call(request)

    call_kwargs = log_fn.call_args.kwargs
    assert call_kwargs["outcome"] == "FALLBACK_ERROR"
    assert call_kwargs["fallback_provider"] == "openrouter"
    assert call_kwargs["fallback_model"] is None


def test_router_suppresses_log_fn_exception() -> None:
    """_log swallows exceptions from refusal_log_fn so they never surface."""
    request = _make_request()
    primary = MagicMock()
    primary.provider_name = "anthropic"
    primary.call.side_effect = _make_refusal()
    log_fn = MagicMock(side_effect=RuntimeError("DB down"))

    router = RefusalFallbackRouter(
        primary=primary, fallback=None, refusal_log_fn=log_fn
    )
    with pytest.raises(ProviderRefusalError):
        router.call(request)  # must not raise RuntimeError
