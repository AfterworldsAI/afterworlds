"""Loaded evidence is validated, and malformed state stays typed — CRD Issue 5d.

Two enforcement gaps, both of the shape *"a check exists, but not on this path."*

**Lift evidence.** ``acceptance.lifts`` is read from a file. The loader's
wire-shape checks establish that each record is well-formed and say nothing about
whether the succession it claims was ever authorized, ever happened, or could
have happened. An artifact loaded clean while asserting an unregistered
transition, a destination contradicting its own declaration, and a proof extent
over collections the representation does not have.

The proof *extent* is the same defect one level down (#137 round 3). It was
compared as a set, so a duplicated row collapsed before the comparison saw it,
and it carried per-collection element counts nothing could check: a committed
file supersedes its predecessor and later batches grow the same collections, so
the pre-lift extent is not re-derivable from the artifact that survives. The
counts are gone rather than bounded — see :class:`SchemaLiftRecord` — and what
remains is checked against the representation's own collection table.

**Typed reconstruction.** ``run_publication_gate`` categorizes
``PersistedStateReconstructionError`` and nothing else, so a malformed JSON
column that raised ``TypeError`` aborted the gate instead of returning the
``PERSISTED_STATE`` refusal the gate exists to return. Fail-closed in the wrong
currency: the caller gets an exception where its contract promises a verdict.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import replace

import pytest
from sqlalchemy import update
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
from afterworlds.ingestion.mechanical.persistence import (
    PersistedStateReconstructionError,
    _applicability_from_row,
    _recurrence_from_row,
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_COLLECTIONS,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_3_HASH,
    SCHEMA_3_VERSION,
    SCHEMA_4_HASH,
    SCHEMA_4_VERSION,
    SchemaLiftRecord,
    lift_accepted_inputs,
    lift_chain_violations,
)
from afterworlds.persistence.orm.mechanical import (
    MechanicalComponentORM,
    MechanicalFactORM,
)
from tests.ingestion.mechanical.conftest import (
    NOW,
    RELEASE_BINDING,
    build_ledger,
    build_representation,
    candidate_of,
)

#: The **legacy specimen**: the committed accepted artifact exactly as it stood
#: before hazards-1 was accepted into it — one batch, reviewed under schema 3,
#: with no schema anchors and no lift evidence. That is the shape this module's
#: scenarios are about, and the Owner's acceptance of hazards-1 legitimately
#: ended it in production, so the specimen is frozen under ``data/`` rather than
#: read out of the oracle directory. Byte-identical to the file this repository
#: committed (Git blob ``42faeca2…``), so every identity pinned below is
#: unchanged.
#:
#: Deliberately **not** in :data:`COMMITTED_ORACLE_DIR`: a second file there
#: claiming one release is exactly what the resolver refuses, and
#: ``test_exactly_one_accepted_artifact_is_committed_for_the_release`` asserts
#: it stays the only one.
LEGACY_PATH = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / "legacy_conditions_1_unanchored_schema3.json"
)
DECLARED_4 = (SCHEMA_4_VERSION, SCHEMA_4_HASH)
DECLARED_3 = (SCHEMA_3_VERSION, SCHEMA_3_HASH)

#: The proof extent a real lift records: every collection the representation has.
FULL_EXTENT = tuple(sorted(REPRESENTATION_COLLECTIONS))


def _record(**overrides: object) -> SchemaLiftRecord:
    """The registered schema-3 to schema-4 record, or a perturbation of it."""
    base: dict[str, object] = {
        "lift_id": "5d-lift-schema-3-to-4",
        "from_version": SCHEMA_3_VERSION,
        "from_hash": SCHEMA_3_HASH,
        "to_version": SCHEMA_4_VERSION,
        "to_hash": SCHEMA_4_HASH,
        "verified_collections": FULL_EXTENT,
    }
    return SchemaLiftRecord(**{**base, **overrides})  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# What must stay legal
# ---------------------------------------------------------------------------


def test_no_evidence_is_legal() -> None:
    """An artifact that never crossed a succession carries nothing to validate.

    The committed ``conditions-1`` artifact is exactly this case, so a rule that
    required a terminal record would refuse the one file that cannot move.
    """
    assert lift_chain_violations((), DECLARED_3) == []


def test_the_committed_artifact_still_loads() -> None:
    """The discriminating test for the loader guard."""
    inputs = load_accepted_inputs(LEGACY_PATH)
    assert inputs.lifts == ()
    assert inputs.oracle.schema_version == SCHEMA_3_VERSION


def test_one_registered_lift_ending_at_the_declaration_is_legal() -> None:
    assert lift_chain_violations((_record(),), DECLARED_4) == []


# ---------------------------------------------------------------------------
# What must be refused
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("lifts", "declared", "expected"),
    [
        pytest.param(
            (_record(from_version="bogus", from_hash="0" * 64, lift_id="made-up"),),
            DECLARED_4,
            "no lift is registered",
            id="invented-transition",
        ),
        pytest.param(
            (_record(to_version="5d-representation-schema-9", to_hash="f" * 64),),
            DECLARED_4,
            "the registered lift from",
            id="registered-source-wrong-destination",
        ),
        pytest.param(
            (_record(lift_id="not-the-registered-one"),),
            DECLARED_4,
            "the registered lift from",
            id="wrong-lift-id",
        ),
        pytest.param(
            (
                _record(
                    from_version=SCHEMA_4_VERSION,
                    from_hash=SCHEMA_4_HASH,
                    to_version=SCHEMA_3_VERSION,
                    to_hash=SCHEMA_3_HASH,
                ),
            ),
            DECLARED_3,
            # Schema 4 now *has* a registered outgoing row (4 to 5), so the
            # refusal sharpens from "nothing is registered from here" to "what
            # is registered from here goes somewhere else". Both refuse a
            # reversed transition; "no lift is registered" is still exercised by
            # ``invented-transition``, whose source has no row at all.
            "the registered lift from",
            id="reversed",
        ),
        pytest.param(
            (_record(), _record()),
            DECLARED_4,
            "already recorded",
            id="duplicated",
        ),
        pytest.param(
            (_record(),), DECLARED_3, "the chain ends at", id="terminal-disagrees"
        ),
        pytest.param(
            (_record(verified_collections=("widgets",)),),
            DECLARED_4,
            "proof extent covers",
            id="invented-proof-collection",
        ),
        pytest.param(
            (_record(verified_collections=FULL_EXTENT[:-1]),),
            DECLARED_4,
            "proof extent covers",
            id="proof-extent-missing-a-collection",
        ),
        pytest.param(
            (_record(verified_collections=FULL_EXTENT + FULL_EXTENT[:1]),),
            DECLARED_4,
            "more than once",
            id="duplicated-collection-row",
        ),
        pytest.param(
            (_record(verified_collections=FULL_EXTENT[:-1] + FULL_EXTENT[:1]),),
            DECLARED_4,
            "more than once",
            id="duplicate-standing-in-for-a-missing-collection",
        ),
    ],
)
def test_evidence_that_does_not_describe_an_authorized_succession_is_refused(
    lifts: tuple[SchemaLiftRecord, ...], declared: tuple[str, str], expected: str
) -> None:
    """Invented, disconnected, reversed, duplicated, and impossible evidence."""
    findings = lift_chain_violations(lifts, declared)
    assert any(expected in f for f in findings), findings


def test_a_disconnected_chain_is_refused() -> None:
    """Continuity is what makes an ordered chain a chain.

    Reordering and omission both break the join, so neither needs a rule of its
    own — which is why this asserts the *join*, not an ordering predicate.
    """
    second = _record(
        from_version=SCHEMA_4_VERSION,
        from_hash=SCHEMA_4_HASH,
        to_version="5d-representation-schema-5",
        to_hash="a" * 64,
        lift_id="hypothetical-4-to-5",
    )
    findings = lift_chain_violations((second, _record()), DECLARED_4)
    assert any("does not continue the previous record" in f for f in findings), findings


def test_the_loader_refuses_invented_evidence_end_to_end(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Through ``load_accepted_inputs``, not only through the validator."""
    raw = json.loads(LEGACY_PATH.read_text(encoding="utf-8"))
    raw["acceptance"]["lifts"] = [
        {
            "lift_id": "totally-made-up",
            "from_version": "bogus",
            "from_hash": "0" * 64,
            "to_version": "5d-representation-schema-9",
            "to_hash": "f" * 64,
            "verified_collections": list(FULL_EXTENT),
        }
    ]
    path = pathlib.Path(tmp_path) / "invented.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(OracleLoadError) as raised:
        load_accepted_inputs(path)
    assert "does not describe an authorized succession" in str(raised.value)


