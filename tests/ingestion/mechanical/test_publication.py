"""Atomic publication and activation — CRD Issue 5d, Decision 8.

The four contract properties, each proven by observing the database rather than
the return value alone: a failed gate leaves no partial active state, published
projections stop verifying once edited, an identical rebuild is idempotent, and
a competing projection cannot take a package's active authority.

Publication commits, so every test here gets its own database.
"""

from __future__ import annotations

import dataclasses

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.gate import run_publication_gate
from afterworlds.ingestion.mechanical.oracle import AcceptedOracle, oracle_identity
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.publication import (
    PublicationOutcome,
    activate_projection,
    publish_from_committed_oracle,
    publish_projection,
    resolve_active_projection,
)
from afterworlds.ingestion.mechanical.report import report_hash
from afterworlds.ingestion.mechanical.representation import (
    ProvenanceTargetKind,
    fact_key,
)
from afterworlds.persistence.orm.mechanical import (
    MechanicalActiveProjectionORM,
    MechanicalFactORM,
    MechanicalProjectionORM,
)
from tests.ingestion.mechanical.conftest import (
    DESCRIPTOR_FACT,
    DESCRIPTOR_KEY,
    NOW,
    PACKAGE_UUID,
    SPELL_KEY,
    build_candidate,
    build_ledger,
    build_representation,
)
from tests.ingestion.mechanical.test_gate import persist

LATER = "2026-08-01T00:00:00Z"


def header(session: Session, uuid: str) -> MechanicalProjectionORM:
    return session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == uuid
        )
    ).scalar_one()


def active_rows(session: Session) -> list[MechanicalActiveProjectionORM]:
    return list(session.execute(select(MechanicalActiveProjectionORM)).scalars().all())


def a_different_projection(
    session: Session, oracle: AcceptedOracle
) -> tuple[str, AcceptedOracle]:
    """A second projection over the same package, and the oracle that accepts it.

    Its spell descriptor states a different level, so it is a different
    projection identity — a genuinely *competing* authority rather than a
    rebuild. It comes with its own accepted oracle because that is the only way
    a second projection can pass the gate at all: the gate derives the expected
    identity from the oracle, so one oracle can bless exactly one projection.

    That is what makes the competing-activation branch reachable. Two committed
    oracles for one release are rejected at load, but publication takes the
    oracle it is given, and "someone published against a second accepted
    authority" is precisely the split the active-projection key exists to stop.
    """
    changed = dataclasses.replace(DESCRIPTOR_FACT, level=8)
    base = build_representation()
    representation = dataclasses.replace(
        base,
        components=(
            dataclasses.replace(base.components[0], facts=(changed,)),
            base.components[1],
        ),
        provenance=tuple(
            (
                dataclasses.replace(
                    p, target_key=(SPELL_KEY, DESCRIPTOR_KEY, fact_key(changed))
                )
                if p.target_kind is ProvenanceTargetKind.FACT
                else p
            )
            for p in base.provenance
        ),
    )
    uuid = persist(
        session, dataclasses.replace(build_candidate(), representation=representation)
    )
    return uuid, dataclasses.replace(oracle, representation=representation)


# ---------------------------------------------------------------------------
# The happy path
# ---------------------------------------------------------------------------


