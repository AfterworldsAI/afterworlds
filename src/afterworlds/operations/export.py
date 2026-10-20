"""Story and account-wide export -- CRD Issue 22 §5.

An export is built from one read transaction of the content store (SQLite
WAL gives it a consistent snapshot), through the existing player-visible
projections only: the transcript the Sojourner already sees, the mode's
visible state and the setup view. Internal canon (Story Bible, which may hold
GM secrets), Rolling Summaries, hidden RPG mechanics/audit, Retrieval index,
provider diagnostics, credentials and other subjects are deliberate,
manifest-listed exclusions; no raw row or database file is ever serialized.

The artifact is a ZIP of UTF-8 JSON and Markdown with a versioned
``manifest.json``. Its inventory row is written before the first file effect
(``staging``), the body is written to a ``.partial`` name and renamed only
when complete, and it becomes ``available`` only after that; a failure
removes the partial file at once and marks the row ``failed`` (anything
left is removed by the 24-hour maintenance sweep). Hosted artifacts expire
7 days after ``available_at``.
"""

from __future__ import annotations

import io
import json
import os
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.entitlement.inspection import list_events, read_projection
from afterworlds.operations.errors import OperationError, OperationErrorKind
from afterworlds.operations.orm import ExportArtifactORM
from afterworlds.operations.policy import ARTIFACT_AVAILABILITY, PARTIAL_CLEANUP
from afterworlds.remote.control_store import iso

FORMAT = "afterworlds-export"

EXCLUSIONS: tuple[tuple[str, str], ...] = (
    (
        "story_bible_internal_canon",
        "Internal narrative canon (may hold unrevealed secrets); the transcript and "
        "visible state carry what you have seen.",
    ),
    ("rolling_summaries_internal", "Internal derived summaries of the transcript."),
    (
        "hidden_rpg_mechanics",
        "Hidden rolls, modifiers, internal adjudication and roll audit.",
    ),
    ("retrieval_index", "Derived search index copies of delivered prose."),
    ("provider_diagnostics", "Provider refusal diagnostics and routing internals."),
    ("credentials_and_secrets", "Provider keys, tokens and password verifiers."),
    (
        "authentication_security_records",
        "Session, recovery and verification security records.",
    ),
    ("shared_rules_packages", "Shared Rules Package source (not account-owned)."),
    ("other_subjects", "Any other account's or Story's data."),
    (
        "internal_storage_inventory",
        "Backup, suppression and artifact storage inventories.",
    ),
)


@dataclass(frozen=True)
class ExportInputs:
    request_id: str
    scope: str
    environment: str
    subject_ref: str
    story_ids: tuple[str, ...]
    #: Account scope: the approved account/profile view (identity owner).
    account_view: dict[str, Any] | None
    #: Account scope: own data-request and support records (operations).
    operational_view: dict[str, Any] | None
    policy_version: str


def _jsonable(model: Any) -> Any:
    return None if model is None else model.model_dump(mode="json")


def _story_record(session: Session, story_id: UUID) -> tuple[dict[str, Any], str]:
    # Late imports: the API projections own these shapes.
    from afterworlds.api.routes.setup import get_setup_state
    from afterworlds.api.story_bootstrap import resolve_play_status
    from afterworlds.api.visible_state import build_visible_state
    from afterworlds.persistence.crud.node import list_turns_by_story
    from afterworlds.persistence.crud.story import get_story

    story = get_story(session, story_id)
    if story is None:
        raise OperationError(
            OperationErrorKind.UNAVAILABLE, "A Story in scope could not be read."
        )
    turns = []
    offset = 0
    while True:
        page = list_turns_by_story(session, story_id, limit=500, offset=offset)
        turns += page
        if len(page) < 500:
            break
        offset += 500
    record = {
        "story": {
            "story_id": str(story.story_id),
            "title": story.title,
            "mode": story.mode.value,
            "status": resolve_play_status(session, story.story_id, story.mode),
            "created_at": story.created_at.isoformat(),
            "updated_at": story.updated_at.isoformat(),
        },
        "transcript": [
            {
                "turn_id": str(t.turn_id),
                "user_input": t.user_input,
                "assistant_output": t.assistant_output,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                "intent_classification": (
                    t.intent_classification.value
                    if hasattr(t.intent_classification, "value")
                    else t.intent_classification
                ),
            }
            for t in turns
        ],
        "visible_state": _jsonable(
            build_visible_state(session, story.story_id, story.mode)
        ),
        "setup_state": _jsonable(get_setup_state(story.story_id, session)).get(
            "setup_state"
        ),
    }
    lines = [f"# {story.title}", "", f"Mode: {story.mode.value}", ""]
    for t in record["transcript"]:
        lines += [
            f"## Turn {t['timestamp'] or ''}".rstrip(),
            "",
            f"**You:** {t['user_input'] or ''}",
            "",
            str(t["assistant_output"] or ""),
            "",
        ]
    return record, "\n".join(lines)


