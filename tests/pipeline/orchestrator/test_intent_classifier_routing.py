"""Round 6 remediation (PR #126 P1): Intent Classification must be routed
through the turn's selected ``TurnProviderBinding`` -- the same access path
every other pass uses -- not a standalone process-hosted key.

These tests use a real ``IntentClassifierService`` (not the ``FakeIntentClassifier``
test double used elsewhere in this package) wired to a *guard* caller that
raises if ever invoked directly, proving the orchestrator always supplies a
per-call provider-routed override. A spy ``ProviderAdapter`` records every
``ProviderCallRequest`` it receives so tests can assert routing, pass_id, and
that ``ANTHROPIC_API_KEY`` is never read by this path.
"""

from __future__ import annotations

import json
from uuid import uuid4

from afterworlds.entitlement.enums import ModelTier, PipelinePassId, RuntimeAccessPath
from afterworlds.models.enums import StoryMode
from afterworlds.pipeline.orchestrator.models import (
    CapabilityProfileAwareSafetyPolicy,
    PipelineDisposition,
)
from afterworlds.pipeline.orchestrator.service import OrchestratorService
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderTextPart,
)
from afterworlds.pipeline.provider._routing import (
    EligibleModelRoute,
    SafetyWhitelistStatus,
    TurnProviderBinding,
)
from afterworlds.services.intent_classifier import IntentClassifierService
from tests.pipeline.orchestrator.conftest import (
    FakeContextBuilder,
    FakeContradictionService,
    FakeExtractorService,
    FakePlannerService,
    FakeSafetyService,
    FakeWriterService,
    fixed_mode_resolver,
)

_SOJOURNER = uuid4()

_CANNED_CLASSIFICATION = json.dumps(
    {
        "intent_type": "in_character_action",
        "confidence": 0.9,
        "ambiguous": False,
        "secondary_intent": None,
    }
)


def _guard_caller(prompt: str) -> str:
    raise AssertionError(
        "IntentClassifierService's constructor-default model_caller was "
        "invoked -- the orchestrator must always supply a per-call "
        "provider-routed override."
    )


class _SpyProviderAdapter:
    """Records every ProviderCallRequest; returns a canned classification."""

    def __init__(self, provider_name: str = "spy-provider") -> None:
        self.provider_name = provider_name
        self.calls: list[ProviderCallRequest] = []

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        self.calls.append(request)
        return ProviderCallResult(
            pass_id=request.pass_id,
            provider_name=self.provider_name,
            model_identifier="spy-model",
            model_tier=ModelTier.HAIKU,
            content_parts=[ProviderTextPart(text=_CANNED_CLASSIFICATION)],
            input_token_count=10,
            output_token_count=5,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
            latency_ms=1,
        )


class _FixedResolver:
    """Duck-typed ProviderResolver yielding one fixed TurnProviderBinding."""

    def __init__(self, adapter: _SpyProviderAdapter, access_path: RuntimeAccessPath):
        route = EligibleModelRoute(
            provider_name=adapter.provider_name,
            model_identifier="spy-model",
            whitelist_status=SafetyWhitelistStatus.NOT_WHITELISTED,
            supports_required_capabilities=False,
        )
        self._binding = TurnProviderBinding(
            adapter=adapter,
            primary_writer_route=route,
            eligible_writer_routes=(route,),
            access_path=access_path,
        )

    def resolve_for_turn(self, access_path: object, sojourner_id: object) -> object:
        return self._binding


def _freeform_branching_session(_story_id):  # type: ignore[no-untyped-def]
    from afterworlds.models.enums import InteractionStyle, PacingStage
    from afterworlds.models.session import BranchingPlayStatus, BranchingSessionState

    return BranchingSessionState(
        story_id=_story_id,
        pacing_stage=PacingStage.ESCALATION,
        interaction_style=InteractionStyle.FREEFORM_ONLY,
        play_status=BranchingPlayStatus.IN_PLAY,
    )


def _make_orchestrator_with_adapter(
    session_factory, adapter: _SpyProviderAdapter, access_path: RuntimeAccessPath
) -> OrchestratorService:
    return OrchestratorService(
        intent_classifier=IntentClassifierService(_guard_caller),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_FixedResolver(adapter, access_path),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.BRANCHING),
        branching_session_resolver=_freeform_branching_session,
    )


