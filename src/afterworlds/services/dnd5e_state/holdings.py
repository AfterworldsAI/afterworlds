"""Parties, creature associations and item instances — CRD Issue 2b.

* A **party** is a minimal story-scoped identity a creature or item can belong
  to. Membership and governance are not modelled; a story is never a party.
* A **creature association** relates a creature to a character or a party.
  Several may be open at once (a shared mount); ending one, or transferring the
  creature, never changes the creature's own state. Absence is not death and
  not a reset. A mechanical association confers no permission and writes no
  Story Bible canon.
* An **item instance** has exactly one holder, which the database enforces.
  Its identity is an accepted equipment or magic-item record, one of that
  record's components where the item is stated as a component, or a member of
  the accepted Poison catalogue (doses are its quantity). An injury poison
  applied to an item is recorded on that item as a poison identity. Anything
  else is refused with a type rather than stored as free text.

**Authority is the holder's.** Every item operation validates against the
holder's own exact binding, which must be current: a character's or
creature's recorded binding, or, for a party (which records no binding of its
own), the current exact binding of the Rules Package it was created under. A
transfer validates against the *destination* holder. An authority index a
caller passes in is never trusted: it must be the holder's exact binding.

Every reference is checked to belong to the same story.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.representation import RecordKind, ToolVariant
from afterworlds.persistence.orm.character_sheet import RpgCharacterSheetBaseORM
from afterworlds.persistence.orm.dnd5e_state import (
    Dnd5eCreatureAssociationORM,
    Dnd5eCreatureORM,
    Dnd5eItemInstanceORM,
    RpgPartyORM,
)
from afterworlds.services.dnd5e_state import store
from afterworlds.services.dnd5e_state.authority import (
    AuthorityIndex,
    authority_index,
    current_binding,
    require_current,
)
from afterworlds.services.dnd5e_state.errors import (
    BindingRefusedError,
    StaleRevisionError,
    StateServiceError,
    SubjectNotFoundError,
    UnsupportedIdentityError,
)
from afterworlds.services.dnd5e_state.validation import tool_variant_failure
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome

__all__ = [
    "POISON_CATALOGUE",
    "AssociationKind",
    "HolderKind",
    "Holder",
    "ItemInstance",
    "associate",
    "associations_of",
    "create_item",
    "create_party",
    "end_association",
    "holder_authority",
    "item_identity_failure",
    "items_held_by",
    "poison_identity_failure",
    "transfer_item",
    "update_item_use",
]

#: The accepted catalogue whose members are poisons an item instance can be.
POISON_CATALOGUE = "gameplay_toolbox.poison"


class AssociationKind(StrEnum):
    """The continuing creatures CRD Issue 2b names."""

    MOUNT = "mount"
    PET = "pet"
    ANIMAL_COMPANION = "animal_companion"
    SUMMON = "summon"


class HolderKind(StrEnum):
    CHARACTER = "character"
    CREATURE = "creature"
    PARTY = "party"


@dataclass(frozen=True)
class Holder:
    kind: HolderKind
    holder_id: UUID


@dataclass(frozen=True)
class ItemInstance:
    item_id: UUID
    story_id: UUID
    record_key: str
    component_key: str | None
    quantity: int
    holder: Holder
    equipped: bool
    attuned_subject_id: UUID | None
    charges_remaining: int | None
    applied_poison_record_key: str | None
    revision: int
    #: The kind of a Gaming Set or Musical Instrument (CRD Issue 15c).
    tool_variant: ToolVariant | None = None


_HOLDER_COLUMN = {
    HolderKind.CHARACTER: "holder_character_id",
    HolderKind.CREATURE: "holder_creature_id",
    HolderKind.PARTY: "holder_party_id",
}
_HOLDER_TABLE: dict[HolderKind, Any] = {
    HolderKind.CHARACTER: RpgCharacterSheetBaseORM,
    HolderKind.CREATURE: Dnd5eCreatureORM,
    HolderKind.PARTY: RpgPartyORM,
}


def _story_of(session: Session, holder: Holder) -> str:
    table = _HOLDER_TABLE[holder.kind]
    story_id = session.execute(
        sa.select(table.story_id).where(
            table.__table__.primary_key.columns[0] == str(holder.holder_id)
        )
    ).scalar_one_or_none()
    if story_id is None:
        raise SubjectNotFoundError(f"no {holder.kind.value} {holder.holder_id}")
    return str(story_id)


def _same_story(session: Session, holder: Holder, story_id: str) -> None:
    if _story_of(session, holder) != story_id:
        raise StateServiceError(
            f"{holder.kind.value} {holder.holder_id} belongs to another story; "
            "references stay story-scoped"
        )


def create_party(
    session: Session, story_id: UUID, label: str, package_uuid: UUID, *, now: str
) -> UUID:
    """A minimal party whose items are governed by *package_uuid*'s authority."""
    current_binding(session, package_uuid, now=now)  # refuses typed if unusable
    party_id = uuid4()
    session.add(
        RpgPartyORM(
            party_id=str(party_id),
            story_id=str(story_id),
            label=label,
            package_uuid=str(package_uuid),
            created_at=now,
        )
    )
    session.flush()
    return party_id


