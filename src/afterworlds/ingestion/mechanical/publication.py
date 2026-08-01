"""Atomic mechanical-projection publication — CRD Issue 5d, Decision 8.

Completes the lifecycle CRD Issue 5c established and #139 built the first half
of:

``build → persist draft → reconstruct → prove → gate → atomically publish``

Four properties are load-bearing, and each is enforced by structure rather than
by discipline:

* **A draft never becomes active before the gate succeeds.** The gate is
  read-only, so a failing run leaves the database exactly as it found it —
  there is no partial write to undo. Activation is a separate, publicly
  callable step that independently refuses any projection whose header is not
  already ``published`` with recorded evidence, so it cannot be reached around
  the gate.
* **Published projections are immutable.** Re-running publication re-runs the
  *complete* gate against reconstructed state and additionally requires the
  recorded evidence-report hash and oracle identity to still match the
  re-derived ones. A projection edited after publication therefore stops being
  publishable and stops verifying.
  ``ponytail: enforced at this seam, not by a database trigger — SQLite has no
  cheap column-level immutability. If direct row edits ever become a real
  threat model, the upgrade path is an append-only published-state table.``
* **Concurrent identical builds are idempotent.** Identity is content-derived,
  so an identical rebuild is the *same* projection UUID; publishing it again
  returns ``ALREADY_PUBLISHED`` — but only after the full gate re-proves it,
  never on a status check alone.
* **Activation cannot split.** ``rp_mech_active_projections`` is keyed by
  ``package_uuid``, so one active projection per package is a database
  constraint. A competing projection is rejected as ``ACTIVE_CONFLICT`` with
  the incumbent untouched.

Every outcome is typed. Nothing here returns ``None``, an empty result, or a
generic exception to mean "not published" (#137 contract 5).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.gate import (
    GateFailureCategory,
    GateResult,
    run_publication_gate,
)
from afterworlds.ingestion.mechanical.oracle import AcceptedOracle, committed_oracle_for
from afterworlds.ingestion.mechanical.report import (
    EvidenceReport,
    build_evidence_report,
    report_hash,
)
from afterworlds.persistence.orm.mechanical import (
    MechanicalActiveProjectionORM,
    MechanicalProjectionORM,
)

__all__ = [
    "ActiveProjection",
    "PublicationOutcome",
    "PublicationResult",
    "activate_projection",
    "publish_from_committed_oracle",
    "publish_projection",
    "resolve_active_projection",
]


class PublicationOutcome(StrEnum):
    """The typed result of a publication or activation attempt.

    Deliberately limited to states this stage can actually reach. Runtime
    binding, selector, and override states (``INVALID_SELECTOR``,
    ``INVALID_OVERRIDE``, ``INVALID_REFERENCE``, ``AMBIGUOUS``) belong to the
    runtime authority path and are not declared here as unreachable members.
    """

    #: The projection passed the gate and is now the package's active authority.
    PUBLISHED = "published"
    #: Already published and still proven — an idempotent no-op, not an error.
    ALREADY_PUBLISHED = "already_published"
    #: No such projection, or no accepted authority committed for its release.
    ABSENT = "absent"
    #: The accepted oracle judges a different release or a different policy.
    MISMATCHED_RELEASE = "mismatched_release"
    #: Spans remain proposed or carry no acceptance record.
    UNREVIEWED = "unreviewed"
    #: Spans remain classified UNRESOLVED.
    UNRESOLVED = "unresolved"
    #: The projection does not exactly match the accepted authority.
    INCOMPLETE = "incomplete"
    #: Persisted state no longer derives its own identity or recorded evidence.
    STALE = "stale"
    #: Another projection already holds this package's active authority.
    ACTIVE_CONFLICT = "active_conflict"
    #: The package has no active mechanical authority.
    UNPUBLISHED = "unpublished"


#: Gate categories mapped to outcomes, most fundamental first. Order is the
#: contract: a projection whose persisted state does not reconstruct is stale
#: regardless of what else the gate found, and calling that "incomplete" would
#: send an auditor looking for missing content instead of tampered rows.
#:
#: ``IDENTITY_MISMATCH`` is deliberately absent. It is the roll-up of every
#: content comparison, so it is present in almost any refusal; treating it as
#: evidence of tamper would make ``STALE`` swallow the specific reason. It
#: falls through to ``INCOMPLETE``, which is what "this is not the accepted
#: authority" actually means.
_OUTCOME_PRECEDENCE: tuple[
    tuple[frozenset[GateFailureCategory], PublicationOutcome], ...
] = (
    (
        frozenset({GateFailureCategory.PERSISTED_STATE}),
        PublicationOutcome.STALE,
    ),
    (
        frozenset(
            {
                GateFailureCategory.MISMATCHED_RELEASE,
                GateFailureCategory.POLICY_MISMATCH,
            }
        ),
        PublicationOutcome.MISMATCHED_RELEASE,
    ),
    (
        frozenset({GateFailureCategory.UNRESOLVED_RESIDUE}),
        PublicationOutcome.UNRESOLVED,
    ),
    (
        frozenset({GateFailureCategory.UNREVIEWED_RESIDUE}),
        PublicationOutcome.UNREVIEWED,
    ),
)


@dataclass(frozen=True)
class PublicationResult:
    """The complete outcome of one publication or activation attempt.

    ``report`` is present whenever a gate ran, including for refusals: a
    refused publication is an auditable decision. It is persisted only on
    success — recording evidence for a projection that was never published
    would be precisely the partial state atomic publication forbids.
    """

    outcome: PublicationOutcome
    projection_uuid: str
    gate: GateResult | None = None
    report: EvidenceReport | None = None
    evidence_report_hash: str | None = None


@dataclass(frozen=True)
class ActiveProjection:
    """The active mechanical authority of one package, or its typed absence."""

    outcome: PublicationOutcome
    package_uuid: str
    projection_uuid: str | None = None
    activated_at: str | None = None


def _outcome_for(gate: GateResult) -> PublicationOutcome:
    """Classify a failed gate into one typed outcome."""
    categories = gate.categories()
    for family, outcome in _OUTCOME_PRECEDENCE:
        if categories & family:
            return outcome
    return PublicationOutcome.INCOMPLETE


def _header(session: Session, projection_uuid: str) -> MechanicalProjectionORM | None:
    return session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == projection_uuid
        )
    ).scalar_one_or_none()


def _active_row(
    session: Session, package_uuid: str
) -> MechanicalActiveProjectionORM | None:
    return session.execute(
        select(MechanicalActiveProjectionORM).where(
            MechanicalActiveProjectionORM.package_uuid == package_uuid
        )
    ).scalar_one_or_none()


def resolve_active_projection(session: Session, package_uuid: str) -> ActiveProjection:
    """Return the package's active mechanical authority.

    ``UNPUBLISHED`` is a typed answer, not ``None`` and not an empty result: a
    caller that cannot tell "no authority is published" from "the query
    returned nothing" is one step from treating absence as permission.
    """
    row = _active_row(session, package_uuid)
    if row is None:
        return ActiveProjection(
            outcome=PublicationOutcome.UNPUBLISHED, package_uuid=package_uuid
        )
    return ActiveProjection(
        outcome=PublicationOutcome.PUBLISHED,
        package_uuid=package_uuid,
        projection_uuid=row.projection_uuid,
        activated_at=row.activated_at,
    )


def activate_projection(
    session: Session, projection_uuid: str, *, now: str
) -> PublicationResult:
    """Make an already-published projection its package's active authority.

    Independently fail-closed, and public for exactly that reason: this is the
    step that would be dangerous if it trusted its caller. It refuses any
    projection whose header is not already ``published`` with recorded
    evidence, so a projection that failed the gate cannot be activated by
    calling activation directly — the check does not depend on the caller
    having run the gate, or on having run it honestly.

    Flushes rather than commits; :func:`publish_projection` owns the commit.
    """
    header = _header(session, projection_uuid)
    if header is None:
        return PublicationResult(PublicationOutcome.ABSENT, projection_uuid)
    if header.publication_status != "published" or header.evidence_report_hash is None:
        return PublicationResult(PublicationOutcome.UNPUBLISHED, projection_uuid)

    active = _active_row(session, header.package_uuid)
    if active is not None:
        if active.projection_uuid != projection_uuid:
            return PublicationResult(
                PublicationOutcome.ACTIVE_CONFLICT,
                projection_uuid,
                evidence_report_hash=header.evidence_report_hash,
            )
        return PublicationResult(
            PublicationOutcome.ALREADY_PUBLISHED,
            projection_uuid,
            evidence_report_hash=header.evidence_report_hash,
        )

    session.add(
        MechanicalActiveProjectionORM(
            package_uuid=header.package_uuid,
            projection_uuid=projection_uuid,
            activated_at=now,
        )
    )
    session.flush()
    return PublicationResult(
        PublicationOutcome.PUBLISHED,
        projection_uuid,
        evidence_report_hash=header.evidence_report_hash,
    )


def publish_projection(
    session: Session,
    projection_uuid: str,
    oracle: AcceptedOracle | None,
    *,
    now: str,
) -> PublicationResult:
    """Gate a persisted projection and, only if it passes, publish it atomically.

    Commits on success, which is what makes publication the durability boundary
    rather than something a caller can forget to finish. On any refusal nothing
    was written, so there is nothing to roll back; on an unexpected exception
    after the first write the transaction is rolled back and the exception
    propagates, so a half-activated package cannot survive.

    *oracle* is ``None`` when no accepted authority is committed for the
    release. That is ``ABSENT`` — never an empty oracle, which would compare
    equal to an empty projection and publish nothing as if it were everything.
    """
    header = _header(session, projection_uuid)
    if header is None or oracle is None:
        return PublicationResult(PublicationOutcome.ABSENT, projection_uuid)

    gate = run_publication_gate(session, projection_uuid, oracle)
    report = build_evidence_report(header, gate)
    digest = report_hash(report)

    if not gate.passed:
        # Read-only up to here: the refusal leaves the database untouched, and
        # the report goes back to the caller rather than into a row.
        return PublicationResult(
            _outcome_for(gate), projection_uuid, gate=gate, report=report
        )

    if header.publication_status == "published":
        # Idempotent reuse, but only after the full gate above re-proved the
        # persisted state. The recorded evidence must also still be the
        # evidence this state derives — a published projection whose report
        # hash or judging oracle has drifted is stale, not reusable.
        if (
            header.evidence_report_hash != digest
            or header.oracle_identity != gate.oracle_identity
        ):
            return PublicationResult(
                PublicationOutcome.STALE, projection_uuid, gate=gate, report=report
            )
        result = activate_projection(session, projection_uuid, now=now)
        session.commit()
        return PublicationResult(
            (
                PublicationOutcome.ALREADY_PUBLISHED
                if result.outcome is PublicationOutcome.PUBLISHED
                else result.outcome
            ),
            projection_uuid,
            gate=gate,
            report=report,
            evidence_report_hash=digest,
        )

    active = _active_row(session, header.package_uuid)
    if active is not None and active.projection_uuid != projection_uuid:
        # The incumbent is left exactly as it is. Publication of a competing
        # projection is a decision for whoever retires the active one.
        return PublicationResult(
            PublicationOutcome.ACTIVE_CONFLICT,
            projection_uuid,
            gate=gate,
            report=report,
        )

    try:
        header.oracle_identity = gate.oracle_identity
        header.evidence_report_hash = digest
        header.report_payload = report.payload
        header.publication_status = "published"
        header.published_at = now
        session.flush()
        activation = activate_projection(session, projection_uuid, now=now)
        if activation.outcome is not PublicationOutcome.PUBLISHED:
            # Unreachable through this path (the conflict was checked above),
            # but a partially published header must never survive a surprise.
            session.rollback()
            return PublicationResult(
                activation.outcome, projection_uuid, gate=gate, report=report
            )
        session.commit()
    except Exception:
        session.rollback()
        raise

    return PublicationResult(
        PublicationOutcome.PUBLISHED,
        projection_uuid,
        gate=gate,
        report=report,
        evidence_report_hash=digest,
    )


def publish_from_committed_oracle(
    session: Session,
    projection_uuid: str,
    *,
    now: str,
    directory: Path | None = None,
) -> PublicationResult:
    """Production entry: judge a projection against *committed* accepted authority.

    The oracle is resolved from the committed oracle directory using the
    release the persisted header actually binds — not from a caller argument,
    so no caller can supply the authority that judges its own output.

    No accepted oracle is committed for the production SRD 5.2.1 release, so
    this path currently returns ``ABSENT`` for it. That is the honest state:
    the accepted full-corpus authority has not been reviewed and committed yet,
    and until it is, nothing over that release can be published.
    """
    header = _header(session, projection_uuid)
    if header is None:
        return PublicationResult(PublicationOutcome.ABSENT, projection_uuid)
    oracle = committed_oracle_for(
        header.package_uuid, header.release_version, directory=directory
    )
    return publish_projection(session, projection_uuid, oracle, now=now)
