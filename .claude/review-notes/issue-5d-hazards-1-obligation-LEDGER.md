# CRD Issue 5d — `hazards-1` obligation ledger, representation schema 3

**Status: PROPOSED, not accepted.** Nothing accepted, published, activated, or retired.
`accept_proposal` never called. `oracles/` untouched. No branch, no production/test/schema
change. Review artifacts only.

**Derived at** `origin/main` = `HEAD` = `319e61c0e9499d9bed68e7f06efd57beb615da90` (PR #158 merge).
Working tree content-identical to the merge; `git status --porcelain` shows zero tracked changes.

**Proposal identity:** `4fa498c0039f2211854aaebfb33b3a75b56f3177e0d56cf8d3143d1fd6ab6f6e`
**Schema:** `5d-representation-schema-3` / `43ed330d3b3630d37ed92122fd87cc2c170863bab4465e53c727f1b8c6b86e05`
— unmoved; no representation code was touched by this work.
**Policy:** `5d-semantic-policy-1` / `e6363968d6ee8ec288e6c7e3382907a1afd8bf2aad0b18e153aec439b5aa9454`
**Release binding:** five of six values re-derived from the committed PDF through `build_candidate`
and asserted at run time; `persisted_corpus_digest` carried from the published 5c release record
and disclosed as such.

---

## 1. Regenerated accounting (verified, not estimated)

| | conditions-1 (accepted) | hazards-1 schema 1 (retained) | **hazards-1 schema 3 (this run)** |
|---|--:|--:|--:|
| records | 16 | 6 | **6** |
| represented leaves | 134 | 43 | **43** |
| policy exclusions | 0 | 0 | **0** |
| spans | 185 | 66 | **94** |
| substantive | 87 | 7 | **4** |
| supporting authority | 98 | 39 | **24** |
| non-mechanical | 0 | 0 | **0** |
| **unresolved** | **0** | **20** | **66** |
| components | 54 | 6 | **2** |
| — structured / mixed / prose-bound | 40 / 10 / 4 | 6 / 0 / 0 | **1 / 1 / 0** |
| typed facts | 70 | 7 | **3** |
| prose bindings | 15 | 0 | **1** |
| references | 15 | 0 | **0** |
| relationships | 0 | 0 | **0** |
| validation findings | 0 | 0 | **0** |

Per record:

| record | leaves | spans | unresolved |
|---|--:|--:|--:|
| `glossary.hazard` | 4 | 9 | 5 |
| `hazard.burning` | 2 | 10 | 5 |
| `hazard.dehydration` | 13 | 25 | 19 |
| `hazard.falling` | 2 | 13 | 8 |
| `hazard.malnutrition` | 20 | 30 | 23 |
| `hazard.suffocation` | 2 | 7 | 6 |
| **total** | **43** | **94** | **66** |

**Four counts, kept apart.** 43 represented leaves · 94 proposal spans · **66 unresolved spans** ·
**33 distinct mechanical obligations** · **15 defect families**. The span:obligation ratio is far from
1:1 here because two obligations (the size-keyed water and food requirements) each span 13 leaves.

---

## 2. Why the counts moved: the emission rule

The schema-1 proposal reported 20 unresolved of 66. This regeneration reports 66 of 94 over the same
43 leaves. **No source text changed and no leaf accounting changed.** One rule changed:

> Emit a typed fact only when the fact's own claim is true as stated and its scope is not narrowed
> or multiplied by a predicate schema 3 cannot carry. Refuse when an unrepresentable qualifier would
> make the fact apply where the source does not, or apply once where the source repeats it.

That is the schema-3 fact-scoped-applicability finding (Grappled > Movable: *"Represented
component-wide, a Tiny subject would stop being transportable at all, which the source never says"*)
applied evenly to this batch. It is also the standard the schema-closure work already applied when it
refused `ConditionEffectFact(EXHAUSTION, APPLIES)` for a level gain — *"asserting bare application
would be lossy in a way that changes the rule."*

Six facts the schema-1 proposal emitted are refused here, each because the emitted fact would have
been **false**, not merely incomplete:

| Refused fact | Source clause | Why the bare fact is false |
|---|---|---|
| `DamageFact(FIRE, 1d4)` | Burning | cadence multiplies it: once vs. every turn |
| `DamageFact(BLUDGEONING, 1d6)` | Falling | scaling multiplies it: a bare 1d6 is wrong for any fall over 10 ft |
| `ConditionEffectFact(PRONE, APPLIES)` | Falling landing | the damage-outcome exception narrows it |
| `AbilityCheckFact(CON, FIXED, 10)` | Malnutrition | the consumption threshold narrows it to under-eaters |
| `ConditionLevelFact(EXHAUSTION, GAIN, 1)` | Dehydration, Suffocation | threshold/trigger narrows it |
| `ConditionLevelFact(EXHAUSTION, REMOVE, all_levels)` | Suffocation | would remove levels caused by dehydration too |

**Design inference, stated as such:** the line drawn is *narrowing or multiplying* versus *silence on
an independent axis*. Two facts survive it — Burning's action cost and its self-applied Prone cost
apply to every burning creature without qualification.

---

## 3. Prose-bound reassessment

The task required each `OPEN_REFERENT` candidate to be reassessed individually rather than carried
forward. Result: **one of the seven survives as an affirmative prose binding; six do not.**

| Candidate | Old label | Reassessed | Why |
|---|---|---|---|
| *"falls into water or another liquid"* | not previously flagged | **PROSE_BOUND** `contextual_applicability` | the source itself generalises to *"another liquid"*; whether a substance qualifies is fiction the projection cannot enumerate. Matches the closed reason's own wording, and matches the accepted conditions-1 disposition of targeting restrictions |
| required water / food per day | OPEN_REFERENT | **UNRESOLVED** | the operand is the in-batch Water/Food Needs per Day table — closed authority, not judgement |
| *"less than half the required"* | OPEN_REFERENT | **UNRESOLVED** | a quantity comparison against a table value. Structurally identical to Prone's accepted `Applicability(QUANTITY_THRESHOLD, SPEED, EQUALS, 0)` — Speed is runtime state too, and it was typed |
| *"the full amount … required for a day"* | OPEN_REFERENT | **UNRESOLVED** | same table operand |
| *"unless it avoids taking any damage from the fall"* | OPEN_REFERENT | **UNRESOLVED** | the operand is the damage outcome of this very rule — closed authority inside the record |
| *"doused, submerged, or suffocated"* | OPEN_REFERENT | **UNRESOLVED** | the trigger is genuinely open, but the *consequence* — the hazard ends — has no structure at all, so the span is blocked before the trigger is reached. Prose-binding it would assert a prose-bound component for a mechanic the schema simply lacks: a backlog state |
| *"runs out of breath or is choking"* | OPEN_REFERENT | **UNRESOLVED** | *"runs out of breath"* is crisp given the derived breath duration; only *"is choking"* is open. A heterogeneous trigger pair, and the crisp half must not be hidden |
| recurrence / duration clauses | OPEN_REFERENT | **UNRESOLVED** | *"at the start of each of its turns"*, *"at the day's end"* are exact cadences over closed boundaries, not judgement |

**Net: `PROSE_BOUND` is used once in 94 spans, affirmatively.** Nothing was prose-bound as a backlog
substitute.

---

## 4. Obligation ledger — 33 open, 4 closed

Substantive obligations only. Supporting-authority spans are accounted in the proposal and audit and
are not repeated here.

### Closed under schema 3 (4)

| # | Source span | Component | Representation |
|---|---|---|---|
| C-1 | Burning ` As an action,` [85,99] | `hazard.burning/self_extinguish` STRUCTURED | `ActionEconomyFact(ACTION)` |
| C-2 | Burning ` by giving yourself the Prone condition` [135,174] | same | `ConditionEffectFact(PRONE, APPLIES)` |
| C-3 | Falling ` A creature that falls into water or another liquid` [224,275] | `hazard.falling/surface_check` MIXED | prose binding, `contextual_applicability` |
| C-4 | Falling ` can use its Reaction` [275,296] | same | `ActionEconomyFact(REACTION)` |

`self_extinguish` honestly asserts less than the sentence states — it omits that the act extinguishes
the fire — but nothing it asserts is false, and the omitted half is carried by an unresolved span
that blocks publication regardless (O-3).

### Open (33)

Legend for **Missing structure**: names the exact absence in merged schema 3.

| # | Record | Exact source span | Referent | Proposed component | Schema 3 represents | Remains unresolved | Missing structure | Prose-bindable? | Outside authority |
|---|---|---|---|---|---|---|---|---|---|
| O-1 | `glossary.hazard` | `"Burning,"` … ` "Suffocation."` [0,10] [10,25] [25,36] [36,52] [56,71] — 5 spans | the five hazard records | *(none possible)* | nothing | the whole reference edge | **H-8** record-grain reference ownership | no — a resolvable reference is not irreducible prose | no |
| O-2 | `burning` | ` takes 1d4 Fire damage` + ` at the start of each of its turns.` | fire damage, per-turn | `burning_damage` | the amount and type, if the cadence could ride it | the cadence, hence the fact | **H-1** recurrence | no | no |
| O-3 | `burning` | ` you can extinguish fire on yourself` | this hazard ends | `self_extinguish` | the action and Prone costs (C-1/C-2) | that the hazard terminates | **H-2** effect/hazard termination | no | no |
| O-4 | `burning` | ` The fire also goes out` + ` if it is doused, submerged, or suffocated.` | termination on fictional events | *(none)* | nothing | consequence **and** trigger | **H-2**, then an open trigger | trigger yes, consequence no | no |
| O-5 | `dehydration` | `A creature requires an amount of water per day based on its size, as shown in the Water Needs per Day table.` + the 12 data cells — 13 spans | `CreatureSize` → volume/day | `water_requirement` | `CreatureSize` exists | the size→quantity mapping | **H-3** size-keyed quantity | no | no |
| O-6 | `dehydration` | ` A creature that drinks less than half the required water for a day` | consumed vs. half the table value | `dehydration_exhaustion` | nothing | the threshold | **H-4** quantity threshold over a table-derived value | no | no |
| O-7 | `dehydration` | ` gains 1 Exhaustion level` | Exhaustion level +1 | same | `ConditionLevelFact` exists | cannot be emitted: O-6 narrows it | **H-4** (blocker) | no | no |
| O-8 | `dehydration` | ` at the day's end.` | daily boundary | same | nothing | the cadence | **H-1** recurrence (day boundary) | no | no |
| O-9 | `dehydration` | ` Exhaustion caused by dehydration` | levels sourced from this record | same | nothing | source scoping | **H-5** cause-scoped condition levels | no | no |
| O-10 | `dehydration` | ` can't be removed until the creature drinks the full amount of water required for a day.` | removal gate on the table value | same | nothing | removal restriction + threshold | **H-4** + **H-6** removal restriction | no | no |
| O-11 | `dehydration` | `"Exhaustion."` [0,13] | `condition.exhaustion` — **accepted authority** | *(none possible)* | nothing | the reference edge | **H-8** | no | resolves into accepted `conditions-1`; supplied by the `prior=` merge |
| O-12 | `falling` | ` takes 1d6 Bludgeoning damage at the end of the fall` + ` for every 10 feet it fell,` | 1d6 per 10 ft fallen | `fall_damage` | the die, if scaling could ride it | the scaling basis | **H-7** distance-fallen scaling | no | no |
| O-13 | `falling` | ` to a maximum of 20d6.` | dice cap | same | nothing | the cap | **H-9** maximum damage dice | no | no |
| O-14 | `falling` | ` When the creature lands, it has the Prone condition` + ` unless it avoids taking any damage from the fall.` | Prone unless zero damage | `landing` | `ConditionEffectFact(PRONE, APPLIES)` exists | the exception, hence the fact | **H-10** applicability over a damage outcome | no — the operand is this rule's own damage | no |
| O-15 | `falling` | ` to make a DC 15 Strength (Athletics) or Dexterity (Acrobatics) check` | either of two skill checks | `surface_check` | the DC and one ability | the skill axis and the alternation | **H-11** skill axis + check alternatives | no | no |
| O-16 | `falling` | ` On a successful check,` + ` any damage resulting from the fall is halved.` | halve on success | same | nothing | outcome gating and the halving | **H-12** roll-outcome applicability + **H-13** damage modification | no | **see R-3 disposition, §6** |
| O-17 | `malnutrition` | `A creature needs an amount of food per day based on its size, as shown in the Food Needs per Day table.` + the 12 data cells — 13 spans | `CreatureSize` → mass/day | `food_requirement` | `CreatureSize` exists | the mapping | **H-3** | no | no |
| O-18 | `malnutrition` | ` A creature that eats but consumes less than half the required food for a day` | consumed vs. half the table value | `starvation_save` | nothing | the threshold | **H-4** | no | no |
| O-19 | `malnutrition` | ` must succeed on a DC 10 Constitution saving throw` | DC 10 Con save | same | `AbilityCheckFact(CON, FIXED, 10)` exists | cannot be emitted: O-18 narrows it. (Separately: the family cannot say *save* rather than *check* — noted in the sibling audit) | **H-4** (blocker) | no | no |
| O-20 | `malnutrition` | ` or gain 1 Exhaustion level` | level +1 on a failed save | same | `ConditionLevelFact` exists | the failure branch | **H-12** roll-outcome applicability | no | no |
| O-21 | `malnutrition` | ` at the day's end.` | daily boundary | same | nothing | the cadence | **H-1** | no | no |
| O-22 | `malnutrition` | ` A creature that eats nothing for 5 days` | 5 consecutive days at zero | `starvation_automatic` | nothing | the duration threshold | **H-14** elapsed-duration threshold | no | no |
| O-23 | `malnutrition` | ` automatically gains 1 Exhaustion level at the end of the fifth day` | level +1, automatic | same | `ConditionLevelFact` exists | cannot be emitted: O-22 narrows it | **H-14** (blocker) | no | no |
| O-24 | `malnutrition` | ` as well as an additional level at the end of each subsequent day without food.` | +1 per subsequent day | same | nothing | open-ended daily recurrence | **H-1** | no | no |
| O-25 | `malnutrition` | ` Exhaustion caused by malnutrition` | levels sourced from this record | `malnutrition_recovery` | nothing | source scoping | **H-5** | no | no |
| O-26 | `malnutrition` | ` can't be removed until the creature eats the full amount of food required for a day.` | removal gate on the table value | same | nothing | removal restriction + threshold | **H-4** + **H-6** | no | no |
| O-27 | `malnutrition` | `"Exhaustion."` [0,13] | `condition.exhaustion` — **accepted authority** | *(none possible)* | nothing | the reference edge | **H-8** | no | resolves into accepted `conditions-1` |
| O-28 | `suffocation` | `A creature can hold its breath for a number of minutes equal to 1 plus its Constitution modifier (minimum of 30 seconds) before suffocation begins.` | 1 + CON mod minutes, floor 30 s | `breath_duration` | nothing | derived quantity, floor, and the onset it gates | **H-15** ability-modifier-derived quantity with a floor | no | no |
| O-29 | `suffocation` | ` When a creature runs out of breath or is choking,` | either trigger | `suffocation_accrual` | nothing | a crisp trigger (O-28 expiry) **or** an open one (*"is choking"*) | **H-16** heterogeneous trigger set | *"is choking"* only — the pair is not | no |
| O-30 | `suffocation` | ` it gains 1 Exhaustion level` | level +1 | same | `ConditionLevelFact` exists | cannot be emitted: O-29 narrows, O-31 multiplies | **H-16** + **H-1** | no | no |
| O-31 | `suffocation` | ` at the end of each of its turns.` | per-turn boundary | same | nothing | the cadence | **H-1** | no | no |
| O-32 | `suffocation` | ` When a creature can breathe again,` | recovery trigger | `suffocation_recovery` | `RecoveryTrigger` exists but is rest-shaped | this trigger | **H-16** | borderline; not needed if H-16 lands | no |
| O-33 | `suffocation` | ` it removes all levels of Exhaustion it gained from suffocating.` | remove levels this hazard caused | same | `ConditionLevelFact(…, all_levels=True)` exists | the cause scoping | **H-5** | no | no |

---

## 5. Dependencies

**On accepted `conditions-1`:** two — O-11 and O-27, each a source-authored `"Exhaustion."` reference
resolving to `condition.exhaustion`. Both are satisfied by the `prior=` merge, which places the
accepted condition records in the same artifact. **This is the first cross-batch reference obligation
in the corpus and it validates the one-artifact-per-release design.** Neither is representable today
for an unrelated reason (H-8).

Every other Exhaustion interaction rides `ConditionKind.EXHAUSTION`, a closed enum member, and needs
no cross-record authority.

**On another unaccepted batch:** none.

**On authority outside the boundary:** none that blocks the ledger. See §6.

---

## 6. R-3 disposition — explicit

**R-3** (*rounding supplied by the governing rule rather than stated locally*) is adjacent to O-16:
Falling's *"any damage resulting from the fall is halved"* produces a fractional value, and unlike
Prone's *"(round down)"* the source does not restate the rounding locally. The governing rule is
`Rules Glossary > Rules Definitions > Round Down`, **outside this boundary and not imported.**

**Disposition: R-3 is not load-bearing for this ledger.** O-16 is already unresolved for two prior
and independent reasons — schema 3 has no roll-outcome applicability (**H-12**) and no structure for
modifying a stated damage amount (**H-13**). R-3 can only become live once both exist. When it does,
the honest resolution is a rounding field left **unpopulated** for Falling — the projection records
what *this* record states, and the `Round Down` record states its own rule in its own batch — rather
than a fact claiming provenance over a span this batch never accounted. That choice belongs to
**H-13's** design and is named in the closure checkpoint; it is not an import and not an Owner
Decision.

**R-1, R-2, R-4, R-5, R-6, R-7: none is load-bearing.** Verified against the regenerated ledger — the
batch contains no counterpart establishment, no creature-to-creature size comparison (the size-keyed
tables key a quantity to the subject's *own* size, which is not a comparison at all), no movement cost
of any form, and no movement-capability predicate.

---

## 7. What this ledger does not claim

* It is **not** an acceptance recommendation. 66 unresolved spans block publication, correctly.
* The 33-obligation grouping is **my derivation** from the 66 unresolved spans; the spans, counts,
  dispositions, and validator results are **verified output** of the run.
* The refusal to emit six facts is a **design judgment** under the rule in §2, applied evenly and
  stated so a reviewer can reject it span by span. Rejecting it moves spans from unresolved to
  substantive; it does not change what schema 3 can express.
