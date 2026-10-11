"""Production entry points for 2b subject state.

Every production write and every readiness read enforces the subject's exact
recorded binding first (:func:`~.authority.require_current`): stale,
unpublished, quarantined, mismatched or invalid authority is refused with its
typed outcome. Proposed state is then validated against that binding's exact
effective authority and written by compare-and-swap.

:func:`read_character` / :func:`read_creature` and :func:`recorded_authority`
deliberately do **not** require the binding to be current: they are the
historical-replay and recorded-binding maintenance path, reading the exact
authority a subject was bound to even after the package has moved on.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.models.dnd5e_state import CreatureState, Dnd5eCharacterState
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
