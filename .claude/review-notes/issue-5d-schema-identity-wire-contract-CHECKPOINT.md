# CRD Issue 5d — representation-schema identity: wire-contract checkpoint

**Status:** design/test-closure checkpoint only. **No code, migration, fixture, or PR-body change was
made.** PR #153 is frozen at `3f8a131f265e41335735bc10e7f330a6595ec3d6`; working tree clean; all Codex
threads left unresolved. Nothing here is implemented.

**Authority:** ADR-005d Decisions 4 and 6; Issue #137's closed-representation contracts; the current
`representation.py` schema-identity implementation; `fact_payload` / `fact_from_payload`;
`projection.representation_payload`; `test_representation_schema_identity.py`.

**Why a checkpoint rather than a fourth patch.** This is the third consecutive finding in the same
mechanism — canonicalization, then ordering, now class-name leakage. The previous pass declared itself the
final bounded remediation of this area. The rule has been corrected twice under fire; correcting it a
third time inside a reactive edit is how a mechanism accumulates rules nobody ever stated whole. What
follows is the whole rule and the whole footprint, for review before any code moves.

---

## 0. The finding, reproduced

`representation_schema_hash()` still depends on Python class names. Verified on the frozen head:

| Rename | Wire effect | Current identity effect |
|---|---|---|
| enum class `RollActor` → `RollActorRenamed` (same members) | none | `_type_name` renders `RollActor` vs `RollActorRenamed` → **hash moves** |
| value object `RollSpec` → `RollSpecification` (same fields) | none | emitted as `value_objects[].name` *and* as every holder's field `type` → **hash moves** |
| fact class `AdvantageFact` → `AdvantageRuleFact` (same family and fields) | none | emitted as `fact_families[].type` → **hash moves** |

Each remints authority for an implementation-only refactor — and, because the pinned canary instructs a
version bump on any hash change, would do so under a bump asserting a contract change that did not happen.
Same failure shape as the declaration-order defect, one level up.

---

## 1. Inventory — every Python identifier reaching the payload

Measured on the frozen head: **25 families, 8 value objects, 33 vocabularies**. These are all the rendered
field shapes present in the union:

```
int (16)   str (3)   bool (10)   None|int (22)
<enum> and <enum>|None             <value-object> and <value-object>|None
tuple[DamageType,...]  (1 — DamageResponseFact.except_types)
```

No dicts, no lists, no nested containers, and no unions other than `X | None`. Maximum nesting depth is 2
(fact → value object → enum).

| # | Identifier reaching the payload | Where | Wire-observable? | Classification |
|---|---|---|---|---|
| 1 | `FactFamily.value` (`"advantage"`) | `fact_families[].family` | **yes** — `fact_payload` emits it as `family`; `fact_from_payload` dispatches on it | **wire-semantic — keep** |
| 2 | fact class name (`AdvantageFact`) | `fact_families[].type` | no — never serialized | **redundant implementation metadata — drop** |
| 3 | fact field name (`roll`, `state`) | `fact_families[].fields[].name` | **yes** — payload keys; rebuild matches and rejects by name | **wire-semantic — keep** |
| 4 | value-object class name (`RollSpec`) | `value_objects[].name` **and** every holder's field `type` | no — a value object serializes as a bare nested object with no type tag | **implementation metadata — replace with the object's structure** |
| 5 | value-object field name (`actor`, `ability`) | `value_objects[].fields[].name` | **yes** — nested payload keys; `_json_object` requires the exact key tuple | **wire-semantic — keep** |
| 6 | enum class name (`RollActor`, `DieSize`) | `vocabularies[].name` **and** every field `type` | no — an enum serializes as a plain string | **implementation metadata — replace with the admitted value set** |
| 7 | enum member values (`"subject"`) | `vocabularies[].members` | **yes** — the admitted strings; `_json_enum` validates against them | **wire-semantic — keep** |
| 8 | `int` / `str` / `bool` | field `type` | **yes** — JSON primitive types | **wire-semantic — keep as neutral shape words** |
| 9 | `None` (from `type(None).__name__`) | field `type`, e.g. `None|int` | meaning **yes** (JSON null admitted); spelling is Python | **wire-semantic property in an implementation spelling — express as a `nullable` flag** |
| 10 | `tuple` container origin | field `type`, `tuple[DamageType,...]` | **partly** — an array is wire-visible, but `tuple` vs `list` is not: `_canonical_value` maps both to a JSON array (verified) | **implementation leakage — express as `array`** |
| 11 | draft vocabulary class names (`RecordKind`, `ComponentHandling`, `RelationshipKind`, `ProvenanceTargetKind`, `ProvenanceRole`) | `vocabularies[].name` | no — each serializes as a plain string at a fixed draft path | **implementation metadata — replace with the stable serialized path** |

