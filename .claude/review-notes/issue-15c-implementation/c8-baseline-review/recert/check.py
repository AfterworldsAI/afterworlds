"""Immutable C8 recert baseline delta audit; no application imports or scanning."""
import collections
import datetime
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
from detect_secrets.plugins.high_entropy_strings import HexHighEntropyString

BASE = '183a664e8645ecadd97c55517e8ba1120e9c5b19'
HEAD = '555be9aed30e48bd05a469c73092177bb676e400'
SOURCE = '.claude/review-notes/issue-15c-implementation/recert/governing-components.json'
PRODUCERS = ['.claude/review-notes/issue-15c-implementation/recert/governing_components.py',
             'src/afterworlds/services/dnd5e_state/authority.py',
             'src/afterworlds/pipeline/rpg/capability.py',
             'tests/services/dnd5e_state/builders.py']
assert str(Path.cwd()).lower() == r'D:\AI\Claude\scratch\AW docs\issue2b-implementation\afterworlds'.lower()

def git(*args):
    return subprocess.check_output(['git', *args])

def blob(rev, path):
    return git('show', rev + ':' + path.replace('\\', '/'))

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def entries(data):
    result = {(p,e['type'],e['hashed_secret']):e for p,es in data['results'].items() for e in es}
    assert len(result) == sum(map(len,data['results'].values()))
    return result

def fields(obj, value, trail=''):
    if isinstance(obj,dict):
        for k,v in obj.items():
            yield from fields(v,value,trail+'/'+k)
    elif isinstance(obj,list):
        for i,v in enumerate(obj):
            yield from fields(v,value,trail+'/'+str(i))
    elif obj == value:
        yield trail

raws = {r:blob(r,'.secrets.baseline') for r in (BASE,HEAD)}
baselines = {r:json.loads(raws[r]) for r in raws}
a,b = (entries(baselines[r]) for r in (BASE,HEAD))
added,removed = b.keys()-a.keys(),a.keys()-b.keys()
modified = {k for k in a.keys()&b.keys() if a[k]!=b[k]}
changed_fields = collections.Counter(f for k in modified for f in a[k].keys()|b[k].keys() if a[k].get(f)!=b[k].get(f))
assert set(changed_fields)=={'line_number'}
assert all(k[0].replace('\\','/')==SOURCE for k in added|removed|modified)
assert {k:v for k,v in baselines[BASE].items() if k!='results'} == {k:v for k,v in baselines[HEAD].items() if k!='results'}
controls=['.pre-commit-config.yaml','.github','.gitignore']
assert not git('diff','--name-only',BASE,HEAD,'--',*controls)
assert importlib.metadata.version('detect-secrets') == '1.5.0'
limit=next(p['limit'] for p in baselines[HEAD]['plugins_used'] if p['name']=='HexHighEntropyString')
assert limit==3.0
plugin=HexHighEntropyString(limit=limit)
source_raws={r:blob(r,SOURCE) for r in (BASE,HEAD)}
docs={r:json.loads(v) for r,v in source_raws.items()}

def inspect(rev,key,e,kind):
    line=source_raws[rev].decode().splitlines()[e['line_number']-1]
    values=[v for v in re.findall('[a-fA-F0-9]+',line) if hashlib.sha1(v.encode()).hexdigest()==key[2]]
    assert len(values)==1
    value=values[0]
    assert len(value)==64
    assert e['type']=='Hex High Entropy String' and e['filename']==key[0]
    assert set(e)=={'type','filename','hashed_secret','is_verified','line_number'} and e['is_verified'] is False
    assert any(d.type==key[1] and d.secret_hash==key[2] and d.filename==key[0] for d in plugin.analyze_line(key[0],line,e['line_number']))
    locations=list(fields(docs[rev],value))
    assert locations
    if all(p.endswith('/fingerprint') for p in locations):
        category='Mechanical procedure fingerprint'
        for p in locations:
            op=p.split('/')[2]
            components=docs[rev]['operations'][op]['components']
            assert sha(json.dumps(sorted(components),separators=(',',':')).encode())==value
            assert ('fingerprint="'+value+'"').encode() in blob(rev,PRODUCERS[2])
    else:
        category='Mechanical component schema digest'
        assert all(re.fullmatch('/operations/[^/]+/components/[0-9]+/2',p) for p in locations)
    row={'change':kind,'revision':rev,'file':key[0],'line':e['line_number'],'hashed_secret':key[2],
         'category':category,'fields':locations,'sha1_content_match':True,'configured_detector_match':True,
         'fingerprint_recomputed_and_manifest_matched':category=='Mechanical procedure fingerprint',
         'redacted_source_line':re.sub('[a-fA-F0-9]{20,}','<HEX>',line)}
    return row,value

