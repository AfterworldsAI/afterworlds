"""Insert the schema-19 contract into the representation, lift and projection
modules at exact anchors (each asserted unique). Run once on a clean tree;
the resulting src diff is the reviewable change.

Usage: venv/Scripts/python.exe .claude/review-notes/issue-15c-native/schema19/insert.py HASH
HASH is the schema-19 representation hash to pin (``PIN`` for a first pass).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
M = REPO / "src/afterworlds/ingestion/mechanical"
PIN = sys.argv[1]


def read(name: str) -> str:
    return (HERE / name).read_text("utf-8")


def rep(s: str, a: str, b: str) -> str:
    assert s.count(a) == 1, (s.count(a), a[:100])
    return s.replace(a, b)


enums = read("enums.py")
classes = read("classes.py")
rules = read("rules.py")
registry = read("registry.py")
reg_main, reg_inv = registry.split("#: The schema-19 invariant manifest rows", 1)
reg_inv = "#: The schema-19 invariant manifest rows" + reg_inv

fact_classes = re.findall(r"^class (\w+Fact)\(?", classes + rules, re.M)
members = re.findall(r"FactFamily\.([A-Z0-9_]+)", classes + rules)
assert len(members) == len(set(members)) == len(fact_classes), (len(members), len(fact_classes))
enum_names = re.findall(r"^class (\w+)\(StrEnum\):", enums, re.M)

# ---------------------------------------------------------------- representation
P = M / "representation.py"
s = P.read_text("utf-8")

s = rep(s, "class ScalingBasis(StrEnum):\n", enums + "\n\nclass ScalingBasis(StrEnum):\n")
family_lines = "".join(f'    {m} = "{m.lower()}"\n' for m in members)
s = rep(
    s,
    '    WEAPON_MASTERY = "weapon_mastery"\n',
    '    WEAPON_MASTERY = "weapon_mastery"\n'
    "    #: Schema 19, CRD Issue 15c. The reviewed bounded-d20 source contract:\n"
    "    #: creature attacks, saves, Multiattack and their clause pieces; the rules,\n"
    "    #: weapon, tool and convention facts; and the contributing grants. Each\n"
    "    #: states what the source prints; execution, applicability and\n"
    "    #: certification are capability, never this union.\n" + family_lines,
)
s = rep(
    s,
    "@dataclass(frozen=True)\nclass EffectTerminationFact:",
    classes + "\n\n" + rules + "\n\n@dataclass(frozen=True)\nclass EffectTerminationFact:",
)
s = rep(
    s,
    "    | WeaponCategoryFact\n    | WeaponMasteryFact\n)\n",
    "    | WeaponCategoryFact\n    | WeaponMasteryFact\n"
    + "".join(f"    | {c}\n" for c in fact_classes)
    + ")\n",
)
s = rep(
    s,
    "#: Every family must declare a builder and an invariant checker.",
    reg_main
    + "\n_FACT_TYPES.update({cast(FactFamily, cls.FAMILY): cls for cls in _SCHEMA_19_FACT_CLASSES})\n"
    "_FACT_BUILDERS.update(\n"
    "    {cast(FactFamily, cls.FAMILY): _build_declared(cls) for cls in _SCHEMA_19_FACT_CLASSES}\n"
    ")\n"
    "_FACT_INVARIANTS.update(\n"
    "    {cast(FactFamily, cls.FAMILY): _check_declared for cls in _SCHEMA_19_FACT_CLASSES}\n"
    ")\n\n"
    "#: Every family must declare a builder and an invariant checker.",
)

# WeaponPropertyFact: four omit-when-empty fields, introduced in 19.
s = rep(
    s,
    "    weapon_property: WeaponProperty\n"
    "    versatile_damage: DiceExpression | None = None\n"
    "    thrown_range_normal_feet: int | None = None\n"
    "    thrown_range_long_feet: int | None = None\n",
    "    weapon_property: WeaponProperty\n"
    "    versatile_damage: DiceExpression | None = None\n"
    "    thrown_range_normal_feet: int | None = None\n"
    "    thrown_range_long_feet: int | None = None\n"
    "    #: Schema 19, omitted when unset. The ammunition an Ammunition weapon's\n"
    "    #: row names, and its normal and long range, stated together and only\n"
    "    #: for :attr:`WeaponProperty.AMMUNITION`.\n"
    "    ammunition: AmmunitionKind | None = None\n"
    "    ammunition_range_normal_feet: int | None = None\n"
    "    ammunition_range_long_feet: int | None = None\n"
    "    #: Schema 19, omitted when unset. The Lance's *\"unless mounted\"*, only\n"
    "    #: for :attr:`WeaponProperty.TWO_HANDED`.\n"
    "    unless: TwoHandedException | None = None\n",
)
s = rep(
    s,
    '        if value is not None and value < 1:\n'
    '            findings.append(f"{name} {value} is not a distance")\n'
    "    return findings\n\n\ndef _check_action_allowance(",
    '        if value is not None and value < 1:\n'
    '            findings.append(f"{name} {value} is not a distance")\n'
    "    return [*findings, *_check_weapon_property_19(fact)]\n\n\n"
    "def _check_weapon_property_19(fact: WeaponPropertyFact) -> list[str]:\n"
    '    """The schema-19 fields: ammunition and its range together, exactly for\n'
    '    the ammunition property; ``unless`` only for two-handed."""\n'
    "    findings = [\n"
    '        *_optional_enum_field(fact.ammunition, AmmunitionKind, "ammunition"),\n'
    "        *_optional_int_field(\n"
    '            fact.ammunition_range_normal_feet, "ammunition_range_normal_feet"\n'
    "        ),\n"
    '        *_optional_int_field(fact.ammunition_range_long_feet, "ammunition_range_long_feet"),\n'
    '        *_optional_enum_field(fact.unless, TwoHandedException, "unless"),\n'
    "    ]\n"
    "    if findings:\n"
    "        return findings\n"
    "    ammunition = (\n"
    "        fact.ammunition,\n"
    "        fact.ammunition_range_normal_feet,\n"
    "        fact.ammunition_range_long_feet,\n"
    "    )\n"
    "    if fact.weapon_property is WeaponProperty.AMMUNITION:\n"
    "        if any(v is None for v in ammunition):\n"
    '            findings.append("ammunition property without its ammunition and range")\n'
    "    elif any(v is not None for v in ammunition):\n"
    "        findings.append(\n"
    '            f"{fact.weapon_property.value} property carries ammunition or its range"\n'
    "        )\n"
    "    for name, value in (\n"
    '        ("ammunition_range_normal_feet", fact.ammunition_range_normal_feet),\n'
    '        ("ammunition_range_long_feet", fact.ammunition_range_long_feet),\n'
    "    ):\n"
    "        if value is not None and value < 1:\n"
    '            findings.append(f"{name} {value} is not a distance")\n'
    "    if fact.unless is not None and fact.weapon_property is not WeaponProperty.TWO_HANDED:\n"
    '        findings.append(f"{fact.weapon_property.value} property carries an exception")\n'
    "    return findings\n\n\ndef _check_action_allowance(",
)
s = rep(
    s,
    "        thrown_range_normal_feet=p[\"thrown_range_normal_feet\"],\n"
    "        thrown_range_long_feet=p[\"thrown_range_long_feet\"],\n"
    "    )\n",
    "        thrown_range_normal_feet=p[\"thrown_range_normal_feet\"],\n"
    "        thrown_range_long_feet=p[\"thrown_range_long_feet\"],\n"
    "        ammunition=cast(\n"
    "            AmmunitionKind | None,\n"
    '            _declared_from_json(AmmunitionKind | None, p.get("ammunition"), "ammunition"),\n'
    "        ),\n"
    "        ammunition_range_normal_feet=cast(\n"
    "            int | None,\n"
    "            _declared_from_json(\n"
    '                int | None,\n'
    '                p.get("ammunition_range_normal_feet"),\n'
    '                "ammunition_range_normal_feet",\n'
    "            ),\n"
    "        ),\n"
    "        ammunition_range_long_feet=cast(\n"
    "            int | None,\n"
    "            _declared_from_json(\n"
    '                int | None, p.get("ammunition_range_long_feet"), "ammunition_range_long_feet"\n'
    "            ),\n"
    "        ),\n"
    "        unless=cast(\n"
    "            TwoHandedException | None,\n"
    '            _declared_from_json(TwoHandedException | None, p.get("unless"), "unless"),\n'
    "        ),\n"
    "    )\n",
)

