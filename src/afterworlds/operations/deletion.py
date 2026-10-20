"""Confirmed Story and account-wide deletion -- CRD Issue 22 §6.

Each attempt runs idempotent steps and records a phase event per store, so a
retry or a resumed attempt after restart completes only what remains and an
interrupted run never reads as complete:

1. ``inventory`` -- durable pre-detachment inventory (Story/Arc/Chapter/
   Node/Turn IDs, including Turns referenced only from Story-scoped rows),
   unioned across attempts, recorded before anything is detached;
2. ``fence`` -- remote: the deletion suppression, recorded through
   ``record_suppression_fenced`` with the *confirmation* time as its
   boundary (so the 30-day backup horizon runs from confirmation); it fences
   new work and is enforced on every restore;
3. ``vector_logical`` -- ADR-018 D11 per-Story delete and count-zero, before
   any ownership mapping is removed (an unavailable read fails);
4. ``sql_content`` -- registered owning-service disposal in one transaction,
   then an independent verification sweep;
5. ``identity`` -- account scope, remote: the identity owner closes the
   account, revokes sessions and removes profile/authentication data;
6. ``artifacts`` -- service-managed export artifacts carrying in-scope data;
7. ``rights_evidence``/``entitlement``/``commercial`` -- account scope:
   minimum BYOK-rights evidence, the retained minimized ledger, and the CRD
   Issue 23 commercial dependency (``dependency_unavailable`` while hosted
   subscription or Cloud Services references are live: no payment semantics
   are invented and the request cannot complete);
8. ``physical_compaction`` -- remote: pending until the offline compaction
   (``operations.compaction``) proves no live journal, free page or vector
   segment still carries the content; local: ``owner_controlled``;
9. ``backups`` -- remote: final completion only when every affected backup
   is disposed (#205 ``backup_disposition``); overdue is a failure.

This is terminal disposal of a Story that no longer exists, not gameplay
cancellation, rewind, reroll, refund or credit reversal.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.entitlement.inspection import read_projection
from afterworlds.entitlement.retention import record_rights_evidence_from_ledger
from afterworlds.operations.disposal import (
    dispose_story_content,
    referenced_turn_ids,
    remaining_story_content,
)
from afterworlds.operations.export import remove_artifact
from afterworlds.operations.orm import (
    DataRequestORM,
    ExportArtifactORM,
    PhaseEventORM,
    RequestInventoryORM,
)
from afterworlds.operations.policy import POLICY_VERSION
from afterworlds.operations.requests import RequestState, RequestStore, RequestView
from afterworlds.persistence.orm.node import NodeORM, TurnORM
from afterworlds.persistence.orm.ownership import AccountResourceORM
from afterworlds.persistence.orm.story import ArcORM, ChapterORM, StoryORM
from afterworlds.remote.control_orm import DeletionSuppressionORM
from afterworlds.remote.control_store import iso
from afterworlds.remote.fence import AccountFence, FenceBusy
from afterworlds.remote.identity import IdentityError, IdentityService
from afterworlds.remote.storage import backup_disposition

#: Phases that must succeed (or be not_applicable/owner_controlled) for
#: final completion.
FINAL_PHASES = (
    "inventory",
    "fence",
    "vector_logical",
    "sql_content",
    "identity",
    "artifacts",
    "rights_evidence",
    "commercial",
    "physical_compaction",
    "backups",
)
DONE = frozenset({"succeeded", "not_applicable", "owner_controlled"})

RETAINED_CATEGORIES: dict[str, tuple[dict[str, str], ...]] = {
    "story": (
        {
            "code": "data_request_receipt",
            "purpose": "Prove this request's authorization, execution and result.",
            "end_condition": "24 calendar months after the request closes.",
        },
        {
            "code": "deletion_suppression",
            "purpose": "Stop restores, replay or delayed work recreating the Story.",
            "end_condition": "Until every affected backup is disposed and no delayed "
            "event or job can recreate it; reviewed annually.",
        },
        {
            "code": "entitlement_history",
            "purpose": "Reconstruct the account's recorded credit/access effects "
            "(opaque Turn IDs only, no Turn text).",
            "end_condition": "While the account is active, then 24 calendar months "
            "after account closure.",
        },
        {
            "code": "content_free_logs",
            "purpose": "Routine operational diagnostics without content.",
            "end_condition": "30 days from recording.",
        },
    ),
    "account": (
        {
            "code": "data_request_receipt",
            "purpose": "Prove this request's authorization, execution and result.",
            "end_condition": "24 calendar months after the request closes.",
        },
        {
            "code": "administrator_action_receipts",
            "purpose": "Minimized record of administrator actions on the account.",
            "end_condition": "24 calendar months after each action closes.",
        },
        {
            "code": "entitlement_history",
            "purpose": "Reconstruct recorded credit/access effects.",
            "end_condition": "24 calendar months after account closure, unless a "
            "verified financial-record duty applies to specific fields.",
        },
        {
            "code": "byok_rights_evidence",
            "purpose": "Preserve any perpetual BYOK licence right.",
            "end_condition": "While the right is enforceable; reviewed annually.",
        },
        {
            "code": "account_tombstone",
            "purpose": "Closed account ID, status and closure time: prevents "
            "identifier reuse and anchors the 24-month clock.",
            "end_condition": "Removed with the last retained record that needs it.",
        },
        {
            "code": "deletion_suppression",
            "purpose": "Stop restores, replay or delayed work recreating the account "
            "or its content.",
            "end_condition": "Until every affected backup is disposed and no delayed "
            "event or job can recreate it; reviewed annually.",
        },
        {
            "code": "content_free_logs",
            "purpose": "Routine operational diagnostics without content.",
            "end_condition": "30 days from recording.",
        },
    ),
}

REMOVED_CLASSES: dict[str, tuple[str, ...]] = {
    "story": (
        "stories_arcs_chapters_nodes",
        "turns",
        "story_bible",
        "story_bible_history",
        "rolling_summaries",
        "session_setup_state",
        "character_sheets",
        "rpg_pending",
        "rpg_audit",
        "rpg_turn_state",
        "story_state",
        "retrieval_markers",
        "retrieval_chunks",
        "provider_refusal_rows",
        "ownership_mappings",
        "export_artifacts",
    ),
}
REMOVED_CLASSES["account"] = REMOVED_CLASSES["story"] + (
    "account_profile",
    "authentication_sessions_and_recovery",
)

RETAINED_CATEGORIES["local"] = tuple(
    c
    for c in RETAINED_CATEGORIES["story"]
    if c["code"] in ("data_request_receipt", "content_free_logs")
) + (
    {
        "code": "entitlement_history",
        "purpose": "Your licence and credit record on this device.",
        "end_condition": "Kept on this device; it is not account data.",
    },
)


def retained_for(scope: str, environment: str) -> tuple[dict[str, str], ...]:
    return RETAINED_CATEGORIES["local" if environment == "local" else scope]


def removed_for(scope: str, environment: str) -> tuple[str, ...]:
    return REMOVED_CLASSES["story" if environment == "local" else scope]


NOTICES = (
    "Files on your own device, local BYOK keys and exports you downloaded are "
    "not touched by remote deletion.",
    "Copies held by an AI provider outside Afterworlds' control are not covered.",
)


@dataclass
class DeletionContext:
    store: RequestStore
    ops: sessionmaker[Session]
    content: sessionmaker[Session]
    environment: str
    #: Delete a Story's chunks; returns the remaining count. Raises when the
    #: vector store cannot be read (never presumed zero).
    delete_story_chunks: Callable[[str], int]
    now: Callable[[], datetime]
    identity: IdentityService | None = None
    fence: AccountFence | None = None
    control: sessionmaker[Session] | None = None
    fence_timeout: float = 30.0
    export_dir: Path | None = None


# -- inventory -------------------------------------------------------------


def current_scope_story_ids(
    content: sessionmaker[Session], header: DataRequestORM, environment: str
) -> list[str]:
    """Stories the request covers right now (for display and confirmation)."""
    if header.scope == "story":
        return list(json.loads(header.story_refs))
    with content() as s:
        return current_scope_story_ids_in(s, header, environment)


def current_scope_story_ids_in(
    s: Session, header: DataRequestORM, environment: str
) -> list[str]:
    """:func:`current_scope_story_ids` read in the caller's session (an
    export selects its Stories inside its content snapshot)."""
    if header.scope == "story":
        return list(json.loads(header.story_refs))
    if environment == "remote":
        return sorted(
            s.scalars(
                sa.select(AccountResourceORM.resource_id).where(
                    AccountResourceORM.account_id == header.subject_ref,
                    AccountResourceORM.resource_type == "story",
                    AccountResourceORM.retired_at.is_(None),
                )
            )
        )
    return sorted(s.scalars(sa.select(StoryORM.story_id)))


def ensure_inventory(ctx: DeletionContext, view: RequestView) -> dict[str, list[str]]:
    """Record the inventory before detachment; later attempts union new
    findings (an account's every Story ever owned, retired mappings too)."""
    header = ctx.store.header(view.request_id)
    with ctx.content() as s:
        stories = set(json.loads(header.story_refs))
        if header.scope == "account":
            if ctx.environment == "remote":
                stories |= set(
                    s.scalars(
                        sa.select(AccountResourceORM.resource_id).where(
                            AccountResourceORM.account_id == header.subject_ref,
                            AccountResourceORM.resource_type == "story",
                        )
                    )
                )
            else:
                stories |= set(s.scalars(sa.select(StoryORM.story_id)))
        story_list = sorted(stories)
        arcs = set(
            s.scalars(sa.select(ArcORM.arc_id).where(ArcORM.story_id.in_(story_list)))
        )
        chapters = set(
            s.scalars(
                sa.select(ChapterORM.chapter_id).where(ChapterORM.arc_id.in_(arcs))
            )
        )
        nodes = set(
            s.scalars(
                sa.select(NodeORM.node_id).where(NodeORM.chapter_id.in_(chapters))
            )
        )
        turns = set(
            s.scalars(sa.select(TurnORM.turn_id).where(TurnORM.node_id.in_(nodes)))
        ) | referenced_turn_ids(s, story_list)
    found = {
        "story": stories,
        "arc": arcs,
        "chapter": chapters,
        "node": nodes,
        "turn": turns,
    }
    now = iso(ctx.now())
    with ctx.ops.begin() as s:
        known = {
            (r.resource_class, r.resource_id)
            for r in s.scalars(
                sa.select(RequestInventoryORM).where(
                    RequestInventoryORM.request_id == view.request_id
                )
            )
        }
        for cls, ids in found.items():
            for rid in ids:
                if (cls, rid) not in known:
                    s.add(
                        RequestInventoryORM(
                            request_id=view.request_id,
                            resource_class=cls,
                            resource_id=rid,
                            recorded_at=now,
                        )
                    )
                    known.add((cls, rid))
    result: dict[str, list[str]] = {c: [] for c in found}
    for cls, rid in known:
        result.setdefault(cls, []).append(rid)
    return {c: sorted(v) for c, v in result.items()}


def inventory_of(ops: sessionmaker[Session], request_id: str) -> dict[str, list[str]]:
    with ops() as s:
        rows = s.scalars(
            sa.select(RequestInventoryORM).where(
                RequestInventoryORM.request_id == request_id
            )
        )
        out: dict[str, list[str]] = {}
        for r in rows:
            out.setdefault(r.resource_class, []).append(r.resource_id)
    return {c: sorted(v) for c, v in out.items()}


# -- steps ------------------------------------------------------------------


def _suppression_for(control: sessionmaker[Session], request_id: str) -> str | None:
    with control() as s:
        return s.scalar(
            sa.select(DeletionSuppressionORM.suppression_id).where(
                DeletionSuppressionORM.request_id == request_id
            )
        )


def purge_sql(
    content: sessionmaker[Session],
    inventory: dict[str, list[str]],
    *,
    subject_ref: str | None,
    account_scope: bool,
    remove_mappings: bool,
) -> tuple[dict[str, int], dict[str, int]]:
    """One content transaction: registered disposal, account-scope refusal
    rows and ownership mappings; then the verification sweep. Returns
    (removed per class, remaining per table)."""
    from afterworlds.operations.lifecycle import dispose_rows

    stories, turns = inventory.get("story", []), inventory.get("turn", [])
    with content() as s:
        # Zero freed content on this connection (defense in depth; the
        # offline compaction is the physical proof).
        s.connection().exec_driver_sql("PRAGMA secure_delete = ON")
        counts = dispose_story_content(s, stories, turns)
        if account_scope and subject_ref is not None:
            counts["provider_refusal_rows"] = counts.get(
                "provider_refusal_rows", 0
            ) + dispose_rows(
                s,
                "provider_refusal_log",
                sa.column("sojourner_id") == subject_ref,
            )
        if remove_mappings and stories:
            result = s.execute(
                sa.delete(AccountResourceORM).where(
                    AccountResourceORM.resource_type == "story",
                    AccountResourceORM.resource_id.in_(stories),
                )
            )
            counts["ownership_mappings"] = int(result.rowcount)  # type: ignore[attr-defined]
        s.commit()
    with content() as s:
        remaining = remaining_story_content(
            s,
            stories,
            turns,
            extra_ids={
                "arcs": inventory.get("arc", []),
                "chapters": inventory.get("chapter", []),
                "nodes": inventory.get("node", []),
            },
        )
        if account_scope and subject_ref is not None:
            left = s.scalar(
                sa.text(
                    "SELECT count(*) FROM provider_refusal_log WHERE sojourner_id = :s"
                ),
                {"s": subject_ref},
            )
            if left:
                remaining["provider_refusal_log"] = int(left)
        if remove_mappings and stories:
            left = s.scalar(
                sa.select(sa.func.count()).where(
                    AccountResourceORM.resource_type == "story",
                    AccountResourceORM.resource_id.in_(stories),
                )
            )
            if left:
                remaining["account_resources"] = int(left)
    return counts, remaining


def record_rights_evidence(
    ctx: DeletionContext, subject_ref: str
) -> tuple[str, dict[str, int]]:
    """Minimum perpetual BYOK-rights evidence before closure (entitlement
    owner's ledger is the source)."""
    return record_rights_evidence_from_ledger(
        ctx.content, ctx.ops, subject_ref, now=ctx.now()
    )


def commercial_dependency(ctx: DeletionContext, subject_ref: str) -> str:
    """Live subscription/renewal references need CRD Issue 23's closure
    contract, which does not exist yet: the dependency stays unavailable."""
    with ctx.content() as s:
        projection = read_projection(s, UUID(subject_ref))
    if projection is not None and (
        projection.hosted_access_active or projection.cloud_services_active
    ):
        return "dependency_unavailable"
    return "not_applicable"


def physical_compaction_after(ops: sessionmaker[Session], request_id: str) -> bool:
    """Whether an offline compaction succeeded after this request's latest
    logical SQL/vector removal."""
    with ops() as s:
        rows = list(
            s.scalars(
                sa.select(PhaseEventORM)
                .where(PhaseEventORM.request_id == request_id)
                .order_by(PhaseEventORM.event_order)
            )
        )
    last_logical = max(
        (
            r.event_order
            for r in rows
            if r.phase_code in ("sql_content", "vector_logical")
            and r.outcome_code == "succeeded"
        ),
        default=None,
    )
    if last_logical is None:
        return False
    return any(
        r.event_order > last_logical
        and r.phase_code == "physical_compaction"
        and r.outcome_code == "succeeded"
        for r in rows
    )


def run_deletion(ctx: DeletionContext, view: RequestView, attempt_id: str) -> None:
    """Run every remaining step of one attempt, then evaluate completion."""
    rid = view.request_id
    record = ctx.store.record_phase
    remote = ctx.environment == "remote"
    account = view.scope == "account"
    subject = view.subject_ref
    assert view.confirmed_at is not None

    if remote and account:
        assert ctx.identity is not None
        if ctx.identity.principal_holds_binding(UUID(subject)):
            record(
                rid,
                attempt_id,
                "identity",
                "failed",
                detail_code="administrator_account",
            )
            ctx.store.end_attempt(
                rid,
                attempt_id,
                RequestState.FAILED,
                reason_code="administrator_account",
            )
            return

    # The enforced write boundary comes first: the fence drains every admitted
    # effect of the account and the suppression refuses any later one, so the
    # final inventory below sees every Turn and Story that can ever exist in
    # scope (review P1-1). For an account, "every export closed and
    # delivered" is checked at that same boundary -- inside the exclusive
    # section, before anything is recorded -- so an export admitted just
    # before it stays fulfillable and the deletion is simply retried (review
    # round 2, F2). Locally the whole run already holds the owner fence.
    def exports_clear() -> None:
        if account:
            blocker = _undelivered_exports(ctx, view)
            if blocker is not None:
                raise _Blocked(blocker)

    try:
        if remote:
            assert ctx.control is not None and ctx.fence is not None
            from afterworlds.remote.access import record_suppression_fenced

            if _suppression_for(ctx.control, rid) is None:
                header = ctx.store.header(rid)
                record_suppression_fenced(
                    ctx.fence,
                    ctx.control,
                    account_id=UUID(subject),
                    story_refs=current_scope_story_ids(ctx.content, header, "remote"),
                    request_id=rid,
                    scope=view.scope,
                    effective_boundary_at=view.confirmed_at,
                    now=ctx.now(),
                    timeout=ctx.fence_timeout,
                    precondition=exports_clear,
                )
            else:
                # Retry behind an existing suppression: no new export can be
                # admitted any more; existing ones must still be closed.
                exports_clear()
            fence_detail = None
        else:
            exports_clear()
            fence_detail = "local_owner_fence"
    except _Blocked as blocked:
        record(rid, attempt_id, "exports", "failed", detail_code=blocked.code)
        ctx.store.end_attempt(
            rid, attempt_id, RequestState.FAILED, reason_code=blocked.code
        )
        return
    except FenceBusy:
        record(rid, attempt_id, "fence", "failed", detail_code="in_flight_work")
        ctx.store.end_attempt(
            rid, attempt_id, RequestState.FAILED, reason_code="in_flight_work"
        )
        return
    if account:
        record(rid, attempt_id, "exports", "succeeded")
    record(rid, attempt_id, "fence", "succeeded", detail_code=fence_detail)

    inventory = ensure_inventory(ctx, view)
    record(
        rid,
        attempt_id,
        "inventory",
        "succeeded",
        counts={c: len(v) for c, v in inventory.items()},
    )

    stories = inventory.get("story", [])
    try:
        remaining = {sid: ctx.delete_story_chunks(sid) for sid in stories}
    except Exception:  # noqa: BLE001 -- any store failure is unverified, typed below
        record(
            rid,
            attempt_id,
            "vector_logical",
            "failed",
            detail_code="vector_unavailable",
        )
        ctx.store.end_attempt(
            rid, attempt_id, RequestState.FAILED, reason_code="vector_unavailable"
        )
        return
    if any(remaining.values()):
        record(
            rid,
            attempt_id,
            "vector_logical",
            "failed",
            counts={"stories_with_chunks": sum(1 for v in remaining.values() if v)},
            detail_code="chunks_remain",
        )
        ctx.store.end_attempt(
            rid, attempt_id, RequestState.FAILED, reason_code="chunks_remain"
        )
        return
    record(
        rid,
        attempt_id,
        "vector_logical",
        "succeeded",
        counts={"stories_verified_zero": len(stories)},
    )

    try:
        removed, left = purge_sql(
            ctx.content,
            inventory,
            subject_ref=subject,
            account_scope=account,
            remove_mappings=remote,
        )
    except Exception:  # noqa: BLE001 -- rolled back; reported, never presumed done
        record(
            rid, attempt_id, "sql_content", "failed", detail_code="content_store_error"
        )
        ctx.store.end_attempt(
            rid, attempt_id, RequestState.FAILED, reason_code="content_store_error"
        )
        return
    if left:
        record(
            rid,
            attempt_id,
            "sql_content",
            "failed",
            counts=left,
            detail_code="rows_remain",
        )
        ctx.store.end_attempt(
            rid, attempt_id, RequestState.FAILED, reason_code="rows_remain"
        )
        return
    if account:
        # Nothing in scope may have appeared outside the inventory (locally no
        # fence orders Story creation): fail visibly; a retry includes it.
        later = current_scope_story_ids(
            ctx.content, ctx.store.header(rid), ctx.environment
        )
        if later:
            record(
                rid,
                attempt_id,
                "sql_content",
                "failed",
                counts={"stories_outside_inventory": len(later)},
                detail_code="scope_changed",
            )
            ctx.store.end_attempt(
                rid, attempt_id, RequestState.FAILED, reason_code="scope_changed"
            )
            return
    record(rid, attempt_id, "sql_content", "succeeded", counts=removed)

    if account and remote:
        assert ctx.identity is not None
        try:
            outcome = ctx.identity.erase_account(
                UUID(subject), actor_ref="lifecycle_executor", request_id=rid
            )
        except FenceBusy:
            record(rid, attempt_id, "identity", "failed", detail_code="in_flight_work")
            ctx.store.end_attempt(
                rid, attempt_id, RequestState.FAILED, reason_code="in_flight_work"
            )
            return
        except IdentityError:
            record(
                rid, attempt_id, "identity", "failed", detail_code="identity_refused"
            )
            ctx.store.end_attempt(
                rid, attempt_id, RequestState.FAILED, reason_code="identity_refused"
            )
            return
        except OSError:
            # A notice copy that could not be verified gone (review round 2,
            # F6): nothing was erased; resolve the outbox, then retry.
            record(rid, attempt_id, "identity", "failed", detail_code="notice_copy")
            ctx.store.end_attempt(
                rid, attempt_id, RequestState.FAILED, reason_code="notice_copy"
            )
            return
        record(rid, attempt_id, "identity", "succeeded", detail_code=outcome)
    else:
        record(rid, attempt_id, "identity", "not_applicable")

    record(
        rid,
        attempt_id,
        "artifacts",
        "succeeded",
        counts={"removed": _remove_artifacts(ctx, view, stories)},
    )

    if account and remote:
        # Only a hosted account is closed: a local deletion keeps the local
        # ledger (and so its licence evidence) and cancels nothing.
        outcome, counts = record_rights_evidence(ctx, subject)
        record(rid, attempt_id, "rights_evidence", outcome, counts=counts)
        record(rid, attempt_id, "commercial", commercial_dependency(ctx, subject))
    else:
        record(rid, attempt_id, "rights_evidence", "not_applicable")
        record(rid, attempt_id, "commercial", "not_applicable")

    evaluate(ctx, rid, attempt_id)


class _Blocked(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _undelivered_exports(ctx: DeletionContext, view: RequestView) -> str | None:
    """Why the subject's exports block closure, if they do: an export request
    still open (queued, approved, running or failed), or a completed one
    whose available artifact was never delivered. ``None`` when clear."""
    from afterworlds.operations.requests import OPEN_STATES, RequestState

    with ctx.ops() as s:
        exports = list(
            s.scalars(
                sa.select(DataRequestORM.request_id).where(
                    DataRequestORM.subject_ref == view.subject_ref,
                    DataRequestORM.environment == view.environment,
                    DataRequestORM.kind == "export",
                )
            )
        )
    now = ctx.now()
    for export_id in exports:
        state = ctx.store.state_of(export_id)[1]
        if state in OPEN_STATES:
            return "export_pending"
        if state is RequestState.COMPLETED:
            artifact = ctx.store.view(export_id).artifact
            if (
                artifact is not None
                and artifact.status == "available"
                and artifact.removed_at is None
                and artifact.expires_at > now
                and artifact.delivered_at is None
            ):
                return "export_awaiting_download"
    return None


def _remove_artifacts(
    ctx: DeletionContext, view: RequestView, stories: list[str]
) -> int:
    """Service-managed export artifacts of this subject that carry in-scope
    data: every one for an account; a Story's own or account exports."""
    removed = 0
    with ctx.ops() as s:
        rows = list(
            s.execute(
                sa.select(
                    ExportArtifactORM.artifact_id,
                    DataRequestORM.scope,
                    DataRequestORM.story_refs,
                )
                .join(
                    DataRequestORM,
                    DataRequestORM.request_id == ExportArtifactORM.request_id,
                )
                .where(
                    DataRequestORM.subject_ref == view.subject_ref,
                    ExportArtifactORM.removed_at.is_(None),
                )
            )
        )
    for artifact_id, scope, refs in rows:
        if (
            view.scope == "account"
            or scope == "account"
            or set(json.loads(refs)) & set(stories)
        ):
            removed += remove_artifact(ctx.ops, artifact_id, now=ctx.now())
    return removed


def evaluate(ctx: DeletionContext, request_id: str, attempt_id: str) -> RequestState:
    """Re-check the pending phases (physical compaction, backups) and record
    completion only when every postcondition holds."""
    record = ctx.store.record_phase
    view = ctx.store.view(request_id)
    remote = ctx.environment == "remote"
    if remote:
        if physical_compaction_after(ctx.ops, request_id):
            pass
        else:
            record(
                request_id,
                attempt_id,
                "physical_compaction",
                "pending",
                deadline_at=view.live_deadline_at,
            )
        assert ctx.control is not None
        suppression = _suppression_for(ctx.control, request_id)
        assert suppression is not None
        disposition = backup_disposition(ctx.control, suppression, now=ctx.now())
        record(
            request_id,
            attempt_id,
            "backups",
            (
                "succeeded"
                if disposition.complete
                else ("failed" if disposition.overdue else "pending")
            ),
            counts={
                "pending": len(disposition.pending_backup_ids),
                "unverified": len(disposition.unverified_backup_ids),
            },
            detail_code="overdue" if disposition.overdue else None,
            deadline_at=disposition.deadline,
        )
    else:
        record(
            request_id,
            attempt_id,
            "physical_compaction",
            "owner_controlled",
            detail_code="local_device",
        )
        record(request_id, attempt_id, "backups", "not_applicable")
    view = ctx.store.view(request_id)
    outcomes = {p.phase_code: p.outcome_code for p in view.phases}
    if any(outcomes.get(code) == "failed" for code in FINAL_PHASES):
        failed = next(c for c in FINAL_PHASES if outcomes.get(c) == "failed")
        ctx.store.end_attempt(
            request_id, attempt_id, RequestState.FAILED, reason_code=failed
        )
        return RequestState.FAILED
    if all(outcomes.get(code) in DONE for code in FINAL_PHASES):
        ctx.store.add_receipt(
            request_id, attempt_id, "deletion_receipt", deletion_receipt(ctx, view)
        )
        ctx.store.end_attempt(request_id, attempt_id, RequestState.COMPLETED)
        return RequestState.COMPLETED
    return RequestState.IN_PROGRESS


def deletion_receipt(ctx: DeletionContext, view: RequestView) -> dict[str, Any]:
    """Allowlisted final receipt: classes/counts, retained categories and end
    conditions, backup disposition and verification evidence -- IDs, counts
    and times only, never content."""
    phases = {p.phase_code: p for p in view.phases}
    return {
        "receipt": "deletion_receipt",
        "schema_version": 1,
        "request_id": view.request_id,
        "scope": view.scope,
        "environment": view.environment,
        "subject_ref": view.subject_ref,
        "policy_version": POLICY_VERSION,
        "confirmed_at": iso(view.confirmed_at) if view.confirmed_at else None,
        "completed_at": iso(ctx.now()),
        "removed_classes": list(removed_for(view.scope, view.environment)),
        "phase_evidence": {
            code: {
                "outcome": p.outcome_code,
                "counts": p.counts,
                "detail": p.detail_code,
                "observed_at": iso(p.observed_at),
            }
            for code, p in phases.items()
        },
        "retained_categories": list(retained_for(view.scope, view.environment)),
        "deadlines": {
            "live_deletion_deadline_at": (
                iso(view.live_deadline_at) if view.live_deadline_at else None
            ),
            "final_deletion_deadline_at": (
                iso(view.backup_deadline_at) if view.backup_deadline_at else None
            ),
            "live_deletion_met": _met(view, view.live_deadline_at),
            "final_deletion_met": (
                view.backup_deadline_at is None or ctx.now() <= view.backup_deadline_at
            ),
        },
        "backup_disposition": (
            phases["backups"].outcome_code if "backups" in phases else None
        ),
        "notices": list(NOTICES),
    }


def _met(view: RequestView, deadline: datetime | None) -> bool:
    """Every live phase (logical and physical) finished by *deadline*."""
    if deadline is None:
        return True
    done = [
        p.observed_at
        for p in view.phases
        if p.phase_code in ("vector_logical", "sql_content", "physical_compaction")
        and p.outcome_code in ("succeeded", "owner_controlled")
    ]
    return bool(done) and max(done) <= deadline


def deletion_preview(
    ctx: DeletionContext, view: RequestView, story_ids: list[str]
) -> dict[str, Any]:
    from afterworlds.operations.requests import scope_revision

    with ctx.content() as s:
        turns = 0
        for sid in story_ids:
            nodes = (
                sa.select(NodeORM.node_id)
                .join(ChapterORM, ChapterORM.chapter_id == NodeORM.chapter_id)
                .join(ArcORM, ArcORM.arc_id == ChapterORM.arc_id)
                .where(ArcORM.story_id == sid)
            )
            turns += int(
                s.scalar(sa.select(sa.func.count()).where(TurnORM.node_id.in_(nodes)))
                or 0
            )
            # Attributable orphan Turns are in scope too (review sibling audit).
            turns += int(
                s.scalar(
                    sa.select(sa.func.count()).where(
                        TurnORM.node_id.is_(None),
                        TurnORM.turn_id.in_(referenced_turn_ids(s, [sid])),
                    )
                )
                or 0
            )
    commercial = (
        commercial_dependency(ctx, view.subject_ref)
        if view.scope == "account" and ctx.environment == "remote"
        else "not_applicable"
    )
    return {
        "scope": view.scope,
        "story_ids": story_ids,
        "counts": {"stories": len(story_ids), "turns": turns},
        "removed_classes": list(removed_for(view.scope, ctx.environment)),
        "retained_categories": list(retained_for(view.scope, ctx.environment)),
        "scope_revision": scope_revision(view.scope, story_ids),
        "live_deletion_limit_days": 7,
        "final_deletion_limit_days": 30 if ctx.environment == "remote" else None,
        "commercial_dependency": commercial,
        "notices": list(NOTICES),
    }
