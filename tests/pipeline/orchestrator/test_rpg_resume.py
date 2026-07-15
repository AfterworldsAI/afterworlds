"""Tests for OrchestratorService.orchestrate_rpg_resume.

CRD Issue 15b, ADR-015b 15b-34.

Setup choice (per the task brief): option (a) — hand-construct a
READY_FOR_NARRATION ``ActionResolutionSequenceORM`` row plus a real
``ActionResolutionEventORM`` row (written through the real ``_append_event``
helper, the same code path ``consume_roll`` uses) rather than driving the
full ``start_sequence`` -> ``consume_roll`` adapter/sheet machinery. The
whole point of ``orchestrate_rpg_resume`` is projecting ``rpg_roll_audit``
rows from real event-ledger rows (the Final Audit Projection), so the event
row must be real; the adapter/sheet mechanics that produced it are already
covered by ``tests/pipeline/rpg/test_sequence.py`` and are not re-tested
here. Error-path tests (not-found/not-ready) don't need an event row at all.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import sqlalchemy as sa

from afterworlds.entitlement.enums import PipelinePassId, RuntimeAccessPath
from afterworlds.models.character_sheet import Dnd5eAbilityScores, Dnd5eCharacterSheet
from afterworlds.models.enums import (
    DiceHandling,
    DiceSelectionRule,
    IntentType,
    ResolvedStepKind,
    RollContribution,
    RollPurpose,
    RollSubmissionSource,
    RpgPlayStatus,
    StoryMode,
)
from afterworlds.models.node import (
    BranchingNodeMetadata,
    Node,
    NodeMetadata,
    StateDelta,
)
from afterworlds.models.rpg import RollEventPayload, RollInstructionSnapshot, RollTerm
from afterworlds.models.session import RpgSessionState
from afterworlds.models.story import Arc, Chapter, Story
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.character_sheet import (
    create_dnd5e_sheet,
    create_rpg_base_sheet,
)
from afterworlds.persistence.crud.node import create_node, create_turn
from afterworlds.persistence.crud.story import create_arc, create_chapter, create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.node import TurnORM
from afterworlds.persistence.orm.rpg import ActionResolutionSequenceORM, RpgRollAuditORM
from afterworlds.pipeline._refusal import (
    PassIdentifier,
    ProviderRefusal,
    ProviderRefusalError,
    RefusalCategory,
)
from afterworlds.pipeline.contradiction.models import (
    ContradictionCategory,
    ContradictionViolation,
)
from afterworlds.pipeline.orchestrator import (
    CapabilityProfileAwareSafetyPolicy,
    OrchestratorService,
    PipelineDisposition,
)
from afterworlds.pipeline.provider._models import ProviderCallRequest
from afterworlds.pipeline.provider._refusal_log import ProviderRefusalEvent
from afterworlds.pipeline.provider._resolver import RefusalLogProxy
from afterworlds.pipeline.provider._routing import (
    EligibleModelRoute,
    SafetyWhitelistStatus,
    TurnProviderBinding,
)
from afterworlds.pipeline.provider.adapters._fallback import RefusalFallbackRouter
from afterworlds.pipeline.rpg.sequence import (
    ActionResolutionService,
    _append_event,
    _build_derived_term_results,
)
from afterworlds.pipeline.safety.models import (
    SafetyCategory,
    SafetyConcern,
    SafetyPassError,
    SafetyReport,
    SafetyResult,
    SafetyTarget,
)
from tests.pipeline.orchestrator.conftest import (
    FakeContextBuilder,
    FakeContradictionService,
    FakeExtractorService,
    FakeIntentClassifier,
    FakePlannerService,
    FakeSafetyService,
    FakeWriterService,
    make_intent,
)
from tests.pipeline.orchestrator.test_service import _make_fake_resolver

_SOJOURNER = uuid4()


# ---------------------------------------------------------------------------
# Instruction/payload builders — copied from tests/pipeline/rpg/test_sequence.py
# (that file's own module docstring defers this integration setup to here).
# ---------------------------------------------------------------------------


def _term(
    selection_rule: DiceSelectionRule = DiceSelectionRule.SUM_ALL,
    *,
    count: int = 1,
    keep_count: int | None = None,
    contribution: RollContribution = RollContribution.ADD,
) -> RollTerm:
    return RollTerm(
        term_id=uuid4(),
        count=count,
        sides=20,
        selection_rule=selection_rule,
        keep_count=keep_count,
        contribution=contribution,
    )


def _instruction(
    *terms: RollTerm,
    sequence_id: UUID,
    step_id: UUID,
    dc: int | None,
    display_label: str = "Stealth Check",
) -> RollInstructionSnapshot:
    return RollInstructionSnapshot(
        instruction_id=uuid4(),
        instruction_revision=1,
        purpose=RollPurpose.SKILL_CHECK,
        terms=tuple(terms),
        modifier_components=(),
        display_expression="1d20",
        display_label=display_label,
        source_rule_refs=(),
        adjustment_options=(),
        sequence_id=sequence_id,
        step_id=step_id,
        dc=dc,
    )


def _seed_ready_sequence(
    session: object,
    *,
    story_id: UUID,
    node_id: UUID,
    status: str = "ready_for_narration",
    with_event: bool = True,
    total: int = 17,
    outcome: str = "success",
    dc: int | None = 15,
) -> tuple[UUID, Dnd5eCharacterSheet, RpgSessionState]:
    """Persist an originating turn, a character sheet, and a sequence row.

    Returns ``(sequence_id, sheet, session_state)``. The sheet is a real
    persisted ``rpg_character_sheet_bases``/``dnd5e_character_sheets`` row
    (required: ``ActionResolutionSequenceORM.character_id`` FKs to it, and
    ``_apply_rpg_sheet_effects`` unconditionally calls ``update_dnd5e_sheet``
    even when there are no accumulated effects to apply).
    """
    now = datetime.now(tz=UTC)

    originating_turn = Turn(
        user_input="I sneak past the guard.",
        assistant_output="",
        timestamp=now,
        intent_classification=IntentType.IN_CHARACTER_ACTION,
        node_id=node_id,
        intent_classification_result=make_intent(),
    )
    create_turn(session, originating_turn)  # type: ignore[arg-type]

    sheet = Dnd5eCharacterSheet(
        story_id=story_id,
        rules_package_id="dnd5e-v1",
        character_name="Aldric",
        character_class="Fighter",
        background="Soldier",
        level=3,
        ability_scores=Dnd5eAbilityScores(
            strength=16,
            dexterity=12,
            constitution=15,
            intelligence=10,
            wisdom=11,
            charisma=9,
        ),
        equipment=["Longsword", "Shield"],
        current_hp=28,
        maximum_hp=28,
        active_conditions=[],
        created_at=now,
        updated_at=now,
    )
    create_rpg_base_sheet(session, sheet)  # type: ignore[arg-type]
    create_dnd5e_sheet(session, sheet)  # type: ignore[arg-type]

    session_state = RpgSessionState(
        story_id=story_id,
        character_sheet_id=sheet.sheet_id,
        dice_handling=DiceHandling.AI_ROLLS,
        play_status=RpgPlayStatus.IN_PLAY,
    )

    sequence_id = uuid4()
    step_id = uuid4()
    session_id = uuid4()
    seq_row = ActionResolutionSequenceORM(
        sequence_id=str(sequence_id),
        story_id=str(story_id),
        node_id=str(node_id),
        character_id=str(sheet.sheet_id),
        originating_turn_id=str(originating_turn.turn_id),
        session_id=str(session_id),
        status=status,
        current_interaction_kind="none",
        resolved_steps_json="[]",
        provisional_effects_json="[]",
        created_at=now.isoformat(),
        updated_at=now.isoformat(),
    )
    session.add(seq_row)  # type: ignore[attr-defined]
    session.flush()  # type: ignore[attr-defined]

    if with_event:
        term = _term(DiceSelectionRule.SUM_ALL)
        instr = _instruction(term, sequence_id=sequence_id, step_id=step_id, dc=dc)
        derived = _build_derived_term_results(instr, {term.term_id: (14,)})
        payload = RollEventPayload(
            kind=ResolvedStepKind.PLAYER_ROLL,
            instruction_snapshot=instr,
            submission_source=RollSubmissionSource.INLINE_UI,
            pending_roll_request_id=uuid4(),
            raw_input_json="[]",
            aggregate_input_json=None,
            derived_selections_json=json.dumps(
                [r.model_dump(mode="json") for r in derived]
            ),
            subtotal=14,
            total=total,
            outcome=outcome,  # type: ignore[arg-type]
            gm_cheating_at_roll=False,
        )
        _append_event(
            session,  # type: ignore[arg-type]
            sequence_id=sequence_id,
            step_id=step_id,
            story_id=story_id,
            session_id=session_id,
            character_id=sheet.sheet_id,
            kind=ResolvedStepKind.PLAYER_ROLL,
            provisional_effects_json="[]",
            payload=payload,
        )

    session.commit()  # type: ignore[attr-defined]
    return sequence_id, sheet, session_state


def _make_resume_orchestrator(
    session_factory: object,
    *,
    session_state: RpgSessionState | None = None,
    sheet: Dnd5eCharacterSheet | None = None,
    writer_output: str = "Narrator: you slip past unseen.",
    safety_output: SafetyResult | None = None,
    contradiction_violations: list[ContradictionViolation] | None = None,
    provider_resolver: object | None = None,
    safety_service: object | None = None,
) -> OrchestratorService:
    sequence_svc = ActionResolutionService(
        adapter=None,  # type: ignore[arg-type]
        dice_service=None,  # type: ignore[arg-type]
        session_factory=session_factory,  # type: ignore[arg-type]
    )
    resolver = (
        (lambda _sid: (session_state, sheet)) if session_state is not None else None
    )
    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(make_intent()),
        context_builder=FakeContextBuilder(),
        safety_service=safety_service
        or FakeSafetyService(output_verdict=safety_output),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(assistant_output=writer_output),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(
            violations=contradiction_violations
        ),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=provider_resolver or _make_fake_resolver(),  # type: ignore[arg-type]
        rpg_session_sheet_resolver=resolver,  # type: ignore[arg-type]
        rpg_sequence_service=sequence_svc,
    )


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


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestOrchestrateRpgResumeHappyPath:
    def test_resume_delivers_and_projects_audit_row(
        self, session_factory: object, session: object, seeded_story: tuple[UUID, UUID]
    ) -> None:
        story_id, node_id = seeded_story
        sequence_id, sheet, session_state = _seed_ready_sequence(
            session,
            story_id=story_id,
            node_id=node_id,
            total=17,
            outcome="success",
            dc=15,
        )
        orch = _make_resume_orchestrator(
            session_factory,
            session_state=session_state,
            sheet=sheet,
            writer_output="Narrator: you slip past unseen.",
        )

        result = orch.orchestrate_rpg_resume(
            story_id,
            node_id,
            sequence_id,
            access_path=RuntimeAccessPath.HOSTED,
            sojourner_id=_SOJOURNER,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.turn_id is not None
        assert result.delivered_output == "Narrator: you slip past unseen."

        with session_factory() as read_session:  # type: ignore[operator]
            audit = (
                read_session.query(RpgRollAuditORM)
                .filter_by(turn_id=str(result.turn_id))
                .one()
            )
            seq_row = (
                read_session.query(ActionResolutionSequenceORM)
                .filter_by(sequence_id=str(sequence_id))
                .one()
            )

        assert audit.total == 17  # noqa: PLR2004
        assert audit.outcome == "success"
        assert audit.check_label == "Stealth Check"
        assert audit.dc == 15  # noqa: PLR2004
        assert seq_row.status == "completed"


# ---------------------------------------------------------------------------
# Idempotency guard
# ---------------------------------------------------------------------------


class TestOrchestrateRpgResumeIdempotency:
    def test_already_completed_sequence_is_pipeline_error(
        self, session_factory: object, session: object, seeded_story: tuple[UUID, UUID]
    ) -> None:
        story_id, node_id = seeded_story
        sequence_id, sheet, session_state = _seed_ready_sequence(
            session,
            story_id=story_id,
            node_id=node_id,
            status="completed",
            with_event=False,
        )
        orch = _make_resume_orchestrator(
            session_factory, session_state=session_state, sheet=sheet
        )

        result = orch.orchestrate_rpg_resume(
            story_id,
            node_id,
            sequence_id,
            access_path=RuntimeAccessPath.HOSTED,
            sojourner_id=_SOJOURNER,
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.pipeline_error_summary is not None
        assert "ACTION_SEQUENCE_ALREADY_COMPLETED" in result.pipeline_error_summary

        with session_factory() as read_session:  # type: ignore[operator]
            audit_count = read_session.query(RpgRollAuditORM).count()
        assert audit_count == 0


# ---------------------------------------------------------------------------
# Not-found / not-ready
# ---------------------------------------------------------------------------


class TestOrchestrateRpgResumeNotFoundNotReady:
    def test_nonexistent_sequence_is_pipeline_error(
        self, session_factory: object
    ) -> None:
        orch = _make_resume_orchestrator(session_factory)

        result = orch.orchestrate_rpg_resume(
            uuid4(),
            uuid4(),
            uuid4(),
            access_path=RuntimeAccessPath.HOSTED,
            sojourner_id=_SOJOURNER,
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.pipeline_error_summary is not None
        assert "ACTION_SEQUENCE_NOT_FOUND" in result.pipeline_error_summary

    def test_active_sequence_not_ready_is_pipeline_error(
        self, session_factory: object, session: object, seeded_story: tuple[UUID, UUID]
    ) -> None:
        story_id, node_id = seeded_story
        sequence_id, _sheet, _session_state = _seed_ready_sequence(
            session,
            story_id=story_id,
            node_id=node_id,
            status="active",
            with_event=False,
        )
        orch = _make_resume_orchestrator(session_factory)

        result = orch.orchestrate_rpg_resume(
            story_id,
            node_id,
            sequence_id,
            access_path=RuntimeAccessPath.HOSTED,
            sojourner_id=_SOJOURNER,
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.pipeline_error_summary is not None
        assert "SEQUENCE_NOT_READY_FOR_NARRATION" in result.pipeline_error_summary


# ---------------------------------------------------------------------------
# Story/node identity mismatch (Issue #127 15b-23; Codex P1, PR #129)
# ---------------------------------------------------------------------------


class TestOrchestrateRpgResumeIdentityMismatch:
    def test_story_mismatch_is_state_conflict_and_touches_nothing(
        self, session_factory: object, session: object, seeded_story: tuple[UUID, UUID]
    ) -> None:
        story_id, node_id = seeded_story
        sequence_id, sheet, session_state = _seed_ready_sequence(
            session, story_id=story_id, node_id=node_id
        )
        orch = _make_resume_orchestrator(
            session_factory, session_state=session_state, sheet=sheet
        )

        result = orch.orchestrate_rpg_resume(
            uuid4(),  # wrong story_id
            node_id,
            sequence_id,
            access_path=RuntimeAccessPath.HOSTED,
            sojourner_id=_SOJOURNER,
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.pipeline_error_summary is not None
        assert "ACTION_SEQUENCE_STATE_CONFLICT" in result.pipeline_error_summary
        assert result.writer_result is None

        with session_factory() as read_session:  # type: ignore[operator]
            audit_count = read_session.query(RpgRollAuditORM).count()
            seq_row = (
                read_session.query(ActionResolutionSequenceORM)
                .filter_by(sequence_id=str(sequence_id))
                .one()
            )
        assert audit_count == 0
        assert seq_row.status == "ready_for_narration"

    def test_node_mismatch_is_state_conflict_and_touches_nothing(
        self, session_factory: object, session: object, seeded_story: tuple[UUID, UUID]
    ) -> None:
        story_id, node_id = seeded_story
        sequence_id, sheet, session_state = _seed_ready_sequence(
            session, story_id=story_id, node_id=node_id
        )
        orch = _make_resume_orchestrator(
            session_factory, session_state=session_state, sheet=sheet
        )

        result = orch.orchestrate_rpg_resume(
            story_id,
            uuid4(),  # wrong node_id -- story has moved on since the roll
            sequence_id,
            access_path=RuntimeAccessPath.HOSTED,
            sojourner_id=_SOJOURNER,
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.pipeline_error_summary is not None
        assert "ACTION_SEQUENCE_STATE_CONFLICT" in result.pipeline_error_summary
        assert result.writer_result is None

        with session_factory() as read_session:  # type: ignore[operator]
            audit_count = read_session.query(RpgRollAuditORM).count()
            seq_row = (
                read_session.query(ActionResolutionSequenceORM)
                .filter_by(sequence_id=str(sequence_id))
                .one()
            )
        assert audit_count == 0
        assert seq_row.status == "ready_for_narration"


# ---------------------------------------------------------------------------
# Output Safety block — ADR-015 Decision 1 rollback proof
# ---------------------------------------------------------------------------


class TestOrchestrateRpgResumeOutputSafetyBlock:
    def test_output_safety_block_rolls_back_audit_and_completion(
        self, session_factory: object, session: object, seeded_story: tuple[UUID, UUID]
    ) -> None:
        story_id, node_id = seeded_story
        sequence_id, sheet, session_state = _seed_ready_sequence(
            session, story_id=story_id, node_id=node_id
        )
        orch = _make_resume_orchestrator(
            session_factory,
            session_state=session_state,
            sheet=sheet,
            safety_output=_block_safety(SafetyTarget.OUTPUT),
        )

        result = orch.orchestrate_rpg_resume(
            story_id,
            node_id,
            sequence_id,
            access_path=RuntimeAccessPath.HOSTED,
            sojourner_id=_SOJOURNER,
        )

        assert result.disposition is PipelineDisposition.BLOCKED_OUTPUT_SAFETY
        assert result.writer_result is not None

        with session_factory() as read_session:  # type: ignore[operator]
            audit_count = (
                read_session.query(RpgRollAuditORM)
                .filter_by(turn_id=str(result.writer_result.turn_id))
                .count()
            )
            seq_row = (
                read_session.query(ActionResolutionSequenceORM)
                .filter_by(sequence_id=str(sequence_id))
                .one()
            )

        # No partial audit row, and the sequence survives ready_for_narration
        # (not completed, not deleted) so a later resume attempt can retry.
        assert audit_count == 0
        assert seq_row.status == "ready_for_narration"


# ---------------------------------------------------------------------------
# Contradiction block — same rollback shape
# ---------------------------------------------------------------------------


class TestOrchestrateRpgResumeContradictionBlock:
    def test_contradiction_block_rolls_back_audit_and_completion(
        self, session_factory: object, session: object, seeded_story: tuple[UUID, UUID]
    ) -> None:
        story_id, node_id = seeded_story
        sequence_id, sheet, session_state = _seed_ready_sequence(
            session, story_id=story_id, node_id=node_id
        )
        violations = [
            ContradictionViolation(
                category=ContradictionCategory.OTHER,
                description="invented detail",
                canon_reference="ref",
            )
        ]
        orch = _make_resume_orchestrator(
            session_factory,
            session_state=session_state,
            sheet=sheet,
            contradiction_violations=violations,
        )

        result = orch.orchestrate_rpg_resume(
            story_id,
            node_id,
            sequence_id,
            access_path=RuntimeAccessPath.HOSTED,
            sojourner_id=_SOJOURNER,
        )

        assert result.disposition is PipelineDisposition.BLOCKED_CONTRADICTION
        assert result.writer_result is not None

        with session_factory() as read_session:  # type: ignore[operator]
            audit_count = (
                read_session.query(RpgRollAuditORM)
                .filter_by(turn_id=str(result.writer_result.turn_id))
                .count()
            )
            seq_row = (
                read_session.query(ActionResolutionSequenceORM)
                .filter_by(sequence_id=str(sequence_id))
                .one()
            )

        assert audit_count == 0
        assert seq_row.status == "ready_for_narration"


# ---------------------------------------------------------------------------
# Transaction hooks (Codex P1, PR #129 discussion r3583794727)
#
# orchestrate_rpg_resume resolves a TurnProviderBinding but originally called
# _run_with_transaction without its pre_transaction_fn/post_transaction_fn --
# unlike the narrative and OOC wrappers. Those hooks switch RefusalLogProxy
# into buffered mode before the outer transaction and flush it only after
# the session closes. Without them, a post-Writer provider refusal during
# resume tries to log through a fresh SQLite session while the resume
# transaction still holds the write lock; RefusalFallbackRouter._log()
# suppresses that failure, silently losing the refusal audit row.
# ---------------------------------------------------------------------------


class _InertAdapter:
    """Adapter stand-in for the happy path: fakes never touch it, so a call
    reaching it is itself a test failure, not a scenario to support."""

    provider_name = "fake-anthropic"

    def call(self, request: object) -> object:
        raise AssertionError("adapter.call must not be reached on the happy path")


class _RefusingPrimary:
    """Primary adapter that always refuses -- drives the real
    RefusalFallbackRouter/RefusalLogProxy path, not a stand-in raise."""

    provider_name = "anthropic"

    def call(self, request: ProviderCallRequest) -> object:
        raise ProviderRefusalError(
            ProviderRefusal(
                provider="anthropic",
                model="claude-test",
                pass_identifier=PassIdentifier.WRITER,
                refusal_category=RefusalCategory.CONTENT_POLICY,
            )
        )


class _RealRouterOutputSafety:
    """Output Safety fake whose check() calls the real provider chain.

    A fake that merely raised ProviderRefusalError itself would never touch
    RefusalFallbackRouter._log()/RefusalLogProxy -- the exact code the bug
    lives in -- so this drives ``provider.call()`` for real, matching what
    the production SafetyService does (fail-closed: any ProviderRefusalError
    becomes SafetyPassError).
    """

    def check(
        self,
        built_context: object,
        text: str,
        target: SafetyTarget,
        *,
        provider: object = None,
    ) -> SafetyResult:
        if target is SafetyTarget.INPUT:
            return SafetyResult(report=SafetyReport(concerns=[]), target=target)
        request = ProviderCallRequest(
            pass_id=PipelinePassId.OUTPUT_SAFETY,
            system_blocks=[],
            rendered_blocks=[],
            max_output_tokens=1000,
        )
        assert provider is not None
        try:
            provider.call(request)  # type: ignore[attr-defined]
        except ProviderRefusalError as exc:
            raise SafetyPassError(str(exc), cause=exc) from exc
        raise AssertionError("refusing primary must always raise")


class TestOrchestrateRpgResumeTransactionHooks:
    def test_hooks_invoked_exactly_once_and_no_spurious_refusal_event_on_success(
        self, session_factory: object, session: object, seeded_story: tuple[UUID, UUID]
    ) -> None:
        story_id, node_id = seeded_story
        sequence_id, sheet, session_state = _seed_ready_sequence(
            session, story_id=story_id, node_id=node_id
        )

        proxy = RefusalLogProxy(session_factory)
        pre_calls: list[None] = []
        post_calls: list[None] = []

        def counted_pre() -> None:
            pre_calls.append(None)
            proxy.start_buffering()

        def counted_post() -> None:
            post_calls.append(None)
            proxy.flush()

        route = EligibleModelRoute(
            provider_name="fake-anthropic",
            model_identifier="fake-anthropic:claude-test",
            whitelist_status=SafetyWhitelistStatus.NOT_WHITELISTED,
            supports_required_capabilities=False,
        )
        binding = TurnProviderBinding(
            adapter=_InertAdapter(),
            primary_writer_route=route,
            eligible_writer_routes=(route,),
            access_path=RuntimeAccessPath.HOSTED,
            pre_transaction_fn=counted_pre,
            post_transaction_fn=counted_post,
        )

        class _Resolver:
            def resolve_for_turn(
                self, access_path: object, sojourner_id: object
            ) -> object:
                return binding

        orch = _make_resume_orchestrator(
            session_factory,
            session_state=session_state,
            sheet=sheet,
            provider_resolver=_Resolver(),
        )

        result = orch.orchestrate_rpg_resume(
            story_id,
            node_id,
            sequence_id,
            access_path=RuntimeAccessPath.HOSTED,
            sojourner_id=_SOJOURNER,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert len(pre_calls) == 1
        assert len(post_calls) == 1

        with session_factory() as read_session:  # type: ignore[operator]
            refusal_rows = (
                read_session.execute(sa.select(ProviderRefusalEvent)).scalars().all()
            )
        assert len(refusal_rows) == 0

    def test_output_safety_refusal_buffers_during_transaction_and_survives_flush(
        self, tmp_path: object
    ) -> None:
        """Real SQLite-backed proof (not a mock): pre-fix, the resume
        transaction's own Writer-flushed Turn row holds the write lock, so a
        direct-mode refusal write from a fresh connection dies to
        "database is locked" and is silently suppressed by
        RefusalFallbackRouter._log(). Post-fix, the proxy buffers instead and
        flushes only after session.close() releases the lock."""
        db_path = tmp_path / "rpg_resume_refusal.db"  # type: ignore[operator]
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"timeout": 0})
        Base.metadata.create_all(engine)
        sf = create_session_factory(engine)

        now = datetime(2026, 1, 1, tzinfo=UTC)
        with sf() as seed_session:
            story = Story(
                title="Resume Refusal Test Story",
                mode=StoryMode.RPG,
                created_at=now,
                updated_at=now,
            )
            create_story(seed_session, story)
            arc = Arc(story_id=story.story_id, title="Arc 1", order=0)
            create_arc(seed_session, arc)
            chapter = Chapter(arc_id=arc.arc_id, title="Chapter 1", order=0)
            create_chapter(seed_session, chapter)
            node = Node(
                chapter_id=chapter.chapter_id,
                content="",
                state_delta=StateDelta(),
                branching_logic=[],
                intent_type=IntentType.IN_CHARACTER_ACTION,
                metadata=NodeMetadata(timestamp=now),
                mode_metadata=BranchingNodeMetadata(),
            )
            create_node(seed_session, node)
            seed_session.commit()
            story_id, node_id = story.story_id, node.node_id

            sequence_id, sheet, session_state = _seed_ready_sequence(
                seed_session, story_id=story_id, node_id=node_id
            )

        proxy = RefusalLogProxy(sf)
        router = RefusalFallbackRouter(
            primary=_RefusingPrimary(), fallback=None, refusal_log_fn=proxy
        )
        route = EligibleModelRoute(
            provider_name="anthropic",
            model_identifier="claude-test",
            whitelist_status=SafetyWhitelistStatus.NOT_WHITELISTED,
            supports_required_capabilities=False,
        )
        binding = TurnProviderBinding(
            adapter=router,
            primary_writer_route=route,
            eligible_writer_routes=(route,),
            access_path=RuntimeAccessPath.HOSTED,
            pre_transaction_fn=proxy.start_buffering,
            post_transaction_fn=proxy.flush,
        )

        class _Resolver:
            def resolve_for_turn(
                self, access_path: object, sojourner_id: object
            ) -> object:
                return binding

        orch = _make_resume_orchestrator(
            sf,
            session_state=session_state,
            sheet=sheet,
            provider_resolver=_Resolver(),
            safety_service=_RealRouterOutputSafety(),
        )

        result = orch.orchestrate_rpg_resume(
            story_id,
            node_id,
            sequence_id,
            access_path=RuntimeAccessPath.HOSTED,
            sojourner_id=_SOJOURNER,
        )

        # Existing typed pass-failure disposition (Output Safety's
        # SafetyPassError maps to PIPELINE_ERROR, same as every other
        # safety-pass failure) -- no new disposition invented for this fix.
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.pipeline_error_summary is not None
        assert "output safety" in result.pipeline_error_summary.lower()
        assert result.writer_result is not None
        resume_turn_id = str(result.writer_result.turn_id)

        with sf() as read_session:  # type: ignore[operator]
            # _seed_ready_sequence also persists an unrelated "originating
            # turn" row -- must check for the resume's own turn_id specifically,
            # not merely that some Turn row exists.
            resume_turn_row = read_session.get(TurnORM, resume_turn_id)
            audit_count = read_session.query(RpgRollAuditORM).count()
            seq_row = (
                read_session.query(ActionResolutionSequenceORM)
                .filter_by(sequence_id=str(sequence_id))
                .one()
            )
            refusal_rows = (
                read_session.execute(sa.select(ProviderRefusalEvent)).scalars().all()
            )

        # Rolled back: no provisional Turn survives, sequence never advances
        # past ready_for_narration, no partial audit row.
        assert resume_turn_row is None
        assert audit_count == 0
        assert seq_row.status == "ready_for_narration"

        # The refusal audit row itself IS preserved -- committed in a
        # separate session after session.close() released the write lock,
        # not lost to RefusalFallbackRouter._log()'s suppressed exception.
        assert len(refusal_rows) == 1
        assert refusal_rows[0].fallback_outcome == "NO_FALLBACK_CONFIGURED"
        assert refusal_rows[0].refusal_category == "content_policy"