# Version.
s = rep(
    s,
    'REPRESENTATION_SCHEMA_VERSION = "5d-representation-schema-18"\n',
    "#:\n"
    "#: Version ``19`` admits the CRD Issue 15c bounded-d20 source contract:\n"
    f"#: {len(fact_classes)} fact families and the {len(enum_names)} vocabularies minted with them\n"
    "#: (creature attacks, saves, Multiattack, usage, contributors and clause\n"
    "#: pieces; rule, weapon, tool and notation facts; contributing grants), and\n"
    "#: four omit-when-empty fields on :class:`WeaponPropertyFact`. No accepted\n"
    "#: component states any of them and no accepted field changes meaning, so\n"
    "#: every accepted fact key and provenance coordinate has the same canonical\n"
    "#: form under 18 and 19.\n"
    'REPRESENTATION_SCHEMA_VERSION = "5d-representation-schema-19"\n',
)
s = rep(
    s,
    "#: The seven families schema 11 admitted, for batch ``speed-1``.",
    'SCHEMA_19 = "5d-representation-schema-19"\n\n'
    "#: The families schema 19 admitted, CRD Issue 15c.\n"
    "_SCHEMA_19_FAMILIES: tuple[FactFamily, ...] = tuple(\n"
    "    cast(FactFamily, cls.FAMILY) for cls in _SCHEMA_19_FACT_CLASSES\n"
    ")\n\n"
    "#: The vocabularies minted with them, each wholly new.\n"
    "_SCHEMA_19_VOCABULARIES: tuple[type[StrEnum], ...] = (\n"
    + "".join(f"    {e},\n" for e in enum_names)
    + ")\n"
    "_SCHEMA_19_VOCABULARY_MEMBERS: dict[str, tuple[str, ...]] = {\n"
    "    vocabulary.__name__: tuple(sorted(m.value for m in vocabulary))\n"
    "    for vocabulary in _SCHEMA_19_VOCABULARIES\n"
    "}\n\n"
    "_SCHEMA_19_MEMBER_INDEX: frozenset[tuple[str, str]] = frozenset(\n"
    "    (vocabulary, member)\n"
    "    for vocabulary, members in _SCHEMA_19_VOCABULARY_MEMBERS.items()\n"
    "    for member in members\n"
    ")\n\n"
    "#: The seven families schema 11 admitted, for batch ``speed-1``.",
)
s = rep(
    s,
    "    rows.extend(\n"
    '        _Introduction("nullable_field", _OPTIONAL_SINCE_WIRE_NAMES[owner], key, arrived)\n',
    "    # Schema 19 adds its families and the vocabularies minted with them; its\n"
    "    # four WeaponPropertyFact fields are gated by the field registry.\n"
    "    rows.extend(\n"
    '        _Introduction("fact_family", "FactFamily", family.value, SCHEMA_19)\n'
    "        for family in _SCHEMA_19_FAMILIES\n"
    "    )\n"
    "    for vocabulary, members in _SCHEMA_19_VOCABULARY_MEMBERS.items():\n"
    "        rows.extend(\n"
    '            _Introduction("vocabulary_member", vocabulary, member, SCHEMA_19)\n'
    "            for member in members\n"
    "        )\n"
    "    rows.extend(\n"
    '        _Introduction("nullable_field", _OPTIONAL_SINCE_WIRE_NAMES[owner], key, arrived)\n',
)
s = rep(
    s,
    "        or _SCHEMA_18_VOCABULARY_MEMBERS.get(owner)\n    )\n",
    "        or _SCHEMA_18_VOCABULARY_MEMBERS.get(owner)\n"
    "        or _SCHEMA_19_VOCABULARY_MEMBERS.get(owner)\n    )\n",
)
s = rep(
    s,
    "            (_SCHEMA_18_MEMBER_INDEX, SCHEMA_18),\n        ):",
    "            (_SCHEMA_18_MEMBER_INDEX, SCHEMA_18),\n"
    "            (_SCHEMA_19_MEMBER_INDEX, SCHEMA_19),\n        ):",
)
s = rep(
    s,
    "    (_SCHEMA_18_FAMILIES, SCHEMA_18),\n)\n",
    "    (_SCHEMA_18_FAMILIES, SCHEMA_18),\n    (_SCHEMA_19_FAMILIES, SCHEMA_19),\n)\n",
)
earlier = "".join(f"            SCHEMA_{n},\n" for n in range(5, 19))
s = rep(
    s,
    "            SCHEMA_17,\n            SCHEMA_18,\n        }\n    ),\n}\n",
    "            SCHEMA_17,\n            SCHEMA_18,\n        }\n    ),\n"
    "    SCHEMA_19: frozenset(\n        {\n"
    '            "5d-representation-schema-4",\n'
    + earlier
    + "            SCHEMA_19,\n        }\n    ),\n}\n",
)
s = rep(
    s,
    "_register_post_schema_3(\n"
    "    # Schema 17. A destination component",
    "_register_post_schema_3(\n"
    "    # Schema 19. WeaponPropertyFact's ammunition, ammunition range and\n"
    "    # two-handed exception, omitted when unset, so every accepted weapon\n"
    "    # property keeps its canonical payload and fact key.\n"
    "    *(\n"
    "        _PostSchema3Field(\n"
    '            owner="WeaponPropertyFact",\n'
    "            key=key,\n"
    "            introduced_in=SCHEMA_19,\n"
    "            is_empty=lambda v: v is None,\n"
    "        )\n"
    "        for key in (\n"
    '            "ammunition",\n'
    '            "ammunition_range_normal_feet",\n'
    '            "ammunition_range_long_feet",\n'
    '            "unless",\n'
    "        )\n"
    "    )\n"
    ")\n\n"
    "_register_post_schema_3(\n"
    "    # Schema 17. A destination component",
)
s = rep(s, "_INVARIANTS: tuple[_Invariant, ...] = (\n", reg_inv + "\n\n_INVARIANTS: tuple[_Invariant, ...] = (\n")
s = rep(
    s,
    '            "terminators would resolve nothing"\n'
    "        ),\n"
    "    ),\n"
    "    _Invariant(\n"
    '        id="movement_depletion.until.no-repeats",',
    '            "terminators would resolve nothing"\n'
    "        ),\n"
    "    ),\n"
    "    _Invariant(\n"
    '        id="movement_depletion.until.no-repeats",',
)
s = rep(
    s,
    '            "sorted, so this is checked without imposing an order the "\n'
    '            "source does not state"\n'
    "        ),\n"
    "    ),\n"
    ")\n",
    '            "sorted, so this is checked without imposing an order the "\n'
    '            "source does not state"\n'
    "        ),\n"
    "    ),\n"
    "    *_SCHEMA_19_INVARIANTS,\n"
    ")\n",
)
# The schema-19 value objects join the closed declared structures, so the
# serializer narrows, and the structural and version-legality walkers descend
# into, a nested ``DamageTerm`` exactly as they do a nested ``RollSpec``.
value_objects = [
    c for c in re.findall(r"^class (\w+)\b", classes, re.M)
    if not c.endswith("Fact") and not c.startswith("_")
]
s = rep(
    s,
    "        SpellRange,\n    }\n)\n\n\n#: Applicability fields whose emptiness",
    "        SpellRange,\n    }\n)\n\n"
    "#: Schema 19's nested value objects (CRD Issue 15c), closed like the shared\n"
    "#: ones above.\n"
    "_CLOSED_TYPES |= frozenset(\n    {\n"
    + "".join(f"        {c},\n" for c in value_objects)
    + "    }\n)\n\n\n#: Applicability fields whose emptiness",
)
P.write_text(s, "utf-8", newline="\n")

