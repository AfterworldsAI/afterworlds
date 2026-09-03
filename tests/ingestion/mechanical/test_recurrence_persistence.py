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

import json
import pathlib
from dataclasses import replace

import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.gate import (
    GateFailureCategory,
    run_publication_gate,
)
from afterworlds.ingestion.mechanical.oracle import (
    OracleLoadError,
    accepted_inputs_payload,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.oracle import _recurrence as load_accepted
from afterworlds.ingestion.mechanical.persistence import (
    PersistedStateReconstructionError,
    compute_persisted_state_digest,
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_persisted_state,
)
from afterworlds.ingestion.mechanical.persistence import (
    _recurrence_from_row as load_persisted,
)
from afterworlds.ingestion.mechanical.projection import (
    identify_projection,
    recurrence_payload,
    representation_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    RECURRENCE_KEYS,
    REPRESENTATION_SCHEMA_VERSION,
    Recurrence,
    RecurrenceBoundary,
    RollActor,
    representation_schema_hash,
)
from afterworlds.persistence.orm.mechanical import MechanicalComponentORM
from afterworlds.services.rules_authority.patches import InvalidPatchError
from afterworlds.services.rules_authority.patches import (
    _build_recurrence as load_patch,
)
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


#: The **legacy specimen**: the committed accepted artifact exactly as it stood
#: before hazards-1 was accepted into it - the conditions-1 batch alone,
#: reviewed under schema 3. What this module asserts is true of that accepted
#: content, so it reads the frozen copy rather than whatever the release
#: currently accepts. Byte-identical to the file this repository committed
#: (Git blob 42faeca2...), so every identity pinned here is unchanged.
LEGACY_PATH = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / "legacy_conditions_1_unanchored_schema3.json"
)


# ---------------------------------------------------------------------------
# Round 9 — a present recurrence carries both keys, and `whose` may be null
# ---------------------------------------------------------------------------
#
# ``recurrence_payload`` emits every field of this value object unconditionally:
# ``{"boundary": "end_of_day", "whose": null}`` is what a day-boundary cadence
# actually serializes to, and the schema grammar does not declare ``whose``
# omitted-when-empty. All three JSON builders nonetheless treated it as optional,
# so ``{"boundary": "end_of_day"}`` — a shape nothing ever wrote — rebuilt as an
# explicit null, giving an incomplete row a meaning instead of refusing it.
#
# The omission that *is* declared is one level up: ``recurs`` itself is absent
# when a component states no cadence, which is what keeps an inherited schema-3
# component byte-identical under schema 4. That stays exactly as it was.

MISSING_WHOSE = {"boundary": "end_of_day"}
EXPLICIT_NULL = {"boundary": "end_of_day", "whose": None}
TURN = {"boundary": "start_of_turn", "whose": "subject"}


def test_the_serializer_emits_both_keys() -> None:
    """The premise, asserted rather than assumed.

    Everything below follows from this: if the canonical payload omitted
    ``whose`` when empty, the builders would have been right to accept its
    absence, and the declared key set is what decides that.
    """
    payload = recurrence_payload(
        Recurrence(boundary=RecurrenceBoundary.END_OF_DAY, whose=None)
    )
    assert payload == EXPLICIT_NULL
    assert set(payload) == RECURRENCE_KEYS


@pytest.mark.parametrize(
    ("build", "error"),
    [
        pytest.param(
            lambda raw: load_accepted(raw, "where"),
            OracleLoadError,
            id="accepted-input",
        ),
        pytest.param(
            lambda raw: load_persisted(raw, "where"),
            PersistedStateReconstructionError,
            id="persisted-state",
        ),
        pytest.param(
            lambda raw: load_patch(raw, "what"), InvalidPatchError, id="override-patch"
        ),
    ],
)
class TestEveryRecurrenceBuilder:
    """The three production readers, held to one key-shape rule.

    Grouped so a fourth builder added later has an obvious place to join, and so
    no builder can quietly diverge: every case below runs against all three.
    """

    def test_a_missing_whose_is_refused(self, build, error) -> None:  # type: ignore[no-untyped-def]
        """The defect. A key the serializer always writes is not optional."""
        with pytest.raises(error):
            build(dict(MISSING_WHOSE))

    def test_an_explicit_null_rebuilds(self, build, error) -> None:  # type: ignore[no-untyped-def]
        """The shape a real day-boundary cadence has, and the over-refusal control."""
        assert build(dict(EXPLICIT_NULL)) == Recurrence(
            boundary=RecurrenceBoundary.END_OF_DAY, whose=None
        )

    def test_a_turn_boundary_still_rebuilds_with_its_actor(self, build, error) -> None:  # type: ignore[no-untyped-def]
        assert build(dict(TURN)) == Recurrence(
            boundary=RecurrenceBoundary.START_OF_TURN, whose=RollActor.SUBJECT
        )

    def test_a_turn_boundary_without_an_actor_is_refused(  # type: ignore[no-untyped-def]
        self, build, error
    ) -> None:
        """The invariant, unchanged: a turn belongs to a creature."""
        with pytest.raises(error):
            build({"boundary": "start_of_turn", "whose": None})

    def test_a_day_boundary_carrying_an_actor_is_refused(  # type: ignore[no-untyped-def]
        self, build, error
    ) -> None:
        with pytest.raises(error):
            build({"boundary": "end_of_day", "whose": "subject"})

    def test_an_unknown_key_is_still_refused(self, build, error) -> None:  # type: ignore[no-untyped-def]
        with pytest.raises(error):
            build({**EXPLICIT_NULL, "extra": 1})

    def test_a_missing_boundary_is_refused(self, build, error) -> None:  # type: ignore[no-untyped-def]
        with pytest.raises(error):
            build({"whose": None})


