"""Basic anomaly visibility -- CRD Issue 22 §7.

A read-only view assembled from durable sources only, each with its own
stable source reference: failed or uncertain support actions, failed,
blocked or overdue data requests, entitlement replay/projection
inconsistency, delivered-turn settlement failures (recorded durably when the
nonblocking ``settlement_warning`` is returned) and unfinished restores.
A source that cannot be read is reported ``unavailable`` -- never an
all-clear. Expected entitlement states (negative balances, depleted credits,
inactive hosted access, lapsed Cloud Services) and provider refusals are not
anomalies. No fraud score is computed; CRD Issue 23 payment events are a
documented, not-yet-integrated source.

Investigation notes append to an anomaly's own stream; reading or noting
never repairs, retries or charges anything.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.entitlement.inspection import (
    ReplayStatus,
    replay_check,
    subjects_with_events,
)
from afterworlds.operations.errors import OperationError, OperationErrorKind
from afterworlds.operations.orm import AnomalyEventORM, SupportActionEventORM
from afterworlds.operations.requests import RequestStore
from afterworlds.operations.support import bounded_text
from afterworlds.remote.control_store import iso, parse_iso
from afterworlds.remote.storage import pending_restores

logger = logging.getLogger("afterworlds.operations.anomalies")

#: A support action still only ``requested`` after this is uncertain.
UNCERTAIN_AFTER = timedelta(minutes=5)
STATES = frozenset({"open", "investigating", "closed"})
NOTE_CODES = frozenset(
    {"investigating", "explained_expected", "escalated", "resolved", "other"}
)


@dataclass(frozen=True)
class Anomaly:
    anomaly_id: str
    source_kind: str
    source_id: str
    subject_ref: str | None
    observed_at: datetime
    signal_code: str
    explanation: str
    investigation_state: str
    notes: tuple[dict[str, str | None], ...]


@dataclass(frozen=True)
class AnomalyReport:
    anomalies: tuple[Anomaly, ...]
    #: source -> available | unavailable | not_integrated
    sources: dict[str, str]
    generated_at: datetime


@dataclass(frozen=True)
class SettlementSink:
    """Where an admitted turn worker records a settlement failure: the ops
    store, and -- remotely, where that is the control store -- the content
    store, which keeps a content-free coverage gap if the ops write fails."""

    ops: sessionmaker[Session]
    gap_store: sessionmaker[Session] | None = None


#: Set by the turn routes for the request (copied into its worker thread).
SETTLEMENT_SINK: ContextVar[SettlementSink | None] = ContextVar(
    "afterworlds_settlement_sink", default=None
)
#: A settlement failure that could not be recorded is kept, without subject
#: or Turn, in the content chain's anomaly table (review of 03506df9, P1-2):
#: after a restart the source is still reported degraded until staff close
#: the gap -- table availability alone never restores coverage.
GAP_KIND = "settlement_coverage"
GAP_SIGNAL = "settlement_unrecorded"
#: Set when a settlement failure could not be recorded in this process, so
#: the anomaly view reports the source degraded instead of healthy.
_UNRECORDED = threading.Event()


def record_settlement_failure(
    sink: SettlementSink | None,
    *,
    subject_ref: str,
    turn_id: str | None,
    error_class: str,
    now: datetime,
) -> None:
    """Make a delivered turn's settlement failure durable (the turn stays
    delivered; nothing is retried or charged). Best effort: a failure to
    record is logged with a fixed category and never affects the turn.
    No store (a caller that set no ``SETTLEMENT_SINK``) is such a failure too,
    so it degrades the source instead of disappearing."""
    source = turn_id or str(uuid4())
    if sink is None:
        _UNRECORDED.set()
        logger.error("anomaly record failed: category=settlement_anomaly_unrecorded")
        return
    try:
        with sink.ops.begin() as s:
            s.add(
                AnomalyEventORM(
                    event_id=str(uuid4()),
                    schema_version=1,
                    anomaly_id=f"turn_settlement:{source}",
                    subject_ref=subject_ref,
                    source_kind="turn_settlement",
                    source_id=source,
                    observed_at=iso(now),
                    safe_signal_code="settlement_failed",
                    investigation_state="open",
                    actor_ref="system",
                    note_code=error_class[:32],
                )
            )
    except SQLAlchemyError:
        _UNRECORDED.set()
        logger.error("anomaly record failed: category=settlement_anomaly_unrecorded")
        _record_gap(sink.gap_store, now)


def _record_gap(store: sessionmaker[Session] | None, now: datetime) -> None:
    """Durable, content-free evidence that settlement coverage is incomplete
    (codes and time only). If this store refuses too, only the process flag
    and the log remain (documented limit: both live stores refusing writes)."""
    if store is None:
        return
    gap = str(uuid4())
    try:
        with store.begin() as s:
            s.add(
                AnomalyEventORM(
                    event_id=str(uuid4()),
                    schema_version=1,
                    anomaly_id=f"{GAP_KIND}:{gap}",
                    subject_ref=None,
                    source_kind=GAP_KIND,
                    source_id=gap,
                    observed_at=iso(now),
                    safe_signal_code=GAP_SIGNAL,
                    investigation_state="open",
                    actor_ref="system",
                    note_code="ops_store_write_failed",
                )
            )
    except SQLAlchemyError:
        logger.error("anomaly record failed: category=settlement_coverage_unrecorded")


class AnomalyService:
    def __init__(
        self,
        ops: sessionmaker[Session],
        content: sessionmaker[Session],
        requests: RequestStore,
        *,
        control: sessionmaker[Session] | None,
        now: Callable[[], datetime],
    ) -> None:
        self._ops = ops
        self._content = content
        self._requests = requests
        self._control = control
        self._now = now

    def report(self) -> AnomalyReport:
        now = self._now()
        found: list[tuple[str, str, str | None, datetime, str, str]] = []
        sources: dict[str, str] = {"commercial_events": "not_integrated"}

        def read(name: str, fn: Callable[[], None]) -> None:
            try:
                fn()
                sources[name] = "available"
            except (SQLAlchemyError, OperationError, OSError):
                sources[name] = "unavailable"

        def support() -> None:
            with self._ops() as s:
                rows = list(
                    s.scalars(
                        sa.select(SupportActionEventORM).order_by(
                            SupportActionEventORM.event_order
                        )
                    )
                )
            last: dict[str, SupportActionEventORM] = {}
            for row in rows:
                last[row.operation_id] = row
            for op, row in last.items():
                at = parse_iso(row.recorded_at)
                if row.outcome_code == "requested" and now - at >= UNCERTAIN_AFTER:
                    found.append(
                        (
                            "support_operation",
                            op,
                            row.subject_ref,
                            at,
                            "support_outcome_uncertain",
                            "A support action has no confirmed outcome; read its "
                            "status before any other effect.",
                        )
                    )
                elif row.outcome_code == "failed":
                    found.append(
                        (
                            "support_operation",
                            op,
                            row.subject_ref,
                            at,
                            "support_action_failed",
                            "A support action failed without effect.",
                        )
                    )

        def requests() -> None:
            for rid in self._requests.request_ids():
                view = self._requests.view(rid)
                at = view.transitions[-1].recorded_at
                if view.state == "failed":
                    found.append(
                        (
                            "data_request",
                            rid,
                            view.subject_ref,
                            at,
                            "data_request_failed",
                            "A data request attempt failed; retry or resolve it "
                            "within its deadline.",
                        )
                    )
                for deadline in view.overdue:
                    found.append(
                        (
                            "data_request",
                            rid,
                            view.subject_ref,
                            now,
                            f"overdue_{deadline}",
                            "A data request missed its approved deadline.",
                        )
                    )
                if any(p.outcome_code == "dependency_unavailable" for p in view.phases):
                    found.append(
                        (
                            "data_request",
                            rid,
                            view.subject_ref,
                            at,
                            "dependency_unavailable",
                            "Account closure waits on CRD Issue 23 commercial "
                            "closure, which is not yet implemented.",
                        )
                    )

        def ledger() -> None:
            with self._content() as s:
                for subject in subjects_with_events(s):
                    check = replay_check(s, subject)
                    if check.status in (ReplayStatus.MISMATCH, ReplayStatus.UNREADABLE):
                        found.append(
                            (
                                "entitlement_subject",
                                str(subject),
                                str(subject),
                                now,
                                f"entitlement_replay_{check.status.value}",
                                "Replaying the ordered ledger does not reproduce "
                                "the projection ("
                                + (check.detail_code or "unknown")
                                + "); nothing was repaired.",
                            )
                        )

        def restores() -> None:
            if self._control is None:
                return
            for restore_id in pending_restores(self._control):
                found.append(
                    (
                        "restore",
                        restore_id,
                        None,
                        now,
                        "restore_unfinished",
                        "A restore is not yet enforced and verified; the app "
                        "stays fenced.",
                    )
                )

        def coverage_gaps() -> None:
            # Remote only: the content store keeps gaps the control store
            # could not take (locally they are one store).
            if self._control is None or self._content is self._ops:
                return
            with self._content() as s:
                for row in s.scalars(
                    sa.select(AnomalyEventORM)
                    .where(AnomalyEventORM.source_kind == GAP_KIND)
                    .order_by(AnomalyEventORM.event_order)
                ):
                    found.append(
                        (
                            GAP_KIND,
                            row.source_id,
                            None,
                            parse_iso(row.observed_at),
                            GAP_SIGNAL,
                            "A delivered turn's settlement failure could not be "
                            "recorded; settlement failures may be missing from "
                            "this view since then. Review the ledger and logs, "
                            "then close this.",
                        )
                    )

        read("support_operations", support)
        read("data_requests", requests)
        read("entitlement_replay", ledger)
        if self._control is not None:
            read("restores", restores)

        gaps_readable = True
        try:
            coverage_gaps()
        except SQLAlchemyError:
            gaps_readable = False
        streams: dict[str, list[AnomalyEventORM]] = {}
        try:
            with self._ops() as s:
                for row in s.scalars(
                    sa.select(AnomalyEventORM).order_by(AnomalyEventORM.event_order)
                ):
                    streams.setdefault(row.anomaly_id, []).append(row)
            # Degraded while this process could not record a failure, or
            # while any durable coverage gap is not closed by staff.
            open_gap = False
            for kind, sid, _subject, _at, signal, _text in found:
                if kind == GAP_KIND:
                    notes = streams.get(f"{kind}:{sid}:{signal}", [])
                    if not notes or notes[-1].investigation_state != "closed":
                        open_gap = True
            if not gaps_readable:
                sources["settlement_failures"] = "unavailable"
            elif _UNRECORDED.is_set() or open_gap:
                sources["settlement_failures"] = "degraded"
            else:
                sources["settlement_failures"] = "available"
        except SQLAlchemyError:
            sources["settlement_failures"] = "unavailable"

        anomalies: list[Anomaly] = []
        seen: set[str] = set()
        for kind, sid, subject, at, signal, text in found:
            anomaly_id = f"{kind}:{sid}:{signal}"
            seen.add(anomaly_id)
            anomalies.append(
                _with_stream(
                    anomaly_id,
                    kind,
                    sid,
                    subject,
                    at,
                    signal,
                    text,
                    streams.get(anomaly_id, []),
                )
            )
        for anomaly_id, events in streams.items():
            if anomaly_id in seen:
                continue
            # A recorded settlement failure, or the noted history of a derived
            # anomaly no longer detected at its source.
            first = events[0]
            anomalies.append(
                _with_stream(
                    anomaly_id,
                    first.source_kind,
                    first.source_id,
                    first.subject_ref,
                    parse_iso(first.observed_at),
                    first.safe_signal_code,
                    (
                        "A delivered turn's settlement failed; the turn stays "
                        "delivered and nothing was retried or charged."
                        if first.source_kind == "turn_settlement"
                        else "No longer detected at its source."
                    ),
                    events,
                )
            )
        anomalies.sort(key=lambda a: (a.observed_at, a.anomaly_id))
        return AnomalyReport(tuple(anomalies), sources, now)

    def add_note(
        self,
        actor_ref: str,
        anomaly_id: str,
        *,
        state: str,
        note_code: str,
        note_text: str | None,
    ) -> Anomaly:
        if state not in STATES or note_code not in NOTE_CODES:
            raise OperationError(
                OperationErrorKind.INVALID_INPUT, "Unsupported investigation state."
            )
        text = bounded_text(note_text, "note") if note_text else None
        current = {a.anomaly_id: a for a in self.report().anomalies}
        anomaly = current.get(anomaly_id)
        if anomaly is None:
            raise OperationError(OperationErrorKind.NOT_FOUND, "Unknown anomaly.")
        with self._ops.begin() as s:
            s.add(
                AnomalyEventORM(
                    event_id=str(uuid4()),
                    schema_version=1,
                    anomaly_id=anomaly_id,
                    subject_ref=anomaly.subject_ref,
                    source_kind=anomaly.source_kind,
                    source_id=anomaly.source_id,
                    observed_at=iso(self._now()),
                    safe_signal_code=anomaly.signal_code,
                    investigation_state=state,
                    actor_ref=actor_ref,
                    note_code=note_code,
                    note_text=text,
                )
            )
        return {a.anomaly_id: a for a in self.report().anomalies}[anomaly_id]


def _with_stream(
    anomaly_id: str,
    kind: str,
    source_id: str,
    subject: str | None,
    at: datetime,
    signal: str,
    explanation: str,
    events: list[AnomalyEventORM],
) -> Anomaly:
    notes = tuple(
        {
            "state": e.investigation_state,
            "note_code": e.note_code,
            "note_text": e.note_text,
            "actor": "system" if e.actor_ref == "system" else "administrator",
            "recorded_at": e.observed_at,
        }
        for e in events
        if e.actor_ref != "system"
    )
    state = events[-1].investigation_state if events else "open"
    return Anomaly(
        anomaly_id=anomaly_id,
        source_kind=kind,
        source_id=source_id,
        subject_ref=subject,
        observed_at=at,
        signal_code=signal,
        explanation=explanation,
        investigation_state=state,
        notes=notes,
    )