Items 2, 4, 6, 10, 11 are the leak. Items 1, 3, 5, 7, 8 are the contract. Item 9 is the contract wearing a
Python spelling.

### 1a. The five draft-only vocabularies, by serialized path

Confirmed against `projection.representation_payload`:

| Enum | Stable serialized path |
|---|---|
| `RecordKind` | `records[].kind` |
| `ComponentHandling` | `components[].handling` |
| `RelationshipKind` | `relationships[].kind` |
| `ProvenanceTargetKind` | `provenance[].target_kind` |
| `ProvenanceRole` | `provenance[].role` |

These are reached from the drafts, not from any fact field, which is why they are named explicitly today
and need an explicit *wire role* rather than simply being dropped.

---

## 2. Proposed canonical wire-schema descriptor

One recursive, name-free shape grammar. Every identifier in it is a wire key, a wire value, or a neutral
shape word.

```
{
  "representation_schema_version": "5d-representation-schema-1",

  "facts": [                                  // sorted by "family"
    { "family": "advantage",                  // FactFamily.value — the wire discriminator
      "fields": [                             // sorted by "name"
        { "name": "roll",  "shape": {"kind": "object", "fields": [
            {"name": "ability", "shape": {"kind": "enum", "nullable": true,
                                          "values": ["charisma", "..."]}},
            {"name": "actor",   "shape": {"kind": "enum",
                                          "values": ["against_subject", "subject"]}},
            {"name": "context", "shape": {"kind": "enum", "values": ["..."]}}
        ]}},
        { "name": "state", "shape": {"kind": "enum",
                                     "values": ["advantage", "disadvantage"]}}
      ]}
  ],

  "draft_vocabularies": [                     // sorted by "path"
    { "path": "components[].handling",    "shape": {"kind": "enum", "values": ["..."]}},
    { "path": "provenance[].role",        "shape": {"kind": "enum", "values": ["..."]}},
    { "path": "provenance[].target_kind", "shape": {"kind": "enum", "values": ["..."]}},
    { "path": "records[].kind",           "shape": {"kind": "enum", "values": ["..."]}},
    { "path": "relationships[].kind",     "shape": {"kind": "enum", "values": ["..."]}}
  ]
}
```

### Shape grammar — closed, covering exactly the observed surface

| Shape | Emitted for | Wire meaning |
|---|---|---|
| `{"kind": "integer"}` | `int` | JSON number |
| `{"kind": "string"}` | `str` | JSON string, unconstrained |
| `{"kind": "boolean"}` | `bool` | JSON boolean |
| `{"kind": "enum", "values": [sorted]}` | any `StrEnum` | JSON string from a closed set |
| `{"kind": "object", "fields": [{name, shape}, ...]}` | any nested value object, **inlined**, fields sorted by name | JSON object with exactly those keys |
| `{"kind": "array", "items": <shape>}` | `tuple[X, ...]` **and** `list[X]` alike | JSON array |
| `"nullable": true` on any shape | `X \| None` | JSON null also admitted |

A shape the grammar does not cover must **raise** rather than render — the same discipline `fact_payload`
already applies to a fact outside the closed union. A silent fallback would reintroduce the leak somewhere
new.

### Deliberately absent

* **No `type` key on families.** The entry *is* keyed by its discriminator; the Python class is not a
  second identity for the same thing.
* **No `value_objects` registry.** Value objects are inlined at each field site, so there is no name to
  reference and no resolution step that could dangle or alias. Cheap here: depth 2, eight distinct
  objects.
* **No enum class names.** A closed vocabulary *is* its admitted value set at the wire.

---

## 3. Trace against serialization and reconstruction

