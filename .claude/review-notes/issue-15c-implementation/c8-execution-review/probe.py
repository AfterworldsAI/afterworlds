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
REV = "555be9aed30e48bd05a469c73092177bb676e400"
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

wizard, wolf, bandit = _medium_wizard(), _creature(hp=40), _humanoid()
if "siblings" in sys.argv:
    from afterworlds.models.dnd5e_state import SummonOrigin, GrantSource, CreaturePresence, ZeroHitPointTreatment
    from afterworlds.models.dnd5e_vocabulary import CreatureType
    from afterworlds.models.rpg import LifecycleAttestation
    from afterworlds.services.dnd5e_state.validation import validate_creature, creature_readiness
    from tests.pipeline.rpg.test_weapon_attacks import _attacker, _proposal, CLUB
    from tests.pipeline.rpg.test_creature_effects import _wyrmling, _breath
    from tests.pipeline.rpg.test_actor_turns import _dying, _edge
    from tests.pipeline.rpg.test_zero_hp_lifecycle import _stable, _op
    def familiarize(subject, presence=CreaturePresence.PRESENT):
        result = _with(subject, template_record_key="animals.cat", summon=SummonOrigin(source=GrantSource(record_key="spells.find_familiar")), creature_type=CreatureType.FEY, presence=presence, hazards=())
        assert validate_creature(result.index, result.stored.state) == ()
        assert creature_readiness(result.stored.state) == ()
        return result
    low = familiarize(_creature("animals.cat", hp=40))
    low = _with(low, hit_points=low.stored.state.hit_points.model_copy(update={"current": 1}))
    warrior = _attacker(CLUB)
    run("weapon Club drops Familiar to zero through shared damage", warrior, [low], [_proposal(low)], roller=_dice((15,), (3,)))
    dragon = _wyrmling()
    run("direct Acid Breath save drops Familiar to zero through shared damage", wizard, [dragon, low], [_breath(dragon, low)], dragon, roller=_dice((2,), (10,)))
    dying = familiarize(_dying(), CreaturePresence.GONE)
    dying = _with(dying, zero_hit_point_treatment=ZeroHitPointTreatment(subject="monster", gamemaster_exception="treat_as_character"))
    run("first aid stabilizes a gone Familiar at zero", wizard, [dying], [_op(dying, "stabilize")], roller=_dice((15,), (2,)))
    run("actor-turn death save naturally recovers a gone Familiar", wizard, [dying], [_edge(wizard, "end_turn"), _edge(dying)], roller=_dice((20,), (2,)))
    stable = familiarize(_stable(3), CreaturePresence.GONE)
    stable = _with(stable, zero_hit_point_treatment=ZeroHitPointTreatment(subject="monster", gamemaster_exception="treat_as_character"))
    run("elapsed stable recovery restores HP on a gone Familiar", wizard, [stable], [_op(stable, "stable_recovery", LifecycleAttestation(instance_id="rec", elapsed_hours=3))])
    assert hashlib.sha256(ORACLE.read_bytes()).hexdigest() == oracle_before
    outdir = ROOT / ".claude/review-notes/issue-15c-implementation/c8-execution-review"
    (outdir / "sibling-results.json").write_text(json.dumps({"revision": REV, "authority_sha256": oracle_before, "results": results, "frozen_modules": hashes}, indent=2), encoding="utf-8")
    sys.exit(0)
if "visibility" in sys.argv:
    from tests.pipeline.rpg.test_creature_types import _record
    from afterworlds.services.dnd5e_state.effects import apply_effects
    hidden_record = _record(bandit, "character_origins.elf", "hidden")
    hidden_state = apply_effects(bandit.stored.state, hidden_record.sheet_effects)
    hidden_subject = _with(bandit, species=hidden_state.species)
    writer = D20RulesSystemAdapter().to_writer_view(hidden_record)
    assert "elf" not in writer.model_dump_json().lower()
    emit({"case": "positive: hidden species writer view", "writer": writer.model_dump(mode="json"), "result": "passed"})
    run("hidden recorded Elf disclosed by repeated species refusal", wizard, [hidden_subject], [_species_proposal(hidden_subject, "character_origins.dwarf")])
    assert hashlib.sha256(ORACLE.read_bytes()).hexdigest() == oracle_before
    outdir = ROOT / ".claude/review-notes/issue-15c-implementation/c8-execution-review"
    (outdir / "visibility-results.json").write_text(json.dumps({"revision": REV, "authority_sha256": oracle_before, "results": results, "frozen_modules": hashes}, indent=2), encoding="utf-8")
    sys.exit(0)
