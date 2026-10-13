"""Generate ``tests/ingestion/mechanical/data/schema_19_exemplars.json``.

Real accepted facts from the recorded CRD Issue 15c successor, chosen greedily
so that together they exercise every schema-19 introduction row (each of the
126 families and each of the 318 vocabulary members), read the way
``test_schema_version_legality`` reads them: from the findings a schema-3
build reports for the object. Deterministic: candidates are taken in the
oracle's component order. Run from the repository root.
"""

from __future__ import annotations

import dataclasses
import json
import typing
from enum import StrEnum
from pathlib import Path

from afterworlds.ingestion.mechanical.oracle import COMMITTED_ORACLE_DIR, load_accepted_inputs
from afterworlds.ingestion.mechanical.representation import (
    fact_from_payload,
    fact_payload,
    introduction_manifest,
    post_schema_3_violations,
)
from afterworlds.ingestion.mechanical.schema_lift import SCHEMA_3_VERSION, SCHEMA_18_VERSION, SCHEMA_19_VERSION

OUT = Path("tests/ingestion/mechanical/data/schema_19_exemplars.json")
SUCCESSOR = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-15c.json"

rows = [r for r in introduction_manifest() if r["introduced_in"] == SCHEMA_19_VERSION]
keys = {(r["kind"], repr(r["vocabulary"]), r["name"]) for r in rows}


def exercised(fact: object) -> set[tuple[str, str, str]]:
    found = post_schema_3_violations(fact, SCHEMA_3_VERSION)
    return {(r["kind"], repr(r["vocabulary"]), r["name"]) for r in rows
            if any(repr(r["name"]) in f for f in found)}


inputs = load_accepted_inputs(SUCCESSOR)
seen: set[str] = set()
candidates = []
for comp in inputs.oracle.representation.components:
    for fact in (*comp.facts, *(f for o in comp.options for f in o.facts)):
        payload = json.dumps(fact_payload(fact), sort_keys=True)
        if payload in seen:
            continue
        seen.add(payload)
        # Only facts schema 18 refuses: an older fact's findings can name a
        # member by substring without carrying it.
        hit = exercised(fact) if post_schema_3_violations(fact, SCHEMA_18_VERSION) else set()
        if hit:
            candidates.append((payload, hit))

chosen, left = [], set(keys)
while left:
    payload, hit = max(candidates, key=lambda c: len(c[1] & left))
    if not hit & left:
        break
    chosen.append(json.loads(payload))
    left -= hit

# Members the schema admits that no accepted fact states (C5 annotates them on
# prose entries, which are not minted): a real fact of a family with a field of
# that vocabulary, with only that field replaced.
derived = []
for kind, vocabulary, name in sorted(left):
    assert kind == "vocabulary_member", (kind, vocabulary, name)
    for payload, _ in candidates:
        fact = fact_from_payload(json.loads(payload))
        hints = typing.get_type_hints(type(fact))
        field = next((f.name for f in dataclasses.fields(fact)
                      if isinstance(hints[f.name], type) and issubclass(hints[f.name], StrEnum)
                      and sorted(m.value for m in hints[f.name]) == eval(vocabulary)), None)
        if field:
            new = dataclasses.replace(fact, **{field: hints[field](name)})
            assert exercised(new) >= {(kind, vocabulary, name)}
            chosen.append(fact_payload(new))
            derived.append(f"{type(fact).__name__}.{field}={name}")
            left.discard((kind, vocabulary, name))
            break
assert not left, sorted(left)
print("derived", derived)
OUT.write_text(json.dumps(chosen, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print(len(rows), "rows covered by", len(chosen), "facts")