Each descriptor element corresponds to a real decision point, not to a declaration.

**`fact_payload`** emits `{"family": <FactFamily.value>, **fields}`; `_canonical_value` maps `StrEnum` to
its `.value` string, dict to a recursed dict, list/tuple to a JSON array, and passes everything else
through. So family ↔ `facts[].family`, field names ↔ payload keys, enum ↔ string, value object ↔ nested
object, tuple/list ↔ array. Every grammar member has a serialization counterpart.

**`fact_from_payload`** resolves the family from `payload["family"]`, computes the expected key set from
`fields(_FACT_TYPES[family])`, and rejects **missing** and **extra** keys by name — never by position.
Per-family builders rebuild nested value objects through `_json_object(value, (names...), where)` (exact
key tuple) and enums through `_json_enum(value, EnumCls, where)` (membership in the admitted set). That is
the direct justification for keying families by discriminator, keying fields by name, ordering by semantic
key, and describing enums by value set.

**Draft serialization** (`projection.representation_payload`) fixes the five paths in §1a; `canonical_order`
orders those collections, so the paths — not positions — are the stable anchors.

### Unambiguity of nesting

Inlining removes the only ambiguity a registry could introduce: a name reference resolving to the wrong
entry or to none. Each field carries its complete shape, equal shapes are equal descriptors by
construction, and recursion terminates because the grammar's only recursive members are
`object.fields[].shape` and `array.items`, while the union's deepest chain is fact → value object → enum.

### Equivalent Python declarations produce one descriptor

| Change | Descriptor effect |
|---|---|
| rename a fact, value-object, or enum class | **none** — no class name is emitted |
| reorder fields, or enum members | **none** — sorted by name / by value |
| `tuple[X, ...]` ↔ `list[X]` | **none** — both are `array`, and both already serialize to a JSON array |
| `Optional[X]` ↔ `X \| None` | **none** — both are `nullable: true` |
| move a definition, edit a comment or docstring | **none** |

### Accidental collapse — measured, not assumed

Under structural identity, two vocabularies with identical admitted sets, or two value objects with
identical field shapes, would produce one descriptor. Measured on the frozen head:

* vocabularies sharing an admitted-value set: **none**;
* value objects sharing a field shape: **none**;
* families sharing a field shape: **one pair** — `action_economy` and `action_restriction` are both
  `{cost: ActionCost}`. They stay distinct because families are keyed by discriminator. This pair is the
  concrete evidence that the discriminator must remain in the descriptor.

If a future pair of enums or value objects did collide, the collapse would be **wire-correct**: neither
carries a type tag in the payload, so their serialized forms are genuinely indistinguishable, and the
difference would live in builder/validator behaviour — the manual `REPRESENTATION_SCHEMA_VERSION`
obligation's territory, not the structural hash's. §4 (S6) surfaces it rather than leaving it silent.

---

## 4. Behavioral test matrix

Invariance is proved with locally declared doubles whose *names* differ and whose wire contract does not;
sensitivity is proved against the real union where possible.

### Must be invariant

| # | Perturbation | Assertion |
|---|---|---|
| I1 | fact class renamed; family and fields identical | descriptor and hash unchanged |
| I2 | value-object class renamed; fields identical | descriptor and hash unchanged |
| I3 | enum class renamed; members identical | descriptor and hash unchanged |
| I4 | field declaration order permuted | unchanged (existing coverage, retained) |
| I5 | enum member declaration order permuted | unchanged (existing coverage, retained) |
| I6 | `tuple[X, ...]` declared as `list[X]` | unchanged — paired with an assertion that `_canonical_value` maps both to the same JSON array, so the claim is grounded rather than asserted |
| I7 | `Optional[X]` vs `X \| None` | unchanged |
| I8 | docstring/comment-only edit to `representation.py` | hash unchanged |

### Must move identity

| # | Perturbation | Assertion |
|---|---|---|
| M1 | family discriminator value changed | descriptor differs |
| M2 | field added or removed | differs |
| M3 | field renamed | differs |
| M4 | field retyped (`int` → `str`) | differs |
| M5 | nullability added or removed | differs |
| M6 | scalar ↔ array | differs |
| M7 | **nested** value-object field added, renamed, or retyped | differs — the case a name-only reference would have hidden |
| M8 | vocabulary value added, removed, or renamed | differs |
| M9 | a draft vocabulary's admitted values changed | differs |
| M10 | a draft vocabulary's serialized **path** changed | differs |

