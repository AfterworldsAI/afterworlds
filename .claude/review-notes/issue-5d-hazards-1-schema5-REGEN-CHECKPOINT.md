# CRD Issue 5d — `hazards-1` regenerated under representation schema 5

**Status: SEMANTIC REVIEW COMPLETE. Ready for a separate Owner-acceptance step, which this
work does not perform.**

`hazards-1` has passed semantic review. Every question this batch raised is resolved — D-3 by Owner
Decision 2026-09-02, D-4 and Z-1 as correctly represented (§5) — and **no semantic question and no
disclosed representation limit remains**. Acceptance is a distinct decision and a distinct action:
nothing here is accepted, published, activated, retired, or merged, `accept_proposal` is never
called, `oracles/` is read and asserted byte-unchanged, and `actions-1` is not begun. The rejected
schema-4 proposal `6277ff73…a259` was not imported, edited, translated, restamped, cloned, or read as
generator input; it is compared against only after the fact, as a diagnostic.

**Zero validator findings was never the argument.** The gate proves the artifact is *admissible*; it
cannot prove the representation is *true of the source*. What closes §6 is a reading of the bound
source per record, recorded and executed, not a green run.

| | |
|---|---|
| Proposal identity | `f7ce449174102f1cdb7087a806d1f594add384282e54fb17181c4f5168c40417` |
| Rejected predecessor | `6277ff735e0e47b3337f2c3736ca7922864b1cde9a3c286b3aee48ee461ba259` — **differs**, asserted |
| Schema | `5d-representation-schema-5` / `2803840899363988cc2f67e0d9f310d9baffe394d52ca0919d11388bcd7f4c40` |
| Policy | `5d-semantic-policy-1` / `e6363968d6ee8ec288e6c7e3382907a1afd8bf2aad0b18e153aec439b5aa9454` |
| Release | `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` / `5.2.1-corpus.36b786d8-fa2` |
| Accepted artifact | `aa59c69d…6e8a1a` before **and** after the run, pinned as a literal the run asserts |
| Open questions / disclosed limits | **none** — asserted empty by the generator |
| Repository root | derived from the generator's own location, `Path(__file__).resolve().parents[2]` — no hard-coded path |

---

## 1. Boundary, re-derived rather than asserted

The source's own entry class: the `[Hazard]`-tagged entries under Rules Definitions, plus the
umbrella `Hazard` glossary rule whose *See also* names exactly those five. Both halves are derived by
scanning the bound ledger and then cross-checked against the umbrella's own printed text, so a hazard
added or renamed upstream fails the run rather than silently dropping out of the batch.

| canary | derived | recorded |
|---|---|---|
| records | 6 | 6 |
| represented 5c leaves | 43 | 43 |
| policy exclusions | 0 | 0 |
| classification spans | 96 | 96 |

All four reproduce. The span count is not a canary the generator targets — it is what the run-time
cut produces — and it reproducing is evidence the source has not moved under the cut.

## 2. Counts, and where they moved

| | schema 4 (rejected) | schema 5 | why |
|---|---|---|---|
| spans / provenance edges | 96 / 96 | **96 / 96** | the source cut is unchanged; the corrections are about what *claims* each span |
| substantive / supporting | 64 / 32 | **65 / 31** | one span moved: *" and rolling on the ground."* is governing prose, not commentary |
| components | 17 | **15** | `landing` merged into `fall_damage`; `fall_halving` into `surface_check` |
| facts | 22 | **21** | the Falling `ScalingFact` is gone; `DamageFact.per` carries the interval instead |
| prose bindings | 4 | **5** | the new `self_extinguish` binding |
| references / relationships | 7 / 0 | **7 / 0** | unchanged |

Two further spans changed claimant kind from a component-scope claim to a fact-scope qualifier:
*" unless it avoids taking any damage from the fall."* and *" On a successful check,"*.

**Read the drop in components and facts as consolidation, not loss.** Nothing the source states was
dropped: every one of the 96 spans still has exactly one honest claimant, and the 36 obligations in
`obligation_closure` are each *executed* against the emitted draft rather than asserted in prose.

## 3. Per-record semantic shape

**`glossary.hazard`** — no components, and honestly cannot acquire one: *"A hazard is an environmental
danger."* states a category, not a mechanic. Five record-owned references, one per hazard.