if "extra" in sys.argv:
    from afterworlds.models.dnd5e_state import SummonOrigin, GrantSource, CreaturePresence
    from afterworlds.models.dnd5e_vocabulary import CreatureType
    from afterworlds.services.dnd5e_state.validation import validate_creature, creature_readiness
    familiar = _with(_creature("animals.cat", hp=40), summon=SummonOrigin(source=GrantSource(record_key="spells.find_familiar")), creature_type=CreatureType.FEY, presence=CreaturePresence.PRESENT, hazards=())
    assert validate_creature(familiar.index, familiar.stored.state) == ()
    assert creature_readiness(familiar.stored.state) == ()
    run("fully ready present Find Familiar cat can attack", wizard, [familiar, bandit], [_bite(familiar, bandit, entry="Scratch")], familiar)
    ghoul = _creature(GHOUL, hp=40)
    missing = _with(familiar, presence=None)
    gone = _with(familiar, presence=CreaturePresence.POCKET_DIMENSION)
    low = _with(familiar, hit_points=familiar.stored.state.hit_points.model_copy(update={"current": 1}))
    run("Ghoul attacks Familiar with unrecorded presence", wizard, [ghoul, missing], [_claw(ghoul, missing)], ghoul)
    run("Ghoul attacks Familiar dismissed to pocket dimension", wizard, [ghoul, gone], [_claw(ghoul, gone)], ghoul)
    run("Ghoul drops present Familiar to zero using ordinary monster death", wizard, [ghoul, low], [_claw(ghoul, low)], ghoul)
    assert hashlib.sha256(ORACLE.read_bytes()).hexdigest() == oracle_before
    outdir = ROOT / ".claude/review-notes/issue-15c-implementation/c8-execution-review"
    (outdir / "source-qualified-results.json").write_text(json.dumps({"revision": REV, "authority_sha256": oracle_before, "results": results, "frozen_modules": hashes}, indent=2), encoding="utf-8")
    sys.exit(0)
one = _species_proposal(bandit, "character_origins.elf")
two = _species_proposal(bandit, "character_origins.dwarf")
run("positive: one recorded selection", wizard, [bandit], [one])
run("duplicate selection, different species", wizard, [bandit], [one, two])
run("valid bite then conflicting species selections", wizard, [wolf, bandit], [_bite(wolf, wizard), one, two], wolf)
run("valid bite then duplicate same species", wizard, [wolf, bandit], [_bite(wolf, wizard), one, one], wolf)

from afterworlds.models.dnd5e_state import SummonOrigin, GrantSource
from afterworlds.models.dnd5e_vocabulary import CreatureType
familiar = _with(_creature("animals.cat", hp=40), summon=SummonOrigin(source=GrantSource(record_key="spells.find_familiar")), creature_type=CreatureType.FEY)
run("Find Familiar cat attacks using ordinary cat Scratch", wizard, [familiar, bandit], [_bite(familiar, bandit, entry="Scratch")], familiar)
ghoul = _creature(GHOUL, hp=40)
run("positive: Ghoul Claw against source-qualified familiar", wizard, [ghoul, familiar], [_claw(ghoul, familiar)], ghoul)

from afterworlds.pipeline.rpg import creature_types
from afterworlds.ingestion.mechanical.representation import SummonedCreatureTypeFact
from afterworlds.pipeline.rpg.defense import facts_of
fact = next(f for f in facts_of(bandit.index, "spells.find_familiar", "effect") if isinstance(f, SummonedCreatureTypeFact))
for ref in fact.forms:
    for kind in fact.type_choice:
        subject = _with(_creature(ref.record_key, hp=40), summon=SummonOrigin(source=GrantSource(record_key="spells.find_familiar")), creature_type=CreatureType(kind.value))
        typed = creature_types.target_type(subject)
        assert typed.type.value == kind.value and typed.elf is False
emit({"case": "eleven named Familiar forms each permit the three exact accepted choices", "forms": [r.record_key for r in fact.forms], "choices": [t.value for t in fact.type_choice], "checks": len(fact.forms) * len(fact.type_choice), "result": "passed"})

# Inspect source-open identities; the source prose eligibility claim is checked
# against the actual finite Humanoid templates, not only the category name.
from afterworlds.services.dnd5e_state.validation import species_open
index = bandit.index
emit({"eligible_humanoid_templates": [k for k in sorted(index.records) if species_open(index, k)]})
assert hashlib.sha256(ORACLE.read_bytes()).hexdigest() == oracle_before
outdir = ROOT / ".claude/review-notes/issue-15c-implementation/c8-execution-review"
(outdir / "results.json").write_text(json.dumps({"revision": REV, "authority_sha256": oracle_before, "results": results, "frozen_modules": hashes}, indent=2), encoding="utf-8")
print(json.dumps({"revision": REV, "authority_sha256": oracle_before, "frozen_module_count": len(hashes), "result_file": str(outdir / "results.json")}), flush=True)
