"""CRD Issue 15c — certification scope (AC2): an operation's pinned shared
procedure covers only what it reads, and each creature an operation reads is
certified per subject against its own binding's template."""

from __future__ import annotations

import dataclasses
import json
from typing import Any
from uuid import uuid4

import pytest

from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import (
    AdjudicationRefusal,
    Operation,
    RefusalKind,
    governing_fingerprint,
)
from afterworlds.services.dnd5e_state.turn import TurnCreature
from tests.pipeline.rpg.test_bounded_checks import _with_component
from tests.pipeline.rpg.test_creature_attacks import (
    _bite,
    _medium_wizard,
    _resolve,
    _subjects,
)
from tests.pipeline.rpg.test_weapon_attacks import (
    CLUB,
    _attacker,
    _creature,
    _dice,
    _proposal,
    _run,
)
from tests.services.dnd5e_state.builders import real_index

WOLF = "animals.wolf"


def _with_index(creature: TurnCreature, index: Any) -> TurnCreature:
    return dataclasses.replace(creature, index=index)


def test_an_unrelated_fixed_dc_override_leaves_other_operations_certified() -> None:
    climb = _with_component(
        real_index(),
        "glossary.climbing",
        "difficult_climb",
        supplied_by_override_id="house-rule",
    )
    base = real_index()
    assert governing_fingerprint(climb, Operation.FIXED_DC_CHECK) != (
        governing_fingerprint(base, Operation.FIXED_DC_CHECK)
    )
    for operation in (Operation.WEAPON_ATTACK, Operation.CREATURE_ATTACK):
        assert governing_fingerprint(climb, operation) == governing_fingerprint(
            base, operation
        )


@pytest.mark.parametrize("how", ["supplied", "suppressed"])
def test_an_overridden_creature_template_is_not_certified(how: str) -> None:
    index = real_index()
    if how == "supplied":
        changed = _with_component(
            index, WOLF, "wolf", supplied_by_override_id="house-rule"
        )
    else:  # a suppression leaves no supplied_by marker on what remains
        changed = dataclasses.replace(index, overridden=frozenset({WOLF}))
    wolf = _with_index(_creature(hp=40), changed)
    wizard = _medium_wizard()
    for proposal, actor in (
        (_bite(wolf, wizard), wizard),  # the template's own attack
        (_proposal(wolf), _attacker(CLUB)),  # its AC and defenses as a target
    ):
        with pytest.raises(AdjudicationRefusal) as caught:
            D20RulesSystemAdapter().require_supported(proposal, actor, _subjects(wolf))
        assert caught.value.kind is RefusalKind.INCOMPATIBLE_CERTIFICATION


def test_an_unchanged_template_is_certified_across_bindings() -> None:
    # Another override set that touches nothing the attack reads.
    other = real_index().binding.model_copy(update={"override_set_uuid": uuid4()})
    wolf = _with_index(
        _creature(hp=40), dataclasses.replace(real_index(), binding=other)
    )
    wizard = _medium_wizard()
    record = _resolve(_bite(wolf, wizard), wizard, _subjects(wolf), _dice((18,), (3,)))
    templates = json.loads(record.modifiers_json)["templates"]
    assert list(templates) == [f"creature:{wolf.subject_id}"]
    # A weapon attack against it records the target's template too.
    record = _run(_attacker(CLUB), wolf, _proposal(wolf), _dice((15,), (3,)))
    assert json.loads(record.modifiers_json)["templates"]
