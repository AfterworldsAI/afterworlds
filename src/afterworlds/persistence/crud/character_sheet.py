"""CRUD for the RPG character identity row (``rpg_character_sheet_bases``).

A character's mechanical state lives in the CRD Issue 2b typed state store
(:mod:`afterworlds.services.dnd5e_state.store`), never here.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.models.character_sheet import RpgCharacterSheetBase
from afterworlds.persistence.orm.character_sheet import RpgCharacterSheetBaseORM


def _base_orm_to_model(row: RpgCharacterSheetBaseORM) -> RpgCharacterSheetBase:
    return RpgCharacterSheetBase(
        sheet_id=UUID(row.sheet_id),
        story_id=UUID(row.story_id),
        character_name=row.character_name,
        created_at=row.created_at,  # type: ignore[arg-type]
        updated_at=row.updated_at,  # type: ignore[arg-type]
    )


def create_rpg_base_sheet(
    session: Session, sheet: RpgCharacterSheetBase
) -> RpgCharacterSheetBase:
    """Persist a new RpgCharacterSheetBase and return it."""
    row = RpgCharacterSheetBaseORM(
        sheet_id=str(sheet.sheet_id),
        story_id=str(sheet.story_id),
        character_name=sheet.character_name,
        created_at=sheet.created_at.isoformat(),
        updated_at=sheet.updated_at.isoformat(),
    )
    session.add(row)
    session.flush()
    return _base_orm_to_model(row)


def get_rpg_base_sheet(
    session: Session, sheet_id: UUID
) -> RpgCharacterSheetBase | None:
    """Return an RpgCharacterSheetBase by primary key, or None."""
    row = session.get(RpgCharacterSheetBaseORM, str(sheet_id))
    if row is None:
        return None
    return _base_orm_to_model(row)


def update_rpg_base_sheet(
    session: Session, sheet: RpgCharacterSheetBase
) -> RpgCharacterSheetBase | None:
    """Update mutable fields on an existing base sheet."""
    row = session.get(RpgCharacterSheetBaseORM, str(sheet.sheet_id))
    if row is None:
        return None
    row.character_name = sheet.character_name
    row.updated_at = sheet.updated_at.isoformat()
    session.flush()
    return _base_orm_to_model(row)


def delete_rpg_base_sheet(session: Session, sheet_id: UUID) -> bool:
    """Delete a base sheet (cascades to its typed state).  True if deleted."""
    row = session.get(RpgCharacterSheetBaseORM, str(sheet_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True
