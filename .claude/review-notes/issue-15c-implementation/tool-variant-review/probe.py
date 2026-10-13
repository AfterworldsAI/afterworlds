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
REV = "b92493eae56ca839e027f3c7919febf0d3646a4d"
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


import dataclasses
from tests.pipeline.rpg import test_bounded_checks as t
from afterworlds.ingestion.mechanical.representation import ToolVariant, Skill
from afterworlds.models.dnd5e_state import ClassLevel, GrantSource, RecordChoice, OptionChoice, ToolGrant, SkillGrant, Dnd5eCharacterState
from afterworlds.pipeline.rpg import grants, checks, scene
from afterworlds.services.dnd5e_state.validation import validate_character
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal
index = t.real_index()
for key, comp in [('classes.monk','core_traits'),('classes.bard','core_traits'),('character_origins.soldier','tool_proficiency'),('feats.skilled','skilled')]:
    c=index.component(key,comp)
    emit({'case':'source','record':key,'component':comp,'facts':[dataclasses.asdict(f.fact) for f in c.facts], 'options':[dataclasses.asdict(o) for o in c.options]})

def run(name,state,target=t.GAMING,selected='dice',held=None,activity='win_the_game'):
    character=t.srd_character(state,items=t._kinds(target, *(held or [ToolVariant(selected)])))
    dice=t._dice(10)
    try:
        proposal=t._tool(target,activity,selected)
        prepared=checks.prepare(proposal,character)
        result=checks.roll(prepared,dice)
        out={'result':'accepted','proficiency':prepared.proficiency,'total':result.total,'identity':prepared.identity}
    except Exception as exc:
        out={'result':'refused','exception':type(exc).__name__,'detail':str(exc),'kind':getattr(exc,'kind',None)}
    emit({'case':name,**out,'dice_calls':dice.roll.call_count})

run('soldier-dice-positive',t._soldier_with('dice'))
run('soldier-other-kind-unproficient',t._soldier_with('playing_cards'))
run('soldier-legacy-null',t._soldier_with(None))
run('soldier-wrong-grant-kind',t._soldier_with('lute'))
s=t._soldier_with('dice'); g=s.tool_proficiencies[0]
run('soldier-two-kinds-over-one',s.model_copy(update={'tool_proficiencies':(g,g.model_copy(update={'variant':'playing_cards'}))}))
run('soldier-duplicate-same-kind-over-one',s.model_copy(update={'tool_proficiencies':(g,g)}))
run('bard-three-instruments',t._bard_with('lute','flute','drum'),t.MUSIC,'lute',activity='improvise_a_song')
run('bard-four-instruments',t._bard_with('lute','flute','drum','viol'),t.MUSIC,'lute',activity='improvise_a_song')
run('bard-duplicate-same-kind',t._bard_with('lute','lute','lute'),t.MUSIC,'lute',activity='improvise_a_song')
monk_source=GrantSource(record_key='classes.monk',component_key='core_traits')
monk=t._state(classes=(ClassLevel(class_record_key='classes.monk',level=1,hit_die='d8'),),level_history=('classes.monk',),tool_proficiencies=(t._kind_grant(t.MUSIC,monk_source,'lute'),))
run('monk-one-instrument',monk,t.MUSIC,'lute',activity='improvise_a_song')
run('monk-two-instruments',monk.model_copy(update={'tool_proficiencies':(t._kind_grant(t.MUSIC,monk_source,'lute'),t._kind_grant(t.MUSIC,monk_source,'drum'))}),t.MUSIC,'lute',activity='improvise_a_song')
for n in [2,3]:
    skilled=t._wizard_with_feat('feats.skilled')
    skilled=skilled.model_copy(update={'skill_proficiencies':tuple(SkillGrant(skill=x,expertise=False,source=t.SKILLED) for x in [Skill.ATHLETICS,Skill.STEALTH,Skill.ARCANA][:n]),'tool_proficiencies':(t._kind_grant(t.GAMING,t.SKILLED,'dice'),)})
    run(f'skilled-{n}-skills-plus-tool',skilled)
# Roundtrip the new field through the character JSON contract.
s=t._soldier_with('dice'); restored=Dnd5eCharacterState.model_validate_json(s.model_dump_json())
assert restored.tool_proficiencies[0].variant == ToolVariant.DICE
emit({'case':'character-json-roundtrip','result':'passed'})
# Exact existing negative/positive tests, called with their parametrized inputs.
for target, state, activity, dc, ability, granted, other in [(t.GAMING,t._soldier_with('playing_cards'),'win_the_game',20,'wisdom',ToolVariant.PLAYING_CARDS,ToolVariant.DICE),(t.MUSIC,t._bard_with('lute','flute','drum'),'improvise_a_song',15,'charisma',ToolVariant.LUTE,ToolVariant.VIOL)]:
    t.test_a_gaming_set_or_instrument_check_is_proficient_per_kind(target,state,activity,dc,ability,granted,other)
emit({'case':'existing-two-per-kind-tests','result':'passed'})
from tests.pipeline.rpg.test_scene import test_the_scene_lists_held_tools_with_their_kind
test_the_scene_lists_held_tools_with_their_kind()
emit({'case':'existing-scene-held-kind-test','result':'passed'})
assert hashlib.sha256(ORACLE.read_bytes()).hexdigest() == oracle_before
outdir=ROOT/'.claude/review-notes/issue-15c-implementation/tool-variant-review'
(outdir/'results.json').write_text(json.dumps({'revision':REV,'authority_sha256':oracle_before,'results':results,'frozen_modules':hashes},indent=2),encoding='utf-8')

