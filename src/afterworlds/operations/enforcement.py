"""Restore-time deletion enforcement and physical-disposal bookkeeping --
CRD Issue 22 §6 "Backup handling", ADR-021 D10 step 4.

A restored snapshot may carry content deleted after its capture. Before the
restored store is served or any background/provider work resumes (the app
refuses to start while the restore is pending), :func:`enforce_restore`
re-applies, from the control store's durable inventories (outside the
snapshot), every deletion whose suppression is active -- Story memory first,
then the registered SQL disposal including orphan Turns -- re-expires
expired entitlement subjects and time-expired content-free rows, and then
compacts both stores physically. ``storage_cli verify-restore`` (#205) then
proves every suppression holds. A closed account stays closed: identity and
suppression state live in the control store and are never restored.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from chromadb.api import ClientAPI
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.operations.compaction import compact_stores
from afterworlds.operations.deletion import inventory_of, purge_sql
from afterworlds.operations.orm import (
    DataRequestORM,
    PhaseEventORM,
    RestoreEnforcementORM,
)
from afterworlds.operations.requests import RequestStore
from afterworlds.operations.retention import (
    SweepResult,
    expire_refusal_log,
    reapply_ledger_expiries,
)
from afterworlds.operations.vectors import story_chunk_deleter
from afterworlds.remote.control_orm import DeletionSuppressionORM
from afterworlds.remote.control_store import iso
from afterworlds.remote.storage import StoreRefused, pending_restores, sqlite_path


def physical_disposal_pending(ops: sessionmaker[Session]) -> list[str]:
    """Requests whose latest physical-compaction phase is pending: a backup
    captured now could still carry their deleted content in free pages or
    vector segments, so capture refuses until compaction runs."""
    with ops() as s:
        rows = list(
            s.scalars(
                sa.select(PhaseEventORM)
                .where(PhaseEventORM.phase_code == "physical_compaction")
                .order_by(PhaseEventORM.event_order)
            )
        )
    latest: dict[str, str] = {}
    for row in rows:
        latest[row.request_id] = row.outcome_code
    return sorted(rid for rid, outcome in latest.items() if outcome == "pending")


def control_file(control: sessionmaker[Session]) -> Path:
    """The live control store's SQLite file, disposed of by compaction; a
    control store that is not a SQLite file is refused (``StoreRefused``):
    its physical disposal could not be shown."""
    engine = control.kw["bind"]
    path = sqlite_path(engine.url.render_as_string(hide_password=False))
    engine.dispose()  # no pooled reader may hold WAL frames back
    return path


def record_compaction(
    ops: sessionmaker[Session], evidence: dict[str, Any], *, now: Callable[[], datetime]
) -> list[str]:
    """Mark every physical-compaction-pending request as physically disposed
    (counts only). Returns those request IDs."""
    store = RequestStore(ops, now=now)
    done = physical_disposal_pending(ops)
    counts = {
        "content_wal_bytes": int(evidence.get("content", {}).get("wal_bytes", 0)),
        "control_wal_bytes": int(evidence.get("control", {}).get("wal_bytes", 0)),
        "vector_records_rebuilt": sum(
            evidence.get("vector", {}).get("collections", {}).values()
        ),
    }
    for request_id in done:
        _, _, attempt = store.state_of(request_id)
        store.record_phase(
            request_id,
            attempt or "maintenance",
            "physical_compaction",
            "succeeded",
            counts=counts,
            detail_code="offline_compaction",
        )
    return done


def enforce_restore(
    control: sessionmaker[Session],
    content: sessionmaker[Session],
    *,
    database_path: Path,
    vector_dir: Path,
    client_factory: Callable[[], ClientAPI],
    now: datetime,
) -> dict[str, Any]:
    """Re-apply every active deletion to a restored store (see module)."""
    if not pending_restores(control):
        raise StoreRefused("no restore is awaiting enforcement")
    with control() as s:
        suppressions = list(
            s.scalars(
                sa.select(DeletionSuppressionORM).where(
                    DeletionSuppressionORM.status == "active"
                )
            )
        )
        headers = {
            h.request_id: h
            for h in s.scalars(
                sa.select(DataRequestORM).where(
                    DataRequestORM.request_id.in_([x.request_id for x in suppressions])
                )
            )
        }
    delete_chunks = story_chunk_deleter(client_factory)
    reapplied = 0
    for sup in suppressions:
        inventory = inventory_of(control, sup.request_id)
        stories = sorted(
            set(inventory.get("story", [])) | set(json.loads(sup.story_refs))
        )
        inventory["story"] = stories
        for story in stories:
            if delete_chunks(story) != 0:
                raise StoreRefused("story-memory chunks remain after re-deletion")
        header = headers.get(sup.request_id)
        _, remaining = purge_sql(
            content,
            inventory,
            subject_ref=sup.subject_ref,
            account_scope=sup.scope == "account",
            remove_mappings=True,
        )
        if remaining:
            raise StoreRefused("deleted rows remain after re-deletion")
        if header is not None:
            reapplied += 1
    result = SweepResult()
    expire_refusal_log(content, now, result)
    ledger = reapply_ledger_expiries(control, content, now=now)
    # Restored fallback coverage gaps: promoted if still live, disposed if
    # already promoted or expired -- never resurrected (review of bd0ae1df).
    from afterworlds.operations.anomalies import promote_coverage_gaps

    promote_coverage_gaps(content, control, now=now)
    content.kw["bind"].dispose()
    evidence = compact_stores(
        database_path, vector_dir, client_factory, control_file(control)
    )
    summary = {
        "suppressions_reapplied": len(suppressions),
        "requests_reapplied": reapplied,
        "refusal_rows_expired": result.refusal_rows_expired,
        "entitlement_events_reexpired": ledger,
        "compaction": evidence,
    }
    # The restore may be verified (and served) only after this record exists
    # (review P1-4); counts only.
    with control.begin() as s:
        for restore_id in pending_restores(control):
            row = s.get(RestoreEnforcementORM, restore_id)
            if row is None:
                s.add(
                    RestoreEnforcementORM(
                        restore_id=restore_id,
                        enforced_at=iso(now),
                        summary_json=json.dumps(summary, sort_keys=True, default=str),
                    )
                )
            else:
                row.enforced_at = iso(now)
                row.summary_json = json.dumps(summary, sort_keys=True, default=str)
    return summary


def restore_enforced(control: sessionmaker[Session], restore_id: str) -> bool:
    """Whether ``enforce-restore`` ran to completion for this restore."""
    with control() as s:
        return s.get(RestoreEnforcementORM, restore_id) is not None
