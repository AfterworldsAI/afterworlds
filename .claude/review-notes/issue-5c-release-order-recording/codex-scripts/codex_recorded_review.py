"""Strict accepted-candidate versus recorded-oracle comparison."""
import collections
import datetime
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEST = ROOT / '.claude/review-notes/issue-5c-release-order-recording'
sys.path.insert(0, str(ROOT / 'src'))
from afterworlds.ingestion.mechanical.canonical import canonical_order
from afterworlds.ingestion.mechanical.oracle import load_accepted_inputs, serialize_accepted_inputs

candidate = DEST / 'accepted-candidate.json'
recorded = ROOT / 'src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b.json'
a = json.loads(candidate.read_text(encoding='utf-8'))
b = json.loads(recorded.read_text(encoding='utf-8'))
receipt = json.loads((DEST / 'owner-acceptance.json').read_text())
checks = {'candidate_sha_exact': hashlib.sha256(candidate.read_bytes()).hexdigest() == receipt['candidate_sha256']}
def exact(x, y):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(',', ':')) == json.dumps(y, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
checks['root_keys_exact'] = a.keys() == b.keys()
for key in a.keys() - {'acceptance'}:
    checks['exact_root_' + key] = exact(a[key], b[key])
checks['acceptance_keys_exact'] = a['acceptance'].keys() == b['acceptance'].keys()
changes = []
all_timestamps = set()
fields = {
    'batches': {'rule'},
    'records': {'reviewer', 'accepted_at'},
    'review_unit_records': {'reviewer', 'accepted_at'},
    'reference_resolution_records': {'reviewer', 'authorized_by', 'resolved_at', 'authorization_reference'},
}

def stripped(row, allowed):
    return {k: v for k, v in row.items() if k not in allowed}

for category in a['acceptance']:
    before, after = a['acceptance'][category], b['acceptance'][category]
    if category not in fields:
        checks['exact_acceptance_' + category] = exact(before, after)
        continue
    allowed = fields[category]
    # Only the two native canonical evidence collections can reorder. Their
    # nested scopes, diffs, routes and other semantic arrays stay positional.
    if category in {'records', 'review_unit_records'}:
        canon = lambda row: json.dumps(stripped(row, allowed), sort_keys=True, separators=(',', ':'))
        checks[category + '_only_approval_fields_differ'] = collections.Counter(map(canon, before)) == collections.Counter(map(canon, after))
        checks[category + '_native_canonical_order'] = before == canonical_order(before) and after == canonical_order(after)
    else:
        checks[category + '_only_approval_fields_differ_in_original_order'] = exact([stripped(r, allowed) for r in before], [stripped(r, allowed) for r in after])
    checks[category + '_all_approval_keys_present'] = all(allowed <= r.keys() for r in before + after)
    if category != 'batches':
        checks[category + '_fresh_real_owner'] = all(r['reviewer'] == receipt['owner'] and ('authorized_by' not in r or r['authorized_by'] == receipt['owner']) for r in after)
        time_key = 'resolved_at' if category == 'reference_resolution_records' else 'accepted_at'
        all_timestamps.update(r[time_key] for r in after)
    if category in {'batches', 'reference_resolution_records'}:
        text_key = 'authorization_reference' if category == 'reference_resolution_records' else 'rule'
        checks[category + '_links_fresh_receipt_and_candidate'] = all('owner-acceptance' in r[text_key] and receipt['candidate_sha256'] in r[text_key] for r in after)
    checks[category + '_no_simulation_provenance'] = all('SIMULATION' not in r[k] for r in after for k in allowed)
    changes.append({'category': category, 'rows': len(after), 'permitted_fields': sorted(allowed)})

checks['24_batches'] = len(b['acceptance']['batches']) == 24
checks['1486_real_reference_approvals'] = len(b['acceptance']['reference_resolution_records']) == 1486
checks['proposal_identities_fixed'] = all([r['proposal_identity'] for r in a['acceptance'][k]] == [r['proposal_identity'] for r in b['acceptance'][k]] for k in ['batches', 'schema_anchors'])
checks['single_real_recording_time'] = len(all_timestamps) == 1
created = datetime.datetime.fromisoformat(receipt['receipt_created_at_utc'].replace('Z', '+00:00'))
now = datetime.datetime.now(datetime.UTC)
checks['recording_time_fresh_and_not_future'] = bool(all_timestamps) and all(created <= datetime.datetime.fromisoformat(t.replace('Z', '+00:00')) <= now for t in all_timestamps)
back = load_accepted_inputs(recorded)
checks['native_serialize_load_bytes_exact'] = serialize_accepted_inputs(back) == recorded.read_bytes()
report = {'candidate_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(), 'recorded_sha256': hashlib.sha256(recorded.read_bytes()).hexdigest(), 'recorded_bytes': recorded.stat().st_size, 'binding': b['release_binding'], 'recording_timestamps': sorted(all_timestamps), 'checks': checks, 'approval_changes': changes}
(DEST / 'codex-recorded-payload-review.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
