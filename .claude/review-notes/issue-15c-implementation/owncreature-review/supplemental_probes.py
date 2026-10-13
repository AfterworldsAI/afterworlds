"""Supplemental bounded size and speculative-condition siblings, pinned 41f892c."""
from pathlib import Path
base=Path(__file__).with_name('correction_probes.py').read_text(encoding='utf-8-sig')
exec(compile(base.split('# Six admitted shapes,')[0],str(Path(__file__)), 'exec'))
from afterworlds.services.dnd5e_state.turn import with_possible
from afterworlds.pipeline.rpg import creature_effects
s=source('animals.giant_ape')
for size in ('medium','gargantuan'):
    for immunity in ((),(ConditionKind.PRONE,)):
        t=changed(wizard(),size=size,condition_immunities=immunity)
        run(f'giant-ape/Boulder-Toss/{size}/immunity-{bool(immunity)}',s,t,[area(s,t,'Boulder Toss')])
for template in ('animals.elephant','animals.mammoth','monsters.gorgon.gorgon'):
    s=source(template);t=prone(wizard())
    run(template+'/already-prone/gore-miss-then-trample',s,t,[_bite(s,t,entry='Gore',moved_straight_toward_target=True),area(s,t,'Trample')],d20=1)
# Related-to-source is a separate requirement: speculative Grappled lacks its referent.
s=source('monsters.glabrezu.glabrezu');t=wizard()
view,subjects=with_possible(t,{('creature',str(s.subject_id)):s},{('character',str(t.subject_id)):{ConditionKind.GRAPPLED}})
try:
    creature_effects.prepare(area(s,t,'Pummel'),view,subjects)
    out['related_source_probe']='unexpected acceptance'
except Exception as exc:
    out['related_source_probe']=f'{type(exc).__name__}: {exc}'
# All current admitted save condition size bounds sampled: Gladiator refuses sight earlier.
s=source('monsters.gladiator.gladiator');t=changed(wizard(),size='gargantuan',condition_immunities=(ConditionKind.PRONE,))
run('gladiator/Shield-Bash/earlier-sight-boundary',s,t,[area(s,t,'Shield Bash')])
assert not subprocess.check_output(['git','diff',PIN,'--','src','tests','pyproject.toml'],cwd=ROOT)
Path(__file__).with_name('supplemental-probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(out['related_source_probe'])
