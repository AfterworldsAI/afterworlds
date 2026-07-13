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
    DiceHandling,
    IntentType,
    RpgPlayStatus,
    RpgTurnRetrievalCategory,
    StoryMode,
    WritingCanonEligibility,
    WritingWorkProductKind,
)
from afterworlds.models.session import RpgSessionState
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
    _make_rpg_session_and_sheet,
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


def _make_rpg_orch_without_adjudication(
    session_factory: object,
    retrieval_write_service: _FakeRetrievalWriteService | None = None,
    *,
    play_status_setup: bool = False,
) -> OrchestratorService:
    """RPG orchestrator with a session/sheet resolver wired but NO RPG
    adjudication service -- the exact shape Codex #119 P2 flagged: a story
    can have Retrieval Memory enabled before adjudication is wired, and the
    mandatory turn-retrieval-marker classification must still resolve
    rpg_play_status correctly rather than defaulting to ORDINARY_NARRATIVE."""
    from afterworlds.models.enums import DiceHandling, RpgPlayStatus
    from afterworlds.models.session import RpgSessionState

    session_state, sheet = _make_rpg_session_and_sheet()
    if play_status_setup:
        session_state = RpgSessionState(
            story_id=session_state.story_id,
            character_sheet_id=session_state.character_sheet_id,
            dice_handling=DiceHandling.AI_ROLLS,
            play_status=RpgPlayStatus.SETUP,
        )

    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(make_intent()),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.RPG),
        rpg_session_sheet_resolver=lambda _sid: (session_state, sheet),  # type: ignore[arg-type]
        # rpg_adjudication_service intentionally absent.
        retrieval_write_service=retrieval_write_service,
    )


def _make_rpg_orch_with_neither_adjudication_nor_resolver(
    session_factory: object,
) -> OrchestratorService:
    """RPG mode active, but nothing can resolve rpg_play_status at all --
    the marker-classification fail-closed case (Codex #119 P2)."""
    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(make_intent()),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.RPG),
        # Neither rpg_adjudication_service nor rpg_session_sheet_resolver wired.
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


class _SpyRetrievalQueryBuilder:
    """Records the args OrchestratorService passes to build_query_request."""

    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def build_query_request(
        self,
        story_id: UUID,
        current_input: str,
        story_mode: StoryMode,
        classified_intent: object,
    ) -> object:
        from afterworlds.models.retrieval import RetrievalQueryRequest

        self.calls.append((story_id, current_input, story_mode, classified_intent))
        return RetrievalQueryRequest(story_id=story_id, query_text=current_input)


