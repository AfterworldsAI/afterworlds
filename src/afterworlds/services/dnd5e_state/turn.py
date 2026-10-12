"""2b state at the turn boundary: the character a turn reads, and the hold.

* :class:`TurnCharacter` is what an adjudicating turn consumes: the stored
  character (state, revision, exact binding) and its readiness under that
  binding. :func:`load_turn_character` refuses a binding that is not current.
* :func:`require_unchanged` is the commit-time recheck: a turn's writes commit
  only if the character's revision and binding are what the turn read.
* :class:`RpgTurnHold` brackets an RPG turn with a durable lease
  (:mod:`.leases`), and after the turn's transaction ends lets held shared
  changes activate and held adoptions proceed (:func:`after_events`).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.persistence.orm.dnd5e_state import (
    Dnd5eCharacterStateORM,
)
from afterworlds.persistence.orm.rules_authority import SharedRuleChangeORM
from afterworlds.services.dnd5e_state import adoption, leases, shared_changes
from afterworlds.services.dnd5e_state.authority import AuthorityIndex, authority_index
from afterworlds.services.dnd5e_state.errors import (
    StaleRevisionError,
    StateFailure,
)
from afterworlds.services.dnd5e_state.holdings import (
    Holder,
    HolderKind,
    ItemInstance,
    items_held_by,
)
from afterworlds.services.dnd5e_state.service import read_character, readiness
from afterworlds.services.dnd5e_state.store import StoredCharacter

__all__ = [
    "RpgTurnHold",
    "TurnCharacter",
    "after_events",
    "load_turn_character",
    "require_unchanged",
]

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class TurnCharacter:
    stored: StoredCharacter
    #: Missing or invalid state under the binding; empty when ready.
    readiness: tuple[StateFailure, ...]
    #: The item instances the character holds.
    items: tuple[ItemInstance, ...] = ()
    #: The exact effective authority the character's binding names (CRD Issue
    #: 15c): the only authority adjudication reads for this character.
    index: AuthorityIndex | None = None

    @property
    def sheet_id(self) -> UUID:
        return self.stored.sheet_id

    @property
    def ready(self) -> bool:
        return not self.readiness


def load_turn_character(session: Session, sheet_id: UUID, *, now: str) -> TurnCharacter:
    """The character a turn reads; refuses a non-current binding (typed)."""
    stored = read_character(session, sheet_id)
    items = items_held_by(session, Holder(HolderKind.CHARACTER, stored.sheet_id))
    ready = readiness(session, stored, now=now)
    index = authority_index(session, stored.binding, now=now)
    return TurnCharacter(stored, ready, items, index)


def require_unchanged(
    session: Session, sheet_id: UUID, revision: int, binding: RulesPackageBinding
) -> None:
    """Refuse a commit computed against a superseded revision or binding."""
    row = session.execute(
        sa.select(
            Dnd5eCharacterStateORM.revision,
            Dnd5eCharacterStateORM.package_uuid,
            Dnd5eCharacterStateORM.release_version,
            Dnd5eCharacterStateORM.projection_uuid,
            Dnd5eCharacterStateORM.override_set_uuid,
        ).where(Dnd5eCharacterStateORM.sheet_id == str(sheet_id))
    ).one_or_none()
    expected = (
        revision,
        str(binding.package_uuid),
        binding.release_version,
        str(binding.mechanical_projection_uuid),
        str(binding.override_set_uuid),
    )
    if row is None or tuple(row) != expected:
        raise StaleRevisionError(
            f"character {sheet_id} changed after this turn read it; its work "
            "cannot commit"
        )


def _uses(session: Session, story_id: UUID, package: str, release: str) -> bool:
    """Whether the story uses (package, release): the same rule that decides
    which stories a change affects (:func:`shared_changes.affected_stories`)."""
    return str(story_id) in shared_changes.affected_stories(session, package, release)


def after_events(factory: sessionmaker[Session], story_id: UUID, *, now: str) -> None:
    """After a story's event resolved: activate what can, then adopt.

    Each held shared change on a package the story uses gets its own
    transaction; then the story's held adoptions are processed in another.
    A change that still finds affected events simply stays held.
    """
    with factory() as session:
        held = [
            change_id
            for change_id, pkg, release in session.execute(
                sa.select(
                    SharedRuleChangeORM.change_id,
                    SharedRuleChangeORM.package_uuid,
                    SharedRuleChangeORM.release_version,
                )
                .where(
                    SharedRuleChangeORM.status == shared_changes.ChangeStatus.HELD.value
                )
                .order_by(SharedRuleChangeORM.requested_at)
            )
            if _uses(session, story_id, pkg, release)
        ]
    for change_id in held:
        with factory() as session, session.begin():
            shared_changes.activate(session, change_id, now=now)
    with factory() as session, session.begin():
        adoption.process_held(session, story_id, now=now)


class RpgTurnHold:
    """The durable in-flight marker and post-turn processing for RPG turns."""

    def __init__(
        self, factory: sessionmaker[Session], clock: Callable[[], str]
    ) -> None:
        self._factory = factory
        self._clock = clock

    def acquire(self, story_id: UUID) -> str:
        return leases.acquire(self._factory, story_id, now=self._clock())

    def recheck(self, session: Session, character: TurnCharacter) -> None:
        """The commit-time recheck: refuse work computed against a superseded
        revision or binding (see :func:`require_unchanged`)."""
        require_unchanged(
            session,
            character.sheet_id,
            character.stored.revision,
            character.stored.binding,
        )

    def finish(self, story_id: UUID, lease_id: str) -> None:
        """Release the lease (idempotent), then process what it held back.

        Post-turn processing never changes the turn's outcome: a failure is
        logged and the held change or adoption stays visibly held, to be
        processed again after the story's next event.
        """
        leases.release_committed(self._factory, lease_id)
        try:
            after_events(self._factory, story_id, now=self._clock())
        except Exception:  # noqa: BLE001
            _log.exception("post-turn hold processing failed for story %s", story_id)
