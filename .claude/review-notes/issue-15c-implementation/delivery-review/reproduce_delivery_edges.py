"""Read-only C7 execution review: real accepted test authority, no stores."""
import dataclasses
import json
from uuid import uuid4

from afterworlds.models.enums import DiceHandling
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
from tests.pipeline.rpg.test_adjudication_service import (
    _FakeProvider, _STORY_ID, _TURN_ID, _make_assembled, _make_session,
)
from tests.pipeline.rpg.test_turn_sequencing import actor_turn, _dice
from tests.pipeline.rpg.test_weapon_attacks import (
    DAGGER, _attacker, _creature, _proposal, _shot, hands_for,
)


def run(actor, target, proposals, others=()):
    dice = _dice()
    subjects = {str(s.subject_id): s for s in (target, *others)}
    svc = RpgAdjudicationPassService(
        D20RulesSystemAdapter(),
        subject_loader=lambda _story, ref: subjects[str(ref.subject_id)],
        coordination_loader=actor_turn(actor),
        bounded_loader=lambda *_: [],
    )
    try:
        result = svc.adjudicate(
            _make_assembled(), _make_session(DiceHandling.AI_ROLLS), actor, dice,
            provider=_FakeProvider([p.model_dump(mode="json") for p in proposals]),
            story_id=_STORY_ID, originating_turn_id=_TURN_ID,
        )
        return {"result": "accepted", "dice_calls": dice.roll.call_count,
                "outcomes": [r.outcome for r in result.proposals],
                "advantage": [json.loads(r.modifiers_json).get("advantage_sources") for r in result.proposals]}
    except AdjudicationRefusal as exc:
        return {"result": "refused", "kind": exc.kind.value,
                "detail": exc.detail, "dice_calls": dice.roll.call_count}


other = dataclasses.replace(DAGGER, item_id=uuid4())
target = _creature(hp=40)
actor = _attacker(DAGGER, other)
hands = hands_for(DAGGER, other)
first = _proposal(target, DAGGER, hands=hands, ability="strength")
second = _proposal(target, other, hands=hands, ability="strength", extra="light")
print(json.dumps({"case": "two distinct dagger items, legal Light attack", **run(actor, target, [first, second])}))

actor, target, shot = _shot("hand_crossbow", "bolts")
print(json.dumps({"case": "Hand Crossbow gripped with both hands and zero free hands", **run(actor, target, [shot])}))

# Positive control: the same one-handed weapon with its required free hand.
sel = shot.weapon_attack
control = shot.model_copy(update={"weapon_attack": sel.model_copy(update={"hands": hands_for(actor.items[0])})})
print(json.dumps({"case": "Hand Crossbow one hand with free hand", **run(actor, target, [control])}))

from tests.pipeline.rpg.test_masteries import _fighter, GREATCLUB
from tests.pipeline.rpg.test_creature_attacks import _bite, _ref
from tests.pipeline.rpg.test_actor_turns import _edge

actor = _fighter("greatclub", items=(GREATCLUB,))
target, wolf = _creature(hp=40), _creature(hp=40)
push = _proposal(target, GREATCLUB, mastery=True, push_ft=10)
bite = _bite(wolf, actor, allies_within_5_feet_of_target=(_ref(target),))
print(json.dumps({"case": "Push ally then consume its old Pack Tactics proximity", **run(actor, target, [push, _edge(actor, "end_turn"), _edge(wolf), bite], (wolf,))}))
