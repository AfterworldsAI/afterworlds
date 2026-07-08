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

    def test_provider_refusal_from_classifier_fails_closed_as_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:
        """No classifier-specific refusal routing exists -- a provider
        refusal during classification must still fail closed as
        PIPELINE_ERROR (Issue 12c's exhaustive terminal-state contract),
        not escape orchestrate_turn as a raw exception."""
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
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
