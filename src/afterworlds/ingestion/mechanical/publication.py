"""Atomic mechanical-projection publication — CRD Issue 5d, Decision 8.

Completes the lifecycle CRD Issue 5c established and #139 built the first half
of:

``build → persist draft → reconstruct → prove → gate → atomically publish``

**The supported surface is one function.** :func:`publish_from_committed_oracle`
resolves the judging authority from the packaged committed-oracle directory
using the release the persisted header actually binds. Nothing exported here
accepts an oracle, an oracle directory, or an activation request, because a
publication API whose caller supplies the authority that judges its own output
proves only that the caller is self-consistent. Gating and activation are
private steps of that one operation; tests that need to publish against a
fixture oracle reach for the private seam deliberately and visibly.

Four properties are load-bearing, and each is enforced by structure rather than
by discipline:

* **A draft never becomes active before the gate succeeds.** The gate is
  read-only, so a failing run leaves the database exactly as it found it —
  there is no partial write to undo. Activation is reachable only from a
  publication operation that has just completed the full committed-oracle gate,
  so there is no path that activates on a status column alone.
* **Published projections are immutable.** Re-running publication re-runs the
  *complete* gate against reconstructed state and additionally re-derives the
  evidence report, requiring the recorded payload to be exactly that report, to
  hash to the recorded hash, and to have been judged by the same oracle. A
  projection — or its recorded evidence — edited after publication therefore
  stops being publishable and stops verifying.
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

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.gate import (
    GateFailureCategory,
    GateResult,
    run_publication_gate,
)
from afterworlds.ingestion.mechanical.oracle import AcceptedOracle, committed_oracle_for
from afterworlds.ingestion.mechanical.report import (
    EVIDENCE_REPORT_SCHEMA_VERSION,
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
    "publish_from_committed_oracle",
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
    #: Persisted state no longer derives its own identity or recorded evidence,
    #: or the 5c release it binds is not an exactly-published, reconstructable
    #: release. Both are the same finding from an auditor's seat: something the
    #: decision rests on is not what the record says it is.
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
        frozenset(
            {
                GateFailureCategory.PERSISTED_STATE,
                GateFailureCategory.BOUND_RELEASE,
            }
        ),
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


#: Every top-level key :func:`build_evidence_report` produces. A payload missing
#: any of them is not this schema, whatever its recorded version claims.
_REQUIRED_REPORT_KEYS = frozenset(
    {
        "report_version",
        "source_release",
        "mechanical_projection",
        "accepted_oracle",
        "gate",
        "obligations",
        "drift_diagnostics",
    }
)


def _recorded_evidence_closure(
    header: MechanicalProjectionORM,
) -> tuple[str, ...]:
    """Is the projection's *recorded* publication evidence internally closed?

    The half of evidence verification that needs nothing but the row itself:
    the payload is present and is the supported schema, the recorded hash is
    the hash *of that payload*, and the publication fields that must exist
    together do.

    The stored hash is never trusted on its own. A hash column identifies a
    payload; checking only the column and ignoring the payload it identifies
    means a cleared or edited ``report_payload`` still reports as verified, and
    the recorded evidence stops being reconstructable from the database while
    publication keeps claiming it is.
    """
    failures: list[str] = []
    if header.evidence_report_hash is None:
        failures.append("no recorded evidence_report_hash")
    if header.oracle_identity is None:
        failures.append("no recorded judging-oracle identity")
    if header.published_at is None:
        failures.append("published projection records no published_at")
    if header.persisted_state_digest is None:
        failures.append("no recorded persisted-state digest")

    payload = header.report_payload
    if payload is None:
        failures.append("no recorded evidence-report payload")
    elif (
        not isinstance(payload, dict)
        or payload.get("report_version") != EVIDENCE_REPORT_SCHEMA_VERSION
        or not set(payload) >= _REQUIRED_REPORT_KEYS
    ):
        failures.append(
            "recorded evidence-report payload is not the supported "
            f"{EVIDENCE_REPORT_SCHEMA_VERSION!r} schema"
        )
    elif report_hash(EvidenceReport(payload=payload)) != header.evidence_report_hash:
        failures.append(
            "recorded evidence-report payload does not hash to the recorded "
            "evidence_report_hash"
        )
    return tuple(failures)


def _recorded_evidence_failures(
    header: MechanicalProjectionORM,
    gate: GateResult,
    report: EvidenceReport,
    digest: str,
) -> tuple[str, ...]:
    """Is the recorded evidence closed *and* still the evidence this state derives?

    Adds the comparisons that need a completed gate run: the persisted payload
    must be exactly the report freshly derived from the current reconstructed
    state under the current committed oracle, its hash must be the recorded
    one, and the judging oracle must be the same authority. A published
    projection whose state, evidence, or judging authority has drifted is
    stale — not reusable, and not re-activatable.
    """
    failures = list(_recorded_evidence_closure(header))
    if header.report_payload != report.payload:
        failures.append(
            "recorded evidence-report payload is not the report this "
            "reconstructed state and committed oracle derive"
        )
    if header.evidence_report_hash != digest:
        failures.append(
            f"recorded evidence_report_hash {header.evidence_report_hash!r} is "
            f"not the freshly derived {digest!r}"
        )
    if header.oracle_identity != gate.oracle_identity:
        failures.append(
            f"recorded judging oracle {header.oracle_identity!r} is not the "
            f"committed oracle {gate.oracle_identity!r}"
        )
    return tuple(dict.fromkeys(failures))


def resolve_active_projection(session: Session, package_uuid: str) -> ActiveProjection:
    """Return the package's active mechanical authority.

    ``UNPUBLISHED`` is a typed answer, not ``None`` and not an empty result: a
    caller that cannot tell "no authority is published" from "the query
    returned nothing" is one step from treating absence as permission.

    An activation row is not by itself an authority claim. This resolves the
    projection it names and requires that projection to be published with
    internally closed recorded evidence; a row pointing at a draft, at another
    package's projection, or at one whose evidence was cleared or edited
    resolves to ``STALE``, never to ``PUBLISHED``.

    **The contract this asserts** is recorded-evidence closure, not a re-run of
    the publication proof: it does not resolve the committed oracle or re-gate
    reconstructed state, so evidence edited *consistently* (payload and hash
    together) is caught by :func:`publish_from_committed_oracle` rather than
    here. Re-proof is a publication operation, and runtime binding resolution
    is CRD Issue 5d PR 3's; this stays a read-only assertion about what the
    database records.
    """
    row = _active_row(session, package_uuid)
    if row is None:
        return ActiveProjection(
            outcome=PublicationOutcome.UNPUBLISHED, package_uuid=package_uuid
        )
    header = _header(session, row.projection_uuid)
    stale = ActiveProjection(
        outcome=PublicationOutcome.STALE,
        package_uuid=package_uuid,
        projection_uuid=row.projection_uuid,
        activated_at=row.activated_at,
    )
    if (
        header is None
        or header.package_uuid != package_uuid
        or header.publication_status != "published"
        or _recorded_evidence_closure(header)
    ):
        return stale
    return ActiveProjection(
        outcome=PublicationOutcome.PUBLISHED,
        package_uuid=package_uuid,
        projection_uuid=row.projection_uuid,
        activated_at=row.activated_at,
    )


def _activate_projection(
    session: Session, projection_uuid: str, *, now: str
) -> PublicationResult:
    """Make a just-proven projection its package's active authority.

    Private, and reachable only from :func:`_publish_projection` after the full
    committed-oracle gate has passed against reconstructed state and the
    recorded evidence has been verified. It is not a step a caller may perform
    on its own: ``publication_status``, a non-NULL hash, and the presence of an
    evidence column are what a successful publication *leaves behind*, not
    proof that one happened, and a function that activated on them would make a
    hand-edited or partially migrated header active authority.

    The header checks below are the residue of that ordering, kept as a
    same-transaction assertion rather than as the gate.

    Flushes rather than commits; :func:`_publish_projection` owns the commit.
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