### Structural integrity

| # | Assertion |
|---|---|
| S1 | every collection canonically ordered — facts by family, fields by name, enum values sorted, draft vocabularies by path |
| S2 | **no Python class name appears anywhere in the rendered descriptor** — scanned against the known names of all 25 fact classes, 8 value objects, and 33 enums |
| S3 | every `FactFamily` member appears exactly once |
| S4 | all five draft vocabulary paths are present, and each matches a key actually emitted by `representation_payload` for a representative draft |
| S5 | a shape outside the closed grammar raises rather than rendering |
| S6 | change-detector: no two vocabularies share an admitted-value set and no two value objects share a field shape, so a future collision surfaces as a deliberate decision instead of a silent merge |
| S7 | the pinned hash canary, updated once, deliberately |

S2 is the test that would have caught this finding. S6 keeps §3's accepted consequence honest.

---

## 5. Expected patch footprint

Confined to one region of one module, plus its tests.

| File | Change | Size |
|---|---|---|
| `representation.py` | replace `_type_name` with a `_shape(annotation)` returning the grammar; fold `_declared_fields` and `_walk` into one recursive shape builder; rewrite `representation_schema_payload` (drop `fact_families[].type`, drop the `value_objects` registry, replace `vocabularies` with `draft_vocabularies` keyed by path); extend the constant's note with the wire-contract rule | ~110 lines replaced in one region |
| `test_representation_schema_identity.py` | add the §4 matrix; retain the existing order tests; update the canary once | ~200 lines added |
| `data/bounded_oracle.json` | declared `representation_schema.hash` only | 1 line |

**Unchanged:** `REPRESENTATION_SCHEMA_VERSION` stays `5d-representation-schema-1` — this corrects the
unmerged initial contract, and nothing accepted, persisted, or published exists under it. The
`{version, hash}` declaration shape is untouched, so `AcceptedOracle`, `ProjectionCandidate`,
`projection_payload`, `oracle_payload`, the projection header columns, `reconstruct_candidate`, the
persisted-state digest, the publication gate, and migration 0027 all stay as they are. **No migration, no
ORM change, no production content.**

The hash will move once more, and the canary moves with it.

---

## 6. Unresolved ownership question — one, and it is about placement

**Where does the draft-vocabulary path table belong?**

The five paths are defined by `projection.representation_payload`, which lives in `projection.py`.
Hand-writing them in `representation.py` puts a second copy of that knowledge in a module that cannot see
it — the "two hand-written derivations eventually disagree" shape this repository already avoids elsewhere
(`derive_obligations` exists precisely so the oracle and the gate cannot drift). A drifted path would not
fail loudly: the descriptor would simply describe a path the payload no longer emits.

Three options, with a recommendation rather than a decision:

1. **Table in `representation.py`, guarded by test S4**, which serializes a representative draft through
   `representation_payload` and asserts every declared path resolves to a real key. Lowest complexity; the
   guard is what makes it honest. *Recommended.*
2. **Move the draft-vocabulary portion into `projection.py`**, where the payload is built, and have the
   schema payload compose it. Removes the duplication, at the cost of splitting the descriptor across two
   modules and introducing an import direction that does not exist today.
3. **Derive the paths from `representation_payload` by construction.** Cleanest in principle, but it means
   executing a serializer to compute a schema identity, coupling identity to a code path it ought to be
   able to describe without running.

Option 1 with S4 is the lowest-complexity repository-native answer, but the choice is an ownership call
about where this knowledge lives, so it is surfaced rather than taken.

Nothing else is unresolved: the corrected governing rule as stated decides every other case in §1,
including the accepted collapse consequence in §3.

---

## Hard stop

Delivered for review. No code, migration, fixture, or PR-body change was made; PR #153 remains open and
frozen at `3f8a131`; all Codex threads remain unresolved; the untracked conditions proposal artifacts were
not regenerated; no production content was accepted or published; 2b, 15c, legacy retirement, and PR #129
are untouched. Implementation waits on a reviewed disposition of §2 and §6.