# ---------------------------------------------------------------- schema_lift
P = M / "schema_lift.py"
s = P.read_text("utf-8")
s = rep(s, '    "SCHEMA_18_VERSION",\n', '    "SCHEMA_18_VERSION",\n    "SCHEMA_19_HASH",\n    "SCHEMA_19_VERSION",\n')
s = rep(
    s,
    'SCHEMA_18_HASH = "276c3d0ca0bf4c2f98aa8e7d2db6cd321d7fb55dee6d8c60fdd4a58e51fa8701"  # noqa: E501  # pragma: allowlist secret\n',
    'SCHEMA_18_HASH = "276c3d0ca0bf4c2f98aa8e7d2db6cd321d7fb55dee6d8c60fdd4a58e51fa8701"  # noqa: E501  # pragma: allowlist secret\n'
    'SCHEMA_19_VERSION = "5d-representation-schema-19"\n'
    f'SCHEMA_19_HASH = "{PIN}"  # noqa: E501  # pragma: allowlist secret\n',
)
s = rep(
    s,
    '            "The policy contract does not move with it."\n'
    "        ),\n"
    "    ),\n"
    "}\n",
    '            "The policy contract does not move with it."\n'
    "        ),\n"
    "    ),\n"
    "    (SCHEMA_18_VERSION, SCHEMA_18_HASH): SchemaLift(\n"
    '        lift_id="5d-lift-schema-18-to-19",\n'
    "        from_version=SCHEMA_18_VERSION,\n"
    "        from_hash=SCHEMA_18_HASH,\n"
    "        to_version=SCHEMA_19_VERSION,\n"
    "        to_hash=SCHEMA_19_HASH,\n"
    "        rationale=(\n"
    '            "Schema 19 admits the CRD Issue 15c bounded-d20 source contract the "\n'
    '            "independent raw review cleared (candidate C5): creature attack, "\n'
    '            "save-effect, Multiattack, usage, contributor and clause-piece "\n'
    '            "families; rule, weapon, tool and stat-block notation families; "\n'
    '            "the contributing-grant families; the closed vocabularies minted "\n'
    '            "with them; and four omit-when-empty WeaponPropertyFact fields "\n'
    '            "(ammunition, its normal and long range, and the two-handed "\n'
    '            "exception). Each family states what the source prints and stops "\n'
    '            "there: applicability, execution and certification are capability, "\n'
    '            "never this union. "\n'
    '            "Nothing accepted moves. No accepted component states a fact of "\n'
    '            "any new family, no accepted field changes meaning, and the four "\n'
    '            "new fields are omitted when unset, so every accepted payload -- "\n'
    '            "and its fact key and provenance coordinate -- is byte-identical "\n'
    '            "under both contracts, which verify_lift proves element by element "\n'
    '            "rather than asserting. A schema-18 declaration carrying any new "\n'
    '            "family, vocabulary member or field is refused by the introduction "\n'
    '            "manifest and the field registry, never flattened. "\n'
    '            "The policy contract does not move with it."\n'
    "        ),\n"
    "    ),\n"
    "}\n",
)
P.write_text(s, "utf-8", newline="\n")

