"""Restore only refreshed line metadata, retaining reviewed additive coverage."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEST = ROOT / '.claude/review-notes/issue-5c-release-order-recording'
usage = json.loads((HERE / 'restart-release-order-recording-usage.json').read_text())
assert usage['process_exit_code'] == 0 and usage['result_subtype'] == 'success'
assert usage['result_present'] and not usage['is_error']
target = ROOT / '.secrets.baseline'
raw = target.read_bytes()
before = json.loads((HERE / 'pre-edit/secrets.baseline').read_bytes())
current = json.loads(raw)
assert all(current[k] == before[k] for k in before if k != 'results')
changed = []
for name, rows in before['results'].items():
    actual = current['results'][name]
    assert len(actual) >= len(rows)
    for index, original in enumerate(rows):
        existing = actual[index]
        assert {k: v for k, v in existing.items() if k != 'line_number'} == {
            k: v for k, v in original.items() if k != 'line_number'}, name
        if existing != original:
            changed.append({'path': name, 'row_index': index,
                'original_line': original['line_number'], 'refreshed_line': existing['line_number']})
            actual[index] = original
assert target.read_bytes() == raw, 'Concurrent baseline edit'
if changed:
    target.write_text(json.dumps(current, indent=2, sort_keys=True) + '\n',
        encoding='utf-8', newline='\n')
after = json.loads(target.read_bytes())
assert all(after['results'][name][:len(rows)] == rows for name, rows in before['results'].items())
receipt = {'operation': ('Restore original baseline line metadata' if changed
    else 'Verify all original baseline rows remain exact; no restoration needed'),
    'baseline_before_restoration_sha256': hashlib.sha256(raw).hexdigest(),
    'prior_rows_exact': True, 'settings_exact': True,
    'reviewed_new_entries_retained': True, 'restored_rows': changed,
    'no_detector_settings_or_secret_classification_changed': True,
    'no_staging': True}
out = DEST / 'codex-baseline-preservation.json'
assert not out.exists()
out.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'prior_rows_exact': True, 'rows_restored': len(changed)}, indent=2))
