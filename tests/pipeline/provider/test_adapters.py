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
from afterworlds.pipeline.provider.adapters._anthropic import (
    AnthropicCapabilityProfile,
    _classify_stop_reason_and_text,
)
from afterworlds.pipeline.provider.adapters._fallback import RefusalFallbackRouter
from afterworlds.pipeline.provider.adapters._openrouter import _detect_refusal
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
    assert p.get_factor("anthropic", ModelTier.SONNET) == Decimal("1.0")


def test_anthropic_normalization_factor_wrong_provider() -> None:
    p = AnthropicNormalizationFactorProvider()
    with pytest.raises(ValueError, match="unexpected provider"):
        p.get_factor("openrouter", ModelTier.SONNET)


def test_openrouter_normalization_factor_happy() -> None:
    p = OpenRouterNormalizationFactorProvider()
    assert p.get_factor("openrouter", ModelTier.SONNET) == Decimal("1.0")


def test_openrouter_normalization_factor_wrong_provider() -> None:
    p = OpenRouterNormalizationFactorProvider()
    with pytest.raises(ValueError, match="unexpected provider"):
        p.get_factor("anthropic", ModelTier.SONNET)


def test_compute_deduction_with_anthropic_normalization_provider() -> None:
    """AnthropicNormalizationFactorProvider satisfies protocol — no TypeError."""
    from afterworlds.entitlement.models import PassUsageSnapshot, TurnCostPolicyConfig
    from afterworlds.entitlement.policy import TurnCostPolicy

    snap = PassUsageSnapshot(
        pass_id=PipelinePassId.WRITER,
        model_tier=ModelTier.SONNET,
        provider="anthropic",
        input_tokens=1000,
        output_tokens=500,
    )
    policy = TurnCostPolicy(config=TurnCostPolicyConfig())
    result = policy.compute_deduction(
        [snap], normalization=AnthropicNormalizationFactorProvider()
    )
    assert result > 0


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


# ---------------------------------------------------------------------------
# Refusal classification — short valid output must NOT be classified as refusal
# ---------------------------------------------------------------------------


def test_anthropic_short_end_turn_not_refusal() -> None:
    """'She nods.' with end_turn is valid output, not a refusal."""
    assert _classify_stop_reason_and_text("end_turn", "She nods.") is None


def test_anthropic_short_yes_not_refusal() -> None:
    """'Yes.' is valid terse output, not a refusal."""
    assert _classify_stop_reason_and_text("end_turn", "Yes.") is None


def test_anthropic_rpg_factual_short_not_refusal() -> None:
    """RPG factual answer under 80 chars is valid output, not a refusal."""
    assert (
        _classify_stop_reason_and_text("end_turn", "No, they are holding shovels.")
        is None
    )


def test_anthropic_refusal_phrase_classified_as_content_policy() -> None:
    """A response containing a known refusal phrase is classified CONTENT_POLICY."""
    result = _classify_stop_reason_and_text(
        "end_turn", "I cannot assist with that request."
    )
    assert result == RefusalCategory.CONTENT_POLICY


def test_anthropic_normal_stop_reason_no_phrase_not_refusal() -> None:
    """'stop_sequence' stop with ordinary prose is not a refusal."""
    assert (
        _classify_stop_reason_and_text("stop_sequence", "The door creaks open.") is None
    )


def test_stop_reason_refusal_no_stop_details_returns_unknown() -> None:
    """stop_reason='refusal' with no stop_details → UNKNOWN (no phrase match needed)."""
    result = _classify_stop_reason_and_text("refusal", "")
    assert result == RefusalCategory.UNKNOWN


def test_stop_reason_refusal_unfamiliar_text_returns_unknown() -> None:
    """stop_reason='refusal' with non-matching text → UNKNOWN, not None."""
    result = _classify_stop_reason_and_text("refusal", "The door is closed.")
    assert result == RefusalCategory.UNKNOWN


def test_stop_reason_refusal_cyber_category_returns_content_policy() -> None:
    """stop_details.category='cyber' with stop_reason='refusal' → CONTENT_POLICY."""
    from unittest.mock import MagicMock as _MagicMock

    details = _MagicMock()
    details.category = "cyber"
    result = _classify_stop_reason_and_text("refusal", "", stop_details=details)
    assert result == RefusalCategory.CONTENT_POLICY


def test_stop_reason_refusal_bio_category_returns_content_policy() -> None:
    """stop_details.category='bio' with stop_reason='refusal' → CONTENT_POLICY."""
    from unittest.mock import MagicMock as _MagicMock

    details = _MagicMock()
    details.category = "bio"
    result = _classify_stop_reason_and_text("refusal", "", stop_details=details)
    assert result == RefusalCategory.CONTENT_POLICY


def test_stop_reason_refusal_none_stop_details_returns_unknown() -> None:
    """Explicit stop_details=None with stop_reason='refusal' → UNKNOWN."""
    result = _classify_stop_reason_and_text("refusal", "", stop_details=None)
    assert result == RefusalCategory.UNKNOWN


