"""Check later committed/working changes without re-running the review or gates."""
import datetime
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess

ROOT = Path.cwd()
assert str(ROOT).lower() == r'D:\AI\Claude\scratch\AW docs\issue2b-implementation\afterworlds'.lower()
OUT = Path(__file__).parent
data = json.loads((OUT / 'results.json').read_bytes())
reviewed = data['reviewed_commit']
def git(*args):
    return subprocess.check_output(['git', *args])
current = git('rev-parse', 'HEAD').decode().strip()
paths = [s['file'].replace('\\', '/') for s in data['sources']]
controls = ['.secrets.baseline', '.pre-commit-config.yaml', '.github', '.gitignore']
changed = git('diff', '--name-only', reviewed, current, '--', *controls, *paths).decode().splitlines()
working = []
for path in ['.secrets.baseline', *paths]:
    original = git('show', reviewed + ':' + path)
    actual = Path(path).read_bytes()
    if original.replace(b'\r\n',b'\n') != actual.replace(b'\r\n',b'\n'):
        working.append(path)
config_working = git('diff', '--name-only', current, '--', *controls).decode().splitlines()
result = {'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'reviewed_commit':reviewed,
          'current_commit':current,'later_committed_changes_to_review_inputs':changed,
          'working_source_or_baseline_changes_after_line_ending_normalization':working,
          'working_control_changes':config_working,'detect_secrets_version':importlib.metadata.version('detect-secrets'),
          'working_baseline_raw_sha256':hashlib.sha256(Path('.secrets.baseline').read_bytes()).hexdigest(),
          'review_still_applies_to_inputs':not(changed or working or config_working)}
assert git('rev-parse', 'HEAD').decode().strip() == current, 'HEAD moved during final check'
(OUT / 'invalidation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
