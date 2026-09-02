# CRD Issue 5d — representation schema 5, bounded sibling audit

**Defect family.** *Mechanically distinct source meanings collapse or disappear because their
qualifiers or composition are not present in canonical typed authority.*

**Trigger.** The sibling gate fired: the hazards-1 semantic review rejected proposal
`6277ff73…a259` on three instances of one family, after PR #159 had already merged a schema
believed to close the hazards surface. Feedback moved from defect to grammar, which is the
boundary-check condition in `CLAUDE.md`.

**Scope discipline.** This audit controls scope; it does not expand it. Every `out of scope`
and `owner decision needed` row below is left alone, not quietly fixed.

---

## 1. The family, stated as a test

For each structure that carries a *qualifier* or a *composition*, ask: **can two source
statements that differ mechanically produce one canonical payload?** If yes, it is an
instance. Every closed structure in the representation was put to that question.

| # | Structure | Can two distinct meanings collapse? | Disposition |
|---|---|---|---|
| 1 | `AbilityCheckFact` — the roll a DC is stated for | **Yes.** A DC 10 Constitution *saving throw* and a DC 10 Constitution *ability check* were one payload and one fact key | **patched** — required `context: RollContext`, admitting exactly the two D20 Tests a DC can be stated for |
| 2 | `Applicability(CONSUMPTION_THRESHOLD)` | **Yes.** One comparison states one side, so *"eats **but** consumes less than half"* and *"eats nothing"* both reduced to `< 1/2` — and the source gives them different consequences | **patched** — `ConsumptionBand`, a closed two-sided band with an optional sustained duration |
| 3 | `DamageFact` + `ScalingFact(DISTANCE_FALLEN)` | **Yes, and worse: it produces two answers.** Nothing said whether the damage was a base the increment adds to or the per-interval amount. A 30-foot fall is 3d6 or 4d6 | **patched** — `DamageFact.per` / `DamageInterval`; `ScalingFact` refuses the basis; a component-level rule refuses the pair |
| 4 | `Applicability(ROLL_OUTCOME)` | **Yes, by *disappearing*.** *"On a successful check"* in a component that calls for no roll names the outcome of nothing, and the authority it gates is unreachable | **patched** — `component_roll_outcome_violations`: exactly one roll established in the same scope |
| 5 | `Applicability(DAMAGE_OUTCOME)` | No. Its operand is a damage result of the rule's own component, and `negated` distinguishes the two forms the source states | already safe |
| 6 | `Applicability(QUANTITY_THRESHOLD)` | No. `quantity`, `comparison` and `value` are all stated, and the closed field matrix keeps them exclusive to the kind | already safe |
| 7 | `Applicability(SIZE_COMPARISON)` | No. `SizeComparison` carries `measured`/`reference` operands and a directional bound — the collapse this shape had was closed at schema 3 | already safe |
| 8 | `Applicability(ELAPSED_DURATION)` | **Adjacent, and deliberately not widened.** It states a duration and nothing about the state that persisted. That is correct for a clause that means "five days have passed"; what was wrong was *using* it for "eats nothing for five days" | already safe — the misuse is closed by row 2 giving that clause its own home |
| 9 | `Recurrence` | No. Boundary and `whose` are both stated, and the turn/day invariant keeps them exclusive | already safe |
| 10 | `FactQualifier` | No. Addressed by content-derived key and scope; composes conjunctively by declaration | already safe |
| 11 | `ComponentOption` | No. Exhaustive by declaration, mutually exclusive, uniquely keyed | already safe |
| 12 | `RollSpec` | No. `actor`, `context`, `ability` and `skill` are all present — this is the family row 1 was measured against | already safe |
| 13 | `ConditionLevelFact` | No. `cause_scoped`, `all_levels` and `amount` are exclusive and stated | already safe |
| 14 | `ConditionRemovalRestrictionFact` | No, once row 2 lands: its `until` is an `Applicability`, so it inherits the band rather than restating a threshold | already safe (carried by row 2) |
| 15 | `SizeKeyedQuantityFact` | No. Rows are exhaustive over `CreatureSize` in declaration order | already safe |
| 16 | `DamageModificationFact` | No. `direction` and `factor` must agree, and `rounding` is optional because the corpus states it separately | already safe |
| 17 | `ScalingFact` other bases | **Out of scope.** `threshold` means "the level above which the change begins" for the level-based bases, which is unambiguous *there*. The ambiguity was the distance basis reading it as an interval, and that basis is now refused | out of scope |
| 18 | `MovementCostFact`, `MovementTransportFact` | No. Payer and participants explicit since schema 3 | already safe |
| 19 | `AttackRollFact` | **Owner decision needed, not taken.** It states no `RollContext` either, but an attack roll *is* its context — the question is whether a DC-bearing family and a roll-stating family should share one axis. No corpus clause forced it here | owner decision needed |
| 20 | `AbilityCheckFact.skill` under a saving throw | **Owner decision needed, not taken.** The SRD prints a skill only after an ability *check*, so a skill-qualified save is a form the source never uses — but nothing in this brief requires refusing it, and `_check_rollspec` permits the same combination on `RollSpec`, so refusing it in one place only would leave the two structures disagreeing | owner decision needed |

**Dispositions: 4 patched · 13 already safe · 1 out of scope · 2 owner decision needed.**

No check was loosened. Every existing refusal — primary-by-span uniqueness, duplicated fact
authority, the closed applicability field matrix, the alternatives contract, provenance-required
kinds — is unchanged and still exercised.

---

## 2. Regression coverage

| Row | Where it is proved |
|---|---|
| 1 | `test_schema_5_representation_corrections.py` — distinct payloads and fact keys, the context never omitted, keyword-only construction, three refused contexts, an undeclared context, mixed-context alternatives both ways, wire round trip, a payload missing the key |
| 2 | same module — six stated forms admitted and mutually distinct, eight malformed bands refused, the old triple unconstructible, the kind's field matrix |
| 3 | same module — one fact with one reading, the schema-4 scaling refused, the component rule, an option arm, a malformed interval, a flat amount |
| 4 | same module — no roll, two rolls, the honest qualifier shape, option-arm scoping, a component-wide outcome not established by one arm |
| all | `test_schema_5_persistence_and_overrides.py` — round trip, absence, identity-bearing in storage *and* in the persisted digest, refused on the way back, and the override patch loader reading the same contract |
| all | `test_schema_5_hazards_regeneration_fixtures.py` — the five corrections the rejection called for, as authorable components |

---

## 3. What this audit deliberately did **not** do

* It did not touch the accepted `conditions-1` artifact, its identity, its provenance
  coordinates, its batch anchor, or its succession record.
* It did not reuse, edit, or bless proposal `6277ff73…a259`.
* It did not begin `actions-1`.
* It did not add a Boolean predicate, an executable expression, a dictionary, or a key/value
  escape hatch. Every addition is a closed value object or a required member of a closed
  vocabulary, and `Applicability` still refuses to combine two of itself.