def test_end_turn_no_phrase_still_not_refusal() -> None:
    """Preserve: end_turn + ordinary prose is still not a refusal."""
    result = _classify_stop_reason_and_text("end_turn", "She nods.")
    assert result is None


def test_parse_response_refusal_stop_reason_no_content_raises_refusal_error() -> None:
    """stop_reason='refusal' with empty content → ProviderRefusalError not CallError."""
    from anthropic.types import Message, Usage

    from afterworlds.pipeline.provider.adapters._anthropic import AnthropicDirectAdapter

    msg = Message(
        id="msg_refusal_empty",
        content=[],
        model="claude-haiku-4-5-20251001",
        role="assistant",
        stop_reason="refusal",
        stop_details=None,
        type="message",
        usage=Usage(input_tokens=10, output_tokens=0),
    )
    parts, cat, coarse = AnthropicDirectAdapter._parse_response(msg)
    assert cat == RefusalCategory.UNKNOWN
    assert parts == []


def test_parse_response_refusal_stop_reason_with_text_returns_refusal() -> None:
    """stop_reason='refusal' with text that does not match phrases → still UNKNOWN."""
    from anthropic.types import Message, TextBlock, Usage

    from afterworlds.pipeline.provider.adapters._anthropic import AnthropicDirectAdapter

    msg = Message(
        id="msg_refusal_text",
        content=[TextBlock(type="text", text="The door is closed.")],
        model="claude-haiku-4-5-20251001",
        role="assistant",
        stop_reason="refusal",
        stop_details=None,
        type="message",
        usage=Usage(input_tokens=10, output_tokens=5),
    )
    parts, cat, coarse = AnthropicDirectAdapter._parse_response(msg)
    assert cat == RefusalCategory.UNKNOWN
    assert coarse == "The door is closed."


def test_parse_response_refusal_stop_reason_cyber_category_content_policy() -> None:
    """stop_reason='refusal' + stop_details.category='cyber' → CONTENT_POLICY."""
    from anthropic.types import Message, RefusalStopDetails, Usage

    from afterworlds.pipeline.provider.adapters._anthropic import AnthropicDirectAdapter

    msg = Message(
        id="msg_refusal_cyber",
        content=[],
        model="claude-haiku-4-5-20251001",
        role="assistant",
        stop_reason="refusal",
        stop_details=RefusalStopDetails(type="refusal", category="cyber"),
        type="message",
        usage=Usage(input_tokens=10, output_tokens=0),
    )
    parts, cat, coarse = AnthropicDirectAdapter._parse_response(msg)
    assert cat == RefusalCategory.CONTENT_POLICY


def test_parse_response_end_turn_normal_prose_not_refusal() -> None:
    """end_turn + normal prose is not classified as a refusal."""
    from anthropic.types import Message, TextBlock, Usage

    from afterworlds.pipeline.provider.adapters._anthropic import AnthropicDirectAdapter

    msg = Message(
        id="msg_normal",
        content=[TextBlock(type="text", text="She nods and steps forward.")],
        model="claude-haiku-4-5-20251001",
        role="assistant",
        stop_reason="end_turn",
        stop_details=None,
        type="message",
        usage=Usage(input_tokens=20, output_tokens=8),
    )
    parts, cat, coarse = AnthropicDirectAdapter._parse_response(msg)
    assert cat is None
    assert len(parts) == 1


def test_openrouter_short_text_not_refusal() -> None:
    """OpenRouter short text 'She nods.' is valid output, not a refusal."""
    assert _detect_refusal("She nods.") is None


def test_openrouter_refusal_phrase_classified_as_content_policy() -> None:
    """OpenRouter response with refusal phrase is classified CONTENT_POLICY."""
    assert (
        _detect_refusal("I'm unable to help with that.")
        == RefusalCategory.CONTENT_POLICY
    )


# ---------------------------------------------------------------------------
# RefusalFallbackRouter — Safety pass exclusion from fallback (Fix 1)
# ---------------------------------------------------------------------------


def _make_safety_request(pass_id: PipelinePassId) -> ProviderCallRequest:
    return ProviderCallRequest(
        pass_id=pass_id,
        rendered_blocks=[RenderedBlock(text="Evaluate this.")],
        max_output_tokens=256,
    )


def test_input_safety_refusal_not_forwarded_to_fallback() -> None:
    """INPUT_SAFETY refusal: fallback NOT tried, log row written, error re-raised."""
    request = _make_safety_request(PipelinePassId.INPUT_SAFETY)
    primary = MagicMock()
    primary.provider_name = "anthropic"
    primary.call.side_effect = _make_refusal()
    fallback = MagicMock()
    fallback.provider_name = "openrouter"
    log_fn = MagicMock()

    router = RefusalFallbackRouter(
        primary=primary, fallback=fallback, refusal_log_fn=log_fn
    )
    with pytest.raises(ProviderRefusalError):
        router.call(request)

    fallback.call.assert_not_called()
    log_fn.assert_called_once()
    _, kwargs = log_fn.call_args
    assert kwargs["outcome"] == "NO_FALLBACK_CONFIGURED"
    assert kwargs["fallback_provider"] is None