class TestIntentClassificationRoutesThroughSelectedAdapter:
    def test_classification_uses_per_call_override_not_constructor_default(
        self, session_factory, seeded_story
    ) -> None:
        """The guard caller must never be invoked -- proves the orchestrator
        always supplies a provider-routed model_caller override."""
        story_id, node_id = seeded_story
        adapter = _SpyProviderAdapter()
        orch = _make_orchestrator_with_adapter(
            session_factory, adapter, RuntimeAccessPath.HOSTED
        )
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert result.disposition is PipelineDisposition.DELIVERED
        assert len(adapter.calls) == 1

    def test_classification_request_uses_intent_classifier_pass_id(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        adapter = _SpyProviderAdapter()
        orch = _make_orchestrator_with_adapter(
            session_factory, adapter, RuntimeAccessPath.HOSTED
        )
        orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert adapter.calls[0].pass_id is PipelinePassId.INTENT_CLASSIFIER

    def test_delivered_result_carries_intent_classifier_usage(
        self, session_factory, seeded_story
    ) -> None:
        """Round 8 remediation (PR #126 P1): the provider-routed classifier
        call's usage must land on the returned OrchestrationResult so hosted
        settlement can account for it."""
        story_id, node_id = seeded_story
        adapter = _SpyProviderAdapter()
        orch = _make_orchestrator_with_adapter(
            session_factory, adapter, RuntimeAccessPath.HOSTED
        )
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert result.disposition is PipelineDisposition.DELIVERED
        usage = result.intent_classifier_usage
        assert usage is not None
        assert usage.pass_id is PipelinePassId.INTENT_CLASSIFIER
        assert usage.provider == "spy-provider"
        assert usage.model_identifier == "spy-model"
        assert usage.model_tier is ModelTier.HAIKU
        assert usage.input_token_count == 10
        assert usage.output_token_count == 5

    def test_byok_delivered_result_carries_byok_adapter_usage(
        self, session_factory, seeded_story, monkeypatch
    ) -> None:
        """Regression: a BYOK-selected turn's classifier usage still comes
        from the BYOK adapter, not a hidden hosted one."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        story_id, node_id = seeded_story
        adapter = _SpyProviderAdapter(provider_name="byok-adapter")
        orch = _make_orchestrator_with_adapter(
            session_factory, adapter, RuntimeAccessPath.BYOK
        )
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.BYOK
        )
        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.intent_classifier_usage is not None
        assert result.intent_classifier_usage.provider == "byok-adapter"

    def test_byok_selected_turn_does_not_require_process_anthropic_api_key(
        self, session_factory, seeded_story, monkeypatch
    ) -> None:
        """BYOK-selected turn must not fail before classification solely
        because a process-hosted ANTHROPIC_API_KEY is absent."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        story_id, node_id = seeded_story
        adapter = _SpyProviderAdapter(provider_name="byok-adapter")
        orch = _make_orchestrator_with_adapter(
            session_factory, adapter, RuntimeAccessPath.BYOK
        )
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.BYOK
        )
        assert result.disposition is PipelineDisposition.DELIVERED
        assert len(adapter.calls) == 1

    def test_byok_turn_uses_byok_resolved_adapter_not_a_hidden_hosted_one(
        self, session_factory, seeded_story, monkeypatch
    ) -> None:
        """No second, hidden provider resolver: the BYOK-selected adapter is
        the one that actually receives the classification call."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        story_id, node_id = seeded_story
        byok_adapter = _SpyProviderAdapter(provider_name="byok-adapter")
        orch = _make_orchestrator_with_adapter(
            session_factory, byok_adapter, RuntimeAccessPath.BYOK
        )
        orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.BYOK
        )
        assert len(byok_adapter.calls) == 1
        assert byok_adapter.calls[0].pass_id is PipelinePassId.INTENT_CLASSIFIER

    def test_hosted_selected_turn_still_classifies_through_hosted_resolver(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        hosted_adapter = _SpyProviderAdapter(provider_name="hosted-adapter")
        orch = _make_orchestrator_with_adapter(
            session_factory, hosted_adapter, RuntimeAccessPath.HOSTED
        )
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert result.disposition is PipelineDisposition.DELIVERED
        assert len(hosted_adapter.calls) == 1

    def test_classifier_never_reads_anthropic_api_key_env_directly(
        self, session_factory, seeded_story, monkeypatch
    ) -> None:
        """Regression: even with no ANTHROPIC_API_KEY set at all, BYOK
        classification succeeds via the spy adapter -- the classifier path
        never reads that env var directly (it would raise/differ if it did,
        since _guard_caller raises on any direct invocation)."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        story_id, node_id = seeded_story
        adapter = _SpyProviderAdapter()
        orch = _make_orchestrator_with_adapter(
            session_factory, adapter, RuntimeAccessPath.BYOK
        )
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.BYOK
        )
        assert result.disposition is PipelineDisposition.DELIVERED

    def test_provider_refusal_from_classifier_maps_to_refused_by_provider(
        self, session_factory, seeded_story
    ) -> None:
        """Round 7 remediation (PR #126 P2): a provider refusal during
        classification must preserve the refusal (REFUSED_BY_PROVIDER,
        provider_refusal populated), not collapse into an
        infrastructure-looking PIPELINE_ERROR that drops the refusal
        details."""
        from afterworlds.pipeline._refusal import (
            PassIdentifier,
            ProviderRefusal,
            ProviderRefusalError,
        )

        class _RefusingAdapter:
            provider_name = "refusing-adapter"

            def call(self, request: ProviderCallRequest) -> ProviderCallResult:
                raise ProviderRefusalError(
                    ProviderRefusal(
                        provider="refusing-adapter",
                        pass_identifier=PassIdentifier.INTENT_CLASSIFIER,
                        coarse_reason="synthetic refusal",
                    )
                )

        story_id, node_id = seeded_story
        orch = _make_orchestrator_with_adapter(
            session_factory, _RefusingAdapter(), RuntimeAccessPath.HOSTED  # type: ignore[arg-type]
        )
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert result.disposition is PipelineDisposition.REFUSED_BY_PROVIDER
        assert result.provider_refusal is not None
        assert (
            result.provider_refusal.pass_identifier is PassIdentifier.INTENT_CLASSIFIER
        )
        assert result.pipeline_error_summary is None
        assert result.turn_id is None
        assert result.delivered_output is None
        # No provider result was ever returned (the adapter raised before
        # producing one), so no usage exists to carry.
        assert result.intent_classifier_usage is None

    def test_non_refusal_classifier_error_still_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:
        """Parser/schema/transport/unexpected classifier failures continue
        to map to typed PIPELINE_ERROR, unchanged by the refusal-parity fix."""

        class _BoomAdapter:
            provider_name = "boom-adapter"

            def call(self, request: ProviderCallRequest) -> ProviderCallResult:
                raise RuntimeError("synthetic transport failure")

        story_id, node_id = seeded_story
        orch = _make_orchestrator_with_adapter(
            session_factory, _BoomAdapter(), RuntimeAccessPath.HOSTED  # type: ignore[arg-type]
        )
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.provider_refusal is None
        # The adapter raised before returning a ProviderCallResult, so no
        # usage exists to carry -- distinct from a post-call parse failure.
        assert result.intent_classifier_usage is None

    def test_refusal_prevents_downstream_passes_from_running(
        self, session_factory, seeded_story
    ) -> None:
        """A classifier refusal must stop the turn immediately -- no
        Planner/Writer/Extractor/Contradiction call after it."""
        from afterworlds.pipeline._refusal import (
            PassIdentifier,
            ProviderRefusal,
            ProviderRefusalError,
        )

        class _RefusingAdapter:
            provider_name = "refusing-adapter"

            def call(self, request: ProviderCallRequest) -> ProviderCallResult:
                raise ProviderRefusalError(
                    ProviderRefusal(
                        provider="refusing-adapter",
                        pass_identifier=PassIdentifier.INTENT_CLASSIFIER,
                        coarse_reason="synthetic refusal",
                    )
                )

        story_id, node_id = seeded_story
        planner = FakePlannerService()
        writer = FakeWriterService()
        extractor = FakeExtractorService()
        contradiction = FakeContradictionService()
        orch = OrchestratorService(
            intent_classifier=IntentClassifierService(_guard_caller),
            context_builder=FakeContextBuilder(),
            safety_service=FakeSafetyService(),
            planner_service=planner,
            writer_service=writer,
            extractor_service=extractor,
            contradiction_service=contradiction,
            session_factory=session_factory,
            safety_policy=CapabilityProfileAwareSafetyPolicy(),
            provider_resolver=_FixedResolver(
                _RefusingAdapter(), RuntimeAccessPath.HOSTED  # type: ignore[arg-type]
            ),
            mode_resolver=fixed_mode_resolver(StoryMode.BRANCHING),
            branching_session_resolver=_freeform_branching_session,
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert result.disposition is PipelineDisposition.REFUSED_BY_PROVIDER
        assert planner.calls == []
        assert writer.calls == []
        assert extractor.calls == []
        assert contradiction.calls == []
