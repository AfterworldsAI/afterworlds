# CRD Issue 5d — representation schema 5: implementation and remediation log

**Status: SCHEMA PR. Nothing accepted, published, activated, or retired.** `accept_proposal` is never
called. `oracles/` is read and asserted byte-unchanged, never written. Proposal
`6277ff735e0e47b3337f2c3736ca7922864b1cde9a3c286b3aee48ee461ba259` is not reused, edited, or blessed.
`actions-1` is not begun. Nothing is merged.

**Branch** `feature/issue-5d-representation-schema-5`, created at `origin/main` =
`8f2391f3d29d501cbde904efee2ffd8bdcd10dd2`.

---

## 1. The defect family, and why a schema succession is the right instrument

*Mechanically distinct source meanings collapse or disappear because their qualifiers or composition
are not present in canonical typed authority.*

This is merge-blocking because the projection is **declarative data a deterministic consumer reads**.
A collapse is not a lossy representation; it is a false one. A DC 10 Constitution saving throw and a
DC 10 Constitution ability check are different rolls with different proficiency; a creature that ate
nothing and one that ate a third of its requirement take different consequences; a 30-foot fall deals
3d6 or 4d6. Under schema 4 each pair produced one canonical payload and one fact key, so no consumer
could recover the difference and no validator could report it.

It cannot be fixed in a proposal. The collapse is in the grammar, so a corrected proposal authored
against schema 4 would state the same thing and hash the same way.

---

## 2. What schema 5 adds — five rules, each closed

### 2.1 `AbilityCheckFact.context: RollContext` — required (Owner Decision 2026-09-02, Option A)

Admits exactly `ABILITY_CHECK` and `SAVING_THROW`. Malnutrition's DC 10 Constitution roll is a
`SAVING_THROW`; Falling's Strength (Athletics) / Dexterity (Acrobatics) alternation stays
`ABILITY_CHECK`; when alternatives are present the fact *and* every alternative must be ability
checks. The family is **not** migrated onto `RollSpec` — actor polarity stays outside a DC source,
for the reason the family already gave.

**Required, not defaulted.** A default would omit one spelling under the post-schema-3 omission rule,
and the omitted form would hash exactly as the stated form — re-creating the collapse inside the
mechanism built to preserve identity.

**Keyword-only.** A required field must precede every defaulted one, which would have made
`AbilityCheckFact(WISDOM, FIXED, 15)` bind `15` to the new axis instead of to `dc_value` — silently,
at every existing call site. `declared_field(kw_only=True)` keeps the declared order and made all 33
existing constructions fail loudly with "missing 1 required keyword-only argument" instead of
mis-binding. That is the reason the change is safe to make at this size.

### 2.2 `ConsumptionBand` — one closed band, not a threshold

`ApplicabilityKind.CONSUMPTION_THRESHOLD` now ranges over exactly one field, `band`. The band carries
the requirement, the period, an optional lower and upper bound each with its own inclusivity, and an
optional **sustained** duration *of the band itself*.

The four distinctions the rejection required, and the two neighbours they must not collapse into:

| Source clause | Band |
|---|---|
| *"eats **but** consumes less than half"* | lower `0` exclusive, upper `1/2` exclusive |
| *"eats nothing"* | lower and upper `0`, both inclusive |
| *"eats nothing **for 5 days**"* | the same point band, `sustained_at_least=5 DAY` |
| *"drinks less than half the required water"* | upper `1/2` exclusive, no lower bound |
| *"drinks the full amount required for a day"* | lower `1` inclusive, no upper bound |

**Not a conjunction, and not a predicate language.** The band is one predicate over one operand — the
subject's consumption of one requirement over one period — with no operators, no nesting, and no way
to combine two bands into a third. `sustained_at_least` is part of the same predicate rather than a
second one: *"eats nothing for 5 days"* is one state with a duration, and stating it as
`ELAPSED_DURATION(5, DAY)` beside a zero-food test would say "five days have passed", which is true of
every creature alive on day five.

