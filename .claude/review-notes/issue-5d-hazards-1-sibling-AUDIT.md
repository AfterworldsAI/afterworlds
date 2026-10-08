# CRD Issue 5d — `hazards-1` bounded sibling audit

**Scope of the audit.** All **twenty** spans the retained schema-1 proposal
(`issue-5d-batch-hazards-1-PROPOSAL.json`, identity
`4c01fe9c93e286b1b75bf6c256179f9734665fa7c3e3216abb56ff7121fdcee8`) classified `UNRESOLVED`,
re-examined against merged representation schema 3, plus a corpus-wide prevalence sweep of every
structure the regeneration would need.

**Trigger.** Not a repeated-defect trigger. This audit is required by the regeneration task, and it
controls scope rather than expanding it.

**Defect family.** *Mechanical obligations whose blocking structure was mis-identified because the
span was classified under schema 1 and labelled by its most visible clause rather than by the
structure that actually blocks it.*

**Derived at** `origin/main` = `HEAD` = `319e61c`. Retained schema-1 artifacts verified byte-identical
after the run (`issue-5d-batch-hazards-1-PROPOSAL.json` `68bc4700…`, `-audit.json` `3dfeaca5…`,
`-generator.py` `ed11184c…`).

---

## 1. Disposition of all twenty

`patched` = re-cut and re-classified in the regeneration · `already safe` = the schema-1 call survives ·
`reclassified` = the disposition or the named blocker changed · `out of scope` / `Known Unknown` /
`owner decision needed` as defined by `CLAUDE.md`.

| # | Record | Schema-1 unresolved span | Schema-1 named blocker | Regenerated disposition | Ledger | Verdict |
|--:|---|---|---|---|---|---|
| 1 | burning | ` at the start of each of its turns.` | recurrence | still unresolved; **and the damage fact it qualifies is now also refused** — the cadence multiplies it | O-2 | **reclassified** (widened) |
| 2 | burning | ` you can extinguish fire on yourself` | hazard termination | still unresolved, same blocker | O-3 | already safe |
| 3 | burning | ` The fire also goes out if it is doused, submerged, or suffocated.` | disjunctive exit triggers | **re-cut into two spans**; the blocker is the *consequence* (no termination family), not the trigger. Trigger openness is secondary and unreachable | O-4 | **reclassified** |
| 4 | dehydration | `A creature requires an amount of water per day…table.` | size-keyed quantity | still unresolved; **12 table-cell spans joined the same obligation** | O-5 | **reclassified** (widened) |
| 5 | dehydration | ` A creature that drinks less than half the required water for a day` | consumption-threshold trigger | still unresolved. **Not an open referent** — the operand is the in-batch table | O-6 | **reclassified** |
| 6 | dehydration | ` gains 1 Exhaustion level at the day's end.` | level accrual | **re-cut into two**; `ConditionLevelFact` exists, so the true blockers are the narrowing threshold and the day cadence | O-7, O-8 | **reclassified** |
| 7 | dehydration | ` Exhaustion caused by dehydration can't be removed until…` | removal restriction | **re-cut into two**; the first blocker is *cause scoping*, which the schema-1 label missed entirely | O-9, O-10 | **reclassified** |
| 8 | falling | ` at the end of the fall for every 10 feet it fell,` | distance-scaled damage | still unresolved; **the 1d6 damage fact is now also refused** — scaling multiplies it | O-12 | **reclassified** (widened) |
| 9 | falling | ` to a maximum of 20d6.` | damage cap | still unresolved, same blocker | O-13 | already safe |
| 10 | falling | ` unless it avoids taking any damage from the fall.` | negative applicability | still unresolved; **the Prone fact it qualifies is now also refused**. Blocker renamed: applicability over a *damage outcome*, which the broad sweep shows is well-evidenced | O-14 | **reclassified** (widened) |
| 11 | falling | ` to make a DC 15 Strength (Athletics) or Dexterity (Acrobatics) check to hit the surface head or feet first.` | disjunction of skill checks | **re-cut into two**; the trailing purpose clause is supporting authority owned by the component, not part of the gap | O-15 | **reclassified** |
| 12 | falling | ` On a successful check, any damage resulting from the fall is halved.` | outcome-conditional halving | **re-cut into two**; two distinct structures — roll-outcome applicability and damage modification. **R-3 adjacency identified here** | O-16 | **reclassified** |
| 13 | malnutrition | `A creature needs an amount of food per day…table.` | size-keyed quantity | as #4; 12 cell spans joined | O-17 | **reclassified** (widened) |
| 14 | malnutrition | ` A creature that eats but consumes less than half the required food for a day` | consumption threshold | as #5; **and the DC 10 save it narrows is now refused** | O-18, O-19 | **reclassified** (widened) |
| 15 | malnutrition | ` or gain 1 Exhaustion level at the day's end.` | failure-branch accrual | **re-cut into two**; blockers are roll-outcome applicability and the day cadence | O-20, O-21 | **reclassified** |
| 16 | malnutrition | ` A creature that eats nothing for 5 days automatically gains…each subsequent day without food.` | duration threshold + recurrence | **re-cut into three**; elapsed-duration threshold, the gain it narrows, and an open-ended daily recurrence | O-22, O-23, O-24 | **reclassified** |
| 17 | malnutrition | ` Exhaustion caused by malnutrition can't be removed until…` | removal restriction | as #7; cause scoping surfaced | O-25, O-26 | **reclassified** |
| 18 | suffocation | `A creature can hold its breath…before suffocation begins.` | derived duration with a floor | still unresolved, same blocker | O-28 | already safe |
| 19 | suffocation | ` When a creature runs out of breath or is choking, it gains 1 Exhaustion level at the end of each of its turns.` | recurring level accrual | **re-cut into three**; heterogeneous trigger, the narrowed gain, the cadence | O-29, O-30, O-31 | **reclassified** |
| 20 | suffocation | ` When a creature can breathe again, it removes all levels of Exhaustion it gained from suffocating.` | conditional full removal | **re-cut into two**; `ConditionLevelFact(all_levels=True)` exists — the real blocker is cause scoping, so a bare emission would remove dehydration's levels too | O-32, O-33 | **reclassified** |

