"""Story-memory backfill / reindex / delete — CRD Issue 18 / ADR-018 D7/D11.

Recovery for a Chroma write failure is a re-run (D7): v1 ships this
idempotent manual backfill/reindex, not an automatic retry queue. All three
operations here consult the single shared eligibility predicate
(``pipeline.retrieval.eligibility``) — the same one the live ingestion gate
uses — so live ingestion and offline backfill/reindex never disagree
(ADR-018 sibling-audit checkpoint #5).
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.models.enums import StoryMode
from afterworlds.persistence.crud.retrieval import get_turn_for_eligibility
from afterworlds.persistence.orm.node import NodeORM, TurnORM
from afterworlds.persistence.orm.story import ArcORM, ChapterORM
from afterworlds.pipeline.retrieval.eligibility import gather_turn_eligibility_for_turn
from afterworlds.pipeline.retrieval.write_service import RetrievalMemoryWriteService


class RetrievalReindexWipeIncompleteError(RuntimeError):
    """Raised when reindex_story()'s delete-before-rebuild phase leaves
    chunks behind (ADR-018 D11). Rebuilding on top of an incomplete wipe
    would leave stale chunks alongside the rebuilt set, so backfill must
    never run in that case — this is distinct from a data-integrity error
    (a per-turn marker/SQLite defect reported in ``BackfillReport``): this
    is an operational failure of the delete phase itself.
    """


@dataclass(frozen=True)
class BackfillReport:
    """Outcome of a backfill or reindex run for one story."""

    turns_scanned: int
    turns_ingested: int
    turns_skipped_ineligible: int
    data_integrity_errors: tuple[UUID, ...]


def _all_turn_ids_for_story(session: Session, story_id: UUID) -> list[UUID]:
    """Return every persisted Turn ID for *story_id*, oldest-first.

    Unlike ``SQLiteRecentTurnsProvider.get_recent_turns``, this is
    unbounded and includes every disposition (OOC included) — the
    eligibility predicate is what filters, not this query.
    """
    stmt = (
        select(TurnORM.turn_id)
        .join(NodeORM, TurnORM.node_id == NodeORM.node_id)
        .join(ChapterORM, NodeORM.chapter_id == ChapterORM.chapter_id)
        .join(ArcORM, ChapterORM.arc_id == ArcORM.arc_id)
        .where(ArcORM.story_id == str(story_id))
        .order_by(TurnORM.timestamp.asc(), TurnORM.turn_id.asc())
    )
    return [UUID(row) for row in session.execute(stmt).scalars().all()]


def backfill_story(
    session: Session,
    write_service: RetrievalMemoryWriteService,
    story_id: UUID,
    story_mode: StoryMode,
) -> BackfillReport:
    """Ingest every currently-eligible, not-yet-indexed turn for *story_id*.

    Idempotent: re-running against an already-ingested turn is a no-op at
    the vector layer (deterministic chunk IDs, D11) even though this
    function re-calls ``ingest_turn`` unconditionally for every eligible
    turn — upsert-by-deterministic-ID makes the re-write byte-identical.
    """
    turn_ids = _all_turn_ids_for_story(session, story_id)
    ingested = 0
    skipped = 0
    integrity_errors: list[UUID] = []
    for turn_id in turn_ids:
        # get_turn_for_eligibility (not the general-purpose get_turn) so a
        # single Writing turn with malformed persisted mode_metadata cannot
        # abort the whole story's backfill/reindex run (Codex review, PR
        # #119) -- ADR-018 D6 already defines that shape as ineligible, not
        # a fatal error.
        turn = get_turn_for_eligibility(session, turn_id)
        if turn is None:
            continue
        decision = gather_turn_eligibility_for_turn(session, turn, story_mode)
        if decision.data_integrity_error:
            integrity_errors.append(turn.turn_id)
            skipped += 1
            continue
        if not decision.eligible:
            skipped += 1
            continue
        write_service.ingest_turn(
            story_id=story_id,
            turn_id=turn.turn_id,
            node_id=turn.node_id,
            mode=story_mode.value,
            delivered_output=turn.assistant_output,
            created_at=turn.timestamp.isoformat(),
        )
        ingested += 1
    return BackfillReport(
        turns_scanned=len(turn_ids),
        turns_ingested=ingested,
        turns_skipped_ineligible=skipped,
        data_integrity_errors=tuple(integrity_errors),
    )


def reindex_story(
    session: Session,
    write_service: RetrievalMemoryWriteService,
    story_id: UUID,
    story_mode: StoryMode,
) -> BackfillReport:
    """Wipe *story_id*'s chunks then rebuild from SQLite ground truth.

    Full story-level reindex (ADR-018 D11): rebuild-from-source rather than
    relying on upsert alone, so a shrunk or corrected history is exactly
    reflected (no stray chunks survive from a chunk-set that has since
    shrunk for reasons outside a single turn's re-ingestion, e.g. a turn
    deletion that predates this reindex run).

    Raises:
        RetrievalReindexWipeIncompleteError: if the delete phase leaves any
            chunks behind — rebuild never runs on top of an incomplete wipe
            (Codex review, PR #119 round 6).
    """
    remaining = write_service.delete_story(story_id)
    if remaining != 0:
        raise RetrievalReindexWipeIncompleteError(
            f"reindex aborted for story {story_id}: delete_story left"
            f" {remaining} chunk(s) behind; refusing to rebuild on top of an"
            " incomplete wipe"
        )
    return backfill_story(session, write_service, story_id, story_mode)