def _entitlement_view(session: Session, subject: UUID) -> dict[str, Any]:
    from afterworlds.api.operations import history_item

    events = []
    after = 0
    total = 0
    while True:
        page = list_events(session, subject, after_sequence=after, limit=500)
        total = page.total_events
        events += [history_item(e).model_dump(mode="json") for e in page.events]
        if page.next_after_sequence is None:
            break
        after = page.next_after_sequence
    for event in events:
        # The operator's principal reference is internal; say who acted.
        if event.get("adjusted_by"):
            event["adjusted_by"] = "administrator"
    projection = read_projection(session, subject)
    return {
        "order": "global_sequence_ascending",
        "total_events": total,
        "events": events,
        "current": (
            None
            if projection is None
            else {
                "hosted_access_active": projection.hosted_access_active,
                "hosted_plan": (
                    projection.hosted_access_plan.value
                    if projection.hosted_access_plan
                    else None
                ),
                "included_credits": f"{projection.hosted_credit_balance:.4f}",
                "top_up_credits": f"{projection.top_up_credit_balance:.4f}",
                "byok_license_active": projection.byok_license_active,
                "cloud_services_active": projection.cloud_services_active,
                "cloud_services_expires_at": (
                    projection.cloud_services_expires_at.isoformat()
                    if projection.cloud_services_expires_at
                    else None
                ),
            }
        ),
    }


