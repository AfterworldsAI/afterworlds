"""Focused schema-19 scalar diagnostics (Codex native scalar review).

For every integer field that some mapped C5 fact states, the fact with that
field at its declared least value is admitted, one below it is refused (unless
the field is signed, where a negative is admitted), and a boolean is refused.
Nested accepted value objects: zero dice and a zero denominator are refused.
FOCUSED DIAGNOSTICS ONLY -- not acceptance or full-suite evidence.
Writes ../reports/scalar-diagnostics.json.
"""

from __future__ import annotations

import dataclasses
import json
import typing
from typing import Any

import common as c
import native_map as m

from afterworlds.ingestion.mechanical import representation as R


def findings(fact: Any) -> list[str]:
    return list(R._FACT_INVARIANTS[R.FactFamily(fact.FAMILY.value)](fact))


def paths(obj: Any, prefix: tuple[Any, ...] = ()) -> typing.Iterator[tuple[tuple[Any, ...], type, str]]:
    """(path, owner class, field) for every integer-valued field in *obj*."""
    if not dataclasses.is_dataclass(obj):
        return
    hints = typing.get_type_hints(type(obj))
    for f in dataclasses.fields(obj):
        v = getattr(obj, f.name)
        if R._int_leaves(hints[f.name]) and isinstance(v, int) and not isinstance(v, bool):
            yield (*prefix, f.name), type(obj), f.name
        elif dataclasses.is_dataclass(v) and type(v) not in (R.DiceExpression, R.Rational) \
                and not isinstance(getattr(v, "FAMILY", None), R.FactFamily):
            yield from paths(v, (*prefix, f.name))
        elif isinstance(v, tuple):
            for i, x in enumerate(v):
                if dataclasses.is_dataclass(x) and not isinstance(getattr(x, "FAMILY", None),
                                                                  R.FactFamily):
                    yield from paths(x, (*prefix, f.name, i))


def replace_at(obj: Any, path: tuple[Any, ...], value: Any) -> Any:
    head, *rest = path
    if isinstance(obj, tuple):
        items = list(obj)
        items[head] = replace_at(items[head], tuple(rest), value) if rest else value
        return tuple(items)
    cur = getattr(obj, head)
    return dataclasses.replace(obj, **{head: replace_at(cur, tuple(rest), value) if rest else value})


def main() -> None:
    covered: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for rk, ck, payload, _ in m.items():
        fact = R.fact_from_payload(payload)
        if type(fact).__name__ not in {cls.__name__ for cls in R._SCHEMA_19_FACT_CLASSES}:
            continue
        for path, owner, name in paths(fact):
            key = f"{owner.__name__}.{name}"
            if key in covered:
                continue
            domain = R._domain_of(owner, name)
            least = -5 if domain == R.SIGNED else int(domain)
            row = {"family": payload["family"], "path": list(path), "domain": domain}
            if findings(replace_at(fact, path, least)):
                failures.append(f"{key}: least value {least} refused")
            if domain != R.SIGNED and not findings(replace_at(fact, path, least - 1)):
                failures.append(f"{key}: {least - 1} admitted below its domain")
            if not findings(replace_at(fact, path, True)):
                failures.append(f"{key}: a boolean admitted as an integer")
            covered[key] = row
    # Nested accepted value objects.
    term = R.DamageTerm(average=4, dice=R.DiceExpression(count=0, die=R.DieSize.D6, modifier=1),
                        constant=None, addends=(), damage_type=R.DamageType.FIRE,
                        damage_type_by_choice=None)
    attack = next(R.fact_from_payload(p) for _, _, p, _ in m.items()
                  if p["family"] == "creature_attack" and p["hit_damage"])
    zero_dice = dataclasses.replace(attack, hit_damage=(term,))
    neg_mod = dataclasses.replace(attack, hit_damage=(dataclasses.replace(
        term, dice=R.DiceExpression(count=1, die=R.DieSize.D6, modifier=-1)),))
    ammo = next(R.fact_from_payload(p) for _, _, p, _ in m.items()
                if p["family"] == "ammunition_expenditure")
    zero_den = dataclasses.replace(ammo, recovery=dataclasses.replace(
        ammo.recovery, fraction=R.Rational(numerator=1, denominator=0)))
    nested = {"zero dice refused": bool(findings(zero_dice)),
              "signed dice modifier admitted": not findings(neg_mod),
              "zero denominator refused": bool(findings(zero_den))}
    failures += [k for k, ok in nested.items() if not ok]
    report = {"label": "FOCUSED DIAGNOSTICS ONLY", "integer_fields_exercised": len(covered),
              "fields": covered, "nested_value_objects": nested, "failures": failures}
    (c.NATIVE / "reports" / "scalar-diagnostics.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "fields"}, indent=1))
    assert not failures, failures


if __name__ == "__main__":
    main()
