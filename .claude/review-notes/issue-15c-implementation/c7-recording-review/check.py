"""Independent read-only recording and baseline inspection. Never constructs authority."""
import collections
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'src'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_bytes())
notes = ROOT / '.claude/review-notes'
preview_dir = ROOT / '.claude/worktrees/agent-afb6123d0b7851456/.claude/review-notes/issue-15c-c7-native/preview'
preview = preview_dir / 'srd-5-2-1-corpus-8781d4e0-a3b-c7-PREVIEW.json'
recording = notes / 'issue-15c-c7-recording'
receipt = load(recording / 'owner-acceptance.json')
followup = load(recording / 'recorded-followup.json')
real = ROOT / receipt['successor_oracle']
assert sha(real) == followup['successor_sha256'] == '2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373'
assert sha(preview) == receipt['reviewed_preview_sha256'] == 'd661cc3be22aa6aca996a4e67cac4f8ebbd2dfa1908dd29a0c7ae2e38177ef6d'
for path_key, hash_key in [('receipt','receipt_sha256'),('integration_authorization','integration_authorization_sha256'),('owner_packet','owner_packet_sha256'),('prior_oracle','prior_oracle_sha256')]:
    assert sha(ROOT / receipt[path_key]) == receipt[hash_key], path_key
preview_report = load(notes / 'issue-15c-c7-native/reports/c7-preview.json')
for filename, digest in preview_report['pins'].items():
    assert sha(ROOT / filename) == digest, filename
for batch, data in preview_report['batches'].items():
    assert sha(preview_dir / f'{batch}-C7-PROPOSAL.json') == data['rendered_proposal_sha256']
p,r = load(preview),load(real)
assert p.keys()==r.keys()
assert all(p[k]==r[k] for k in p if k!='acceptance')
touch = {'character-origins-feats','equipment'}
evidence = {'rule','reviewer','accepted_at'}
counts = collections.Counter()
assert p['acceptance'].keys()==r['acceptance'].keys()
for name, rows in p['acceptance'].items():
    after = r['acceptance'][name]
    if name not in {'batches','records','review_unit_records'}:
        assert rows == after, name
        continue
    def key(x): return (x['batch_id'], x.get('span_id',x.get('unit_id','')))
    a,b = {key(x):x for x in rows},{key(x):x for x in after}
    assert len(a)==len(rows) and len(b)==len(after) and a.keys()==b.keys()
    assert [x for x in rows if x['batch_id'] not in touch] == [x for x in after if x['batch_id'] not in touch]
    for k,x in a.items():
        y=b[k]
        assert x.keys()==y.keys()
        for field in x:
            if x[field] != y[field]:
                assert field in evidence and x['batch_id'] in touch,(name,k,field)
                counts[f'{name}.{field}'] += 1
                if field=='reviewer': assert y[field] == receipt['owner']
                if field=='accepted_at': assert y[field] == followup['recorded_at'] and y[field]>receipt['receipt_recorded_at_utc']
                if field=='rule': assert repr(receipt['exact_user_message']) in y[field]
assert dict(counts)==followup['comparison_with_reviewed_preview']['evidence_changed']
assert b'SIMULATION' not in real.read_bytes()
from afterworlds.ingestion.mechanical.oracle import load_accepted_inputs,serialize_accepted_inputs,oracle_identity,candidate_from_accepted_inputs,committed_inputs_for,SUPERSEDED_ORACLE_SHA256
from afterworlds.ingestion.mechanical.projection import identify_projection
import afterworlds
native=load_accepted_inputs(real)
assert serialize_accepted_inputs(native)==real.read_bytes()
assert oracle_identity(native.oracle)==receipt['oracle_identity']
ident=identify_projection(candidate_from_accepted_inputs(native))
assert str(ident.projection_uuid)==receipt['projection'] and ident.payload_hash==receipt['projection_payload_hash']
selected=committed_inputs_for(native.oracle.binding.package_uuid,native.oracle.binding.release_version)
assert selected is not None and oracle_identity(selected.oracle)==receipt['oracle_identity']
assert SUPERSEDED_ORACLE_SHA256 == {receipt['prior_oracle_sha256'],followup['g1_sha256_after'],followup['predecessor_sha256_after']}

base=json.loads(subprocess.check_output(['git','show','e83018c:.secrets.baseline']))
current=load(ROOT / '.secrets.baseline')
settings_changes={k:[base.get(k),current.get(k)] for k in base.keys()|current.keys() if k not in {'results','generated_at'} and base.get(k)!=current.get(k)}
def entries(data): return {(f,e['type'],e['hashed_secret']):e for f,ee in data['results'].items() for e in ee}
be,ce=entries(base),entries(current)
added=ce.keys()-be.keys()
removed=be.keys()-ce.keys()
groups=collections.Counter((f,t) for f,t,h in added)
nonhex=[{'file':f,**ce[f,t,h]} for f,t,h in added if t!='Hex High Entropy String']
out={'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'import_path':afterworlds.__file__,'recording_sha256':sha(real),'preview_sha256':sha(preview),'recording_comparison':'PASS','evidence_changes':dict(counts),'oracle_identity':oracle_identity(native.oracle),'projection':str(ident.projection_uuid),'payload_hash':ident.payload_hash,'native_roundtrip_and_selection':'PASS','baseline_sha256':sha(ROOT / '.secrets.baseline'),'baseline_settings_changes':settings_changes,'baseline_added':len(added),'baseline_removed':len(removed),'baseline_addition_groups':[{'file':f,'type':t,'count':n} for (f,t),n in sorted(groups.items())],'baseline_nonhex_additions':nonhex,'baseline_audit_flag_changes':dict(collections.Counter(str(be[k].get('is_secret'))+' -> '+str(ce[k].get('is_secret')) for k in be.keys()&ce.keys() if be[k].get('is_secret')!=ce[k].get('is_secret')))}
print(json.dumps(out,indent=2))
