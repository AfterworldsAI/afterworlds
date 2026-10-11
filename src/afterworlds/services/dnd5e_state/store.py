"""Persistence of 2b subject state: typed reads and compare-and-swap writes.

Every write names the revision *and* the binding it was computed against, and
commits only if both are still current in the database: a conditional
``UPDATE ... WHERE revision = :expected AND <binding> = :expected``. Work
computed against superseded state therefore cannot commit, across real
connections, without any lock. Reads parse the document into its typed model
and never fill in what is not recorded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session

from afterworlds.models.dnd5e_state import CreatureState, Dnd5eCharacterState
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.persistence.orm.character_sheet import RpgCharacterSheetBaseORM
from afterworlds.persistence.orm.dnd5e_state import (
    Dnd5eBindingHistoryORM,
    Dnd5eCharacterStateORM,
    Dnd5eCreatureORM,
)
from afterworlds.services.dnd5e_state.errors import (
    StaleRevisionError,
    SubjectNotFoundError,
)

__all__ = [
    "StoredCharacter",
    "StoredCreature",
    "binding_history",
    "create_character_state",
    "create_creature",
    "get_character",
    "get_creature",
    "rebind",
    "save_state",
]


@dataclass(frozen=True)
class StoredCharacter:
    sheet_id: UUID
    story_id: UUID
    character_name: str
    revision: int
    binding: RulesPackageBinding
    state: Dnd5eCharacterState

    @property
    def subject_id(self) -> UUID:
        return self.sheet_id


@dataclass(frozen=True)
class StoredCreature:
    creature_id: UUID
    story_id: UUID
    display_name: str
    revision: int
    binding: RulesPackageBinding
    state: CreatureState

    @property
    def subject_id(self) -> UUID:
        return self.creature_id


def _binding_of(row: Any) -> RulesPackageBinding:
    return RulesPackageBinding(
        package_uuid=UUID(row.package_uuid),
        release_version=row.release_version,
        mechanical_projection_uuid=UUID(row.projection_uuid),
        override_set_uuid=UUID(row.override_set_uuid),
    )


def _binding_values(binding: RulesPackageBinding) -> dict[str, str]:
    return {
        "package_uuid": str(binding.package_uuid),
        "release_version": binding.release_version,
        "projection_uuid": str(binding.mechanical_projection_uuid),
        "override_set_uuid": str(binding.override_set_uuid),
    }


def _history(
    session: Session,
    *,
    kind: str,
    subject_id: str,
    story_id: str,
    event: str,
    binding: RulesPackageBinding,
    revision: int,
    request_id: str | None,
    now: str,
) -> None:
    session.add(
        Dnd5eBindingHistoryORM(
            history_id=str(uuid4()),
            subject_kind=kind,
            subject_id=subject_id,
            story_id=story_id,
            event=event,
            state_revision=revision,
            adoption_request_id=request_id,
            recorded_at=now,
            **_binding_values(binding),
        )
    )


def create_character_state(
    session: Session,
    sheet_id: UUID,
    state: Dnd5eCharacterState,
    binding: RulesPackageBinding,
    *,
    now: str,
) -> StoredCharacter:
    base = session.get(RpgCharacterSheetBaseORM, str(sheet_id))
    if base is None:
        raise SubjectNotFoundError(f"no character {sheet_id}")
    session.add(
        Dnd5eCharacterStateORM(
            sheet_id=str(sheet_id),
            story_id=base.story_id,
            revision=1,
            document=state.model_dump(mode="json"),
            updated_at=now,
            **_binding_values(binding),
        )
    )
    _history(
        session,
        kind="character",
        subject_id=str(sheet_id),
        story_id=base.story_id,
        event="bound",
        binding=binding,
        revision=1,
        request_id=None,
        now=now,
    )
    session.flush()
    stored = get_character(session, sheet_id)
    assert stored is not None
    return stored


def get_character(session: Session, sheet_id: UUID) -> StoredCharacter | None:
    row = session.execute(
        sa.select(Dnd5eCharacterStateORM, RpgCharacterSheetBaseORM.character_name)
        .join(
            RpgCharacterSheetBaseORM,
            RpgCharacterSheetBaseORM.sheet_id == Dnd5eCharacterStateORM.sheet_id,
        )
        .where(Dnd5eCharacterStateORM.sheet_id == str(sheet_id))
        .execution_options(populate_existing=True)
    ).one_or_none()
    if row is None:
        return None
    state_row, name = row
    return StoredCharacter(
        sheet_id=UUID(state_row.sheet_id),
        story_id=UUID(state_row.story_id),
        character_name=name,
        revision=state_row.revision,
        binding=_binding_of(state_row),
        state=Dnd5eCharacterState.model_validate(state_row.document),
    )


def create_creature(
    session: Session,
    story_id: UUID,
    display_name: str,
    state: CreatureState,
    binding: RulesPackageBinding,
    *,
    now: str,
) -> StoredCreature:
    creature_id = str(uuid4())
    session.add(
        Dnd5eCreatureORM(
            creature_id=creature_id,
            story_id=str(story_id),
            display_name=display_name,
            created_at=now,
            revision=1,
            document=state.model_dump(mode="json"),
            updated_at=now,
            **_binding_values(binding),
        )
    )
    _history(
        session,
        kind="creature",
        subject_id=creature_id,
        story_id=str(story_id),
        event="bound",
        binding=binding,
        revision=1,
        request_id=None,
        now=now,
    )
    session.flush()
    stored = get_creature(session, UUID(creature_id))
    assert stored is not None
    return stored


def get_creature(session: Session, creature_id: UUID) -> StoredCreature | None:
    row = session.execute(
        sa.select(Dnd5eCreatureORM)
        .where(Dnd5eCreatureORM.creature_id == str(creature_id))
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()
    if row is None:
        return None
    return StoredCreature(
        creature_id=UUID(row.creature_id),
        story_id=UUID(row.story_id),
        display_name=row.display_name,
        revision=row.revision,
        binding=_binding_of(row),
        state=CreatureState.model_validate(row.document),
    )


def _table(kind: str) -> tuple[Any, Any]:
    if kind == "character":
        return Dnd5eCharacterStateORM, Dnd5eCharacterStateORM.sheet_id
    if kind == "creature":
        return Dnd5eCreatureORM, Dnd5eCreatureORM.creature_id
    raise ValueError(f"unknown subject kind {kind!r}")


def _cas(
    session: Session,
    kind: str,
    subject_id: UUID,
    *,
    expected_revision: int,
    expected_binding: RulesPackageBinding,
    values: dict[str, Any],
) -> int:
    table, key = _table(kind)
    expected = _binding_values(expected_binding)
    result = session.execute(
        sa.update(table)
        .where(key == str(subject_id))
        .where(table.revision == expected_revision)
        .where(table.package_uuid == expected["package_uuid"])
        .where(table.release_version == expected["release_version"])
        .where(table.projection_uuid == expected["projection_uuid"])
        .where(table.override_set_uuid == expected["override_set_uuid"])
        .values(revision=expected_revision + 1, **values)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:  # type: ignore[attr-defined]
        raise StaleRevisionError(
            f"{kind} {subject_id}: revision {expected_revision} under the "
            "expected binding is no longer current"
        )
    return expected_revision + 1


def save_state(
    session: Session,
    kind: str,
    subject_id: UUID,
    state: Dnd5eCharacterState | CreatureState,
    *,
    expected_revision: int,
    expected_binding: RulesPackageBinding,
    now: str,
) -> int:
    """Replace a subject's document; returns the new revision."""
    expected_type = Dnd5eCharacterState if kind == "character" else CreatureState
    if not isinstance(state, expected_type):
        raise TypeError(f"{kind} state must be {expected_type.__name__}")
    return _cas(
        session,
        kind,
        subject_id,
        expected_revision=expected_revision,
        expected_binding=expected_binding,
        values={"document": state.model_dump(mode="json"), "updated_at": now},
    )


