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
from uuid import uuid4

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
    RollContribution,
    RollPurpose,
)
from afterworlds.models.rpg import (
    AdjustmentEventPayload,
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


def _instruction(*terms: RollTerm) -> RollInstructionSnapshot:
    return RollInstructionSnapshot(
        instruction_id=uuid4(),
        instruction_revision=1,
        purpose=RollPurpose.SKILL_CHECK,
        terms=tuple(terms),
        modifier_components=(),
        display_expression="test",
        display_label="Test Check",
        source_rule_refs=(),
        adjustment_options=(),
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