def associate(
    session: Session,
    creature_id: UUID,
    kind: AssociationKind,
    target: Holder,
    *,
    now: str,
) -> UUID:
    """Open an association of a creature with a character or a party."""
    if target.kind is HolderKind.CREATURE:
        raise StateServiceError("a creature is associated with a character or a party")
    creature = session.get(Dnd5eCreatureORM, str(creature_id))
    if creature is None:
        raise SubjectNotFoundError(f"no creature {creature_id}")
    _same_story(session, target, creature.story_id)
    association_id = uuid4()
    session.add(
        Dnd5eCreatureAssociationORM(
            association_id=str(association_id),
            creature_id=str(creature_id),
            kind=kind.value,
            character_id=(
                str(target.holder_id) if target.kind is HolderKind.CHARACTER else None
            ),
            party_id=str(target.holder_id) if target.kind is HolderKind.PARTY else None,
            started_at=now,
        )
    )
    session.flush()
    return association_id


def end_association(session: Session, association_id: UUID, *, now: str) -> None:
    """Close an association. The creature and its state are untouched."""
    result = session.execute(
        sa.update(Dnd5eCreatureAssociationORM)
        .where(Dnd5eCreatureAssociationORM.association_id == str(association_id))
        .where(Dnd5eCreatureAssociationORM.ended_at.is_(None))
        .values(ended_at=now)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:  # type: ignore[attr-defined]
        raise StateServiceError(f"association {association_id} is not open")


def associations_of(
    session: Session, creature_id: UUID, *, open_only: bool = True
) -> tuple[tuple[UUID, AssociationKind, Holder, str, str | None], ...]:
    """(association id, kind, target, started, ended) for a creature."""
    query = sa.select(Dnd5eCreatureAssociationORM).where(
        Dnd5eCreatureAssociationORM.creature_id == str(creature_id)
    )
    if open_only:
        query = query.where(Dnd5eCreatureAssociationORM.ended_at.is_(None))
    out = []
    for row in session.execute(
        query.order_by(Dnd5eCreatureAssociationORM.started_at)
    ).scalars():
        target = (
            Holder(HolderKind.CHARACTER, UUID(row.character_id))
            if row.character_id
            else Holder(HolderKind.PARTY, UUID(str(row.party_id)))
        )
        out.append(
            (
                UUID(row.association_id),
                AssociationKind(row.kind),
                target,
                row.started_at,
                row.ended_at,
            )
        )
    return tuple(out)


def poison_identity_failure(index: AuthorityIndex, record_key: str) -> str | None:
    """Why *record_key* is not an accepted poison, or ``None``."""
    if index.record(record_key) is None:
        return f"{record_key!r} is not an accepted record"
    if not index.is_member(POISON_CATALOGUE, record_key):
        return f"{record_key!r} is not in the accepted Poison catalogue"
    return None


def item_identity_failure(
    index: AuthorityIndex,
    record_key: str,
    component_key: str | None,
    applied_poison_record_key: str | None = None,
    tool_variant: str | None = None,
) -> str | None:
    """Why an item identity is not representable under *index*, or ``None``.
    A recorded *tool_variant* must be one of the tool component's typed kinds."""
    kind = index.kind(record_key)
    if kind is None:
        return f"{record_key!r} is not an accepted record"
    poison = kind is RecordKind.GAMEPLAY_TOOL and index.is_member(
        POISON_CATALOGUE, record_key
    )
    if kind not in (RecordKind.EQUIPMENT, RecordKind.MAGIC_ITEM) and not poison:
        return f"{record_key!r} is a {kind.value}, not an item"
    if component_key is not None and index.component(record_key, component_key) is None:
        return f"{record_key!r} has no component {component_key!r}"
    if failure := tool_variant_failure(index, record_key, component_key, tool_variant):
        return failure
    if applied_poison_record_key is not None:
        return poison_identity_failure(index, applied_poison_record_key)
    return None


def holder_authority(session: Session, holder: Holder, *, now: str) -> AuthorityIndex:
    """The exact current authority governing what *holder* may hold.

    Refuses typed when the holder has no recorded state, or when its binding
    (for a party, its package's binding) is not current.
    """
    if holder.kind is HolderKind.PARTY:
        party = session.get(RpgPartyORM, str(holder.holder_id))
        if party is None:
            raise SubjectNotFoundError(f"no party {holder.holder_id}")
        binding = current_binding(session, UUID(party.package_uuid), now=now)
    else:
        stored = (
            store.get_character(session, holder.holder_id)
            if holder.kind is HolderKind.CHARACTER
            else store.get_creature(session, holder.holder_id)
        )
        if stored is None:
            raise SubjectNotFoundError(
                f"no {holder.kind.value} state for {holder.holder_id}; an item "
                "holder is bound to a Rules Package"
            )
        require_current(session, stored.binding, now=now)
        binding = stored.binding
    return authority_index(session, binding, now=now)


def _admit(
    session: Session,
    holder: Holder,
    record_key: str,
    component_key: str | None,
    applied_poison_record_key: str | None,
    *,
    now: str,
    given: AuthorityIndex | None = None,
    tool_variant: str | None = None,
) -> None:
    index = holder_authority(session, holder, now=now)
    if given is not None and given.binding != index.binding:
        raise BindingRefusedError(
            AuthorityOutcome.MISMATCHED_RELEASE,
            f"the authority given ({given.binding}) is not the exact binding of "
            f"{holder.kind.value} {holder.holder_id} ({index.binding})",
        )
    if failure := item_identity_failure(
        index, record_key, component_key, applied_poison_record_key, tool_variant
    ):
        raise UnsupportedIdentityError(failure)


def _to_item(row: Dnd5eItemInstanceORM) -> ItemInstance:
    for kind, column in _HOLDER_COLUMN.items():
        value = getattr(row, column)
        if value is not None:
            holder = Holder(kind, UUID(value))
    return ItemInstance(
        item_id=UUID(row.item_id),
        story_id=UUID(row.story_id),
        record_key=row.record_key,
        component_key=row.component_key,
        quantity=row.quantity,
        holder=holder,
        equipped=row.equipped,
        attuned_subject_id=(
            UUID(row.attuned_subject_id) if row.attuned_subject_id else None
        ),
        charges_remaining=row.charges_remaining,
        applied_poison_record_key=row.applied_poison_record_key,
        revision=row.revision,
        tool_variant=ToolVariant(row.tool_variant) if row.tool_variant else None,
    )


def create_item(
    session: Session,
    index: AuthorityIndex,
    holder: Holder,
    record_key: str,
    *,
    component_key: str | None = None,
    quantity: int = 1,
    equipped: bool = False,
    charges_remaining: int | None = None,
    applied_poison_record_key: str | None = None,
    tool_variant: ToolVariant | None = None,
    now: str,
) -> ItemInstance:
    """Create an item instance held by *holder*.

    Validated against the holder's exact current authority; *index* must be
    that authority (it is checked, never trusted).
    """
    story_id = _story_of(session, holder)
    _admit(
        session,
        holder,
        record_key,
        component_key,
        applied_poison_record_key,
        now=now,
        given=index,
        tool_variant=tool_variant,
    )
    item_id = str(uuid4())
    session.add(
        Dnd5eItemInstanceORM(
            item_id=item_id,
            story_id=story_id,
            record_key=record_key,
            component_key=component_key,
            tool_variant=tool_variant,
            quantity=quantity,
            equipped=equipped,
            charges_remaining=charges_remaining,
            applied_poison_record_key=applied_poison_record_key,
            revision=1,
            created_at=now,
            **{_HOLDER_COLUMN[holder.kind]: str(holder.holder_id)},
        )
    )
    session.flush()
    row = session.get(Dnd5eItemInstanceORM, item_id)
    assert row is not None
    return _to_item(row)


def _cas_update(
    session: Session,
    row: Dnd5eItemInstanceORM,
    expected_revision: int,
    values: dict[str, object],
) -> ItemInstance:
    item_id = row.item_id
    result = session.execute(
        sa.update(Dnd5eItemInstanceORM)
        .where(Dnd5eItemInstanceORM.item_id == item_id)
        .where(Dnd5eItemInstanceORM.revision == expected_revision)
        .values(**values, revision=expected_revision + 1)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:  # type: ignore[attr-defined]
        raise StaleRevisionError(
            f"item {item_id} revision {expected_revision} is stale"
        )
    session.expire(row)
    refreshed = session.get(Dnd5eItemInstanceORM, item_id)
    assert refreshed is not None
    return _to_item(refreshed)


def _item_row(session: Session, item_id: UUID) -> Dnd5eItemInstanceORM:
    row = session.get(Dnd5eItemInstanceORM, str(item_id))
    if row is None:
        raise SubjectNotFoundError(f"no item {item_id}")
    return row


def transfer_item(
    session: Session, item_id: UUID, to: Holder, *, expected_revision: int, now: str
) -> ItemInstance:
    """Move an item to one new holder in the same story, by CAS.

    The item must be representable under the destination holder's exact
    current authority. Attunement and equipped state end with the transfer;
    the new holder starts unattuned and unequipped.
    """
    row = _item_row(session, item_id)
    _same_story(session, to, row.story_id)
    _admit(
        session,
        to,
        row.record_key,
        row.component_key,
        row.applied_poison_record_key,
        now=now,
        tool_variant=row.tool_variant,
    )
    values: dict[str, object] = {column: None for column in _HOLDER_COLUMN.values()}
    values[_HOLDER_COLUMN[to.kind]] = str(to.holder_id)
    values.update(equipped=False, attuned_subject_id=None)
    return _cas_update(session, row, expected_revision, values)


def update_item_use(
    session: Session,
    item_id: UUID,
    *,
    expected_revision: int,
    equipped: bool,
    attuned: bool,
    charges_remaining: int | None,
    applied_poison_record_key: str | None = None,
    now: str,
) -> ItemInstance:
    """Record equipped/attuned/charges/applied poison for an item, by CAS.

    Every field is replaced. Validated under the holder's exact current
    authority. Attunement is to the item's current character or creature
    holder; a party-held item cannot be attuned.
    """
    row = _item_row(session, item_id)
    holder = _to_item(row).holder
    if attuned and holder.kind is HolderKind.PARTY:
        raise StateServiceError("a party-held item cannot be attuned")
    _admit(
        session,
        holder,
        row.record_key,
        row.component_key,
        applied_poison_record_key,
        now=now,
        tool_variant=row.tool_variant,
    )
    return _cas_update(
        session,
        row,
        expected_revision,
        {
            "equipped": equipped,
            "attuned_subject_id": str(holder.holder_id) if attuned else None,
            "charges_remaining": charges_remaining,
            "applied_poison_record_key": applied_poison_record_key,
        },
    )


def spend_item(
    session: Session, item_id: UUID, *, expected_revision: int, count: int
) -> ItemInstance | None:
    """Expend *count* of an item (ammunition), by CAS against the revision
    the turn read (CRD Issue 15c). The last one removes the row: a quantity
    of zero is not a holding. Returns the item left, or ``None``."""
    row = _item_row(session, item_id)
    if count < 1 or count > row.quantity:
        raise StateServiceError(
            f"item {item_id} holds {row.quantity}; {count} cannot be expended"
        )
    if count < row.quantity:
        return _cas_update(
            session, row, expected_revision, {"quantity": row.quantity - count}
        )
    result = session.execute(
        sa.delete(Dnd5eItemInstanceORM)
        .where(Dnd5eItemInstanceORM.item_id == row.item_id)
        .where(Dnd5eItemInstanceORM.revision == expected_revision)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:  # type: ignore[attr-defined]
        raise StaleRevisionError(
            f"item {item_id} revision {expected_revision} is stale"
        )
    session.expunge(row)
    return None


def items_held_by(session: Session, holder: Holder) -> tuple[ItemInstance, ...]:
    column = getattr(Dnd5eItemInstanceORM, _HOLDER_COLUMN[holder.kind])
    rows = session.execute(
        sa.select(Dnd5eItemInstanceORM)
        .where(column == str(holder.holder_id))
        .order_by(Dnd5eItemInstanceORM.created_at, Dnd5eItemInstanceORM.item_id)
        .execution_options(populate_existing=True)
    ).scalars()
    return tuple(_to_item(r) for r in rows)
