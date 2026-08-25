"""Recurrence survives persistence, reconstruction, and the digest — CRD Issue 5d.

``ComponentDraft.recurs`` is representation schema 4's only *component* key, so
it is the only schema-4 addition that reaches a column rather than riding the
family-keyed fact payload. That makes it the one addition whose round trip can
fail in storage rather than in serialization, and this module is where that is
proved rather than assumed.

Four properties:

* a component stating a cadence reconstructs with the same cadence;
* a component stating none reconstructs as ``None`` — NULL is a real state, not
  a defect awaiting repair;
* the cadence is identity-bearing, so persisting a different one is a different
  projection and the persisted-state digest moves with it; and
* a stored value outside the declared vocabulary fails reconstruction instead of
  silently becoming a different cadence.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.persistence import (
    PersistedStateReconstructionError,
    compute_persisted_state_digest,
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_persisted_state,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.representation import (
    Recurrence,
    RecurrenceBoundary,
    RollActor,
)
from afterworlds.persistence.orm.mechanical import MechanicalComponentORM
from tests.ingestion.mechanical.conftest import (
    NOW,
    RELEASE_BINDING,
    build_ledger,
    build_representation,
    candidate_of,
)

PER_TURN = Recurrence(boundary=RecurrenceBoundary.END_OF_TURN, whose=RollActor.SUBJECT)
PER_DAY = Recurrence(boundary=RecurrenceBoundary.END_OF_DAY)


def _with_recurrence(recurs: Recurrence | None):
    """The bounded fixture, with a cadence on its first component."""
    representation = build_representation()
    components = list(representation.components)
    components[0] = replace(components[0], recurs=recurs)
    return replace(representation, components=tuple(components))


def _persisted(session: Session, recurs: Recurrence | None):
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), _with_recurrence(recurs))
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()
    return identified


def test_a_stated_cadence_survives_the_round_trip(session: Session) -> None:
    """Persist, reconstruct, and get the same value object back."""
    identified = _persisted(session, PER_TURN)
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert rebuilt.representation.components[0].recurs == PER_TURN
    assert verify_persisted_state(session, identified.projection_uuid) == ()


def test_a_day_boundary_cadence_round_trips_without_a_whose(session: Session) -> None:
    """``whose`` is absent for a day boundary, and absent is what comes back.

    A turn belongs to a creature and a day does not, so this is the shape the
    invariant requires rather than an incomplete one.
    """
    identified = _persisted(session, PER_DAY)
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert rebuilt.representation.components[0].recurs == PER_DAY
    assert rebuilt.representation.components[0].recurs.whose is None  # type: ignore[union-attr]


def test_no_cadence_reconstructs_as_none_rather_than_a_defect(
    session: Session,
) -> None:
    """NULL is a real state: a component whose effect the source does not repeat."""
    identified = _persisted(session, None)
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert rebuilt.representation.components[0].recurs is None
    assert verify_persisted_state(session, identified.projection_uuid) == ()


def test_the_cadence_is_identity_bearing_and_moves_the_digest(
    session: Session,
) -> None:
    """Two cadences are two projections, and the digest follows the content.

    Asserted on the digest as well as the UUID because they answer different
    questions: the UUID says the accepted semantics differ, the digest says the
    persisted rows do. A cadence that moved one but not the other would leave
    stored state that verifies against the wrong projection.
    """
    turn = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), _with_recurrence(PER_TURN))
    )
    day = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), _with_recurrence(PER_DAY))
    )
    none = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), _with_recurrence(None))
    )
    uuids = {
        turn.projection_uuid,
        day.projection_uuid,
        none.projection_uuid,
    }
    assert len(uuids) == 3

    identified = _persisted(session, PER_TURN)
    before = compute_persisted_state_digest(session, identified.projection_uuid)
    session.execute(
        update(MechanicalComponentORM)
        .where(
            MechanicalComponentORM.projection_uuid == identified.projection_uuid,
            MechanicalComponentORM.semantic_key
            == build_representation().components[0].semantic_key,
        )
        .values(recurs={"boundary": "start_of_turn", "whose": "subject"})
    )
    session.flush()
    assert compute_persisted_state_digest(session, identified.projection_uuid) != before


def test_a_stored_cadence_outside_the_vocabulary_fails_reconstruction(
    session: Session,
) -> None:
    """Refused, never coerced into a cadence the source did not state."""
    identified = _persisted(session, PER_TURN)
    row = session.execute(
        select(MechanicalComponentORM).where(
            MechanicalComponentORM.projection_uuid == identified.projection_uuid
        )
    ).scalars()
    first = next(r for r in row if r.recurs is not None)
    first.recurs = {"boundary": "every_fortnight", "whose": "subject"}
    session.flush()
    with pytest.raises(PersistedStateReconstructionError):
        reconstruct_candidate(session, identified.projection_uuid)


def test_a_stored_cadence_violating_its_own_invariant_fails_reconstruction(
    session: Session,
) -> None:
    """A day boundary carrying ``whose`` is refused on the way back in.

    The invariant is not only a build-time check: storage can be edited, so the
    reconstruction path asks the same question rather than trusting the row.
    """
    identified = _persisted(session, PER_TURN)
    rows = session.execute(
        select(MechanicalComponentORM).where(
            MechanicalComponentORM.projection_uuid == identified.projection_uuid
        )
    ).scalars()
    first = next(r for r in rows if r.recurs is not None)
    first.recurs = {"boundary": "end_of_day", "whose": "subject"}
    session.flush()
    with pytest.raises(PersistedStateReconstructionError) as caught:
        reconstruct_candidate(session, identified.projection_uuid)
    assert "does not range over" in str(caught.value)
