"""Re-baseline ONE file, in place, without touching any other entry.

``detect-secrets scan --baseline`` rewrites the whole baseline; this rescans the
accepted-authority artifact alone, replaces that file's results block, and
asserts every other file's block and every setting is byte-identical afterwards.
"""

import json
import pathlib
import sys

from detect_secrets.core import baseline

BASELINE = pathlib.Path(".secrets.baseline")
TARGET = "src\\afterworlds\\ingestion\\mechanical\\oracles\\srd-5-2-1-corpus-36b786d8-fa2.json"

before = json.loads(BASELINE.read_text(encoding="utf-8"))

secrets = baseline.load(baseline.load_from_file(str(BASELINE)), str(BASELINE))
secrets.data.pop(TARGET, None)
secrets.scan_file(TARGET.replace("\\", "/"))

after = baseline.format_for_output(secrets)

# Nothing but the one file's block (and the timestamp) may move.
assert set(after["results"]) == set(before["results"]), sorted(
    set(after["results"]) ^ set(before["results"])
)
for key in ("filters_used", "plugins_used", "version"):
    assert after[key] == before[key], key
for name, block in before["results"].items():
    if name != TARGET:
        assert after["results"][name] == block, name

print(f"{TARGET}: {len(before['results'][TARGET])} -> {len(after['results'][TARGET])}")
if "--write" not in sys.argv:
    print("dry run; pass --write to save")
    raise SystemExit(0)

baseline.save_to_file(after, str(BASELINE))
print("written")
