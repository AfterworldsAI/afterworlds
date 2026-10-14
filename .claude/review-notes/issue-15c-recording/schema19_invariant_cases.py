"""Generate ``tests/ingestion/mechanical/data/schema_19_invariant_cases.json``.

One refused exemplar (or, for exactly-one rows with a donor, two: none stated
and two stated) and one admitted control per schema-19 invariant row, for
``test_schema_4_invariant_closure``. Explicit rows reuse the reviewed
``issue-15c-native/scripts/invariant_exemplars.py`` construction (real mapped
C5 facts, mutated); the integer-domain and nested-value-object rows mutate one
real fact each. Every payload round-trips through ``fact_from_payload``.
Run from the repository root.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0, ".claude/review-notes/issue-15c-native/scripts")
import invariant_exemplars as ie  # noqa: E402

from afterworlds.ingestion.mechanical import representation as R  # noqa: E402

OUT = Path("tests/ingestion/mechanical/data/schema_19_invariant_cases.json")


def first(family: str, pred=lambda f: True):  # type: ignore[no-untyped-def]
    return next(f for f in ie.FACTS if f.FAMILY.value == family and pred(f)
                and not ie.findings(f))


cases = []
for row in R._SCHEMA_19_INVARIANTS:
    if row.locus.split(":")[0] != "fields":
        bads, good = ie.exemplar(row)
        bad_objs = [b for b, _ in bads]
    elif row.id == "nested-value-object.accepted-rules":
        good = first("creature_attack", lambda f: f.hit_damage and f.hit_damage[0].dice)
        term = good.hit_damage[0]
        bad_objs = [dataclasses.replace(good, hit_damage=(dataclasses.replace(
            term, dice=dataclasses.replace(term.dice, count=0)), *good.hit_damage[1:]))]
    elif row.id == "integer-field.domain.1":
        good = first("creature_attack", lambda f: f.reach_ft)
        bad_objs = [dataclasses.replace(good, reach_ft=0)]
    elif row.id == "integer-field.domain.0":
        good = first("clause_condition")
        bad_objs = [dataclasses.replace(good, piece=-1)]
    elif row.id == "integer-field.domain.signed":
        good = first("creature_attack", lambda f: f.attack_bonus is not None)
        bad_objs = [dataclasses.replace(good, attack_bonus=True)]
    else:
        raise AssertionError(row.id)
    assert not ie.findings(good), row.id
    for b in bad_objs:
        assert ie.findings(b), row.id
    entry = {"id": row.id, "good": R.fact_payload(good), "bad": [], "bad_replace": []}
    for b in bad_objs:
        payload = R.fact_payload(b)
        try:
            assert R.fact_from_payload(payload) == b, row.id
            entry["bad"].append(payload)
        except R.MalformedFactPayloadError:
            # A value no payload can carry (a boolean integer): the test
            # applies it to the control with ``dataclasses.replace``.
            changed = {f.name: getattr(b, f.name) for f in dataclasses.fields(b)
                       if getattr(b, f.name) != getattr(good, f.name)
                       or type(getattr(b, f.name)) is not type(getattr(good, f.name))}
            assert dataclasses.replace(good, **changed) == b, row.id
            entry["bad_replace"].append(changed)
    cases.append(entry)
OUT.write_text(json.dumps(cases, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print(len(cases), "rows;", sum(len(c["bad"]) for c in cases), "refused exemplars")
