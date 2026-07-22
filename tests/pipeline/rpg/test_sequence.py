"""Unit tests for ActionResolutionService's event-ledger wiring (ADR-015b 15b-34).

Full start_sequence -> consume_roll integration coverage is deferred to
orchestrate_rpg_resume's own tests (see the CRD Issue 15b (15b-25) note in
tests/pipeline/orchestrator/test_service.py) — no fixture for a real,
persisted ActionResolutionService call chain (story/turn/character sheet
rows) exists anywhere in this repo yet, and building one is that task's
job, not this one's. These tests instead exercise the two new pieces
directly: _build_derived_term_results (pure) and _append_event (DB-backed,
no FK rows needed since action_resolution_events has none).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

# Import every ORM module action_resolution_events/pending_roll_requests/
# rpg_roll_audit transitively FK-reference, so Base.metadata.create_all()
# can resolve them — mirrors tests/persistence/conftest.py's import list.
import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.rpg  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
from afterworlds.models.enums import (
    DiceSelectionRule,
    ResolvedStepKind,
    RollAdjustmentTiming,
    RollContribution,
    RollPurpose,
)
from afterworlds.models.rpg import (
    AdjustmentEventPayload,
    RollAdjustmentOption,
    RollEventPayload,
    RollInstructionSnapshot,
    RollTerm,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.rpg import ActionResolutionEventORM
from afterworlds.pipeline.rpg.sequence import _append_event, _build_derived_term_results

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


# ---------------------------------------------------------------------------
# _build_derived_term_results (pure)
# ---------------------------------------------------------------------------


def _term(
    selection_rule: DiceSelectionRule,
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
    adjustment_options: tuple[RollAdjustmentOption, ...] = (),
) -> RollInstructionSnapshot:
    return RollInstructionSnapshot(
        instruction_id=uuid4(),
        instruction_revision=1,
        purpose=RollPurpose.SKILL_CHECK,
        terms=tuple(terms),
        modifier_components=(),
        display_expression="test",
        display_label="Test Check",
        source_rule_refs=(),
        adjustment_options=adjustment_options,
        sequence_id=uuid4(),
        step_id=uuid4(),
    )


def test_derived_term_results_sum_all() -> None:
    term = _term(DiceSelectionRule.SUM_ALL)
    instr = _instruction(term)
    results = _build_derived_term_results(instr, {term.term_id: (14,)})
    assert results[0].selected_indices == (0,)
    assert results[0].contribution_applied_subtotal == 14


def test_derived_term_results_keep_highest() -> None:
    term = _term(DiceSelectionRule.KEEP_HIGHEST, count=2, keep_count=1)
    instr = _instruction(term)
    results = _build_derived_term_results(instr, {term.term_id: (15, 8)})
    assert results[0].selected_indices == (0,)
    assert results[0].contribution_applied_subtotal == 15


def test_derived_term_results_keep_lowest() -> None:
    term = _term(DiceSelectionRule.KEEP_LOWEST, count=2, keep_count=1)
    instr = _instruction(term)
    results = _build_derived_term_results(instr, {term.term_id: (15, 8)})
    assert results[0].selected_indices == (1,)
    assert results[0].contribution_applied_subtotal == 8


def test_derived_term_results_keep_highest_multi_index() -> None:
    """4d6-drop-lowest shape: keep_count > 1 exercises the multi-index sort path."""
    term = _term(DiceSelectionRule.KEEP_HIGHEST, count=4, keep_count=3)
    instr = _instruction(term)
    results = _build_derived_term_results(instr, {term.term_id: (2, 6, 4, 5)})
    # Dropped: index 0 (value 2, the lowest). Kept: indices 1, 2, 3.
    assert results[0].selected_indices == (1, 2, 3)
    assert results[0].contribution_applied_subtotal == 15


def test_derived_term_results_subtract_contribution_is_negative() -> None:
    term = _term(DiceSelectionRule.SUM_ALL, contribution=RollContribution.SUBTRACT)
    instr = _instruction(term)
    results = _build_derived_term_results(instr, {term.term_id: (6,)})
    assert results[0].contribution_applied_subtotal == -6


def test_derived_term_results_keep_highest_tie_sums_correctly() -> None:
    """Ties are immaterial to the sum: either kept index yields the same total."""
    term = _term(DiceSelectionRule.KEEP_HIGHEST, count=2, keep_count=1)
    instr = _instruction(term)
    results = _build_derived_term_results(instr, {term.term_id: (10, 10)})
    assert results[0].contribution_applied_subtotal == 10


# ---------------------------------------------------------------------------
# _append_event (DB-backed; action_resolution_events has no FK columns)
# ---------------------------------------------------------------------------


@pytest.fixture()
def session():  # type: ignore[no-untyped-def]
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _roll_payload(instr: RollInstructionSnapshot) -> RollEventPayload:
    return RollEventPayload(
        kind=ResolvedStepKind.PLAYER_ROLL,
        instruction_snapshot=instr,
        submission_source=None,
        pending_roll_request_id=uuid4(),
        raw_input_json="[]",
        aggregate_input_json=None,
        derived_selections_json="[]",
        subtotal=14,
        total=17,
        outcome="success",
        gm_cheating_at_roll=False,
    )


def test_append_event_persists_roll_payload(session) -> None:  # type: ignore[no-untyped-def]
    instr = _instruction(_term(DiceSelectionRule.SUM_ALL))
    sequence_id, step_id = uuid4(), uuid4()
    story_id, session_id, character_id = uuid4(), uuid4(), uuid4()

    _append_event(
        session,
        sequence_id=sequence_id,
        step_id=step_id,
        story_id=story_id,
        session_id=session_id,
        character_id=character_id,
        kind=ResolvedStepKind.PLAYER_ROLL,
        provisional_effects_json="[]",
        payload=_roll_payload(instr),
    )
    session.commit()

    row = (
        session.query(ActionResolutionEventORM)
        .filter_by(sequence_id=str(sequence_id))
        .one()
    )
    assert row.event_order == 1
    assert row.kind == "player_roll"
    assert row.story_id == str(story_id)
    assert row.session_id == str(session_id)
    assert row.character_id == str(character_id)

    payload = RollEventPayload.model_validate_json(row.payload_json)
    assert payload.total == 17
    assert payload.outcome == "success"


def test_append_event_increments_event_order_per_sequence(session) -> None:  # type: ignore[no-untyped-def]
    instr = _instruction(_term(DiceSelectionRule.SUM_ALL))
    sequence_id, story_id, session_id, character_id = (
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
    )

    _append_event(
        session,
        sequence_id=sequence_id,
        step_id=uuid4(),
        story_id=story_id,
        session_id=session_id,
        character_id=character_id,
        kind=ResolvedStepKind.PLAYER_ROLL,
        provisional_effects_json="[]",
        payload=_roll_payload(instr),
    )
    session.flush()

    revised = instr.model_copy(update={"instruction_revision": 2})
    _append_event(
        session,
        sequence_id=sequence_id,
        step_id=instr.step_id,
        story_id=story_id,
        session_id=session_id,
        character_id=character_id,
        kind=ResolvedStepKind.ADJUSTMENT,
        provisional_effects_json="[]",
        payload=AdjustmentEventPayload(
            resulting_instruction_snapshot=revised,
            accepted_adjustment_option_id="advantage",
        ),
    )
    session.commit()

    rows = (
        session.query(ActionResolutionEventORM)
        .filter_by(sequence_id=str(sequence_id))
        .order_by(ActionResolutionEventORM.event_order)
        .all()
    )
    assert [r.event_order for r in rows] == [1, 2]
    assert [r.kind for r in rows] == ["player_roll", "adjustment"]


def test_append_event_order_independent_per_sequence(session) -> None:  # type: ignore[no-untyped-def]
    """A second, unrelated sequence starts its own event_order at 1."""
    instr = _instruction(_term(DiceSelectionRule.SUM_ALL))

    for _ in range(2):
        _append_event(
            session,
            sequence_id=uuid4(),
            step_id=uuid4(),
            story_id=uuid4(),
            session_id=uuid4(),
            character_id=uuid4(),
            kind=ResolvedStepKind.PLAYER_ROLL,
            provisional_effects_json="[]",
            payload=_roll_payload(instr),
        )
    session.commit()

    orders = [r.event_order for r in session.query(ActionResolutionEventORM).all()]
    assert orders == [1, 1]


# ---------------------------------------------------------------------------
# consume_roll — atomic conditional consume (Codex P1, PR #129 remediation)
# ---------------------------------------------------------------------------


def _seed_pending_roll(session, *, instr: RollInstructionSnapshot) -> UUID:  # type: ignore[no-untyped-def]
    """Persist a minimal sequence + pending-roll row set consume_roll can act on.

    No real parent rows for story_id/character_id/originating_turn_id: the
    caller must use a plain (non-FK-enforcing) engine — see
    ``test_consume_roll_rejects_already_consumed_row``, which builds its own
    rather than the module ``session`` fixture (that one goes through
    ``persistence.database.create_engine``, which enables
    ``PRAGMA foreign_keys = ON``; Alembic's own migration-runner engine does
    not, which is why the 0017 precondition test can use synthetic UUIDs too).
    """
    from afterworlds.persistence.orm.rpg import (
        ActionResolutionSequenceORM,
        PendingRollRequestORM,
    )

    now = datetime.now(tz=UTC).isoformat()
    session.add(
        ActionResolutionSequenceORM(
            sequence_id=str(instr.sequence_id),
            story_id=str(uuid4()),
            node_id=str(uuid4()),
            character_id=str(uuid4()),
            session_id=str(uuid4()),
            originating_turn_id=str(uuid4()),
            status="active",
            current_interaction_kind="roll",
            resolved_steps_json="[]",
            provisional_effects_json="[]",
            created_at=now,
            updated_at=now,
        )
    )
    request_id = uuid4()
    session.add(
        PendingRollRequestORM(
            request_id=str(request_id),
            story_id=str(uuid4()),
            session_id=str(uuid4()),
            character_id=str(uuid4()),
            originating_turn_id=str(uuid4()),
            visibility="player",
            source_proposal_ref="test/stealth",
            status="pending",
            created_at=now,
            sequence_id=str(instr.sequence_id),
            step_id=str(instr.step_id),
            instruction_id=str(instr.instruction_id),
            instruction_revision=instr.instruction_revision,
            instruction_schema_version=instr.schema_version,
            instruction_snapshot_json=instr.model_dump_json(),
        )
    )
    session.commit()
    return request_id


def test_consume_roll_rejects_already_consumed_row() -> None:
    """A row consumed out-of-band is rejected cleanly, with zero events written.

    Does not isolate genuine cross-session interleaving (consume_roll has no
    injection point to pause mid-call) — end-to-end, this exercises both the
    pre-existing status check in _load_pending_and_instruction and the new
    atomic conditional UPDATE as defense-in-depth. The UPDATE's WHERE
    status='pending' + rowcount check is what actually closes the race under
    real concurrent sessions (SQLite serializes the two UPDATE statements;
    whichever commits second sees rowcount=0), which this test cannot force
    without a second real session/thread interleaved mid-call.

    Uses a plain, non-FK-enforcing engine (unlike the module ``session``
    fixture) so story_id/character_id/originating_turn_id can be synthetic —
    this test only cares about pending_roll_requests.status, not referential
    integrity to parent rows.
    """
    import sqlalchemy as sa

    from afterworlds.models.rpg import PlayerRollTermResult, RawPlayerRollSubmission
    from afterworlds.persistence.database import create_session_factory
    from afterworlds.persistence.orm.rpg import (
        ActionResolutionEventORM,
        PendingRollRequestORM,
    )
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
    from afterworlds.pipeline.rpg.pending import PendingRollAlreadyConsumedError
    from afterworlds.pipeline.rpg.sequence import ActionResolutionService

    engine = sa.create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = create_session_factory(engine)()
    try:
        term = _term(DiceSelectionRule.SUM_ALL)
        instr = _instruction(term)
        request_id = _seed_pending_roll(session, instr=instr)

        # Simulate a concurrent transaction that already consumed this row.
        session.query(PendingRollRequestORM).filter_by(
            request_id=str(request_id)
        ).update({"status": "consumed"})
        session.commit()

        svc = ActionResolutionService(
            adapter=D20RulesSystemAdapter(),
            dice_service=None,  # type: ignore[arg-type]
            session_factory=lambda: session,
        )
        submission = RawPlayerRollSubmission(
            source="inline_ui",
            pending_roll_request_id=request_id,
            expected_instruction_revision=instr.instruction_revision,
            term_results=(PlayerRollTermResult(term_id=term.term_id, values=(14,)),),
        )

        with pytest.raises(PendingRollAlreadyConsumedError):
            svc.consume_roll(
                session,
                submission=submission,
                rule_slice=None,
                overrides=[],
                gm_cheating=False,
            )

        assert session.query(ActionResolutionEventORM).count() == 0
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_consume_roll_rejects_out_of_range_aggregate_before_any_mutation() -> None:
    """An out-of-range aggregate report leaves the pending row and event
    ledger untouched — rejection happens before any write (Codex P1,
    aggregate_range fix, PR #129)."""
    import sqlalchemy as sa

    from afterworlds.models.rpg import PhysicalAggregateRollSubmission
    from afterworlds.persistence.database import create_session_factory
    from afterworlds.persistence.orm.rpg import (
        ActionResolutionEventORM,
        PendingRollRequestORM,
    )
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
    from afterworlds.pipeline.rpg.models import PendingRollInvalidAggregateError
    from afterworlds.pipeline.rpg.sequence import ActionResolutionService

    engine = sa.create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = create_session_factory(engine)()
    try:
        # 2d20kh1 (advantage): legal aggregate range is [1, 20].
        term = _term(DiceSelectionRule.KEEP_HIGHEST, count=2, keep_count=1)
        instr = _instruction(term)
        request_id = _seed_pending_roll(session, instr=instr)

        svc = ActionResolutionService(
            adapter=D20RulesSystemAdapter(),
            dice_service=None,  # type: ignore[arg-type]
            session_factory=lambda: session,
        )
        submission = PhysicalAggregateRollSubmission(
            source="physical_self_report",
            pending_roll_request_id=request_id,
            expected_instruction_revision=instr.instruction_revision,
            reported_aggregate=35,  # illegal for 2d20kh1 (max is 20)
        )

        with pytest.raises(PendingRollInvalidAggregateError):
            svc.consume_roll(
                session,
                submission=submission,
                rule_slice=None,
                overrides=[],
                gm_cheating=False,
            )

        assert session.query(ActionResolutionEventORM).count() == 0
        row = (
            session.query(PendingRollRequestORM)
            .filter_by(request_id=str(request_id))
            .one()
        )
        assert row.status == "pending"
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


# ---------------------------------------------------------------------------
# apply_adjustment — Issue #127 criteria 9/10 (PR #129 sibling audit)
#
# No adapter path populates adjustment_options in v1 (advantage/disadvantage
# is decided at instruction-build time, not offered post-hoc; parameterized
# mechanics like spell-slot upcasting are deferred — see the "Parameterized
# adjustments" Known Unknown). apply_adjustment's own state-transition logic
# is fully written and reachable by direct call, though: these tests
# hand-build an instruction WITH a populated adjustment_options tuple (the
# same "prove the engine, not proposal-pipeline reachability" pattern used
# for mixed/repeated pools in test_adapter.py) to prove that logic is
# correct, without building new adapter-side option generation.
# ---------------------------------------------------------------------------


def _adjustment_option(option_id: str = "advantage") -> RollAdjustmentOption:
    return RollAdjustmentOption(
        option_id=option_id,
        ability_id="luck",
        timing=RollAdjustmentTiming.PRE_ROLL,
        player_visible_label="Use Luck Point",
    )


def test_apply_adjustment_accepted_revises_instruction_without_new_phase() -> None:
    """Criterion 9: an eligible option revises the pending instruction and
    stays PENDING_ROLL -- no separate interaction phase is created."""
    import sqlalchemy as sa

    from afterworlds.models.enums import RpgInteractionPhase
    from afterworlds.persistence.database import create_session_factory
    from afterworlds.persistence.orm.rpg import ActionResolutionEventORM
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
    from afterworlds.pipeline.rpg.sequence import ActionResolutionService

    engine = sa.create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = create_session_factory(engine)()
    try:
        option = _adjustment_option("advantage")
        term = _term(DiceSelectionRule.SUM_ALL)
        instr = _instruction(term, adjustment_options=(option,))
        request_id = _seed_pending_roll(session, instr=instr)

        svc = ActionResolutionService(
            adapter=D20RulesSystemAdapter(),
            dice_service=None,  # type: ignore[arg-type]
            session_factory=lambda: session,
        )
        result = svc.apply_adjustment(
            session, pending_roll_request_id=request_id, option_id="advantage"
        )

        assert result.interaction_phase is RpgInteractionPhase.PENDING_ROLL
        assert result.pending_roll is not None
        assert result.pending_roll.instruction_revision == 2  # noqa: PLR2004

        events = session.query(ActionResolutionEventORM).all()
        assert len(events) == 1
        assert events[0].kind == "adjustment"
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_apply_adjustment_rejected_option_changes_nothing() -> None:
    """Criterion 10: an unsupported/mistimed option_id is rejected and
    mutates nothing -- no revision bump, no event written."""
    import sqlalchemy as sa

    from afterworlds.persistence.database import create_session_factory
    from afterworlds.persistence.orm.rpg import (
        ActionResolutionEventORM,
        PendingRollRequestORM,
    )
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
    from afterworlds.pipeline.rpg.models import ActionAdjustmentNotAllowedError
    from afterworlds.pipeline.rpg.sequence import ActionResolutionService

    engine = sa.create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = create_session_factory(engine)()
    try:
        option = _adjustment_option("advantage")
        term = _term(DiceSelectionRule.SUM_ALL)
        instr = _instruction(term, adjustment_options=(option,))
        request_id = _seed_pending_roll(session, instr=instr)

        svc = ActionResolutionService(
            adapter=D20RulesSystemAdapter(),
            dice_service=None,  # type: ignore[arg-type]
            session_factory=lambda: session,
        )

        with pytest.raises(ActionAdjustmentNotAllowedError):
            svc.apply_adjustment(
                session,
                pending_roll_request_id=request_id,
                option_id="nonexistent_option",
            )

        row = (
            session.query(PendingRollRequestORM)
            .filter_by(request_id=str(request_id))
            .one()
        )
        assert row.instruction_revision == 1
        assert session.query(ActionResolutionEventORM).count() == 0
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
