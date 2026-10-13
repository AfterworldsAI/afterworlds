"""CRD Issue 15c — actor-turn coordination (contract G1): legal transitions,
once-only edges by compare-and-swap, and an edge log the document can be
rebuilt from."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
import sqlalchemy as sa

from afterworlds.models.dnd5e_state import (
    ActiveTurn,
    SubjectReference,
    TurnCoordination,
)
from afterworlds.persistence.orm.dnd5e_state import RpgTurnEdgeORM
from afterworlds.services.dnd5e_state import coordination
from afterworlds.services.dnd5e_state.coordination import EdgeRefused, apply_edge
from afterworlds.services.dnd5e_state.errors import StaleRevisionError
from tests.services.dnd5e_state.conftest import NOW, Table, new_story

A = SubjectReference(kind="character", subject_id=uuid4())
B = SubjectReference(kind="creature", subject_id=uuid4())


def test_begin_opens_the_next_instance_and_end_closes_it() -> None:
    doc, begun = apply_edge(TurnCoordination(), "begin", A, begun_this_turn=False)
    assert doc.active == ActiveTurn(subject=A, instance=1)
    assert (begun.instance, doc.next_instance) == (1, 2)
    doc, ended = apply_edge(doc, "end", A, begun_this_turn=True)
    assert doc.active is None and ended.instance == 1


@pytest.mark.parametrize(
    ("document", "kind", "subject", "begun"),
    [
        # A turn is still active.
        (TurnCoordination(active=ActiveTurn(subject=A, instance=1)), "begin", B, False),
        # The named subject's turn is not the active one.
        (TurnCoordination(active=ActiveTurn(subject=A, instance=1)), "end", B, False),
        (TurnCoordination(), "end", A, False),
        # One delivered Turn begins at most one actor turn.
        (TurnCoordination(), "begin", B, True),
        # A cast member takes no turns; no other edge kind exists.
        (
            TurnCoordination(),
            "begin",
            SubjectReference(kind="cast_member", subject_id=uuid4()),
            False,
        ),
        (TurnCoordination(), "round", A, False),
    ],
)
def test_an_illegal_transition_refuses(
    document: TurnCoordination, kind: str, subject: SubjectReference, begun: bool
) -> None:
    with pytest.raises(EdgeRefused):
        apply_edge(document, kind, subject, begun_this_turn=begun)


def _commit(table: Table, story, read, after, *edges) -> int:  # type: ignore[no-untyped-def]
    with table.factory() as session:
        revision = coordination.commit(
            session, read, after, edges, turn_id=uuid4(), now=NOW
        )
        session.commit()
        return revision


def test_edges_commit_once_and_the_log_rebuilds_the_document(table: Table) -> None:
    with table.factory() as session:
        story = new_story(session)
        session.commit()
    with table.factory() as session:
        read = coordination.read(session, story)
    assert read.revision == 0
    doc, begin_a = apply_edge(read.document, "begin", A, begun_this_turn=False)
    doc, end_a = apply_edge(doc, "end", A, begun_this_turn=True)
    assert _commit(table, story, read, doc, begin_a, end_a) == 1

    # A turn that read revision 0 cannot commit over revision 1.
    stale_doc, stale_edge = apply_edge(read.document, "begin", B, begun_this_turn=False)
    with pytest.raises(StaleRevisionError):
        _commit(table, story, read, stale_doc, stale_edge)

    with table.factory() as session:
        current = coordination.read(session, story)
    doc, begin_b = apply_edge(current.document, "begin", B, begun_this_turn=False)
    assert _commit(table, story, current, doc, begin_b) == 2
    with pytest.raises(StaleRevisionError):
        _commit(table, story, current, doc, begin_b)

    with table.factory() as session:
        rows = session.execute(
            sa.select(RpgTurnEdgeORM)
            .where(RpgTurnEdgeORM.story_id == str(story))
            .order_by(RpgTurnEdgeORM.sequence)
        ).scalars()
        log = [(r.sequence, r.kind, r.subject_id, r.turn_instance) for r in rows]
        stored = coordination.read(session, story).document
    assert log == [
        (1, "begin", str(A.subject_id), 1),
        (2, "end", str(A.subject_id), 1),
        (3, "begin", str(B.subject_id), 2),
    ]
    rebuilt = TurnCoordination()
    for _, kind, subject_id, _ in log:
        subject = A if subject_id == str(A.subject_id) else B
        rebuilt, _edge = apply_edge(rebuilt, kind, subject, begun_this_turn=False)
    assert rebuilt == stored


def test_a_once_per_turn_use_needs_the_subjects_turn_and_a_new_turn_clears_it(
    table: Table,
) -> None:
    from afterworlds.services.dnd5e_state.coordination import take_use

    key = "equipment.weapons.cleave/cleave"
    with pytest.raises(EdgeRefused):
        take_use(TurnCoordination(), A, key)
    doc, _ = apply_edge(TurnCoordination(), "begin", A, begun_this_turn=False)
    used = take_use(doc, A, key)
    with pytest.raises(EdgeRefused):
        take_use(used, A, key)
    with pytest.raises(EdgeRefused):
        take_use(doc, B, key)
    ended, _ = apply_edge(used, "end", A, begun_this_turn=False)
    renewed, _ = apply_edge(ended, "begin", A, begun_this_turn=False)
    assert renewed.uses == () and take_use(renewed, A, key).uses

    # A use alone changes the document, so it commits.
    with table.factory() as session:
        story = new_story(session)
        session.commit()
    with table.factory() as session:
        read = coordination.read(session, story)
    doc, begin = apply_edge(read.document, "begin", A, begun_this_turn=False)
    assert _commit(table, story, read, doc, begin) == 1
    with table.factory() as session:
        current = coordination.read(session, story)
    assert _commit(table, story, current, take_use(current.document, A, key)) == 2


# ---------------------------------------------------------------------------
# Delivery read set: uses are logged events, read-only coordination reads and
# holdings are rechecked at commit (codex-c7-delivery-review)
# ---------------------------------------------------------------------------


def _log(table: Table, story: Any) -> list[tuple[str, coordination.AppliedEdge]]:
    with table.factory() as session:
        rows = session.execute(
            sa.select(RpgTurnEdgeORM)
            .where(RpgTurnEdgeORM.story_id == str(story))
            .order_by(RpgTurnEdgeORM.sequence)
        ).scalars()
        return [
            (
                r.turn_id,
                coordination.AppliedEdge(
                    r.kind,
                    SubjectReference(kind=r.subject_kind, subject_id=r.subject_id),
                    r.turn_instance,
                    r.use_key,
                ),
            )
            for r in rows
        ]


def test_a_use_only_delivery_is_logged_and_the_log_replays_it(table: Table) -> None:
    key = "equipment.weapons.cleave/cleave"
    with table.factory() as session:
        story = new_story(session)
        session.commit()
    with table.factory() as session:
        read = coordination.read(session, story)
    doc, begin = apply_edge(read.document, "begin", A, begun_this_turn=False)
    _commit(table, story, read, doc, begin)
    with table.factory() as session:
        current = coordination.read(session, story)
    used, event = coordination.use_event(current.document, A, key)
    assert event == coordination.AppliedEdge("use", A, 1, key)
    _commit(table, story, current, used, event)
    with table.factory() as session:
        stored = coordination.read(session, story).document
    assert stored.uses and coordination.replay(_log(table, story)) == stored


def test_a_read_only_coordination_snapshot_is_rechecked_at_commit(
    table: Table,
) -> None:
    with table.factory() as session:
        story = new_story(session)
        session.commit()
    with table.factory() as session:
        stale = coordination.read(session, story)  # absent: revision 0
    doc, begin = apply_edge(stale.document, "begin", A, begun_this_turn=False)
    _commit(table, story, stale, doc, begin)  # a concurrent delivery
    # A turn that only read the (then absent) coordination writes nothing,
    # yet cannot commit timing computed from it.
    with pytest.raises(StaleRevisionError):
        _commit(table, story, stale, stale.document)
    with table.factory() as session:
        current = coordination.read(session, story)
    assert _commit(table, story, current, current.document) == current.revision


def test_a_holdings_change_after_the_read_refuses_the_commit(
    table: Table, srd_content: Any
) -> None:
    from afterworlds.services.dnd5e_state import holdings
    from afterworlds.services.dnd5e_state.holdings import Holder, HolderKind
    from afterworlds.services.dnd5e_state.turn import require_holdings_unchanged
    from tests.services.dnd5e_state.test_holdings import _bound, _setup

    _, sheet = _setup(table)
    index = _bound(table, sheet, srd_content)
    holder = Holder(HolderKind.CHARACTER, sheet)
    with table.factory() as s, s.begin():
        club = holdings.create_item(
            s, index, holder, "equipment.weapons.club", equipped=True, now=NOW
        )
    with table.factory() as s:
        snapshot = holdings.items_held_by(s, holder)
        require_holdings_unchanged(s, holder, snapshot)  # unchanged: passes
    with table.factory() as s, s.begin():  # unequipped: its revision moves
        holdings.update_item_use(
            s,
            club.item_id,
            expected_revision=club.revision,
            equipped=False,
            attuned=False,
            charges_remaining=None,
            now=NOW,
        )
    with table.factory() as s, pytest.raises(StaleRevisionError):
        require_holdings_unchanged(s, holder, snapshot)
    with table.factory() as s:
        current = holdings.items_held_by(s, holder)
    with table.factory() as s, s.begin():  # an item gained
        holdings.create_item(s, index, holder, "equipment.weapons.dagger", now=NOW)
    with table.factory() as s, pytest.raises(StaleRevisionError):
        require_holdings_unchanged(s, holder, current)