def rebind(
    session: Session,
    kind: str,
    subject_id: UUID,
    story_id: UUID,
    *,
    expected_revision: int,
    from_binding: RulesPackageBinding,
    to_binding: RulesPackageBinding,
    request_id: str,
    now: str,
) -> int:
    """Move a subject to *to_binding*, keeping its document; append history."""
    revision = _cas(
        session,
        kind,
        subject_id,
        expected_revision=expected_revision,
        expected_binding=from_binding,
        values={**_binding_values(to_binding), "updated_at": now},
    )
    _history(
        session,
        kind=kind,
        subject_id=str(subject_id),
        story_id=str(story_id),
        event="adopted",
        binding=to_binding,
        revision=revision,
        request_id=request_id,
        now=now,
    )
    session.flush()
    return revision


def binding_history(
    session: Session, subject_id: UUID
) -> tuple[tuple[str, RulesPackageBinding, int], ...]:
    """(event, binding, state revision) for every binding held, oldest first."""
    rows = (
        session.execute(
            sa.select(Dnd5eBindingHistoryORM)
            .where(Dnd5eBindingHistoryORM.subject_id == str(subject_id))
            .order_by(
                Dnd5eBindingHistoryORM.recorded_at,
                Dnd5eBindingHistoryORM.state_revision,
            )
        )
        .scalars()
        .all()
    )
    return tuple((r.event, _binding_of(r), r.state_revision) for r in rows)
