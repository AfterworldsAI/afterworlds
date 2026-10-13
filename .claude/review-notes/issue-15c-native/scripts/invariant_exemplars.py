"""Focused exemplars for the explicit schema-19 invariant rows.

The manifest's ``test_schema_4_invariant_closure`` contract, applied to the
rows schema 19 declares: every explicit row is refused by a violating exemplar
and admitted by a real mapped C5 fact. The integer-domain and nested
value-object rows are exercised field by field in ``scalar_diagnostics.py``.
Exemplars are built from real mapped facts (the first one carrying the row's
locus), so no row is witnessed by an invented value.
FOCUSED DIAGNOSTICS ONLY. Writes ../reports/invariant-exemplars.json.
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Iterator
from typing import Any

import common as c
import native_map as m

from afterworlds.ingestion.mechanical import representation as R

Path = tuple[Any, ...]


def findings(fact: Any) -> list[str]:
    return list(R._FACT_INVARIANTS[R.FactFamily(fact.FAMILY.value)](fact))


def nodes(obj: Any, path: Path = ()) -> Iterator[tuple[Path, Any]]:
    if dataclasses.is_dataclass(obj):
        yield path, obj
        for f in dataclasses.fields(obj):
            yield from nodes(getattr(obj, f.name), (*path, f.name))
    elif isinstance(obj, tuple):
        for i, x in enumerate(obj):
            yield from nodes(x, (*path, i))


def replace_at(obj: Any, path: Path, value: Any) -> Any:
    if not path:
        return value
    head, *rest = path
    if isinstance(obj, tuple):
        items = list(obj)
        items[head] = replace_at(items[head], tuple(rest), value)
        return tuple(items)
    return dataclasses.replace(obj, **{head: replace_at(getattr(obj, head), tuple(rest), value)})


def matches(locus: str, node: Any, path: Path) -> bool:
    kind, _, name = locus.partition(":")
    if kind == "fact":
        return not path and node.FAMILY.value == name
    return bool(path) and kind == "shape" and "+".join(
        sorted(f.name for f in dataclasses.fields(node))) == name


def empty(value: Any) -> Any:
    return () if isinstance(value, tuple) else (False if isinstance(value, bool) else None)


def stated(value: Any) -> bool:
    return value not in (None, (), False)


FACTS = [R.fact_from_payload(p) for _, _, p, _ in m.items()]


def sites(locus: str) -> Iterator[tuple[Any, Path, Any]]:
    for fact in FACTS:
        for path, node in nodes(fact):
            if matches(locus, node, path):
                yield fact, path, node


def two_stated(row: Any, fields: list[str], fact: Any, path: Path, node: Any
               ) -> tuple[Any, str] | None:
    """*node* with a second of *fields* stated, taken from another real site."""
    have = [f for f in fields if stated(getattr(node, f))]
    if len(have) != 1:
        return None
    for _, _, donor in sites(row.locus):
        missing = [f for f in fields if f not in have and stated(getattr(donor, f))]
        if missing:
            bad = dataclasses.replace(node, **{missing[0]: getattr(donor, missing[0])})
            return replace_at(fact, path, bad), f"{have[0]} and {missing[0]} both"
    return None


def exemplar(row: Any) -> tuple[list[tuple[Any, str]], Any]:
    """(violations with how, admitted control) for one explicit row. An
    exactly-one row is witnessed both ways where the data has a donor: none
    stated, and two stated."""
    fields = row.field.split("+")
    kind = row.id.rsplit(".", 1)[-1]
    for fact, path, node in sites(row.locus):
        if findings(fact):
            continue
        if kind.endswith("-only"):  # weapon_property: a field off its property
            if stated(getattr(node, fields[0])):
                other = next(p for p in R.WeaponProperty if p != node.weapon_property)
                return [(dataclasses.replace(fact, weapon_property=other),
                         f"{row.field} kept with weapon_property={other.value}")], fact
            continue
        two = two_stated(row, fields, fact, path, node)
        if kind == "at-most-one" or row.rule.endswith("never both"):
            if two:
                return [two], fact
            continue
        none = dataclasses.replace(node, **{f: empty(getattr(node, f)) for f in fields})
        return [(replace_at(fact, path, none), f"none of {row.field}"),
                *([two] if two else [])], fact
    raise AssertionError(f"no exemplar site for {row.id}")


def main() -> None:
    rows = [r for r in R._SCHEMA_19_INVARIANTS if r.locus.split(":")[0] != "fields"]
    report, failures = {}, []
    for row in rows:
        bads, good = exemplar(row)
        refused = [bool(findings(bad)) for bad, _ in bads]
        admitted = findings(good)
        report[row.id] = {"violation": [how for _, how in bads], "refused": refused,
                          "control_admitted": not admitted}
        if not all(refused) or admitted:
            failures.append(row.id)
    out = {"label": "FOCUSED DIAGNOSTICS ONLY", "explicit_rows": len(rows), "rows": report,
           "failures": failures}
    (c.NATIVE / "reports" / "invariant-exemplars.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps({k: (v if k != "rows" else {i: r["violation"] for i, r in v.items()})
                      for k, v in out.items()}, indent=1))
    assert not failures, failures


if __name__ == "__main__":
    main()
