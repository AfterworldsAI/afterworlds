"""Only the new C8 recording baseline delta; immutable blobs, no application imports."""
import collections
import datetime
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
from detect_secrets.plugins.high_entropy_strings import HexHighEntropyString

BASE = '5c4d8d6e56c015862cb16f5e34d2229c985faf5a'
HEAD = '183a664e8645ecadd97c55517e8ba1120e9c5b19'
ROOT = Path.cwd()
assert str(ROOT).lower() == r'D:\AI\Claude\scratch\AW docs\issue2b-implementation\afterworlds'.lower()

def git(*args):
    return subprocess.check_output(['git', *args])

def blob(rev, path):
    return git('show', rev + ':' + path.replace('\\', '/'))

def entries(data):
    result = {(p,e['type'],e['hashed_secret']):e for p,es in data['results'].items() for e in es}
    assert len(result) == sum(map(len,data['results'].values()))
    return result

def fields(obj, target, trail=''):
    if isinstance(obj, dict):
        for k,v in obj.items():
            yield from fields(v,target,trail+'/'+k)
    elif isinstance(obj,list):
        for i,v in enumerate(obj):
            yield from fields(v,target,trail+'/'+str(i))
    elif obj == target:
        yield trail

old_raw,new_raw = blob(BASE,'.secrets.baseline'),blob(HEAD,'.secrets.baseline')
old,new = json.loads(old_raw),json.loads(new_raw)
a,b = entries(old),entries(new)
added = b.keys()-a.keys()
assert not a.keys()-b.keys()
assert all(a[k]==b[k] for k in a.keys()&b.keys())
assert {k:v for k,v in old.items() if k!='results'} == {k:v for k,v in new.items() if k!='results'}
controls = ['.secrets.baseline','.pre-commit-config.yaml','.github','.gitignore']
assert not git('diff','--name-only',BASE,HEAD,'--',*controls[1:])
limit=next(p['limit'] for p in new['plugins_used'] if p['name']=='HexHighEntropyString')
plugin=HexHighEntropyString(limit=limit)
sources,rows=[],[]
for path in sorted({k[0] for k in added}):
    raw=blob(HEAD,path)
    lines=raw.decode().splitlines()
    parsed=json.loads(raw) if path.endswith('.json') else None
    sources.append({'file':path,'committed_blob_sha256':hashlib.sha256(raw).hexdigest()})
    for key in sorted((k for k in added if k[0]==path),key=lambda k:b[k]['line_number']):
        e=b[key];n=e['line_number'];line=lines[n-1]
        assert key[1]=='Hex High Entropy String'
        assert set(e)=={'type','filename','hashed_secret','is_verified','line_number'}
        assert e['filename']==path and e['is_verified'] is False
        matched=[m for m in re.findall('[a-fA-F0-9]+',line) if hashlib.sha1(m.encode()).hexdigest()==key[2]]
        assert len(matched)==1,(path,n,'content match')
        value=matched[0]
        assert len(value) in {40,64}
        assert any(d.type==key[1] and d.secret_hash==key[2] and d.filename==path for d in plugin.analyze_line(path,line,n)),(path,n,'detector')
        locations=list(fields(parsed,value)) if parsed is not None else []
        category=None
        if len(value)==40:
            assert git('cat-file','-t',value).decode().strip()=='commit'
            category='Git revision pin'
        elif path.endswith('record_successor.py'):
            if n in {73,77,81,85,89}: category='Mechanical proposal identity'
            elif n==115: category='Mechanical schema digest'
            elif n==117: category='Mechanical oracle identity'
            elif n==119: category='Mechanical projection payload digest'
            elif n in {72,76,80,84,88,93,96,98,100,101,102,103,104,105,106}: category='Artifact/source SHA-256 pin'
        elif path.endswith('record.out.txt'):
            assert n==45 and 'payload_hash' in line
            category='Mechanical projection payload digest'
        elif '/schema/1' in locations: category='Mechanical schema digest'
        elif '/oracle_identity' in locations: category='Mechanical oracle identity'
        elif any(p.endswith(('/payload_hash','/projection_payload_hash')) for p in locations): category='Mechanical projection payload digest'
        elif any(p.startswith('/proposal_identities/') for p in locations): category='Mechanical proposal identity'
        elif any('sha256' in p for p in locations): category='Artifact/source SHA-256 pin'
        assert category,(path,n,'unclassified')
        rows.append({'file':path,'line':n,'detector':key[1],'matched_hex_length':len(value),'category':category,'fields':locations,
                     'redacted_source_line':re.sub('[a-fA-F0-9]{20,}','<HEX>',line),'sha1_content_match':True,'configured_detector_match':True})

# Check the sole newly recorded oracle identity pin against its committed bytes.
followup=json.loads(blob(HEAD,'.claude/review-notes/issue-15c-c8-recording/recorded-followup.json'))
assert hashlib.sha256(blob(HEAD,followup['successor'])).hexdigest()==followup['successor_sha256']
current=git('rev-parse','HEAD').decode().strip()
paths=[s['file'].replace('\\','/') for s in sources]
changed=git('diff','--name-only',HEAD,current,'--',*controls,*paths).decode().splitlines()
working=[]
for path in ['.secrets.baseline',*paths]:
    if blob(HEAD,path).replace(b'\r\n',b'\n')!=Path(path).read_bytes().replace(b'\r\n',b'\n'):
        working.append(path)
config_working=git('diff','--name-only',current,'--',*controls).decode().splitlines()
assert git('rev-parse','HEAD').decode().strip()==current,'HEAD moved during final check'
out={'base_commit':BASE,'reviewed_commit':HEAD,'base_baseline_sha256':hashlib.sha256(old_raw).hexdigest(),'reviewed_baseline_sha256':hashlib.sha256(new_raw).hexdigest(),
     'added':len(added),'removed':0,'modified_existing_entries':0,'is_secret_added_or_modified':0,'new_is_verified_false':len(rows),
     'settings_identical_including_metadata':True,'hook_ci_and_gitignore_unchanged':True,'configured_hex_entropy_limit':limit,
     'detect_secrets_version':importlib.metadata.version('detect-secrets'),'in_memory_detector_matches':len(rows),
     'categories':dict(collections.Counter(r['category'] for r in rows)),'sources':sources,'entries':rows,
     'recorded_successor_sha256_matches_committed_bytes':True,'recorded_successor_sha256':followup['successor_sha256'],
     'negative_control':'Reused unchanged C7/post-C7/C8 matching-control evidence; not rerun.',
     'invalidation':{'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'current_commit':current,
                     'later_committed_changes_to_review_inputs':changed,'working_source_or_baseline_changes_normalized':working,
                     'working_control_changes':config_working,'review_still_applies_to_inputs':not(changed or working or config_working)}}
Path(__file__).with_name('results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in {'sources','entries'}},indent=2))
