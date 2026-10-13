"""Bounded reviewer probes at immutable 41f892c. No store/source mutations."""
from pathlib import Path
import sys, dataclasses, json, hashlib, subprocess
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import afterworlds
from afterworlds.models.enums import DiceHandling, RollVisibility, ConditionVisibility
from afterworlds.models.rpg import RollProposal, CreatureSaveEffectSelection
from afterworlds.models.dnd5e_state import HitPoints, ConditionInstance
from afterworlds.ingestion.mechanical.representation import ConditionKind, CreatureSaveEffectFact, CreatureAttackFact
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
from afterworlds.pipeline.rpg.defense import facts_of
from tests.pipeline.rpg.test_creature_attacks import _bite, _medium_wizard, _ref
from tests.pipeline.rpg.test_weapon_attacks import _creature, _dice
from tests.pipeline.rpg.test_adjudication_service import _STORY_ID, _TURN_ID, _FakeProvider, _make_assembled, _make_session
from tests.pipeline.rpg.test_turn_sequencing import actor_turn
PIN = '41f892cc9d1e2ce235fc4334b4b63a3fd2d71650'
assert not subprocess.check_output(['git','diff',PIN,'--','src','tests','pyproject.toml'],cwd=ROOT)
assert Path(afterworlds.__file__).resolve() == ROOT / 'src/afterworlds/__init__.py'
def changed(s, **v):
    state=type(s.stored.state).model_validate({**s.stored.state.model_dump(mode='python'), **v})
    return dataclasses.replace(s, stored=dataclasses.replace(s.stored,state=state))
def wizard(): return changed(_medium_wizard(),hit_points=HitPoints(current=200,maximum=200,temporary=0))
def source(template): return changed(_creature(template,hp=300),usage_counters=())
def prone(t): return changed(t,conditions=(ConditionInstance(instance_id='review-prone',condition=ConditionKind.PRONE,visibility=ConditionVisibility.VISIBLE),))
def area(s,t,entry):
    return RollProposal(check_label=entry,subsystem_tag='save',visibility=RollVisibility.SHOWN,operation='creature_save_effect',creature_save_effect=CreatureSaveEffectSelection(source=_ref(s),entry=entry,targets=(_ref(t),),auras_in_range=()))
out={'head':PIN,'import':afterworlds.__file__,'cases':[]}
def run(label,s,t,ps,d20=1,damage=8,extra=()):
    dice=_dice((d20,),(damage,))
    subjects={(_ref(x).kind,str(x.subject_id)):x for x in (s,t,*extra)}
    service=RpgAdjudicationPassService(adapter=D20RulesSystemAdapter(),subject_loader=lambda _story,r:subjects[(r.kind,str(r.subject_id))],coordination_loader=actor_turn(s),bounded_loader=lambda _story,_ref:[],aura_loader=lambda _story:[])
    row={'label':label}
    try:
        result=service.adjudicate(_make_assembled(),_make_session(DiceHandling.AI_ROLLS),t,dice,provider=_FakeProvider([p.model_dump(mode='json',exclude_none=True) for p in ps]),story_id=_STORY_ID,originating_turn_id=_TURN_ID)
        row['status']='completed'
        row['records']=[{'outcome':r.outcome,'provenance':json.loads(r.modifiers_json),'effects':[e.model_dump(mode='json') for e in r.sheet_effects]} for r in result.proposals]
    except Exception as exc:
        row['status']=type(exc).__name__;row['detail']=str(exc)
    row['dice']=dice.calls
    out['cases'].append(row)
    print(json.dumps({k:v for k,v in row.items() if k!='records'}),flush=True)
    return row

# Six admitted shapes, effects on failed and successful saves, applicable negatives.
shapes=[('animals.elephant','Trample'),('animals.mammoth','Trample'),('monsters.gorgon.gorgon','Trample'),('monsters.dragon_turtle.dragon_turtle','Steam Breath'),('monsters.sphinxes.sphinx_of_lore','Mind-Rending Roar'),('monsters.sphinxes.sphinx_of_valor','Third Roar')]
for template,entry in shapes:
    s=source(template);t=prone(wizard()) if entry=='Trample' else wizard()
    for face in (1,20): run(template+'/'+entry+f'/save{face}',s,t,[area(s,t,entry)],d20=face)
    if entry=='Trample':
        for kind,target in [('standing',wizard()),('missing-conditions',changed(wizard(),conditions=None))]:
            run(template+'/'+kind,s,target,[area(s,target,entry)])
    # Source itself is never a permitted enemy/ordinary target for these shapes.
    run(template+'/wrong-self',s,t,[area(s,s,entry)])

