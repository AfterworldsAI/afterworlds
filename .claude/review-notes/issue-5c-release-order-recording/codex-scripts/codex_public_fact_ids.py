"""Verify short-hex oracle values by their native fact-key constructor."""
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEST = ROOT / '.claude/review-notes/issue-5c-release-order-recording'
sys.path.insert(0, str(ROOT / 'src'))
from afterworlds.ingestion.mechanical.oracle import load_accepted_inputs
from afterworlds.ingestion.mechanical.representation import fact_key

files = ['.claude/review-notes/issue-5c-release-order-recording/accepted-candidate.json',
         '.claude/review-notes/issue-5c-release-order-recording/prior-live-oracle.json',
         'src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b.json']
reports = []
for name in files:
    path = ROOT / name
    inputs = load_accepted_inputs(path)
    native = {fact_key(fact) for c in inputs.oracle.representation.components
              for facts in [c.facts, *(o.facts for o in c.options)] for fact in facts}
    values = set()
    fields = collections.Counter()
    def walk(value, field=''):
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, key)
        elif isinstance(value, list):
            for item in value:
                walk(item, field)
        elif isinstance(value, str) and re.fullmatch('[0-9a-f]{16}', value):
            values.add(value)
            fields[field] += 1
    raw = path.read_bytes()
    walk(json.loads(raw))
    assert set(fields) == {'fact_key', 'target_key'}, fields
    assert values <= native, (name, len(values - native))
    reports.append({'path': name, 'sha256': hashlib.sha256(raw).hexdigest(),
        'native_fact_keys': len(native), 'short_identifiers': len(values),
        'fields': dict(fields), 'every_short_value_matches_native_fact_key': True})
out = DEST / 'codex-public-fact-ids.json'
assert not out.exists()
out.write_text(json.dumps({'constructor': 'fact_key: SHA-256(canonical fact_payload)[:16]',
    'scope': 'Read-only identifier classification; no detector settings changed',
    'artifacts': reports}, indent=2) + '\n', encoding='utf-8')
print(json.dumps(reports, indent=2))
