"""CRUD operations for WorldState and CharacterState with partition-aware updates."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.models.state import (
    CharacterState,
    CharacterStateDynamicPartition,
    CharacterStateStaticPartition,
    WorldState,
    WorldStateDynamicPartition,
    WorldStateStaticPartition,
)
from afterworlds.persistence.orm.state import CharacterStateORM, WorldStateORM

# ---------------------------------------------------------------------------
# WorldState helpers
# ---------------------------------------------------------------------------


def _world_state_orm_to_model(row: WorldStateORM) -> WorldState:
    return WorldState(
        world_state_id=UUID(row.world_state_id),
        story_id=UUID(row.story_id),
        static=WorldStateStaticPartition(
            setting_name=row.static_setting_name,
            world_rules=list(row.static_world_rules),
            geography=row.static_geography,
            time_period=row.static_time_period,
        ),
        dynamic=WorldStateDynamicPartition(
            current_location=row.dynamic_current_location,
            time_of_day=row.dynamic_time_of_day,
            weather=row.dynamic_weather,
            faction_standings=dict(row.dynamic_faction_standings),
        ),
        updated_at=row.updated_at,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# WorldState CRUD
# ---------------------------------------------------------------------------


def create_world_state(session: Session, ws: WorldState) -> WorldState:
    """Persist a new WorldState and return it."""
    row = WorldStateORM(
        world_state_id=str(ws.world_state_id),
        story_id=str(ws.story_id),
        static_setting_name=ws.static.setting_name,
        static_world_rules=list(ws.static.world_rules),
        static_geography=ws.static.geography,
        static_time_period=ws.static.time_period,
        dynamic_current_location=ws.dynamic.current_location,
        dynamic_time_of_day=ws.dynamic.time_of_day,
        dynamic_weather=ws.dynamic.weather,
        dynamic_faction_standings=dict(ws.dynamic.faction_standings),
        updated_at=ws.updated_at.isoformat(),
    )
    session.add(row)
    session.flush()
    return _world_state_orm_to_model(row)


def get_world_state(session: Session, world_state_id: UUID) -> WorldState | None:
    """Return a WorldState by primary key, or None."""
    row = session.get(WorldStateORM, str(world_state_id))
    if row is None:
        return None
    return _world_state_orm_to_model(row)


def get_world_state_by_story(session: Session, story_id: UUID) -> WorldState | None:
    """Return the WorldState for a given story, or None."""
    row = session.scalars(
        select(WorldStateORM).where(WorldStateORM.story_id == str(story_id))
    ).first()
    if row is None:
        return None
    return _world_state_orm_to_model(row)


def update_world_state_static(
    session: Session,
    story_id: UUID,
    static_data: WorldStateStaticPartition,
) -> WorldState | None:
    """Update only the static partition columns.  Dynamic columns are untouched."""
    row = session.scalars(
        select(WorldStateORM).where(WorldStateORM.story_id == str(story_id))
    ).first()
    if row is None:
        return None
    row.static_setting_name = static_data.setting_name
    row.static_world_rules = list(static_data.world_rules)
    row.static_geography = static_data.geography
    row.static_time_period = static_data.time_period
    row.updated_at = datetime.now(tz=timezone.utc).isoformat()
    session.flush()
    return _world_state_orm_to_model(row)


def update_world_state_dynamic(
    session: Session,
    story_id: UUID,
    dynamic_data: WorldStateDynamicPartition,
) -> WorldState | None:
    """Update only the dynamic partition columns.  Static columns are untouched."""
    row = session.scalars(
        select(WorldStateORM).where(WorldStateORM.story_id == str(story_id))
    ).first()
    if row is None:
        return None
    row.dynamic_current_location = dynamic_data.current_location
    row.dynamic_time_of_day = dynamic_data.time_of_day
    row.dynamic_weather = dynamic_data.weather
    row.dynamic_faction_standings = dict(dynamic_data.faction_standings)
    row.updated_at = datetime.now(tz=timezone.utc).isoformat()
    session.flush()
    return _world_state_orm_to_model(row)


def delete_world_state(session: Session, world_state_id: UUID) -> bool:
    """Delete a WorldState.  Returns True if deleted."""
    row = session.get(WorldStateORM, str(world_state_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True


# ---------------------------------------------------------------------------
# CharacterState helpers
# ---------------------------------------------------------------------------


def _char_state_orm_to_model(row: CharacterStateORM) -> CharacterState:
    return CharacterState(
        character_state_id=UUID(row.character_state_id),
        story_id=UUID(row.story_id),
        static=CharacterStateStaticPartition(
            character_name=row.static_character_name,
        ),
        dynamic=CharacterStateDynamicPartition(
            current_location=row.dynamic_current_location,
            status_effects=list(row.dynamic_status_effects),
            relationship_meters=dict(row.dynamic_relationship_meters),
            inventory=list(row.dynamic_inventory),
        ),
        updated_at=row.updated_at,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# CharacterState CRUD
# ---------------------------------------------------------------------------


def create_character_state(session: Session, cs: CharacterState) -> CharacterState:
    """Persist a new CharacterState and return it."""
    row = CharacterStateORM(
        character_state_id=str(cs.character_state_id),
        story_id=str(cs.story_id),
        static_character_name=cs.static.character_name,
        dynamic_current_location=cs.dynamic.current_location,
        dynamic_status_effects=list(cs.dynamic.status_effects),
        dynamic_relationship_meters=dict(cs.dynamic.relationship_meters),
        dynamic_inventory=list(cs.dynamic.inventory),
        updated_at=cs.updated_at.isoformat(),
    )
    session.add(row)
    session.flush()
    return _char_state_orm_to_model(row)


def get_character_state(
    session: Session, character_state_id: UUID
) -> CharacterState | None:
    """Return a CharacterState by primary key, or None."""
    row = session.get(CharacterStateORM, str(character_state_id))
    if row is None:
        return None
    return _char_state_orm_to_model(row)


def get_character_state_by_story(
    session: Session, story_id: UUID
) -> CharacterState | None:
    """Return the CharacterState for a given story, or None."""
    row = session.scalars(
        select(CharacterStateORM).where(CharacterStateORM.story_id == str(story_id))
    ).first()
    if row is None:
        return None
    return _char_state_orm_to_model(row)


def update_character_state_static(
    session: Session,
    story_id: UUID,
    static_data: CharacterStateStaticPartition,
) -> CharacterState | None:
    """Update only the static partition columns.  Dynamic columns are untouched."""
    row = session.scalars(
        select(CharacterStateORM).where(CharacterStateORM.story_id == str(story_id))
    ).first()
    if row is None:
        return None
    row.static_character_name = static_data.character_name
    row.updated_at = datetime.now(tz=timezone.utc).isoformat()
    session.flush()
    return _char_state_orm_to_model(row)


def update_character_state_dynamic(
    session: Session,
    story_id: UUID,
    dynamic_data: CharacterStateDynamicPartition,
) -> CharacterState | None:
    """Update only the dynamic partition columns.  Static columns are untouched."""
    row = session.scalars(
        select(CharacterStateORM).where(CharacterStateORM.story_id == str(story_id))
    ).first()
    if row is None:
        return None
    row.dynamic_current_location = dynamic_data.current_location
    row.dynamic_status_effects = list(dynamic_data.status_effects)
    row.dynamic_relationship_meters = dict(dynamic_data.relationship_meters)
    row.dynamic_inventory = list(dynamic_data.inventory)
    row.updated_at = datetime.now(tz=timezone.utc).isoformat()
    session.flush()
    return _char_state_orm_to_model(row)


def delete_character_state(session: Session, character_state_id: UUID) -> bool:
    """Delete a CharacterState.  Returns True if deleted."""
    row = session.get(CharacterStateORM, str(character_state_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True
