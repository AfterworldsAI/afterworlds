"""The spatial record's store (issue #211, M1).

Reads are cheap local queries: the per-Turn consult loads the story's active
record and its latest revision, nothing else. Writes stage a new immutable
revision in the caller's session, which for a Turn is the delivery-gated
transaction, so an undelivered Turn leaves no revision.

``begin_scene`` and ``resume_scene`` with a place key stand in for a scene
entity, which AW doesn't have (Design v11; issue #211 dependencies).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session

from afterworlds.mapper.models import MapRecord, Revision, Snapshot, SpatialUpdate
from afterworlds.mapper.refine import GENERATOR_VERSION
from afterworlds.mapper.updates import UpdateRefused, apply_all, content_hash
from afterworlds.persistence.orm.spatial import SpatialMapORM, SpatialMapRevisionORM


def _record(row: SpatialMapORM) -> MapRecord:
    return MapRecord(
        map_id=UUID(row.map_id),
        story_id=UUID(row.story_id),
        place_key=row.place_key,
        label=row.label,
        status=row.status,  # type: ignore[arg-type]
        grid_type=row.grid_type,  # type: ignore[arg-type]
        seed=row.seed,
        generator_version=row.generator_version,
        style=dict(row.style),
        revision=row.revision,
        created_turn_id=UUID(row.created_turn_id) if row.created_turn_id else None,
    )


def _revision(row: SpatialMapRevisionORM) -> Revision:
    return Revision.model_validate(
        {
            "map_id": row.map_id,
            "revision": row.revision,
            "parent_revision": row.parent_revision,
            "turn_id": row.turn_id,
            "node_id": row.node_id,
            "sequence_id": row.sequence_id,
            "updates": row.updates,
            "snapshot": row.snapshot,
            "content_hash": row.content_hash,
        }
    )


def _uuid(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def begin_scene(
    session: Session,
    *,
    story_id: UUID,
    place_key: str,
    label: str,
    snapshot: Snapshot,
    seed: int,
    now: datetime,
    turn_id: UUID | None = None,
    style: dict[str, str] | None = None,
) -> MapRecord:
    """Start the record for a place and make it the story's active scene.
    A place that already has a record is resumed instead (its geography is
    never replaced)."""
    existing = resume_scene(session, story_id=story_id, place_key=place_key)
    if existing is not None:
        return existing
    _archive_others(session, story_id, keep=None)
    map_id = uuid4()
    session.add(
        SpatialMapORM(
            map_id=str(map_id),
            story_id=str(story_id),
            place_key=place_key,
            label=label,
            status="active",
            grid_type="square",
            seed=seed,
            generator_version=GENERATOR_VERSION,
            style=style or {},
            revision=0,
            created_turn_id=_uuid(turn_id),
            created_at=now.isoformat(),
        )
    )
    session.flush()
    session.add(
        SpatialMapRevisionORM(
            map_id=str(map_id),
            revision=0,
            parent_revision=None,
            turn_id=_uuid(turn_id),
            node_id=None,
            sequence_id=None,
            updates=[],
            snapshot=snapshot.model_dump(mode="json"),
            content_hash=content_hash(snapshot),
            created_at=now.isoformat(),
        )
    )
    session.flush()
    row = session.get(SpatialMapORM, str(map_id))
    assert row is not None
    return _record(row)


def resume_scene(
    session: Session, *, story_id: UUID, place_key: str
) -> MapRecord | None:
    """Reopen a place's record at its latest revision and make it active."""
    row = session.scalars(
        sa.select(SpatialMapORM).where(
            SpatialMapORM.story_id == str(story_id),
            SpatialMapORM.place_key == place_key,
        )
    ).first()
    if row is None:
        return None
    if row.status != "active":
        _archive_others(session, story_id, keep=row.map_id)
        row.status = "active"
        session.flush()
    return _record(row)


def archive_map(session: Session, map_id: UUID) -> None:
    row = session.get(SpatialMapORM, str(map_id))
    if row is not None:
        row.status = "archived"
        session.flush()


def _archive_others(session: Session, story_id: UUID, *, keep: str | None) -> None:
    for row in session.scalars(
        sa.select(SpatialMapORM).where(
            SpatialMapORM.story_id == str(story_id),
            SpatialMapORM.status == "active",
        )
    ):
        if row.map_id != keep:
            row.status = "archived"
    session.flush()


def active_scene(session: Session, story_id: UUID) -> tuple[MapRecord, Revision] | None:
    """The per-Turn consult: the story's active record and its latest
    revision, one indexed read each. No generation, no model call."""
    row = session.scalars(
        sa.select(SpatialMapORM).where(
            SpatialMapORM.story_id == str(story_id),
            SpatialMapORM.status == "active",
        )
    ).first()
    if row is None:
        return None
    rev = session.get(SpatialMapRevisionORM, (row.map_id, row.revision))
    assert rev is not None
    return _record(row), _revision(rev)


def revisions(session: Session, map_id: UUID) -> list[Revision]:
    rows = session.scalars(
        sa.select(SpatialMapRevisionORM)
        .where(SpatialMapRevisionORM.map_id == str(map_id))
        .order_by(SpatialMapRevisionORM.revision)
    )
    return [_revision(r) for r in rows]


def stage_revision(
    session: Session,
    *,
    map_id: UUID,
    updates: Sequence[SpatialUpdate],
    base_revision: int,
    now: datetime,
    turn_id: UUID | None = None,
    node_id: UUID | None = None,
    sequence_id: UUID | None = None,
) -> Revision:
    """Apply *updates* to the latest revision and stage the result as the
    next one, or :class:`UpdateRefused` (nothing is staged)."""
    row = session.get(SpatialMapORM, str(map_id))
    if row is None:
        raise UpdateRefused(f"no map {map_id}")
    if row.revision != base_revision:
        from afterworlds.mapper.updates import MAP_MOVED_ON

        raise UpdateRefused(MAP_MOVED_ON)
    current = session.get(SpatialMapRevisionORM, (row.map_id, row.revision))
    assert current is not None
    snapshot = Snapshot.model_validate(current.snapshot)
    after = apply_all(snapshot, updates, current_revision=row.revision, seed=row.seed)
    new = SpatialMapRevisionORM(
        map_id=row.map_id,
        revision=row.revision + 1,
        parent_revision=row.revision,
        turn_id=_uuid(turn_id),
        node_id=_uuid(node_id),
        sequence_id=_uuid(sequence_id),
        updates=[u.model_dump(mode="json") for u in updates],
        snapshot=after.model_dump(mode="json"),
        content_hash=content_hash(after),
        created_at=now.isoformat(),
    )
    session.add(new)
    row.revision += 1
    session.flush()
    return _revision(new)
