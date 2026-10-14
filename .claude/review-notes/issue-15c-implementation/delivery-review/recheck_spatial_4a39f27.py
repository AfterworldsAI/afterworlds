"""Bounded frozen-source follow-up; no DB or authority writes."""
from pathlib import Path
import hashlib
import importlib.abc
import importlib.util
import json
import subprocess
import sys
from unittest.mock import MagicMock

ROOT = Path.cwd()
REV = "4a39f27becb1ae265ba549727e72846fbce83ae8"
CHANGING = "afterworlds.pipeline.rpg.creature_effects"
SOURCE = "src/afterworlds/pipeline/rpg/creature_effects.py"
frozen = subprocess.check_output(["git", "show", f"{REV}:{SOURCE}"])

loaded_hashes = {}
class FrozenCreatureEffects(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith("afterworlds.pipeline.rpg."):
            source_path = "src/" + fullname.replace(".", "/") + ".py"
            if (ROOT / source_path).is_file():
                return importlib.util.spec_from_loader(fullname, self, origin=str(ROOT / source_path))
        return None
    def create_module(self, spec):
        return None
    def exec_module(self, module):
        source_path = "src/" + module.__name__.replace(".", "/") + ".py"
        content = subprocess.check_output(["git", "show", f"{REV}:{source_path}"])
        module.__file__ = str(ROOT / source_path)
        loaded_hashes[source_path] = hashlib.sha256(content).hexdigest()
        exec(compile(content, module.__file__, "exec"), module.__dict__)

sys.meta_path.insert(0, FrozenCreatureEffects())

from afterworlds.models.enums import DiceHandling, RollVisibility
from afterworlds.models.rpg import CreatureSaveEffectSelection, RollProposal
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
from tests.pipeline.rpg.test_adjudication_service import _STORY_ID, _TURN_ID, _FakeProvider, _make_assembled, _make_session
from tests.pipeline.rpg.test_actor_turns import _edge
from tests.pipeline.rpg.test_creature_attacks import _bite, _ref
from tests.pipeline.rpg.test_masteries import _fighter, GREATCLUB
from tests.pipeline.rpg.test_turn_sequencing import actor_turn
from tests.pipeline.rpg.test_weapon_attacks import _attacker, _creature, _proposal
from tests.rpg_characters import srd_character
from tests.services.dnd5e_state.builders import complete_character, real_index

def run(case, actor, subjects, proposals, auras=()):
    by_id = {str(s.subject_id): s for s in subjects}
    dice = MagicMock()
    try:
        RpgAdjudicationPassService(
            adapter=D20RulesSystemAdapter(),
            subject_loader=lambda _, ref: by_id[str(ref.subject_id)],
            coordination_loader=actor_turn(actor),
            bounded_loader=lambda *_: [],
            aura_loader=lambda _: list(auras),
        ).adjudicate(
            _make_assembled(), _make_session(DiceHandling.AI_ROLLS), actor, dice,
            provider=_FakeProvider([p.model_dump(mode="json", exclude_none=True) for p in proposals]),
            story_id=_STORY_ID, originating_turn_id=_TURN_ID,
        )
    except AdjudicationRefusal as exc:
        row = {"case": case, "kind": exc.kind.value, "detail": exc.detail, "dice_calls": dice.roll.call_count}
        print(json.dumps(row), flush=True)
        assert exc.kind.value == "invalid_selection" and "can move" in exc.detail
        assert dice.roll.call_count == 0
        return
    raise AssertionError(f"{case}: failed to refuse")

actor = _fighter("greatclub", items=(GREATCLUB,))
pushed = _creature(hp=40)
for rule in ("pack_tactics", "close_combat"):
    source = _creature(hp=40) if rule == "pack_tactics" else _creature("monsters.goblins.goblin_warrior", hp=40)
    follow = _bite(source, actor, allies_within_5_feet_of_target=(_ref(pushed),)) if rule == "pack_tactics" else _bite(source, actor, entry="Shortbow", range="within_normal_range", hostiles_within_5_feet=(_ref(pushed),))
    run(rule, actor, (pushed, source), [_proposal(pushed, GREATCLUB, mastery=True, push_ft=10), _edge(actor, "end_turn"), _edge(source), follow])

# The aura source is discovered even though the proposal says none are in range.
paladin = srd_character(complete_character(real_index(), "classes.paladin", 6))
lion, saver = _creature("animals.lion", hp=40), _attacker()
roar = RollProposal(check_label="Roar", subsystem_tag="save", visibility=RollVisibility.SHOWN, operation="creature_save_effect", creature_save_effect=CreatureSaveEffectSelection(source=_ref(lion), entry="Roar", targets=(_ref(saver),), auras_in_range=()))
run("discovered_out_of_range_aura", actor, (paladin, lion, saver), [_proposal(paladin, GREATCLUB, mastery=True, push_ft=10), _edge(actor, "end_turn"), _edge(lion), roar], (paladin,))
print(json.dumps({"frozen_modules": loaded_hashes, "revision": REV, "result": "3 spatial regressions refused before dice"}), flush=True)
