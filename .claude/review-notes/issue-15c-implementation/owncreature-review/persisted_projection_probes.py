"""Persisted/projection provenance review at e5d9a68; no store changes."""
from pathlib import Path
base=Path(__file__).with_name('correction_probes.py').read_text(encoding='utf-8-sig').split('# Six admitted shapes,')[0]
base=base.replace('41f892cc9d1e2ce235fc4334b4b63a3fd2d71650','e5d9a684c33d232fd468c9eea705d2b184ecfba8')
exec(compile(base,str(Path(__file__)), 'exec'))
from afterworlds.services.dnd5e_state.validation import validate_character, validate_creature
from afterworlds.services.dnd5e_state.turn import with_possible, with_effects
from afterworlds.pipeline.rpg.conditions import established, effective
from afterworlds.models.rpg import SheetEffect

def held(s): return {e.condition for e in established(s)}
def with_condition(t,kind,instance):
    t=changed(t,conditions=(ConditionInstance(instance_id=instance,condition=kind,visibility=ConditionVisibility.VISIBLE),))
    t=changed(t,conditions=type(t.stored.state).model_validate_json(t.stored.state.model_dump_json()).conditions)
    errors=validate_creature(t.index,t.stored.state) if _ref(t).kind=='creature' else validate_character(t.index,t.stored.state)
    assert not errors,errors
    assert not t.speculative
    return t
s=source('animals.elephant')
for ident in ('review-real-prone','possible:prone','possible:legitimate-imported-condition'):
    t=with_condition(wizard(),ConditionKind.PRONE,ident)
    row=run('persisted-character/'+ident,s,t,[area(s,t,'Trample')])
    assert row['status']=='completed'
    assert row['records'][0]['effects'] and ConditionKind.PRONE in held(t)
    row['serialized_state_validation']='passed'
# A creature target's persistent prefix-named condition uses the same contract.
t=with_condition(source('animals.wolf'),ConditionKind.PRONE,'possible:prone')
a=wizard();row=run('persisted-creature/possible:prone',s,a,[area(s,t,'Trample')],extra=(t,))
assert row['status']=='completed'
# Existing implied Prone is preserved; projected Unconscious is excluded before implications.
t=with_condition(wizard(),ConditionKind.UNCONSCIOUS,'possible:unconscious')
assert {ConditionKind.UNCONSCIOUS,ConditionKind.PRONE,ConditionKind.INCAPACITATED} <= held(t)
row=run('persisted-implied-prone',s,t,[area(s,t,'Trample')]);assert row['status']=='completed'
for template in ('animals.elephant','animals.mammoth','monsters.gorgon.gorgon'):
    s=source(template);t=wizard()
    row=run(template+'/speculative-gore-prone',s,t,[_bite(s,t,entry='Gore',moved_straight_toward_target=True,target_within_5_feet=True),area(s,t,'Trample')])
    assert row['status']=='AdjudicationRefusal' and row['dice']==[] and 'prone condition' in row['detail']
# Service sibling: another creature's prior damage could imply Prone through Unconscious.
goblin=source('monsters.goblins.goblin_warrior');s=source('animals.elephant');t=wizard()
def edge(s,kind): return RollProposal(check_label=kind,subsystem_tag='turn',visibility=RollVisibility.SHOWN,operation=kind,subject=_ref(s))
row=run('speculative-implied-prone',goblin,t,[_bite(goblin,t,entry='Scimitar'),edge(goblin,'end_turn'),edge(s,'begin_turn'),area(s,t,'Trample')],extra=(s,))
assert row['status']=='AdjudicationRefusal' and row['dice']==[] and 'prone condition' in row['detail']
# Provenance lifecycle on each subject; no marker or projection leaks into originals.
t=with_condition(wizard(),ConditionKind.PRONE,'possible:prone')
c=with_condition(source('animals.wolf'),ConditionKind.PRONE,'possible:prone')
ct=('character',str(t.subject_id));cc=('creature',str(c.subject_id))
v,ss=with_possible(t,{cc:c},{ct:{ConditionKind.PRONE,ConditionKind.UNCONSCIOUS},cc:{ConditionKind.PRONE,ConditionKind.STUNNED}})
assert not t.speculative and not c.speculative
assert len(v.speculative)==1 and len(ss[cc].speculative)==1 and v.speculative.isdisjoint(ss[cc].speculative)
assert 'possible:prone' not in v.speculative|ss[cc].speculative
assert held(v)=={ConditionKind.PRONE} and held(ss[cc])=={ConditionKind.PRONE}
assert ConditionKind.UNCONSCIOUS in {x.condition for x in effective(v,v.index)}
assert ConditionKind.INCAPACITATED in {x.condition for x in effective(ss[cc],ss[cc].index)}
# Subsequent in-memory advancement and another projection retain origin markers.
u=with_effects(v,[SheetEffect(target='current_hp',operation='set',value_json='199')])
assert u.speculative==v.speculative and held(u)=={ConditionKind.PRONE}
u,us=with_possible(u,ss,{ct:{ConditionKind.STUNNED}})
assert len(u.speculative)==2 and held(u)=={ConditionKind.PRONE}
assert us[cc].speculative==ss[cc].speculative
assert 'speculative' not in t.stored.state.model_dump()
out['lifecycle_assertions']='passed: original subjects unmodified, own-subject marker sets, real Prone retained, direct/implied projections excluded, markers survive advancement and repeat projection; no persisted provenance field'
paths=['src/afterworlds/services/dnd5e_state/turn.py','src/afterworlds/pipeline/rpg/conditions.py','tests/pipeline/rpg/test_before_dice.py','src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json']
out['hashes']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
assert not subprocess.check_output(['git','diff',PIN,'--','src','tests'],cwd=ROOT)
Path(__file__).with_name('persisted-projection-probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print('Assertions passed:',len(out['cases']),'bounded real-service cases plus projection lifecycle checks.')
