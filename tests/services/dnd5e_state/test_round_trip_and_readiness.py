"""Every inventory family round-trips; readiness is not legality (2b)."""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.representation import DieSize
from afterworlds.models.dnd5e_state import (
    ActiveEffect,
    ArmorTrainingGrant,
    CreatureState,
    GrantSource,
    HitPoints,
)
from afterworlds.models.dnd5e_vocabulary import ArmorCategory
from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.services.dnd5e_state import adoption, service, store
from afterworlds.services.dnd5e_state.adoption import AdoptionStatus
from afterworlds.services.dnd5e_state.shared_changes import (
    ChangeStatus,
    OverrideSpec,
    activate,
    request_change,
)
from afterworlds.services.dnd5e_state.validation import (
    character_readiness,
    validate_character,
)
from tests.services.dnd5e_state.builders import (
    CLASSES,
    complete_character,
    real_index,
)
from tests.services.dnd5e_state.conftest import (
    CREATURE_KEY,
    NOW,
    Table,
    new_character,
    new_story,
)
from tests.services.rules_authority.conftest import (
    DISABLE_PAYLOAD,
    PROSE_COMPONENT_TARGET,
)


@pytest.mark.parametrize(
    ("class_key", "subclass", "die"), CLASSES, ids=[c[0] for c in CLASSES]
)
def test_a_complete_character_of_every_class_round_trips_every_family(
    table: Table, class_key: str, subclass: str, die: DieSize
) -> None:
    state = complete_character(
        real_index(), class_key, 5, subclass=subclass, hit_die=die
    )
    state = state.model_copy(
        update={
            "active_effects": (
                ActiveEffect(
                    instance_id="e1",
                    source=GrantSource(record_key="spells.bless"),
                    cast_level=1,
                    concentration=True,
                ),
                ActiveEffect(
                    instance_id="e2",
                    source=GrantSource(record_key="spells.bless"),
                    concentration=False,
                ),
            )
        }
    )
    unset = [n for n in type(state).model_fields if getattr(state, n) is None]
    # Only families the class makes inapplicable may be unset.
    assert set(unset) <= {"spell_slot_pools", "spell_access"}
    binding = _binding(table)
    with table.factory() as s, s.begin():
        sheet = new_character(s, new_story(s))
        store.create_character_state(s, sheet, state, binding, now=NOW)
    with table.factory() as s:
        assert service.read_character(s, sheet).state == state
    with table.factory() as s, s.begin():
        changed = state.model_copy(update={"heroic_inspiration": True})
        store.save_state(
            s,
            "character",
            sheet,
            changed,
            expected_revision=1,
            expected_binding=binding,
            now=NOW,
        )
    with table.factory() as s:
        stored = service.read_character(s, sheet)
    assert (stored.revision, stored.state) == (2, changed)


def _binding(table: Table):  # type: ignore[no-untyped-def]
    from afterworlds.services.dnd5e_state.authority import current_binding

    with table.factory() as s:
        return current_binding(s, table.package, now=NOW)


def test_readiness_never_certifies_legality() -> None:
    """A well-formed but rules-questionable record is ready: legality is 15c's."""
    index = real_index()
    wizard = complete_character(index, "classes.wizard", 1)
    # Heavy armor training from a source that grants no such thing: recorded
    # state is well-formed, so it is valid and ready; whether it is legal is
    # an eligibility judgement 2b does not make.
    questionable = wizard.model_copy(
        update={
            "armor_training": (
                ArmorTrainingGrant(
                    category=ArmorCategory.HEAVY,
                    source=GrantSource(record_key="character_origins.sage"),
                ),
            )
        }
    )
    assert validate_character(index, questionable) == ()
    assert character_readiness(index, questionable) == ()


def test_a_creature_adopts_on_its_own_without_its_owner(table: Table) -> None:
    with table.factory() as s, s.begin():
        story = new_story(s)
        creature = service.create_creature(
            s,
            story,
            "Servant",
            table.package,
            CreatureState(
                template_record_key=CREATURE_KEY,
                hit_points=HitPoints(current=5, maximum=5, temporary=0),
                conditions=(),
                active_effects=(),
            ),
            now=NOW,
        )
        change = request_change(
            s,
            table.package,
            table.runtime.release_version,
            (
                OverrideSpec(
                    override_id="h",
                    target=PROSE_COMPONENT_TARGET,
                    operation=OverrideOperationEnum.DISABLE,
                    payload=DISABLE_PAYLOAD,
                ),
            ),
            requested_by="owner",
            now=NOW,
        )
    with table.factory() as s, s.begin():
        assert activate(s, change, now=NOW).status is ChangeStatus.ACTIVE
    with table.factory() as s, s.begin():
        outcome = adoption.request_adoption(
            s, "creature", creature.creature_id, change_id=change, now=NOW
        )
    assert outcome.status is AdoptionStatus.APPLIED
    with table.factory() as s:
        after = service.read_creature(s, creature.creature_id)
    assert after.state == creature.state
    assert after.binding != creature.binding
