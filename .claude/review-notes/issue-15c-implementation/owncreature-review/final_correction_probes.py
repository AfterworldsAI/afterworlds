"""Changed-seam review at f8be6ca; reuses previous helper definitions only."""
from pathlib import Path
base=Path(__file__).with_name('correction_probes.py').read_text(encoding='utf-8-sig')
base=base.split('# Six admitted shapes,')[0].replace('41f892cc9d1e2ce235fc4334b4b63a3fd2d71650','f8be6caa8b6d3dc7e86c2d7c23b50718869ee2ba')
exec(compile(base,str(Path(__file__)), 'exec'))
from afterworlds.services.dnd5e_state.validation import validate_character
from afterworlds.pipeline.rpg.scene import render
from afterworlds.pipeline.rpg.caller import PRODUCE_ADJUDICATION_PROPOSALS_TOOL_SPEC
for template in ('animals.elephant','animals.mammoth','monsters.gorgon.gorgon'):
    s=source(template)
    for starts_prone in (False,True):
        t=prone(wizard()) if starts_prone else wizard()
        for face in (1,19):
            row=run(template+f'/prone-{starts_prone}/d20-{face}',s,t,[_bite(s,t,entry='Gore',moved_straight_toward_target=True,target_within_5_feet=True),area(s,t,'Trample')],d20=face)
            if starts_prone: assert row['status']=='completed'
            else: assert row['status']=='AdjudicationRefusal' and row['dice']==[] and 'invalid_selection' in row['detail']
# Legal persisted IDs must retain their meaning through serialization and readiness validation.
s=source('animals.elephant')
for instance in ('review-real-prone','possible:prone','possible:legitimate-imported-condition'):
    t=changed(wizard(),conditions=(ConditionInstance(instance_id=instance,condition=ConditionKind.PRONE,visibility=ConditionVisibility.VISIBLE),))
    t=changed(t,conditions=type(t.stored.state).model_validate_json(t.stored.state.model_dump_json()).conditions)
    failures=validate_character(t.index,t.stored.state)
    assert not failures,failures
    row=run('persisted-id/'+instance,s,t,[area(s,t,'Trample')])
    row['state_validation_failures']=[str(x) for x in failures]
    if instance=='review-real-prone': assert row['status']=='completed'
    else: assert row['status']=='AdjudicationRefusal' and row['dice']==[]

def roar(s,t,entry,enemies,targets=None):
    p=area(s,t,entry);sel=p.creature_save_effect
    return p.model_copy(update={'creature_save_effect':sel.model_copy(update={'enemies_in_area':None if enemies is None else tuple(_ref(e) for e in enemies),'targets':tuple(_ref(e) for e in targets) if targets is not None else sel.targets})})
for template,entry,condition in [('monsters.sphinxes.sphinx_of_lore','Mind-Rending Roar','incapacitated'),('monsters.sphinxes.sphinx_of_valor','Third Roar','prone')]:
    s=source(template);t=wizard();extra=source('animals.wolf')
    for face in (1,20):
        row=run(template+f'/qualified/d20-{face}',s,t,[roar(s,t,entry,(t,))],d20=face)
        assert row['status']=='completed'
        effects=row['records'][0]['effects']; assert any(e['target']==condition and e['operation']=='apply_condition' for e in effects) is (face==1)
        assert row['records'][0]['provenance']['source']['subject_id']==str(s.subject_id)
        assert row['records'][0]['provenance']['targets'][0]['subject']['subject_id']==str(t.subject_id)
    negatives=[('missing',None,None),('nonenemy',(),None),('untargeted',(t,extra),None),('self',(s,),(s,)),('duplicate',(t,t),None),('extra-target',(t,),(t,extra))]
    for label,enemies,targets in negatives:
        row=run(template+'/'+label,s,t,[roar(s,t,entry,enemies,targets)],extra=(extra,))
        assert row['status']=='AdjudicationRefusal' and row['dice']==[]
    view=json.loads(render(t,[s],actor_turn(s)(_STORY_ID).document).split('\n',1)[1])
    own=next(x for x in view['subjects'] if x['subject_id']==str(s.subject_id))
    assert entry in own['enemy_only_effects']
    out.setdefault('enemy_options',{})[template]=own['enemy_only_effects']
    assert ('character',str(t.subject_id)) in D20RulesSystemAdapter().spatial_subjects(roar(s,t,entry,(t,)),t)
s=source('animals.lion');t=wizard()
row=run('nonenemy-effect-rejects-cohort',s,t,[roar(s,t,'Roar',(t,))])
assert row['status']=='AdjudicationRefusal' and row['dice']==[]
assert 'enemies_in_area' in json.dumps(PRODUCE_ADJUDICATION_PROPOSALS_TOOL_SPEC)
assert 'enemy_only_effects' in (ROOT/'docs/prompts/rpg_adjudication.md').read_text()
paths=['src/afterworlds/pipeline/rpg/conditions.py','src/afterworlds/pipeline/rpg/creature_effects.py','src/afterworlds/pipeline/rpg/adapter.py','src/afterworlds/pipeline/rpg/scene.py','src/afterworlds/pipeline/rpg/caller.py','src/afterworlds/models/rpg.py','docs/prompts/rpg_adjudication.md','src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json']
out['hashes']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
assert not subprocess.check_output(['git','diff',PIN,'--','src','tests','docs/prompts'],cwd=ROOT)
Path(__file__).with_name('final-correction-probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print('Assertions passed:',len(out['cases']),'service cases; prefix-collision defect reproduced with validated serialized persisted conditions.')
