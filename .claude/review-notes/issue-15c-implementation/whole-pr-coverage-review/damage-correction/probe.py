"""Frozen, read-only correction check for one CRD Issue 15c damage family."""

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
REV = "6caa63e36a143feab0d3ddec50175803d24ee8c4"
OUT = ROOT / ".claude/review-notes/issue-15c-implementation/whole-pr-coverage-review/damage-correction/results.json"
ORACLE = "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json"
SOURCE = "docs/sources/community/dnd-5e-srd-markdown/playing-the-game.md"
DAMAGE = "src/afterworlds/pipeline/rpg/damage.py"


def blob(relative: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{REV}:{relative}"], cwd=ROOT)


for relative in (ORACLE, SOURCE):
    assert (ROOT / relative).read_bytes() == blob(relative), relative

paths = set(
    subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", REV], text=True, cwd=ROOT
    ).splitlines()
)


class Loader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname: str):
        relative = Path(self.path).relative_to(ROOT).as_posix()
        return compile(blob(relative), self.path, "exec")


class Frozen(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path=None, target=None):
        if not (
            fullname == "afterworlds"
            or fullname.startswith("afterworlds.")
            or fullname == "tests"
            or fullname.startswith("tests.")
        ):
            return None
        stem = ("src/" if fullname.startswith("afterworlds") else "") + fullname.replace(".", "/")
        for relative in (stem + "/__init__.py", stem + ".py"):
            if relative in paths:
                filename = str(ROOT / relative)
                return importlib.util.spec_from_file_location(
                    fullname, filename, loader=Loader(fullname, filename)
                )
        return None


sys.meta_path.insert(0, Frozen())
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from afterworlds.ingestion.mechanical.representation import DamageType  # noqa: E402
from afterworlds.models.dnd5e_state import ZeroHitPointTreatment  # noqa: E402
from afterworlds.pipeline.rpg.damage import take_damage  # noqa: E402
from tests.pipeline.rpg.test_actor_turns import _dying  # noqa: E402
from tests.pipeline.rpg.test_zero_hp_lifecycle import _stable  # noqa: E402
from tests.pipeline.rpg.test_weapon_attacks import _creature  # noqa: E402


def with_hp(subject, *, current=None, temporary=None):
    hp = subject.stored.state.hit_points
    assert hp is not None
    updates = {}
    if current is not None:
        updates["current"] = current
    if temporary is not None:
        updates["temporary"] = temporary
    state = subject.stored.state.model_copy(
        update={"hit_points": hp.model_copy(update=updates)}
    )
    return dataclasses.replace(
        subject, stored=dataclasses.replace(subject.stored, state=state)
    )


def run(label, subject, amount, damage_type=DamageType.PIERCING, critical=False):
    result = take_damage(subject, amount, damage_type, critical=critical)
    effects = {e.target: json.loads(e.value_json) for e in result.effects}
    return {
        "case": label,
        "incoming": amount,
        "maximum": subject.stored.state.hit_points.maximum,
        "taken": result.taken,
        "outcome": result.outcome,
        "effects": effects,
    }


dying = _dying(successes=1, failures=0)
stable = _stable()
cases = [
    run("dying_fully_absorbed", with_hp(dying, temporary=5), 3),
    run("stable_fully_absorbed", with_hp(stable, temporary=5), 3),
    run("equals_maximum", with_hp(dying, temporary=5), 11),
    run("below_maximum", with_hp(dying, temporary=5), 9),
    run("dying_without_temporary", dying, 3),
    run("stable_without_temporary", stable, 3),
    run("zero_incoming", with_hp(dying, temporary=5), 0),
    run("above_zero_absorption", with_hp(_creature(hp=11, treatment=ZeroHitPointTreatment(subject="character")), current=7, temporary=5), 3),
    run("critical_absorbed", with_hp(dying, temporary=5), 3, critical=True),
]
immune = _creature(
    "monsters.skeletons.skeleton", hp=11,
    treatment=ZeroHitPointTreatment(
        subject="monster", gamemaster_exception="treat_as_character"
    ),
)
cases.append(run("immune_at_zero", with_hp(immune, current=0, temporary=5), 3, DamageType.POISON))
by = {c["case"]: c for c in cases}

assert by["dying_fully_absorbed"]["outcome"] == "death_save_failure"
assert by["dying_fully_absorbed"]["effects"]["temporary_hp"] == 2
assert by["dying_fully_absorbed"]["effects"]["death_state"]["failures"] == 1
assert by["stable_fully_absorbed"]["outcome"] == "death_save_failure"
assert by["stable_fully_absorbed"]["effects"]["temporary_hp"] == 2
assert by["stable_fully_absorbed"]["effects"]["death_state"]["stable"] is False
assert by["stable_fully_absorbed"]["effects"]["death_state"]["stable_recovery"] is None
assert by["equals_maximum"]["outcome"] == "died"
assert by["equals_maximum"]["effects"]["death_state"]["dead"] is True
assert by["equals_maximum"]["effects"]["temporary_hp"] == 0
assert by["below_maximum"]["outcome"] == "death_save_failure"
assert by["below_maximum"]["effects"]["death_state"]["dead"] is False
for label in ("dying_without_temporary", "stable_without_temporary"):
    assert by[label]["outcome"] == "death_save_failure"
    assert "temporary_hp" not in by[label]["effects"]
assert by["zero_incoming"]["taken"] == 0 and by["zero_incoming"]["effects"] == {}
assert by["above_zero_absorption"]["outcome"] == "absorbed"
assert by["above_zero_absorption"]["effects"] == {"temporary_hp": 2}
assert by["critical_absorbed"]["effects"]["death_state"]["failures"] == 2
assert by["critical_absorbed"]["effects"]["temporary_hp"] == 2
assert by["immune_at_zero"]["taken"] == 0 and by["immune_at_zero"]["effects"] == {}
for relative in (ORACLE, SOURCE):
    assert (ROOT / relative).read_bytes() == blob(relative), relative

OUT.write_text(
    json.dumps(
        {
            "revision": REV,
            "oracle_sha256": hashlib.sha256(blob(ORACLE)).hexdigest(),
            "source_sha256": hashlib.sha256(blob(SOURCE)).hexdigest(),
            "damage_sha256": hashlib.sha256(blob(DAMAGE)).hexdigest(),
            "cases": cases,
        },
        indent=2,
    ) + "\n",
    encoding="utf-8",
)
print(json.dumps({"revision": REV, "cases": len(cases), "output": str(OUT)}))
