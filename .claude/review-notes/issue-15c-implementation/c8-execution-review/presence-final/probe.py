"""Bounded presence follow-up: frozen project/test blobs, no source writes."""
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
prior = (BASE / "correction/probe.py").read_text(encoding="utf-8")
header = prior.split("from afterworlds.models.dnd5e_state import SummonOrigin", 1)[0]
header = header.replace("c6c2b2ad295d7d474eaa900a77988af20832e7d5", "6caa63e36a143feab0d3ddec50175803d24ee8c4")
header = header.replace('"effects": [e.model_dump(mode="json") for r in result.proposals for e in r.sheet_effects]', '"records": [r.model_dump(mode="json") for r in result.proposals]')
header = header.replace('"detail": str(exc)', '"detail": str(exc), "kind": getattr(getattr(exc, "kind", None), "value", None)')
exec(compile(header, str(BASE / "correction/probe.py"), "exec"))

from afterworlds.models.dnd5e_state import SummonOrigin, GrantSource, CreaturePresence
from afterworlds.models.dnd5e_vocabulary import CreatureType
from tests.pipeline.rpg.test_weapon_attacks import _attacker, _proposal, DAGGER
from tests.pipeline.rpg.test_creature_attacks import _ref
from afterworlds.services.dnd5e_state.validation import validate_creature

wizard, wolf = _medium_wizard(), _creature(hp=40)
thrower = _attacker(DAGGER)

def familiar(presence):
    subject = _with(_creature("animals.cat", hp=40),
        summon=SummonOrigin(source=GrantSource(record_key="spells.find_familiar")),
        creature_type=CreatureType.FEY, presence=presence, hazards=())
    assert validate_creature(subject.index, subject.stored.state) == ()
    return subject

def check(label, bystander, path, expected):
    ref = _ref(bystander)
    if path == "ally":
        proposal = _bite(wolf, wizard, allies_within_5_feet_of_target=(ref,))
        actor, active = wizard, wolf
    else:
        proposal = _proposal(wolf, DAGGER, range="within_normal_range", thrown=True,
            hostiles_within_5_feet=(ref,), ability="dexterity", target_within_5_feet=False)
        actor, active = thrower, thrower
    run(label + " " + path, actor, [wolf, bystander], [proposal], active,
        roller=_dice((12, 15), (1,)))
    result = results[-1]
    if expected in ("missing_state", "invalid_selection"):
        assert result["exception"] == "AdjudicationRefusal", result
        assert result["kind"] == expected, result
        assert result["dice_calls"] == [], result
        assert str(bystander.subject_id) in result["detail"], result
    else:
        assert result["result"] == "accepted", result
        assert result["dice_calls"][0] == expected, result
        assert result["operations"] == 1, result

for presence, kind in ((None, "missing_state"),
        (CreaturePresence.POCKET_DIMENSION, "invalid_selection"),
        (CreaturePresence.GONE, "invalid_selection")):
    for path in ("ally", "enemy"):
        check("Familiar " + str(presence), familiar(presence), path, kind)
for path, expression in (("ally", "2d20kh1"), ("enemy", "2d20kl1")):
    check("present Familiar", familiar(CreaturePresence.PRESENT), path, expression)
    check("ordinary animal", _creature("animals.cat", hp=40), path, expression)

oracle_after = hashlib.sha256(ORACLE.read_bytes()).hexdigest()
assert oracle_after == oracle_before
out = Path(__file__).resolve().parent
(out / "results.json").write_text(json.dumps({
    "revision": REV, "project_import": __import__("afterworlds").__file__,
    "oracle_sha256": oracle_before, "checks": results,
    "frozen_module_sha256": hashes,
}, indent=2), encoding="utf-8")
evidence = {}
for suffix in ("result.json", "out.txt", "err.txt"):
    relative = ".claude/review-notes/issue-15c-c8-recording/runs/rpg-suites-4." + suffix
    data = subprocess.check_output(["git", "show", REV + ":" + relative])
    filename = "rpg-suites-4." + suffix
    (out / filename).write_bytes(data)
    evidence[filename] = hashlib.sha256(data).hexdigest()
evidence["results.json"] = hashlib.sha256((out / "results.json").read_bytes()).hexdigest()
(out / "evidence-pins.json").write_text(json.dumps({"revision": REV, "sha256": evidence}, indent=2), encoding="utf-8")
print(json.dumps({"checks_passed": len(results), "frozen_modules": len(hashes), "revision": REV}), flush=True)