**Totals: 3 `already safe`, 17 `reclassified`, 0 `out of scope`, 0 `Known Unknown`, 1
`owner decision needed` (§4, arising from the audit rather than from any single span).**

Nothing was silently fixed. Nothing outside the six-record boundary was inspected as batch content;
everything outside it was read only as sibling evidence, which is how every prior sweep in this issue
has worked.

**Two findings the schema-1 labels missed entirely**, both surfaced only by re-cutting to obligations:

1. **Cause-scoped condition levels** (#7, #17, #20). Three clauses scope Exhaustion to the hazard that
   caused it. `ConditionLevelFact`'s merged docstring cites Suffocation's *"removes all levels of
   Exhaustion"* as its motivating example, yet the family has no cause scoping — so the very clause it
   names cannot be represented without asserting something false.
2. **Six facts that the schema-1 proposal emitted are false as emitted** (#1, #8, #10, #14, #6, #20).
   The proposal reported 6/0/0 structured components with 7 facts; under the emission rule in the
   ledger §2, three of those facts survive and four do not.

---

## 2. Corpus-wide prevalence sweep

Run over the 28,109 represented leaves of the bound release. Two passes: a narrow lexical pass, then a
**broad re-sweep of every candidate the narrow pass called singular**, because a narrow regex
under-reports and a singular verdict is the one that decides whether a structure may be minted at all.
The broad pass reversed one verdict and confirmed five.

| Addition | Narrow | **Broad** | Distinct rules / sections after de-duplicating restatements | Verdict |
|---|---|---|---|---|
| **H-1** recurrence at a turn boundary | 88 / 7 | — | 88 / 7 | **PASS** |
| **H-1** recurrence at a day boundary | 2 / 1 | — | 2 / 1 — both in this batch | rides H-1's turn evidence; the boundary vocabulary widens, the structure does not |
| **H-2** effect / hazard termination | 144 / 5 | — | broad lexical, not de-duplicated; clearly ≫ 2 / 2 | **PASS** |
| **H-3** size-keyed quantity | 5 / 2 | — | Carrying Capacity, Water Needs, Food Needs, Oil of Etherealness/Slipperiness | **PASS** |
| **H-4** threshold against a table-required quantity | 2 / 1 | **2 / 1** | both in this batch. Carrying Capacity is a *capacity*, not a consumption threshold | **FAIL** |
| **H-5** cause-scoped condition levels | 3 / 1 | 15 / 2 → **3 / 1** | the Monsters A–Z hits are *"Temporary Hit Points gained from the spell"* — a different mechanic, and one duplicated leaf | **FAIL** |
| **H-6** removal blocked until a condition is met | 2 / 1 | 55 / 6 → **2 / 1** | the broad hits are *durations* (*"until the spell ends"*), not restrictions on an already-applied condition | **FAIL** |
| **H-7** distance-scaled damage | 3 / 3 | — | Falling, Wall of Thorns, Water Elemental | **PASS** |
| **H-8** record-grain reference ownership | 91 sites / 1 | — | 91 `See also` blocks. Structural, not a fact vocabulary — see note below | **PASS** |
| **H-9** maximum damage dice | 1 / 1 | **1 / 1** | Falling only, confirmed under a broadened pattern | **FAIL** |
| **H-10** applicability over a damage outcome | 1 / 1 | **25 / 6** | *"ends early … if it takes any damage"*, *"It wakes up if it takes any damage"*, *"the creature takes no damage from the fall"* | **PASS — verdict reversed by the broad sweep** |
| **H-11** skill axis on a roll | 128 / 11 | — | overwhelming | **PASS** |
| **H-11** alternation of two same-shaped checks | 3 / 2 | — | Falling, Grappling, Rope of Entanglement | **PASS** |
| **H-12** roll-outcome applicability | 112 / 9 | — | overwhelming | **PASS** |
| **H-13** stated modification of a damage amount | 2 / 2 | — | Falling's halving; Resistance/Vulnerability halving/doubling in *Playing the Game* | **PASS** |
| **H-14** elapsed-duration threshold | 24 / 7 | 19 / 7 | **both passes are dominated by *"on the same turn"* noise; neither validates the actual shape** | **UNVALIDATED** |
| **H-15** quantity from an ability modifier with a floor | 17 / 3 | — | Bardic Inspiration, Turn Undead, Hit Dice, Suffocation, and others | **PASS** |
| **H-16** heterogeneous state trigger | 1 / 1 | 2 / 2 → **1 / 1** | the Magic Items hit is *"runs out of charges"* — resource depletion, a different mechanic | **FAIL** |

**On H-8 and the admission standard.** The ≥2-rules/≥2-sections bar was devised for *fact
vocabularies*, where a one-member enum named after one clause is the hazard it guards against. H-8 is
not a vocabulary; it is making one existing field nullable so a reference can be owned by the record
that authored it. Its 91 `See also` sites all sit in the Rules Glossary because that is where the
source puts cross-reference blocks — a fact about the source's layout, not about the structure's
generality. Recorded so the bar is not applied where it was never meant to bite.

---

## 3. What the sweep means for zero

Building **every one of the ten PASS additions** closes 18 of the 33 open obligations, covering
**51 of the 66 unresolved spans**. Fifteen spans remain, blocked by the five FAIL families plus the one
unvalidated family:

| Blocked obligation | Blocking family | Verdict |
|---|---|---|
| O-6, O-18 consumption thresholds | H-4 | FAIL 2/1 |
| O-7, O-19 the facts those thresholds narrow | H-4 | FAIL |
| O-9, O-25, O-33 cause-scoped levels | H-5 | FAIL 3/1 |
| O-10, O-26 removal restrictions | H-4 + H-6 | FAIL |
| O-13 the 20d6 cap | H-9 | FAIL 1/1 |
| O-29, O-30, O-32 suffocation triggers | H-16 | FAIL 1/1 |
| O-22, O-23 the five-day threshold | H-14 | UNVALIDATED |

**`hazards-1` therefore reaches 66 → 15 unresolved under a fully built ten-addition schema 4. It does
not reach zero.**

The blocker is **not** an out-of-boundary authority dependency, and **not** a Boolean predicate
language. It is an evidence shortfall: five structures are mechanically crisp and would be
representable, but the corpus states each of them once or twice, in one section — because the SRD
contains exactly one falling rule, one suffocation rule, and two consumption-threshold rules. **No
later batch can supply the missing siblings, because the siblings do not exist.**

---

## 4. Owner Decision — one, and it is not batch selection

The audit surfaces a conflict between two authorities that cannot both hold for this corpus.

* **ADR-005d Decision 1 and #137 *Delivery and Engineering Discretion*** make *complete mechanically
  substantive accounting* explicitly **non-discretionary**. Unresolved spans block publication.
* **ADR-005d Decision 4** states the actual admission rule: *"A new mechanical family requires a typed
  schema and tests **or** an honest prose-bound classification."* It imposes **no** sibling-count bar.
* **The ≥2-distinct-rules / ≥2-top-level-sections bar** that produced the five FAIL verdicts above
  appears nowhere in the ADR or the issue. It was introduced by the schema-closure checkpoints as
  engineering discipline against clause-specific vocabulary, and it has governed the shape of schemas
  2 and 3.

For a mechanic that is **crisp, unique in the corpus, and not affirmatively irreducible** — Falling's
`to a maximum of 20d6` is the cleanest instance — the three cannot be satisfied together. It cannot be
typed (the bar refuses it), it cannot be prose-bound (that would be the backlog state #137 forbids),
and it cannot stay unresolved (that blocks publication permanently). `CLAUDE.md` requires this be
surfaced rather than resolved in code.

**The smallest exact question:**

> When the corpus states a mechanically crisp, non-irreducible mechanic exactly once, does the
> self-imposed ≥2-rules/≥2-sections admission bar yield to ADR-005d Decision 4, permitting a typed
> structure on single-instance evidence?

**Credible options:**

| | Option | Consequence |
|---|---|---|
| **A** | **The bar yields for crisp single instances.** ADR-005d Decision 4 governs: type it, with a narrow field on an existing family wherever possible rather than a new vocabulary. | `hazards-1` reaches zero. Admits H-4, H-5, H-6, H-9, H-16 as fields/variants. Risk: schema grows one structure per unique mechanic; mitigated by preferring nullable fields on existing families over new enums. |
| **B** | **The bar holds; unique crisp mechanics stay `UNRESOLVED` until full-corpus accounting.** | `hazards-1` cannot be accepted now, and neither can any batch containing a unique mechanic. 5d publishes only at the very end, if ever. Honest but may never terminate. |
| **C** | **The bar holds, and the ADR is amended** to add a closed irreducibility reason for *"crisp but unique"*, prose-binding such mechanics. | Contradicts #137's rule that `PROSE_BOUND` is never a backlog state, and would need an explicit ADR amendment. Recorded for completeness; not recommended. |

**Recommendation: A**, because ADR-005d Decision 4 is accepted authority and the sibling bar is not,
and because the ADR's own guard — *"a typed schema and tests"* — already prevents the abuse the bar was
invented to stop. This is a reconciliation between accepted authority and self-imposed discipline, so
it may be an engineering call rather than a product decision; it is raised here because reversing the
bar changes the character of schemas 2 and 3, which were shaped by it.

**Not an Owner Decision, and not raised as one:** batch selection, span cutting, component boundaries,
the emission rule, the R-3 disposition, or which of the ten PASS additions to build.