def build_archive(
    content: sessionmaker[Session], inputs: ExportInputs, *, now: datetime
) -> tuple[bytes, dict[str, Any]]:
    """The artifact body and its manifest, from one consistent read."""
    files: dict[str, str] = {}
    per_story: dict[str, dict[str, Any]] = {}
    counts = {"stories": 0, "turns": 0}
    with content() as session:
        session.connection().exec_driver_sql("BEGIN")
        for story_id in inputs.story_ids:
            record, markdown = _story_record(session, UUID(story_id))
            transcript = record["transcript"]
            per_story[story_id] = {
                "turns": len(transcript),
                "last_turn_id": transcript[-1]["turn_id"] if transcript else None,
                "last_turn_at": transcript[-1]["timestamp"] if transcript else None,
            }
            counts["stories"] += 1
            counts["turns"] += len(transcript)
            files[f"stories/{story_id}/story.json"] = json.dumps(record, indent=2)
            files[f"stories/{story_id}/transcript.md"] = markdown
        included = ["story_metadata", "transcript", "visible_state", "setup_state"]
        boundary: dict[str, Any] = {"read": "single_transaction", "stories": per_story}
        if inputs.scope == "account":
            ledger = _entitlement_view(session, UUID(inputs.subject_ref))
            counts["entitlement_events"] = ledger["total_events"]
            boundary["entitlement_through_sequence"] = (
                ledger["events"][-1]["global_sequence"] if ledger["events"] else None
            )
            files["account/entitlement_history.json"] = json.dumps(ledger, indent=2)
            files["account/account.json"] = json.dumps(inputs.account_view, indent=2)
            files["account/operational_records.json"] = json.dumps(
                inputs.operational_view, indent=2
            )
            ops = inputs.operational_view or {}
            counts["data_requests"] = len(ops.get("data_requests", []))
            counts["support_actions"] = len(ops.get("support_actions", []))
            included += [
                "account_profile",
                "entitlement_history",
                "data_requests",
                "support_actions",
            ]
        session.rollback()
    manifest = {
        "format": FORMAT,
        "schema_version": 1,
        "request_id": inputs.request_id,
        "scope": inputs.scope,
        "environment": inputs.environment,
        "subject_ref": inputs.subject_ref,
        "generated_at": iso(now),
        "policy_version": inputs.policy_version,
        "snapshot_boundary": boundary,
        "included_classes": included,
        "counts": counts,
        "exclusions": [{"code": c, "reason": r} for c, r in EXCLUSIONS],
        "files": sorted(files),
        "reading": (
            "UTF-8 JSON and Markdown files in a ZIP archive. Afterworlds does not "
            "provide an import or restore path for this format."
        ),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        for name, body in sorted(files.items()):
            archive.writestr(name, body)
    return buffer.getvalue(), manifest


def produce_artifact(
    ops: sessionmaker[Session],
    export_dir: Path,
    *,
    request_id: str,
    attempt_id: str,
    build: Callable[[], tuple[bytes, dict[str, Any]]],
    now: Callable[[], datetime],
) -> tuple[str, dict[str, Any]]:
    """Inventory, write and publish one artifact; returns (artifact_id,
    manifest). Any failure leaves a ``failed`` row and no partial file."""
    artifact_id = str(uuid4())
    final = export_dir / f"{artifact_id}.zip"
    partial = export_dir / f"{artifact_id}.zip.partial"
    started = now()
    with ops.begin() as s:
        s.add(
            ExportArtifactORM(
                artifact_id=artifact_id,
                request_id=request_id,
                attempt_id=attempt_id,
                storage_locator=str(final),
                status="staging",
                created_at=iso(started),
                expires_at=iso(started + PARTIAL_CLEANUP),
            )
        )
    try:
        body, manifest = build()
        export_dir.mkdir(parents=True, exist_ok=True)
        fd = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(partial, final)
        with zipfile.ZipFile(final) as check:
            if check.testzip() is not None or "manifest.json" not in check.namelist():
                raise OSError("export archive failed verification")
    except BaseException:
        for leftover in (partial, final):
            leftover.unlink(missing_ok=True)
        failed_at = now()
        with ops.begin() as s:
            row = s.get(ExportArtifactORM, artifact_id)
            assert row is not None
            row.status = "removed"
            row.removed_at = iso(failed_at)
        raise
    available = now()
    with ops.begin() as s:
        row = s.get(ExportArtifactORM, artifact_id)
        assert row is not None
        row.status = "available"
        row.available_at = iso(available)
        row.expires_at = iso(available + ARTIFACT_AVAILABILITY)
        row.size_bytes = len(body)
    return artifact_id, manifest


def remove_artifact(
    ops: sessionmaker[Session], artifact_id: str, *, now: datetime
) -> bool:
    """Delete one service-managed artifact and revoke its download (the row
    leaves ``available``). Returns whether anything was removed."""
    with ops.begin() as s:
        row = s.get(ExportArtifactORM, artifact_id)
        if row is None or row.removed_at is not None:
            return False
        Path(row.storage_locator).unlink(missing_ok=True)
        Path(row.storage_locator + ".partial").unlink(missing_ok=True)
        row.status = "expired" if row.status == "available" else "removed"
        row.removed_at = iso(now)
    return True


def artifacts_for_requests(
    ops: sessionmaker[Session], request_ids: list[str]
) -> list[str]:
    with ops() as s:
        return list(
            s.scalars(
                sa.select(ExportArtifactORM.artifact_id).where(
                    ExportArtifactORM.request_id.in_(request_ids),
                    ExportArtifactORM.removed_at.is_(None),
                )
            )
        )
