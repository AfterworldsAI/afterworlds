"""Actor-turn coordination — CRD Issue 15c (timing contract G1).

A story's :class:`~afterworlds.models.dnd5e_state.TurnCoordination` changes
only through explicit GameMaster ``begin_turn``/``end_turn`` edges, each
validated by :func:`apply_edge`:

* ``begin`` needs no active turn, and opens the next turn instance;
* ``end`` needs the named subject's turn to be the active one;
* a delivered Turn applies at most one ``begin``, so one response cannot
  cycle begin/end/begin to reset a per-turn budget.

Nothing decides whose turn is next (no round or initiative order). A turn's
edges commit in its delivery transaction by compare-and-swap on the revision
it read (:func:`commit`), and each is appended to ``rpg_turn_edges``, from
which the document is reconstructable.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session

from afterworlds.models.dnd5e_state import (
    ActiveTurn,
    SubjectReference,
    TurnCoordination,
    TurnUse,
)
from afterworlds.persistence.orm.dnd5e_state import (
    RpgTurnCoordinationORM,
    RpgTurnEdgeORM,
)
from afterworlds.services.dnd5e_state.errors import StaleRevisionError

__all__ = [
    "AppliedEdge",
    "EdgeRefused",
    "StoredCoordination",
    "apply_edge",
    "commit",
    "read",
    "take_use",
]


class EdgeRefused(ValueError):
    """An edge that is not a legal transition of the coordination."""


@dataclass(frozen=True)
class StoredCoordination:
    story_id: UUID
    #: 0 when the story has no coordination row yet.
    revision: int
    document: TurnCoordination


@dataclass(frozen=True)
class AppliedEdge:
    kind: str
    subject: SubjectReference
    instance: int


def read(session: Session, story_id: UUID) -> StoredCoordination:
    row = session.get(RpgTurnCoordinationORM, str(story_id))
    if row is None:
        return StoredCoordination(story_id, 0, TurnCoordination())
    return StoredCoordination(
        story_id, row.revision, TurnCoordination.model_validate(row.document)
    )


def apply_edge(
    document: TurnCoordination,
    kind: str,
    subject: SubjectReference,
    *,
    begun_this_turn: bool,
) -> tuple[TurnCoordination, AppliedEdge]:
    """*document* after one edge, or :class:`EdgeRefused`. Pure."""
    if subject.kind not in ("character", "creature"):
        raise EdgeRefused(f"a {subject.kind} takes no turns")
    active = document.active
    if kind == "begin":
        if begun_this_turn:
            raise EdgeRefused("a delivered Turn begins at most one actor turn")
        if active is not None:
            raise EdgeRefused(
                f"{active.subject.kind} {active.subject.subject_id}'s turn is "
                "still active; end it first"
            )
        instance = document.next_instance
        after = document.model_copy(
            update={
                "active": ActiveTurn(subject=subject, instance=instance),
                "next_instance": instance + 1,
                "uses": (),
            }
        )
        return after, AppliedEdge(kind, subject, instance)
    if kind == "end":
        if active is None or active.subject != subject:
            raise EdgeRefused(
                f"{subject.kind} {subject.subject_id}'s turn is not the active one"
            )
        return document.model_copy(update={"active": None}), AppliedEdge(
            kind, subject, active.instance
        )
    raise EdgeRefused(f"{kind!r} is not an actor-turn edge")


def take_use(
    document: TurnCoordination, subject: SubjectReference, key: str
) -> TurnCoordination:
    """*document* after *subject* takes its once-per-turn *key* use, or
    :class:`EdgeRefused`: it must be *subject*'s active turn, and unused."""
    active = document.active
    if active is None or active.subject != subject:
        raise EdgeRefused(
            f"{key} is once per turn, and it is not {subject.kind} "
            f"{subject.subject_id}'s turn"
        )
    use = TurnUse(instance=active.instance, subject=subject, key=key)
    if use in document.uses:
        raise EdgeRefused(f"{key} was already used this turn")
    return document.model_copy(update={"uses": (*document.uses, use)})


def commit(
    session: Session,
    read_state: StoredCoordination,
    after: TurnCoordination,
    edges: tuple[AppliedEdge, ...],
    *,
    turn_id: UUID,
    now: str,
) -> int:
    """Write *after* over the revision the turn read and append *edges*;
    returns the new revision. A concurrent change raises
    :class:`StaleRevisionError` so the delivery transaction rolls back."""
    if not edges and after == read_state.document:
        return read_state.revision
    story = str(read_state.story_id)
    revision = read_state.revision + 1
    document = after.model_dump(mode="json")
    if read_state.revision == 0:
        if session.get(RpgTurnCoordinationORM, story) is not None:
            raise StaleRevisionError(f"story {story}'s turn coordination changed")
        session.add(
            RpgTurnCoordinationORM(
                story_id=story, revision=revision, document=document, updated_at=now
            )
        )
        session.flush()
    else:
        result = session.execute(
            sa.update(RpgTurnCoordinationORM)
            .where(
                RpgTurnCoordinationORM.story_id == story,
                RpgTurnCoordinationORM.revision == read_state.revision,
            )
            .values(revision=revision, document=document, updated_at=now)
        )
        if result.rowcount != 1:  # type: ignore[attr-defined]
            raise StaleRevisionError(f"story {story}'s turn coordination changed")
    last = session.execute(
        sa.select(sa.func.max(RpgTurnEdgeORM.sequence)).where(
            RpgTurnEdgeORM.story_id == story
        )
    ).scalar()
    for offset, edge in enumerate(edges, start=1):
        session.add(
            RpgTurnEdgeORM(
                edge_id=str(uuid4()),
                story_id=story,
                sequence=(last or 0) + offset,
                turn_id=str(turn_id),
                kind=edge.kind,
                subject_kind=edge.subject.kind,
                subject_id=str(edge.subject.subject_id),
                turn_instance=edge.instance,
                coordination_revision=read_state.revision,
                recorded_at=now,
            )
        )
    session.flush()
    return revision