def _lifted_artifact(tmp_path: pathlib.Path) -> tuple[pathlib.Path, SchemaLiftRecord]:
    """The committed schema-3 artifact, really lifted and really written out."""
    inputs = load_accepted_inputs(LEGACY_PATH)
    lifted, records = lift_accepted_inputs(inputs, DECLARED_4)
    path = tmp_path / "lifted.json"
    path.write_text(
        json.dumps(accepted_inputs_payload(replace(lifted, lifts=records))),
        encoding="utf-8",
    )
    return path, records[-1]


def test_a_real_record_survives_writing_and_loading(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Writer, loader and validator agree about a record none of them invented.

    The load-bearing case: every refusal below is worthless if the one shape a
    genuine ``verify_lift`` produces cannot make the round trip.
    """
    path, record = _lifted_artifact(pathlib.Path(tmp_path))
    loaded = load_accepted_inputs(path)

    assert loaded.lifts == (record,)
    assert loaded.oracle.schema_version == SCHEMA_4_VERSION
    assert lift_chain_violations(loaded.lifts, DECLARED_4) == []
    # Every collection, proved: an empty one is proved empty rather than skipped,
    # which is why the extent is stated over the collection table and not over
    # whichever collections happened to hold something.
    assert set(record.verified_collections) == REPRESENTATION_COLLECTIONS
    assert loaded.oracle.representation.relationships == ()


def test_a_grown_artifact_is_not_mistaken_for_the_pre_lift_extent(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The determination behind removing the counts, pinned as behaviour.

    A lifted artifact keeps accepting content, so the collections it holds when
    it is next loaded are the inherited elements *plus* everything accepted
    after. The loaded evidence describes the crossing and makes no claim about
    how much was inherited — so growth loads clean, and nothing in the file
    invites a reader to read a historical extent out of a present size.
    """
    path, record = _lifted_artifact(pathlib.Path(tmp_path))
    raw = json.loads(path.read_text(encoding="utf-8"))
    grown = raw["representation"]["relationships"]
    assert grown == []

    loaded = load_accepted_inputs(path)
    assert lift_chain_violations(loaded.lifts, DECLARED_4) == []
    # Names, and nothing a size could be compared against.
    assert record.verified_collections == tuple(sorted(REPRESENTATION_COLLECTIONS))


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        pytest.param(
            lambda names: names + names[:1],
            "more than once",
            id="duplicate-row",
        ),
        pytest.param(
            lambda names: [*names[:-1], "widgets"],
            "proof extent covers",
            id="invented-collection",
        ),
        pytest.param(lambda names: names[:-1], "proof extent covers", id="missing"),
    ],
)
def test_the_loader_refuses_a_tampered_extent_end_to_end(  # type: ignore[no-untyped-def]
    tmp_path, mutate, expected: str
) -> None:
    """Through ``load_accepted_inputs``, on evidence that was genuine first."""
    path, _ = _lifted_artifact(pathlib.Path(tmp_path))
    raw = json.loads(path.read_text(encoding="utf-8"))
    lift = raw["acceptance"]["lifts"][0]
    lift["verified_collections"] = mutate(list(lift["verified_collections"]))
    path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(OracleLoadError) as raised:
        load_accepted_inputs(path)
    assert "does not describe an authorized succession" in str(raised.value)
    assert expected in str(raised.value)