def _publish_projection(
    session: Session,
    projection_uuid: str,
    oracle: AcceptedOracle | None,
    *,
    now: str,
) -> PublicationResult:
    """Gate a persisted projection and, only if it passes, publish it atomically.

    Private: *oracle* is the authority that judges the projection, so exporting
    this would restore exactly the bypass removing the oracle-directory
    parameter closes — a caller able to author the authority its own output is
    measured against. :func:`publish_from_committed_oracle` is the supported
    entry, and it resolves the oracle from the committed directory rather than
    accepting one. Tests reach for this seam directly and visibly, which is a
    property of the test, not an API a production caller can use by accident.

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
        # persisted state *and* the recorded evidence proves closed against the
        # freshly derived report. Reuse is the path an auditor is most likely to
        # take on trust, so it is the one that must not accept a stored claim.
        if _recorded_evidence_failures(header, gate, report, digest):
            return PublicationResult(
                PublicationOutcome.STALE, projection_uuid, gate=gate, report=report
            )
        result = _activate_projection(session, projection_uuid, now=now)
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
        activation = _activate_projection(session, projection_uuid, now=now)
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
    session: Session, projection_uuid: str, *, now: str
) -> PublicationResult:
    """The production publication entry — the only supported one.

    The oracle is resolved from :data:`oracle.COMMITTED_ORACLE_DIR`, the fixed
    packaged location, using the release the persisted header actually binds.
    There is deliberately no directory parameter: one would let a caller point
    publication at a writable directory holding a self-authored oracle that
    matches its own projection, which is the guarantee this function exists to
    make — and a guarantee with an override is a default.

    Re-publication and re-activation enter here too, and re-run the complete
    proof. There is no cheaper door.

    No accepted oracle is committed for the production SRD 5.2.1 release, so
    this path currently returns ``ABSENT`` for it. That is the honest state:
    the accepted full-corpus authority has not been reviewed and committed yet,
    and until it is, nothing over that release can be published.
    """
    header = _header(session, projection_uuid)
    if header is None:
        return PublicationResult(PublicationOutcome.ABSENT, projection_uuid)
    oracle = committed_oracle_for(header.package_uuid, header.release_version)
    return _publish_projection(session, projection_uuid, oracle, now=now)