def _make_branching_orch_with_retrieval(
    session_factory: object,
    retrieval_write_service: _FakeRetrievalWriteService,
    *,
    safety_output: SafetyResult | None = None,
    retrieval_query_builder: object | None = None,
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
        retrieval_query_builder=retrieval_query_builder,  # type: ignore[arg-type]
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


class TestOrchestratorPassesClassifiedIntentToQueryBuilder:
    """Codex review (PR #119) round 4: the orchestrator must thread the
    real, already-computed IntentClassificationResult into
    RetrievalQueryBuilder.build_query_request -- not omit it, and not
    synthesize a separate one."""

    def test_real_classified_intent_is_passed(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        story_id, node_id = seeded_story
        fake_retrieval = _FakeRetrievalWriteService()
        spy_query_builder = _SpyRetrievalQueryBuilder()
        orch = _make_branching_orch_with_retrieval(
            session_factory,
            fake_retrieval,
            retrieval_query_builder=spy_query_builder,
        )

        orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert len(spy_query_builder.calls) == 1
        called_story_id, called_input, called_mode, called_intent = (
            spy_query_builder.calls[0]
        )
        assert called_story_id == story_id
        assert called_input == "I open the door."
        assert called_mode is StoryMode.BRANCHING
        assert called_intent.intent_type is IntentType.IN_CHARACTER_ACTION


class _RaisingRetrievalQueryBuilder:
    """Simulates a configured RetrievalQueryBuilder whose query construction
    fails (Codex review, PR #119 round 8) -- a pre-context read/construction
    failure, distinct from the post-commit ingestion write path."""

    def build_query_request(
        self,
        story_id: UUID,
        current_input: str,
        story_mode: StoryMode,
        classified_intent: object,
    ) -> object:
        raise RuntimeError("chroma unreachable")


class TestRetrievalQueryConstructionFailureFailsClosed:
    """Codex review (PR #119) round 8: a configured RetrievalQueryBuilder
    that raises must fail the turn with a typed PIPELINE_ERROR, not silently
    proceed with retrieval_query_request=None (ADR-018 D7's best-effort
    swallow applies only to the post-commit ingestion/write path, not to
    this pre-context query-construction step)."""

    def test_query_build_failure_returns_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        story_id, node_id = seeded_story
        fake_retrieval = _FakeRetrievalWriteService()
        orch = _make_branching_orch_with_retrieval(
            session_factory,
            fake_retrieval,
            retrieval_query_builder=_RaisingRetrievalQueryBuilder(),
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.pipeline_error_summary is not None
        assert "retrieval query construction failed" in result.pipeline_error_summary

    def test_writer_not_called_after_query_build_failure(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        story_id, node_id = seeded_story
        fake_retrieval = _FakeRetrievalWriteService()
        orch = _make_branching_orch_with_retrieval(
            session_factory,
            fake_retrieval,
            retrieval_query_builder=_RaisingRetrievalQueryBuilder(),
        )

        orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert orch._writer_service.calls == []  # type: ignore[attr-defined]

    def test_context_builder_not_called_after_query_build_failure(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        """Not merely 'not called with retrieval_query_request=None' --
        _build_context() must never run at all once query construction has
        already failed for this turn."""
        story_id, node_id = seeded_story
        fake_retrieval = _FakeRetrievalWriteService()
        orch = _make_branching_orch_with_retrieval(
            session_factory,
            fake_retrieval,
            retrieval_query_builder=_RaisingRetrievalQueryBuilder(),
        )

        orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert orch._context_builder.calls == []  # type: ignore[attr-defined]

    def test_no_configured_query_builder_still_delivers_normally(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        """The Null-builder case (no retrieval query builder wired at all)
        remains a valid no-retrieval turn -- distinct from a configured
        builder that raises."""
        story_id, node_id = seeded_story
        fake_retrieval = _FakeRetrievalWriteService()
        orch = _make_branching_orch_with_retrieval(
            session_factory, fake_retrieval, retrieval_query_builder=None
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.DELIVERED

    def test_query_builder_returning_empty_request_still_delivers_normally(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        """A configured builder that succeeds (even with an effectively empty
        retrieval query) is not an error -- only a raised exception is."""
        story_id, node_id = seeded_story
        fake_retrieval = _FakeRetrievalWriteService()
        orch = _make_branching_orch_with_retrieval(
            session_factory,
            fake_retrieval,
            retrieval_query_builder=_SpyRetrievalQueryBuilder(),
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.DELIVERED

    def test_post_commit_ingestion_failure_remains_swallowed(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        """Sibling contrast: a post-commit retrieval-ingestion failure (D7)
        must still be best-effort and swallowed -- unaffected by this
        round's read-path fix, which only tightens pre-context query
        construction."""

        class _RaisingRetrievalWriteService:
            def ingest_turn(self, *args: object, **kwargs: object) -> None:
                raise RuntimeError("chroma write failed")

        story_id, node_id = seeded_story
        orch = _make_branching_orch_with_retrieval(
            session_factory,
            _RaisingRetrievalWriteService(),  # type: ignore[arg-type]
            retrieval_query_builder=_SpyRetrievalQueryBuilder(),
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.DELIVERED


class _AdjServiceAnnouncingPending:
    """Fake adjudication service that always announces a new pending roll.

    CRD Issue 15b: the announce path itself (structured instruction +
    ActionResolutionSequence persistence) is now
    ``ActionResolutionService.start_sequence``'s job, called by the real
    orchestrator from ``_write_rpg_audit`` — this fake only needs to supply
    the raw ``RollProposal`` the LLM would have produced.
    """

    def is_adjudicable(self, sheet: object) -> bool:
        return True

    def adjudicate(self, *args: object, **kwargs: object) -> object:
        from afterworlds.models.enums import RollVisibility
        from afterworlds.models.rpg import RollProposal
        from afterworlds.pipeline.rpg.models import AdjudicationPassResult

        return AdjudicationPassResult(
            proposals=(),
            writer_views=(),
            player_proposal=RollProposal(
                check_label="Stealth Check",
                subsystem_tag="skill_check",
                skill_or_attribute_label="stealth",
                visibility=RollVisibility.PLAYER,
            ),
        )


def _seed_character_sheet(session_factory: object, story_id: UUID) -> object:
    """Persist a real RpgCharacterSheetBase + Dnd5eCharacterSheet row pair
    for *story_id* and return the (session_state, sheet) pair to hand to the
    orchestrator. The announce path's FK to rpg_character_sheet_bases has
    never been exercised by an existing fixture — every prior test either
    reads an existing DB-less fake pending or never reaches the INSERT."""
    from afterworlds.models.enums import DiceHandling, RpgPlayStatus
    from afterworlds.models.session import RpgSessionState
    from afterworlds.persistence.crud.character_sheet import (
        create_dnd5e_sheet,
        create_rpg_base_sheet,
    )

    _, sheet = _make_rpg_session_and_sheet()
    sheet = sheet.model_copy(update={"story_id": story_id})  # type: ignore[attr-defined]
    session = session_factory()  # type: ignore[operator]
    try:
        create_rpg_base_sheet(session, sheet)  # type: ignore[arg-type]
        create_dnd5e_sheet(session, sheet)  # type: ignore[arg-type]
        session.commit()
    finally:
        session.close()

    session_state = RpgSessionState(
        story_id=story_id,
        character_sheet_id=sheet.sheet_id,  # type: ignore[attr-defined]
        dice_handling=DiceHandling.AI_ROLLS,
        play_status=RpgPlayStatus.IN_PLAY,
    )
    return session_state, sheet


def _make_rpg_orch_announcing_pending_with_svc(
    session_factory: object,
    story_id: UUID,
    retrieval_write_service: _FakeRetrievalWriteService,
) -> OrchestratorService:
    """RPG orchestrator: adjudication announces a pending roll and the
    lifecycle service IS wired — the turn completes DELIVERED, unlike the
    no-service-wired guard case covered by TestRpgPendingRollServiceGuard."""
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
    from afterworlds.pipeline.rpg.dice import SystemRandomDiceService
    from afterworlds.pipeline.rpg.sequence import ActionResolutionService

    session_state, sheet = _seed_character_sheet(session_factory, story_id)

    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(make_intent()),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.RPG),
        rpg_adjudication_service=_AdjServiceAnnouncingPending(),  # type: ignore[arg-type]
        rpg_session_sheet_resolver=lambda _sid: (session_state, sheet),  # type: ignore[arg-type]
        rpg_dice_service=SystemRandomDiceService(seed=42),  # type: ignore[arg-type]
        rpg_sequence_service=ActionResolutionService(  # type: ignore[arg-type]
            adapter=D20RulesSystemAdapter(),
            dice_service=SystemRandomDiceService(seed=42),
            session_factory=session_factory,  # type: ignore[arg-type]
        ),
        retrieval_write_service=retrieval_write_service,
    )


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

    def test_pending_roll_announced_gets_roll_request_marker_and_is_not_ingested(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        """ADR-018 D6: a turn on which adjudication announces a new pending
        roll must be marked ROLL_REQUEST (not ORDINARY_NARRATIVE) and must
        never enter Retrieval Memory — the marker⟺PendingRollRequest
        correspondence the ADR requires, exercised end-to-end rather than
        only at the pure-predicate level (see test_eligibility.py)."""
        story_id, node_id = seeded_story
        fake_retrieval = _FakeRetrievalWriteService()
        orch = _make_rpg_orch_announcing_pending_with_svc(
            session_factory, story_id, fake_retrieval
        )

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
        assert category is RpgTurnRetrievalCategory.ROLL_REQUEST
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

    def test_setup_confirmation_marker_without_adjudication_wired(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        """Codex review (PR #119) P2: rpg_play_status must resolve from the
        session/sheet resolver directly, independent of RPG adjudication
        wiring -- a story can have Retrieval Memory enabled before
        adjudication is wired. A SETUP turn must still get
        SETUP_CONFIRMATION, not fall through to ORDINARY_NARRATIVE."""
        story_id, node_id = seeded_story
        fake_retrieval = _FakeRetrievalWriteService()
        orch = _make_rpg_orch_without_adjudication(
            session_factory, fake_retrieval, play_status_setup=True
        )

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

    def test_ordinary_narrative_marker_without_adjudication_wired(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        """Same independence proof as above, for the IN_PLAY/non-SETUP case:
        rpg_play_status resolves to IN_PLAY without adjudication wired, and
        the turn is marked ORDINARY_NARRATIVE (and ingested) exactly as it
        would be with adjudication wired."""
        story_id, node_id = seeded_story
        fake_retrieval = _FakeRetrievalWriteService()
        orch = _make_rpg_orch_without_adjudication(session_factory, fake_retrieval)

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

    def test_unresolvable_play_status_fails_closed_not_ordinary_narrative(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        """Codex review (PR #119) P2: when RPG mode is active but nothing
        can resolve rpg_play_status at all (no adjudication service, no
        session/sheet resolver), marker classification must fail closed --
        a typed PIPELINE_ERROR and rollback, never a silently-written
        ORDINARY_NARRATIVE marker for an unclassified turn."""
        story_id, node_id = seeded_story
        orch = _make_rpg_orch_with_neither_adjudication_nor_resolver(session_factory)

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
        with session_factory() as read_session:  # type: ignore[operator]
            # No marker row at all -- never a fallback ORDINARY_NARRATIVE.
            from sqlalchemy import select

            from afterworlds.persistence.orm.node import NodeORM, TurnORM
            from afterworlds.persistence.orm.story import ArcORM, ChapterORM

            existing_turn_ids = (
                read_session.execute(
                    select(TurnORM.turn_id)
                    .join(NodeORM, TurnORM.node_id == NodeORM.node_id)
                    .join(ChapterORM, NodeORM.chapter_id == ChapterORM.chapter_id)
                    .join(ArcORM, ChapterORM.arc_id == ArcORM.arc_id)
                    .where(ArcORM.story_id == str(story_id))
                )
                .scalars()
                .all()
            )
        # Rolled back: no Turn row was committed for this failed attempt.
        assert existing_turn_ids == []


class TestRpgSessionResolverSetupWithoutSheet:
    """P1 remediation (PR #126 review round 3): RPG setup turns must not
    require a completed Dnd5eCharacterSheet. Only RpgCharacterSheetBase
    exists during RPG setup (Issue 15's conversational character-creation
    pipeline has not produced a full sheet yet), so a resolver that requires
    one raises and incorrectly failed the mandatory turn-retrieval-marker
    classification closed. rpg_session_resolver (session-state-only)
    resolves play_status without ever consulting the sheet-requiring
    resolver."""

    def test_setup_marker_resolves_without_sheet_lookup(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        story_id, node_id = seeded_story
        session_state, _sheet = _make_rpg_session_and_sheet()
        setup_state = RpgSessionState(
            story_id=session_state.story_id,
            character_sheet_id=session_state.character_sheet_id,
            dice_handling=DiceHandling.AI_ROLLS,
            play_status=RpgPlayStatus.SETUP,
        )

        sheet_resolver_calls: list[UUID] = []

        def _raising_sheet_resolver(sid: UUID) -> tuple[object, object]:
            # Mirrors the real production resolver
            # (api/pipeline_wiring.py::_make_rpg_session_sheet_resolver),
            # which raises when no concrete Dnd5eCharacterSheet exists yet
            # -- exactly the state every RPG story is in during setup.
            sheet_resolver_calls.append(sid)
            raise ValueError(
                "no Dnd5eCharacterSheet yet (character creation not complete)"
            )

        orch = OrchestratorService(
            intent_classifier=FakeIntentClassifier(make_intent()),
            context_builder=FakeContextBuilder(),
            safety_service=FakeSafetyService(),
            planner_service=FakePlannerService(),
            writer_service=FakeWriterService(),
            extractor_service=FakeExtractorService(),
            contradiction_service=FakeContradictionService(),
            session_factory=session_factory,  # type: ignore[arg-type]
            safety_policy=CapabilityProfileAwareSafetyPolicy(),
            provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
            mode_resolver=fixed_mode_resolver(StoryMode.RPG),
            rpg_session_sheet_resolver=_raising_sheet_resolver,  # type: ignore[arg-type]
            rpg_session_resolver=lambda _sid: setup_state,
            # rpg_adjudication_service intentionally absent -- setup turns
            # never require it (Codex P1, PR #126 round 3).
        )

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
        assert sheet_resolver_calls == [], (
            "rpg_session_sheet_resolver must not be consulted for play-status"
            " resolution once rpg_session_resolver is wired"
        )

    def test_missing_session_state_row_still_fails_closed(
        self, session_factory, seeded_story
    ) -> None:  # type: ignore[no-untyped-def]
        """rpg_session_resolver returning None (no RpgSessionState row) must
        still fail closed, exactly like the pre-existing no-resolver-at-all
        case -- this fix must not silently default missing session state to
        SETUP."""
        story_id, node_id = seeded_story
        orch = OrchestratorService(
            intent_classifier=FakeIntentClassifier(make_intent()),
            context_builder=FakeContextBuilder(),
            safety_service=FakeSafetyService(),
            planner_service=FakePlannerService(),
            writer_service=FakeWriterService(),
            extractor_service=FakeExtractorService(),
            contradiction_service=FakeContradictionService(),
            session_factory=session_factory,  # type: ignore[arg-type]
            safety_policy=CapabilityProfileAwareSafetyPolicy(),
            provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
            mode_resolver=fixed_mode_resolver(StoryMode.RPG),
            rpg_session_resolver=lambda _sid: None,
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
