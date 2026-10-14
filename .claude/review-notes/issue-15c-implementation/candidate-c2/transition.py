"""Which accepted batches C2 would touch if minted (REVIEW MATERIAL, read only).

Maps every record C2 places a fact on to the accepted batches whose spans that
record's components are bound to, via the accepted oracle's own provenance.
Writes ``transition.json``.
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

REPO = Path.cwd()
HERE = Path(__file__).parent
ORACLE = REPO / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-g1.json"


def main() -> None:
    d = json.loads(ORACLE.read_bytes())
    span_batch = {r["span_id"]: r["batch_id"] for r in d["acceptance"]["records"]}
    record_batches: dict[str, set[str]] = collections.defaultdict(set)
    for b in d["representation"]["prose_bindings"]:
        if b["span_id"] in span_batch:
            record_batches[b["record_key"]].add(span_batch[b["span_id"]])
    touched: dict[str, set[str]] = collections.defaultdict(set)
    for part, key in (("c2a.json", "facts"), ("c2c.json", "facts"), ("c2b.json", "creatures")):
        for f in json.loads((HERE / part).read_text("utf-8"))[key]:
            for batch in record_batches.get(f["record_key"], {"<unbound>"}):
                touched[batch].add(part)
    out = {"batches": {b: sorted(p) for b, p in sorted(touched.items())},
           "batch_count": len(touched),
           "all_batches": sorted({b["batch_id"] for b in d["acceptance"]["batches"]})}
    (HERE / "transition.json").write_text(json.dumps(out, indent=1) + "\n", "utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