rows=[]
for kind,rev,keys,es in [('added',HEAD,added,b),('removed',BASE,removed,a)]:
    for key in sorted(keys,key=lambda k:es[k]['line_number']):
        row,value=inspect(rev,key,es[key],kind)
        if kind=='removed':
            assert not list(fields(docs[HEAD],value))
            assert row['fields']==['/operations/creature_attack/fingerprint']
            row['obsolete_value_absent_from_new_source']=True
        rows.append(row)
for key in sorted(modified,key=lambda k:b[k]['line_number']):
    oldrow,oldvalue=inspect(BASE,key,a[key],'relocated_old')
    newrow,newvalue=inspect(HEAD,key,b[key],'relocated')
    assert oldvalue==newvalue
    newrow['old_line']=a[key]['line_number']
    rows.append(newrow)

oldops,newops=docs[BASE]['operations'],docs[HEAD]['operations']
ops=[]
for name in sorted(oldops.keys()|newops.keys()):
    old,new=oldops.get(name,{}),newops.get(name,{})
    aa={tuple(c) for c in old.get('components',[])};bb={tuple(c) for c in new.get('components',[])}
    if old!=new:
        ops.append({'operation':name,'old_components':len(aa),'new_components':len(bb),
                    'added_component_tuples':len(bb-aa),'removed_component_tuples':len(aa-bb),
                    'fingerprint_change':'added' if not old else 'changed' if old['fingerprint']!=new['fingerprint'] else 'unchanged',
                    'added_record_component_pairs':[[c[0],c[1]] for c in sorted(bb-aa)]})

# Bound inline suppressions added on the manifest's exact public fingerprint constants.
patch=git('diff','--unified=0',BASE,HEAD,'--',PRODUCERS[2]).decode()
added_allowlists=[l for l in patch.splitlines() if l.startswith('+') and not l.startswith('+++') and 'allowlist secret' in l]
assert len(added_allowlists)==2
for line in added_allowlists:
    value=re.search('fingerprint="([a-f0-9]{64})"',line).group(1)
    assert any(newops[op]['fingerprint']==value for op in ('creature_attack','creature_species'))

current=git('rev-parse','HEAD').decode().strip()
paths=['.secrets.baseline',SOURCE,*PRODUCERS]
later=git('diff','--name-only',HEAD,current,'--',*paths,*controls).decode().splitlines()
working=[p for p in paths if blob(HEAD,p).replace(b'\r\n',b'\n')!=Path(p).read_bytes().replace(b'\r\n',b'\n')]
control_working=git('diff','--name-only',current,'--',*controls).decode().splitlines()
assert git('rev-parse','HEAD').decode().strip()==current
out={'base_commit':BASE,'reviewed_commit':HEAD,'baseline_sha256':{r:sha(v) for r,v in raws.items()},
     'source_sha256':{r:sha(v) for r,v in source_raws.items()},
     'producer_sha256':{p:sha(blob(HEAD,p)) for p in PRODUCERS},
     'governing_issue_working_sha256':sha(Path('.claude/review-notes/issue-15c-preparation/issue-draft.md').read_bytes()),
     'total_baseline_entries':{'base':len(a),'reviewed':len(b)},
     'source_baseline_entries':{r:len(baselines[r]['results'][SOURCE.replace('/','\\')]) for r in (BASE,HEAD)},
     'added':len(added),'removed':len(removed),'modified_existing_entries':len(modified),'changed_entry_fields':dict(changed_fields),
     'unchanged_existing_entries':len(a.keys()&b.keys())-len(modified),
     'added_categories':dict(collections.Counter(r['category'] for r in rows if r['change']=='added')),
     'removed_categories':dict(collections.Counter(r['category'] for r in rows if r['change']=='removed')),
     'operation_content_changes':ops,'binding_changed_fields':[k for k in docs[BASE]['binding'] if docs[BASE]['binding'][k]!=docs[HEAD]['binding'][k]],
     'settings_and_metadata_identical':True,'baseline_audit_flags_unchanged':True,'hook_ci_gitignore_unchanged':True,
     'detect_secrets_version':importlib.metadata.version('detect-secrets'),'hex_limit':limit,
     'new_manifest_inline_allowlists_for_verified_fingerprints':len(added_allowlists),
     'detector_reproductions':len(added)+len(removed)+2*len(modified),
     'negative_control':'Reused prior C7/C8 changed-value subtraction proof; unchanged matcher/settings; not rerun.',
     'invalidation':{'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'current_commit':current,
       'later_committed_input_changes':later,'working_input_changes_normalized':working,'working_control_changes':control_working,
       'scope':'Exact immutable revisions only; later mutable additions remain unreviewed.'},'entries':rows}
Path(__file__).with_name('results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in {'entries','operation_content_changes'}},indent=2))
