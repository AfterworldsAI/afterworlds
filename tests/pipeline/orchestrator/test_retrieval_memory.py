"""Orchestrator-level integration tests for Retrieval Memory ingestion.

CRD Issue 18 / ADR-018. Covers the ingestion gate (§6/D6/D7), the mandatory
RPG turn-retrieval-marker write (D6, typed PIPELINE_ERROR on failure), and
the Writing durable setup-turn guard (D6).
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.models.enums import (
    IntentType,
    RpgTurnRetrievalCategory,
    StoryMode,
    WritingCanonEligibility,
    WritingWorkProductKind,
)
from afterworlds.persistence.crud.node import get_turn
from afterworlds.persistence.crud.retrieval import get_rpg_turn_retrieval_marker
from afterworlds.pipeline.orchestrator.models import (
    CapabilityProfileAwareSafetyPolicy,
    PipelineDisposition,
)
from afterworlds.pipeline.orchestrator.service import OrchestratorService
from afterworlds.pipeline.provider._routing import (
    EligibleModelRoute,
    TurnProviderBinding,
)
from afterworlds.pipeline.safety.models import (
    SafetyCategory,
    SafetyConcern,
    SafetyReport,
    SafetyResult,
    SafetyTarget,
)
from afterworlds.pipeline.writing.models import WritingTurnRequest
from tests.pipeline.orchestrator.conftest import (
    FakeContextBuilder,
    FakeContradictionService,
    FakeExtractorService,
    FakeIntentClassifier,
    FakePlannerService,
    FakeSafetyService,
    FakeWriterService,
    fixed_mode_resolver,
    make_intent,
)
from tests.pipeline.orchestrator.test_service import (
    _make_orchestrator_with_adjudication,
    _seed_writing_story_setup_wss,
)

_SOJOURNER = uuid4()


class _FakeProviderAdapter:
    provider_name = "fake-anthropic"


def _make_fake_resolver() -> object:
    from afterworlds.pipeline.provider._routing import SafetyWhitelistStatus

    route = EligibleModelRoute(
        provider_name="fake-anthropic",
        model_identifier="fake-anthropic:claude-test",
        whitelist_status=SafetyWhitelistStatus.NOT_WHITELISTED,
        supports_required_capabilities=False,
    )
    binding = TurnProviderBinding(
        adapter=_FakeProviderAdapter(),
        primary_writer_route=route,
        eligible_writer_routes=(route,),
        access_path=RuntimeAccessPath.HOSTED,
    )

    class _Resolver:
        def resolve_for_turn(self, access_path: object, sojourner_id: object) -> object:
            return binding

    return _Resolver()


def _block_safety(target: SafetyTarget) -> SafetyResult:
    return SafetyResult(
        report=SafetyReport(
            concerns=[
                SafetyConcern(
                    category=SafetyCategory.OTHER,
                    description="synthetic",
                    evidence_summary="test",
                )
            ]
        ),
        target=target,
    )


class _FakeRetrievalWriteService:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def ingest_turn(
        self,
        story_id: UUID,
        turn_id: UUID,
        node_id: UUID | None,
        mode: str,
        delivered_output: str,
        created_at: str,
    ) -> None:
        self.calls.append(
            (story_id, turn_id, node_id, mode, delivered_output, created_at)
        )


def _make_branching_orch_with_retrieval(
    session_factory: object,
    retrieval_write_service: _FakeRetrievalWriteService,
    *,
    safety_output: SafetyResult | None = None,
) -> OrchestratorService:
    from afterworlds.models.enums import InteractionStyle, PacingStage
    from afterworlds.models.session import BranchingPlayStatus, BranchingSessionState

    def _branching_resolver(story_id: UUID) -> BranchingSessionState:
        return BranchingSessionState(
            story_id=story_id,
            pacing_stage=PacingStage.ESCALATION,
            interaction_style=InteractionStyle.FREEFORM_ONLY,
            play_status=BranchingPlayStatus.IN_PLAY,
        )

    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(
            make_intent(IntentType.IN_CHARACTER_ACTION)
        ),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(output_verdict=safety_output),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.BRANCHING),
        branching_session_resolver=_branching_resolver,
        retrieval_write_service=retrieval_write_service,
    )


class TestIngestionGateBranching:
    def test_delivered_turn_is_ingested_exactly_once(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        story_id, node_id = seeded_story
        fake_retrieval = _FakeRetrievalWriteService()
        orch = _make_branching_orch_with_retrieval(session_factory, fake_retrieval)

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert len(fake_retrieval.calls) == 1
        called_story_id, called_turn_id, *_ = fake_retrieval.calls[0]
        assert called_story_id == story_id
        assert called_turn_id == result.turn_id

    def test_blocked_input_safety_never_ingests(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        story_id, node_id = seeded_story
        fake_retrieval = _FakeRetrievalWriteService()
        orch = _make_branching_orch_with_retrieval(session_factory, fake_retrieval)
        # Force input safety block via the FakeSafetyService input_verdict.
        orch._safety_service.input_verdict = _block_safety(  # type: ignore[attr-defined]
            SafetyTarget.INPUT
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "harmful?", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.BLOCKED_INPUT_SAFETY
        assert fake_retrieval.calls == []

    def test_blocked_output_safety_rolls_back_and_never_ingests(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        story_id, node_id = seeded_story
        fake_retrieval = _FakeRetrievalWriteService()
        orch = _make_branching_orch_with_retrieval(
            session_factory,
            fake_retrieval,
            safety_output=_block_safety(SafetyTarget.OUTPUT),
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.BLOCKED_OUTPUT_SAFETY
        assert result.turn_id is None
        assert fake_retrieval.calls == []


class TestRpgTurnRetrievalMarker:
    def test_ordinary_narrative_turn_gets_marker_and_is_ingested(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        story_id, node_id = seeded_story
        fake_retrieval = _FakeRetrievalWriteService()
        orch = _make_orchestrator_with_adjudication(session_factory)
        orch._retrieval_write_service = fake_retrieval  # type: ignore[attr-defined]

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I attack the goblin.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.turn_id is not None
        with session_factory() as read_session:  # type: ignore[operator]
            category = get_rpg_turn_retrieval_marker(read_session, result.turn_id)
        assert category is RpgTurnRetrievalCategory.ORDINARY_NARRATIVE
        assert len(fake_retrieval.calls) == 1

    def test_setup_turn_gets_setup_confirmation_marker_and_is_not_ingested(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        story_id, node_id = seeded_story
        fake_retrieval = _FakeRetrievalWriteService()
        orch = _make_orchestrator_with_adjudication(
            session_factory, play_status_setup=True
        )
        orch._retrieval_write_service = fake_retrieval  # type: ignore[attr-defined]

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I roll up my character.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.turn_id is not None
        with session_factory() as read_session:  # type: ignore[operator]
            category = get_rpg_turn_retrieval_marker(read_session, result.turn_id)
        assert category is RpgTurnRetrievalCategory.SETUP_CONFIRMATION
        assert fake_retrieval.calls == []

    def test_marker_write_failure_is_mandatory_pipeline_error(
        self, session_factory, seeded_story, monkeypatch: pytest.MonkeyPatch
    ) -> None:  # type: ignore[no-untyped-def]
        """ADR-018 D6: the marker write is mandatory, not best-effort — unlike
        the Writing metadata block, a failure here must map to typed
        PIPELINE_ERROR and roll back, never commit markerless."""
        story_id, node_id = seeded_story
        orch = _make_orchestrator_with_adjudication(session_factory)

        def _raise(*args: object, **kwargs: object) -> None:
            raise RuntimeError("synthetic marker write failure")

        monkeypatch.setattr(
            "afterworlds.persistence.crud.retrieval.create_rpg_turn_retrieval_marker",
            _raise,
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I attack the goblin.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.turn_id is None
        assert result.delivered_output is None


class TestWritingSetupTurnGuard:
    def test_setup_turn_request_override_is_forced_non_canon(
        self, session_factory, session
    ) -> None:  # type: ignore[no-untyped-def]
        """ADR-018 D6: a request carrying a prose-like work_product_kind +
        EXTRACTOR_ELIGIBLE taken during SETUP must be persisted as
        SETUP_CONFIRMATION/NON_CANON_SUPPORT regardless of the request."""
        story_id, node_id = _seed_writing_story_setup_wss(session)
        fake_retrieval = _FakeRetrievalWriteService()

        from afterworlds.models.session import WritingSessionState

        def _resolver(sid: UUID) -> WritingSessionState:
            return WritingSessionState(story_id=sid)  # SETUP, no persona

        from tests.pipeline.orchestrator.test_service import _make_writing_gate_orch

        orch = _make_writing_gate_orch(session_factory, writing_resolver=_resolver)
        orch._retrieval_write_service = fake_retrieval  # type: ignore[attr-defined]

        writing_turn_request = WritingTurnRequest(
            work_product_kind=WritingWorkProductKind.DRAFT_PROSE,
            canon_eligibility_override=WritingCanonEligibility.EXTRACTOR_ELIGIBLE,
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "Continue the draft.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
            writing_turn_request=writing_turn_request,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.turn_id is not None
        with session_factory() as read_session:  # type: ignore[operator]
            turn = get_turn(read_session, result.turn_id)
        assert turn is not None
        assert turn.mode_metadata is not None
        assert (
            turn.mode_metadata.work_product_kind  # type: ignore[union-attr]
            == WritingWorkProductKind.SETUP_CONFIRMATION.value
        )
        assert (
            turn.mode_metadata.canon_eligibility  # type: ignore[union-attr]
            == WritingCanonEligibility.NON_CANON_SUPPORT.value
        )
        # Ineligible per the durable guard: never ingested despite the
        # request having asked for EXTRACTOR_ELIGIBLE.
        assert fake_retrieval.calls == []
