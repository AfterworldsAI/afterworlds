# CRD Issue 5d — conditions-driven schema closure

Detail log for the schema-closure PR. The PR body carries the short version; this file holds the
per-clause dispositions, the sibling audit, and the evidence for every include/defer call.

**Base:** `c4c7edc2ac9fd7b3b6cb06e7ad9038a5e06b3aac` (merge of PR #151).
**Production 5c release used for all corpus evidence:** `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` /
`5.2.1-corpus.36b786d8-fa2`, rebuilt from the committed PDF; all six binding values reproduce PR #151's
table exactly.

---

## 1. Why this PR exists

The conditions-1 proposal checkpoint proposed **33 clauses as `UNRESOLVED`** because the closed typed
union could not carry them, and four of those were not lossy but broken. `accounting.validate_acceptance`
rejects `UNRESOLVED` spans, so the batch was un-acceptable by construction until the union closed.

The four verified structural failures, each reproduced by running the repository's own code:

| # | Clause | Failure |
|---|---|---|
| 1 | Blinded *"Attack rolls against you have Advantage, and your attack rolls have Disadvantage"* vs Invisible's exact inverse | **byte-identical fact keys** for opposite rules |
| 2 | Prone *"You have Disadvantage on attack rolls. … Otherwise, that attack roll has Disadvantage."* | two claims collapse to one key → `duplicate typed fact`, clause unrepresentable |
| 3 | Petrified *"You have Resistance to all damage."* | no `ALL` scope; enumerating 13 types needs 13 `PRIMARY` claims on one span → `conflicting primary claims` |
| 4 | Restrained *"You have Disadvantage on Dexterity saving throws."* | nearest typed form asserts disadvantage on **every** saving throw — false, not lossy |

---

## 2. Include/defer rule, applied uniformly

A type is added only if it (a) resolves a required regression point or several unresolved clauses,
(b) has siblings in **two or more** top-level sections, and (c) needs no referent vocabulary. Counts are
corpus-wide occurrences over the 28,109 represented leaves.

| Candidate | Siblings | Sections | Verdict |
|---|---:|---:|---|
| roll actor polarity | 60 (+8 "your attack rolls") | 10 | **added** — `RollSpec.actor` |
| ability-qualified saving throw | 529 | 10 | **added** — `RollSpec.ability` |
| ability-qualified check | 17 (+ `Ability (Skill)` forms) | 8 | same field |
| advantage on an ability-qualified roll | 43 | 9 | same field |
| automatic success/failure | 25 | 5 | **added** — `AutomaticOutcomeFact` |
| "Speed is 0" / reduced / halved | 34 | 7 | **added** — `SpeedModificationFact` |
| Resistance/Immunity "to all damage" | 12 | 7 | **added** — `DamageScope` |
| "all damage except …" | 3 (1 and 2 exceptions) | 3 | **added** — `except_types` |
| critical-hit change | 2 promotion + 2 threshold | 2 | **added** — `CriticalHitRuleFact`; thin, and named by the owner |
| action-economy prohibition | 3 | 2 | **added** — `ActionRestrictionFact`; borderline, minimal shape, central condition |
| `D20_TEST` roll context | Exhaustion + Spells *"Advantage on D20 Tests"* | 2 | **added** |
| Concentration broken | 7 | 3 | **added** — `StateEffectKind` |
| "you drop whatever you're holding" | 6 (4 genuine) | 2 | **added** — `StateEffectKind` |
| "can't speak" | 4 genuine (27 Monsters A–Z hits are a *Languages* descriptor and are **not** counted) | 2 | **added** — `StateEffectKind` |
| "unaware of your surroundings" | 2 | 2 | **added** — thinnest member, stated as such |
| **imposed sensory state** ("You can't see"/"can't hear") | **1 each** | 1 | **residue** — every other blinding effect says *"has the Blinded condition"*, which `ConditionEffectFact` already carries; a member here would be condition-specific |
| **targeting restrictions** | 11 + 14 + 5 + 9 | 6 | **deferred, narrowed** — referents do not close (§3) |
| **Exhaustion accrual / death threshold / level removal** | 1 each | 1 | **residue** — a condition-level state machine, and the source itself calls Exhaustion *"an exception to that rule"* |

---

## 3. Sibling audit — targeting restrictions

**Defect family:** clauses that forbid an action against a referent. **Trigger:** three unresolved
clauses (Charmed, Frightened, Invisible) that the previous checkpoint refused to call prose-bound without
shown work.

**Structures inspected**, corpus-wide: `can't attack` (11 / 5 sections), `can't target` + `can't be
targeted` + `invalid target` (14 / 6), `can't willingly` (5 / 3), `unaffected by` / `isn't affected by`
(9 / 3).

**Finding.** The referents do not converge:

| Instance | Referent |
|---|---|
| *"you can't attack a target beyond this range"* | a distance |
| *"A familiar can't attack"* / *"the target can't attack or cast spells"* | unconditional |
| *"You can't attack the charmer"* | a creature relationship established by the effect |
| *"can't be targeted by any Divination spell"* | a spell school |
| *"Creatures of the chosen types can't willingly enter the area"* | a spatial area plus a creature-type set |
| *"unaffected by any effect that requires its target to be seen"* | a property of the effect itself |

A closed vocabulary spanning distances, creature relationships, spell schools, spatial areas, and effect
properties is a predicate language, which #137's Boundary Stop forbids.

**Disposition:** Charmed's, Frightened's, and Invisible's restrictions are **affirmatively prose-bound**
under `contextual_applicability`. This is a judgement made *from* the sweep, not a convenience — the
sweep is the justification, and it is recorded here and in `representation.py`'s module docstring.
`known_unknowns.md` records the family as narrowed, **not** discharged.

---

## 4. Disposition of all 33 formerly unresolved clauses

Numbering follows §7.1 of the proposal checkpoint.

| # | Record | Clause | Now |
|---:|---|---|---|
| 1 | blinded | *"You can't see …"* | **split**: *"You can't see"* → **residue**; *"and automatically fail any ability check"* → `AutomaticOutcomeFact`; *"that requires sight."* → prose (`contextual_applicability`) |
| 2 | charmed | *"can't attack the charmer …"* | **prose-bound**, `contextual_applicability` (§3) |
| 3 | deafened | *"You can't hear …"* | as #1 |
| 4 | exhaustion | cumulative levels + *"You die if …"* | **residue** |
| 5 | exhaustion | *"the roll is reduced by 2 times your Exhaustion level"* | `ScalingFact(CONDITION_LEVEL, D20_TEST, DECREASE, amount=2)` |
| 6 | exhaustion | *"Speed is reduced by … 5 times your Exhaustion level"* | `ScalingFact(CONDITION_LEVEL, SPEED, DECREASE, amount=5)` |
| 7 | exhaustion | *"Finishing a Long Rest removes 1 …"* | **residue** |
| 8 | frightened | *"can't willingly move closer to the source of fear"* | **prose-bound** (§3) |
| 9, 15, 19, 26, 30 | grappled, paralyzed, petrified, restrained, unconscious | *"Your Speed is 0 and can't increase."* ×5 | `SpeedModificationFact(SET_TO, 0, can_increase=False)` |
| 10 | grappled | movement cost + size eligibility | **residue** |
| 11 | incapacitated | *"can't take any action, Bonus Action, or Reaction"* | 3 × `ActionRestrictionFact` |
| 12 | incapacitated | *"Your Concentration is broken."* | `StateEffectFact(CONCENTRATION_BROKEN)` |
| 13 | incapacitated | *"You can't speak."* | `StateEffectFact(CANNOT_SPEAK)` |
| 14 | invisible | *"aren't affected by any effect that requires its target to be seen …"* | **prose-bound** (§3) |
| 16, 20, 28, 31 | paralyzed, petrified, stunned, unconscious | *"automatically fail Strength and Dexterity saving throws"* ×4 | 2 × `AutomaticOutcomeFact` each, distinguished by ability |
| 17, 32 | paralyzed, unconscious | *"… is a Critical Hit if the attacker is within 5 feet of you."* ×2 | `CriticalHitRuleFact(AUTOMATIC_ON_HIT)` + prose qualifier → `MIXED` |
| 18 | petrified | transformation, ×10 weight, ceased aging | **residue** |
| 21 | petrified | *"You have Resistance to all damage."* | `DamageResponseFact(RESISTANCE, ALL)` — one claim, one primary provenance |
| 22, 23 | prone | movement options and cost | **residue** |
| 24, 25 | prone | *"An attack roll against you has Advantage if …"* / *"Otherwise, …"* | two `AdvantageFact`s distinguished by `RollSpec.actor`, **+ the branch selector (*"if the attacker is within 5 feet of you. Otherwise,"*) bound as prose → `MIXED`**, matching #17/#32 |
| 27 | restrained | *"Disadvantage on Dexterity saving throws"* | `AdvantageFact(DIS, RollSpec(SUBJECT, SAVING_THROW, DEXTERITY))` |
| 29 | unconscious | *"you drop whatever you're holding. When this condition ends, you remain Prone."* | **split**: drop → `StateEffectFact(DROPS_HELD_OBJECTS)`; *"When this condition ends …"* → **residue** (sequencing) |
| 33 | unconscious | *"You're unaware of your surroundings."* | `StateEffectFact(UNAWARE_OF_SURROUNDINGS)` |

Components: 31 `STRUCTURED`, 9 `MIXED`, 4 `PROSE_BOUND`.

**24 of 33 resolved as typed authority, 3 as affirmatively prose-bound, 6 remain unresolved** — plus the
two sensory-state fragments split out of #1 and #3 and the sequencing fragment split out of #29, giving
**9 unresolved spans** in the regenerated proposal.

### Remaining residue and why

| Clause | Why it stays unresolved |
|---|---|
| Blinded *"You can't see"*, Deafened *"You can't hear"* | one instance each corpus-wide; every other blinding effect delegates to the condition record |
| Exhaustion accrual + death threshold | a per-condition level counter and a death trigger; singular machinery |
| Exhaustion level removal on a Long Rest | a condition-level decrement, not resource cadence; `ResourceRecoveryFact` would need a free-string `resource_key`, the escape hatch Decision 4 forbids |
| Grappled movement cost + size comparison | movement cost and creature size are both untyped; eligibility is a deferred family this clause alone does not force |
| Petrified transformation | three singular claims (substance, ×10 weight, ceased aging) |
| Prone movement options ×2 | crawling and the half-Speed stand-up cost; also split across two 5c leaves |
| Unconscious *"When this condition ends, you remain Prone."* | sequencing, a deferred family |

None is prose-bound. Each is an honest "cannot classify safely yet" that continues to block acceptance,
which is the correct state.

---

## 5. Schema families added or extended

**New shared value object:** `RollSpec(actor, context, ability)` — held to the same strictness as
`DiceExpression`, with its own checker and builder.

**New families (5):** `AUTOMATIC_OUTCOME`, `SPEED_MODIFICATION`, `ACTION_RESTRICTION`,
`CRITICAL_HIT_RULE`, `STATE_EFFECT`. The union goes 20 → 25.

**Extended families (3):**

* `AdvantageFact` — `context: RollContext` → `roll: RollSpec`;
* `DamageResponseFact` — gains `scope` and `except_types`; `damage_type` becomes optional and set exactly
  for `SPECIFIC`;
* `ScalingFact` — gains `direction`. `dice_increase`/`amount_increase` are renamed `dice_amount`/`amount`
  so a decrease is not a value whose field name contradicts it.

**New enums:** `RollActor` (2), `AutomaticOutcome`, `DamageScope`, `SpeedChange`, `CriticalHitChange`,
`StateEffectKind` (4), `ScalingDirection`.
**Extended enums:** `RollContext += D20_TEST`; `ScalingBasis += CONDITION_LEVEL`;
`ScalingEffect += D20_TEST, SPEED`.

**`RollActor` has two members, not three.** A third-party actor — *"the charmer has Advantage on any
ability check to interact with you socially"* — is a roll directed at the subject whose actor restriction
is applicability prose on a `MIXED` component, which is the representation this module already defines.
No corpus evidence forced a third member, so none was added.

**`AbilityCheckFact` was deliberately not migrated onto `RollSpec`.** It states that a roll is called for
and where its DC comes from; `RollSpec` says which roll a stated modification applies to. A DC source has
no actor polarity, so folding them together would give that family a field it can never populate.

---

## 6. Regenerated proposal

Same selection rule, same 16 entry containers, same 134 leaves, regenerated against the closed schema.

| | before | after |
|---|---:|---:|
| spans | 159 | 173 |
| substantive | 30 | 68 |
| supporting authority | 96 | 96 |
| **unresolved** | **33** | **9** |
| non-mechanical | 0 | 0 |
| components | 20 | 44 |
| typed facts | 25 | 55 |
| fact families exercised | 2 | 9 |
| prose bindings | 5 | 13 |
| records with no component | 2 (Deafened, Exhaustion) | **0** |
| validation findings | 0 | 0 |

Families exercised: `advantage` 22, `automatic_outcome` 10, `condition_effect` 6, `speed_modification` 5,
`state_effect` 4, `action_restriction` 3, `critical_hit_rule` 2, `scaling` 2, `damage_response` 1.

Proposal identity: `0f362df6a0c7e433d4c7fbade3b28c293455e83c54ce4f1d226863c9a4f28338`
(was `dfcee03dd93d76e109ec932641a367119f63f8fc82d68836d2c817400610a662`).

The proposal, its audit trail, and the generator remain **untracked** working files under
`.claude/review-notes/`, per PR #151's treatment of proposals as disposable review material.

---

## 7. Verification

| Check | Result |
|---|---|
| `black src/ tests/` | clean |
| `ruff check src/ tests/` | clean |
| `mypy src/` | Success: no issues found in 224 source files |
| `pytest tests/ingestion/mechanical tests/services/rules_authority` | 1077 passed |
| regenerated proposal: `validate_partition` ×134, `validate_reason_codes`, `validate_representation` | 0 findings |
| `committed_oracle_for(production release)` | `None` — asserted |
| `accept_proposal` | **never called**; `oracles/` still holds only `README.md` |

Regression coverage for the six required proof points lives in
`tests/ingestion/mechanical/test_conditions_schema_closure.py` (39 tests) and the new section of
`tests/services/rules_authority/test_expanded_families_overrides.py`. Every test in the first module
fails against the pre-closure union.

The generic per-family machinery in `test_fact_families.py` covers the five new families automatically —
canonical round trip, JSON-primitive payloads, missing/extra field rejection, per-field type checking,
look-alike-dict rejection, and persistence + reconstruction — because each declares a corpus-grounded
exemplar. That is the module's existing design and the reason no per-family boilerplate was added.

---

## 8. Review round 4 — representation identity describes the wire contract

Fourth finding in the same mechanism (canonicalization, then ordering, then subclass acceptance, now
class-name leakage). Rather than a fourth reactive edit, PR #153 was frozen at
`3f8a131f265e41335735bc10e7f330a6595ec3d6` and a design/test-closure checkpoint was produced and
reviewed before any code moved. The checkpoint is
`.claude/review-notes/issue-5d-schema-identity-wire-contract-CHECKPOINT.md`; this section records what
was implemented from it and what the implementation found that the checkpoint did not.

### 8.1 The finding, reproduced on the frozen head

`representation_schema_hash()` still depended on Python class names. Three renames with no wire effect
each moved the hash:

| Rename | Wire effect | Identity effect before the fix |
|---|---|---|
| enum class `RollActor` → `RollActorRenamed`, same members | none | `_type_name` rendered the class name → **moved** |
| value object `RollSpec` → `RollSpecification`, same fields | none | emitted as `value_objects[].name` *and* every holder's field `type` → **moved** |
| fact class `AdvantageFact` → `AdvantageRuleFact`, same family and fields | none | emitted as `fact_families[].type` → **moved** |

Each reminted authority for an implementation-only refactor — and, since the pinned canary instructs a
version bump whenever the hash moves, would have done so under a bump asserting a contract change that
never happened.

### 8.2 The governing rule, as accepted

Representation-schema identity describes the **canonical serialized contract**, never Python
implementation names or declaration layout.

* Renaming a fact class, a value-object class, an enum class, a module, or a local symbol **must not**
  move it.
* Renaming a family discriminator or a serialized field, adding or removing an admitted vocabulary
  value, or changing a primitive, nullability, array, or nested-object shape **must** move it.
* A meaning-changing validation invariant that is not structurally represented remains a **manual**
  `REPRESENTATION_SCHEMA_VERSION` bump obligation. Unchanged by this round, and still stated in the
  constant's own docstring and proved by `test_the_schema_hash_does_not_cover_invariant_behaviour`.

### 8.3 The closed shape grammar

`representation_schema_payload()` now renders one recursive grammar with nowhere to put a Python name:

| Shape | Emitted for | Wire meaning |
|---|---|---|
| `{"kind": "integer"}` | `int` | JSON number |
| `{"kind": "string"}` | `str` | JSON string, unconstrained |
| `{"kind": "boolean"}` | `bool` | JSON boolean |
| `{"kind": "enum", "values": [...]}` | any `StrEnum` | JSON string from a closed, sorted set |
| `{"kind": "object", "fields": [{name, shape}]}` | any nested value object, **inlined** | JSON object with exactly those keys |
| `{"kind": "array", "items": <shape>}` | `tuple[X, ...]` **and** `list[X]` alike | JSON array |
| `"nullable": true` | `X \| None` | JSON null also admitted |

An annotation outside the grammar **raises** `UnsupportedRepresentationShapeError` rather than rendering.
This is the whole reason the leak cannot return: the old `_type_name` fell back to
`getattr(annotation, "__name__", str(annotation))`, so every shape nobody had described silently became
its Python name. There is now no fallback to fall into.

Payload shape:

```
{"representation_schema_version": ..., "facts": [{"family", "fields"}], "draft_vocabularies": [{"path", "shape"}]}
```

Dropped: `fact_families[].type` (fact class name), the whole `value_objects` registry (value objects are
inlined at each field site, so there is no name to reference and no reference that can dangle or alias),
and `vocabularies[].name` (a closed vocabulary *is* its admitted value set at the wire).

### 8.4 Draft-only vocabularies — the checkpoint's one open ownership question

Five closed vocabularies are reached from the drafts rather than from any fact field, so nothing finds
them by walking fact types. The checkpoint offered three placements and recommended the first; that is
what was implemented.

`_DRAFT_VOCABULARIES` is now keyed by **serialized path**, with the enum classes used only as the source
of their admitted values:

| Path | Admitted values from |
|---|---|
| `components[].handling` | `ComponentHandling` |
| `provenance[].role` | `ProvenanceRole` |
| `provenance[].target_kind` | `ProvenanceTargetKind` |
| `records[].kind` | `RecordKind` |
| `relationships[].kind` | `RelationshipKind` |

The paths are hand-written in `representation.py` while the payload emitting them is built by
`projection.representation_payload`. That duplication is real and is **guarded, not trusted**:
`test_every_declared_draft_path_resolves_in_a_real_payload` serializes a representative draft through the
production serializer and resolves every declared path against it, asserting the collection is non-empty
*and* the key present on every element *and* each observed value inside the declared set. A resolver that
passed on an empty collection would prove nothing, which is why non-emptiness is asserted first.

Verified by deliberate breakage: renaming the table's key to `records[].record_kind` fails the test with
`records[].record_kind: absent from ['kind', 'parent_key', 'semantic_key']`.

`representation_payload` was not moved, no new shared module was created, and no second serializer exists.

### 8.5 What the implementation found beyond the reported three

* **`tuple` container spelling was a fourth leak.** `_type_name` rendered `tuple[DamageType,...]`, but
  `_canonical_value` maps tuple and list to the same JSON array, so the Python container spelling was
  never wire-observable. Now both render `array`, proved by
  `test_tuple_and_list_are_the_same_array_contract`, which asserts the serializer equivalence alongside
  the descriptor equality rather than asserting the claim bare.
* **`None` was the contract in a Python spelling.** `type(None).__name__` produced `None|int`; nullability
  is genuinely wire-observable, so it survives as an explicit `nullable` flag rather than a type name.
* **Subclass dispatch would have collapsed 33 vocabularies into one shape, silently.** `bool` is a
  subclass of `int` and every `StrEnum` is a subclass of `str`. `_PRIMITIVE_SHAPES` is therefore matched
  by **exact type identity**, and `test_primitives_are_matched_by_exact_type_not_by_subclass` pins it.
  This failure mode raises no error and produces a plausible descriptor, so it needed its own test.
* **The pinned-hash count is two, not the one the checkpoint estimated.** `EXPECTED_SCHEMA_HASH` in the
  identity test and `data/bounded_oracle.json`. `tests/ingestion/mechanical/conftest.py` computes
  `SCHEMA_HASH` from `representation_schema_hash()`, so it needed no edit.

### 8.6 Structurally identical shapes are permitted, deliberately

Under structural identity, two vocabularies admitting the same values — or two value objects with the same
fields — render identically. That is **wire-correct**: neither carries a type tag, so nothing reading a
payload could distinguish them either. Context comes from the enclosing family discriminator, the field
name, or the draft path. No global uniqueness invariant was introduced.

Measured on this head: no vocabulary collisions, no value-object collisions, and **one** family pair
sharing a field shape — `action_economy` and `action_restriction` are both `{cost: <ActionCost values>}`.
They stay distinct because families are keyed by their discriminator, which is the concrete evidence that
the discriminator belongs in the descriptor. `test_no_two_closed_shapes_currently_collide` records all
three facts as a change-detector, so a future collision surfaces as a decision rather than a silent merge.

### 8.7 Test matrix

`tests/ingestion/mechanical/test_representation_schema_identity.py`, 55 tests.

| # | Perturbation | Expected | Test |
|---|---|---|---|
| I1 | fact class renamed | invariant | `..._a_family_entry_has_nowhere_to_put_a_class_name` (no `type` slot exists) |
| I1–I3 | holder, nested value object, **and** enum all renamed | invariant | `..._renaming_every_python_class_in_reach_leaves_the_contract` |
| I4/I5 | field and vocabulary declaration order permuted | invariant | `..._declaration_order_does_not_reach_the_contract` |
| I6 | `tuple[X, ...]` vs `list[X]` | invariant | `..._tuple_and_list_are_the_same_array_contract` |
| I7 | `Optional[X]` vs `X \| None` | invariant | `..._optional_spellings_agree` |
| I8 | docstring reworded | invariant | `..._prose_only_edits_leave_the_hash` (re-executes an edited copy of the module) |
| M1 | family discriminator changed | moves | `..._a_changed_family_discriminator_moves_the_contract` |
| M2–M8 | field added/removed/renamed/retyped, nullability, array↔scalar, nested reshape, vocabulary value | moves | `..._an_observable_change_still_moves_the_contract`, `..._a_removed_field_moves_the_contract` |
| M9 | draft vocabulary values changed | moves | `..._changing_a_draft_vocabulary_moves_the_contract` |
| M10 | draft **path** changed | moves | `..._changing_a_draft_path_moves_the_contract` |
| S1 | every collection canonically ordered, recursively | — | `..._every_collection_in_the_payload_is_canonically_ordered` |
| S2 | no Python class name anywhere in the descriptor | — | `..._no_python_class_name_appears_in_the_contract` |
| S3 | every `FactFamily` described exactly once | — | `..._every_family_is_described_exactly_once` |
| S4 | every draft path resolves in a real payload | — | `..._every_declared_draft_path_resolves_in_a_real_payload` |
| S5 | undescribable annotation fails closed | — | `..._an_undescribable_annotation_fails_closed` (×5), `..._primitives_are_matched_by_exact_type_not_by_subclass` |
| S6 | no closed-shape collisions today | — | `..._no_two_closed_shapes_currently_collide` |
| S7 | pinned hash canary | — | `..._the_committed_union_still_hashes_to_its_recorded_value` |

S2 is a **supplementary** canary, not the authority: a substring scan proves today's 75 class names are
absent, while the behavioural rename tests prove the property that keeps tomorrow's absent too. Both were
verified by deliberate breakage — reintroducing `fact_families[].type` fails S2 and I1 together.

Six existing tests in this module were **rewritten rather than retained**, because they indexed
`payload["value_objects"]` / `payload["vocabularies"]` by class name or asserted the literal rendered type
`"AbilityScore|None"`. Their assertions survive in the new form; their old shape could not.

### 8.8 Identity and version

`REPRESENTATION_SCHEMA_VERSION` stays `5d-representation-schema-1`. Nothing has been accepted, persisted,
or published under any earlier form of this unmerged contract, so this corrects the initial contract
rather than succeeding it; inventing a historical `2` would fabricate a version nothing was ever built
under. The structural hash moves once, deliberately:

| | |
|---|---|
| before | `09dcd290ba6b24b80f6f74c922103f8b39865f609f8b9407271c92c0aac39066` |
| after | `44bf8519d57a28a193717219e276b329f0eaa30c56cf52284219f67916d09ff3` |

Updated in exactly two places: `EXPECTED_SCHEMA_HASH` and `data/bounded_oracle.json`.

### 8.9 Patch footprint

| File | Change |
|---|---|
| `src/afterworlds/ingestion/mechanical/representation.py` | one region: `_type_name`/`_declared_fields`/`_walk` replaced by `_shape`/`_wire_fields`; `_DRAFT_VOCABULARIES` rekeyed by path; `_PRIMITIVE_SHAPES` and `UnsupportedRepresentationShapeError` added (the error exported); `representation_schema_payload` rewritten; the constant's ownership docstring corrected |
| `tests/ingestion/mechanical/test_representation_schema_identity.py` | six tests rewritten, the matrix added, canary updated |
| `tests/ingestion/mechanical/data/bounded_oracle.json` | one declared hash |

**Untouched, and no change was needed:** the `{version, hash}` declaration shape, and therefore
`AcceptedOracle`, `ProjectionCandidate`, `projection_payload`, `oracle_payload`, `MechanicalProposal`,
`accept_proposal`, the projection header columns, `reconstruct_candidate`, the persisted-state digest, the
publication gate, and migration 0027. No ORM change, no migration, no production content.
