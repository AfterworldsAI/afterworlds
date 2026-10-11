"""Continuing creatures, parties and item instances on a real database (2b)."""

from __future__ import annotations

from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from afterworlds.models.dnd5e_state import (
    CreatureState,
    GrantSource,
    HitPoints,
    SummonOrigin,
)
from afterworlds.persistence.orm.dnd5e_state import Dnd5eItemInstanceORM
from afterworlds.services.dnd5e_state import holdings, service
from afterworlds.services.dnd5e_state.errors import (
    StaleRevisionError,
    StateServiceError,
    UnsupportedIdentityError,
)
from afterworlds.services.dnd5e_state.holdings import (
    AssociationKind,
    Holder,
    HolderKind,
)
from tests.services.dnd5e_state.builders import real_index
from tests.services.dnd5e_state.conftest import (
    CREATURE_KEY,
    NOW,
    Table,
    new_character,
    new_story,
    poisoned,
    wizardish,
)

G1_ITEMS = (
    "equipment.weapons.dart",
    "equipment.weapons.glaive",
    "equipment.weapons.halberd",
    "equipment.weapons.lance",
    "equipment.weapons.maul",
    "equipment.weapons.trident",
    "equipment.weapons.war_pick",
    "equipment.weapons.whip",
    "equipment.weapons.blowgun",
    "equipment.armor.scale_mail",
    "equipment.armor.ring_mail",
    "equipment.adventuring_gear.needles",
)


def _servant(**updates: object) -> CreatureState:
    return CreatureState(
        template_record_key=CREATURE_KEY,
        hit_points=HitPoints(current=5, maximum=5, temporary=0),
        conditions=(),
        active_effects=(),
    ).model_copy(update=updates)


def _setup(table: Table) -> tuple[UUID, UUID]:
    with table.factory() as s, s.begin():
        story = new_story(s)
        sheet = new_character(s, story)
        service.create_character(s, sheet, table.package, wizardish(), now=NOW)
    return story, sheet


def _creature(table: Table, story: UUID, **updates: object) -> UUID:
    with table.factory() as s, s.begin():
        return service.create_creature(
            s, story, "Servant", table.package, _servant(**updates), now=NOW
        ).creature_id


def test_same_template_instances_are_independent_records(table: Table) -> None:
    story, _ = _setup(table)
    first = _creature(table, story)
    second = _creature(table, story)
    with table.factory() as s, s.begin():
        stored = service.read_creature(s, first)
        service.update_creature(
            s,
            first,
            _servant(
                hit_points=HitPoints(current=1, maximum=5, temporary=0),
                conditions=(poisoned("p"),),
            ),
            expected_revision=stored.revision,
            now=NOW,
        )
    with table.factory() as s:
        assert first != second
        assert service.read_creature(s, first).state.hit_points == HitPoints(
            current=1, maximum=5, temporary=0
        )
        assert service.read_creature(s, second).state == _servant()


def test_ending_or_transferring_an_association_never_touches_the_creature(
    table: Table,
) -> None:
    story, sheet = _setup(table)
    mount = _creature(
        table, story, hit_points=HitPoints(current=-3, maximum=5, temporary=0)
    )
    with table.factory() as s, s.begin():
        party = holdings.create_party(s, story, "The Company", now=NOW)
        rider = holdings.associate(
            s,
            mount,
            AssociationKind.MOUNT,
            Holder(HolderKind.CHARACTER, sheet),
            now=NOW,
        )
        shared = holdings.associate(
            s, mount, AssociationKind.MOUNT, Holder(HolderKind.PARTY, party), now=NOW
        )
        before = service.read_creature(s, mount)
    with table.factory() as s, s.begin():
        holdings.end_association(s, rider, now=NOW)
        holdings.end_association(s, shared, now=NOW)
    with table.factory() as s:
        after = service.read_creature(s, mount)
        assert holdings.associations_of(s, mount) == ()
        assert len(holdings.associations_of(s, mount, open_only=False)) == 2
    # Absent from every association: same HP (no floor, not reset), alive.
    assert (after.state, after.revision) == (before.state, before.revision)