**"Each subsequent day" needs no structure**, and this is the one place the design leans on declared
component semantics rather than adding something. `ComponentDraft.applies_when` is documented as
*"When this component applies at all. `None` means unconditionally."* A component whose applicability
is the band and whose `recurs` is a daily boundary therefore repeats only while the band holds, and
stops the day eating resumes. That sentence is quoted rather than paraphrased so a reviewer can check
the inference instead of trusting it.

**Rejected alternative, recorded.** A component `applies_when` of `CONSUMPTION_THRESHOLD(FOOD,
EQUALS, 0)` plus a `FactQualifier(ELAPSED_DURATION, 5, DAY)`, composing conjunctively. It has no
accepted precedent — the single accepted fact qualifier sits on a component whose `applies_when` is
`null` — and it contradicts `FactQualifier`'s declared purpose, *one fact's condition where it differs
from its siblings'*, which is not this case. Using two scopes as a conjunction operator is the
predicate language `Applicability` is built to refuse.

**`required_quantity` and `fraction` are removed, not left dormant.** With the kind ranging over
`band`, no kind ranges over them, so they would be unreachable by construction — which is the same
class of ambiguity this succession closes. Consequence, stated and tested: a hypothetical schema-4
artifact using `consumption_threshold` cannot lift to schema 5. That is correct rather than
regrettable — schema 5 *redefines* what the kind means, and a lift may never reshape content — and no
such artifact exists, because nothing has been accepted since `conditions-1` at schema 3.

### 2.3 `DamageFact.per: DamageInterval` — one reading for Falling

*"1d6 Bludgeoning damage at the end of the fall for every 10 feet it fell, to a maximum of 20d6"* is
now one fact: the amount is per interval, capped, with **no additive base die**.

Enforced three ways, none of them a consumer inference:

1. `ScalingFact` **refuses** `ScalingBasis.DISTANCE_FALLEN` outright — the ambiguous form is
   unstateable rather than discouraged;
2. a **component-level** rule refuses a per-interval damage beside a damage-effect scaling, which
   catches the composition that is legal fact by fact and unreadable together; and
3. `per` requires `dice`, because an interval repeats a dice expression and a cap has nothing to cap
   otherwise.

`DistanceUnit` is its own vocabulary rather than a member of `MeasureUnit`: that one is volumes and
masses from the requirement tables, and folding a distance in would let a water requirement state
itself in feet.

**Documentation reconciled in this PR, not contradicted.** Schema 4 declared that
`ScalingFact.threshold` carried the per-unit interval for this basis. That reading was not
enforceable — under every other basis the same field is *the level above which the change begins* —
and it is now **withdrawn** in three places: the `ScalingBasis.DISTANCE_FALLEN` docstring, ADR-005d
Decision 4 (Owner Decision 2026-09-02), and the H-7 rows of the hazards schema-closure checkpoint.

### 2.4 A roll outcome answers to exactly one roll in its own scope

Not on the brief's numbered list, but required by two of its fixtures and by the same defect family:
*"On a successful check"* in a component that calls for no roll names the outcome of nothing, and the
authority it gates becomes unreachable. Two rolls in scope is worse — a consumer picks one.

`component_roll_outcome_violations` requires exactly one roll-establishing fact
(`ABILITY_CHECK` or `ATTACK_ROLL`) in the same scope, with the same scoping rule
`component_participant_violations` already uses: a component's own facts establish for every scope; an
option's facts establish only within that option, because the arms are mutually exclusive.

The honest authoring it forces is the one the source states, and it is the third proposal correction:
the halving sits in the component that holds the check, qualifying that one fact.

### 2.5 A skill qualifies an ability check, and nothing else

Carried as an owner decision in the first cut and resolved 2026-09-02 as implementation work. The SRD
prints a skill in parentheses after the ability of a *check* — *"a DC 15 Dexterity (Acrobatics)
check"* — and never after a saving throw. Proficiency in a skill applies to the check it names; a save
adds save proficiency, a different bonus from a different column of the sheet.

Schema 5 is what makes this statable: before the context axis existed there was no check/save
distinction to apply. Having introduced it, admitting a skilled save would let the new distinction
express a combination the source never uses.

