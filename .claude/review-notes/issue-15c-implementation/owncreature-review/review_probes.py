"""Read-only bounded reviewer probes, b5051d8. No test/store mutation."""
import dataclasses
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import afterworlds
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
from afterworlds.ingestion.mechanical.representation import ConditionKind
from afterworlds.models.enums import DiceHandling
from tests.pipeline.rpg.test_creature_attacks import _bite, _medium_wizard, _subjects
from tests.pipeline.rpg.test_weapon_attacks import _creature, _dice
from tests.pipeline.rpg.test_adjudication_service import _STORY_ID, _TURN_ID, _FakeProvider, _make_assembled, _make_session
from tests.pipeline.rpg.test_turn_sequencing import actor_turn

a=D20RulesSystemAdapter()
out={'import':afterworlds.__file__, 'cases': []}
def changed(subject, **values):
 state=type(subject.stored.state).model_validate({**subject.stored.state.model_dump(mode='python'), **values})
 return dataclasses.replace(subject,stored=dataclasses.replace(subject.stored,state=state))
def probe(label, source, target, entry, **facts):
 p=_bite(source,target,entry=entry,**facts)
 dice=_dice((19,),(1,))
 row={'label':label}
 try: a.require_supported(p,target,_subjects(source)); row['preflight']='accepted'
 except Exception as e: row['preflight']=f'{type(e).__name__}: {e}'
 service=RpgAdjudicationPassService(adapter=a, subject_loader=lambda _story,_ref:source, coordination_loader=actor_turn(source))
 try:
  r=service.adjudicate(_make_assembled(),_make_session(DiceHandling.AI_ROLLS),target,dice,provider=_FakeProvider([p.model_dump(mode='json',exclude_none=True)]),story_id=_STORY_ID,originating_turn_id=_TURN_ID)
  row['service']='completed'
 except Exception as e: row['service']=f'{type(e).__name__}: {e}'
 row['dice']=dice.calls
 out['cases'].append(row)
 print(json.dumps(row),flush=True)

probe('wolf prone immunity',_creature(),changed(_medium_wizard(),condition_immunities=(ConditionKind.PRONE,)),'Bite')
probe('worm linked restrained immunity',_creature('monsters.purple_worm.purple_worm',hp=250),changed(_medium_wizard(),condition_immunities=(ConditionKind.RESTRAINED,)),'Bite',target_within_5_feet=False)
probe('swarm missing HP',changed(_creature('animals.swarm_of_rats'),hit_points=None),_medium_wizard(),'Bites',target_within_5_feet=True)
probe('allosaurus clause prone immunity',_creature('animals.allosaurus'),changed(_medium_wizard(),condition_immunities=(ConditionKind.PRONE,)),'Claws',moved_straight_toward_target=True)
probe('ghast claw',_creature('monsters.ghast.ghast'),_medium_wizard(),'Claw')
from tests.pipeline.rpg.test_creature_roster import _results
r=_results()
out['admitted_refusals']={k:why for k,(positive,admitted,why) in r.items() if admitted and why}
out['c5_positive_refusals']={k:why for k,(positive,admitted,why) in r.items() if positive and why}
print(json.dumps(out,indent=2),flush=True)
Path(__file__).with_name('review-probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