def test_a_summon_records_its_source_specific_origin(table: Table) -> None:
    story, sheet = _setup(table)
    summon = SummonOrigin(
        source=GrantSource(record_key="spell:wish"),
        summoner_subject=sheet,
        effect_instance_id="wish-1",
        controller_subject=sheet,
        ends_marker="dawn",
    )
    servant = _creature(table, story, summon=summon)
    with table.factory() as s, s.begin():
        holdings.associate(
            s,
            servant,
            AssociationKind.SUMMON,
            Holder(HolderKind.CHARACTER, sheet),
            now=NOW,
        )
    with table.factory() as s:
        assert service.read_creature(s, servant).state.summon == summon


def test_associations_and_items_stay_story_scoped(table: Table) -> None:
    story, _ = _setup(table)
    other_story, other_sheet = _setup(table)
    creature = _creature(table, story)
    with table.factory() as s, s.begin(), pytest.raises(StateServiceError):
        holdings.associate(
            s,
            creature,
            AssociationKind.PET,
            Holder(HolderKind.CHARACTER, other_sheet),
            now=NOW,
        )
    del other_story


def test_an_item_has_exactly_one_holder_enforced_by_the_database(table: Table) -> None:
    story, sheet = _setup(table)
    creature = _creature(table, story)
    with table.factory() as s:
        for holders in (
            {},
            {"holder_character_id": str(sheet), "holder_creature_id": str(creature)},
        ):
            with pytest.raises(IntegrityError), s.begin():
                s.add(
                    Dnd5eItemInstanceORM(
                        item_id=f"bad-{len(holders)}",
                        story_id=str(story),
                        record_key="equipment.weapons.dart",
                        quantity=1,
                        equipped=False,
                        revision=1,
                        created_at=NOW,
                        **holders,
                    )
                )


def test_all_twelve_g1_items_are_stored_and_resolved(table: Table) -> None:
    index = real_index()
    _, sheet = _setup(table)
    holder = Holder(HolderKind.CHARACTER, sheet)
    with table.factory() as s, s.begin():
        for key in G1_ITEMS:
            holdings.create_item(s, index, holder, key, now=NOW)
    with table.factory() as s:
        held = holdings.items_held_by(s, holder)
    assert sorted(i.record_key for i in held) == sorted(G1_ITEMS)
    assert all(index.record(i.record_key) is not None for i in held)


def test_an_identity_that_is_not_an_item_is_refused_with_a_type(table: Table) -> None:
    index = real_index()
    _, sheet = _setup(table)
    holder = Holder(HolderKind.CHARACTER, sheet)
    with table.factory() as s, s.begin():
        for key, component in (
            ("spells.fire_bolt", None),  # a spell, not an item
            ("equipment.mounts_and_vehicles", "galley"),  # no such component
            ("equipment.weapons.blunderbuss", None),  # no such record
        ):
            with pytest.raises(UnsupportedIdentityError):
                holdings.create_item(
                    s, index, holder, key, component_key=component, now=NOW
                )


def test_transfer_moves_one_holder_by_cas_and_ends_attunement(table: Table) -> None:
    index = real_index()
    story, sheet = _setup(table)
    creature = _creature(table, story)
    with table.factory() as s, s.begin():
        item = holdings.create_item(
            s,
            index,
            Holder(HolderKind.CHARACTER, sheet),
            "magic_items.bag_of_tricks",
            now=NOW,
        )
        item = holdings.update_item_use(
            s,
            item.item_id,
            expected_revision=item.revision,
            equipped=True,
            attuned=True,
            charges_remaining=3,
        )
    assert item.attuned_subject_id == sheet
    with table.factory() as s, s.begin():
        moved = holdings.transfer_item(
            s,
            item.item_id,
            Holder(HolderKind.CREATURE, creature),
            expected_revision=item.revision,
        )
    assert moved.holder == Holder(HolderKind.CREATURE, creature)
    assert (moved.attuned_subject_id, moved.equipped, moved.charges_remaining) == (
        None,
        False,
        3,
    )
    with table.factory() as s, s.begin(), pytest.raises(StaleRevisionError):
        holdings.transfer_item(
            s,
            item.item_id,
            Holder(HolderKind.CHARACTER, sheet),
            expected_revision=item.revision,
        )
    with table.factory() as s:
        rows = s.execute(
            sa.select(sa.func.count()).select_from(Dnd5eItemInstanceORM)
        ).scalar_one()
    assert rows == 1
