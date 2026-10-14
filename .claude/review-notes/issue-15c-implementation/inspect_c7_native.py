"""Read-only independent inspection of existing C7 bytes; no mint, tests or stores."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / '.claude/worktrees/agent-afb6123d0b7851456'
PACKET = WORK / '.claude/review-notes/issue-15c-c7-native'
sys.path.insert(0, str(WORK / 'src'))

def load(path):
    return json.loads(path.read_bytes())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def key(row):
    return row['record_key'], row['semantic_key']

prior_path = ROOT / 'src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c.json'
preview_path = PACKET / 'preview/srd-5-2-1-corpus-8781d4e0-a3b-c7-PREVIEW.json'
raw_path = ROOT / '.claude/review-notes/issue-15c-implementation/candidate-c7/c7.json'
report = load(PACKET / 'reports/c7-preview.json')
a, b, raw = load(prior_path), load(preview_path), load(raw_path)
assert digest(prior_path) == '23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69'
assert digest(raw_path) == 'bf2a269c6f5446a63d5ce2353c27d5dc75224935cd16960ce79da7e766aefa77'
assert digest(preview_path) == report['preview_sha256'] == 'd661cc3be22aa6aca996a4e67cac4f8ebbd2dfa1908dd29a0c7ae2e38177ef6d'
assert len(raw['facts']) == 9
expected = {(x['record_key'], x['component_key']): x['fact'] for x in raw['facts']}
assert len(expected) == 9
for filename, sha in report['pins'].items():
    assert digest(ROOT / filename) == sha, filename
touch = set(report['touched_batches'])
assert touch == {'character-origins-feats', 'equipment'}
for field in a:
    if field not in {'acceptance','obligations','representation','representation_schema','review_units'}:
        assert a[field] == b[field], field
ar, br = a['representation'], b['representation']
for field in ar:
    if field not in {'components','provenance'}:
        assert ar[field] == br[field], field
ac,bc={key(x):x for x in ar['components']},{key(x):x for x in br['components']}
assert len(ac)==len(ar['components']) and len(bc)==len(br['components'])
assert ac.keys()==bc.keys()
assert [key(x) for x in ar['components'] if key(x) not in expected] == [key(x) for x in br['components'] if key(x) not in expected]
changed = []
for k,before in ac.items():
    after=bc[k]
    k = key(before)
    if k not in expected:
        assert before == after, k
    else:
        assert before['facts'] == [] and before['handling'] == 'prose_bound'
        wanted = copy.deepcopy(before)
        wanted['facts'] = [expected[k]]
        wanted['handling'] = 'mixed'
        assert after == wanted, k
        changed.append(k)
assert len(changed) == 9
canon = lambda row: json.dumps(row,sort_keys=True,separators=(',',':'))
old_prov = {canon(x) for x in ar['provenance']}
new_prov = {canon(x) for x in br['provenance']}
assert old_prov <= new_prov
assert len(new_prov - old_prov) == 9
assert len(ar['provenance']) == len(old_prov) and len(br['provenance']) == len(new_prov)
extra_prov = [x for x in br['provenance'] if canon(x) not in old_prov]
assert all(x['target_kind'] == 'fact' and x['role'] == 'contextual' for x in extra_prov)
assert {tuple(x['target_key'][:2]) for x in extra_prov} == set(expected)
for field in ('batches','records','review_unit_records','schema_anchors'):
    aa, bb = a['acceptance'][field], b['acceptance'][field]
    assert [x for x in aa if x['batch_id'] not in touch] == [x for x in bb if x['batch_id'] not in touch], field
    assert len(aa) == len(bb), field
assert len(a['acceptance']['batches']) == 24
assert [x['batch_id'] for x in a['acceptance']['batches']] == [x['batch_id'] for x in b['acceptance']['batches']]
for field in a['acceptance']:
    if field not in {'batches','records','review_unit_records','schema_anchors','lifts'}:
        assert a['acceptance'][field] == b['acceptance'][field], field
assert b['acceptance']['lifts'][:-1] == a['acceptance']['lifts']
assert b['acceptance']['lifts'][-1]['lift_id'] == '5d-lift-schema-19-to-20'
for batch in touch:
    old = next(x for x in a['acceptance']['batches'] if x['batch_id'] == batch)
    new = next(x for x in b['acceptance']['batches'] if x['batch_id'] == batch)
    assert old['resolved_scope'] == new['resolved_scope'] and old['diff'] == new['diff']
    assert 'SIMULAT' in new['rule'].upper(), new['rule']
for field in ('records','review_unit_records'):
    aa,bb = a['acceptance'][field],b['acceptance'][field]
    for batch in touch:
        old = [x for x in aa if x['batch_id'] == batch]
        new = [x for x in bb if x['batch_id'] == batch]
        for o,n in zip(old,new,strict=True):
            assert {k:v for k,v in o.items() if k not in {'proposal_identity','rule','reviewer','accepted_at'}} == {k:v for k,v in n.items() if k not in {'proposal_identity','rule','reviewer','accepted_at'}}, (field,batch)
            assert 'SIMULAT' in str(n.get('rule',n.get('reviewer',''))).upper(), (field,batch,n)
au,bu = {x['unit_id']:x for x in a['review_units']},{x['unit_id']:x for x in b['review_units']}
assert au.keys() == bu.keys()
rules_added = []
for uid,o in au.items():
    n=bu[uid]
    assert {k:v for k,v in o.items() if k!='expected_rules'} == {k:v for k,v in n.items() if k!='expected_rules'}
    oo = {canon(x) for x in o['expected_rules']};nn={canon(x) for x in n['expected_rules']}
    assert oo <= nn
    rules_added += [x for x in n['expected_rules'] if canon(x) not in oo]
assert len(rules_added)==9
assert {(x['record_key'],x['component_key']) for x in rules_added} == set(expected)
ao,bo = {x['record_key']:x for x in a['obligations']},{x['record_key']:x for x in b['obligations']}
assert ao.keys()==bo.keys()
assert {k for k in ao if ao[k]!=bo[k]} == {k[0] for k in expected}
from afterworlds.ingestion.mechanical.oracle import load_accepted_inputs, serialize_accepted_inputs, oracle_identity, candidate_from_accepted_inputs
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.representation import representation_schema_hash, REPRESENTATION_SCHEMA_VERSION
native=load_accepted_inputs(preview_path)
assert serialize_accepted_inputs(native)==preview_path.read_bytes()
assert oracle_identity(native.oracle)==report['oracle_identity']
assert [REPRESENTATION_SCHEMA_VERSION,representation_schema_hash()]==report['schema']
ident=identify_projection(candidate_from_accepted_inputs(native))
assert str(ident.projection_uuid)==report['native']['projection'] and ident.payload_hash==report['native']['payload_hash']
print(json.dumps({'result':'read-only independent comparison passed','schema':report['schema'],'preview_sha256':digest(preview_path),'oracle':report['oracle_identity'],'projection':str(ident.projection_uuid),'added_facts':len(changed),'added_claims':len(extra_prov),'added_expected_rules':len(rules_added),'untouched_ordered_batches':22,'prior_source_pins_verified':True},indent=2))