**`hazard.burning`** — `burning_damage` (1d4 Fire, recurring at the start of the subject's turns);
`self_extinguish`, one **MIXED** component holding the Action cost, the Prone application and the
fire's termination as typed authority, with *" and rolling on the ground."* bound as affirmative
governing prose beside them; `ambient_extinguish` (the same termination fact from a genuinely
different rule, under its own prose-bound trigger).

**`hazard.dehydration`** — the printed six-row water table; the accrual, whose band is
*"drinks less than half"* — upper ½ exclusive, **no lower bound**, because drinking nothing is inside
this rule — recurring at each day's end; the cause-scoped removal restriction, gated on the band
*"the full amount required for a day"* (lower 1 inclusive, unbounded above).

**`hazard.falling`** — `fall_damage` holds the damage and the landing together, as one coherent rule
about one fall: **one** `DamageFact`, 1d6 Bludgeoning **per** 10 feet fallen, capped at 20d6, with no
`ScalingFact` anywhere in the batch; and the Prone application, whose *"unless it avoids taking any
damage"* exception is qualified onto **that fact alone** so it cannot gate the damage. `surface_check`
is MIXED and holds the Reaction cost, the DC 15 Strength (Athletics) / Dexterity (Acrobatics)
**ability check** with both alternatives themselves ability checks, and the halving — qualified
`ROLL_OUTCOME(SUCCESS)` onto the halving fact, in the same scope as the check it answers to.
`rounding` stays unset: R-3, *Round Down*, is its own Rules Definitions entry outside this boundary,
checked in the artifact rather than assumed.

**`hazard.malnutrition`** — the printed six-row food table; `starvation_save`, whose band is
*"eats **but** consumes less than half"* — lower 0 **exclusive**, upper ½ exclusive — holding the
DC 10 Constitution **saving throw** (no skill, no alternatives) with the Exhaustion gain qualified on
failure of that same in-scope save, recurring at each day's end; `starvation_automatic`, one
zero-food-governed recurring component whose band is the point 0..0 inclusive **sustained at least 5
days**, recurring at each day's end — which is how the fifth day and every subsequent day without
food are stated once, and why resuming food makes the component inapplicable rather than needing a
stated stop; the malnutrition-specific removal restriction, distinct from Dehydration's by its band's
quantity.

**`hazard.suffocation`** — `breath_duration` (1 + Constitution modifier minutes, floor 30 seconds);
`suffocation_accrual`, H-16 Shape B preserved: **one** MIXED component carrying the whole disjunctive
trigger *" When a creature runs out of breath or is choking,"* as affirmative governing prose, with
the Exhaustion gain stated **once** and the end-of-turn recurrence stated **once** at component
scope — no split into siblings, no duplicated consequence; `suffocation_recovery`, the cause-scoped
removal of the levels this record caused, under its own prose-bound trigger.

The H-16 trigger boundary was **derived** from the bound leaf at run time and then asserted equal to
`[147,197)`, with a failure message that says the bound source moved. It was not copied.

## 4. What the run proves

| claim | result |
|---|---|
| partition, per leaf | 0 findings, **and** each leaf's spans concatenate back to the leaf byte for byte |
| reason codes | 0 |
| draft shape, held-authority shape | 0 / 0 |
| schema-5 component rules (damage composition, roll outcome), run per component | 0 |
| declared schema binding | 0 |
| representation gate, **standalone** | 2 — exactly the two cross-batch citations, set-equal to the enumerated pair |
| representation gate, **merged with accepted `conditions-1`** | **0** |
| wire round trip (`representation_payload` → `_representation`) | identical |
| succession | `5d-lift-schema-3-to-4` → `5d-lift-schema-4-to-5`, 6 collections verified at **each** step |
| six-collection overlap with accepted authority | 0 / 0 / 0 / 0 / 0 / 0 |
| zero movement of accepted elements | all six collections: the merge keeps every prior element as a byte-identical prefix, every prior element still serializes to the exact same payload, and the merged counts are prior + new with nothing dropped or coalesced |
| no component holds both facts and options | none |
| no `ScalingFact` anywhere | none |
| no detached or ambiguous roll outcome | none; each roll-outcome scope establishes exactly one roll |
| ownership | 65 substantive spans, each with exactly one primary claimant; 0 supporting spans carrying a primary claim; 0 spans unclaimed |
| obligations | 36 closed, 0 open — each executed against the draft |
| determinism | a clean rerun in a separate process reproduces identical artifact bytes and the same identity, and both artifacts are byte-stable across processes with different string-hash seeds |

**Unresolved references, enumerated exactly.** Standalone, this batch cites one record it does not
define, twice: `hazard.dehydration → condition.exhaustion` and
`hazard.malnutrition → condition.exhaustion`. The claim asserted is *set equality* against that pair,
not "only Exhaustion appears". Both resolve into accepted `conditions-1` authority, and the merged
gate reports nothing at all.

## 5a. D-3, Falling's timing — **RESOLVED**, Owner Decision 2026-09-02

> A normal fall finishes during the turn in which it begins. Resolve its damage and landing
> immediately. Only delay completion when a specific rule provides a falling rate or duration.

**Grounds.** The SRD's general Falling rule gives no speed, no distance per round and no duration.
Where the SRD intends a slower descent it says so explicitly — Ring of Feather Falling prints 60 feet
per round. No general fall-duration calculation and no real-world physics apply.

**What the phrases mean.** *"at the end of the fall"* and *"When the creature lands"* describe the
**immediate completion of the fall**, not a delayed event requiring a new timing structure. The
question that was open — whether a moment-of-effect axis was needed — is answered: it is not.

**What this changes in the batch: nothing.** The ruling changes review documentation, not the
proposed mechanical authority, and the proposal is byte-identical with its identity unmoved.

| held after the ruling | state |
|---|---|
| both phrases | SUBSTANTIVE, exact source accounting preserved — `[21,73)` and `[122,174)`, each claimed PRIMARY inside the span of the fact it belongs to, recorded in `falling_timing_spans` |
| `fall_damage` | one component holding the falling damage **and** the landing consequence |
| the Prone result | still dependent on whether falling damage occurred, via the `DAMAGE_OUTCOME` qualifier on the landing fact alone |
| structure added for an ordinary fall | **none** — no schema field, prose binding, recurrence, duration, falling-speed rule, or physics calculation |

Each row is executed as an assertion in the generator and recorded in the audit under
`d3_resolution.checked`, so the ruling is checked rather than described.

## 5b. D-4, Burning's required physical performance — **RESOLVED**, correctly represented

Never actually an open question: the governing review instructions had already decided all three
parts of it, and the proposal is exactly that shape.

| required | as built |
|---|---|
| `self_extinguish` is one MIXED component | one component, `MIXED`, reason `contextual_applicability` |
| *" and rolling on the ground."* is substantive governing rule text | SUBSTANTIVE, `[174,201)`, claimed PRIMARY by the component's single prose binding |
| the consequence is stated once | exactly one `EffectTerminationFact`, and the bound span restates no consequence |
| the rest is typed | `ActionEconomyFact`, `ConditionEffectFact`, `EffectTerminationFact` |

The reason code was chosen against the catalog's literal wording rather than for whichever code
validated: the clause conditions whether the extinguishing takes effect, which is applicability, over
an act the projection cannot enumerate. `subjective_judgment` would claim a judgement call the source
does not ask for, and `fiction_dependent_consequence` would misdescribe a consequence that *is*
typed. Every row above is executed as an assertion and recorded under `d4_resolution.checked`. **No
schema change and no Owner decision is outstanding.**

## 5c. Z-1, the sustained zero-food rule — **RESOLVED**, correctly represented

The required reading, and where each part lives:

| required reading | as built |
|---|---|
| *"eats nothing for 5 days"* is continuous zero consumption for **at least** five days | `ConsumptionBand(FOOD, 0 ≤ x ≤ 0, sustained_at_least=5 DAY)` as `starvation_automatic.applies_when` |
| Exhaustion is gained at the end of the fifth foodless day | that band composed with `Recurrence(END_OF_DAY)` |
| additional Exhaustion at the end of each following foodless day | the same recurrence — one `ConditionLevelFact`, not a second rule |
| the recurrence stays conditional on continued zero consumption | `applies_when` says *when this component applies at all*, so the cadence runs only while the band holds |
| eating any food ends that applicability | leaving the band makes the component inapplicable; no stop condition is stated, and none is needed |

No elapsed clock survives anywhere in the batch — asserted — so *"five days have passed"*, which is
true of every creature alive on day five, is not what this rule says. Recorded under
`z1_resolution.checked`.

## 6. Review disposition

**No semantic questions remain, and no disclosed representation limits remain.** The three the batch
raised are closed:

| id | where | disposition |
|---|---|---|
| D-3 | `hazard.falling/fall_damage` | resolved — Owner Decision 2026-09-02, immediate-fall ruling |
| D-4 | `hazard.burning/self_extinguish` | resolved — correctly represented |
| Z-1 | `hazard.malnutrition/starvation_automatic` | resolved — correctly represented |

The generator asserts that the audit's disclosed-limit list and open-question list are both empty,
that all three carry a resolved status, that the proposal identity is
`f7ce4491…c40417`, and that the accepted artifact's digest is `aa59c69d…6e8a1a` before and after.

`hazards-1` has passed semantic review and is ready for a **separate Owner-acceptance step**. This
work does not take it: acceptance remains a distinct decision and a distinct action.

## 7. Stop conditions honoured

`accept_proposal` not called · accepted authority not modified, and its SHA-256 asserted identical
before and after · nothing published, activated, or retired · branch not merged · `actions-1` not
begun · the rejected proposal's payload not used as input · no schema, validator, or reason code
changed by this work — `src/` is untouched on this branch.
