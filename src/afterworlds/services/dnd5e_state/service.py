"""Production entry points for 2b subject state.

Every production write and every readiness read enforces the subject's exact
recorded binding first (:func:`~.authority.require_current`): stale,
unpublished, quarantined, mismatched or invalid authority is refused with its
typed outcome. Proposed state is then validated against that binding's exact
effective authority, every subject, cast-entry and item reference it records
is checked to exist in the subject's own story, and it is written by
compare-and-swap.

:func:`read_character` / :func:`read_creature` and :func:`recorded_authority`
deliberately do **not** require the binding to be current: they are the
historical-replay and recorded-binding maintenance path, reading the exact
authority a subject was bound to even after the package has moved on.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session

from afterworlds.models.dnd5e_state import (
    CreatureState,
    Dnd5eCharacterState,
    SubjectReference,
)
from afterworlds.persistence.orm.character_sheet import RpgCharacterSheetBaseORM
from afterworlds.persistence.orm.dnd5e_state import (
    Dnd5eCreatureORM,
    Dnd5eItemInstanceORM,
)
from afterworlds.persistence.orm.story_bible import SBCastEntryORM
from afterworlds.services.dnd5e_state import store
from afterworlds.services.dnd5e_state.authority import (
    AuthorityIndex,
    authority_index,
    current_binding,
    require_current,
)
from afterworlds.services.dnd5e_state.errors import (
    FailureCode,
    InvalidStateError,
    StateFailure,
    SubjectNotFoundError,
)
from afterworlds.services.dnd5e_state.store import StoredCharacter, StoredCreature
from afterworlds.services.dnd5e_state.validation import (
    character_readiness,
    creature_readiness,
    validate_character,
    validate_creature,
)

__all__ = [
    "check_references",
    "create_character",
    "create_creature",
    "readiness",
    "read_character",
    "read_creature",
    "recorded_authority",
    "update_character",
    "update_creature",
]


def _checked(failures: tuple[StateFailure, ...]) -> None:
    if failures:
        raise InvalidStateError(failures)


_SUBJECT_TABLES: dict[str, Any] = {
    "character": (RpgCharacterSheetBaseORM, RpgCharacterSheetBaseORM.sheet_id),
    "creature": (Dnd5eCreatureORM, Dnd5eCreatureORM.creature_id),
    "cast_member": (SBCastEntryORM, SBCastEntryORM.cast_id),
    "item": (Dnd5eItemInstanceORM, Dnd5eItemInstanceORM.item_id),
}


def _in_story(session: Session, kind: str, ref: UUID, story_id: UUID) -> bool:
    table, key = _SUBJECT_TABLES[kind]
    found = session.execute(
        sa.select(table.story_id).where(key == str(ref))
    ).scalar_one_or_none()
    return found is not None and str(found) == str(story_id)


def _references(
    session: Session, story_id: UUID, state: Dnd5eCharacterState | CreatureState
) -> tuple[StateFailure, ...]:
    """Every reference the state records must exist in the subject's story."""
    refs: list[tuple[str, str, UUID]] = []

    def subject(path: str, ref: SubjectReference | None) -> None:
        if ref is not None:
            refs.append((path, ref.kind, ref.subject_id))

    def item(path: str, item_id: UUID | None) -> None:
        if item_id is not None:
            refs.append((path, "item", item_id))

    for c in state.conditions or ():
        subject(f"conditions[{c.instance_id}].referent", c.referent)
        item(f"conditions[{c.instance_id}].item_id", c.item_id)
    for e in state.active_effects or ():
        subject(f"active_effects[{e.instance_id}].caster", e.caster)
        for i, target in enumerate(e.targets or ()):
            subject(f"active_effects[{e.instance_id}].targets[{i}]", target)
        item(f"active_effects[{e.instance_id}].item_id", e.item_id)
    for u in state.usage_counters or ():
        item(f"usage_counters[{u.counter_id}].item_id", u.item_id)
    failures = [
        StateFailure(
            FailureCode.INVALID_IDENTITY, path, f"no {kind} {ref} in this story"
        )
        for path, kind, ref in refs
        if not _in_story(session, kind, ref, story_id)
    ]
    summon = state.summon if isinstance(state, CreatureState) else None
    if summon is not None:
        if summon.item_id is not None and not _in_story(
            session, "item", summon.item_id, story_id
        ):
            failures.append(
                StateFailure(
                    FailureCode.INVALID_IDENTITY,
                    "summon.item_id",
                    f"no item {summon.item_id} in this story",
                )
            )
        for name in ("summoner_subject", "controller_subject"):
            ref = getattr(summon, name)
            if ref is not None and not any(
                _in_story(session, kind, ref, story_id)
                for kind in ("character", "creature")
            ):
                failures.append(
                    StateFailure(
                        FailureCode.INVALID_IDENTITY,
                        f"summon.{name}",
                        f"no character or creature {ref} in this story",
                    )
                )
    return tuple(failures)


