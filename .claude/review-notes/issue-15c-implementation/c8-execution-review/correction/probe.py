"""Read-only C8 execution controls, all project/test Python frozen to REV."""
from pathlib import Path
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import subprocess
import sys

ROOT = Path.cwd()
REV = "c6c2b2ad295d7d474eaa900a77988af20832e7d5"
paths = set(subprocess.check_output(["git", "ls-tree", "-r", "--name-only", REV], text=True).splitlines())
hashes = {}
results = []
def emit(output):
    results.append(output)
    print(json.dumps(output), flush=True)
class Loader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname):
        relative = Path(self.path).relative_to(ROOT).as_posix()
        source = subprocess.check_output(["git", "show", f"{REV}:{relative}"])
        hashes[relative] = hashlib.sha256(source).hexdigest()
        return compile(source, self.path, "exec")
class Frozen(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
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

# Non-Python authority is preserved, hash-pinned, and rechecked at the end.
ORACLE = ROOT / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json"
oracle_before = hashlib.sha256(ORACLE.read_bytes()).hexdigest()
assert oracle_before == "ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d"

from afterworlds.models.enums import DiceHandling
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
from tests.pipeline.rpg.test_adjudication_service import _STORY_ID, _TURN_ID, _FakeProvider, _make_assembled, _make_session
from tests.pipeline.rpg.test_creature_types import _humanoid, _species_proposal, _medium_wizard, _with, _species, _claw, GHOUL
from tests.pipeline.rpg.test_creature_attacks import _bite
from tests.pipeline.rpg.test_weapon_attacks import _creature, _dice
from tests.pipeline.rpg.test_turn_sequencing import actor_turn

def run(case, actor, subjects, proposals, active=None, roller=None):
    by_id = {str(s.subject_id): s for s in subjects}
    dice = roller if roller is not None else _dice((15,), (1,))
    try:
        result = RpgAdjudicationPassService(
            adapter=D20RulesSystemAdapter(),
            subject_loader=lambda _, ref: by_id[str(ref.subject_id)],
            coordination_loader=actor_turn(active or actor),
            bounded_loader=lambda *_: [], aura_loader=lambda *_: [],
        ).adjudicate(_make_assembled(), _make_session(DiceHandling.AI_ROLLS), actor, dice,
            provider=_FakeProvider([p.model_dump(mode="json") for p in proposals]),
            story_id=_STORY_ID, originating_turn_id=_TURN_ID)
        output = {"result": "accepted", "operations": len(result.proposals), "effects": [e.model_dump(mode="json") for r in result.proposals for e in r.sheet_effects]}
    except Exception as exc:
        output = {"result": "error", "exception": type(exc).__name__, "detail": str(exc)}
    output.update(case=case, dice_calls=dice.calls)
    emit(output)

from afterworlds.models.dnd5e_state import SummonOrigin, GrantSource, CreaturePresence, ZeroHitPointTreatment
from afterworlds.models.dnd5e_vocabulary import CreatureType
from afterworlds.models.rpg import LifecycleAttestation
from afterworlds.services.dnd5e_state.validation import validate_creature, creature_readiness
from afterworlds.services.dnd5e_state.effects import apply_effects
from tests.pipeline.rpg.test_weapon_attacks import _attacker, _proposal, CLUB
from tests.pipeline.rpg.test_creature_attacks import _ref
from tests.pipeline.rpg.test_creature_effects import _wyrmling, _breath
from tests.pipeline.rpg.test_actor_turns import _dying, _edge
from tests.pipeline.rpg.test_zero_hp_lifecycle import _stable, _op, _knocked_out
from tests.pipeline.rpg.test_creature_types import _record

def refuse(*args, **kwargs):
    run(*args, **kwargs)
    assert results[-1]["exception"] == "AdjudicationRefusal", results[-1]
    assert results[-1]["dice_calls"] == [], results[-1]

def accept(*args, **kwargs):
    run(*args, **kwargs)
    assert results[-1]["result"] == "accepted", results[-1]

def familiarize(subject, presence=CreaturePresence.PRESENT):
    result = _with(subject, template_record_key="animals.cat", summon=SummonOrigin(source=GrantSource(record_key="spells.find_familiar")), creature_type=CreatureType.FEY, presence=presence, hazards=())
    assert validate_creature(result.index, result.stored.state) == ()
    if presence is not None:
        assert creature_readiness(result.stored.state) == ()
    return result

wizard, wolf, bandit, bandit2 = _medium_wizard(), _creature(hp=40), _humanoid(), _humanoid()
one = _species_proposal(bandit, "character_origins.elf")
for second in (one, _species_proposal(bandit, "character_origins.dwarf")):
    refuse("duplicate species before any earlier valid attack dice: " + second.species, wizard, [wolf, bandit], [_bite(wolf, wizard), one, second], wolf)
accept("two independent species selections execute together", wizard, [bandit, bandit2], [one, _species_proposal(bandit2, "character_origins.dwarf")])
assert len(results[-1]["effects"]) == 2
assert {e["subject_id"] for e in results[-1]["effects"]} == {str(bandit.subject_id), str(bandit2.subject_id)}

hidden_record = _record(bandit, "character_origins.elf", "hidden")
hidden_state = apply_effects(bandit.stored.state, hidden_record.sheet_effects)
hidden_subject = _with(bandit, species=hidden_state.species)
writer = D20RulesSystemAdapter().to_writer_view(hidden_record)
assert "elf" not in writer.model_dump_json().lower()
refuse("repeat hidden stored selection yields identity-free public error", wizard, [hidden_subject], [_species_proposal(hidden_subject, "character_origins.dwarf")])
assert "elf" not in results[-1]["detail"].lower()

cat = familiarize(_creature("animals.cat", hp=40))
ghoul = _creature(GHOUL, hp=40)
refuse("present Familiar cannot attack", wizard, [cat, bandit], [_bite(cat, bandit, entry="Scratch")], cat)
for presence in (None, CreaturePresence.POCKET_DIMENSION, CreaturePresence.GONE, CreaturePresence.PRESENT):
    target = familiarize(cat, presence)
    refuse("Ghoul target Familiar presence " + str(presence), wizard, [ghoul, target], [_claw(ghoul, target)], ghoul)

low = _with(cat, hit_points=cat.stored.state.hit_points.model_copy(update={"current": 1}))
warrior, dragon = _attacker(CLUB), _wyrmling()
refuse("shared weapon damage holds Familiar", warrior, [low], [_proposal(low)], roller=_dice((15,), (3,)))
refuse("shared direct-save damage holds Familiar", wizard, [dragon, low], [_breath(dragon, low)], dragon, roller=_dice((2,), (10,)))
for presence in (CreaturePresence.PRESENT, CreaturePresence.GONE):
    dying = familiarize(_dying(), presence)
    dying = _with(dying, zero_hit_point_treatment=ZeroHitPointTreatment(subject="monster", gamemaster_exception="treat_as_character"))
    refuse("Familiar first aid " + presence.value, wizard, [dying], [_op(dying, "stabilize")], roller=_dice((15,), (2,)))
    refuse("Familiar death save " + presence.value, wizard, [dying], [_edge(wizard, "end_turn"), _edge(dying)], roller=_dice((20,), (2,)))
    stable = familiarize(_stable(3), presence)
    refuse("Familiar Stable recovery " + presence.value, wizard, [stable], [_op(stable, "stable_recovery", LifecycleAttestation(instance_id="rec", elapsed_hours=3))])
    knocked = familiarize(_knocked_out(), presence)
    refuse("Familiar knockout recovery hold " + presence.value, wizard, [knocked], [_op(knocked, "knockout_recovery", LifecycleAttestation(instance_id="ko"))])

# The new guard must leave ordinary animals and their bounded lifecycle intact.
ordinary = _creature(hp=1)
accept("ordinary Club damage remains executable", warrior, [ordinary], [_proposal(ordinary)], roller=_dice((15,), (3,)))
accept("ordinary direct-save damage remains executable", wizard, [dragon, ordinary], [_breath(dragon, ordinary)], dragon, roller=_dice((2,), (10,)))
accept("ordinary Ghoul target remains executable", wizard, [ghoul, ordinary], [_claw(ghoul, ordinary)], ghoul)
dying = _dying()
accept("ordinary first aid remains executable", wizard, [dying], [_op(dying, "stabilize")], roller=_dice((15,), (2,)))
accept("ordinary death-save recovery remains executable", wizard, [dying], [_edge(wizard, "end_turn"), _edge(dying)], roller=_dice((20,), (2,)))
stable = _stable(3)
accept("ordinary Stable recovery remains executable", wizard, [stable], [_op(stable, "stable_recovery", LifecycleAttestation(instance_id="rec", elapsed_hours=3))])
knocked = _knocked_out()
accept("ordinary knockout recovery remains executable", wizard, [knocked], [_op(knocked, "knockout_recovery", LifecycleAttestation(instance_id="ko"))])

# Same presence family: a named physical participant must also be present when
# used as the source-qualified ally in an existing attack context.
gone = familiarize(cat, CreaturePresence.POCKET_DIMENSION)
run("presence residue check: dismissed Familiar as Pack Tactics ally", wizard, [wolf, gone], [_bite(wolf, wizard, allies_within_5_feet_of_target=(_ref(gone),))], wolf, roller=_dice((12,15), (1,)))

assert hashlib.sha256(ORACLE.read_bytes()).hexdigest() == oracle_before
outdir = ROOT / ".claude/review-notes/issue-15c-implementation/c8-execution-review/correction"
(outdir / "results.json").write_text(json.dumps({"revision": REV, "authority_sha256": oracle_before, "results": results, "frozen_modules": hashes}, indent=2), encoding="utf-8")
print(json.dumps({"checks": len(results), "frozen_modules": len(hashes), "source_revision": REV}), flush=True)

