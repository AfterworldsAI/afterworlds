"""Immutable-blob, narrow secret-baseline review. No matched values are emitted."""
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

from detect_secrets.plugins.high_entropy_strings import HexHighEntropyString

BASE = '1d4193c4b162e3db4df3a3240d00313f36dd918b'
HEAD = '5c4d8d6e56c015862cb16f5e34d2229c985faf5a'
ROOT = Path.cwd()
assert str(ROOT).lower() == r'D:\AI\Claude\scratch\AW docs\issue2b-implementation\afterworlds'.lower()

def git(*args):
    return subprocess.check_output(['git', *args])

def blob(rev, path):
    return git('show', rev + ':' + path.replace('\\', '/'))

def entries(data):
    rows = {(p, e['type'], e['hashed_secret']): e for p, es in data['results'].items() for e in es}
    assert len(rows) == sum(map(len, data['results'].values()))
    return rows

def fields(obj, value, trail=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from fields(v, value, trail + '/' + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from fields(v, value, trail + '/' + str(i))
    elif obj == value:
        yield trail

old_raw, new_raw = blob(BASE, '.secrets.baseline'), blob(HEAD, '.secrets.baseline')
old, new = json.loads(old_raw), json.loads(new_raw)
a, b = entries(old), entries(new)
added = b.keys() - a.keys()
assert not a.keys() - b.keys()
assert all(a[k] == b[k] for k in a.keys() & b.keys())
assert {k:v for k,v in old.items() if k != 'results'} == {k:v for k,v in new.items() if k != 'results'}
assert not git('diff', '--name-only', BASE, HEAD, '--', '.pre-commit-config.yaml', '.github')
limit = next(p['limit'] for p in new['plugins_used'] if p['name'] == 'HexHighEntropyString')
plugin = HexHighEntropyString(limit=limit)
rows, sources = [], []
for path in sorted({k[0] for k in added}):
    raw = blob(HEAD, path)
    lines = raw.decode('utf-8').splitlines()
    parsed = json.loads(raw) if path.endswith('.json') else None
    if path.endswith('c8-build.log.out'):
        parsed = json.JSONDecoder().raw_decode(raw.decode('utf-8')[raw.index(b'{'):])[0]
    sources.append({'file':path, 'committed_blob_sha256':hashlib.sha256(raw).hexdigest()})
    for key in sorted((k for k in added if k[0] == path), key=lambda k:(b[k]['line_number'],k[2])):
        e = b[key]
        assert key[1] == 'Hex High Entropy String'
        assert set(e) == {'type','filename','hashed_secret','is_verified','line_number'}
        assert e['filename'] == path and e['is_verified'] is False
        number = e['line_number']
        line = lines[number-1]
        matches = [m for m in re.findall(r'[a-fA-F0-9]+', line) if hashlib.sha1(m.encode()).hexdigest() == key[2]]
        assert len(matches) == 1, (path, number, 'no unique match')
        value = matches[0]
        assert len(value) in {40, 64}, (path, number, 'unexpected token length')
        assert any(d.type == key[1] and d.secret_hash == key[2] and d.filename == path for d in plugin.analyze_line(path, line, number)), (path, number, 'detector mismatch')
        locations = list(fields(parsed, value)) if parsed is not None else []
        category = None
        if len(value) == 40:
            assert git('cat-file', '-t', value).decode().strip() == 'commit'
            category = 'Git revision pin'
        elif path.endswith(('build_c8_preview.py', 'original-build_c8_preview.py')):
            assert number in {123,158,161,162,163,164,165,185,186,190,191,195,196,200,201,205,206}
            category = ('Mechanical schema digest' if number == 123 else
                        'Mechanical proposal identity' if number in {186,191,196,201,206} else
                        'Artifact/source SHA-256 pin')
        elif path.endswith('original-common.py'):
            assert number in {37,39,42,46,51,52,53,54}
            category = 'Artifact/source SHA-256 pin'
        else:
            assert locations, (path, number, 'no JSON field context')
            if any(p.endswith(('/schema/1','/schema_hash','/schema20_hash','/schema21_pin','/prior_schema_hash','/preview_schema_hash')) for p in locations):
                category = 'Mechanical schema digest'
            elif any(p.endswith(('/proposal_identity','/accepted_proposal_identity')) for p in locations):
                category = 'Mechanical proposal identity'
            elif any(p.endswith(('/payload_hash','/successor_lifted_payload_hash')) for p in locations):
                category = 'Mechanical projection payload digest'
            elif '/oracle_identity' in locations:
                category = 'Mechanical oracle identity'
            elif any('sha256' in p or p.startswith(('/pins/','/accepted_inputs_located/','/launch/native_pins/','/working_packet_code_pins_unchanged/','/r2_hashes/')) for p in locations):
                category = 'Artifact/source SHA-256 pin'
        assert category, (path, number, 'unclassified')
        rows.append({'file':path, 'line':number, 'detector':key[1], 'matched_hex_length':len(value), 'category':category,
                     'fields':locations, 'redacted_source_line':re.sub(r'[a-fA-F0-9]{20,}', '<HEX>', line),
                     'sha1_content_match':True, 'configured_detector_match':True})
transitions=[]
prior=a
for rev in git('rev-list','--reverse',BASE+'..'+HEAD,'--','.secrets.baseline').decode().splitlines():
    current=entries(json.loads(blob(rev,'.secrets.baseline')))
    transitions.append({'commit':rev,'added':len(current.keys()-prior.keys()),'removed':len(prior.keys()-current.keys()),'changed_existing':sum(current[k]!=prior[k] for k in current.keys()&prior.keys())})
    prior=current
assert prior==b
out={'base_commit':BASE,'reviewed_commit':HEAD,'base_baseline_sha256':hashlib.sha256(old_raw).hexdigest(),'reviewed_baseline_sha256':hashlib.sha256(new_raw).hexdigest(),
     'settings_identical_including_metadata':True,'ci_and_hook_config_unchanged':True,'added':len(added),'removed':0,'modified_existing_entries':0,
     'is_secret_added_or_modified':0,'new_is_verified_false':len(rows),'configured_hex_entropy_limit':limit,'in_memory_detector_matches':len(rows),
     'categories':dict(collections.Counter(r['category'] for r in rows)),'transitions':transitions,'sources':sources,'entries':rows,
     'negative_control':'Reuse independently reviewed C7 and post-C7 evidence; unchanged settings and matching machinery; not repeated.'}
Path(__file__).with_name('results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in {'entries','sources'}},indent=2))