def test_a_complete_projection_publishes_and_becomes_active(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    uuid = persist(session)
    result = publish_projection(session, uuid, committed_oracle, now=NOW)

    assert result.outcome is PublicationOutcome.PUBLISHED
    assert result.report is not None
    assert result.evidence_report_hash == report_hash(result.report)

    row = header(session, uuid)
    assert row.publication_status == "published"
    assert row.published_at == NOW
    assert row.oracle_identity == oracle_identity(committed_oracle)
    assert row.evidence_report_hash == result.evidence_report_hash
    assert row.report_payload == result.report.payload

    active = resolve_active_projection(session, PACKAGE_UUID)
    assert active.outcome is PublicationOutcome.PUBLISHED
    assert active.projection_uuid == uuid
    assert active.activated_at == NOW


def test_publication_survives_a_new_session(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Publication commits, so it is durable rather than pending in a session."""
    uuid = persist(session)
    assert (
        publish_projection(session, uuid, committed_oracle, now=NOW).outcome
        is PublicationOutcome.PUBLISHED
    )
    session.expunge_all()
    assert resolve_active_projection(session, PACKAGE_UUID).projection_uuid == uuid


# ---------------------------------------------------------------------------
# A failed gate leaves nothing behind
# ---------------------------------------------------------------------------


def test_a_failed_gate_leaves_no_partial_active_state(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    ledger = build_ledger()
    unaccepted = dataclasses.replace(ledger, acceptances=())
    uuid = persist(
        session, dataclasses.replace(build_candidate(), classification=unaccepted)
    )

    result = publish_projection(session, uuid, committed_oracle, now=NOW)
    assert result.outcome is PublicationOutcome.UNREVIEWED

    row = header(session, uuid)
    assert row.publication_status == "draft"
    assert row.published_at is None
    assert row.evidence_report_hash is None
    assert row.report_payload is None
    assert active_rows(session) == []
    assert (
        resolve_active_projection(session, PACKAGE_UUID).outcome
        is PublicationOutcome.UNPUBLISHED
    )


def test_a_failed_gate_still_produces_an_auditable_report(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """The refusal is returned as evidence, and is not written anywhere."""
    uuid = persist(session)
    session.execute(
        MechanicalFactORM.__table__.delete().where(
            MechanicalFactORM.projection_uuid == uuid
        )
    )
    session.flush()
    result = publish_projection(session, uuid, committed_oracle, now=NOW)
    assert result.report is not None
    gate = result.report.payload["gate"]
    assert isinstance(gate, dict)
    assert gate["passed"] is False
    assert gate["failures"]
    assert header(session, uuid).report_payload is None


def test_activation_after_a_failed_gate_is_refused(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Activation is fail-closed on its own, not because publication behaved.

    Called directly, with nothing between it and the database — the state a
    caller who skipped the gate, or ran it and ignored the answer, would be in.
    """
    uuid = persist(session)
    session.execute(
        MechanicalFactORM.__table__.delete().where(
            MechanicalFactORM.projection_uuid == uuid
        )
    )
    session.flush()
    assert (
        publish_projection(session, uuid, committed_oracle, now=NOW).outcome
        is not PublicationOutcome.PUBLISHED
    )

    direct = activate_projection(session, uuid, now=NOW)
    assert direct.outcome is PublicationOutcome.UNPUBLISHED
    assert active_rows(session) == []


def test_activation_of_an_unknown_projection_is_absent(session: Session) -> None:
    assert (
        activate_projection(session, "no-such-projection", now=NOW).outcome
        is PublicationOutcome.ABSENT
    )


# ---------------------------------------------------------------------------
# Idempotence and immutability
# ---------------------------------------------------------------------------


def test_publishing_the_same_projection_twice_is_idempotent(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """An identical rebuild is the same content-derived identity.

    The second attempt still runs the complete gate — reuse is never accepted
    on a status check alone — and leaves the activation record byte-identical.
    """
    uuid = persist(session)
    first = publish_projection(session, uuid, committed_oracle, now=NOW)
    before = (
        active_rows(session)[0].projection_uuid,
        active_rows(session)[0].activated_at,
    )

    second = publish_projection(session, uuid, committed_oracle, now=LATER)
    assert second.outcome is PublicationOutcome.ALREADY_PUBLISHED
    assert second.gate is not None and second.gate.passed
    assert second.evidence_report_hash == first.evidence_report_hash

    assert len(active_rows(session)) == 1
    assert (
        active_rows(session)[0].projection_uuid,
        active_rows(session)[0].activated_at,
    ) == before
    assert header(session, uuid).published_at == NOW


def test_a_published_projection_edited_afterwards_stops_verifying(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Published projections are immutable: an edit is detected, not absorbed."""
    uuid = persist(session)
    assert (
        publish_projection(session, uuid, committed_oracle, now=NOW).outcome
        is PublicationOutcome.PUBLISHED
    )

    row = session.execute(select(MechanicalFactORM)).scalars().one()
    payload = dict(row.payload)
    payload["level"] = 1
    row.payload = payload
    session.flush()

    again = publish_projection(session, uuid, committed_oracle, now=LATER)
    assert again.outcome is PublicationOutcome.STALE


def test_a_published_projection_whose_evidence_was_rewritten_is_stale(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Recorded evidence must still be the evidence this state derives."""
    uuid = persist(session)
    publish_projection(session, uuid, committed_oracle, now=NOW)
    header(session, uuid).evidence_report_hash = "e" * 64
    session.flush()
    assert (
        publish_projection(session, uuid, committed_oracle, now=LATER).outcome
        is PublicationOutcome.STALE
    )


# ---------------------------------------------------------------------------
# Competing activation
# ---------------------------------------------------------------------------


def test_a_competing_projection_that_passes_its_own_gate_is_still_refused(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """The challenger passes a gate — against its own accepted oracle.

    This is the case that actually needs the active-projection key. The
    challenger is internally honest, proven, and blessed by an oracle that
    derives its exact identity, so nothing about *it* is wrong. It is refused
    solely because the package already has active authority, and it is refused
    before its own header is mutated, so it stays a draft rather than becoming
    a second published-but-inactive projection.
    """
    incumbent = persist(session)
    assert (
        publish_projection(session, incumbent, committed_oracle, now=NOW).outcome
        is PublicationOutcome.PUBLISHED
    )

    challenger, challenger_oracle = a_different_projection(session, committed_oracle)
    assert challenger != incumbent
    assert run_publication_gate(session, challenger, challenger_oracle).passed

    result = publish_projection(session, challenger, challenger_oracle, now=LATER)
    assert result.outcome is PublicationOutcome.ACTIVE_CONFLICT

    assert header(session, challenger).publication_status == "draft"
    assert header(session, challenger).evidence_report_hash is None
    assert len(active_rows(session)) == 1
    assert active_rows(session)[0].projection_uuid == incumbent
    assert active_rows(session)[0].activated_at == NOW


def test_a_competing_projection_judged_by_the_incumbents_oracle_is_incomplete(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """One oracle blesses exactly one projection.

    Judged by the authority that accepted the incumbent, the challenger is not
    the accepted content and never reaches the activation check at all.
    """
    incumbent = persist(session)
    publish_projection(session, incumbent, committed_oracle, now=NOW)

    challenger, _ = a_different_projection(session, committed_oracle)
    result = publish_projection(session, challenger, committed_oracle, now=LATER)
    assert result.outcome is PublicationOutcome.INCOMPLETE
    assert active_rows(session)[0].projection_uuid == incumbent


def test_activating_a_second_published_projection_is_an_active_conflict(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """The activation seam itself refuses to split, whatever the caller did.

    The challenger is forced into a ``published`` header with recorded evidence
    — the state a bug, a partial migration, or a hand edit could produce — and
    activation still refuses, because one active projection per package is a
    primary key rather than a convention.
    """
    incumbent = persist(session)
    publish_projection(session, incumbent, committed_oracle, now=NOW)

    challenger, _ = a_different_projection(session, committed_oracle)
    forced = header(session, challenger)
    forced.publication_status = "published"
    forced.evidence_report_hash = "f" * 64
    session.flush()

    result = activate_projection(session, challenger, now=LATER)
    assert result.outcome is PublicationOutcome.ACTIVE_CONFLICT
    assert len(active_rows(session)) == 1
    assert active_rows(session)[0].projection_uuid == incumbent
    assert active_rows(session)[0].activated_at == NOW


# ---------------------------------------------------------------------------
# Typed outcomes, never None
# ---------------------------------------------------------------------------


def test_no_accepted_oracle_is_absent_not_a_pass(session: Session) -> None:
    """An absent oracle is never an empty one: nothing is published by default."""
    uuid = persist(session)
    result = publish_projection(session, uuid, None, now=NOW)
    assert result.outcome is PublicationOutcome.ABSENT
    assert result.gate is None
    assert active_rows(session) == []


def test_the_committed_oracle_path_refuses_a_release_with_no_authority(
    session: Session,
) -> None:
    """The production entry resolves its own oracle and fails closed.

    Nothing is committed for this release, so the projection cannot be
    published — no caller can supply the authority that judges its own output.
    """
    uuid = persist(session)
    result = publish_from_committed_oracle(session, uuid, now=NOW)
    assert result.outcome is PublicationOutcome.ABSENT
    assert active_rows(session) == []


def test_publishing_an_unknown_projection_is_absent(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    result = publish_projection(
        session, "no-such-projection", committed_oracle, now=NOW
    )
    assert result.outcome is PublicationOutcome.ABSENT


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        pytest.param(
            lambda c: dataclasses.replace(
                c, binding=dataclasses.replace(c.binding, bundle_root_hash="9" * 64)
            ),
            PublicationOutcome.MISMATCHED_RELEASE,
            id="mismatched-5c-binding",
        ),
        pytest.param(
            lambda c: dataclasses.replace(
                c,
                classification=dataclasses.replace(c.classification, acceptances=()),
            ),
            PublicationOutcome.UNREVIEWED,
            id="unreviewed-residue",
        ),
    ],
)
def test_each_refusal_has_its_own_typed_outcome(
    session: Session,
    committed_oracle: AcceptedOracle,
    mutate,  # type: ignore[no-untyped-def]
    expected: PublicationOutcome,
) -> None:
    """Refusals stay distinguishable rather than collapsing into one failure."""
    uuid = persist(session, mutate(build_candidate()))
    assert (
        publish_projection(session, uuid, committed_oracle, now=NOW).outcome is expected
    )


def test_an_undrafted_projection_is_never_activated(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """A draft with no recorded proof cannot reach publication at all."""
    identified = identify_projection(build_candidate())
    persist_draft(session, identified, now=NOW)
    result = publish_projection(
        session, identified.projection_uuid, committed_oracle, now=NOW
    )
    assert result.outcome is PublicationOutcome.STALE
    assert active_rows(session) == []


def test_a_projection_in_an_unknown_status_is_refused(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Status no publication path produces is rejected, not interpreted."""
    uuid = persist(session)
    header(session, uuid).publication_status = "retired"
    session.flush()
    result = publish_projection(session, uuid, committed_oracle, now=NOW)
    assert result.outcome is PublicationOutcome.STALE
    assert active_rows(session) == []


def test_record_digest_is_not_re_recorded_on_the_reuse_path(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Publishing twice must not try to record a proof that already exists."""
    uuid = persist(session)
    digest = header(session, uuid).persisted_state_digest
    publish_projection(session, uuid, committed_oracle, now=NOW)
    publish_projection(session, uuid, committed_oracle, now=LATER)
    assert header(session, uuid).persisted_state_digest == digest


def test_publication_leaves_the_projection_content_untouched(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Activation is package state, so it never changes a projection's proof."""
    uuid = persist(session)
    before = header(session, uuid).persisted_state_digest
    payload_hash = header(session, uuid).payload_hash
    publish_projection(session, uuid, committed_oracle, now=NOW)
    assert header(session, uuid).persisted_state_digest == before
    assert header(session, uuid).payload_hash == payload_hash
