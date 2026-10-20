"""Owner-approved D4 retention expiry -- CRD Issue 22 §6.

:func:`sweep` applies every time-based end condition at one instant ``now``
and returns counts (the disposal evidence; nothing expired is copied):

* hosted export artifacts 7 days after availability; staging/failed
  artifacts 24 hours after creation (file deleted, download revoked);
* minimized data-request records 24 calendar months after closure --
  never an open request, and never while its deletion suppression is still
  active (restore enforcement needs its inventory);
* support-action operations 24 months after their terminal outcome (an
  unresolved operation has no closure date and is kept);
* identity/administrator audit receipts 24 months after recording (remote);
* anomaly records: an investigated one 24 months after closure, routine
  system-only telemetry 30 days after observation;
* content-free provider refusal rows 30 days after recording;
* a closed account's entitlement history 24 months after recorded closure,
  through the entitlement owner, registered so a restore re-applies it.

Suppression release and BYOK-rights evidence are not calendar expiries:
:func:`release_suppression` requires verified end conditions, and both are
listed for annual review by :func:`reviews_due`.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.entitlement.retention import (
    expire_subject_history,
    record_rights_evidence_from_ledger,
)
from afterworlds.operations.export import remove_artifact
from afterworlds.operations.lifecycle import dispose_rows
from afterworlds.operations.orm import (
    AnomalyEventORM,
    DataRequestEventORM,
    DataRequestORM,
    EntitlementExpiryORM,
    ExportArtifactORM,
    PhaseEventORM,
    ReceiptCredentialORM,
    ReceiptORM,
    RequestInventoryORM,
    RightsEvidenceORM,
    SupportActionEventORM,
)
from afterworlds.operations.policy import (
    LOG_RETENTION,
    POLICY_VERSION,
    RECEIPT_RETENTION_MONTHS,
    add_calendar_months,
    is_expired,
)
from afterworlds.pipeline.provider._refusal_log import ProviderRefusalEvent
from afterworlds.remote.control_orm import (
    DeletionSuppressionORM,
    HostedAccountORM,
    IdentityAuditEventORM,
)
from afterworlds.remote.control_store import iso, parse_iso
from afterworlds.remote.storage import backup_disposition

_TERMINAL_SUPPORT = (
    "committed",
    "rejected_precondition",
    "rejected_stale",
    "conflict",
    "failed",
)


@dataclass
class SweepResult:
    artifacts_expired: int = 0
    staging_removed: int = 0
    requests_expired: int = 0
    support_operations_expired: int = 0
    audit_receipts_expired: int = 0
    anomalies_expired: int = 0
    refusal_rows_expired: int = 0
    entitlement_subjects_expired: int = 0
    details: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, int]:
        return {k: v for k, v in vars(self).items() if isinstance(v, int)}


def _months(value: str, now: datetime) -> bool:
    return is_expired(
        add_calendar_months(parse_iso(value), RECEIPT_RETENTION_MONTHS), now
    )


def expire_artifacts(
    ops: sessionmaker[Session], now: datetime, result: SweepResult
) -> None:
    with ops() as s:
        rows = list(
            s.scalars(
                sa.select(ExportArtifactORM).where(
                    ExportArtifactORM.removed_at.is_(None)
                )
            )
        )
    for row in rows:
        if is_expired(parse_iso(row.expires_at), now) and remove_artifact(
            ops, row.artifact_id, now=now
        ):
            if row.status == "available":
                result.artifacts_expired += 1
            else:
                result.staging_removed += 1


def _active_suppression_requests(control: sessionmaker[Session] | None) -> set[str]:
    if control is None:
        return set()
    with control() as s:
        return set(
            s.scalars(
                sa.select(DeletionSuppressionORM.request_id).where(
                    DeletionSuppressionORM.status == "active"
                )
            )
        )


def expire_requests(
    ops: sessionmaker[Session],
    control: sessionmaker[Session] | None,
    now: datetime,
    result: SweepResult,
) -> None:
    protected = _active_suppression_requests(control)
    with ops() as s:
        candidates = []
        for header in s.scalars(sa.select(DataRequestORM)):
            last = s.scalars(
                sa.select(DataRequestEventORM)
                .where(DataRequestEventORM.request_id == header.request_id)
                .order_by(DataRequestEventORM.revision.desc())
            ).first()
            if (
                last is not None
                and last.state in ("completed", "rejected")
                and last.closed_at
                and _months(last.closed_at, now)
                and header.request_id not in protected
            ):
                candidates.append(header.request_id)
    for request_id in candidates:
        with ops.begin() as s:
            remaining = s.scalar(
                sa.select(sa.func.count()).where(
                    ExportArtifactORM.request_id == request_id,
                    ExportArtifactORM.removed_at.is_(None),
                )
            )
            if remaining:
                continue  # an unexpired artifact first follows its own clock
            for table, column in (
                ("ops_receipts", ReceiptORM.request_id),
                ("ops_phase_events", PhaseEventORM.request_id),
                ("ops_data_request_events", DataRequestEventORM.request_id),
            ):
                dispose_rows(s, table, sa.column(column.key) == request_id)
            for model in (
                RequestInventoryORM,
                ReceiptCredentialORM,
                ExportArtifactORM,
            ):
                s.execute(sa.delete(model).where(model.request_id == request_id))
            s.execute(
                sa.delete(DataRequestORM).where(DataRequestORM.request_id == request_id)
            )
        result.requests_expired += 1


def expire_support(
    ops: sessionmaker[Session], now: datetime, result: SweepResult
) -> None:
    with ops() as s:
        closed = {
            op: recorded
            for op, recorded in s.execute(
                sa.select(
                    SupportActionEventORM.operation_id,
                    SupportActionEventORM.recorded_at,
                ).where(SupportActionEventORM.outcome_code.in_(_TERMINAL_SUPPORT))
            )
        }
    for operation_id, recorded in closed.items():
        if _months(recorded, now):
            with ops.begin() as s:
                dispose_rows(
                    s, "ops_support_events", sa.column("operation_id") == operation_id
                )
            result.support_operations_expired += 1


def expire_anomalies(
    ops: sessionmaker[Session], now: datetime, result: SweepResult
) -> None:
    with ops() as s:
        streams: dict[str, list[AnomalyEventORM]] = {}
        for row in s.scalars(
            sa.select(AnomalyEventORM).order_by(AnomalyEventORM.event_order)
        ):
            streams.setdefault(row.anomaly_id, []).append(row)
    for anomaly_id, events in streams.items():
        last = events[-1]
        investigated = any(e.actor_ref != "system" for e in events)
        if investigated:
            due = last.investigation_state == "closed" and _months(
                last.observed_at, now
            )
        else:
            due = is_expired(parse_iso(events[0].observed_at) + LOG_RETENTION, now)
        if due:
            with ops.begin() as s:
                dispose_rows(
                    s, "ops_anomaly_events", sa.column("anomaly_id") == anomaly_id
                )
            result.anomalies_expired += 1


def expire_refusal_log(
    content: sessionmaker[Session], now: datetime, result: SweepResult
) -> None:
    cutoff = (now - LOG_RETENTION).replace(tzinfo=None)
    with content.begin() as s:
        result.refusal_rows_expired += dispose_rows(
            s,
            "provider_refusal_log",
            sa.column("created_at", ProviderRefusalEvent.created_at.type) <= cutoff,
        )


def expire_audit_receipts(
    control: sessionmaker[Session], now: datetime, result: SweepResult
) -> None:
    with control() as s:
        due = [
            e.event_order
            for e in s.scalars(sa.select(IdentityAuditEventORM))
            if _months(e.recorded_at, now)
        ]
    if due:
        with control.begin() as s:
            result.audit_receipts_expired += dispose_rows(
                s, "identity_audit_events", sa.column("event_order").in_(due)
            )


def expire_closed_ledgers(
    control: sessionmaker[Session],
    content: sessionmaker[Session],
    now: datetime,
    result: SweepResult,
) -> None:
    with control() as s:
        accounts = [
            (a.account_id, a.closed_at)
            for a in s.scalars(
                sa.select(HostedAccountORM).where(HostedAccountORM.status == "closed")
            )
            if a.closed_at
        ]
        done = set(s.scalars(sa.select(EntitlementExpiryORM.subject_ref)))
    for account_id, closed_at in accounts:
        if account_id in done or not _months(closed_at, now):
            continue
        # The perpetual right outlives the ledger: evidence first (accounts
        # closed by #205 self-service never passed through erasure).
        record_rights_evidence_from_ledger(content, control, account_id, now=now)
        with content.begin() as s:
            removed = expire_subject_history(s, UUID(account_id))
        with control.begin() as s:
            s.add(
                EntitlementExpiryORM(
                    subject_ref=account_id,
                    closed_at=closed_at,
                    expired_at=iso(now),
                    event_count=removed,
                    policy_version=POLICY_VERSION,
                )
            )
        result.entitlement_subjects_expired += 1


def reapply_ledger_expiries(
    control: sessionmaker[Session], content: sessionmaker[Session]
) -> int:
    """Restore enforcement: an expired subject's events that came back with a
    restored snapshot are expired again."""
    with control() as s:
        subjects = list(s.scalars(sa.select(EntitlementExpiryORM.subject_ref)))
    removed = 0
    for subject in subjects:
        with content.begin() as s:
            removed += expire_subject_history(s, UUID(subject))
    return removed


def sweep(
    *,
    ops: sessionmaker[Session],
    content: sessionmaker[Session],
    control: sessionmaker[Session] | None,
    now: datetime,
) -> SweepResult:
    result = SweepResult()
    expire_artifacts(ops, now, result)
    expire_requests(ops, control, now, result)
    expire_support(ops, now, result)
    expire_anomalies(ops, now, result)
    expire_refusal_log(content, now, result)
    if control is not None:
        expire_audit_receipts(control, now, result)
        expire_closed_ledgers(control, content, now, result)
    return result


# -- conditional end conditions --------------------------------------------


def release_suppression(
    control: sessionmaker[Session], suppression_id: str, *, now: datetime
) -> bool:
    """Release a suppression only when its end conditions are verified:
    every affected backup disposed, and its backup/replay horizons passed (no
    delayed event or job can recreate the subject). Returns whether released."""
    disposition = backup_disposition(control, suppression_id, now=now)
    with control.begin() as s:
        row = s.get(DeletionSuppressionORM, suppression_id)
        if row is None or row.status != "active":
            return False
        horizons: Iterable[str | None] = (row.backup_horizon_at, row.replay_horizon_at)
        if not disposition.complete or any(
            h is not None and not is_expired(parse_iso(h), now) for h in horizons
        ):
            return False
        row.status = "released"
        row.release_verified_at = iso(now)
    return True


def reviews_due(
    ops: sessionmaker[Session], control: sessionmaker[Session] | None, *, now: datetime
) -> dict[str, list[str]]:
    """Annual reviews due: active suppressions and BYOK-rights evidence."""
    due: dict[str, list[str]] = {"suppressions": [], "rights_evidence": []}
    if control is not None:
        with control() as s:
            due["suppressions"] = [
                r.suppression_id
                for r in s.scalars(
                    sa.select(DeletionSuppressionORM).where(
                        DeletionSuppressionORM.status == "active"
                    )
                )
                if is_expired(parse_iso(r.annual_review_at), now)
            ]
    with ops() as s:
        due["rights_evidence"] = [
            r.rights_id
            for r in s.scalars(sa.select(RightsEvidenceORM))
            if is_expired(parse_iso(r.annual_review_at), now)
        ]
    return due