# Complete-preflight regressions and applicability.
for template,entry,immunity,facts in [('animals.wolf','Bite',ConditionKind.PRONE,{}),('monsters.purple_worm.purple_worm','Bite',ConditionKind.RESTRAINED,{'target_within_5_feet':False}),('animals.allosaurus','Claws',ConditionKind.PRONE,{'moved_straight_toward_target':True})]:
    for face in (1,19):
        s=source(template);t=changed(wizard(),condition_immunities=(immunity,))
        run(template+f'/immune/d20-{face}',s,t,[_bite(s,t,entry=entry,**facts)],d20=face)
s=changed(source('animals.swarm_of_rats'),hit_points=None);t=wizard()
run('swarm/source-missing-HP',s,t,[_bite(s,t,entry='Bites',target_within_5_feet=True)])
s=source('animals.lion');t=changed(wizard(),condition_immunities=(ConditionKind.FRIGHTENED,))
run('lion/save-immunity',s,t,[area(s,t,'Roar')])
s=source('animals.allosaurus');t=changed(wizard(),condition_immunities=(ConditionKind.PRONE,))
run('allosaurus/false-charge-immunity-not-read',s,t,[_bite(s,t,entry='Claws',moved_straight_toward_target=False)],d20=19)
# A miss must not establish the Prone prerequisite for a later Bonus Action.
for template in ('animals.elephant','animals.mammoth','monsters.gorgon.gorgon'):
    s=source(template);t=wizard()
    for face in (1,19):
        run(template+f'/gore-trample/d20-{face}',s,t,[_bite(s,t,entry='Gore',moved_straight_toward_target=True),area(s,t,'Trample')],d20=face)

# Accepted inventory of save rider size bounds and source/target Bloodied readers.
idx=wizard().index
out['source_inventory']=[]
for rec in idx.records.values():
    for component in rec.components:
        for ef in component.facts:
            f=ef.fact
            if isinstance(f,CreatureSaveEffectFact) and f.failure_effect is not None and f.failure_effect.maximum_size is not None:
                out['source_inventory'].append({'record':rec.semantic_key,'entry':f.entry, 'fact':repr(f)})
            if isinstance(f,CreatureAttackFact) and f.hit_effect is not None and (f.hit_effect.rider_save is not None or (f.hit_effect.conditional_damage is not None and f.hit_effect.conditional_damage.when.target_bloodied)):
                out['source_inventory'].append({'record':rec.semantic_key,'entry':f.entry, 'fact':repr(f)})
s=source('animals.blood_hawk');t=changed(wizard(),hit_points=None)
run('blood-hawk/target-missing-HP',s,t,[_bite(s,t,entry='Beak')])
# Independent attacker state does not choose a target-Bloodied branch.
for current in (101,100):
    t=changed(wizard(),hit_points=HitPoints(current=current,maximum=200,temporary=80))
    run(f'blood-hawk/target-HP-{current}',s,t,[_bite(s,t,entry='Beak')],d20=19)
# Sequential damage crosses target Bloodied; the next operation reads advanced HP.
s=source('animals.blood_hawk');t=changed(wizard(),hit_points=HitPoints(current=103,maximum=200,temporary=0))
def edge(s,kind): return RollProposal(check_label=kind,subsystem_tag='turn',visibility=RollVisibility.SHOWN,operation=kind,subject=_ref(s))
run('blood-hawk/advanced-target-HP',s,t,[_bite(s,t,entry='Beak'),edge(s,'end_turn'),edge(s,'begin_turn'),_bite(s,t,entry='Beak')],d20=19)
# Natural Fire defense still applies; the underwater exception cannot remove it.
s=source('monsters.dragon_turtle.dragon_turtle');t=wizard(); other=source('monsters.dragon_turtle.dragon_turtle')
run('steam/natural-fire-resistance',s,t,[area(s,other,'Steam Breath')],extra=(other,))
# Size-gated direct condition does not consult an impossible immunity.
s=source('animals.wolf');t=changed(wizard(),size='gargantuan',condition_immunities=(ConditionKind.PRONE,))
run('wolf/too-large-immunity-not-read',s,t,[_bite(s,t)],d20=19)
out['hashes']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'.claude/review-notes/issue-15c-preparation/issue-draft.md',ROOT/'src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json',ROOT/'src/afterworlds/pipeline/rpg/creature_attacks.py',ROOT/'src/afterworlds/pipeline/rpg/creature_effects.py',ROOT/'src/afterworlds/pipeline/rpg/service.py']}
assert not subprocess.check_output(['git','diff',PIN,'--','src','tests','pyproject.toml'],cwd=ROOT)
Path(__file__).with_name('correction-probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')