def test_output_safety_refusal_not_forwarded_to_fallback() -> None:
    """OUTPUT_SAFETY refusal: fallback NOT tried, log row written, error re-raised."""
    request = _make_safety_request(PipelinePassId.OUTPUT_SAFETY)
    primary = MagicMock()
    primary.provider_name = "anthropic"
    primary.call.side_effect = _make_refusal()
    fallback = MagicMock()
    fallback.provider_name = "openrouter"
    log_fn = MagicMock()

    router = RefusalFallbackRouter(
        primary=primary, fallback=fallback, refusal_log_fn=log_fn
    )
    with pytest.raises(ProviderRefusalError):
        router.call(request)

    fallback.call.assert_not_called()
    log_fn.assert_called_once()
    _, kwargs = log_fn.call_args
    assert kwargs["outcome"] == "NO_FALLBACK_CONFIGURED"
    assert kwargs["fallback_provider"] is None


def test_narrative_pass_refusal_still_uses_fallback() -> None:
    """WRITER refusal: fallback IS invoked (existing behavior preserved)."""
    request = _make_request()  # pass_id=WRITER
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
    fallback.call.assert_called_once()


# ---------------------------------------------------------------------------
# AnthropicCapabilityProfile.tier_for — Finding 2 (CRD Issue 14a)
# ---------------------------------------------------------------------------


def test_tier_for_default_planner_returns_haiku() -> None:
    """No overrides: Planner pass returns HAIKU (default profile)."""
    profile = AnthropicCapabilityProfile()
    assert profile.tier_for(PipelinePassId.PLANNER) is ModelTier.HAIKU


def test_tier_for_default_writer_returns_sonnet() -> None:
    """No overrides: Writer pass returns SONNET (default profile)."""
    profile = AnthropicCapabilityProfile()
    assert profile.tier_for(PipelinePassId.WRITER) is ModelTier.SONNET


def test_tier_for_override_writer_to_haiku_returns_haiku() -> None:
    """Writer overridden to a haiku model → tier_for returns HAIKU."""
    profile = AnthropicCapabilityProfile(
        pass_model_overrides={PipelinePassId.WRITER: "claude-haiku-4-5-20251001"}
    )
    assert profile.tier_for(PipelinePassId.WRITER) is ModelTier.HAIKU
    assert profile.model_for(PipelinePassId.WRITER) == "claude-haiku-4-5-20251001"


def test_tier_for_override_planner_to_sonnet_returns_sonnet() -> None:
    """Planner overridden to a sonnet model → tier_for returns SONNET."""
    profile = AnthropicCapabilityProfile(
        pass_model_overrides={PipelinePassId.PLANNER: "claude-sonnet-4-5"}
    )
    assert profile.tier_for(PipelinePassId.PLANNER) is ModelTier.SONNET
    assert profile.model_for(PipelinePassId.PLANNER) == "claude-sonnet-4-5"


def test_tier_for_unknown_override_raises_provider_config_error() -> None:
    """Override with an unclassifiable model id → ProviderConfigError (fail closed)."""
    profile = AnthropicCapabilityProfile(
        pass_model_overrides={PipelinePassId.WRITER: "gpt-4o"}
    )
    with pytest.raises(ProviderConfigError, match="Cannot classify model tier"):
        profile.tier_for(PipelinePassId.WRITER)


def test_model_for_and_tier_for_agree_for_overridden_pass() -> None:
    """model_for and tier_for are consistent when an override is set."""
    profile = AnthropicCapabilityProfile(
        pass_model_overrides={PipelinePassId.EXTRACTOR: "claude-haiku-4-5-20251001"}
    )
    model = profile.model_for(PipelinePassId.EXTRACTOR)
    tier = profile.tier_for(PipelinePassId.EXTRACTOR)
    assert "haiku" in model.lower()
    assert tier is ModelTier.HAIKU


def test_router_fallback_not_triggered_on_short_valid_output() -> None:
    """Fallback is NOT triggered when primary returns a short but valid result."""
    request = _make_request()
    short_result = ProviderCallResult(
        pass_id=PipelinePassId.WRITER,
        provider_name="anthropic",
        model_identifier="claude-sonnet-4-6",
        model_tier=ModelTier.SONNET,
        content_parts=[ProviderTextPart(text="She nods.")],
        input_token_count=100,
        output_token_count=3,
        cache_read_token_count=None,
        cache_creation_token_count=None,
        cache_warmed=False,
        latency_ms=150,
    )
    primary = MagicMock()
    primary.provider_name = "anthropic"
    primary.call.return_value = short_result
    fallback = MagicMock()
    fallback.provider_name = "openrouter"

    router = RefusalFallbackRouter(primary=primary, fallback=fallback)
    result = router.call(request)

    assert result is short_result
    fallback.call.assert_not_called()
