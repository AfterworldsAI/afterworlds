"""Supplement completed recording coverage for changed small review evidence."""
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from detect_secrets.core.secrets_collection import SecretsCollection
from detect_secrets.settings import transient_settings
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DEST=ROOT/'.claude/review-notes/issue-5c-release-order-recording'
baseline=ROOT/'.secrets.baseline'
before_bytes=baseline.read_bytes()
before=json.loads(before_bytes)
delta=json.loads((HERE/'codex-delta.json').read_text())
changed={r['path'].replace('\\','/') for r in delta['changed_existing_files'] if r['after'] is not None and r['path']!='.secrets.baseline'}
reused={
 '.claude/review-notes/issue-5c-release-order-recording/accepted-candidate.json':'8a6a9a9c305f41207190c0deb55875a027019116ce3f825a6a0425a3a115b4bf',
 '.claude/review-notes/issue-5c-release-order-recording/prior-live-oracle.json':'e6f5f36aa3af13807bbff721797d971dcf0d8e588a97483c7d769cf88cbd1308',
 'src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b.json':'def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c',
}
recording_receipt=json.loads((DEST/'recorded-secrets-validation.json').read_text())
assert recording_receipt['private_copy_hook_exit']==0
for name,digest in reused.items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    assert name in before['results'] or name.replace('/','\\') in before['results'],name
files=sorted(({str(p.relative_to(ROOT)).replace('\\','/') for p in DEST.rglob('*') if p.is_file()} | changed | {'.claude/review-notes/issue-5c-release-order-recording-codex-review.md'})-set(reused))
assert all((ROOT/name).is_file() for name in files)
assert all((ROOT/name).stat().st_size<2_000_000 for name in files)
with transient_settings(before):
    found=SecretsCollection()
    for name in files:
        found.scan_file(name)
short_note='.claude/review-notes/issue-5c-release-order-recording/codex-baseline-preservation-note.md'
short_files={short_note,'.claude/review-notes/issue-5c-release-order-recording/codex-scripts/codex_scoped_secrets.py'}
for name,secret in found:
    value=secret.secret_value or ''
    public_sha=bool(re.fullmatch(r'[a-fA-F0-9]{64}',value))
    public_fact_id=name.replace('\\','/') in short_files and value=='68a72ddbcab08b83'
    assert secret.type=='Hex High Entropy String' and (public_sha or public_fact_id),('Unclassified hit requires review',name,secret.type,secret.line_number)
after=json.loads(before_bytes)
added=0
for name,rows in found.json().items():
    existing=after['results'].setdefault(name,[])
    keys={(r['type'],r['hashed_secret']) for r in existing}
    for row in rows:
        key=(row['type'],row['hashed_secret'])
        if key not in keys:
            row['is_secret']=False
            existing.append(row)
            keys.add(key)
            added+=1
assert all(after[k]==before[k] for k in before if k!='results')
assert all(after['results'][k][:len(v)]==v for k,v in before['results'].items())
assert baseline.read_bytes()==before_bytes,'Concurrent baseline edit'
baseline.write_text(json.dumps(after,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
sealed=hashlib.sha256(baseline.read_bytes()).hexdigest()
private=HERE/'codex-private-secrets.baseline'
shutil.copyfile(baseline,private)
def hook(path,label):
    result=subprocess.run([str(ROOT/'venv/Scripts/detect-secrets-hook.exe'),'--baseline',str(path),*files],cwd=ROOT,capture_output=True,text=True)
    (DEST/'run'/f'codex-secrets-{label}.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    (DEST/'run'/f'codex-secrets-{label}.exit').write_text(str(result.returncode)+'\n')
    return result
private_result=hook(private,'private')
real_result=hook(Path('.secrets.baseline'),'real')
assert hashlib.sha256(baseline.read_bytes()).hexdigest()==sealed,'Real hook changed baseline'
assert private_result.returncode==0,private_result.stdout+private_result.stderr
assert real_result.returncode==1 and 'unstaged' in (real_result.stdout+real_result.stderr),real_result.stdout+real_result.stderr
receipt={'scope':'Supplemental small recording/Codex evidence, affected current live pins and final restart opening; immutable payload coverage reused','inspected_hits_are_public_hashes_or_verified_native_fact_id':True,'prior_entries_exact':True,'baseline_settings_exact':True,'public_hash_coverage_present':True,'files_checked':len(files),'reused_immutable_payloads':reused,'private_content_hook_exit':private_result.returncode,'real_unstaged_hook_exit':real_result.returncode,'real_failure_reason':'Baseline is unstaged; staging is not authorized','no_staging':True}
(DEST/'secrets-validation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2))