def _artifact_with_cadence(recurs: dict[str, object], tmp_path, name: str):  # type: ignore[no-untyped-def]
    """The committed artifact carrying one cadence, declared under schema 4.

    A cadence *is* schema-4 meaning, so the declaration has to move with it or
    the legality guard refuses the file before the key shape is ever read — and
    then this test would pass for the wrong reason. Moving the declaration means
    anchoring the batches, which is the fresh-schema-4 shape round 7 admits.
    """
    raw = json.loads(LEGACY_PATH.read_text(encoding="utf-8"))
    raw["representation"]["components"][0]["recurs"] = recurs
    raw["representation_schema"] = {
        "version": REPRESENTATION_SCHEMA_VERSION,
        "hash": representation_schema_hash(),
    }
    raw["acceptance"]["schema_anchors"] = [
        {
            "batch_id": batch["batch_id"],
            "proposal_identity": batch["proposal_identity"],
            "schema_version": REPRESENTATION_SCHEMA_VERSION,
            "schema_hash": representation_schema_hash(),
        }
        for batch in raw["acceptance"]["batches"]
    ]
    path = pathlib.Path(tmp_path) / name
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path


def test_the_committed_loader_refuses_a_day_cadence_missing_whose(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """End to end, and refused for the key shape rather than for the schema."""
    path = _artifact_with_cadence(dict(MISSING_WHOSE), tmp_path, "missing-whose.json")
    with pytest.raises(OracleLoadError) as raised:
        load_accepted_inputs(path)
    assert "missing ['whose']" in str(raised.value), raised.value


def test_the_committed_loader_accepts_an_explicit_null(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The same artifact with the shape the serializer writes still loads.

    The component's own identity moves — ``recurs`` is meaning-bearing — so this
    asserts the cadence reconstructed, not that the artifact is unchanged. The
    unchanged-artifact proof is ``test_the_committed_artifact_is_untouched``.
    """
    path = _artifact_with_cadence(dict(EXPLICIT_NULL), tmp_path, "explicit-null.json")
    loaded = load_accepted_inputs(path)
    assert loaded.oracle.representation.components[0].recurs == Recurrence(
        boundary=RecurrenceBoundary.END_OF_DAY, whose=None
    )


def test_a_persisted_row_missing_whose_is_a_categorized_gate_refusal(
    session: Session, committed_oracle
) -> None:  # type: ignore[no-untyped-def]
    """The gate returns a verdict rather than raising, as in rounds 2 and 5."""
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()
    session.execute(
        update(MechanicalComponentORM)
        .where(MechanicalComponentORM.projection_uuid == identified.projection_uuid)
        .values(recurs=dict(MISSING_WHOSE))
    )
    session.flush()

    with pytest.raises(PersistedStateReconstructionError):
        reconstruct_candidate(session, identified.projection_uuid)

    result = run_publication_gate(
        session, identified.projection_uuid, oracle=committed_oracle
    )
    assert not result.passed
    assert GateFailureCategory.PERSISTED_STATE in {f.category for f in result.failures}


def test_an_explicit_null_persisted_row_reconstructs_and_verifies(
    session: Session,
) -> None:
    """The control on the persistence path: the real shape still round-trips."""
    draft = build_representation()
    with_cadence = replace(
        draft,
        components=(
            replace(
                draft.components[0],
                recurs=Recurrence(boundary=RecurrenceBoundary.END_OF_DAY, whose=None),
            ),
            *draft.components[1:],
        ),
    )
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), with_cadence)
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()

    stored = session.scalars(
        select(MechanicalComponentORM.recurs).where(
            MechanicalComponentORM.projection_uuid == identified.projection_uuid
        )
    ).all()
    assert EXPLICIT_NULL in stored, "the column holds the shape the serializer writes"

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert rebuilt.representation.components[0].recurs == Recurrence(
        boundary=RecurrenceBoundary.END_OF_DAY, whose=None
    )
    assert verify_persisted_state(session, identified.projection_uuid) == ()


def test_a_component_stating_no_cadence_still_omits_the_key_entirely() -> None:
    """The declared omission, one level up, and untouched.

    ``recurs`` is absent when a component states no cadence — that is what keeps
    an inherited schema-3 component byte-identical under schema 4. This round
    changed the shape *inside* a present recurrence, not whether one is present.
    """
    draft = build_representation()
    assert draft.components[0].recurs is None
    payload = representation_payload(
        draft, schema_version=REPRESENTATION_SCHEMA_VERSION
    )
    assert all("recurs" not in c for c in payload["components"])  # type: ignore[union-attr]


def test_the_committed_artifact_is_untouched() -> None:
    """Zero movement, asserted where the change could have reached it."""
    inputs = load_accepted_inputs(LEGACY_PATH)
    committed = json.loads(LEGACY_PATH.read_text(encoding="utf-8"))
    assert accepted_inputs_payload(inputs) == committed
    assert all(c.recurs is None for c in inputs.oracle.representation.components)