def test_a_count_claim_cannot_re_enter_through_the_wire(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The removed claim stays removed.

    A per-collection element count is a claim about content that no longer
    exists in isolation, so no loaded artifact may carry one — including as a
    leftover key beside the extent, which would read as evidence while being
    checked by nothing.
    """
    path, _ = _lifted_artifact(pathlib.Path(tmp_path))
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["acceptance"]["lifts"][0]["verified_counts"] = [
        {"collection": "records", "elements": 999999}
    ]
    path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(OracleLoadError) as raised:
        load_accepted_inputs(path)
    assert "unexpected ['verified_counts']" in str(raised.value)


# ---------------------------------------------------------------------------
# Typed reconstruction, and the gate verdict that depends on it
# ---------------------------------------------------------------------------

#: Every JSON shape a corrupted or hand-edited column can hold. The scalars are
#: the ones that used to escape: ``set(7)`` raises ``TypeError``, and the guard
#: has to run before the value is inspected rather than after.
MALFORMED = [
    pytest.param(7, id="int"),
    pytest.param(3.5, id="float"),
    pytest.param(True, id="bool"),
    pytest.param("start_of_turn", id="string"),
    pytest.param(["start_of_turn"], id="array"),
    pytest.param({"boundary": "not_a_boundary"}, id="unknown-vocabulary-member"),
    pytest.param({"smuggled": 1}, id="undeclared-key"),
]


@pytest.mark.parametrize("payload", MALFORMED)
def test_a_malformed_recurrence_is_a_typed_refusal(payload: object) -> None:
    """Every shape normalizes to the one error the publication gate categorizes."""
    with pytest.raises(PersistedStateReconstructionError):
        _recurrence_from_row(payload, "where")  # type: ignore[arg-type]


@pytest.mark.parametrize("payload", MALFORMED)
def test_a_malformed_applicability_is_a_typed_refusal(payload: object) -> None:
    """The sibling boundary, audited in the same pass and already safe.

    Pinned rather than assumed: it is safe because
    ``applicability_payload_violations`` checks the mapping shape first, and a
    later edit could reorder that.
    """
    with pytest.raises(PersistedStateReconstructionError):
        _applicability_from_row(payload, "table", "where")  # type: ignore[arg-type]


def test_a_malformed_fact_payload_is_a_typed_refusal(session: Session) -> None:
    """The third boundary.

    ``fact_from_payload`` meets a scalar with ``AttributeError``, so the mapping
    guard has to run in ``_fact_from_row`` before the payload is handed over.
    """
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    )
    persist_draft(session, identified, now=NOW)
    session.flush()
    session.execute(
        update(MechanicalFactORM)
        .where(MechanicalFactORM.projection_uuid == identified.projection_uuid)
        .values(payload=7)
    )
    session.flush()
    with pytest.raises(PersistedStateReconstructionError):
        reconstruct_candidate(session, identified.projection_uuid)


def test_the_publication_gate_returns_persisted_state_rather_than_raising(
    session: Session, committed_oracle
) -> None:  # type: ignore[no-untyped-def]
    """The property the typed error exists for, asserted on the gate itself.

    The gate's contract is that a caller receives a refusal rather than an
    exception. A ``TypeError`` escaping reconstruction aborted the publication
    path instead — fail-closed, but in the wrong currency, and uncategorized.
    """
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()
    session.execute(
        update(MechanicalComponentORM)
        .where(MechanicalComponentORM.projection_uuid == identified.projection_uuid)
        .values(recurs=7)
    )
    session.flush()

    result = run_publication_gate(
        session, identified.projection_uuid, oracle=committed_oracle
    )
    assert not result.passed
    assert GateFailureCategory.PERSISTED_STATE in {f.category for f in result.failures}
