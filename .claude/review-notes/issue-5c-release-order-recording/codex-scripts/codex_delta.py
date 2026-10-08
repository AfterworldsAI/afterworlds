"""Report current recording delta against the fresh dirty-tree snapshot."""
import hashlib
import json
import importlib.metadata
import platform
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DEST=ROOT/'.claude/review-notes/issue-5c-release-order-recording'
before=json.loads((HERE/'pre-edit/snapshot.json').read_text())
def sha(p):
    return hashlib.file_digest(p.open('rb'),'sha256').hexdigest() if p.is_file() else None
def git(*args):
    return subprocess.check_output(['rtk','proxy','git',*args],cwd=ROOT).decode().strip()
changes=[{'path':k,'before':v['sha256'],'after':sha(ROOT/k)} for k,v in before['file_hashes'].items() if sha(ROOT/k)!=v['sha256']]
checks={
 'head_exact':git('rev-parse','HEAD')==before['head'],
 'branch_exact':git('branch','--show-current')==before['branch'],
 'index_exact':sha(ROOT/'.git/index')==before['index_sha256'],
 'stashes_exact':git('stash','list','--format=%H %gd %s')==before['stashes'].strip(),
 'external_exact':all(sha(Path(k))==v for k,v in before['external_hashes'].items()),
 'accepted_candidate_exact':sha(DEST/'accepted-candidate.json')=='8a6a9a9c305f41207190c0deb55875a027019116ce3f825a6a0425a3a115b4bf',
 'old_oracle_retained_exact':sha(DEST/'prior-live-oracle.json')==before['oracle_sha256'],
 'restart_history_exact':(ROOT/'docs/architecture/issue-5c-5d-clean-restart.md').read_bytes().split(b'## Historical implementation record',1)[1]==(HERE/'pre-edit/restart.md').read_bytes().split(b'## Historical implementation record',1)[1],
}
native=json.loads((ROOT/'.claude/review-notes/issue-5c-release-order-codex-evidence/native-code-fingerprint.json').read_text())
checks['native_python_code_fingerprint_exact']=all(sha(ROOT/k)==v for k,v in native['source_files'].items())
checks['native_python_version_exact']=platform.python_version()==native['python']
checks['native_dependency_versions_exact']=all(importlib.metadata.version(k)==v for k,v in native['dependencies'].items())
checks['isolated_old_source_store_exact']=sha(ROOT/'.claude/_sp/release-order-candidate/rel-old/afterworlds.db')=='91da4ada4c56c3ab7d38fe7bfc098b52a30e548cc4f3ac44789bbdcec74e7d32'
checks['isolated_new_source_store_exact']=sha(ROOT/'.claude/_sp/release-order-candidate/rel-new/afterworlds.db')=='f2067b83d5ba9cbcd8165540517a826c08c023b9aa94a0e1d3e8cca3d2d57c4b'
result={'checks':checks,'changed_existing_files':changes}
(HERE/'codex-delta.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':checks,'changed_existing_files':[r['path'] for r in changes]},indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
