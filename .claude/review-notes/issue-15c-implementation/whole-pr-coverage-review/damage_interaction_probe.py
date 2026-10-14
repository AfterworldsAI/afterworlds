"""Read-only CRD Issue 15c damage interaction probe from immutable Git blobs."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
REV = "c6c2b2ad295d7d474eaa900a77988af20832e7d5"
OUT = ROOT / ".claude/review-notes/issue-15c-implementation/whole-pr-coverage-review/damage-interaction-results.json"
ORACLE = "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json"
SOURCE = "docs/sources/community/dnd-5e-srd-markdown/playing-the-game.md"

def blob(relative: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{REV}:{relative}"], cwd=ROOT)

assert not subprocess.check_output(
    ["git", "diff", "--name-only", REV, "--", "src/afterworlds/ingestion/mechanical/oracles", "docs/sources"], cwd=ROOT
)
for relative in (ORACLE, SOURCE):
    assert (ROOT / relative).read_bytes() == blob(relative), relative

paths = set(subprocess.check_output(["git", "ls-tree", "-r", "--name-only", REV], text=True, cwd=ROOT).splitlines())
loaded: dict[str, str] = {}

class Loader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname: str):
        relative = Path(self.path).relative_to(ROOT).as_posix()
        source = blob(relative)
        loaded[relative] = hashlib.sha256(source).hexdigest()
        return compile(source, self.path, "exec")

class Frozen(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path=None, target=None):
        if not (fullname == "afterworlds" or fullname.startswith("afterworlds.") or fullname == "tests" or fullname.startswith("tests.")):
            return None
        stem = ("src/" if fullname.startswith("afterworlds") else "") + fullname.replace(".", "/")
        for relative in (stem + "/__init__.py", stem + ".py"):
            if relative in paths:
                filename = str(ROOT / relative)
                return importlib.util.spec_from_file_location(fullname, filename, loader=Loader(fullname, filename))
        return None

sys.meta_path.insert(0, Frozen())
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from afterworlds.ingestion.mechanical.representation import (
    DamageAtZeroHitPointsFact, DamageType, StableStateFact, TemporaryHitPointAbsorptionFact
)
from afterworlds.models.dnd5e_state import HitPoints, ZeroHitPointTreatment
from afterworlds.pipeline.rpg.damage import take_damage
from afterworlds.pipeline.rpg.defense import facts_of
from tests.pipeline.rpg.test_actor_turns import _dying
from tests.pipeline.rpg.test_zero_hp_lifecycle import _stable
from tests.pipeline.rpg.test_weapon_attacks import _creature

def with_hp(subject, *, current: int | None = None, temporary: int | None = None):
    hp = subject.stored.state.hit_points
    assert hp is not None
    updates = {}
    if current is not None:
        updates["current"] = current
    if temporary is not None:
        updates["temporary"] = temporary
    state = subject.stored.state.model_copy(update={"hit_points": hp.model_copy(update=updates)})
    return dataclasses.replace(subject, stored=dataclasses.replace(subject.stored, state=state))

def run(label: str, subject, amount: int, damage_type=DamageType.PIERCING, critical=False):
    result = take_damage(subject, amount, damage_type, critical=critical)
    effects = {e.target: json.loads(e.value_json) for e in result.effects}
    return {"case": label, "incoming": amount, "current_before": subject.stored.state.hit_points.current,
            "temporary_before": subject.stored.state.hit_points.temporary, "maximum": subject.stored.state.hit_points.maximum,
            "taken": result.taken, "outcome": result.outcome, "effects": effects}

dying = _dying(successes=1, failures=0)
stable = _stable()
index = dying.index
facts = {}
for name, cls in (("lost_first", TemporaryHitPointAbsorptionFact),
                  ("damage_at_0_hit_points", DamageAtZeroHitPointsFact),
                  ("stable", StableStateFact)):
    rows = [f for f in facts_of(index, "play.damage_and_healing", name) if isinstance(f, cls)]
    assert len(rows) == 1, (name, rows)
    facts[name] = repr(rows[0])

cases = [
    run("dying_at_zero_fully_absorbed", with_hp(dying, temporary=5), 3),
    run("stable_at_zero_fully_absorbed", with_hp(stable, temporary=5), 3),
    run("dying_at_zero_damage_equals_max_with_temp", with_hp(dying, temporary=5), 11),
    run("dying_at_zero_partial_temp_below_max", with_hp(dying, temporary=5), 9),
    run("dying_at_zero_without_temp", dying, 3),
    run("stable_at_zero_without_temp", stable, 3),
    run("dying_at_zero_zero_incoming", with_hp(dying, temporary=5), 0),
    run("positive_hp_temp_absorption", with_hp(_creature(hp=11, treatment=ZeroHitPointTreatment(subject="character")), current=7, temporary=5), 3),
]
immune = _creature("monsters.skeletons.skeleton", hp=11,
                   treatment=ZeroHitPointTreatment(subject="monster", gamemaster_exception="treat_as_character"))
cases.append(run("immune_at_zero_poison", with_hp(immune, current=0, temporary=5), 3, DamageType.POISON))

assert cases[0]["taken"] == 3 and cases[0]["outcome"] == "absorbed" and "death_state" not in cases[0]["effects"]
assert cases[1]["taken"] == 3 and cases[1]["outcome"] == "absorbed" and "death_state" not in cases[1]["effects"]
assert cases[2]["taken"] == cases[2]["maximum"] and cases[2]["outcome"] == "death_save_failure"
assert cases[4]["outcome"] == "death_save_failure" and cases[5]["outcome"] == "death_save_failure"
assert cases[6]["taken"] == 0 and "death_state" not in cases[6]["effects"]
assert cases[7]["outcome"] == "absorbed" and cases[7]["effects"]["temporary_hp"] == 2
assert cases[8]["taken"] == 0 and "death_state" not in cases[8]["effects"]
assert (ROOT / ORACLE).read_bytes() == blob(ORACLE)
assert (ROOT / SOURCE).read_bytes() == blob(SOURCE)

payload = {"revision": REV, "authority_sha256": hashlib.sha256(blob(ORACLE)).hexdigest(),
           "source_sha256": hashlib.sha256(blob(SOURCE)).hexdigest(),
           "damage_module_sha256": loaded["src/afterworlds/pipeline/rpg/damage.py"],
           "typed_facts": facts, "cases": cases, "frozen_modules": loaded}
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"revision": REV, "cases": cases, "output": str(OUT)}, indent=2))
