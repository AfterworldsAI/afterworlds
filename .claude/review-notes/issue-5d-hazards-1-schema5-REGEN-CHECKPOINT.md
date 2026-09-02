# CRD Issue 5d — `hazards-1` regenerated under representation schema 5

**Status: SEMANTIC-REVIEW HANDOFF. Not an acceptance recommendation.**

Nothing here is accepted, published, activated, or retired. `accept_proposal` is never called,
`oracles/` is read and asserted byte-unchanged, and `actions-1` is not begun. The rejected schema-4
proposal `6277ff73…a259` was not imported, edited, translated, restamped, cloned, or read as
generator input; it is compared against only after the fact, as a diagnostic.

**Zero validator findings is necessary and explicitly insufficient.** The gate proves the artifact is
*admissible*. It cannot prove the representation is *true of the source*, and the four questions in
§6 are exactly the ones no validator can answer. Two disclosed limits (§5) need a ruling.

| | |
|---|---|
| Proposal identity | `f7ce449174102f1cdb7087a806d1f594add384282e54fb17181c4f5168c40417` |
| Rejected predecessor | `6277ff735e0e47b3337f2c3736ca7922864b1cde9a3c286b3aee48ee461ba259` — **differs**, asserted |
| Schema | `5d-representation-schema-5` / `2803840899363988cc2f67e0d9f310d9baffe394d52ca0919d11388bcd7f4c40` |
| Policy | `5d-semantic-policy-1` / `e6363968d6ee8ec288e6c7e3382907a1afd8bf2aad0b18e153aec439b5aa9454` |
| Release | `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` / `5.2.1-corpus.36b786d8-fa2` |
| Accepted artifact | `aa59c69d…6e8a1a` before **and** after the run, both recorded in the audit |

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
| determinism | a clean rerun in a separate process reproduces identical artifact bytes and the same identity |

**Unresolved references, enumerated exactly.** Standalone, this batch cites one record it does not
define, twice: `hazard.dehydration → condition.exhaustion` and
`hazard.malnutrition → condition.exhaustion`. The claim asserted is *set equality* against that pair,
not "only Exhaustion appears". Both resolve into accepted `conditions-1` authority, and the merged
gate reports nothing at all.

## 5. Disclosed limits — these need a ruling

**D-3 — Falling's moment of effect.** *"at the end of the fall"* and *"When the creature lands"* state
**when** a one-shot effect occurs. `Recurrence` states repetition; `Phase` states only `WHILE_ACTIVE`
and `ON_END` relative to an effect's own life. No declared element carries a moment. Both clauses are
SUBSTANTIVE and both are claimed PRIMARY *inside the span of the fact whose timing they state* — so
neither is omitted and neither is demoted to supporting authority, and both are recorded in the audit
with exact ranges and text under `falling_timing_spans`. They were deliberately **not** split into
their own spans: a split needs a claimant that states a moment, and assigning one that does not is
the role-chosen-to-satisfy-the-validator move the H-16 finding condemned. *If the reviewer wants the
timing typed, that is a schema question, not a re-cut of this batch.*

**D-4 — Burning's required physical performance.** *"and rolling on the ground"* is half of a compound
required performance whose other half — the Prone condition — is typed. Rolling on the ground has no
typed family. It is bound as affirmative governing prose under `contextual_applicability`: the clause
conditions whether the extinguishing takes effect, which is applicability, and its operand is fiction
the projection cannot enumerate. The reason code was chosen against the catalog's literal wording,
not for whichever code validated: `subjective_judgment` would claim a judgement call the source does
not ask for, and `fiction_dependent_consequence` would misdescribe a consequence that *is* typed. The
typed consequence is stated once, beside the binding, and is not restated inside the binding's span.

## 6. What a semantic reviewer should decide

The validators cannot answer any of these.

1. **Is `fall_damage` the right grain?** Damage and landing are one rule about one fall here, with the
   exception scoped to the landing fact. The alternative — two components — puts the exception on a
   component whose only fact it governs anyway, and separates two halves of one sentence.
2. **Is the sustained zero band a faithful reading of *"eats nothing for 5 days … as well as an
   additional level at the end of each subsequent day without food"*?** The design leans on
   `applies_when`'s declared meaning (*when this component applies at all*) composed with `recurs`.
   That inference is stated so it can be checked rather than trusted.
3. **Is *" and rolling on the ground."* substantive?** It is classified as governing prose here. If it
   is commentary, one span moves back and the prose binding goes.
4. **Are D-3 and D-4 acceptable as disclosed limits, or does either need schema work?** Neither was
   solved by an unreviewed schema patch, and neither should be.

## 7. Stop conditions honoured

`accept_proposal` not called · accepted authority not modified, and its SHA-256 asserted identical
before and after · nothing published, activated, or retired · branch not merged · `actions-1` not
begun · the rejected proposal's payload not used as input · no schema, validator, or reason code
changed by this work — `src/` is untouched on this branch.
