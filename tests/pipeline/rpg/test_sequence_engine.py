"""CRD Issue 15b: the generalized term engine and its provenance.

Synthetic instructions only: these pin the engine's arithmetic and the event
and audit projections for shapes the contract admits (several terms, the same
die repeated, keep-highest/keep-lowest of many, a subtracted term, hidden
modifiers). They claim no rules mechanic that produces any of them.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from afterworlds.models.enums import (
    DiceSelectionRule,
    ModifierVisibility,
    ResolvedStepKind,
    RollContribution,
    RollPurpose,
)
from afterworlds.models.rpg import (
    ActionResolutionEvent,
    DiceResult,
    NaturalOutcome,
    PlayerRollTermResult,
    RawPlayerRollSubmission,
    RollInstructionSnapshot,
    RollModifierComponent,
    RollTerm,
    SubjectRef,
)
from afterworlds.persistence.orm.rpg import RpgRollAuditORM
from afterworlds.pipeline.rpg import dice as engine
from afterworlds.pipeline.rpg.models import (
    ActionSequenceIntegrityError,
    PendingRollInvalidValueError,
    PendingRollTermMismatchError,
)
from afterworlds.pipeline.rpg.sequence import _roll_payload, _validate_roll, audit_rows
from afterworlds.pipeline.rpg.steps import AcceptedRoll

ME = SubjectRef(kind="character", subject_id=uuid4())
KH, KL, ALL = (
    DiceSelectionRule.KEEP_HIGHEST,
    DiceSelectionRule.KEEP_LOWEST,
    DiceSelectionRule.SUM_ALL,
)


def _term(
    count: int,
    sides: int,
    rule: DiceSelectionRule = ALL,
    keep: int | None = None,
    contribution: RollContribution = RollContribution.ADD,
) -> RollTerm:
    return RollTerm(
        term_id=uuid4(),
        count=count,
        sides=sides,
        selection_rule=rule,
        keep_count=keep,
        contribution=contribution,
    )


def _modifier(value: int, visible: bool = True) -> RollModifierComponent:
    return RollModifierComponent(
        modifier_id=uuid4(),
        label="Bonus",
        value=value,
        visibility=(
            ModifierVisibility.PLAYER_VISIBLE if visible else ModifierVisibility.HIDDEN
        ),
        source_kind="test",
    )


def _snapshot(
    *terms: RollTerm, modifiers: tuple[RollModifierComponent, ...] = (), **kw: Any
) -> RollInstructionSnapshot:
    return RollInstructionSnapshot(
        instruction_id=uuid4(),
        instruction_revision=1,
        purpose=kw.pop("purpose", RollPurpose.DAMAGE),
        terms=terms,
        modifier_components=modifiers,
        display_expression="engine",
        display_label="Engine roll",
        source_rule_refs=(),
        sequence_id=kw.pop("sequence_id", uuid4()),
        step_id=kw.pop("step_id", uuid4()),
        roller=ME,
        operation_index=0,
        die_index=0,
        **kw,
    )


# ---------------------------------------------------------------------------
# Selection: keep-highest/keep-lowest of many, ties, mixed and repeated pools
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("rule", "values", "kept", "subtotal"),
    [
        (KH, (6, 1, 6, 3), (0, 2, 3), 15),
        (KL, (6, 1, 6, 3), (0, 1, 3), 10),  # the earlier 6 of two
        (KL, (2, 2, 5, 2), (0, 1, 3), 6),  # ties keep the earlier die
        (KH, (4, 4, 4, 4), (0, 1, 2), 12),
    ],
    ids=["kh3", "kl3", "kl3-ties", "kh3-all-equal"],
)
def test_multi_keep_selects_in_roll_order(
    rule: DiceSelectionRule,
    values: tuple[int, ...],
    kept: tuple[int, ...],
    subtotal: int,
) -> None:
    term = _term(4, 6, rule, 3)
    (derived,) = engine.derive(_snapshot(term), {term.term_id: values})
    assert derived.values == values  # omitted dice stay reconstructable
    assert derived.selected_indices == kept
    assert derived.contribution_applied_subtotal == subtotal


def test_mixed_repeated_and_subtracted_terms_each_derive_alone() -> None:
    d8, d6a, d6b = _term(1, 8), _term(2, 6), _term(2, 6)
    minus = _term(1, 4, contribution=RollContribution.SUBTRACT)
    snapshot = _snapshot(d8, d6a, d6b, minus, modifiers=(_modifier(2),))
    derived = engine.derive(
        snapshot,
        {
            d8.term_id: (5,),
            d6a.term_id: (1, 6),
            d6b.term_id: (3, 3),
            minus.term_id: (4,),
        },
    )
    assert [d.term_id for d in derived] == [
        d8.term_id,
        d6a.term_id,
        d6b.term_id,
        minus.term_id,
    ]
    assert [d.contribution_applied_subtotal for d in derived] == [5, 7, 6, -4]
    # The aggregate range counts kept dice only, reverses a subtracted term
    # and adds the visible modifiers.
    assert engine.aggregate_range(snapshot) == (1 + 2 + 2 - 4 + 2, 8 + 12 + 12 - 1 + 2)
    keep = _snapshot(_term(4, 6, KH, 3))
    assert engine.aggregate_range(keep) == (3, 18)


def test_a_natural_face_exists_only_for_one_kept_die() -> None:
    assert engine.single_face(_snapshot(_term(1, 20)))
    assert engine.single_face(_snapshot(_term(2, 20, KH, 1)))
    assert not engine.single_face(_snapshot(_term(2, 6)))
    assert not engine.single_face(_snapshot(_term(1, 20), _term(1, 4)))


def test_outcome_prefers_a_fixed_natural_then_the_target() -> None:
    snapshot = _snapshot(
        _term(1, 20),
        purpose=RollPurpose.ATTACK,
        dc=15,
        natural_outcomes=(
            NaturalOutcome(face=1, outcome="failure"),
            NaturalOutcome(face=20, outcome="critical_success"),
        ),
    )
    assert engine.outcome(snapshot, 30, 1) == "failure"
    assert engine.outcome(snapshot, 3, 20) == "critical_success"
    assert engine.outcome(snapshot, 15, 10) == "success"
    assert engine.outcome(snapshot, 14, 10) == "failure"
    assert engine.outcome(_snapshot(_term(2, 6)), 9, None) == "undetermined"


@pytest.mark.parametrize("expression", ["4d6kh0", "4d6kh5", "1d20+5", "2d6-1", "d20"])
def test_expressions_carry_no_arithmetic_and_bounded_keeps(expression: str) -> None:
    with pytest.raises(ValueError):
        engine.parse_expression(expression)


# ---------------------------------------------------------------------------
# Validation of raw multi-term submissions (stored snapshot only)
# ---------------------------------------------------------------------------


def _raw(
    snapshot: RollInstructionSnapshot, *terms: tuple[UUID, tuple[int, ...]]
) -> Any:
    return RawPlayerRollSubmission(
        source="inline_ui",
        pending_roll_request_id=uuid4(),
        expected_instruction_revision=snapshot.instruction_revision,
        term_results=tuple(PlayerRollTermResult(term_id=t, values=v) for t, v in terms),
    )


def test_each_term_is_submitted_exactly_once_with_its_own_count() -> None:
    a, b = _term(4, 6, KH, 3), _term(2, 6)
    snapshot = _snapshot(a, b)
    for bad, error in (
        (_raw(snapshot, (a.term_id, (1, 2, 3, 4))), PendingRollTermMismatchError),
        (
            _raw(snapshot, (a.term_id, (1, 2, 3, 4)), (a.term_id, (1, 2, 3, 4))),
            PendingRollTermMismatchError,
        ),
        (
            _raw(snapshot, (a.term_id, (1, 2, 3)), (b.term_id, (1, 2))),
            PendingRollInvalidValueError,
        ),
        (
            _raw(snapshot, (a.term_id, (1, 2, 3, 7)), (b.term_id, (1, 2))),
            PendingRollInvalidValueError,
        ),
    ):
        with pytest.raises(error):
            _validate_roll(snapshot, bad)
    accepted = _validate_roll(
        snapshot, _raw(snapshot, (b.term_id, (5, 6)), (a.term_id, (6, 1, 6, 3)))
    )
    assert accepted.result.chosen == 15 + 11
    assert accepted.result.raw_rolls == (6, 1, 6, 3, 5, 6)


# ---------------------------------------------------------------------------
# Provenance: the event payload and the final audit row from it alone
# ---------------------------------------------------------------------------


def _event(payload: Any, snapshot: RollInstructionSnapshot) -> ActionResolutionEvent:
    return ActionResolutionEvent(
        event_id=uuid4(),
        sequence_id=snapshot.sequence_id,
        step_id=snapshot.step_id,
        story_id=uuid4(),
        session_id=uuid4(),
        character_id=ME.subject_id,
        event_order=1,
        kind=payload.kind,
        mechanical_provenance="{}",
        provisional_effects_json='[{"x": 1}]',
        created_at=datetime(2026, 10, 15, tzinfo=UTC),
        payload=payload,
    )


def test_a_multi_keep_roll_event_and_its_audit_row_carry_every_fact() -> None:
    a, b = _term(4, 6, KH, 3), _term(1, 4, contribution=RollContribution.SUBTRACT)
    snapshot = _snapshot(
        a, b, modifiers=(_modifier(2), _modifier(-1, visible=False)), dc=12
    )
    accepted = _validate_roll(
        snapshot, _raw(snapshot, (a.term_id, (6, 1, 6, 3)), (b.term_id, (2,)))
    )
    payload = _roll_payload(accepted, gm_cheating=False)
    derived = json.loads(payload.derived_selections_json)
    assert [d["selected_indices"] for d in derived] == [[0, 2, 3], [0]]
    assert payload.subtotal == 15 - 2
    assert payload.total == 13 + 2 - 1  # the hidden modifier counts
    assert payload.outcome == "success"  # no single face: the total decides
    assert json.loads(payload.raw_input_json or "") == [
        {"term_id": str(a.term_id), "values": [6, 1, 6, 3]},
        {"term_id": str(b.term_id), "values": [2]},
    ]

    event = _event(payload, snapshot)
    turn_id = uuid4()
    (row,) = audit_rows((event,), turn_id)
    expected = {
        "turn_id": str(turn_id),
        "story_id": str(event.story_id),
        "session_id": str(event.session_id),
        "character_id": str(event.character_id),
        "check_label": snapshot.display_label,
        "visibility": "player",
        "expression": snapshot.display_expression,
        "raw_rolls_json": json.dumps([6, 1, 6, 3, 2]),  # omitted dice too
        "total": 14,
        "dc": 12,
        "outcome": "success",
        "source": "player",
        "gm_cheating_at_roll": False,
        "sheet_effects_json": event.provisional_effects_json,
        "created_at": event.created_at.isoformat(),
        "sequence_id": str(snapshot.sequence_id),
        "step_id": str(snapshot.step_id),
        "pending_roll_request_id": str(accepted.pending_roll_request_id),
        "instruction_id": str(snapshot.instruction_id),
        "instruction_revision": 1,
        "instruction_schema_version": 1,
        "instruction_snapshot_json": snapshot.model_dump_json(),
        "submission_source": "inline_ui",
        "raw_values_complete": True,
        "contest_resolution_json": None,
    }
    assert {k: getattr(row, k) for k in expected} == expected
    assert [m["value"] for m in json.loads(row.modifiers_json)] == [2, -1]
    # Field-complete: every audit column is one the projection sets (or the
    # table's own rowid), so none silently falls back to a default.
    columns = {c.name for c in RpgRollAuditORM.__table__.columns}
    assert columns - set(expected) - {"modifiers_json"} == {"global_sequence"}


def test_an_aggregate_only_report_audits_no_dice_and_incomplete_values() -> None:
    term = _term(2, 6)
    snapshot = _snapshot(term, modifiers=(_modifier(1),))
    accepted = AcceptedRoll(
        snapshot,
        DiceResult(expression="2d6", raw_rolls=(), chosen=8),
        ResolvedStepKind.PLAYER_ROLL,
        pending_roll_request_id=uuid4(),
        reported_aggregate=9,
        source="physical_self_report",
    )
    payload = _roll_payload(accepted, gm_cheating=False)
    assert (payload.subtotal, payload.total, payload.derived_selections_json) == (
        None,
        9,
        "[]",
    )
    (row,) = audit_rows((_event(payload, snapshot),), uuid4())
    assert (row.raw_rolls_json, row.raw_values_complete) == ("[]", False)


def test_a_backend_die_must_be_its_terms_whole_pool() -> None:
    term = _term(4, 6, KH, 3)
    snapshot = _snapshot(term)
    for raw, chosen in (
        ((6, 6, 6), 18),
        ((6, 1, 6, 3), 16),
    ):  # short pool; wrong kept sum
        with pytest.raises(ActionSequenceIntegrityError):
            _roll_payload(
                AcceptedRoll(
                    snapshot,
                    DiceResult(expression="4d6kh3", raw_rolls=raw, chosen=chosen),
                    ResolvedStepKind.AI_ROLL,
                ),
                gm_cheating=False,
            )
