"""CRD Issue 15c (C8) — the Ghast's and Ghoul's Claw rider exclusions.

"If the target is a creature that isn't an Undead or elf, it is subjected to
the following effect" (``monsters-A-Z.md``:6919, the Ghoul; the Ghast spares
Undead only). The target's type and Elf status come from accepted authority
(:mod:`afterworlds.pipeline.rpg.creature_types`): an excluded target still
takes the hit's damage and makes no save; an unestablished one refuses before
any die.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any
from uuid import uuid4

import pytest

from afterworlds.models.dnd5e_state import (
    ActiveEffect,
    CreatureSpeciesSelection,
    GrantSource,
    OriginSelection,
    SummonOrigin,
)
from afterworlds.models.dnd5e_vocabulary import CreatureType
from afterworlds.pipeline.rpg import creature_types
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.services.dnd5e_state.turn import TurnCharacter, TurnCreature
from tests.pipeline.rpg.test_creature_attacks import (
    _bite,
    _medium_wizard,
    _refused,
    _resolve,
    _subjects,
)
from tests.pipeline.rpg.test_weapon_attacks import _creature, _dice

GHOUL, GHAST = "monsters.ghoul.ghoul", "monsters.ghast.ghast"


def _with(subject: Any, **state: Any) -> Any:
    updated = subject.stored.state.model_copy(update=state)
    return dataclasses.replace(
        subject, stored=dataclasses.replace(subject.stored, state=updated)
    )


def _claw(attacker: TurnCreature, target: Any) -> Any:
    return _bite(attacker, target, entry="Claw", target_within_5_feet=True)


def _strike(attacker: TurnCreature, target: Any, actor: TurnCharacter) -> Any:
    """Hit with the Claw (d20 15, damage die 1), save rolled at 2 (fails)."""
    subjects = _subjects(attacker, *([target] if target is not actor else []))
    dice = _dice((15,), (1,))
    original = dice.roll.side_effect

    def roll(expression: str) -> Any:
        if dice.calls and "d20" in expression:  # the rider's save
            dice.calls.append(expression)
            from afterworlds.models.rpg import DiceResult

            return DiceResult(expression=expression, raw_rolls=(2,), chosen=2)
        return original(expression)

    dice.roll.side_effect = roll
    record = _resolve(_claw(attacker, target), actor, subjects, dice)
    return record, json.loads(record.modifiers_json), dice.calls


def _paralyzed(record: Any) -> bool:
    return any(
        e.operation == "apply_condition"
        and json.loads(e.value_json)["condition"] == "paralyzed"
        for e in record.sheet_effects
    )


def _damage(record: Any, subject: Any) -> bool:
    return any(
        e.target == "current_hp" and e.subject_id == subject.subject_id
        for e in record.sheet_effects
    )


def _humanoid(**state: Any) -> TurnCreature:
    return _with(_creature("monsters.bandits.bandit", hp=40), **state)


def _species(creature: TurnCreature, species: str) -> CreatureSpeciesSelection:
    assert creature.index is not None
    return CreatureSpeciesSelection(
        species_record_key=species,
        template_record_key=creature.stored.state.template_record_key,
        mechanical_projection_uuid=creature.index.binding.mechanical_projection_uuid,
        override_set_uuid=creature.index.binding.override_set_uuid,
    )


# --- positive coverage -------------------------------------------------------


def test_a_ghoul_claw_paralyzes_an_ordinary_non_humanoid_creature() -> None:
    """A Beast is not an Elf (Elf ⇒ Humanoid): the rider applies."""
    ghoul, wizard = _creature(GHOUL, hp=40), _medium_wizard()
    wolf = _creature(hp=40)
    record, provenance, calls = _strike(ghoul, wolf, wizard)
    assert calls == ["1d20", "1d4", "1d20"]
    assert _damage(record, wolf) and _paralyzed(record)
    assert provenance["rider"]["target_type"] == "beast"


def test_a_ghast_claw_paralyzes_an_elf_character() -> None:
    """The Ghast excludes only Undead."""
    ghast, wizard = _creature(GHAST, hp=40), _medium_wizard()
    record, _provenance, _calls = _strike(ghast, wizard, wizard)
    assert _damage(record, wizard) and _paralyzed(record)


def test_a_ghoul_claw_paralyzes_a_non_elf_character() -> None:
    ghoul = _creature(GHOUL, hp=40)
    human = _with(
        _medium_wizard(), species=OriginSelection(record_key="character_origins.human")
    )
    record, _provenance, _calls = _strike(ghoul, human, human)
    assert _damage(record, human) and _paralyzed(record)


def test_a_ghoul_claw_paralyzes_a_humanoid_recorded_as_a_dwarf() -> None:
    ghoul, bandit = _creature(GHOUL, hp=40), _humanoid()
    dwarf = _with(bandit, species=_species(bandit, "character_origins.dwarf"))
    record, provenance, _calls = _strike(ghoul, dwarf, _medium_wizard())
    assert _damage(record, dwarf) and _paralyzed(record)
    assert "character_origins.dwarf" in provenance["rider"]["basis"]


# --- excluded targets: damage, no rider --------------------------------------


@pytest.mark.parametrize("attacker", [GHOUL, GHAST])
def test_an_undead_target_takes_the_damage_without_the_rider(attacker: str) -> None:
    claw, zombie = _creature(attacker, hp=40), _creature(
        "monsters.zombies.zombie", hp=40
    )
    record, provenance, calls = _strike(claw, zombie, _medium_wizard())
    assert len(calls) == 2 and calls[0] == "1d20"  # attack and damage; no save
    assert _damage(record, zombie) and not _paralyzed(record)
    assert provenance["rider"] == {"result": "excluded", "by": "undead"}


def test_a_ghoul_claw_spares_an_elf_character() -> None:
    ghoul, elf = _creature(GHOUL, hp=40), _medium_wizard()
    record, provenance, calls = _strike(ghoul, elf, elf)
    assert calls == ["1d20", "1d4"]
    assert _damage(record, elf) and not _paralyzed(record)
    assert provenance["rider"] == {"result": "excluded", "by": "elf"}


def test_a_ghoul_claw_spares_a_humanoid_recorded_as_an_elf() -> None:
    ghoul, bandit = _creature(GHOUL, hp=40), _humanoid()
    elf = _with(bandit, species=_species(bandit, creature_types.ELF))
    record, provenance, _calls = _strike(ghoul, elf, _medium_wizard())
    assert _damage(record, elf) and not _paralyzed(record)
    assert provenance["rider"] == {"result": "excluded", "by": "elf"}


def test_a_familiar_is_its_chosen_type() -> None:
    """Find Familiar: a named form, a type within the choice."""
    familiar = _with(
        _creature("animals.cat", hp=40),
        summon=SummonOrigin(source=GrantSource(record_key="spells.find_familiar")),
        creature_type=CreatureType.FEY,
    )
    typed = creature_types.target_type(familiar)
    assert (typed.type, typed.elf) == (CreatureType.FEY, False)


# --- refusals before any die -------------------------------------------------


def _refuses(kind: RefusalKind, target: Any, attacker: str = GHOUL) -> str:
    ghoul = _creature(attacker, hp=40)
    if isinstance(target, TurnCharacter):  # the acting character is the target
        return _refused(kind, _claw(ghoul, target), target, _subjects(ghoul)).detail
    subjects = _subjects(ghoul, target)
    return _refused(kind, _claw(ghoul, target), _medium_wizard(), subjects).detail


def test_a_humanoid_with_no_species_refuses_for_the_ghoul_only() -> None:
    bandit = _humanoid()
    assert "species is not recorded" in _refuses(RefusalKind.MISSING_STATE, bandit)
    record, _provenance, _calls = _strike(
        _creature(GHAST, hp=40), bandit, _medium_wizard()
    )
    assert _paralyzed(record)  # the Ghast does not ask


def test_a_stale_species_selection_refuses() -> None:
    bandit = _humanoid()
    stale = _species(bandit, creature_types.ELF).model_copy(
        update={"mechanical_projection_uuid": uuid4()}
    )
    _refuses(RefusalKind.STALE_BINDING, _with(bandit, species=stale))


def test_a_non_humanoid_species_selection_refuses() -> None:
    """Only a source-open Humanoid may record a species."""
    wolf = _creature(hp=40)
    assert wolf.index is not None
    assert not creature_types.species_open(wolf.index, "animals.wolf")
    _refuses(
        RefusalKind.INVALID_SELECTION,
        _with(wolf, species=_species(wolf, creature_types.ELF)),
    )


@pytest.mark.parametrize(
    ("state", "kind"),
    [
        ({"active_effects": None}, RefusalKind.MISSING_STATE),
        (
            {
                "active_effects": (
                    ActiveEffect(
                        instance_id="poly",
                        source=GrantSource(record_key="spells.polymorph"),
                        concentration=True,
                        form_record_key="animals.giant_ape",
                    ),
                )
            },
            RefusalKind.UNSUPPORTED_CAPABILITY,
        ),
        (
            {
                "active_effects": (
                    ActiveEffect(
                        instance_id="bless",
                        source=GrantSource(record_key="spells.bless"),
                        concentration=True,
                    ),
                )
            },
            RefusalKind.UNSUPPORTED_CAPABILITY,
        ),
        ({"creature_type": CreatureType.FEY}, RefusalKind.UNSUPPORTED_CAPABILITY),
    ],
    ids=["effects-unrecorded", "assumed-form", "unexecuted-effect", "bare-stored-type"],
)
def test_an_unestablished_creature_type_refuses(
    state: dict[str, Any], kind: RefusalKind
) -> None:
    _refuses(kind, _with(_creature(hp=40), **state))


@pytest.mark.parametrize(
    ("template", "state", "kind"),
    [
        ("animals.cat", {"creature_type": None}, RefusalKind.MISSING_STATE),
        (
            "animals.cat",
            {"creature_type": CreatureType.BEAST},
            RefusalKind.INVALID_SELECTION,
        ),
        (
            "animals.wolf",
            {"creature_type": CreatureType.FEY},
            RefusalKind.UNSUPPORTED_CAPABILITY,
        ),
    ],
    ids=["no-choice", "choice-outside", "unnamed-form"],
)
def test_an_invalid_familiar_refuses(
    template: str, state: dict[str, Any], kind: RefusalKind
) -> None:
    familiar = _with(
        _creature(template, hp=40),
        summon=SummonOrigin(source=GrantSource(record_key="spells.find_familiar")),
        **state,
    )
    _refuses(kind, familiar)


def test_an_unrepresented_familiar_source_refuses() -> None:
    familiar = _with(
        _creature("animals.cat", hp=40),
        summon=SummonOrigin(
            source=GrantSource(record_key="classes.druid.wild_companion")
        ),
        creature_type=CreatureType.FEY,
    )
    _refuses(RefusalKind.UNSUPPORTED_CAPABILITY, familiar)


def test_a_character_whose_recorded_type_contradicts_its_species_refuses() -> None:
    wizard = _with(_medium_wizard(), creature_type=CreatureType.FEY)
    _refuses(RefusalKind.INVALID_SELECTION, wizard)


def test_the_species_options_are_the_humanoid_species() -> None:
    bandit = _humanoid()
    assert bandit.index is not None
    options = creature_types.species_options(bandit.index)
    assert creature_types.ELF in options and len(options) == 9
    assert creature_types.species_open(bandit.index, "monsters.bandits.bandit")


# --- the creature_species operation ------------------------------------------


def _species_proposal(
    creature: TurnCreature, species: str | None, visibility: str = "shown"
) -> Any:
    from afterworlds.models.enums import RollVisibility
    from afterworlds.models.rpg import RollProposal, SubjectRef

    return RollProposal(
        check_label="The bandit is an elf",
        subsystem_tag="species",
        visibility=RollVisibility(visibility),
        operation="creature_species",
        subject=SubjectRef(kind="creature", subject_id=creature.subject_id),
        species=species,
    )


def _record(
    creature: TurnCreature, species: str | None, visibility: str = "shown"
) -> Any:
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter

    dice = _dice((20,))
    record = D20RulesSystemAdapter().resolve_roll(
        _species_proposal(creature, species, visibility),
        _medium_wizard(),
        None,
        dice,
        False,
        _subjects(creature),
    )
    assert dice.calls == []  # no dice
    return record


def test_a_species_is_recorded_as_a_creature_effect_and_read_back() -> None:
    from afterworlds.services.dnd5e_state.effects import apply_effects

    bandit = _humanoid()
    record = _record(bandit, creature_types.ELF)
    (effect,) = record.sheet_effects
    assert (effect.target, effect.subject_id) == ("creature_species", bandit.subject_id)
    provenance = json.loads(record.modifiers_json)
    assert provenance["species"] == creature_types.ELF
    assert provenance["certificate"]["operation"] == "creature_species"
    state = apply_effects(bandit.stored.state, record.sheet_effects)
    assert state.species == _species(bandit, creature_types.ELF)
    typed = creature_types.target_type(_with(bandit, species=state.species))
    assert typed.elf is True


@pytest.mark.parametrize(
    ("template", "species", "detail"),
    [
        ("animals.wolf", creature_types.ELF, "source leaves its species open"),
        ("monsters.ghoul.ghoul", creature_types.ELF, "source leaves its species open"),
        ("monsters.bandits.bandit", "classes.wizard", "not one of the species options"),
        ("monsters.bandits.bandit", None, "names a creature and one species"),
    ],
)
def test_an_ineligible_species_selection_refuses(
    template: str, species: str | None, detail: str
) -> None:
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter

    creature = _creature(template, hp=40)
    with pytest.raises(AdjudicationRefusal) as caught:
        D20RulesSystemAdapter().require_supported(
            _species_proposal(creature, species), _medium_wizard(), _subjects(creature)
        )
    assert caught.value.kind is RefusalKind.INVALID_SELECTION
    assert detail in caught.value.detail


def test_a_current_species_is_never_changed_but_a_stale_one_is_recorded_again() -> None:
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter

    bandit = _humanoid()
    elf = _with(bandit, species=_species(bandit, creature_types.ELF))
    with pytest.raises(AdjudicationRefusal) as caught:
        D20RulesSystemAdapter().require_supported(
            _species_proposal(elf, "character_origins.human"),
            _medium_wizard(),
            _subjects(elf),
        )
    assert "does not change" in caught.value.detail
    stale = _with(
        bandit,
        species=_species(bandit, creature_types.ELF).model_copy(
            update={"mechanical_projection_uuid": uuid4()}
        ),
    )
    record = _record(stale, "character_origins.human")
    assert json.loads(record.modifiers_json)["replaces"] == creature_types.ELF


def test_a_hidden_species_record_reveals_nothing_to_the_writer() -> None:
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter

    bandit = _humanoid()
    adapter = D20RulesSystemAdapter()
    hidden = adapter.to_writer_view(_record(bandit, creature_types.ELF, "hidden"))
    assert (hidden.check_label, hidden.player_facing_summary) == (
        "",
        "The scene continues.",
    )
    shown = adapter.to_writer_view(_record(bandit, creature_types.ELF))
    assert "elf" not in shown.player_facing_summary.lower()


def test_state_validation_admits_only_a_source_open_humanoid_species() -> None:
    from afterworlds.services.dnd5e_state.validation import validate_creature

    bandit, wolf = _humanoid(), _creature(hp=40)
    assert bandit.index is not None
    ok = bandit.stored.state.model_copy(
        update={"species": _species(bandit, creature_types.ELF)}
    )
    assert validate_creature(bandit.index, ok) == ()
    bad = [
        ok.model_copy(
            update={"species": _species(bandit, "character_origins.not_a_species")}
        ),
        wolf.stored.state.model_copy(
            update={"species": _species(wolf, creature_types.ELF)}
        ),
        ok.model_copy(
            update={
                "species": _species(bandit, creature_types.ELF).model_copy(
                    update={"template_record_key": "monsters.mages.mage"}
                )
            }
        ),
    ]
    for state in bad:
        assert validate_creature(bandit.index, state), state.species


def test_a_species_and_a_ghoul_claw_in_one_turn_refuse_with_no_die() -> None:
    """The Claw is checked before any operation has an effect: a species this
    same turn records is not yet established, so it needs a later turn."""
    from unittest.mock import MagicMock

    from afterworlds.models.enums import DiceHandling
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
    from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
    from tests.pipeline.rpg.test_adjudication_service import (
        _STORY_ID,
        _TURN_ID,
        _FakeProvider,
        _make_assembled,
        _make_session,
    )
    from tests.pipeline.rpg.test_turn_sequencing import actor_turn

    ghoul, bandit, wizard = _creature(GHOUL, hp=40), _humanoid(), _medium_wizard()
    by_id = {str(ghoul.subject_id): ghoul, str(bandit.subject_id): bandit}
    dice = MagicMock()
    proposals = [_species_proposal(bandit, creature_types.ELF), _claw(ghoul, bandit)]
    with pytest.raises(AdjudicationRefusal) as caught:
        RpgAdjudicationPassService(
            adapter=D20RulesSystemAdapter(),
            subject_loader=lambda _story, ref: by_id[str(ref.subject_id)],
            coordination_loader=actor_turn(ghoul),
            bounded_loader=lambda _story, _ref: [],
            aura_loader=lambda _story: [],
        ).adjudicate(
            _make_assembled(),
            _make_session(DiceHandling.AI_ROLLS),
            wizard,
            dice,
            provider=_FakeProvider(
                [p.model_dump(mode="json", exclude_none=True) for p in proposals]
            ),
            story_id=_STORY_ID,
            originating_turn_id=_TURN_ID,
        )
    assert caught.value.kind is RefusalKind.MISSING_STATE
    assert "species is not recorded" in caught.value.detail
    dice.roll.assert_not_called()
