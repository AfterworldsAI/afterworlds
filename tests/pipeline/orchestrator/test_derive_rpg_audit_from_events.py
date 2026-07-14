"""Unit tests for _derive_rpg_audit_from_events (the Final Audit Projection).

CRD Issue 15b (ADR-015b 15b-34). Issue #127 criterion 45 (roll-only audit
derivation) and criterion 58 (hidden-roll internal retention vs. Writer
redaction) — PR #129 sibling audit closing a gap where these had no
dedicated test exercising the projection function directly.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa

import afterworlds.persistence.orm.node  # noqa: F401 — registers "turns"
import afterworlds.persistence.orm.rpg  # noqa: F401
from afterworlds.models.enums import DiceSelectionRule, ResolvedStepKind, RollPurpose
from afterworlds.models.rpg import (
    AdjustmentEventPayload,
    MechanicalDecisionEventPayload,
    MechanicalDecisionOptionSnapshot,
    MechanicalDecisionSnapshot,
    RollEventPayload,
    RollInstructionSnapshot,
    RollTerm,
)
from afterworlds.persistence.database import create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.rpg import RpgRollAuditORM
from afterworlds.pipeline.orchestrator.service import _derive_rpg_audit_from_events
from afterworlds.pipeline.rpg.sequence import _append_event

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _instruction(dc: int | None = None) -> RollInstructionSnapshot:
    return RollInstructionSnapshot(
        instruction_id=uuid4(),
        instruction_revision=1,
        purpose=RollPurpose.SKILL_CHECK,
        terms=(
            RollTerm(
                term_id=uuid4(),
                count=1,
                sides=20,
                selection_rule=DiceSelectionRule.SUM_ALL,
                keep_count=None,
            ),
        ),
        modifier_components=(),
        display_expression="1d20",
        display_label="Perception Check",
        source_rule_refs=(),
        adjustment_options=(),
        sequence_id=uuid4(),
        step_id=uuid4(),
        dc=dc,
    )


def _roll_payload(
    *, kind: ResolvedStepKind, dc: int | None, outcome: str
) -> RollEventPayload:
    return RollEventPayload(
        kind=kind,  # type: ignore[arg-type]
        instruction_snapshot=_instruction(dc=dc),
        submission_source=None,
        pending_roll_request_id=(
            uuid4() if kind is ResolvedStepKind.PLAYER_ROLL else None
        ),
        raw_input_json="[]",
        aggregate_input_json=None,
        derived_selections_json="[]",
        subtotal=14,
        total=19,
        outcome=outcome,  # type: ignore[arg-type]
        gm_cheating_at_roll=False,
    )


def _seed(session, story_id, session_id, character_id, sequence_id):  # type: ignore[no-untyped-def]
    def append(kind: ResolvedStepKind, payload: object) -> None:
        _append_event(
            session,
            sequence_id=sequence_id,
            step_id=uuid4(),
            story_id=story_id,
            session_id=session_id,
            character_id=character_id,
            kind=kind,
            provisional_effects_json="[]",
            payload=payload,  # type: ignore[arg-type]
        )
        # _next_event_order queries committed/flushed rows; without an
        # intervening flush, back-to-back appends in one session would all
        # compute the same order (autoflush=False project-wide).
        session.flush()

    return append


def test_only_roll_kinds_produce_audit_rows() -> None:
    """Criterion 45: adjustment and mechanical-decision events must never
    populate rpg_roll_audit, even when mixed with real roll events."""
    engine = sa.create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = create_session_factory(engine)()
    try:
        story_id, session_id, character_id, sequence_id = (
            uuid4(),
            uuid4(),
            uuid4(),
            uuid4(),
        )
        append = _seed(session, story_id, session_id, character_id, sequence_id)

        append(
            ResolvedStepKind.PLAYER_ROLL,
            _roll_payload(kind=ResolvedStepKind.PLAYER_ROLL, dc=15, outcome="success"),
        )
        append(
            ResolvedStepKind.ADJUSTMENT,
            AdjustmentEventPayload(
                resulting_instruction_snapshot=_instruction(),
                accepted_adjustment_option_id="advantage",
            ),
        )
        append(
            ResolvedStepKind.MECHANICAL_DECISION,
            MechanicalDecisionEventPayload(
                decision_snapshot=MechanicalDecisionSnapshot(
                    decision_id=uuid4(),
                    decision_revision=1,
                    prompt="Choose a condition.",
                    options=(
                        MechanicalDecisionOptionSnapshot(
                            option_id="poisoned",
                            player_visible_label="Poisoned",
                            source_rule_ref=None,
                            provisional_effects_json="[]",
                        ),
                    ),
                    source_rule_refs=(),
                    sequence_id=sequence_id,
                    step_id=uuid4(),
                ),
                accepted_decision_option_id="poisoned",
            ),
        )
        session.commit()

        turn_id = uuid4()
        _derive_rpg_audit_from_events(session, sequence_id=sequence_id, turn_id=turn_id)
        session.commit()

        rows = session.query(RpgRollAuditORM).filter_by(turn_id=str(turn_id)).all()
        assert len(rows) == 1
        assert rows[0].outcome == "success"
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_hidden_roll_event_projects_complete_internal_audit_row() -> None:
    """Criterion 58: a HIDDEN_ROLL event retains complete internal total/
    dc/outcome in the projected audit row -- identical in shape to a
    player or AI roll event. Writer-facing redaction (WriterAdjudicationView
    nulling these for HIDDEN visibility) is separate, untouched code
    (tests/pipeline/rpg/test_adapter.py) -- this test proves the audit
    row itself is never redacted."""
    engine = sa.create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = create_session_factory(engine)()
    try:
        story_id, session_id, character_id, sequence_id = (
            uuid4(),
            uuid4(),
            uuid4(),
            uuid4(),
        )
        append = _seed(session, story_id, session_id, character_id, sequence_id)
        append(
            ResolvedStepKind.HIDDEN_ROLL,
            _roll_payload(kind=ResolvedStepKind.HIDDEN_ROLL, dc=15, outcome="failure"),
        )
        session.commit()

        turn_id = uuid4()
        _derive_rpg_audit_from_events(session, sequence_id=sequence_id, turn_id=turn_id)
        session.commit()

        row = session.query(RpgRollAuditORM).filter_by(turn_id=str(turn_id)).one()
        assert row.visibility == "hidden"
        assert row.source == "hidden"
        assert row.total == 19  # noqa: PLR2004
        assert row.dc == 15  # noqa: PLR2004
        assert row.outcome == "failure"
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
