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

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, replace
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.ingestion.mechanical.representation import ConditionKind
from afterworlds.models.enums import ConditionVisibility
from afterworlds.models.rpg import SheetEffect
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.persistence.orm.dnd5e_state import (
    Dnd5eCharacterStateORM,
    Dnd5eCreatureORM,
)
from afterworlds.persistence.orm.rules_authority import SharedRuleChangeORM
from afterworlds.services.dnd5e_state import adoption, leases, shared_changes
from afterworlds.services.dnd5e_state.authority import AuthorityIndex, authority_index
from afterworlds.services.dnd5e_state.effects import apply_effects
from afterworlds.services.dnd5e_state.errors import (
    StaleRevisionError,
    StateFailure,
    SubjectNotFoundError,
)
from afterworlds.services.dnd5e_state.holdings import (
    Holder,
    HolderKind,
    ItemInstance,
    items_held_by,
)
from afterworlds.services.dnd5e_state.service import (
    read_character,
    read_creature,
    readiness,
)
from afterworlds.services.dnd5e_state.store import StoredCharacter, StoredCreature

__all__ = [
    "RpgTurnHold",
    "TurnCharacter",
    "TurnCreature",
    "TurnSubject",
    "advanced",
    "after_events",
    "load_turn_character",
    "load_turn_creature",
    "require_holdings_unchanged",
    "require_unchanged",
    "with_effects",
    "with_possible",
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
    def subject_id(self) -> UUID:
        return self.stored.sheet_id

    @property
    def ready(self) -> bool:
        return not self.readiness


@dataclass(frozen=True)
class TurnCreature:
    """A continuing creature a turn reads as an independent subject (CRD Issue
    15c): its own state, revision and exact binding, held items and authority.
    """

    stored: StoredCreature
    readiness: tuple[StateFailure, ...]
    items: tuple[ItemInstance, ...] = ()
    index: AuthorityIndex | None = None

    @property
    def subject_id(self) -> UUID:
        return self.stored.creature_id

    @property
    def ready(self) -> bool:
        return not self.readiness


#: One subject of a turn: the acting character, or another character or
#: creature an operation targets.
TurnSubject = TurnCharacter | TurnCreature


def advanced(
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
    effects: tuple[SheetEffect, ...],
) -> tuple[TurnCharacter, dict[tuple[str, str], TurnSubject]]:
    """The turn's view of *actor* and *subjects* after *effects*, in memory.

    Each keeps the revision and binding it was read at, so the commit-time
    recheck is unchanged; only later operations of the same turn read the
    advanced state. An effect without a subject is the actor's.
    """
    grouped: dict[tuple[str, str], list[SheetEffect]] = {}
    for effect in effects:
        key = (
            ("character", str(actor.subject_id))
            if effect.subject_id is None
            else (str(effect.subject_kind), str(effect.subject_id))
        )
        grouped.setdefault(key, []).append(effect)
    out = dict(subjects)
    for key, group in grouped.items():
        if key == ("character", str(actor.subject_id)):
            actor = with_effects(actor, group)
        elif key in out:
            out[key] = with_effects(out[key], group)
        else:
            raise ValueError(f"an effect names {key}, which this turn did not read")
    return actor, out


def with_effects[T: TurnSubject](subject: T, effects: list[SheetEffect]) -> T:
    """*subject* after *effects*, in memory; revision and binding as read."""
    stored: StoredCharacter | StoredCreature = subject.stored
    state = apply_effects(stored.state, tuple(effects))
    stored = replace(stored, state=state)  # type: ignore[arg-type]
    return replace(subject, stored=stored)  # type: ignore[arg-type]


def with_possible(
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
    possible: dict[tuple[str, str], set[ConditionKind]],
) -> tuple[TurnCharacter, dict[tuple[str, str], TurnSubject]]:
    """*actor* and *subjects* with every condition in *possible* present, for
    the preflight: a condition the subject already has is not added twice."""
    present = {key: _conditions_of(actor, subjects, key) for key in possible}
    effects = tuple(
        SheetEffect(
            target=kind.value,
            operation="apply_condition",
            value_json=json.dumps(
                {
                    "instance_id": f"possible:{kind.value}",
                    "condition": kind.value,
                    "visibility": ConditionVisibility.VISIBLE.value,
                    **({"level": 1} if kind is ConditionKind.EXHAUSTION else {}),
                }
            ),
            subject_kind=key[0],  # type: ignore[arg-type]
            subject_id=key[1],  # type: ignore[arg-type]
        )
        for key, kinds in possible.items()
        for kind in sorted(kinds)
        if (have := present[key]) is not None and kind not in have
    )
    return advanced(actor, subjects, effects)


def _conditions_of(
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
    key: tuple[str, str],
) -> set[ConditionKind] | None:
    """The subject's recorded conditions, or ``None`` when it records none
    (its operations refuse that as missing state)."""
    subject = actor if key == ("character", str(actor.subject_id)) else subjects[key]
    conditions = subject.stored.state.conditions
    return None if conditions is None else {c.condition for c in conditions}


def load_turn_creature(
    session: Session, story_id: UUID, creature_id: UUID, *, now: str
) -> TurnCreature:
    """A creature of *story_id*, read with its exact binding; refuses a
    creature of another story or a non-current binding (typed)."""
    stored = read_creature(session, creature_id)
    if stored.story_id != story_id:
        raise SubjectNotFoundError(f"creature {creature_id} is not in story {story_id}")
    items = items_held_by(session, Holder(HolderKind.CREATURE, stored.creature_id))
    ready = readiness(session, stored, now=now)
    index = authority_index(session, stored.binding, now=now)
    return TurnCreature(stored, ready, items, index)


def load_turn_character(session: Session, sheet_id: UUID, *, now: str) -> TurnCharacter:
    """The character a turn reads; refuses a non-current binding (typed)."""
    stored = read_character(session, sheet_id)
    items = items_held_by(session, Holder(HolderKind.CHARACTER, stored.sheet_id))
    ready = readiness(session, stored, now=now)
    index = authority_index(session, stored.binding, now=now)
    return TurnCharacter(stored, ready, items, index)


def require_unchanged(
    session: Session,
    sheet_id: UUID,
    revision: int,
    binding: RulesPackageBinding,
    *,
    kind: str = "character",
) -> None:
    """Refuse a commit computed against a superseded revision or binding, for
    a character (by sheet id) or a creature (``kind="creature"``)."""
    table: type[Dnd5eCharacterStateORM] | type[Dnd5eCreatureORM]
    if kind == "creature":
        table, key = Dnd5eCreatureORM, Dnd5eCreatureORM.creature_id
    else:
        table, key = Dnd5eCharacterStateORM, Dnd5eCharacterStateORM.sheet_id
    row = session.execute(
        sa.select(
            table.revision,
            table.package_uuid,
            table.release_version,
            table.projection_uuid,
            table.override_set_uuid,
        ).where(key == str(sheet_id))
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
            f"{kind} {sheet_id} changed after this turn read it; its work "
            "cannot commit"
        )


def require_holdings_unchanged(
    session: Session, holder: Holder, items: tuple[ItemInstance, ...]
) -> None:
    """Refuse a commit computed against holdings that changed after the turn
    read them: an item gained, lost or transferred, or one whose revision
    moved (equipped, attuned, charges, quantity). A subject's state revision
    does not cover its holdings (CRD Issue 15c)."""
    now = {(i.item_id, i.revision) for i in items_held_by(session, holder)}
    if now != {(i.item_id, i.revision) for i in items}:
        raise StaleRevisionError(
            f"{holder.kind.value} {holder.holder_id}'s holdings changed after this "
            "turn read them; its work cannot commit"
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

    def recheck(self, session: Session, character: TurnSubject) -> None:
        """The commit-time recheck: refuse work computed against a superseded
        revision or binding (see :func:`require_unchanged`)."""
        if isinstance(character, TurnCreature):
            require_unchanged(
                session,
                character.subject_id,
                character.stored.revision,
                character.stored.binding,
                kind="creature",
            )
            holder = Holder(HolderKind.CREATURE, character.subject_id)
        else:
            require_unchanged(
                session,
                character.sheet_id,
                character.stored.revision,
                character.stored.binding,
            )
            holder = Holder(HolderKind.CHARACTER, character.sheet_id)
        require_holdings_unchanged(session, holder, character.items)

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
