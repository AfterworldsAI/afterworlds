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
from unittest.mock import patch
from tests.pipeline.rpg import test_bounded_checks as t
from afterworlds.ingestion.mechanical.representation import ToolVariantsFact, ToolActivityFact, ToolVariant
from afterworlds.models.enums import DiceHandling, RollVisibility
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
from afterworlds.services.dnd5e_state import holdings, adoption
from tests.pipeline.rpg.test_adjudication_service import _FakeProvider, _make_assembled, _make_session, _STORY_ID, _TURN_ID
index=t.real_index()
# Each typed activity/kind is a finite sibling of the same new execution path.
for target, state in [(t.GAMING,t._soldier_with('dice')),(t.MUSIC,t._bard_with('lute'))]:
    c=index.component(*target)
    combinations=0
    for option in c.options:
        activities=[f.fact.activity for f in option.facts if isinstance(f.fact,ToolActivityFact)]
        kinds=[v for f in option.facts if isinstance(f.fact,ToolVariantsFact) for v in f.fact.variants]
        for activity in activities:
            for kind in kinds:
                record,dice=t._resolve(t.srd_character(state,items=t._kinds(target,kind)),10,proposal=t._tool(target,activity.value,kind.value))
                assert dice.roll.call_count==1 and record.outcome in ('success','failure')
                assert json.loads(record.modifiers_json)['check_identity'].endswith(':'+kind.value)
                combinations+=1
    emit({'case':'activity-kind-siblings','target':target,'combinations':combinations,'result':'passed'})
# Caller's parsed tool output reaches the real adjudication service with hidden filtering.
for visibility in [RollVisibility.SHOWN,RollVisibility.HIDDEN]:
    actor=t.srd_character(t._soldier_with('dice'),items=t._kinds(t.GAMING,ToolVariant.DICE))
    proposal=t._tool(t.GAMING,'win_the_game','dice').model_copy(update={'visibility':visibility})
    dice=t._dice(10)
    result=RpgAdjudicationPassService(adapter=D20RulesSystemAdapter()).adjudicate(_make_assembled(),_make_session(DiceHandling.AI_ROLLS),actor,dice,provider=_FakeProvider([proposal.model_dump(mode='json')]),story_id=_STORY_ID,originating_turn_id=_TURN_ID)
    assert len(result.proposals)==1 and dice.roll.call_count==1
    record=result.proposals[0]
    assert json.loads(record.modifiers_json)['check_identity'].endswith(':dice')
    writer=D20RulesSystemAdapter().to_writer_view(record)
    if visibility is RollVisibility.HIDDEN:
        assert writer.total is None and writer.dc is None and writer.outcome is None and 'dice' not in writer.model_dump_json()
    emit({'case':'real-caller-service-'+visibility.value,'result':'passed','dice_calls':dice.roll.call_count,'total':record.total})
# Existing rejection cases run using their committed pytest parameter values.
func=t.test_an_unrecorded_or_wrong_tool_kind_is_refused
mark=next(m for m in func.pytestmark if m.name=='parametrize')
for params in mark.args[1]: func(*params)
t.test_a_tool_without_kinds_refuses_a_selected_kind()
emit({'case':'committed-before-dice-negative-controls','result':'passed','cases':len(mark.args[1])+1})
# A target effective authority losing this kind rejects the held item during adoption.
record=index.record(t.GAMING[0])
def narrow(f):
    return dataclasses.replace(f,fact=dataclasses.replace(f.fact,variants=tuple(v for v in f.fact.variants if v is not ToolVariant.DICE))) if isinstance(f.fact,ToolVariantsFact) else f
components=tuple(dataclasses.replace(c,facts=tuple(narrow(f) for f in c.facts),options=tuple(dataclasses.replace(o,facts=tuple(narrow(f) for f in o.facts)) for o in c.options)) for c in record.components)
records=dict(index.records); records[t.GAMING[0]]=dataclasses.replace(record,components=components)
target=dataclasses.replace(index,records=records)
item=t._kinds(t.GAMING,ToolVariant.DICE)[0]
assert holdings.item_identity_failure(index,*t.GAMING,tool_variant=item.tool_variant) is None
assert holdings.item_identity_failure(target,*t.GAMING,tool_variant=item.tool_variant) is not None
with patch.object(adoption,'items_held_by',return_value=(item,)):
    assert adoption._held_item_failures(None,index,'character',item.holder.holder_id)==()
    failures=adoption._held_item_failures(None,target,'character',item.holder.holder_id)
    assert len(failures)==1 and 'items[' in failures[0].path
emit({'case':'held-kind-adoption-target-validation','result':'passed','method':'pure exact helper; fake holdings read; no store'})
assert hashlib.sha256(ORACLE.read_bytes()).hexdigest()==oracle_before
outdir=ROOT/'.claude/review-notes/issue-15c-implementation/tool-variant-review'
(outdir/'seam-results.json').write_text(json.dumps({'revision':REV,'authority_sha256':oracle_before,'results':results,'frozen_modules':hashes},indent=2),encoding='utf-8')
