"""Read-only, exact-revision baseline delta checks; prints no matched values.
Run from the specified implementation checkout with venv/Scripts/python.exe -B.
Does not invoke review probes, application code, hooks, candidate builders or stores.
"""
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess
from detect_secrets.plugins.high_entropy_strings import HexHighEntropyString

BASE = 'b5051d8433ac2be7336daa41f2aae038b9d21c9e'
HEAD = '1d4193c4b162e3db4df3a3240d00313f36dd918b'
ROOT = Path.cwd()
assert str(ROOT).lower() == r'D:\AI\Claude\scratch\AW docs\issue2b-implementation\afterworlds'.lower()

def git(*args):
    return subprocess.check_output(['git', *args])

def blob(revision, path):
    return git('show', revision + ':' + path.replace('\\', '/'))

def entries(data):
    rows = {(p, e['type'], e['hashed_secret']): e for p, es in data['results'].items() for e in es}
    assert len(rows) == sum(map(len, data['results'].values()))
    return rows

def norm(raw):
    return raw.replace(b'\r\n', b'\n')

def fields(obj, target, trail=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from fields(v, target, trail + '/' + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from fields(v, target, trail + '/' + str(i))
    elif obj == target:
        yield trail

assert git('rev-parse', 'HEAD').decode().strip() == HEAD
old_raw, new_raw = blob(BASE, '.secrets.baseline'), blob(HEAD, '.secrets.baseline')
old, new = json.loads(old_raw), json.loads(new_raw)
a, b = entries(old), entries(new)
added, removed = b.keys() - a.keys(), a.keys() - b.keys()
assert not removed
assert all(a[k] == b[k] for k in a.keys() & b.keys())
assert {k:v for k,v in old.items() if k != 'results'} == {k:v for k,v in new.items() if k != 'results'}
assert norm(Path('.secrets.baseline').read_bytes()) == norm(new_raw)
assert not git('diff', '--name-only', BASE, HEAD, '--', '.pre-commit-config.yaml', '.github')
assert not git('diff', '--name-only', HEAD, '--', '.secrets.baseline', '.pre-commit-config.yaml', '.github')
limit = next(p['limit'] for p in new['plugins_used'] if p['name'] == 'HexHighEntropyString')
plugin = HexHighEntropyString(limit=limit)
rows=[]
for path in sorted({k[0] for k in added}):
    raw=Path(path).read_bytes()
    assert norm(raw) == norm(blob(HEAD,path)),path
    lines=raw.decode('utf-8').splitlines()
    objects = ([json.loads(line) for line in lines if line.startswith('{')] if path.endswith('.jsonl') else [json.loads(raw)]) if path.endswith(('.json','.jsonl')) else []
    for k in sorted((k for k in added if k[0]==path), key=lambda k:(b[k]['line_number'],k[2])):
        assert k[1]=='Hex High Entropy String'
        assert set(b[k]) == {'type','filename','hashed_secret','is_verified','line_number'}
        assert b[k]['filename']==path and b[k]['is_verified'] is False
        line_number=b[k]['line_number']; line=lines[line_number-1]
        matched=[m for m in re.findall(r'[a-fA-F0-9]+',line) if hashlib.sha1(m.encode()).hexdigest()==k[2]]
        assert len(matched)==1,(path,line_number)
        value=matched[0]
        assert len(value) in {40,64}
        detected=plugin.analyze_line(path,line,line_number)
        assert any(d.type==k[1] and d.secret_hash==k[2] and d.filename==path for d in detected),(path,line_number)
        locations=[loc for obj in objects for loc in fields(obj,value)]
        if len(value)==40:
            category='Git revision pin'
            assert git('cat-file','-t',value).decode().strip()=='commit'
        elif any('/provenance/certificate/fingerprint' in x for x in locations):
            category='Mechanical certificate fingerprint'
        elif any('/provenance/templates/' in x for x in locations):
            category='Mechanical template fingerprint'
        else:
            category='Artifact/source SHA-256 pin'
        rows.append({'file':path,'line':line_number,'detector':k[1],'matched_hex_length':len(value),'category':category,'json_field_examples':locations[:2],'sha1_content_match':True,'configured_detector_match':True})
transitions=[]
prior=a
for rev in git('rev-list','--reverse',BASE+'..'+HEAD,'--','.secrets.baseline').decode().splitlines():
    current=entries(json.loads(blob(rev,'.secrets.baseline')))
    transitions.append({'commit':rev,'added':len(current.keys()-prior.keys()),'removed':len(prior.keys()-current.keys()),'changed_existing':sum(current[k]!=prior[k] for k in current.keys()&prior.keys())})
    prior=current
assert prior==b
out={'base_commit':BASE,'reviewed_commit':HEAD,'base_baseline_sha256':hashlib.sha256(old_raw).hexdigest(),'reviewed_baseline_sha256':hashlib.sha256(new_raw).hexdigest(),'worktree_baseline_raw_sha256':hashlib.sha256(Path('.secrets.baseline').read_bytes()).hexdigest(),'settings_identical_including_metadata':True,'ci_and_hook_config_unchanged':True,'referenced_worktree_content_matches_head_after_line_ending_normalization':True,'added':len(added),'removed':len(removed),'modified_existing_entries':0,'is_secret_added_or_modified':0,'new_is_verified_false':len(rows),'configured_hex_entropy_limit':limit,'in_memory_detector_matches':len(rows),'categories':dict(collections.Counter(r['category'] for r in rows)),'transitions':transitions,'entries':rows,'negative_control':'Reused C7 review evidence; unchanged settings and matching machinery; not repeated.'}
print(json.dumps(out,indent=2))