# ---------------------------------------------------------------- projection
P = M / "projection.py"
s = P.read_text("utf-8")
s = rep(s, '    "SCHEMA_18_VERSION",\n', '    "SCHEMA_18_VERSION",\n    "SCHEMA_19_VERSION",\n')
s = rep(
    s,
    'SCHEMA_18_VERSION = "5d-representation-schema-18"\n',
    'SCHEMA_18_VERSION = "5d-representation-schema-18"\nSCHEMA_19_VERSION = "5d-representation-schema-19"\n',
)
s = rep(
    s,
    "    SCHEMA_18_VERSION: frozenset(\n"
    "        {\n"
    '            "applies_when",\n'
    '            "options",\n'
    '            "fact_qualifiers",\n'
    '            "recurs",\n'
    '            "prose_retention_reason_code",\n'
    "        }\n"
    "    ),\n"
    "}\n",
    "    SCHEMA_18_VERSION: frozenset(\n"
    "        {\n"
    '            "applies_when",\n'
    '            "options",\n'
    '            "fact_qualifiers",\n'
    '            "recurs",\n'
    '            "prose_retention_reason_code",\n'
    "        }\n"
    "    ),\n"
    "    # Schema 19 adds fact families and four omit-when-empty fact fields and\n"
    "    # no component key, so its row repeats schema 18's.\n"
    "    SCHEMA_19_VERSION: frozenset(\n"
    "        {\n"
    '            "applies_when",\n'
    '            "options",\n'
    '            "fact_qualifiers",\n'
    '            "recurs",\n'
    '            "prose_retention_reason_code",\n'
    "        }\n"
    "    ),\n"
    "}\n",
)
n = s.count("        SCHEMA_18_VERSION,\n    }\n)\n")
assert n == 3, n
s = s.replace("        SCHEMA_18_VERSION,\n    }\n)\n", "        SCHEMA_18_VERSION,\n        SCHEMA_19_VERSION,\n    }\n)\n")
s = rep(
    s,
    "    {SCHEMA_17_VERSION, SCHEMA_18_VERSION}\n",
    "    {SCHEMA_17_VERSION, SCHEMA_18_VERSION, SCHEMA_19_VERSION}\n",
)
P.write_text(s, "utf-8", newline="\n")
print("inserted", len(fact_classes), "families,", len(enum_names), "vocabularies")