def check_references(
    session: Session, story_id: UUID, state: Dnd5eCharacterState | CreatureState
) -> None:
    """Refuse (typed) state whose references leave *story_id*."""
    _checked(_references(session, story_id, state))


def _story_of_sheet(session: Session, sheet_id: UUID) -> UUID:
    story = session.execute(
        sa.select(RpgCharacterSheetBaseORM.story_id).where(
            RpgCharacterSheetBaseORM.sheet_id == str(sheet_id)
        )
    ).scalar_one_or_none()
    if story is None:
        raise SubjectNotFoundError(f"no character {sheet_id}")
    return UUID(str(story))


def create_character(
    session: Session,
    sheet_id: UUID,
    package_uuid: UUID,
    state: Dnd5eCharacterState,
    *,
    now: str,
) -> StoredCharacter:
    """Bind a character to the package's current exact binding and store it."""
    binding = current_binding(session, package_uuid, now=now)
    _checked(validate_character(authority_index(session, binding, now=now), state))
    _checked(_references(session, _story_of_sheet(session, sheet_id), state))
    return store.create_character_state(session, sheet_id, state, binding, now=now)


def create_creature(
    session: Session,
    story_id: UUID,
    display_name: str,
    package_uuid: UUID,
    state: CreatureState,
    *,
    now: str,
) -> StoredCreature:
    """A new continuing-creature instance under the current exact binding."""
    binding = current_binding(session, package_uuid, now=now)
    _checked(validate_creature(authority_index(session, binding, now=now), state))
    _checked(_references(session, story_id, state))
    return store.create_creature(
        session, story_id, display_name, state, binding, now=now
    )


def read_character(session: Session, sheet_id: UUID) -> StoredCharacter:
    stored = store.get_character(session, sheet_id)
    if stored is None:
        raise SubjectNotFoundError(f"no character state for {sheet_id}")
    return stored


def read_creature(session: Session, creature_id: UUID) -> StoredCreature:
    stored = store.get_creature(session, creature_id)
    if stored is None:
        raise SubjectNotFoundError(f"no creature {creature_id}")
    return stored


def recorded_authority(
    session: Session, stored: StoredCharacter | StoredCreature, *, now: str
) -> AuthorityIndex:
    """The exact authority a subject's recorded binding names, current or not."""
    return authority_index(session, stored.binding, now=now)


def update_character(
    session: Session,
    sheet_id: UUID,
    state: Dnd5eCharacterState,
    *,
    expected_revision: int,
    now: str,
) -> StoredCharacter:
    """Replace a character's state under its current binding, by CAS."""
    stored = read_character(session, sheet_id)
    require_current(session, stored.binding, now=now)
    _checked(
        validate_character(authority_index(session, stored.binding, now=now), state)
    )
    _checked(_references(session, stored.story_id, state))
    store.save_state(
        session,
        "character",
        sheet_id,
        state,
        expected_revision=expected_revision,
        expected_binding=stored.binding,
        now=now,
    )
    return read_character(session, sheet_id)


def update_creature(
    session: Session,
    creature_id: UUID,
    state: CreatureState,
    *,
    expected_revision: int,
    now: str,
) -> StoredCreature:
    stored = read_creature(session, creature_id)
    require_current(session, stored.binding, now=now)
    _checked(
        validate_creature(authority_index(session, stored.binding, now=now), state)
    )
    _checked(_references(session, stored.story_id, state))
    if state.template_record_key != stored.state.template_record_key:
        raise InvalidStateError(
            (
                StateFailure(
                    FailureCode.INCONSISTENT,
                    "template",
                    "a creature instance never changes template",
                ),
            )
        )
    store.save_state(
        session,
        "creature",
        creature_id,
        state,
        expected_revision=expected_revision,
        expected_binding=stored.binding,
        now=now,
    )
    return read_creature(session, creature_id)


def readiness(
    session: Session, stored: StoredCharacter | StoredCreature, *, now: str
) -> tuple[StateFailure, ...]:
    """Validity plus missing applicable state under the current binding.

    Empty means the recorded inputs are complete and well-formed for the
    binding. It does not mean legal or executable.
    """
    require_current(session, stored.binding, now=now)
    index = authority_index(session, stored.binding, now=now)
    if isinstance(stored, StoredCharacter):
        return validate_character(index, stored.state) + character_readiness(
            index, stored.state
        )
    return validate_creature(index, stored.state) + creature_readiness(stored.state)
