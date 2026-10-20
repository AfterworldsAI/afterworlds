"""Data-request lifecycle -- CRD Issue 22 §4 (Story and account-wide export
and deletion, remote and local).

A request is an immutable header (:class:`DataRequestORM`) plus an ordered,
append-only stream of transitions (:class:`DataRequestEventORM`); its state
and revision are the last transition. Every transition names the expected
current revision (stale or invalid transitions are refused) and the trusted
actor. Retries are new attempts on the same request; failures are never
rewritten.

States::

    requested --confirm--> awaiting_authorization --approve--> approved
    (deletion only)        (export starts here)                  |
                                                       execute -> in_progress
    in_progress -> completed | failed;  failed --execute (new attempt)--> ...
    requested/awaiting_authorization/approved --reject--> rejected

Clocks (D4): an export's service clock starts at verification (the
authenticated owner request); a deletion's at verified, explicit scope
confirmation. Approval waits, retries, restarts and new attempts never move
them. Remote requests are approved and executed by the Owner administrator
(two recorded steps, the same person allowed); a local request is confirmed
and executed by the local owner, with no cloud account.

Fulfillment is real: :mod:`afterworlds.operations.export` produces the
artifact and :mod:`afterworlds.operations.deletion` removes the data; a
manual state edit cannot complete a request (no transition sets
``completed`` except those executors' verified results).
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.operations.errors import OperationError, OperationErrorKind
from afterworlds.operations.orm import (
    DataRequestEventORM,
    DataRequestORM,
    ExportArtifactORM,
    PhaseEventORM,
    ReceiptCredentialORM,
    ReceiptORM,
)
from afterworlds.operations.policy import (
    DELETION_BACKUP_DEADLINE,
    EXPORT_PRODUCTION,
    LIVE_DELETION,
    POLICY_VERSION,
    is_overdue,
)
from afterworlds.operations.support import bounded_text
from afterworlds.remote.control_store import iso, parse_iso, utc_now
from afterworlds.remote.verifiers import new_token, token_verifier


class RequestKind(StrEnum):
    EXPORT = "export"
    DELETION = "deletion"


class RequestScope(StrEnum):
    STORY = "story"
    ACCOUNT = "account"


class RequestState(StrEnum):
    REQUESTED = "requested"
    AWAITING_AUTHORIZATION = "awaiting_authorization"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


OPEN_STATES = frozenset(
    {
        RequestState.REQUESTED,
        RequestState.AWAITING_AUTHORIZATION,
        RequestState.APPROVED,
        RequestState.IN_PROGRESS,
        RequestState.FAILED,
    }
)
CLOSED_STATES = frozenset({RequestState.COMPLETED, RequestState.REJECTED})

#: Bounded reason codes an administrator may record with a rejection.
REJECTION_CODES = frozenset(
    {"out_of_scope", "unverified_requester", "duplicate", "administrator"}
)


@dataclass(frozen=True)
class RequestActor:
    """The trusted actor of a lifecycle step, from server state only."""

    #: "requester" (owner/Sojourner or local owner) | "administrator" |
    #: "system"
    role: str
    actor_ref: str
    environment: str
    subject_ref: str | None = None


@dataclass(frozen=True)
class TransitionView:
    event_id: str
    event_order: int
    revision: int
    state: str
    attempt_id: str | None
    actor_ref: str
    authorization_code: str | None
    reason_code: str | None
    reason_text: str | None
    recorded_at: datetime


@dataclass(frozen=True)
class PhaseView:
    phase_code: str
    outcome_code: str
    attempt_id: str
    counts: dict[str, int]
    detail_code: str | None
    observed_at: datetime
    deadline_at: datetime | None


@dataclass(frozen=True)
class ArtifactView:
    artifact_id: str
    status: str
    available_at: datetime | None
    expires_at: datetime
    removed_at: datetime | None
    size_bytes: int | None


@dataclass(frozen=True)
class RequestView:
    request_id: str
    kind: str
    environment: str
    scope: str
    subject_ref: str
    story_refs: tuple[str, ...]
    requester_ref: str
    requested_at: datetime
    verified_at: datetime
    policy_version: str
    state: str
    revision: int
    confirmed_at: datetime | None
    approved_at: datetime | None
    closed_at: datetime | None
    export_deadline_at: datetime | None
    live_deadline_at: datetime | None
    backup_deadline_at: datetime | None
    overdue: tuple[str, ...]
    transitions: tuple[TransitionView, ...]
    phases: tuple[PhaseView, ...]
    receipts: tuple[dict[str, Any], ...]
    artifact: ArtifactView | None
    #: active_data_removed_backup_pending etc. -- phase-level summary.
    progress_code: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def scope_revision(scope: str, story_ids: Iterable[str]) -> str:
    """Opaque confirmation token over the scope's Story IDs (opaque IDs only,
    never content): a scope that changed since display is refused."""
    canonical = json.dumps([scope, sorted(story_ids)])
    return hashlib.sha256(canonical.encode()).hexdigest()[:32]


class RequestStore:
    """Persistence and transitions of requests in the operations store."""

    def __init__(
        self,
        ops: sessionmaker[Session],
        *,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self._ops = ops
        self._now = now

    # -- creation ----------------------------------------------------------

    def create(
        self,
        actor: RequestActor,
        *,
        kind: RequestKind,
        scope: RequestScope,
        story_refs: list[str],
    ) -> str:
        """Persist a new request, refusing a duplicate open request for the
        same subject/kind/scope/Story (409 with that request's ID)."""
        assert actor.subject_ref is not None
        now = self._now()
        request_id = str(uuid4())
        with self._locked() as s:
            for row in s.scalars(
                sa.select(DataRequestORM).where(
                    DataRequestORM.subject_ref == actor.subject_ref,
                    DataRequestORM.kind == kind.value,
                    DataRequestORM.scope == scope.value,
                    DataRequestORM.environment == actor.environment,
                )
            ):
                if (
                    json.loads(row.story_refs) == story_refs
                    and self._state(s, row.request_id) in OPEN_STATES
                ):
                    raise OperationError(
                        OperationErrorKind.CONFLICT,
                        f"An open request already exists: {row.request_id}",
                    )
            s.add(
                DataRequestORM(
                    request_id=request_id,
                    schema_version=1,
                    kind=kind.value,
                    environment=actor.environment,
                    scope=scope.value,
                    subject_ref=actor.subject_ref,
                    story_refs=json.dumps(story_refs),
                    requester_ref=actor.actor_ref,
                    requested_at=iso(now),
                    verified_at=iso(now),
                    policy_version=POLICY_VERSION,
                    export_deadline_at=(
                        iso(now + EXPORT_PRODUCTION)
                        if kind is RequestKind.EXPORT
                        else None
                    ),
                )
            )
            s.flush()
            initial = (
                RequestState.AWAITING_AUTHORIZATION
                if kind is RequestKind.EXPORT
                else RequestState.REQUESTED
            )
            self._add_event(
                s,
                request_id,
                revision=1,
                state=initial,
                actor=actor,
                authorization_code="owner_verified_session",
            )
        return request_id

    # -- transitions -------------------------------------------------------

    def confirm(
        self,
        actor: RequestActor,
        request_id: str,
        *,
        expected_revision: int,
        confirmed_scope_revision: str,
        current_scope_revision: str,
        issue_credential: bool,
    ) -> str | None:
        """Explicit scope confirmation by the requester: starts the deletion
        clocks. Returns a one-time post-closure receipt credential when asked
        (account deletion); only its verifier is stored."""
        now = self._now()
        credential = new_token() if issue_credential else None
        with self._locked() as s:
            header = self._header(s, request_id)
            if header.kind != RequestKind.DELETION.value:
                raise OperationError(
                    OperationErrorKind.CONFLICT, "Only deletion requests are confirmed."
                )
            self._expect(s, request_id, expected_revision, {RequestState.REQUESTED})
            if confirmed_scope_revision != current_scope_revision:
                raise OperationError(
                    OperationErrorKind.STALE,
                    "The deletion scope changed since it was displayed; review it "
                    "again.",
                )
            self._add_event(
                s,
                request_id,
                revision=expected_revision + 1,
                state=RequestState.AWAITING_AUTHORIZATION,
                actor=actor,
                authorization_code="scope_confirmed",
                confirmation_ref=str(uuid4()),
                scope_revision=current_scope_revision,
                confirmed_at=now,
                live_deadline_at=now + LIVE_DELETION,
                backup_deadline_at=now + DELETION_BACKUP_DEADLINE,
            )
            if credential is not None:
                s.add(
                    ReceiptCredentialORM(
                        request_id=request_id,
                        credential_verifier=token_verifier(credential),
                        issued_at=iso(now),
                    )
                )
        return credential

    def approve(
        self,
        actor: RequestActor,
        request_id: str,
        *,
        expected_revision: int,
        reason: str | None,
    ) -> None:
        with self._locked() as s:
            self._expect(
                s, request_id, expected_revision, {RequestState.AWAITING_AUTHORIZATION}
            )
            self._add_event(
                s,
                request_id,
                revision=expected_revision + 1,
                state=RequestState.APPROVED,
                actor=actor,
                authorization_code=(
                    "local_owner" if actor.environment == "local" else "administrator"
                ),
                reason_text=bounded_text(reason) if reason else None,
                approved_at=self._now(),
            )

    def reject(
        self,
        actor: RequestActor,
        request_id: str,
        *,
        expected_revision: int,
        reason_code: str,
        reason: str,
    ) -> None:
        if reason_code not in REJECTION_CODES:
            raise OperationError(
                OperationErrorKind.INVALID_INPUT, "Unsupported rejection reason code."
            )
        text = bounded_text(reason)
        with self._locked() as s:
            self._expect(
                s,
                request_id,
                expected_revision,
                {
                    RequestState.REQUESTED,
                    RequestState.AWAITING_AUTHORIZATION,
                    RequestState.APPROVED,
                },
            )
            self._add_event(
                s,
                request_id,
                revision=expected_revision + 1,
                state=RequestState.REJECTED,
                actor=actor,
                reason_code=reason_code,
                reason_text=text,
                closed_at=self._now(),
            )

    def begin_attempt(
        self, actor: RequestActor, request_id: str, *, expected_revision: int
    ) -> str:
        """``approved`` or ``failed`` (retry) or an interrupted ``in_progress``
        (resume after restart) -> a new attempt in progress."""
        attempt = str(uuid4())
        with self._locked() as s:
            self._expect(
                s,
                request_id,
                expected_revision,
                {RequestState.APPROVED, RequestState.FAILED, RequestState.IN_PROGRESS},
            )
            self._add_event(
                s,
                request_id,
                revision=expected_revision + 1,
                state=RequestState.IN_PROGRESS,
                actor=actor,
                attempt_id=attempt,
            )
        return attempt

    def end_attempt(
        self,
        request_id: str,
        attempt_id: str,
        state: RequestState,
        *,
        reason_code: str | None = None,
    ) -> None:
        """Record an executor's verified outcome for its own attempt."""
        assert state in (
            RequestState.COMPLETED,
            RequestState.FAILED,
            RequestState.IN_PROGRESS,
        )
        actor = RequestActor("system", "lifecycle_executor", "system")
        with self._locked() as s:
            revision, current, attempt = self._current(s, request_id)
            if current is not RequestState.IN_PROGRESS or attempt != attempt_id:
                raise OperationError(
                    OperationErrorKind.CONFLICT, "The attempt is no longer current."
                )
            if state is RequestState.IN_PROGRESS and reason_code is None:
                return
            self._add_event(
                s,
                request_id,
                revision=revision + 1,
                state=state,
                actor=actor,
                attempt_id=attempt_id,
                reason_code=reason_code,
                closed_at=self._now() if state is RequestState.COMPLETED else None,
            )

    # -- phases, receipts, artifacts ----------------------------------------

    def record_phase(
        self,
        request_id: str,
        attempt_id: str,
        phase_code: str,
        outcome_code: str,
        *,
        counts: dict[str, int] | None = None,
        detail_code: str | None = None,
        deadline_at: datetime | None = None,
    ) -> None:
        with self._ops.begin() as s:
            s.add(
                PhaseEventORM(
                    event_id=str(uuid4()),
                    request_id=request_id,
                    attempt_id=attempt_id,
                    phase_code=phase_code,
                    outcome_code=outcome_code,
                    counts_json=json.dumps(counts or {}, sort_keys=True),
                    detail_code=detail_code,
                    observed_at=iso(self._now()),
                    deadline_at=iso(deadline_at) if deadline_at else None,
                )
            )

    def add_receipt(
        self, request_id: str, attempt_id: str, kind: str, body: dict[str, Any]
    ) -> str:
        receipt_id = str(uuid4())
        with self._ops.begin() as s:
            s.add(
                ReceiptORM(
                    receipt_id=receipt_id,
                    request_id=request_id,
                    receipt_kind=kind,
                    schema_version=1,
                    attempt_id=attempt_id,
                    body_json=json.dumps(body, sort_keys=True),
                    created_at=iso(self._now()),
                    policy_version=POLICY_VERSION,
                )
            )
        return receipt_id

    # -- reads -------------------------------------------------------------

    def header(self, request_id: str) -> DataRequestORM:
        with self._ops() as s:
            row = self._header(s, request_id)
            s.expunge(row)
            return row

    def state_of(self, request_id: str) -> tuple[int, RequestState, str | None]:
        with self._ops() as s:
            return self._current(s, request_id)

    def request_ids(
        self,
        *,
        subject_ref: str | None = None,
        environment: str | None = None,
    ) -> list[str]:
        with self._ops() as s:
            query = sa.select(DataRequestORM.request_id).order_by(
                DataRequestORM.requested_at, DataRequestORM.request_id
            )
            if subject_ref is not None:
                query = query.where(DataRequestORM.subject_ref == subject_ref)
            if environment is not None:
                query = query.where(DataRequestORM.environment == environment)
            return list(s.scalars(query))

    def credential_matches(self, request_id: str, credential: str) -> bool:
        with self._ops() as s:
            row = s.get(ReceiptCredentialORM, request_id)
            return row is not None and row.credential_verifier == token_verifier(
                credential
            )

    def view(self, request_id: str) -> RequestView:
        now = self._now()
        with self._ops() as s:
            header = self._header(s, request_id)
            events = list(
                s.scalars(
                    sa.select(DataRequestEventORM)
                    .where(DataRequestEventORM.request_id == request_id)
                    .order_by(DataRequestEventORM.event_order)
                )
            )
            phase_rows = list(
                s.scalars(
                    sa.select(PhaseEventORM)
                    .where(PhaseEventORM.request_id == request_id)
                    .order_by(PhaseEventORM.event_order)
                )
            )
            receipts = [
                {
                    "receipt_id": r.receipt_id,
                    "receipt_kind": r.receipt_kind,
                    "attempt_id": r.attempt_id,
                    "created_at": r.created_at,
                    "body": json.loads(r.body_json),
                }
                for r in s.scalars(
                    sa.select(ReceiptORM)
                    .where(ReceiptORM.request_id == request_id)
                    .order_by(ReceiptORM.created_at, ReceiptORM.receipt_id)
                )
            ]
            artifact_row = s.scalars(
                sa.select(ExportArtifactORM)
                .where(ExportArtifactORM.request_id == request_id)
                .order_by(ExportArtifactORM.created_at.desc())
            ).first()
        last = events[-1]

        def first(name: str) -> datetime | None:
            for e in events:
                value = getattr(e, name)
                if value:
                    return parse_iso(value)
            return None

        latest: dict[str, PhaseEventORM] = {}
        for row in phase_rows:
            latest[row.phase_code] = row
        phases = tuple(
            PhaseView(
                phase_code=row.phase_code,
                outcome_code=row.outcome_code,
                attempt_id=row.attempt_id,
                counts=json.loads(row.counts_json),
                detail_code=row.detail_code,
                observed_at=parse_iso(row.observed_at),
                deadline_at=parse_iso(row.deadline_at) if row.deadline_at else None,
            )
            for row in latest.values()
        )
        state = RequestState(last.state)
        export_deadline = (
            parse_iso(header.export_deadline_at) if header.export_deadline_at else None
        )
        live_deadline = first("live_deadline_at")
        backup_deadline = first("backup_deadline_at")
        overdue: list[str] = []
        if state not in CLOSED_STATES:
            if (
                export_deadline
                and is_overdue(export_deadline, now)
                and not _artifact_available(artifact_row)
            ):
                overdue.append("export_production")
            if (
                live_deadline
                and is_overdue(live_deadline, now)
                and not _live_done(phases)
            ):
                overdue.append("live_deletion")
            if backup_deadline and is_overdue(backup_deadline, now):
                overdue.append("final_deletion")
        return RequestView(
            request_id=header.request_id,
            kind=header.kind,
            environment=header.environment,
            scope=header.scope,
            subject_ref=header.subject_ref,
            story_refs=tuple(json.loads(header.story_refs)),
            requester_ref=header.requester_ref,
            requested_at=parse_iso(header.requested_at),
            verified_at=parse_iso(header.verified_at),
            policy_version=header.policy_version,
            state=state.value,
            revision=last.revision,
            confirmed_at=first("confirmed_at"),
            approved_at=first("approved_at"),
            closed_at=parse_iso(last.closed_at) if last.closed_at else None,
            export_deadline_at=export_deadline,
            live_deadline_at=live_deadline,
            backup_deadline_at=backup_deadline,
            overdue=tuple(overdue),
            transitions=tuple(
                TransitionView(
                    event_id=e.event_id,
                    event_order=e.event_order,
                    revision=e.revision,
                    state=e.state,
                    attempt_id=e.attempt_id,
                    actor_ref=e.actor_ref,
                    authorization_code=e.authorization_code,
                    reason_code=e.reason_code,
                    reason_text=e.reason_text,
                    recorded_at=parse_iso(e.recorded_at),
                )
                for e in events
            ),
            phases=phases,
            receipts=tuple(receipts),
            artifact=(
                ArtifactView(
                    artifact_id=artifact_row.artifact_id,
                    status=artifact_row.status,
                    available_at=(
                        parse_iso(artifact_row.available_at)
                        if artifact_row.available_at
                        else None
                    ),
                    expires_at=parse_iso(artifact_row.expires_at),
                    removed_at=(
                        parse_iso(artifact_row.removed_at)
                        if artifact_row.removed_at
                        else None
                    ),
                    size_bytes=artifact_row.size_bytes,
                )
                if artifact_row is not None
                else None
            ),
            progress_code=_progress(header.kind, state, phases),
        )

    # -- internals ---------------------------------------------------------

    @staticmethod
    def _header(s: Session, request_id: str) -> DataRequestORM:
        row = s.get(DataRequestORM, request_id)
        if row is None:
            raise OperationError(OperationErrorKind.NOT_FOUND, "Request not found.")
        return row

    @staticmethod
    def _current(s: Session, request_id: str) -> tuple[int, RequestState, str | None]:
        last = s.scalars(
            sa.select(DataRequestEventORM)
            .where(DataRequestEventORM.request_id == request_id)
            .order_by(DataRequestEventORM.revision.desc())
        ).first()
        if last is None:
            raise OperationError(OperationErrorKind.NOT_FOUND, "Request not found.")
        attempt = s.scalars(
            sa.select(DataRequestEventORM.attempt_id)
            .where(
                DataRequestEventORM.request_id == request_id,
                DataRequestEventORM.attempt_id.is_not(None),
            )
            .order_by(DataRequestEventORM.revision.desc())
        ).first()
        return last.revision, RequestState(last.state), attempt

    def _state(self, s: Session, request_id: str) -> RequestState:
        return self._current(s, request_id)[1]

    def _expect(
        self,
        s: Session,
        request_id: str,
        expected_revision: int,
        allowed: set[RequestState],
    ) -> None:
        self._header(s, request_id)
        revision, state, _ = self._current(s, request_id)
        if revision != expected_revision:
            raise OperationError(
                OperationErrorKind.STALE,
                f"The request is at revision {revision}, not {expected_revision}.",
            )
        if state not in allowed:
            raise OperationError(
                OperationErrorKind.CONFLICT,
                f"This step is not allowed while the request is {state.value}.",
            )

    def _add_event(
        self,
        s: Session,
        request_id: str,
        *,
        revision: int,
        state: RequestState,
        actor: RequestActor,
        attempt_id: str | None = None,
        authorization_code: str | None = None,
        confirmation_ref: str | None = None,
        scope_revision: str | None = None,
        reason_code: str | None = None,
        reason_text: str | None = None,
        confirmed_at: datetime | None = None,
        approved_at: datetime | None = None,
        closed_at: datetime | None = None,
        live_deadline_at: datetime | None = None,
        backup_deadline_at: datetime | None = None,
    ) -> None:
        s.add(
            DataRequestEventORM(
                event_id=str(uuid4()),
                schema_version=1,
                request_id=request_id,
                revision=revision,
                state=state.value,
                attempt_id=attempt_id,
                actor_ref=actor.actor_ref,
                authorization_code=authorization_code,
                confirmation_ref=confirmation_ref,
                scope_revision=scope_revision,
                reason_code=reason_code,
                reason_text=reason_text,
                recorded_at=iso(self._now()),
                confirmed_at=iso(confirmed_at) if confirmed_at else None,
                approved_at=iso(approved_at) if approved_at else None,
                closed_at=iso(closed_at) if closed_at else None,
                live_deadline_at=iso(live_deadline_at) if live_deadline_at else None,
                backup_deadline_at=(
                    iso(backup_deadline_at) if backup_deadline_at else None
                ),
                policy_version=POLICY_VERSION,
            )
        )

    def _locked(self) -> Any:
        return _locked(self._ops)


class _LockedSession:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory

    def __enter__(self) -> Session:
        self._session = self._factory()
        self._session.connection().exec_driver_sql("BEGIN IMMEDIATE")
        return self._session

    def __exit__(self, exc_type: Any, *_: Any) -> None:
        try:
            if exc_type is None:
                self._session.commit()
            else:
                self._session.rollback()
        finally:
            self._session.close()


def _locked(factory: sessionmaker[Session]) -> _LockedSession:
    """A transaction holding SQLite's write lock from its first read, so a
    revision check and the transition it guards cannot interleave."""
    return _LockedSession(factory)


def _artifact_available(row: ExportArtifactORM | None) -> bool:
    return row is not None and row.available_at is not None


LIVE_PHASES = ("vector_logical", "sql_content")


def _live_done(phases: tuple[PhaseView, ...]) -> bool:
    outcomes = {p.phase_code: p.outcome_code for p in phases}
    return all(outcomes.get(code) == "succeeded" for code in LIVE_PHASES)


def _progress(
    kind: str, state: RequestState, phases: tuple[PhaseView, ...]
) -> str | None:
    if kind != RequestKind.DELETION.value or state is not RequestState.IN_PROGRESS:
        return None
    outcomes = {p.phase_code: p.outcome_code for p in phases}
    if not _live_done(phases):
        return "active_deletion_in_progress"
    pending = sorted(
        code
        for code, outcome in outcomes.items()
        if outcome in ("pending", "dependency_unavailable", "unverified")
    )
    return "active_data_removed_" + (
        "_".join(pending) + "_pending" if pending else "finalizing"
    )


class AttemptRegistry:
    """Process-local guard: one running attempt per request (the single
    writer process, ADR-021 D6)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running: set[str] = set()

    def claim(self, request_id: str) -> bool:
        with self._lock:
            if request_id in self._running:
                return False
            self._running.add(request_id)
            return True

    def release(self, request_id: str) -> None:
        with self._lock:
            self._running.discard(request_id)