**One function, read by both carriers.** `_check_skill_context` is called by `_check_ability_check`
and by `_check_rollspec`. That is the whole point: the asymmetry that deferred this rule was that
refusing it on `AbilityCheckFact` alone would leave `RollSpec` admitting it, and two validators that
happen to agree are not one rule. The invariant manifest declares both loci
(`fact:ability_check` and the `RollSpec` shape) so the identity covers the pair.

**`_check_ability_check` was restructured into three passes** — vocabulary, then context, then the DC
relationship — because each reads values the pass before admitted. Putting the context rules ahead of
the skill, alternatives and DC clauses is not cosmetic: a saving throw offering a choice of checks
*also* fails the alternatives completeness rule, and reporting that first names the symptom ("no
member states the fact's own pair") instead of the defect.

**It adds no field.** The rule is an invariant over two fields that already existed, so it moves the
schema hash and moves no payload: every accepted `conditions-1` element stays byte-identical across
it, and the disclosed `APPEND_COMPONENT` override identity does **not** move again — rechecked
against the final hash and still `3f6443f6-5d47-5178-9f44-ce1f6fd92c87`.

**Where it is enforced, and where deliberately not.** `fact_from_payload` rebuilds the declared
*shape* and runs no family invariant — that is the pre-existing design for every fact rule, and the
fixed-DC rule behaves identically — so a tampered payload rebuilds and the authority it would become
is refused. Enforcement is `fact_invariant_violations`, reached by `_validate_components` and by
`held_structure_violations`, which together cover the publication gate, acceptance, the committed
loader, `verify_lift`, persistence reconstruction and the override effective view.

**`AttackRollFact` needs no counterpart change.** `FactFamily.ATTACK_ROLL` is the discriminator a
consumer reads and `attack_kind` supplies the closed subtype, so the family already states its own
context; adding a `RollContext` field would restate one axis in two places, which is the collapse
risk inverted.

---

## 3. Succession — 3 → 4 → 5, resolved as a path

| | |
|---|---|
| schema 5 version | `5d-representation-schema-5` |
| schema 5 hash (pinned literally) | `2803840899363988cc2f67e0d9f310d9baffe394d52ca0919d11388bcd7f4c40` |
| lift id | `5d-lift-schema-4-to-5` |
| schema 4 pin | `241860418b183f67bcc4d914d1fdaa3bbcea1705f28cdd460eb05716d40ce3e9` — **unchanged**, still a recognized contract |
| schema 3 pin | `43ed330d3b3630d37ed92122fd87cc2c170863bab4465e53c727f1b8c6b86e05` — **unchanged** |

`lift_for` stays the exact single-step lookup. `lift_path` is new and walks **registered rows only**
from the exact source pair to the exact target pair, bounded by the registry's own size. A direct
3 → 5 row was deliberately **not** registered: it would reach the same declaration while asserting the
artifact never crossed schema 4, which `lift_chain_violations` refuses as decoration. `accept_proposal`
and `lift_accepted_inputs` now apply and record every step, so the committed artifact's evidence keeps
saying which successions actually happened.

Unregistered, reversed, skipped, and hash-mismatched transitions each have no path and raise
`UnknownSchemaLiftError`; the no-op is still decided by the caller, not by the registry.

### Zero-movement proof, re-run against the **final** declarations

```
build declares       : 5d-representation-schema-5 28038408…f4c40   (pin matches)
prior declares       : 5d-representation-schema-3
prior oracle id      : a0f0bd2f6f6f05d3b0b46b63d1dfa9c5e4c3bf0741118b063a5d2b6adf401fda
lift chain           : ['5d-lift-schema-3-to-4', '5d-lift-schema-4-to-5']
verified collections : components, records, references, relationships, prose_bindings, provenance
collections moved    : NONE
spans                : 185 unchanged      obligations : 16 unchanged
acceptances          : 185 unchanged      batches     : unchanged
anchors              : [('conditions-1', '5d-representation-schema-3')]  — synthesized at the schema
                        it was reviewed under, never at the destination
representation       : carried by object identity, not by transformation
ability_check facts  : 0  — asserted against the artifact, not assumed
committed artifact   : bytes unchanged
lifted oracle id     : 03623492…  — moves only because the declared schema did (Decision 8)
```

---

## 4. Every authority-bearing seam the new meaning threads

| Seam | Change |
|---|---|
| canonicalization | `context` always emitted; `per` and `band` are post-schema-4 omit-when-empty, so every schema-3 and schema-4 element keeps its exact canonical form |
| fact builders | `_build_ability_check` reads `context` unconditionally; `_build_damage` rebuilds `per`; both refuse a truncated payload |
| value-object builders | `build_consumption_band` and `_build_damage_interval`, each validating on the way back in |
| the three applicability loaders | `oracle.py`, `persistence.py`, `services/rules_authority/patches.py` — all three now call the **one** `build_consumption_band`, replacing three copies of `_rational_operand` |
| schema legality | `_REQUIRED_SINCE` (a required field an earlier contract could not carry) beside `_POST_SCHEMA_3_FIELDS`; `_SCHEMA_5_VOCABULARY_MEMBERS`; `_VERSION_STATES[schema 5]` written out rather than inherited |
| schema identity | `introduction_manifest` gains the `DistanceUnit` rows; `invariant_manifest` gains seven rows and replaces the schema-4 consumption-fraction row; `_wire_fields` declares `required_since` |
| closed structures | `ConsumptionBand` and `DamageInterval` added to `_CLOSED_TYPES`, so subclass refusal and `_declared_type` reach them |
| projection | `SCHEMA_5_VERSION` rows in `_MERGED_COMPONENT_FIELDS` and `_RECORD_OWNED_REFERENCE_VERSIONS`, both written out; `_APPLICABILITY_OPTIONAL_KEYS` gains `band` and loses the two removed keys |
| validation | `component_roll_outcome_violations` and `component_damage_composition_violations` called from `_validate_components` |
| typed overrides / effective views | both new component rules called from `application.py` after the whole ordered set resolves, failing through the established `INVALID_OVERRIDE` path |
| persistence | **no migration.** No component key is added: `context` and `per` ride the fact payload JSON, `band` rides the existing `rp_mech_components.applies_when` JSON. Proved against a real session rather than asserted |
| acceptance | multi-step lift path; `lifts` accumulates every crossing |

---

## 5. Tests

| Module | Count | Covers |
|---|--:|---|
| `test_schema_5_representation_corrections.py` | 57 | the three corrections, the roll-outcome rule, and the whole succession |
| `test_schema_5_persistence_and_overrides.py` | 16 | round trip, absence, identity-bearing in storage *and* in the persisted digest, refusal on the way back, and the patch loader |
| `test_schema_5_hazards_regeneration_fixtures.py` | 13 | the five proposal corrections, as authorable components |
| `test_schema_5_skill_context.py` | 27 | a skill only on an ability check, at both carriers and every seam |

Every item the brief lists is covered:

* identical ability/DC under check versus save yield distinct payloads **and** fact keys;
* invalid contexts (three) and mixed-context alternatives (both directions) fail closed;
* schema 4 rejects schema-5-only meaning — all four carriers, and schema 5 admits each;
* partial-food, zero-food, five-day and resumed-eating boundaries are distinguishable, with eight
  malformed bands refused;
* Falling cannot be interpreted as base damage plus scaling — at the fact, at the component, and
  inside an option arm;
* ambiguous and detached roll-outcome applicability both fail;
* the 3 → 4 → 5 lift preserves every inherited accepted element byte-for-byte, in two recorded steps;
* persistence, override and wire round-trips retain every new field;
* a Constitution save with no skill is valid, Athletics and Acrobatics are each refused on a save,
  a `RollSpec` save carrying a skill is refused, a skilled check stays valid, alternative checks stay
  valid and canonically ordered, and malformed skill/context combinations fail at every seam that
  admits authority.

---

## 5a. Existing assertions changed, and why each was over-asserting

Two properties are **weakened**, and both were incidental rather than declared. Saying so plainly
because "an assertion relaxed by the PR that would otherwise fail it" is exactly the shape a reviewer
should challenge.

| Assertion | Was | Now | Why the old form was not the property |
|---|---|---|---|
| `test_each_merged_version_extends_the_one_before_it` | `fields[earlier] < fields[later]` | `<=` | Its own docstring states the rule as *"a version whose key set is not a superset of its predecessor's would mean a key was removed"* — that is `<=`. Strict growth additionally demanded that **every** succession add a component key, which held for schemas 1–4 by coincidence. Schema 5 widens the contract with a required fact field, a fact field, an applicability field and two value objects; none is a component key. |
| `test_no_two_merged_versions_share_a_key_set` → `test_every_merged_version_states_its_own_key_set` | no two versions share a set, *"otherwise the version is noise"* | each version has its own explicitly written row, and an unrecognised version still fails closed | The premise is false: a version can add meaning without adding a *component* key. What `_MERGED_COMPONENT_FIELDS` actually guarantees — its own docstring — is that each version *states its own row* so a later succession cannot silently redefine an earlier one. That is now what is asserted, together with the failing-closed lookup `_emitted_component_fields` relies on. |

**Nothing that guards the rule was touched.** `_emitted_component_fields` still raises
`UnsupportedSchemaVersionError` on an unrecognised version; the module-level assertion still refuses
a build whose current version has no row; every earlier version's row is unchanged and still asserted
individually.

Three premises are **generalized** rather than weakened — each pinned the build to one named
successor and would expire at every future mint:

* `test_the_build_implements_a_later_schema_than_the_artifact_declares`:
  `REPRESENTATION_SCHEMA_VERSION == SCHEMA_4_VERSION` → `!= SCHEMA_3_VERSION`, which is the premise
  the module's tests actually need (*the build is later than the artifact*).
* `test_the_captured_structural_hash_is_the_one_already_pinned`: `== SCHEMA_4_VERSION` →
  `!= SCHEMA_2_VERSION`, beside the unchanged hash-inequality assertion it exists for.
* `test_each_merged_schema_version_has_its_own_structural_identity`: same shape, stated against the
  schema-1 and schema-2 literals it is really about.

Six **pins** moved from schema 4's hash to schema 5's, which is the ordinary cost of a mint and is
what keeps the restamp guard loud: `test_representation_schema_identity` (`EXPECTED_SCHEMA_HASH`),
`test_schema_4_invariant_closure`, `test_schema_version_legality`,
`test_subclass_refusal_at_authority_seams`, `test_review_round_7_draft_exact_types`, and
`test_review_round_5_component_patch_schema2`. Two "unknown version" sentinels moved from
`5d-representation-schema-5` to `-6`, because the old sentinel is now a real contract.

### `bounded_oracle.json` — carried, not restamped

The committed gate fixture declared schema 4 with its batch anchored at schema 4 and no lift
evidence. It **had** to move, because `accepted_oracle()` builds the in-memory comparison from the
live `REPRESENTATION_SCHEMA_VERSION` and the gate refuses a schema mismatch outright. Of the two
coherent ways to move it, the fixture now declares schema 5 while keeping its anchor at **schema 4**
and carrying a real `5d-lift-schema-4-to-5` record over all six collections. A bare hash swap would
have tripped rule 4 of `succession_evidence_violations` (*"reviewed under X, which this artifact
declares as Y without a registered succession carrying it there"*), and re-anchoring at schema 5 would
have asserted the batch was *reviewed* under a contract that did not exist when it was written. The
form chosen also earns its keep: it is the only committed file that exercises the loaded
lift-evidence path end to end.

---

## 6. Residue, stated rather than resolved

Two rows of the sibling audit are **owner decisions, deliberately not taken**:

* **`AttackRollFact` states no `RollContext` either.** An attack roll *is* its own context, so the
  question is whether a DC-bearing family and a roll-stating family should share one axis. No corpus
  clause in this boundary forced it.
* **`AbilityCheckFact.skill` under a saving throw.** The SRD prints a skill only after an ability
  *check*, so a skill-qualified save is a form the source never uses. It was considered and **not**
  implemented: nothing in this brief requires it, it is not needed for any of the five required
  distinctions, and `_check_rollspec` permits the same combination on `RollSpec` — so refusing it in
  one structure only would leave the two disagreeing about one combination. Fixing both is visibly
  outside the four requirements.

One boundary is **tested rather than papered over**: a schema-4 artifact using `consumption_threshold`
cannot lift to schema 5, because schema 5 redefines what that kind ranges over and a lift may never
reshape content. No such artifact exists.
