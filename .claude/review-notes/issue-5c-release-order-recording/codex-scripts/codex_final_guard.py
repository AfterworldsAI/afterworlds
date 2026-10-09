"""Seal preservation after reviewed pin edits and additive hash coverage."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DEST=ROOT/'.claude/review-notes/issue-5c-release-order-recording'
subprocess.run([str(ROOT/'venv/Scripts/python.exe'),str(HERE/'codex_delta.py')],cwd=ROOT,check=True,capture_output=True)
result=json.loads((HERE/'codex-delta.json').read_text())
allowed=json.loads((HERE/'reviewed-pin-allowlist.json').read_text())
result['checks']['only_reviewed_existing_files_changed']=all(r['path'].replace('\\','/') in allowed for r in result['changed_existing_files'])
a=json.loads((HERE/'pre-edit/secrets.baseline').read_text())
b=json.loads((ROOT/'.secrets.baseline').read_text())
result['checks']['baseline_settings_exact']=all(a[k]==b[k] for k in a if k!='results')
result['checks']['baseline_prior_entries_exact']=all(b['results'].get(k,[])[:len(v)]==v for k,v in a['results'].items())
new_paths=set(b['results'])-set(a['results'])
result['checks']['baseline_only_authorized_paths_added']=all(k.replace('\\','/').startswith('.claude/review-notes/issue-5c-release-order-recording') or k.replace('\\','/') in allowed or k.replace('\\','/')=='src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b.json' for k in new_paths)
result['checks']['recorded_oracle_sha_exact']=hashlib.sha256((ROOT/'src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b.json').read_bytes()).hexdigest()=='def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c'
usage=json.loads((HERE/'restart-release-order-recording-usage.json').read_text())
result['checks']['claude_run_completed']=usage['process_exit_code']==0 and usage['result_present'] and usage['result_subtype']=='success' and not usage['is_error']
original=set(json.loads((HERE/'pre-edit/snapshot.json').read_text())['file_hashes'])
paths=set(subprocess.check_output(['rtk','proxy','git','ls-files','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0'))
new_files=sorted(k for k in paths-original if k and not k.startswith('.claude/_sp/') and (ROOT/k).is_file())
receipt_path='.claude/review-notes/issue-5c-release-order-recording/codex-final-preservation.json'
new_files=sorted(set(new_files)|{receipt_path})
result['checks']['new_git_visible_files_scoped']=all(k.replace('\\','/').startswith('.claude/review-notes/issue-5c-release-order-recording') or k.replace('\\','/')=='src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b.json' for k in new_files)
result['new_git_visible_files']=new_files
for row in result['changed_existing_files']:
    if row['path']=='.secrets.baseline':
        row.pop('after')
        row['after_validation']='Additive inspected public-hash entries only; previous entries and settings exact. Current baseline hash omitted to avoid recursive hash coverage.'
result['scope']='Native exact-candidate recording and bounded live-pin verification only; no staging, commit, push, merge, publication, activation, shared-store writes or expanded gates.'
data=json.dumps(result,indent=2)+'\n'
target=DEST/'codex-final-preservation.json'
if target.exists():
    assert target.read_text()==data,'Final preservation state changed; inspect before replacing receipt'
else:
    target.write_text(data,encoding='utf-8')
print(json.dumps({'checks':result['checks'],'changed_existing_files':[r['path'] for r in result['changed_existing_files']],'new_git_visible_files':len(new_files)},indent=2))
raise SystemExit(0 if all(result['checks'].values()) else 1)
