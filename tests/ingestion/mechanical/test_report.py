"""The deterministic evidence report — CRD Issue 5d.

The report is the audit trail for a publication decision, so it has to be
reproducible from the same inputs and complete enough to re-derive the verdict
without the database that produced it.
"""

from __future__ import annotations

import dataclasses

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.gate import run_publication_gate
from afterworlds.ingestion.mechanical.oracle import AcceptedOracle, oracle_identity
from afterworlds.ingestion.mechanical.publication import (
    PublicationOutcome,
    _publish_projection,
)
from afterworlds.ingestion.mechanical.report import (
    EVIDENCE_REPORT_SCHEMA_VERSION,
    build_evidence_report,
    report_hash,
)
from afterworlds.persistence.orm.mechanical import (
    MechanicalFactORM,
    MechanicalProjectionORM,
)
from tests.ingestion.mechanical.conftest import NOW, build_candidate, build_ledger
from tests.ingestion.mechanical.test_gate import persist

LATER = "2026-08-01T00:00:00Z"


def build(session: Session, uuid: str, oracle: AcceptedOracle):  # type: ignore[no-untyped-def]
    header = session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == uuid
        )
    ).scalar_one()
    return build_evidence_report(header, run_publication_gate(session, uuid, oracle))


def test_the_report_identifies_everything_needed_to_reproduce_the_decision(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    uuid = persist(session)
    payload = build(session, uuid, committed_oracle).payload

    assert payload["report_version"] == EVIDENCE_REPORT_SCHEMA_VERSION
    source = payload["source_release"]
    assert isinstance(source, dict)
    assert set(source) == {
        "package_uuid",
        "release_version",
        "authoritative_source_hash",
        "transform_config_hash",
        "bundle_root_hash",
        "persisted_corpus_digest",
    }

    projection = payload["mechanical_projection"]
    assert isinstance(projection, dict)
    assert projection["projection_uuid"] == uuid
    assert projection["persisted_state_digest"] is not None
    assert projection["payload_hash"]

    accepted = payload["accepted_oracle"]
    assert isinstance(accepted, dict)
    assert accepted["oracle_identity"] == oracle_identity(committed_oracle)
    assert accepted["derived_projection_uuid"] == uuid

    gate = payload["gate"]
    assert isinstance(gate, dict)
    assert gate == {"passed": True, "failure_categories": [], "failures": []}
    assert payload["obligations"] == [
        {"record_key": "spell:wish", "satisfied": True, "failures": []},
        {
            "record_key": "creature:wish-scoped-servant",
            "satisfied": True,
            "failures": [],
        },
    ]


def test_the_report_is_byte_identical_for_the_same_state(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Same committed inputs, same persisted state, same hash — no wall clock."""
    uuid = persist(session)
    first = build(session, uuid, committed_oracle)
    second = build(session, uuid, committed_oracle)
    assert first.payload == second.payload
    assert report_hash(first) == report_hash(second)


def test_the_report_hash_survives_publication(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Publication status is not in the payload, so the hash does not move.

    Asserted through ``_publish_projection`` itself, because that is where the
    property is relied on: the reuse path compares the hash it re-derives from
    a *published* header against the one recorded when the header was still a
    draft, and treats a difference as divergence. If the payload carried the
    status, every republication would look like tamper.
    """
    uuid = persist(session)
    first = _publish_projection(session, uuid, committed_oracle, now=NOW)
    assert first.outcome is PublicationOutcome.PUBLISHED

    second = _publish_projection(session, uuid, committed_oracle, now=LATER)
    assert second.outcome is PublicationOutcome.ALREADY_PUBLISHED
    assert second.evidence_report_hash == first.evidence_report_hash
    assert second.report is not None and first.report is not None
    assert second.report.payload == first.report.payload


def test_a_changed_verdict_changes_the_report(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    uuid = persist(session)
    honest = report_hash(build(session, uuid, committed_oracle))
    session.execute(
        MechanicalFactORM.__table__.delete().where(
            MechanicalFactORM.projection_uuid == uuid
        )
    )
    session.flush()
    assert report_hash(build(session, uuid, committed_oracle)) != honest


def test_a_refusal_reports_categorized_failures_and_failed_obligations(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Structured, not a wall of prose: an auditor can group and count them."""
    ledger = build_ledger()
    uuid = persist(
        session,
        dataclasses.replace(
            build_candidate(),
            classification=dataclasses.replace(ledger, acceptances=()),
        ),
    )
    payload = build(session, uuid, committed_oracle).payload
    gate = payload["gate"]
    assert isinstance(gate, dict)
    assert gate["passed"] is False
    assert "unreviewed_residue" in gate["failure_categories"]
    assert all(
        set(f) == {"category", "detail"} and f["detail"] for f in gate["failures"]
    )


def test_diagnostics_are_named_as_drift_signal(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Counts are present and are labelled for what they are.

    ADR-005d Decision 5 forbids proving completeness with totals. They live
    under ``drift_diagnostics`` and nothing reads them to decide anything.
    """
    payload = build(session, persist(session), committed_oracle).payload
    diagnostics = payload["drift_diagnostics"]
    assert isinstance(diagnostics, dict)
    assert diagnostics["represented_leaves"] == 3
    assert diagnostics["facts"] == 1

    # The verdict carries no totals of its own: it is a pass/fail plus
    # categorized findings, so no reader can mistake a number for a proof.
    gate = payload["gate"]
    assert isinstance(gate, dict)
    assert set(gate) == {"passed", "failure_categories", "failures"}


def test_the_stored_report_is_the_returned_report(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    uuid = persist(session)
    result = _publish_projection(session, uuid, committed_oracle, now=NOW)
    assert result.report is not None
    header = session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == uuid
        )
    ).scalar_one()
    assert header.report_payload == result.report.payload
    assert header.evidence_report_hash == report_hash(result.report)
