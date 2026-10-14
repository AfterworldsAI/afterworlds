"""Verify saved deterministic probe evidence without re-importing the application."""
import json
from pathlib import Path
folder=Path(__file__).parent
d=json.loads((folder/'correction-probes.json').read_text())
r={v['label']:v for v in d['cases']}
for template,damage in [('animals.elephant',14),('animals.mammoth',15),('monsters.gorgon.gorgon',13)]:
    for face,expected in [(1,damage),(20,damage//2)]:
        row=r[f'{template}/Trample/save{face}']; assert row['status']=='completed'
        record=row['records'][0]; assert record['provenance']['targets'][0]['damage']['taken']==expected
        assert any(e['target']=='current_hp' and json.loads(e['value_json'])==200-expected for e in record['effects'])
    for suffix in ['standing','missing-conditions','wrong-self']:
        row=r[template+'/'+suffix]; assert row['status']=='AdjudicationRefusal' and row['dice']==[]
    assert r[template+'/gore-trample/d20-1']['status']=='PreflightGapError'
    assert r[template+'/gore-trample/d20-1']['dice']==['1d20']
    assert r[template+'/gore-trample/d20-19']['status']=='completed'
for template,entry,condition in [('monsters.dragon_turtle.dragon_turtle','Steam Breath',None),('monsters.sphinxes.sphinx_of_lore','Mind-Rending Roar','incapacitated'),('monsters.sphinxes.sphinx_of_valor','Third Roar','prone')]:
    for face in (1,20):
        row=r[f'{template}/{entry}/save{face}']; assert row['status']=='completed'
        record=row['records'][0]; target=record['provenance']['targets'][0]
        assert target['save']['outcome'] == ('success' if face==20 else 'failure')
        expected=8 if face==1 else (0 if condition=='incapacitated' else 4)
        assert target.get('damage',{}).get('taken',0)==expected
        applied=[e for e in record['effects'] if e['operation']=='apply_condition']
        assert bool(applied) is (face==1 and condition is not None)
        if applied:
            assert applied[0]['target']==condition
            if condition=='incapacitated':
                v=json.loads(applied[0]['value_json']); assert v['ends']['turn']['boundary']=='start' and v['ends']['turn']['created_in_turn']==1
    assert r[template+'/wrong-self']['dice']==[]
for label,row in r.items():
    if '/immune/' in label or label in ['swarm/source-missing-HP','blood-hawk/target-missing-HP','lion/save-immunity']:
        assert row['status']=='AdjudicationRefusal' and row['dice']==[]
assert r['blood-hawk/target-HP-101']['dice']==['1d20','1d4']
assert r['blood-hawk/target-HP-100']['dice']==['1d20','1d8']
assert r['blood-hawk/advanced-target-HP']['dice']==['1d20','1d4','1d20','1d8']
assert r['steam/natural-fire-resistance']['records'][0]['provenance']['targets'][0]['damage']['taken']==4
assert r['wolf/too-large-immunity-not-read']['status']=='completed'
assert r['allosaurus/false-charge-immunity-not-read']['status']=='completed'
s=json.loads((folder/'supplemental-probes.json').read_text())
assert 'invalid_selection' in s['related_source_probe']
for row in s['cases']:
    if '/already-prone/' in row['label'] and 'mammoth' not in row['label']:
        assert row['status']=='completed'
    if row['label'].startswith(('giant-ape/','gladiator/')):
        assert row['status']=='AdjudicationRefusal' and row['dice']==[]
print('Saved evidence verified: 45 primary service probes; 8 supplemental service probes and one direct related-source preparation probe. Three speculative Trample sequences reproduce PreflightGapError. The supplemental Mammoth initially-Prone sequence lacks its reach fact and is not counted as positive proof; standalone Mammoth Trample succeeds in the primary results.')

