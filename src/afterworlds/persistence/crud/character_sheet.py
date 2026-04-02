"""CRUD operations for the RPG character sheet two-table chain."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.models.character_sheet import (
    Dnd5eCharacterSheet,
    RpgCharacterSheetBase,
)
from afterworlds.persistence.orm.character_sheet import (
    Dnd5eCharacterSheetORM,
    RpgCharacterSheetBaseORM,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _base_orm_to_model(row: RpgCharacterSheetBaseORM) -> RpgCharacterSheetBase:
    return RpgCharacterSheetBase(
        sheet_id=UUID(row.sheet_id),
        story_id=UUID(row.story_id),
        rules_package_id=row.rules_package_id,
        character_name=row.character_name,
        created_at=row.created_at,  # type: ignore[arg-type]
        updated_at=row.updated_at,  # type: ignore[arg-type]
    )


def _dnd5e_orm_to_model(
    base_row: RpgCharacterSheetBaseORM,
    dnd_row: Dnd5eCharacterSheetORM,
) -> Dnd5eCharacterSheet:
    # spell_slots serialised as {"1": {"total": 2, "used": 0}, ...}
    # Pydantic handles str→int key coercion on model_validate.
    return Dnd5eCharacterSheet.model_validate(
        {
            "sheet_id": base_row.sheet_id,
            "story_id": base_row.story_id,
            "rules_package_id": base_row.rules_package_id,
            "character_name": base_row.character_name,
            "created_at": base_row.created_at,
            "updated_at": base_row.updated_at,
            "character_class": dnd_row.character_class,
            "background": dnd_row.background,
            "level": dnd_row.level,
            "ability_scores": dnd_row.ability_scores,
            "skills": dnd_row.skills,
            "equipment": dnd_row.equipment,
            "current_hp": dnd_row.current_hp,
            "maximum_hp": dnd_row.maximum_hp,
            "spell_slots": dnd_row.spell_slots,
        }
    )


# ---------------------------------------------------------------------------
# RpgCharacterSheetBase CRUD
# ---------------------------------------------------------------------------


def create_rpg_base_sheet(
    session: Session, sheet: RpgCharacterSheetBase
) -> RpgCharacterSheetBase:
    """Persist a new RpgCharacterSheetBase and return it."""
    row = RpgCharacterSheetBaseORM(
        sheet_id=str(sheet.sheet_id),
        story_id=str(sheet.story_id),
        rules_package_id=sheet.rules_package_id,
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
    """Delete a base sheet (cascades to dnd5e row).  Returns True if deleted."""
    row = session.get(RpgCharacterSheetBaseORM, str(sheet_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True


# ---------------------------------------------------------------------------
# Dnd5eCharacterSheet CRUD
# ---------------------------------------------------------------------------


def create_dnd5e_sheet(
    session: Session, sheet: Dnd5eCharacterSheet
) -> Dnd5eCharacterSheet:
    """Persist base + dnd5e rows and return the complete sheet."""
    base_row = session.get(RpgCharacterSheetBaseORM, str(sheet.sheet_id))
    if base_row is None:
        raise ValueError(
            f"No RpgCharacterSheetBase row found for sheet_id={sheet.sheet_id!r}. "
            "Call create_rpg_base_sheet before create_dnd5e_sheet."
        )

    # Serialize spell_slots: dict[int, SpellSlotLevel] → dict[str, dict]
    spell_slots_serialised = {
        str(level): slot.model_dump() for level, slot in sheet.spell_slots.items()
    }

    dnd_row = Dnd5eCharacterSheetORM(
        sheet_id=str(sheet.sheet_id),
        character_class=sheet.character_class,
        background=sheet.background,
        level=sheet.level,
        ability_scores=sheet.ability_scores.model_dump(),
        skills=dict(sheet.skills),
        equipment=list(sheet.equipment),
        current_hp=sheet.current_hp,
        maximum_hp=sheet.maximum_hp,
        spell_slots=spell_slots_serialised,
    )
    session.add(dnd_row)
    session.flush()
    return _dnd5e_orm_to_model(base_row, dnd_row)


def get_dnd5e_sheet(session: Session, sheet_id: UUID) -> Dnd5eCharacterSheet | None:
    """Return a Dnd5eCharacterSheet by primary key, or None."""
    dnd_row = session.get(Dnd5eCharacterSheetORM, str(sheet_id))
    if dnd_row is None:
        return None
    base_row = session.get(RpgCharacterSheetBaseORM, str(sheet_id))
    if base_row is None:
        return None
    return _dnd5e_orm_to_model(base_row, dnd_row)


def update_dnd5e_sheet(
    session: Session, sheet: Dnd5eCharacterSheet
) -> Dnd5eCharacterSheet | None:
    """Update mutable fields on an existing Dnd5eCharacterSheet."""
    dnd_row = session.get(Dnd5eCharacterSheetORM, str(sheet.sheet_id))
    if dnd_row is None:
        return None
    base_row = session.get(RpgCharacterSheetBaseORM, str(sheet.sheet_id))
    if base_row is None:
        return None

    spell_slots_serialised = {
        str(level): slot.model_dump() for level, slot in sheet.spell_slots.items()
    }

    base_row.character_name = sheet.character_name
    base_row.updated_at = sheet.updated_at.isoformat()
    dnd_row.character_class = sheet.character_class
    dnd_row.background = sheet.background
    dnd_row.level = sheet.level
    dnd_row.ability_scores = sheet.ability_scores.model_dump()
    dnd_row.skills = dict(sheet.skills)
    dnd_row.equipment = list(sheet.equipment)
    dnd_row.current_hp = sheet.current_hp
    dnd_row.maximum_hp = sheet.maximum_hp
    dnd_row.spell_slots = spell_slots_serialised
    session.flush()
    return _dnd5e_orm_to_model(base_row, dnd_row)


def delete_dnd5e_sheet(session: Session, sheet_id: UUID) -> bool:
    """Delete a Dnd5eCharacterSheet (and base row).  Returns True if deleted."""
    base_row = session.get(RpgCharacterSheetBaseORM, str(sheet_id))
    if base_row is None:
        return False
    session.delete(base_row)
    session.flush()
    return True
