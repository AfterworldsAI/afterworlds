"""Grappled -> Restrained "until the grapple ends" — CRD Issue 15c
(codex-bloodied-linked-conditions-classification): the accepted linked shape
executed through an instance-specific relationship in condition state."""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import ValidationError

from afterworlds.models.dnd5e_state import (
    ConditionInstance,
    CreatureState,
    SubjectReference,
)
from afterworlds.models.enums import ConditionVisibility
from afterworlds.models.rpg import SheetEffect
from afterworlds.services.dnd5e_state.turn import with_effects
from tests.pipeline.rpg.test_creature_attacks import (
    _bite,
    _medium_wizard,
    _resolve,
    _subjects,
)
from tests.pipeline.rpg.test_weapon_attacks import _creature, _dice

WORM = "monsters.purple_worm.purple_worm"
REMORHAZ = "monsters.remorhaz.remorhaz"


def _conditions(record: Any) -> list[dict[str, Any]]:
    return [
        json.loads(e.value_json)
        for e in record.sheet_effects
        if e.operation == "apply_condition"
    ]


@pytest.mark.parametrize("template", [WORM, REMORHAZ])
def test_a_bite_grapples_and_restrains_until_that_grapple_ends(template: str) -> None:
    wolf = _creature(hp=200)
    biter = _creature(template, hp=250)
    record = _resolve(
        _bite(biter, wolf, entry="Bite", target_within_5_feet=False),
        _medium_wizard(),
        _subjects(biter, wolf),
        _dice((19,), (1,)),
    )
    grappled, restrained = _conditions(record)
    assert (grappled["condition"], restrained["condition"]) == (
        "grappled",
        "restrained",
    )
    assert restrained["lasts_while_instance"] == grappled["instance_id"]
    assert grappled["escape_dc"] in (17, 19)
    held = with_effects(wolf, [e for e in record.sheet_effects])
    state = held.stored.state
    assert [c.condition.value for c in state.conditions or ()] == [
        "grappled",
        "restrained",
    ]
    # Round trip through the persisted document.
    again = CreatureState.model_validate_json(state.model_dump_json())
    assert again == state


def _clear(subject: Any, **which: str) -> Any:
    return with_effects(
        subject,
        [
            SheetEffect(
                target="condition",
                operation="clear_condition",
                value_json=json.dumps(which),
                subject_kind="creature",
                subject_id=subject.subject_id,
            )
        ],
    )


def test_ending_the_grapple_ends_only_its_own_restraint() -> None:
    """A second grapple and an unrelated Restrained survive; clearing the
    first grapple, by instance or by kind, removes exactly its dependant."""
    wolf = _creature(hp=200)
    worm, remorhaz = _creature(WORM, hp=250), _creature(REMORHAZ, hp=250)
    net = ConditionInstance(
        instance_id="net",
        condition="restrained",  # type: ignore[arg-type]
        visibility=ConditionVisibility.VISIBLE,
    )
    state = wolf.stored.state.model_copy(update={"conditions": (net,)})
    import dataclasses

    wolf = dataclasses.replace(
        wolf, stored=dataclasses.replace(wolf.stored, state=state)
    )
    for biter in (worm, remorhaz):
        record = _resolve(
            _bite(biter, wolf, entry="Bite", target_within_5_feet=False),
            _medium_wizard(),
            _subjects(biter, wolf),
            _dice((19,), (1,)),
        )
        wolf = with_effects(wolf, list(record.sheet_effects))
    conditions = wolf.stored.state.conditions or ()
    first = next(c for c in conditions if c.condition.value == "grappled")
    left = _clear(wolf, instance_id=first.instance_id).stored.state.conditions or ()
    assert sorted(c.condition.value for c in left) == [
        "grappled",
        "restrained",
        "restrained",
    ]
    assert any(c.instance_id == "net" for c in left)
    assert all(c.lasts_while_instance != first.instance_id for c in left)
    # Clearing Grappled by kind ends every grapple and each one's dependant.
    gone = _clear(wolf, condition="grappled").stored.state.conditions or ()
    assert [c.instance_id for c in gone] == ["net"]


def test_immunity_follows_each_condition() -> None:
    """Immune to Grappled (a swarm): neither applies. Immune to Restrained
    only (Guardian Naga): the grapple applies alone."""
    worm = _creature(WORM, hp=250)
    for template, expected in (
        ("animals.swarm_of_rats", []),
        ("monsters.guardian_naga.guardian_naga", ["grappled"]),
    ):
        target = _creature(template, hp=200)
        record = _resolve(
            _bite(worm, target, entry="Bite", target_within_5_feet=False),
            _medium_wizard(),
            _subjects(worm, target),
            _dice((19,), (1,)),
        )
        assert [c["condition"] for c in _conditions(record)] == expected


@pytest.mark.parametrize("problem", ["dangling", "not_grappled", "other_referent"])
def test_a_malformed_link_is_refused_by_the_state(problem: str) -> None:
    worm = SubjectReference(kind="creature", subject_id=_creature(WORM).subject_id)
    other = SubjectReference(kind="creature", subject_id=_creature().subject_id)
    held = ConditionInstance(
        instance_id="g",
        condition="prone" if problem == "not_grappled" else "grappled",  # type: ignore[arg-type]
        visibility=ConditionVisibility.VISIBLE,
        referent=worm,
        escape_dc=None if problem == "not_grappled" else 19,
    )
    linked = ConditionInstance(
        instance_id="r",
        condition="restrained",  # type: ignore[arg-type]
        visibility=ConditionVisibility.VISIBLE,
        referent=other if problem == "other_referent" else worm,
        lasts_while_instance="missing" if problem == "dangling" else "g",
    )
    base = _creature().stored.state
    with pytest.raises(ValidationError):
        CreatureState.model_validate(
            {
                **base.model_dump(mode="json"),
                "conditions": [
                    held.model_dump(mode="json"),
                    linked.model_dump(mode="json"),
                ],
            }
        )


def test_the_purple_worms_multiattack_executes() -> None:
    from tests.pipeline.rpg.test_creature_attacks import _multiattack_turn

    worm = _creature(WORM, hp=247)
    result, _ = _multiattack_turn(
        worm, ["Bite", "Tail Stinger"], target_within_5_feet=False
    )
    assert [json.loads(r.modifiers_json)["entry"] for r in result.proposals] == [
        "Bite",
        "Tail Stinger",
    ]
