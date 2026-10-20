"""Data-request service -- the CRD Issue 22 §4-§6 entry point for the API.

Binds every request to the trusted actor (never a submitted ID): a remote
Sojourner's subject is their authenticated account, a local request's is the
local owner, and the Owner administrator acts only through a staff session.
A request the caller does not own is the same ``not_found`` as a missing one.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.operations.deletion import (
    DeletionContext,
    current_scope_story_ids,
    current_scope_story_ids_in,
    deletion_preview,
    evaluate,
    run_deletion,
)
from afterworlds.operations.errors import OperationError, OperationErrorKind
from afterworlds.operations.export import (
    ExportInputs,
    NothingToExport,
    build_archive,
    produce_artifact,
)
from afterworlds.operations.orm import (
    DataRequestEventORM,
    ExportArtifactORM,
    SupportActionEventORM,
)
from afterworlds.operations.policy import is_expired
from afterworlds.operations.requests import (
    AttemptRegistry,
    RequestActor,
    RequestKind,
    RequestScope,
    RequestState,
    RequestStore,
    RequestView,
    scope_revision,
)
from afterworlds.operations.support import SupportService
from afterworlds.persistence.crud.story import get_story
from afterworlds.remote.access import AccessPolicy, story_owner
from afterworlds.remote.control_orm import HostedAccountORM, IdentityPrincipalORM
from afterworlds.remote.control_store import parse_iso, utc_now
from afterworlds.remote.fence import AccountFence, FenceBusy
from afterworlds.remote.identity import Actor, ActorKind, IdentityService
from afterworlds.remote.storage import is_suppressed


def _not_found() -> OperationError:
    return OperationError(OperationErrorKind.NOT_FOUND, "Request not found.")


class DataRequestService:
    def __init__(
        self,
        *,
        ops: sessionmaker[Session],
        content: sessionmaker[Session],
        environment: str,
        policy: AccessPolicy,
        delete_story_chunks: Callable[[str], int],
        export_dir: Path,
        identity: IdentityService | None = None,
        fence: AccountFence | None = None,
        support: SupportService | None = None,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self.store = RequestStore(ops, now=now)
        self._ops = ops
        self._content = content
        self._environment = environment
        self._policy = policy
        self._identity = identity
        self._support = support
        self._export_dir = export_dir
        self._now = now
        self._attempts = AttemptRegistry()
        self._local_lock = threading.Lock()
        self.deletion = DeletionContext(
            store=self.store,
            ops=ops,
            content=content,
            environment=environment,
            delete_story_chunks=delete_story_chunks,
            now=now,
            identity=identity,
            fence=fence,
            control=ops if environment == "remote" else None,
            export_dir=export_dir,
        )

    # -- actors ------------------------------------------------------------

    def _requester(self, actor: Actor) -> RequestActor:
        if actor.kind is ActorKind.LOCAL and self._environment == "local":
            return RequestActor(
                "requester", "local_owner", "local", str(actor.account_id)
            )
        if actor.kind is ActorKind.SOJOURNER and self._environment == "remote":
            assert actor.principal_ref is not None
            return RequestActor(
                "requester", actor.principal_ref, "remote", str(actor.account_id)
            )
        raise OperationError(
            OperationErrorKind.UNSUPPORTED, "This session cannot make data requests."
        )

    def _administrator(self, actor: Actor) -> RequestActor:
        if actor.kind is not ActorKind.STAFF or self._identity is None:
            raise OperationError(
                OperationErrorKind.UNSUPPORTED, "Staff authority is required."
            )
        if not self._identity.actor_is_current(actor):
            raise OperationError(
                OperationErrorKind.PRECONDITION_FAILED, "staff_session_not_current"
            )
        assert actor.principal_ref is not None
        return RequestActor("administrator", actor.principal_ref, "remote")

    def _owned(self, actor: Actor, request_id: str) -> RequestView:
        requester = self._requester(actor)
        try:
            view = self.store.view(request_id)
        except OperationError:
            raise _not_found() from None
        if (
            view.subject_ref != requester.subject_ref
            or view.environment != requester.environment
        ):
            raise _not_found()
        return view

    # -- requester paths ---------------------------------------------------

    def create(
        self,
        actor: Actor,
        kind: RequestKind,
        scope: RequestScope,
        story_id: UUID | None,
    ) -> RequestView:
        requester = self._requester(actor)
        if (scope is RequestScope.STORY) != (story_id is not None):
            raise OperationError(
                OperationErrorKind.INVALID_INPUT,
                "A Story request names one Story; an account request names none.",
            )
        refs: list[str] = []
        if story_id is not None:
            with self._content() as s:
                allowed = (
                    self._policy.actor_may_access(s, actor, story_id)
                    if self._policy.remote
                    else get_story(s, story_id) is not None
                )
            if not allowed:
                raise OperationError(OperationErrorKind.NOT_FOUND, "Story not found.")
            refs = [str(story_id)]
        request_id = self.store.create(
            requester, kind=kind, scope=scope, story_refs=refs
        )
        return self.store.view(request_id)

    def list_own(self, actor: Actor) -> list[RequestView]:
        requester = self._requester(actor)
        return [
            self.store.view(rid)
            for rid in self.store.request_ids(
                subject_ref=requester.subject_ref, environment=requester.environment
            )
        ]

    def get_own(self, actor: Actor, request_id: str) -> RequestView:
        return self._owned(actor, request_id)

    def preview(self, actor: Actor, request_id: str) -> dict[str, Any]:
        view = self._owned(actor, request_id)
        if view.kind != RequestKind.DELETION.value:
            raise OperationError(
                OperationErrorKind.CONFLICT, "Only deletion requests have a preview."
            )
        return deletion_preview(self.deletion, view, self._scope_ids(view))

    def confirm(
        self,
        actor: Actor,
        request_id: str,
        *,
        expected_revision: int,
        confirmed_scope_revision: str,
        password: str | None,
    ) -> tuple[RequestView, str | None]:
        view = self._owned(actor, request_id)
        requester = self._requester(actor)
        account_remote = view.scope == "account" and self._environment == "remote"
        if account_remote:
            assert self._identity is not None
            if not password or not self._identity.reauthenticate(actor, password):
                raise OperationError(
                    OperationErrorKind.PRECONDITION_FAILED,
                    "Password re-authentication is required to confirm account "
                    "deletion.",
                )
        credential = self.store.confirm(
            requester,
            request_id,
            expected_revision=expected_revision,
            confirmed_scope_revision=confirmed_scope_revision,
            current_scope_revision=scope_revision(view.scope, self._scope_ids(view)),
            issue_credential=account_remote,
        )
        return self.store.view(request_id), credential

    def execute_local(
        self, actor: Actor, request_id: str, *, expected_revision: int
    ) -> RequestView:
        """The local owner authorizes and executes their own request: two
        recorded steps, no cloud account."""
        view = self._owned(actor, request_id)
        if self._environment != "local":
            raise OperationError(
                OperationErrorKind.UNSUPPORTED,
                "Remote requests are executed by the administrator.",
            )
        requester = self._requester(actor)
        if view.kind != RequestKind.DELETION.value:
            return self._authorize_and_run(requester, view, expected_revision)
        # A local deletion holds the local owner's fence exclusive for its
        # whole run: in-flight turns and Story creation finish first, and none
        # is admitted until the final scope is removed (review round 2, F1).
        assert self.deletion.fence is not None
        try:
            with self.deletion.fence.exclusive(
                UUID(actor.account_id.hex), timeout=30.0
            ):
                return self._authorize_and_run(requester, view, expected_revision)
        except FenceBusy:
            raise OperationError(
                OperationErrorKind.IN_PROGRESS,
                "Other work is still running; try again shortly.",
            ) from None

    def _authorize_and_run(
        self, requester: RequestActor, view: RequestView, expected_revision: int
    ) -> RequestView:
        revision = expected_revision
        if view.state == RequestState.AWAITING_AUTHORIZATION.value:
            self.store.approve(
                requester, view.request_id, expected_revision=revision, reason=None
            )
            revision += 1
        return self._run(requester, view.request_id, revision)

    def artifact_path(self, actor: Actor, request_id: str) -> tuple[Path, str]:
        """The owner's available artifact file and its ID (to mark delivery
        once the whole body was sent)."""
        view = self._owned(actor, request_id)
        artifact = view.artifact
        if (
            artifact is None
            or artifact.status != "available"
            or artifact.removed_at is not None
            or is_expired(artifact.expires_at, self._now())
        ):
            raise OperationError(
                OperationErrorKind.NOT_FOUND, "No export is available for download."
            )
        if self._policy.remote and self._carries_suppressed(view):
            # Its Stories are being deleted: the artifact is about to be
            # removed by that deletion and is no longer served.
            raise OperationError(
                OperationErrorKind.NOT_FOUND, "No export is available for download."
            )
        with self._ops() as s:
            row = s.get(ExportArtifactORM, artifact.artifact_id)
            assert row is not None
            path = Path(row.storage_locator)
        if not path.is_file():
            raise OperationError(
                OperationErrorKind.UNAVAILABLE, "The export file is unavailable."
            )
        return path, artifact.artifact_id

    def _carries_suppressed(self, view: RequestView) -> bool:
        manifest: dict[str, Any] = next(
            (
                r["body"]
                for r in view.receipts
                if r["receipt_kind"] == "export_manifest"
            ),
            {},
        )
        stories = set(view.story_refs) | set(
            manifest.get("snapshot_boundary", {}).get("stories", {})
        )
        assert self.deletion.control is not None
        return any(
            is_suppressed(
                self.deletion.control, story_id=story, account_id=view.subject_ref
            )
            for story in stories
        )

    def mark_delivered(self, artifact_id: str) -> None:
        """Called after a download response's body was fully sent."""
        self.store.mark_delivered(artifact_id)

    def reissue_credential(
        self, actor: Actor, request_id: str, password: str
    ) -> tuple[RequestView, str]:
        """Replace a lost receipt credential before closure: the owner's
        current session plus password re-authentication. Confirmation time
        and deadlines are unchanged; the old credential stops working."""
        view = self._owned(actor, request_id)
        if self._identity is None or view.scope != "account" or view.kind != "deletion":
            raise OperationError(
                OperationErrorKind.UNSUPPORTED,
                "Only remote account deletions have a receipt credential.",
            )
        if not self._identity.reauthenticate(actor, password):
            raise OperationError(
                OperationErrorKind.PRECONDITION_FAILED,
                "Password re-authentication is required to reissue the credential.",
            )
        credential = self.store.reissue_credential(request_id)
        return self.store.view(request_id), credential

    def receipt(self, request_id: str, credential: str) -> RequestView:
        """Post-closure status/receipt: only with the credential issued at
        confirmation. Every mismatch is the same not_found."""
        try:
            UUID(request_id)
            ok = self.store.credential_matches(request_id, credential)
        except (ValueError, OperationError):
            ok = False
        if not ok:
            raise _not_found()
        return self.store.view(request_id)

    # -- administrator paths -----------------------------------------------

    def list_all(self) -> list[RequestView]:
        return [self.store.view(rid) for rid in self.store.request_ids()]

    def get(self, request_id: str) -> RequestView:
        return self.store.view(request_id)

    def approve(
        self,
        actor: Actor,
        request_id: str,
        *,
        expected_revision: int,
        reason: str | None,
    ) -> RequestView:
        admin = self._administrator(actor)
        self.store.approve(
            admin, request_id, expected_revision=expected_revision, reason=reason
        )
        return self.store.view(request_id)

    def reject(
        self,
        actor: Actor,
        request_id: str,
        *,
        expected_revision: int,
        reason_code: str,
        reason: str,
    ) -> RequestView:
        admin = self._administrator(actor)
        self.store.reject(
            admin,
            request_id,
            expected_revision=expected_revision,
            reason_code=reason_code,
            reason=reason,
        )
        return self.store.view(request_id)

    def execute(
        self, actor: Actor, request_id: str, *, expected_revision: int
    ) -> RequestView:
        return self._run(self._administrator(actor), request_id, expected_revision)

    def finalize(self, actor: Actor | None, request_id: str) -> RequestView:
        """Re-check a deletion's pending physical/backup phases (administrator
        or maintenance); completes only when every postcondition holds."""
        if actor is not None:
            self._administrator(actor)
        view = self.store.view(request_id)
        _, state, attempt = self.store.state_of(request_id)
        if (
            view.kind != RequestKind.DELETION.value
            or state is not RequestState.IN_PROGRESS
            or attempt is None
            or not self._attempts.claim(request_id)
        ):
            raise OperationError(
                OperationErrorKind.CONFLICT, "Nothing is pending finalization."
            )
        try:
            evaluate(self.deletion, request_id, attempt)
        finally:
            self._attempts.release(request_id)
        return self.store.view(request_id)

    # -- execution ---------------------------------------------------------

    def _scope_ids(self, view: RequestView) -> list[str]:
        return current_scope_story_ids(
            self._content, self.store.header(view.request_id), self._environment
        )

    def _run(
        self, actor: RequestActor, request_id: str, expected_revision: int
    ) -> RequestView:
        if not self._attempts.claim(request_id):
            raise OperationError(
                OperationErrorKind.IN_PROGRESS, "This request is already running."
            )
        # Locally no account fence exists: one fulfillment runs at a time, so
        # an export never snapshots or publishes beside a deletion.
        serial = self._local_lock if self._environment == "local" else nullcontext()
        try:
            with serial:
                attempt = self.store.begin_attempt(
                    actor, request_id, expected_revision=expected_revision
                )
                view = self.store.view(request_id)
                if view.kind == RequestKind.EXPORT.value:
                    self._run_export(view, attempt)
                else:
                    run_deletion(self.deletion, view, attempt)
        finally:
            self._attempts.release(request_id)
        return self.store.view(request_id)

    def _run_export(self, view: RequestView, attempt: str) -> None:
        """Snapshot and publish under the account fence (remote), so a
        deletion's suppression waits for an export in flight and no export
        admitted later can include a suppressed Story or publish after the
        deletion removed its artifacts (CRD Issue 22 review P1-2)."""
        fence = self.deletion.fence
        try:
            if fence is None:
                self._export_attempt(view, attempt)
                return
            with fence.held(UUID(view.subject_ref)):
                self._export_attempt(view, attempt)
        except FenceBusy:
            self._fail_export(view, attempt, "account_operation_in_progress")

    def _fail_export(self, view: RequestView, attempt: str, code: str) -> None:
        self.store.record_phase(
            view.request_id, attempt, "artifact", "failed", detail_code=code
        )
        self.store.end_attempt(
            view.request_id, attempt, RequestState.FAILED, reason_code=code
        )

    def _export_attempt(self, view: RequestView, attempt: str) -> None:
        if self._policy.remote and self._account_suppressed(view.subject_ref):
            self._fail_export(view, attempt, "account_under_deletion")
            return
        header = self.store.header(view.request_id)

        def select_stories(session: Session) -> tuple[list[str], int]:
            # Inside the content snapshot (PR #208 review): membership and
            # contents share one boundary.
            candidates = current_scope_story_ids_in(session, header, self._environment)
            stories = [
                sid
                for sid in candidates
                if self._story_exportable_in(session, view, sid)
            ]
            return stories, len(candidates) - len(stories)

        inputs = ExportInputs(
            request_id=view.request_id,
            scope=view.scope,
            environment=view.environment,
            subject_ref=view.subject_ref,
            policy_version=view.policy_version,
            select_stories=select_stories,
            read_operational=(
                (lambda session: self._operational_snapshot(view, session))
                if view.scope == "account"
                else None
            ),
        )
        try:
            _, manifest = produce_artifact(
                self._ops,
                self._export_dir,
                request_id=view.request_id,
                attempt_id=attempt,
                build=lambda: build_archive(self._content, inputs, now=self._now()),
                now=self._now,
            )
        except NothingToExport:
            self._fail_export(view, attempt, "story_unavailable")
            return
        except Exception:  # noqa: BLE001 -- typed below; no partial file remains
            self._fail_export(view, attempt, "generation_failed")
            return
        self.store.record_phase(
            view.request_id, attempt, "artifact", "succeeded", counts=manifest["counts"]
        )
        self.store.add_receipt(view.request_id, attempt, "export_manifest", manifest)
        self.store.end_attempt(view.request_id, attempt, RequestState.COMPLETED)

    def _account_suppressed(self, account_id: str) -> bool:
        return self._policy.account_suppressed(UUID(account_id))

    def _story_exportable_in(
        self, s: Session, view: RequestView, story_id: str
    ) -> bool:
        """Owned by the subject, present, and under no deletion suppression,
        read in the export's content snapshot. (Suppressions cannot change
        while the export holds the account fence.)"""
        if get_story(s, UUID(story_id)) is None:
            return False
        if not self._policy.remote:
            return True
        if story_owner(s, UUID(story_id)) != view.subject_ref:
            return False
        assert self.deletion.control is not None
        return not is_suppressed(
            self.deletion.control, story_id=story_id, account_id=view.subject_ref
        )

    def _operational_snapshot(
        self, view: RequestView, content_session: Session
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        """The account/profile view and own operational records, each store
        read in one transaction taken after the content snapshot was fixed.

        Locally the operations store is the content store: the records are
        read in the content snapshot itself. Remotely they come from one
        control-store transaction (account/profile, request membership and
        views, support history), which starts after the content snapshot --
        so a support action whose effect is in the exported ledger is always
        present, and its record may be later than that ledger's boundary.
        Returns (account view, operational records, read boundary)."""
        if not self._policy.remote:
            account = {"account": "local_owner", "subject_ref": view.subject_ref}
            records = self._operational_records(view, content_session)
            return (
                account,
                records,
                {
                    "store": "content",
                    "read": "same_transaction_as_content",
                },
            )
        with self._ops() as s:
            s.connection().exec_driver_sql("BEGIN")
            account = self._account_record(view, s)
            records = self._operational_records(view, s)
            boundary = {
                "store": "control",
                "read": "single_transaction",
                "taken": "after_content_snapshot",
                "data_request_event_through_order": s.scalar(
                    sa.select(sa.func.max(DataRequestEventORM.event_order))
                ),
                "support_event_through_order": s.scalar(
                    sa.select(sa.func.max(SupportActionEventORM.event_order))
                ),
            }
            s.rollback()
        return account, records, boundary

    def _account_record(self, view: RequestView, s: Session) -> dict[str, Any]:
        row = s.get(HostedAccountORM, view.subject_ref)
        principal = s.scalar(
            sa.select(IdentityPrincipalORM).where(
                IdentityPrincipalORM.account_id == view.subject_ref
            )
        )
        return {
            "account_id": view.subject_ref,
            "status": row.status if row else None,
            "created_at": (parse_iso(row.created_at).isoformat() if row else None),
            "contact_address": principal.contact_address if principal else None,
            "collected_profile_fields": ["contact_address"],
        }

    def _operational_records(self, view: RequestView, s: Session) -> dict[str, Any]:
        requests = [
            {
                "request_id": r.request_id,
                "kind": r.kind,
                "scope": r.scope,
                "state": r.state,
                "requested_at": r.requested_at.isoformat(),
                "closed_at": r.closed_at.isoformat() if r.closed_at else None,
            }
            for r in (
                self.store.view_in(s, rid)
                for rid in RequestStore.request_ids_in(
                    s, subject_ref=view.subject_ref, environment=view.environment
                )
            )
        ]
        actions = []
        if self._support is not None:
            actions = [
                {
                    "operation_id": e.operation_id,
                    "action_code": e.action_code,
                    "actor": "administrator",
                    "outcome_code": e.outcome_code,
                    "hosted_credit_delta": e.hosted_credit_delta,
                    "top_up_credit_delta": e.top_up_credit_delta,
                    "reason_text": e.reason_text,
                    "recorded_at": e.recorded_at.isoformat(),
                }
                for e in SupportService.history_in(s, UUID(view.subject_ref))
            ]
        return {"data_requests": requests, "support_actions": actions}
