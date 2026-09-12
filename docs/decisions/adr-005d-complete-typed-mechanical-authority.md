# ADR-005d — Complete Typed Mechanical Authority and Deterministic Rules-Package Binding

**Issue:** CRD Issue 5d  
**Date:** 2026-07-30  
**Status:** Accepted — finalized by Owner 2026-07-30; amended by Owner Decision 2026-07-30 (PR #138
review) so the effective runtime binding also carries an immutable override-set identity, and clarified
in the same review so the contents that identity names are retained as immutable, provenance-exact replay
evidence; further amended by Owner Decision 2026-08-08 so a runtime prose-bound override may resolve
through a first-class authored-authority overlay distinct from 5c source prose, replacing this ADR's
blanket prohibition on a second prose store with the narrower invariant that there is no duplicated store
for what the SRD source says; further amended by Owner Decision 2026-08-09 so that overlay's effective
`handling` is a final classification of each component's own surviving facts and prose, derived once at
final assembly for every component regardless of which override family supplied its authority or which
operation resolved last, rather than remembered as a sticky promotion, correcting this ADR's prior text to
the contrary  
**Amends/clarifies:** ADR-005c, ADR-0007, ADR-015, ADR-018

---

## Context

ADR-005c established the Rules Authority repair sequence:

```text
5c source-corpus integrity
→ 5d typed mechanical authority and deterministic binding
→ 2b package-bound character state
→ 15c repaired bounded-d20 execution and certification
```

CRD Issue 5c now publishes the complete authoritative SRD 5.2.1 source corpus with deterministic
identity, exact source accounting, provenance, persisted-state verification, and a publication gate. It
deliberately does not decide which text is mechanically substantive or produce typed mechanical
authority.

Discovery against the real 5c pipeline found:

- 28,109 represented leaves in the measured release, including rules, headings, legal text, examples,
  explanatory prose, and other non-mechanical material;
- 2,422 `ENTRY` containers, whose geometry-derived boundaries are reliable for some categories but not
  for composite stat blocks, non-entry general rules, nested creature records, or many tables;
- 683 logical tables, including stat-block prose fragmented across cells;
- 1,533 represented leaves with at least two lexical mechanical-signal families;
- multiple mechanical facts spanning several leaves/table cells; and
- 203 colliding names among 1,893 distinct container names.

Therefore:

1. 5c `REPRESENTED` cannot mean "mechanically substantive."
2. One record per `ENTRY` and one component per leaf are unsound.
3. Reference coverage alone cannot prove faithful mechanical representation.
4. A projection identity that omits actual facts and relationships can reuse stale authority.
5. Aggregate extraction floors or prose percentages cannot prove per-record completeness.
6. Complete representation must not be confused with how much the bounded-d20 adapter executes.

The Owner has settled completed 5d scope as the full mechanically substantive SRD 5.2.1 corpus.

---

## Central Decision

Afterworlds will publish one complete typed mechanical-authority projection for an exact published 5c
release. Every mechanically substantive source component is represented:

- through typed declarative facts where meaning can be preserved faithfully;
- through exact governing prose where contextual, subjective, or open-ended GameMaster judgment remains
  necessary; or
- through both.

This projection is complete mechanical **representation**, not universal deterministic **execution**.
The hand-authored Rules System Adapter separately declares and proves the component shapes it can execute.

---

## Decisions

### Decision 1 — Complete source accounting, selective execution

The completed first projection accounts for the full mechanically substantive content of SRD 5.2.1.
Implementation phasing cannot redefine a partial projection as completed 5d.

Structured/prose-bound handling follows representability of source meaning. No owner-selected extraction
percentage, prose ceiling, or adapter-coverage target determines that classification.

### Decision 2 — Span-exact semantic classification

Every 5c `REPRESENTED` leaf is partitioned into accepted semantic spans classified as:

- substantive mechanical authority;
- supporting authority;
- non-mechanical material under a closed reason;
- or unresolved.

Unreviewed/proposed and unresolved spans block publication. `PROSE_BOUND` is not a classification default;
it is an affirmative component-handling judgment requiring a closed irreducibility reason.

Supporting authority is first-class. Headings, examples, cross-references, explanatory clauses, and
GameMaster guidance may identify, limit, explain, or exemplify mechanics even when they are not
independent structured facts.

### Decision 3 — Semantic records and many-to-many provenance

Mechanical records are assembled from a committed accepted inventory. A 5c `ENTRY` is structural evidence,
not universal semantic authority.

Records and components use stable semantic keys rather than positional ordinals. Facts, prose bindings,
and relationships carry exact many-to-many provenance to 5c leaf subspans. Primary and contextual roles
are distinct; contextual overlap is permitted while conflicting primary claims fail.

**Amended by Owner Decision 2026-08-08.** The many-to-many provenance required above binds the immutable
base projection's prose bindings: those resolve exclusively to 5c leaf subspans and carry no other
provenance. A distinct runtime authored-authority prose overlay, layered over a published record or
component (Decision 10), is not a prose binding under this decision and does not participate in its
many-to-many 5c subspan provenance. Authored prose is never assigned a 5c leaf subspan, a chunk identity,
or an irreducibility claim copied from base-projection authority; its provenance is the authored override
record and the retained override-set version that supplied it (Decision 9).

### Decision 4 — Closed typed facts, no generated rules engine

Structured authority uses a closed, versioned discriminated union of fact families. A new mechanical
family requires a typed schema and tests or an honest prose-bound classification.

The projection cannot contain:

- arbitrary executable expressions;
- runtime-interpreted scripts or a general rules DSL;
- model-authored mechanical logic;
- generic numeric/key-value escape hatches; or
- mechanically authoritative values inferred from source prose at runtime.

The projection is declarative data consumed by hand-authored code.

**Amended by Owner Decision 2026-08-29 (#137 round 6) — schema identity binds the intrinsic validation
contract, not only the wire shape.** A serialized grammar is not only which fields exist and which values
they admit; it is also which combinations of them mean anything. Two builds agreeing on every family,
field, and vocabulary while disagreeing about whether a duration may be negative, whether a fraction may
have a zero denominator, or whether a closed choice must contain the pair the fact declares are not
implementing one contract — and before this they hashed identically.

The representation schema payload therefore carries an **invariant manifest** beside its introduction
manifest, on these terms:

* **Serialized identifiers only.** Each row names a locus the wire can show — a fact family discriminator,
  an applicability kind, or, for a nested value object that carries no type tag, its sorted field set — and
  never a Python class, function, or module name. Identity may not depend on what a payload cannot show.
* **Declarations, never implementations.** No source text, bytecode, comment, or docstring is hashed.
  Reminting accepted authority for a refactor is the failure this rule exists to prevent, and it is
  unchanged.
* **Scope, so the declaration is stable.** Every intrinsic invariant a schema-4 addition settled and the
  representation's validators enforce, plus the shared value-object rules those additions delegate to,
  including a joined rule's full extent. Schema-3-era ranges this succession did not touch, and relational
  rules checked against the corpus rather than intrinsic to a value, stay outside it.
* **Executable, or it is not declared.** Every row is exercised by an exemplar the shared validator refuses
  and one it admits, and the coverage is asserted as a set equality, so a row nothing demonstrates fails
  the suite rather than standing as prose.
* **Loosening it costs the succession.** Weakening or removing a row moves the schema hash, so the
  registered lift's destination pin no longer describes this build and `lift_for` refuses the transition.

Finalizing this contract moved the schema-4 destination hash before merge, most recently to
`241860418b183f67bcc4d914d1fdaa3bbcea1705f28cdd460eb05716d40ce3e9` when the reconciliation in round 7
found a declared addition whose joined rule was only half declared. The schema-3 source pin
`43ed330d3b3630d37ed92122fd87cc2c170863bab4465e53c727f1b8c6b86e05` is unchanged, and zero movement was
re-run against the finalized destination: six collections byte-identical, every stored coordinate
re-deriving, `oracle_identity` unmoved.

**Amended by Owner Decision 2026-09-02 — representation schema 5, and a correction to what schema 4
declared about distance-scaled damage.** The `hazards-1` semantic review rejected proposal
`6277ff735e0e47b3337f2c3736ca7922864b1cde9a3c286b3aee48ee461ba259` on one defect family: *mechanically
distinct source meanings collapse or disappear because their qualifiers or composition are not present
in canonical typed authority.* Schema 4 admitted three instances, and schema 5 closes each with a
closed structure rather than a predicate language:

* **A DC source states which roll it is stated for.** `AbilityCheckFact.context: RollContext` is
  required and admits exactly `ability_check` and `saving_throw`. Until now Malnutrition's *"must
  succeed on a DC 10 Constitution saving throw"* and a DC 10 Constitution ability check produced one
  payload and one fact key. It is required rather than defaulted because a default would omit one of
  the two spellings under the post-schema-3 omission rule, and the omitted form would hash exactly as
  the stated one — re-creating the collapse inside the mechanism that exists to preserve identity. The
  family is **not** migrated onto `RollSpec`: actor polarity stays outside a DC source, for the reason
  the family already gave.
* **A consumption rule states a band, not a threshold.** `ConsumptionBand` carries the requirement, the
  period, an optional lower and upper bound each with its own inclusivity, and an optional *sustained*
  duration of the band itself. `ApplicabilityKind.CONSUMPTION_THRESHOLD` now ranges over exactly that
  one field. A single comparison could state only one side, so *"eats **but** consumes less than half"*
  and *"eats nothing"* both reduced to `< 1/2` — and the source gives them different consequences.
  "Each subsequent day without food" needs no further structure: `applies_when` already says *when a
  component applies at all*, so a component whose applicability is the band and whose `recurs` is a
  daily boundary repeats only while the band holds.
* **A distance-scaled damage is stated once, on the damage.** `DamageFact.per: DamageInterval` says the
  stated amount is dealt *per* interval, `ScalingBasis.DISTANCE_FALLEN` is refused on `ScalingFact`, and
  a component may not hold a per-interval damage beside a damage-effect scaling. **This corrects
  schema 4's own declaration**, which said `ScalingFact.threshold` carried the per-unit interval for
  this basis. That reading was not enforceable — under every other basis the same field is *the level
  above which the change begins* — so Falling was 3d6 or 4d6 on a 30-foot fall depending on which
  reading a consumer applied. The schema-4 text is withdrawn rather than left standing beside its
  replacement.

A fourth rule joins them, on the same family: a `ROLL_OUTCOME` applicability answers to **exactly one**
roll established in its own scope. *"On a successful check"* in a component that calls for no roll names
the outcome of nothing, and the authority it gates becomes unreachable.

The schema-5 destination pin is
`2803840899363988cc2f67e0d9f310d9baffe394d52ca0919d11388bcd7f4c40`. The schema-4 pin is unchanged and
stays a recognized contract. Succession is registered one step at a time and resolved as a **path**:
the committed `conditions-1` artifact declares schema 3 and reaches schema 5 across two recorded
crossings, because a direct 3 → 5 row would reach the same declaration while asserting the artifact
never crossed schema 4. Zero movement was re-run against the finalized destination: all six collections
byte-identical across both steps, 185 spans, 185 acceptances and 16 obligations carried by object
identity, the batch anchor still at schema 3, and the committed file never written. Nothing accepted
moves at the new required axis because the accepted artifact holds no ability-check fact at all, which
is asserted against the artifact rather than assumed.

**Amended by representation schema 6 — the `actions-1` schema stop.** Discovery over the thirteen
`actions-1` records reached a schema stop before any proposal was generated: 21 blocking families across
35 `UNRESOLVED` obligations, none of which schema 5's union could carry without either losing a
distinction the source draws or asserting one it does not. Schema 6 answers them under contract 3's first
branch — twelve typed families and a set of widenings — and leaves the rest under its second, as prose
bound at the scope where it applies. Answering the batch's obligations is not the same as discharging a
contract-3 family group: `known_unknowns.md` records each affected group against its own closure
standard, and none of them reaches **discharged** on this batch's evidence.

The twelve families are `ActionAllowanceFact`, `MovementAllowanceFact`, `MovementInterleaveFact`,
`EffectDurationFact`, `ReactionProvocationFact`, `RetryRestrictionFact`, `RecurringActionRequirementFact`,
`SustainedStateRequirementFact`, `ResourceExpenditureFact`, `EquipmentChangeFact`,
`TriggeredResolutionFact`, and `ActivationCostEligibilityFact`. Three of the decisions inside that set
are the ones worth recording here, because each refuses a shape that would have been smaller:

* **An allowance states either a slot or an activity, never both, and never one vocabulary spanning
  the two.** *"You can take one additional action"* and *"you can make one additional attack"* are
  different grants; a single enum admitting overlapping members would render them identically on the
  wire.
* **A sequencing point is two families, not one discriminator.** *"between attacks"* and *"immediately
  after the trigger"* locate a thing in different domains, and one enum spanning both would have to
  refuse most of its own cross products — two families wearing one field. The same argument keeps
  `RecurringActionRequirementFact` and `SustainedStateRequirementFact` apart, and keeps obscurement's
  vocabulary apart from cover's.
* **Eligibility is substantive authority, not supporting prose.** *"To be readied, a spell must have a
  casting time of an action"* states **which spells the mechanic reaches**, over a printed, enumerable
  field. `Ready` L8 had been classified as supporting; the sweep for comparable clauses confirmed
  `Magic` K1 and `Utilize` O2 were already typed, so it is the only reclassification.

The widenings: `RollActor.ALLY`, admitted because `Help`'s two arms are neither the subject's roll nor a
roll directed at the subject and so produced identical typed authority; two `DcKind` members, one of
which carries a number, correcting the family's earlier "only `FIXED` carries a number" declaration;
`AbilityCheckFact.ability` made **optional** — an ability the GM chooses, beside a printed DC, was
otherwise unrepresentable — with `dc_ability` and `against_subject` beside it; `AdvantageFact.use_limit`;
five `ApplicabilityKind` members including a **depth-1, canonically ordered, at-least-two**
disjunction; and `ProseBindingDraft.option_key`, which lets prose govern one arm of a choice where
component-grain binding would be false rather than merely lossy. `option_key` appends a sixth element to
the provenance coordinate **only when non-empty**, so all twenty accepted five-element coordinates are
unchanged.

**Amended in the same review round, before anything was accepted under it.** Schema 6 was reviewed
against its own consuming paths and four things it declared were not yet true of them. Each is a defect
of *propagation* — new meaning that existing contracts had not been carried across — rather than a
reason to revisit the twelve families, and one of them changes this ADR's own contract:

* **Option-scoped prose reaches a consumer.** The effective view discarded `option_key`, so `Help`'s two
  arms published the same governing passage twice and moving a clause between arms produced an
  identical effective record. `SourceProse` now carries the scope, and the component-wide scope stays
  the empty string every accepted binding states.
* **A schema-6 null is refused under an earlier declaration.** `AbilityCheckFact.ability` became
  optional at schema 6, and nothing enforced that: an artifact declaring schema 5 could state
  `"ability": null` — a check fixing no ability, beside a printed DC — and be read as authority a
  schema-5 reviewer signed off on. The key is a schema-1 field, so the payload is *complete* either way
  and only the value is new; neither the omission registry nor the required-since registry can see that
  shape. A third registry states it, and **it is part of the version-legality contract, so it is inside
  the schema hash**: the destination pin is now
  `0e4b4378bf1409ed3ffbbec61a279430689ce4a0d3b70b1b3e9d886f66ae20b7`, replacing the
  `d4584a74…c1d6` recorded above before review. Nothing accepted moves — every accepted ability check
  states an ability, so every accepted payload and `fact_key` is byte-identical — and no batch had been
  accepted under the earlier pin.
* **A disjunction is not a place to hide a condition from its scope rule.** `ANY_OF` states no operand
  of its own, so the roll-outcome and counterpart-establishment rules read it as stating nothing:
  wrapping a refused condition in one made it legal, in component, option, fact-qualifier and override
  scope alike. Both rules now read a disjunction's terms, which is a flatten rather than a walk because
  depth is 1 by invariant.
* **Every applicability ingress refuses depth before it recurses.** The builder reached through
  `fact_from_payload` — and therefore `ConditionRemovalRestrictionFact.until`, and the override seam —
  rebuilt terms as deep as the payload asked, so a 600-level payload raised `RecursionError` from the
  one layer whose contract is to report malformed input.

Schema 4 and schema 5 remain
recognized contracts and their pins are unchanged. Succession stays one row per crossing and resolved as
a path: the committed artifact declares schema 5, which is where `hazards-1` was reviewed, and reaches
schema 6 across `5d-lift-schema-5-to-6`. Zero movement was re-run against the finalized destination —
all six collections byte-identical, 281 spans and every accepted provenance coordinate carried by object
identity, both batch anchors still at the schema each was reviewed under, and the committed file never
written.

Nothing is accepted, published, activated, or retired by the schema change, and acceptance-ready
regeneration for `actions-1` stays paused until it passes review.

> **Historical — the state at the schema-6 amendment.** The two paragraphs above record what was true
> when schema 6 was registered, and are kept as written. The committed artifact declared schema 5 then;
> it declares schema 7 now, and `hazards-1` is no longer the batch the newest acceptance was reviewed
> under. The pause stated here ended on 2026-09-09; see the note under the schema-7 amendment below.
> Every pin, anchor and lift row recorded above is unchanged.

**Amended by representation schema 7 — the `actions-1` residue S-1.** Independent review of the
schema-6 batch cleared the `Dash` correction, the `Magic`/`Ready` activation-cost eligibility
reclassification and the `Help`/`Influence` governing prose, and confirmed one stop. *"If you cast a
spell that has a casting time of 1 minute or longer"* (`Magic`, p185) is a threshold over a spell's
**printed casting-time descriptor**, and schema 6 had no shape for it. `ActivationCostEligibilityFact`
ranges over `ActionCost`, which prints no amount and no unit, so it cannot carry a duration;
`ApplicabilityKind.ELAPSED_DURATION` would have meant time *already spent* casting, which is false at
the moment the clause first has to apply. `Magic` K2, K3 and K4 stayed unresolved together because the
recurring action, the Concentration duty and the failure/resource consequences are all consequences of
that one gate.

Schema 7 is the smallest closed extension that states it: **one** `ApplicabilityKind` member,
`SPELL_CASTING_TIME`, over **one** closed value object, `CastingTimeThreshold(at_least_amount,
at_least_unit)` — the same shape schema 5 used for `CONSUMPTION_THRESHOLD`/`ConsumptionBand`. No fact
family, no ownership form, no nullable field, no predicate language and no executable rule. Three
decisions inside it are worth recording:

* **Applicability, not a fact, because the gate has to be shared.** K2's requirement and K4's
  consequences are two components of one record, and both are inside the same printed condition. A gate
  carried as a *fact* and restated on both is refused by the duplicated-fact-authority rule — correctly,
  since one source statement would have become two copies of the same authority. Applicability may
  repeat across components, because a condition two structures share is one condition. That asymmetry
  is what makes it the scope-preserving carrier, and it is asserted in test rather than argued here.
* **The break stays conditional inside the gate.** A component has exactly one `applies_when`, which
  the gate occupies, so *"If your Concentration is broken"* rides `FactQualifier` on each of the two
  consequence facts. Qualifiers compose conjunctively inward, which is the reading the source prints: a
  long casting, whose Concentration is broken. A component stating only `CONCENTRATION_BROKEN` would
  have reached every broken Concentration in the game.
* **A one-minute spell falls outside `Magic` K1, not outside the Magic action.** K1's eligibility fact
  says which spells the action *reaches* by the cost they print; a timed casting prints no cost and so
  matches no eligibility fact. K2 is a different clause about a further requirement **inside** the
  action. Widening `ActionCost` to carry a duration would have conflated them.

Two intrinsic invariants are declared inside schema identity, so weakening either moves the hash and
strands the registered lift: an amount below 1 states no duration and would reach every timed casting,
and `ROUND`/`TURN` are cadences of the initiative cycle rather than units a casting time is printed in.
`casting_time_meets` compares the two **stated durations by magnitude**, reducing each through the
fixed calendar length of its unit — second, minute, hour, day. A 120-minute threshold is therefore not
met by a 1-hour casting, and a 1-minute threshold is met by a 60-second one. *(An earlier draft of this
helper ranked the unit *names* and dropped both amounts whenever the units differed, which was
over-inclusive in the first direction and under-inclusive in the second. Corrected before any
acceptance; recorded here rather than silently replaced.)* A round and a turn are slices of the
initiative cycle whose length no printed casting time states, so a casting time or threshold in either
**raises** rather than answering — `False` is the substantive answer *"this rule does not reach that
spell"*, and returning it for a comparison never made would hide a wrong eligibility decision behind a
Boolean. That refusal is the boundary of the supported forms; no SRD casting time is printed in rounds
or turns, so nothing in the corpus is reached by it, and the residue is recorded in
`known_unknowns.md`. The conversion table is a property of the calendar words, not a ruling about the
corpus, and the general eligibility question stays deferred.

The schema-7 destination pin is
`80e853ef9433ba2e7232c384a7192235692463c9954f5ff766be1fafade6f43d`. Schemas 4, 5 and 6 remain recognized
contracts with unchanged pins; schema 6 becomes recognized *as the source of a registered lift*, which
is the registry rule rather than a hand-kept list. Succession stays one row per crossing and resolved as
a path: the committed artifact still declares schema 5, which is where `hazards-1` was reviewed, and now
reaches schema 7 across `5d-lift-schema-5-to-6` then `5d-lift-schema-6-to-7`. Nothing accepted moves —
`Applicability.casting_time` is omitted when unset, so every applicability accepted under schemas 3
through 6 already has its schema-7 canonical form, and the frozen prior is lifted rather than rewritten.

Nothing is accepted, published, activated, or retired by this schema change either, and acceptance-ready
regeneration for `actions-1` remains paused. The new composition for `Magic` K2/K3/K4 is demonstrated
through review and test evidence only — a persisted-gate proof against the pinned source coordinates,
not a proposal and not an acceptance.

> **Historical — the state at the schema-7 amendment, superseded by Owner Decision 2026-09-09.** The
> paragraph above records the state when schema 7 was registered and is kept as written; the pause it
> states has since ended. On 2026-09-09 the Owner accepted this exact schema-7 proposal,
> `62202e9a4b9e0cb539c770e1244b3aa322d8f988e82a544991998fd8fb363b5c`, as batch `actions-1` — all 182
> spans and the complete representation, extending the preserved `conditions-1`/`hazards-1` prior
> through the registered transitions. **No unresolved architectural choice remains here and no further
> Owner ruling is required**; this note reconciles the description with a decision already recorded, and
> amends no contract.
>
> What the acceptance changed: the committed artifact now declares schema 7 rather than schema 5, and
> carries a third anchor, `actions-1` at schema 7. What it did not change: `conditions-1` stays anchored
> at schema 3 and `hazards-1` at schema 5, where each was reviewed; succession is still one row per
> crossing, resolved as the path `5d-lift-schema-3-to-4` → `4-to-5` → `5-to-6` → `6-to-7`; schemas 4, 5
> and 6 remain recognized contracts with the pins above; and the schema-7 destination pin is still
> `80e853ef9433ba2e7232c384a7192235692463c9954f5ff766be1fafade6f43d`. The accepted mechanical identity is
> `8c41b01e92878c614fad5c039c006c66221a4cc55cfab68698ef9302865a6eee`.
>
> What remains open is unchanged by it. The acceptance published, activated and retired **nothing**, and
> it resolved no reference it did not define: `glossary.speed`, `glossary.concentration`,
> `attitude.friendly`, `attitude.hostile` and `attitude.indifferent` are still unresolved and are still
> explicit publication blockers. General casting-time eligibility stays a deferred Known Unknown,
> recorded in `known_unknowns.md`, together with representation limit L-1 and residue R-help-reason. The
> `Magic` K2/K3/K4 demonstration named above was no part of the accepted batch and remains
> demonstration evidence only.

**Amended by representation schema 8 — the `attitudes-1` stop S-2.** *"Indifferent is the default
attitude of a monster."* (`Indifferent`, p184) states which member of a closed class applies when
nothing else has been specified, and schema 7 had no shape for it. No composition of accepted families
says it either: a default is not an effect, a duration, an allowance, a roll, or a state transition.
The gate is **#137 contract 3** — add a specific typed family, or classify the affected component
honestly as prose-bound — read under **Decision 4** above, which constrains the shape. The prose-bound
branch is unavailable rather than declined: none of the six closed irreducibility reason codes is
affirmatively true of the clause, and the batch's audit prints the per-code disposition. So schema 8
adds exactly one family, `DefaultAttitudeFact`, over exactly one closed vocabulary, `Attitude`
(`friendly`, `hostile`, `indifferent`). Nothing else moves: no field is added to, made required on, or
made nullable on any accepted family, and no ownership form changes.

The vocabulary is admitted at its **printed closure** — *"A monster has a starting attitude toward a
player character: Friendly, Hostile, or Indifferent."* enumerates the class in one line — rather than at
the single member this batch uses. That is `MovementMode`'s accepted reasoning: a closure that tracked
whichever member happened to be represented first would be a property of the batch order, not of the
source. Sibling count is not the gate here and is not treated as one; the standard this document states
for **discharging** a Known-Unknown group (`known_unknowns.md`) governs discharge of those groups, not
admission of a family under contract 3, and the accepted union already records the counterexample —
`MovementPermissionFact`, *"the thinnest family admitted here"*, whose *"vocabulary is stronger than its
sibling count."*

Decisions worth recording, because each was a shape considered and rejected. `is_default: bool` would
have left *which* member to whoever read the record's semantic key — a by-convention inference, and one
that silently produces a different mechanic on a record named differently; the field is a stated value.
An `Applicability` was rejected because a default is not a gate: it does not say *when* something
applies, it says what holds absent other specification. A single-member vocabulary was rejected for the
closure reason above. A creature-kind or subject field was rejected as a generic escape hatch — the
family carries no beneficiary, subject or creature category, because it states a default rather than
assigning one. *"of a monster"* is scope carried by the **declared vocabulary**: `Attitude` is declared
as a monster's stance toward a player character, so `DefaultAttitudeFact(attitude=INDIFFERENT)` states a
monster-scoped default in the typed contract itself, and that member is exactly what both consumer views
deliver — the typed view carries the fact, the GameMaster view carries it in `structured_context` on a
`STRUCTURED` component that resolves no prose and cites no span of its own, and the fact entry there
names the clause by span id, not as text. Provenance establishes the **source** of that declared contract — *"Indifferent is the default attitude
of a monster."* (`Indifferent`, p184), at the closure *"A monster has a starting attitude toward a player
character"* (`Attitude`, p177) — rather than carrying the scope to a consumer. Neither the family name
nor the record key states it, and nothing is adjudicated at runtime. Friendly's and Hostile's influence-check bias is unchanged by all of this: it
stays `condition.charmed`'s accepted `AdvantageFact` shape on a `MIXED` component with prose-bound
`contextual_applicability`, and `RollContext` is deliberately not widened.

The schema-8 destination pin is
`8a125f6c4c9929109879ad98a8f14a4ec1d0c7f5fe56fe4f894dafbdf707afff`. Schemas 3 through 7 remain
recognized contracts with unchanged pins, and succession stays one row per crossing: exactly one
registered transition, `5d-lift-schema-7-to-8`, separates schema 7 from schema 8, and the batch
exercises it with `verify_lift_path` rather than describing it. **Nothing accepted moves.** The
committed artifact and the frozen prior both still declare schema 7 after this change; were
`attitudes-1` ever accepted, the path from the committed artifact would resolve as
`5d-lift-schema-3-to-4` → `4-to-5` → `5-to-6` → `6-to-7` → `7-to-8`, and the prior would be lifted
rather than rewritten.

Nothing is accepted, published, activated, or retired by this schema change. `attitudes-1` is a
**proposal**, `c571dfd6b829852e58ca066f8735b6d5944cb51c0f4b42c82052d876392bff22`, reviewable material
only; the accepted mechanical identity is still
`8c41b01e92878c614fad5c039c006c66221a4cc55cfab68698ef9302865a6eee`. Because nothing is accepted,
`attitude.friendly`, `attitude.hostile` and `attitude.indifferent` remain **unresolved** reference
targets and remain publication blockers, exactly as `known_unknowns.md` records them. Schema 8 narrows
no Known Unknown group listed there and discharges none, so that document is amended only with a
pointer to this change and not otherwise.

> **Historical — the state at the schema-8 amendment, superseded by Owner Decision 2026-09-10.** The
> two paragraphs above record the state when schema 8 was registered and are kept as written; the
> "nothing is accepted" they state has since ended. On 2026-09-10 the Owner accepted this exact
> schema-8 proposal, `c571dfd6b829852e58ca066f8735b6d5944cb51c0f4b42c82052d876392bff22`, as batch
> `attitudes-1` — all 24 spans and the complete representation, extending the preserved
> `conditions-1`/`hazards-1`/`actions-1` prior through the registered transitions. **No unresolved
> architectural choice remains here and no further Owner ruling is required**; this note reconciles the
> description with a decision already recorded, and amends no contract.
>
> What the acceptance changed: the committed artifact now declares schema 8 rather than schema 7, and
> carries a fourth anchor, `attitudes-1` at schema 8. The conditional above is now the fact — the path
> resolved as `5d-lift-schema-3-to-4` → `4-to-5` → `5-to-6` → `6-to-7` → `7-to-8`, and the prior was
> lifted rather than rewritten. What it did not change: `conditions-1` stays anchored at schema 3,
> `hazards-1` at schema 5 and `actions-1` at schema 7, where each was reviewed; the frozen prior
> `accepted_prior_conditions_1_hazards_1_actions_1.json` is untouched at schema 7 and keeps its own
> digest; schemas 3 through 7 remain recognized contracts with the pins above; and the schema-8
> destination pin is still `8a125f6c4c9929109879ad98a8f14a4ec1d0c7f5fe56fe4f894dafbdf707afff`. The
> accepted mechanical identity is now
> `c3b4d4b759441b05418fcbe1d90811e0d7c2535319aa005e64201ce29b5c74fa`, over 39 records and 487 spans.
>
> What remains open is narrowed but not closed by it. The acceptance published, activated and retired
> **nothing**. It did resolve three reference targets it also defines — `attitude.friendly`,
> `attitude.hostile` and `attitude.indifferent` are no longer unresolved — which is a consequence of
> accepting a complete source class rather than the reason for accepting it. `glossary.concentration`
> and `glossary.speed` are still unresolved and are still explicit publication blockers, so the corpus
> stays incomplete and runtime-unpublished. `[Area of Effect]`, the remaining complete tagged class,
> stays disclosed and deferred on the spatial-geometry family it would require.

**Amended by representation schema 9 — the `areas-of-effect-1` class.** `[Area of Effect]` is the
last complete tagged class in the bound release: seven Rules Glossary entries, 43 clauses, of which 24
are substantive. Schema 8 can state **none** of the 24. The prose-bound branch is unavailable rather
than declined — no clause in the class matches any of the six closed reason codes in
`policy.IRREDUCIBILITY_REASONS`; every one states a closed, printed, non-delegated rule — so **#137
contract 3** read under **Decision 4** requires typed families. Schema 9 adds seven, over eleven closed
vocabularies: `AreaOriginFact`, `AreaDimensionRequirementFact`, `AreaOriginInclusionFact`,
`AreaWidthRelationFact`, `AreaOriginMovementFact`, `BlockedLineExclusionFact` and
`UnseenOriginRelocationFact`. Nothing else moves: no field is added to, made required on, or made
nullable on any accepted family, and no ownership form changes.

The deferral this supersedes was framed in grid vocabulary the source does not use. The bound text
contains no `square`, `grid`, `battle`, `map`, `token` or `space` in any of the 43 clauses; it says
*point of origin*. "Whether the origin square is included" sounds like grid simulation, and *"A
Cylinder's point of origin is included in the area of effect"* is a printed declarative state. No
spatial-geometry family is admitted here and none is needed: **no parameter value, unit, coordinate or
grid semantic is represented anywhere in schema 9.**

Decisions worth recording, because each was a shape considered and rejected.

- **One family per gap was rejected for G1/G2.** The general rule — every area has a point of origin —
  and the per-shape placement rule are fields of one `AreaOriginFact`, so a shape record states both
  without either restating the other, and the two coexist faithfully. Emanation is the discriminating
  witness: its origin is *a creature or an object*, so `AreaOriginKind` carries `CREATURE_OR_OBJECT`
  beside `POINT` and a point-only origin would have silently lost the printed distinction.
- **A single dimension slot was rejected.** Arity is printed and varies: Cylinder requires the radius of
  the base *and* the height, Line requires length *and* width, the other four require one.
  `AreaDimensionRequirementFact` carries an ordered tuple of `AreaDimension` **parameter names**. The
  creating effect supplies the values, which is what the source says; the only "feet" in the class is
  `Cone/1/2`, a worked example, and `DistanceUnit` is deliberately not reached for.
- **A formula for Cone's taper was rejected** as exactly the executable expression Decision 4 forbids.
  `AreaWidthRelation.EQUAL_TO_THAT_POINTS_DISTANCE_FROM_THE_POINT_OF_ORIGIN` names the printed relation
  as a closed member a hand-authored adapter interprets. Computing a width at a distance is adapter
  arithmetic and stays outside.
- **A boolean origin-inclusion flag was rejected.** The printed state is not two-valued in the way a
  bool suggests: four shapes print *excluded unless its creator decides otherwise*, and dropping the
  creator's control would publish a stricter rule than the source states. `AreaOriginInclusion` carries
  the exception in the member.
- **Reusing `DurationKind.INSTANTANEOUS` alone for G6 was rejected.** Emanation moves with its origin
  except for two effect kinds, and *"stationary effect"* has no member anywhere in schema 8 — not in
  `DurationKind`, not in `SustainedState`, not in `EffectTerminationFact`. Both exceptions are carried,
  as a tuple over `AreaMovementSuspension`, because either alone is a different rule.
- **The G7 quantifier is a stated member, not an implicit reading.** The rule excludes a location when
  **all** straight lines from the point of origin to it are blocked; one blocked line among many
  excludes nothing. `BlockedLineQuantifier.ALL_STRAIGHT_LINES_FROM_THE_POINT_OF_ORIGIN` states it, so
  *all blocked* and *some blocked* are distinguishable in the typed contract rather than in a reader's
  head. `blocking_cover` is typed as the whole `CoverDegree` and pinned to `TOTAL` by the fact this
  batch states: the field's type is the kind of thing that blocks, the printed threshold is the value,
  and `CoverDegree` — a schema-6 vocabulary — is therefore not re-declared as a schema-9 one.
- **An obstruction vocabulary was rejected for G8.** *"such as a wall"* is inline exemplification inside
  a substantive clause, not a closed enumeration, and reading it as one would publish a list the source
  does not print. `UnseenOriginRelocationFact` carries the printed **conjunction** — an unseen point
  *and* an intervening obstruction — and the printed result, the near side of the obstruction. Deleting
  either condition is refused, because a single-condition form is a different rule.

**The intrinsic contract these families add is declared, not only enforced.** Decision 4 binds the
invariant manifest into schema identity, so a rule a validator enforces and the manifest omits is a
rule outside the identity that is supposed to describe it. Three of the seven families carry an
intrinsic rule beyond the enum domain their wire shape already states, and those become five declared
rows, because emptiness and repetition are separate claims refused by separate branches: a stated
`placement` states an `extent` beside it; `dimensions` holds at least one parameter and no parameter
twice; `suspended_by_any_of` holds at least one exception and no exception twice. The other four
families add no row — what they admit is exactly their vocabularies, which the payload already carries.
Each row is exercised in both directions in `test_schema_4_invariant_closure`, and dropping any one of
them is proved there to move the hash and make `lift_for` refuse the 8-to-9 crossing.

None of this evaluates anything. Every member names what a rule *says*; nothing carries an expression, a
predicate, a formula, a free-form value or a dispatch table, and the vocabularies are closed, so a
consumer meeting a member it does not handle fails rather than interprets. That is the line **#137**
draws between its Out of scope — *"Generated executable mechanics, a runtime rules language, a generic
rules engine, or a cross-system plugin framework"* — and its In scope — *"Typed deterministic-consumer
and GameMaster-facing authority views"* and *"Typed record/component/fact `RuleOverride` application
with existing precedence semantics."* Declarative representation is in scope; runtime execution is not.
Runtime geometry, grid simulation, adapter execution and downstream adjudication all stay outside, where
Decision 11 and #137 leave them.

The schema-9 destination pin is
`f5a5e30817e64f019e31aa7f4692d72611215e4294e7da36242e492bca6b336e`. Schemas 3 through 8 remain
recognized contracts with unchanged pins, and succession stays one row per crossing: exactly one
registered transition, `5d-lift-schema-8-to-9`, separates schema 8 from schema 9, and the build
exercises it rather than describing it. **Nothing accepted moves.** The committed artifact and both
frozen priors still declare the schema they were accepted under after this change — schema 8 and schema
7 respectively — each keeps its own digest, every per-batch anchor is retained (`conditions-1`→3,
`hazards-1`→5, `actions-1`→7, `attitudes-1`→8), and the lift re-declares the binding and proves the
content unmoved rather than rewriting it.

Identity is reported at the scope it holds. The frozen authority on disk is read by this work and
never written by it, so it keeps `oracle_identity`
`c3b4d4b759441b05418fcbe1d90811e0d7c2535319aa005e64201ce29b5c74fa`. The **lifted copy** the build
produces is not that object and does not carry that identity: `oracle_payload` includes
`representation_schema.{version,hash}`, so re-declaring the binding necessarily re-identifies the copy.
At this head the lifted copy is `3454f61f51163f5cd3b5cfd24638c2fc89e87f69973f9e92a194739b311c4b95`,
and that value moves again whenever the destination pin does. What the lift proves is narrower and
stronger than an equal identity: the lifted copy holds the *same* representation object, and the only
top-level payload key that differs is `representation_schema`. Decision 4's intrinsic contract is what
makes this true rather than incidental — identity covers the binding on purpose, so a copy claiming a
schema it was not built against cannot present the accepted identity.

Nothing is accepted, published, activated, or retired by this schema change, and no proposal exists for
`areas-of-effect-1` yet. The accepted mechanical identity is still
`c3b4d4b759441b05418fcbe1d90811e0d7c2535319aa005e64201ce29b5c74fa`, over 39 records and 487 spans. The
class cites `Cover`, an untagged Rules Glossary entry no accepted batch has represented, so composing it
**adds** a third unresolved reference target, `glossary.cover`, beside `glossary.concentration` and
`glossary.speed`; all three are publication blockers and the corpus stays incomplete and
runtime-unpublished. That is a consequence of representing a complete source class, not a reason to
represent it, and sequencing a `cover-1` batch is ordinary engineering under #137 rather than an Owner
Decision. Schema 9 narrows no Known Unknown group listed in `known_unknowns.md` and discharges none, so
that document is amended only with a pointer to this change and not otherwise. The full-corpus work
Decision 5 requires remains undischarged.

> **Historical — the state at the schema-9 registration, superseded by Owner Decision 2026-09-11.** The
> paragraphs above record the state when schema 9 was registered and are kept as written; the "nothing
> is accepted and no proposal exists" they state has since ended. On 2026-09-11 the Owner accepted the
> schema-9 proposal `d602f4e59ab90dbb04852661f78f03e2e311025e80be03f39f4b324f2c6d6878` as batch
> `areas-of-effect-1` — all 43 spans and the complete representation, extending the preserved
> `conditions-1`/`hazards-1`/`actions-1`/`attitudes-1` prior through the registered transitions. **No
> unresolved architectural choice remains here and no further Owner ruling is required**; this note
> reconciles the description with a decision already recorded, and amends no contract.
>
> What the acceptance changed: the committed artifact now declares schema 9 rather than schema 8, and
> carries a fifth anchor, `areas-of-effect-1` at schema 9. The conditional above is now the fact — the
> path resolved as `5d-lift-schema-3-to-4` → `4-to-5` → `5-to-6` → `6-to-7` → `7-to-8` → `8-to-9`, and
> the prior was lifted rather than rewritten. What it did not change: `conditions-1` stays anchored at
> schema 3, `hazards-1` at schema 5, `actions-1` at schema 7 and `attitudes-1` at schema 8, where each
> was reviewed; the frozen priors
> `accepted_prior_conditions_1_hazards_1_actions_1.json` and
> `accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1.json` are untouched at schema 7 and
> schema 8 and keep their own digests; schemas 3 through 8 remain recognized contracts with the pins
> above; and the schema-9 destination pin is still
> `f5a5e30817e64f019e31aa7f4692d72611215e4294e7da36242e492bca6b336e`. The accepted mechanical identity
> is now `8e08ac48f2a57a4498557990a07270f9abd855b246c1039da68cc9ec82d44b40`, over 46 records and 530
> spans. Because the artifact now declares the schema this build implements, the lifted-copy identity
> reported above describes the earlier state and no lift stands between the committed file and current
> authority.
>
> What remains open is *widened* by it, and stated that way rather than softened. The acceptance
> published, activated and retired **nothing**. It resolved **no** reference target, and it added the
> one the amendment above predicted: `glossary.cover` is now unresolved beside `glossary.concentration`
> and `glossary.speed`. All three are explicit publication blockers, so the corpus stays incomplete and
> runtime-unpublished, and the full-corpus work Decision 5 requires remains undischarged.

**Amended by representation schema 10 — the `Cover` entry.** `Cover` is printed twice in the bound
release, as a Rules Glossary definition (p179) and as a `Playing the Game > Combat` section with a
table (p15): 16 leaves, 28 clauses, 16 of them substantive. Schema 9 can state **none** of the 16. The
prose-bound branch is unavailable rather than declined — no clause matches any of the six closed reason
codes in `policy.IRREDUCIBILITY_REASONS`; every one states a closed, printed, non-delegated rule with a
stated threshold or a stated value — so **#137 contract 3** read under **Decision 4** requires typed
families. Schema 10 adds five, over eight closed vocabularies: `CoverDefensiveBonusFact`,
`CoverTargetingProhibitionFact`, `CoverProvisionFact`, `CoverBenefitOriginFact` and
`CoverDegreeSelectionFact`. Nothing else moves: no field is added to, made required on, or made
nullable on any accepted family, and no ownership form changes.

**It also widens a vocabulary accepted authority already consumes, which is the part worth recording.**
`CoverDegree` was minted at schema 6 for `Applicability.cover` and carries `THREE_QUARTERS` and `TOTAL`;
`areas-of-effect-1` states `TOTAL` on `BlockedLineExclusionFact.blocking_cover` under schema 9, and
`action.hide` consumes two of the three. Schema 10 adds `HALF`. Widening is recorded the same way a new
vocabulary is: schema 6's registered member set stays frozen at the two it introduced and schema 10
registers `half` as its own introduction, so a schema-6 or schema-9 reader refuses `half` on the member
alone even though it recognises the field. That is asserted per specimen in
`tests/ingestion/mechanical/test_schema_version_legality.py`, not inferred — *consuming* a degree of
cover has always been legal, and defining one is the new thing.

Decisions worth recording, because each was a shape considered.

- **A `Rational` coverage fraction was considered and not used — for sufficiency, not because it is
  forbidden.** The table prints *at least half*, *at least three-quarters* and *the whole target*.
  Two of those are exact fractional thresholds and the source does print them as fractions, so
  `Rational(1, 2)` with a `Comparison` beside it would have been a faithful representation as well.
  Recording a printed threshold is exact declarative data; it is not the runtime measurement #137's
  Out of scope and **Decision 11** exclude, and neither authority bars a schema from carrying exact
  numbers. What decides it is that the numeric shape buys nothing here. The source prints exactly
  three thresholds, each carries its own comparison inside the printed phrase, and no clause in this
  population varies a threshold, derives one, or compares two of them — so a closed three-member
  vocabulary states every printed phrase once, on one axis instead of two, and leaves no fourth value
  for a consumer to invent. It also lets *the whole target* stay the phrase the page prints. If a
  later batch prints a coverage threshold this vocabulary cannot name, the exact numeric carrier is
  still available and is the natural extension.
- **Reusing `AreaOriginKind.CREATURE_OR_OBJECT` for the offeror was rejected.** It is precedent that
  *"a creature or an object"* is admissible as a closed member, not a vocabulary to share: merging an
  area-origin kind with a cover offeror would make two unrelated rules move together. `CoverOfferor`
  carries `ANOTHER_CREATURE_OR_AN_OBJECT` and `AN_OBJECT`, which is the printed asymmetry — Half admits
  a creature or an object, Three-Quarters and Total admit an object only — and a single shared member
  would have erased it.
- **A bonus of zero for Total Cover was rejected.** Total Cover's benefit is categorically different:
  *"Can't be targeted directly."* `CoverTargetingProhibitionFact` is a separate family for that reason,
  and `TargetingProhibition.DIRECT_TARGETING` keeps *"directly"* — a prohibition on all effects is a
  stronger, different rule.
- **A rank over the three degrees was rejected.** *"Only the most protective degree applies"* is a
  printed selection rule; no ordering of the three is printed anywhere in either site.
  `CoverDegreeSelection.MOST_PROTECTIVE` names the rule the page states and stops there. The combat
  printing's *"the degrees aren't added together"* is the same rule stated negatively, so it is a
  second field — `CoverDegreeCombination.NOT_ADDED_TOGETHER` — on one fact rather than a second fact.
- **Splitting the defensive bonus into AC and saving-throw halves was rejected.** One printed benefit is
  two modifications at once, both keyed to one degree; a shape that could state only the saving-throw
  half (`RollSpec` reaches that one, and `RollContext` has no member for AC) would silently drop AC.
  `CoverDefensiveBonusFact` carries the degree, the amount, the defense and the ability together.
- **Two facts for the rules printed at both sites were rejected.** Four rules appear in both the
  glossary and the combat section. Provenance is many-to-many under **Decision 3** and
  `validation.py:621` rejects only a span with more than one *primary* owner, so both sites' spans claim
  the same fact as `PRIMARY`: shared authority, exact provenance, one stated effect. The alternative —
  typing one site and classifying the other as supporting authority — was available and is what
  `areas-of-effect-1` used for two spans, but here both sites genuinely state the rule.
- **The closure statement is carried by a component, not a fact.** *"There are three degrees of cover"*
  (`glossary/1/1`) states the closure of a vocabulary, and `ProvenanceTargetKind` has no vocabulary
  member. Read substantive with nothing to claim it, the span would trip `validation.py:637`. A
  component-level `PRIMARY` claim is the carrier that exists, and it is precedent rather than invention:
  the accepted prior holds 19 `component/primary` claims and 0 `record/primary`. The combat section's
  `combat/1/1` defers instead of stating — *"As detailed in the Cover table"* — so it is supporting
  authority on the same component, and that asymmetry is the reading, not an oversight.

None of this evaluates anything. Every member names what a rule *says*; nothing carries an expression, a
predicate, a formula, a free-form value or a dispatch table, and the vocabularies are closed, so a
consumer meeting a member it does not handle fails rather than interprets. **No runtime geometry is
computed**, and no parameter value, unit, coordinate or grid semantic appears anywhere in schema 10 —
because nothing in this population prints one, not because geometric meaning may not be represented.
The boundary is computation and adjudication, not subject matter. Measuring what fraction of a target
an obstacle covers, deciding which side an effect originated on, choosing a degree for a scene and
executing an attack are all runtime, where **Decision 11** and #137's Out of scope leave them. `Applicability.cover` already lets a rule be *conditioned* on a degree; that
existing field consumes a cover state and was never a definition of one, which is precisely the gap
schema 10 closes.

The schema-10 destination pin is
`c39e3a35e197a1d1db5c2c2b3445ff0cbf03395c91e3426353a4bce589be4be0`. Schemas 3 through 9 remain
recognized contracts with unchanged pins, and succession stays one row per crossing: exactly one
registered transition, `5d-lift-schema-9-to-10`, separates schema 9 from schema 10, and the build
exercises it rather than describing it. **Nothing accepted moves.** The committed artifact and every
frozen prior still declare the schema they were accepted under after this change, each keeps its own
digest, and all five per-batch anchors are retained unchanged (`conditions-1`→3, `hazards-1`→5,
`actions-1`→7, `attitudes-1`→8, `areas-of-effect-1`→9) — the assertion this succession most needs to
make, because a lift that re-derived anchors would erase the record of what each batch was accepted
under. The frozen five-batch prior on disk keeps the identity the Owner accepted,
`8e08ac48f2a57a4498557990a07270f9abd855b246c1039da68cc9ec82d44b40`, over 46 records and 530 spans. Its
*lifted copy* is a different object with a different identity —
`34128ca4c3dd8060cd43e1a0b1097d8abe40b029c03c02d556748a21e86b1d6a` — because the oracle payload carries
the representation binding and the lift re-declares exactly that; the only top-level payload key that
moves is `representation_schema`, and everything else crosses by object identity rather than by
equality. The lift rebinds; it does not rebuild.

Nothing is accepted, published, activated, or retired by this schema change, and no proposal exists for
`cover-1`. The accepted mechanical corpus is unchanged, and the three unresolved cross-batch reference
targets — `glossary.concentration`, `glossary.cover` and `glossary.speed` — are still three. Schema 10
makes `glossary.cover` *representable*; only accepting a `cover-1` proposal would resolve it, and that
is a later step. The full-corpus work Decision 5 requires remains undischarged.

> **Historical — the state at the schema-10 registration, superseded by Owner Decision 2026-09-11.**
> The paragraphs above record the state when schema 10 was registered and are kept as written; the
> "nothing is accepted and no proposal exists" they state has since ended. On 2026-09-11 the Owner
> accepted the schema-10 proposal
> `1d8a51164f9be0a1559aba93fb076ee0e8c262dda183791491bc339e3ebfec01` as batch `cover-1` — all 28
> spans and the complete representation, extending the preserved five-batch prior through the
> registered transitions. **No unresolved architectural choice remains here and no further Owner
> ruling is required**; this note reconciles the description with a decision already recorded, and
> amends no contract.
>
> What the acceptance changed: the committed artifact now declares schema 10 rather than schema 9,
> and carries a sixth anchor, `cover-1` at schema 10. The registered path resolved as
> `5d-lift-schema-3-to-4` → `4-to-5` → `5-to-6` → `6-to-7` → `7-to-8` → `8-to-9` → `9-to-10`, and the
> prior was lifted rather than rewritten. What it did not change: `conditions-1` stays anchored at
> schema 3, `hazards-1` at schema 5, `actions-1` at schema 7, `attitudes-1` at schema 8 and
> `areas-of-effect-1` at schema 9, where each was reviewed; the frozen priors
> `accepted_prior_conditions_1_hazards_1_actions_1.json`,
> `accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1.json` and
> `accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1_areas_of_effect_1.json` are untouched
> at schemas 7, 8 and 9 and keep their own digests; schemas 3 through 9 remain recognized contracts
> with the pins above; and the schema-10 destination pin is still
> `c39e3a35e197a1d1db5c2c2b3445ff0cbf03395c91e3426353a4bce589be4be0`. The accepted mechanical
> identity is now `86cd11c2be330f5962982d8d87dfc1847815710868223257529f30bef8cdb500`, over 47 records
> and 558 spans. Because the artifact now declares the schema this build implements, the lifted-copy
> identity reported above describes the earlier state and no lift stands between the committed file
> and current authority.
>
> What it resolved, and what it did not. This acceptance *narrows* the residue by defining a target
> another batch already cited: `glossary.cover` — added by
> `areas-of-effect-1` and made representable by schema 10 — is now defined, and
> `areas-of-effect-1`'s `Cover` citation resolves. `glossary.concentration` and `glossary.speed`
> remain unresolved, no target was invented for either, and the batch added none of its own. Both
> are still explicit publication blockers, so the corpus stays incomplete and runtime-unpublished,
> the acceptance published, activated and retired **nothing**, and the full-corpus work Decision 5
> requires remains undischarged.

**Amended by representation schema 11 — the `Speed` entry.** `Speed` is printed twice in the bound
release, as a Rules Glossary definition (p188) and as `Playing the Game > Combat > Movement and
Position` (p14), joined by the source's own reciprocal citation rather than by a label match: 16
leaves, 36 clauses, 16 of them substantive. **Schema 10 can state no one of the 16 completely, and
only one of them even in part.** Of the four modes `combat/3/0` prints it admits `climb`, `crawl`
and `swim` through `MovementPermissionFact` — a family already present at schema 3, the earliest
registered contract — and refuses `jump` on the member. The three allowance clauses
(`combat/1/0`, `combat/2/0`, `combat/2/1`) reach `MovementAllowanceFact`, minted at schema 6, and
are refused on the `window` key alone; what survives without it is a bare basis that never says the
allowance is per turn. The remaining twelve reach no family at all. So the distinctions schema 11
adds, named rather than counted, are: what a Speed *is* — a distance in feet coverable on the
creature's own turn; the per-turn window on the allowance; depletion by two terminators and the
race between them; selection among several speeds and the switch mid-move; the switch's accounting
and its nonpositive prohibition; propagation of a Speed change to every special speed; *special
speed* as a named category in an open list; the `jump` member; and how a mode composes with regular
movement. The prose-bound
branch is unavailable rather than declined — no clause matches any of the six closed reason codes in
`policy.IRREDUCIBILITY_REASONS`; *"the distance in feet"*, *"a distance equal to your Speed or less"*,
*"subtract the distance already moved"* and *"until it is used up or until you are done moving,
whichever comes first"* are exact, printed, non-delegated statements — so **#137 contract 3** read
under **Decision 4** requires typed families. Schema 11 adds seven, over eleven **new** closed
vocabularies — a twelfth, `MovementMode`, it widens rather than mints:
`SpeedDefinitionFact`, `MovementDepletionFact`, `SpeedSelectionFact`, `SpeedSwitchLimitFact`,
`SpeedChangePropagationFact`, `SpecialSpeedFact` and `MovementCompositionFact`.

**Unlike schema 10, this one does add a field to an accepted family, and that is the part worth
recording.** `MovementAllowanceFact` was minted at schema 6 and carries three accepted instances over two
records (`action.dash` twice, `action.ready` once). Schema 11 adds one **optional** field,
`window: MovementWindow | None`, defaulting to `None`, so those three instances are unchanged field
for field across the lift and no accepted payload gains a key. The alternative — minting a sibling
family for the base per-turn allowance — was rejected: the family names *where a movement quantity
comes from*, and nothing in its type, its invariants or its validator asserts that the quantity was
granted by another rule. That its three accepted instances happen to sit on records that grant
movement is a property of those records. A per-turn base allowance and a Dash's extra movement are the
same kind of statement about the same budget, and a second family would have made a consumer ask which
one it was holding.

**It also widens a vocabulary accepted authority already consumes.** `MovementMode` was admitted at
schema 3 with six of its seven members, and accepted authority consumes it through
`MovementPermissionFact` at exactly one place: `condition.prone`, component
`restricted_movement`, `mode=crawl` — the single accepted instance of that family. (`action.dash`'s
two accepted movement facts are `MovementAllowanceFact`, which carries no mode; its bare *"such as
a Fly Speed or Swim Speed"* names no mode either.) Schema 11 adds `JUMP`, which is printed in the
same sentence the other modes
came from — *"Your movement can include climbing, crawling, jumping, and swimming"* — and was simply
missing. Widening is recorded the way a new vocabulary is. The other six members need no registry
row and get none — schema 3 predates the introduction manifest entirely — and schema 11 registers `jump` as
its own introduction, so a schema-8 or schema-10 reader refuses `jump` on the member alone even
though it recognises the field — the precedent schema 10 set for `CoverDegree.HALF`. That refusal is
asserted per specimen against schema 8 and schema 10, not inferred.

Decisions worth recording, because each was a shape considered.

- **`MovementDepletionFact.until` is a tuple, not a single terminator.** The sentence prints two
  stopping conditions and then resolves *between* them. *"Whichever comes first"* is a statement about
  the pair, so `resolution` has nothing to resolve unless `until` carries both, and one fact per
  terminator would make each half assert a race against an opponent it does not name. The shape is
  `AreaOriginMovementFact.suspended_by_any_of`'s, accepted at schema 9 for the same reason: a printed
  list whose members are alternatives to one another. It carries two intrinsic rules —
  `movement_depletion.until.at-least-one` and `movement_depletion.until.no-repeats` — and printed order
  is preserved rather than sorted, because the page prints an order and `resolution` is precisely the
  statement that the order does not decide the outcome.
- **A zero-movement fact for *"Or you can decide not to move"* was rejected.** `action.ready` already
  represents *"move up to your Speed"* with no extra field, so the ceiling is what `movement_allowance`
  has always meant, and a ceiling already permits being left unused. A separate fact would state a rule
  the page does not print. The clause is provenance on the allowance fact instead.
- **Folding depletion into the allowance was rejected.** The ceiling and the spending of it are two
  printed statements about one budget. One family carrying both would conflate what a turn grants with
  how it runs out, and `MovementCostFact`'s own docstring already draws that line — *"it states the
  cost, never what the cost buys"*.
- **`SpeedSwitchOutcome.FORBIDS_USING_THE_NEW_SPEED` is a prohibition, not a clamp.** The page prints
  *"If the result is 0 or less, you can't use the new speed"*. A shape that recorded only the
  subtraction, or that clamped a remainder to zero, would lose the prohibition and state arithmetic the
  source does not ask anyone to perform.
- **`SpecialSpeedListing.NAMED_IN_A_NON_EXHAUSTIVE_LIST` keeps *"such as"* open.** The four special
  speeds the entry names are stated as members of a list the page marks open. The member says so at the
  consumer, so naming four does not close the category — and the four entries that define them stay in
  later batches, which is the same asymmetry `cover-1` accepted in reverse when `CoverDegree` predated
  the entry defining the degrees.
- **`SpeedChangePropagationFact` states the rule; the worked examples are evidence.** *"If a Speed is
  reduced to 0… every special speed is also 0"* and the halving example are provenance on the
  propagation fact at `CONTEXTUAL`, not facts of their own. No arithmetic engine is implied or built:
  the fact names a scope, an equal magnitude and a same duration, and applying that to a creature's
  actual speed list is runtime.
- **`CreatureSpeedFact` was not reused for the definition.** It states what a stat block prints —
  `Speed 20 ft.` — and requires a number. *"A creature's Speed is the distance in feet the creature can
  cover when it moves on its turn"* prints no number, so stating it as a creature speed would require
  inventing one. `SpeedDefinitionFact(unit, window)` carries the unit, the quantity kind and the
  window, which is what the sentence states and no more. The two sourcing sentences — *"determined
  during character creation"*, *"noted in the monster's stat block"* — name a *source* for a value and
  print none, so they are record-level supporting authority.

None of this evaluates anything. Every member names what a rule *says*; nothing carries an expression, a
predicate, a formula, a free-form value or a dispatch table, and the vocabularies are closed, so a
consumer meeting a member it does not handle fails rather than interprets. **No parameter value, unit,
coordinate or grid semantic is invented anywhere in schema 11** — `DistanceUnit.FOOT` is the unit the
sentence prints, and there is no square, segment or corner in any vocabulary. Subtracting a move from
the allowance, choosing a route, applying the propagation rule to a creature's actual speed list and
converting a Speed to a travel rate are all runtime, where **Decision 11** and #137's Out of scope leave
them. The optional grid rules printed at `Playing the Game > Exploration > Vehicles` are outside this
**batch** by its membership rule and are not thereby outside declarative 5d: their execution is
downstream, their printed representation remains later 5d work, and nothing here prejudges or schedules
it.

The schema-11 destination pin is
`605e8b4cfdaf0cb6d4f0b65fcf0d23f3e45c4734404c9568f41dc4261eefd037`. Schemas 3 through 10 remain
recognized contracts with unchanged pins, and succession stays one row per crossing: exactly one
registered transition, `5d-lift-schema-10-to-11`, separates schema 10 from schema 11, and the build
exercises it rather than describing it. **Nothing accepted moves.** The committed artifact and every
frozen prior still declare the schema they were accepted under after this change, each keeps its own
digest, and all six per-batch anchors are retained unchanged (`conditions-1`→3, `hazards-1`→5,
`actions-1`→7, `attitudes-1`→8, `areas-of-effect-1`→9, `cover-1`→10) — the assertion this succession
most needs to make, because `actions-1` consumes the very family and the very vocabulary schema 11 extends, and a lift that
re-derived anchors would erase the record of what each batch was accepted under. The frozen six-batch
prior on disk keeps the identity the Owner accepted,
`86cd11c2be330f5962982d8d87dfc1847815710868223257529f30bef8cdb500`, over 47 records and 558 spans. Its
*lifted copy* is a different object with a different identity —
`bc8757af6483d63894ce9c9359a5e8c1c8cce0cd410c7e89f92185d5d5aa2136` — because the oracle payload carries
the representation binding and the lift re-declares exactly that; the only top-level payload key that
moves is `representation_schema`, and everything else crosses by object identity rather than by
equality. The lift rebinds; it does not rebuild.

Nothing is accepted, published, activated, or retired by this schema change, and no proposal exists for
`speed-1`. The accepted mechanical corpus is unchanged, and the two unresolved cross-batch reference
targets — `glossary.concentration` and `glossary.speed` — are still two. Schema 11 makes
`glossary.speed` *representable*; only accepting a `speed-1` proposal would resolve it, and that is a
later step. Such a proposal would close `glossary.speed` and open nine — the five entries the glossary
`See also` leaf cites and the four special speeds the definition sentence says are *"defined in this
glossary"* — taking the combined residue to ten. ~~That is arithmetic over two sets rather than a measured
result: no operation merges an accepted prior with an unaccepted draft.~~ The full-corpus work Decision 5
requires remains undischarged.

**Superseded in part at the `speed-1` proposal (2026-09-12).** Two statements above described the state
before a proposal existed. They are corrected here rather than deleted, so the record shows what changed.

1. *"No proposal exists for `speed-1`"* was true when written and is not now. The proposal artifact
   `.claude/review-notes/issue-5d-batch-speed-1-PROPOSAL.json` exists, identity
   `bd9d49427b7f2d996269e4e30a74abc26dacb7804e9176d8ca7f908b6c6a2bf8`, awaiting independent semantic
   review and Owner acceptance. Nothing about it is accepted: the accepted mechanical corpus is still the
   frozen six-batch prior and its unresolved targets are still exactly two.
2. The struck sentence was **wrong**, not merely superseded. `acceptance._merge_representation` does
   merge a lifted accepted prior with a draft, and `oracle.candidate_from_accepted_inputs` builds a
   candidate over the result. Ten is a *measured* figure: the proposal generator runs
   `validate_representation` twice — **nine** unresolved-reference findings against the draft standing
   alone, **ten** against the merge of the schema-11-lifted six-batch prior with it — and asserts both
   target lists exactly. The measurement is in memory and changes no accepted authority.

### Decision 5 — Exact completeness, not aggregate thresholds

Publication is proven through exact full-corpus accounting and accepted per-record/component obligations.
Every expected record, component, fact family, prose-bound claim, provenance edge, and reference must be
present exactly as required.

Counts, extraction floors, prose percentages, and category ceilings may detect regressions but cannot
prove completeness. An all-prose projection and a duplicated-fact projection must both fail.

**Amended by Owner Decision 2026-08-24 — duplication is a shape, not only a fact.** "A duplicated-fact
projection must fail" is the general rule that one source statement may not be published twice, and it
binds every element kind the representation carries, not only typed facts. Two forms of it are now stated
explicitly because both were reachable and neither was caught:

- **Sibling components.** Two different components of one record may not hold facts with the same
  `fact_key` when both draw it from the *same* substantive span. Facts equal by content alone are not
  duplication — a rule genuinely restated in two places is two claims — so the rule is fact equivalence
  **plus shared source provenance**, never fact equality alone, and never inferred from parsed target-key
  positions. This is deliberately not global cross-component fact uniqueness.
- **Reference ownership.** Where a record owns a citation directly (Decision 7 as amended), no component
  of that same record may state the same citation. Record ownership *means* no component states it, so the
  pair contradicts its own justification. Two different **components** citing the same wording stay legal:
  each is its own claim and each carries its own provenance edge.

### Decision 6 — Complete meaning-bearing identity

Mechanical projection identity binds:

- the exact published 5c source release;
- semantic classification;
- record assembly and membership;
- actual components and handling;
- actual structured facts and relationships;
- prose bindings and exact provenance;
- reference resolutions;
- representation schema and semantic policy; and
- normalization/canonicalization rules.

Reviewer names, timestamps, proposal origins, and comments are audit metadata and do not change semantic
identity unless the accepted semantic content changes.

Identity derivation is acyclic. Stable record/component/fact IDs derive from the projection UUID and
committed semantic keys, never local ordinals.

This identity covers the immutable base projection only. `RuleOverride` state is deliberately outside it
and carries its own separate identity under Decisions 9 and 10, so an override change never mutates or
remints the base projection UUID.

**Amended by Owner Decision 2026-08-08.** A runtime authored-authority prose overlay never contributes a
component, fact, or prose binding to this identity. Whether zero or many authored prose overrides are
applied at runtime, the projection they are applied over has exactly one `mechanical_projection_uuid`; the
authored overlay's own complete canonical form participates instead in the override-set identity governed
by Decision 9.

**Amended by Owner Decision 2026-08-24 — explicit verified schema succession, and zero identity movement
across it.** Accepted authority is committed under the representation schema it was reviewed under, and
identity binds that schema (above). A later content batch may need a wider schema, so the two have to
meet. They meet on exactly these terms, and on no others:

1. **Zero movement.** A previously accepted fact key or provenance coordinate may not move. The absence of
   published consumers or overrides does not authorize identity churn. A succession that would move one is
   refused; it is never reconciled, renumbered, or re-derived.

2. **A field added after a schema is omitted from the canonical payload when it carries no meaning.** An
   absent field and a field at its declared default state the same thing, so one canonical form serves
   both. This is what makes zero movement achievable rather than merely required: an element accepted
   under the earlier schema *already has* its later-schema canonical form, so nothing has to be rewritten
   for it to be inherited. The rule is value-keyed, never version-keyed — a fact's canonical form does not
   depend on which schema is declared.

3. **The declared version decides legality, never canonical form.** A post-succession field holding
   meaning under an earlier declaration is refused, and refused *as a restamp* — an artifact whose declared
   schema and content disagree — rather than silently emptied to reproduce a legacy identity. Fields
   introduced at or before the last-accepted schema keep unconditional emission; switching one to
   omit-when-empty would move exactly the identities this rule exists to hold still.

   *Amended 2026-08-28 (#137 round 4) — legality is checked wherever authority is created or admitted, not
   only where the schema changes.* A representation and the schema identity it declares are admissible
   together only when its meaning is legal under that version **and** its exact `(version, hash)` pair is a
   contract this build accepts authority under — the live pair, or an endpoint of the registered succession
   graph. Unknown versions, invented hashes, and known versions paired with another version's hash are one
   refusal: the union that decides what these facts may mean cannot be established. An empty lift history
   exempts neither half — an artifact that crossed no succession has said nothing about whether it was
   built under the schema it names. The rule is enforced at committed-artifact loading, at acceptance for
   both the proposed and the prior half, inside a verified lift, and at publication, which holds the strict
   end of the same rule: a projection about to become *current* authority must declare the live pair
   exactly. Being *serializable* under a version is deliberately not sufficient — schema 1 and schema 2
   payloads remain reproducible for historical reconstruction, and reproducing an identity is not admitting
   new accepted authority under it.

4. **Compatibility is declared, never inferred.** Each authorized succession is registered by its exact
   `(version, hash)` source **and** destination pair, with its destination hash written literally rather
   than derived from whatever the type surface currently is. Version ordering is not evidence: "schema 4
   is newer than schema 3" says nothing about whether schema 4 can carry schema 3's accepted content, and
   a rule that reasoned that way would authorize every future succession in advance. An unregistered,
   reversed, skipped, or hash-mismatched transition fails closed.

5. **A succession proves, it does not transform.** Before any re-declaration, every inherited element is
   proved byte-identical under both schemas, collection by collection. Nothing is normalized, reshaped, or
   defaulted on the way through: a difference is a semantic change the reviewer never saw. This is a
   stronger guarantee than a transforming lift could give — a transforming lift has to *argue* that its
   mapping preserved meaning; this one demonstrates that nothing moved.

6. **A batch states the schema it was reviewed under.** *Added by Owner Decision 2026-08-30 (#137 round
   7).* Acceptance evidence records which representation schema each retained batch was reviewed under, as
   a schema anchor beside the batch — never inside it, because a batch records what a human accepted and
   may not be rewritten by a later succession. Without it an empty lift history has two readings that
   cannot be told apart: authority genuinely first accepted under the declared schema, and authority
   reviewed under an earlier schema whose declaration was simply overwritten. The second is a restamp, and
   it loaded clean.

   An anchor names a retained batch and repeats that batch's own proposal identity; its pair must be a
   recognized contract; a batch anchored at the artifact's declaration needs no succession, and one
   anchored earlier needs a registered chain that starts where it was reviewed and terminates at the
   declaration; and every recorded crossing must be one some anchored authority actually needed. Absence
   of anchors is admitted for exactly one shape — a pre-schema-4 declaration with no lift evidence, where
   it has a single possible meaning — and the same absence under a later declaration fails. Nothing else
   is retained: no predecessor artifact, no per-element identity, no historical count, no timestamp, no
   signature.

7. **The crossing is evidence, never identity.** That an artifact was carried across a succession is
   recorded beside its acceptance batches, on the evidence half of accepted inputs, and never on the
   accepted oracle. Which schema an artifact was carried across is review and migration process, and
   process is not identity-bearing. The combined artifact declares the destination schema and takes the
   new oracle identity that follows from declaring it.

   *Amended 2026-08-28 (#137 round 3) — the recorded evidence is exactly what a loader can check.* Loaded
   evidence is read from a file, so it proves nothing about itself. Each record is therefore validated
   against the registry and the artifact's own declaration: the transition is registered by its exact
   source and destination pair under the registered lift ID, the records form a continuous oldest-first
   chain, the last destination is the schema the artifact declares, no transition repeats, and the proof
   extent names exactly the representation's collections, each of them once. What a record may **not**
   carry is a per-collection element count. The count a lift produces is true when it is produced and
   unverifiable ever after: one committed artifact supersedes its predecessor, later batches merge into
   the same collections, and no record fixes the crossing to a point in the batch sequence — the schema
   anchors added in round 7 say which contract each batch was reviewed under, never how much content
   existed when it was crossed, so they do not make a historical count checkable — and so the
   pre-lift extent cannot be re-derived, and a fabricated number would validate exactly as well as a true
   one. Evidence a reader cannot check is not evidence, and an audit surface may not state more than the
   build can support.

### Decision 7 — Build-time reference resolution

Mechanical references resolve at build time through committed source scope, aliases, and exact target
semantic keys. Unique destination names alone do not establish source intent. Bare strings, runtime
similarity, and model selection are never authoritative references.

Ambiguous, unresolved, invalid, or cross-release references block publication.

**Amended by Owner Decision 2026-08-24 — a record may own the references it authors.** Some records cite
other records in their own right: a hazard umbrella names the five hazards it collects, and no component
of that umbrella states the naming. A reference therefore has exactly one owner, and it is either the
source **record** or one named **component** of that record.

- A component-owned reference must name a component that really exists within its source record —
  unchanged, and every previously accepted reference is one.
- A record-owned reference must name a real source record and must not carry a fabricated or dangling
  component. It does not license inventing a component to hang a citation on, and a component invented for
  that purpose publishes a component the source never states.
- Everything else about a reference is unchanged and remains fail-closed: ambiguity, scope resolution,
  target existence, per-element provenance, canonical ordering, persistence reconstruction, and digest
  coverage.
- An earlier schema continues to reject record-owned reference meaning. Serializing it under a schema that
  has no such form would produce bytes an earlier reviewer would read as a component-owned reference to a
  component with an empty key, which is the restamp Decision 6 as amended refuses.

This ownership widening is a *domain* widening of the existing owner field rather than a new ownership
field beside it, precisely so that no accepted reference's canonical payload or provenance coordinate
moves.

### Decision 8 — Persist, reconstruct, prove, then publish

5d follows:

```text
build candidate
→ persist draft
→ reconstruct from persisted state
→ compute persisted-state digest
→ run exact completeness gate
→ atomically publish
```

Draft/partial projections are not active authority. Published projections are immutable. Meaning-changing
corrections *to the projection itself* mint a new projection UUID; changes to override state do not (see
Decision 9).

**Owner Decision 2026-08-01, as amended 2026-08-03 — what the 5d publication gate proves about the
bound 5c release.**

*Preservation note.* This block is recorded on `main` for the first time here. The 2026-08-01 Owner
Decision was drafted on PR #141, which remains open, draft, and unmerged; its Chroma provisions are
carried below **unchanged**, and its downstream re-proof requirement is carried in its amended form.

CRD Issue 5d owns typed interpretation and deterministic Rules Package construction. It consumes an
approved CRD Issue 5c release; it does not become a second 5c publication system. Before publishing a
mechanical projection, the gate must establish, through the narrow 5c-owned operational trust seam:

- the requested release exists and is marked published;
- the release identifier and package/release relationship are internally consistent;
- the release identifies the expected authoritative source and corpus;
- the authoritative SQLite corpus state being supplied matches the approved release's recorded
  persisted-corpus identity through a **direct operational integrity check** — not merely because an
  evidence-report hash matches;
- the corpus records 5d needs are present and reachable through the approved authoritative seam; and
- the release uses a corpus contract or schema version supported by the 5d transformation.

"Compatible with the 5d transformation" means only that 5d recognizes and supports the published corpus
contract/schema it is about to consume. This ADR does not prescribe whether engineering represents that
support through a version field, a capability declaration, or an equivalent low-cost mechanism.

The gate **fails closed** when any of these checks fails. It may record the 5c release identity, source
identity, corpus identity, and compatibility version as provenance for its own deterministic Rules
Package.

Merely because it loads an approved release, 5d must **not** reconstruct and re-hash the full source
ledger, reconciliation member, policy chain, canonical bundle, or evidence report; prove that every
historical identity was mathematically derived from every recorded predecessor; compare diagnostic
report summaries against a newly reconstructed publication history; or rerun coherent-rewrite or
adversarial mutation controls.

*Amended 2026-08-03.* The 2026-08-01 decision as drafted also required the gate to "reconstruct and
re-prove all SQLite-authoritative corpus state that seam exposes." That requirement is prospectively
superseded: it made every downstream load a re-execution of 5c's historical publication proof, which
CRD Issue 5c no longer promises. Fresh 5c publication and 5c verified reuse may still perform stronger
internal checks where they cheaply support an operational outcome; those checks do not automatically
become downstream obligations. See
[CRD Issue 5c Operational Reliability Amendment](adr-005c-operational-reliability-amendment.md) §5.

**Chroma — preserved exactly (2026-08-01).** The 5d gate **does not** open or depend on ChromaDB to
recompute the vector-backed portion of the 5c persisted-corpus digest. Chroma remains an informational,
rebuildable projection and is not mechanical authority (ADR-018 D4/D10). Loss, corruption, or absence of
the live rules-corpus vector collection after successful 5c publication is a CRD Issue 18
operational/reindex defect; it does not make the 5c source authority stale for 5d publication.

This does not weaken CRD Issue 5c. Fresh 5c publication and 5c's own verified-reuse path must continue
to write, read back, and verify the required vector projection before declaring a 5c release published
or reusable.

### Decision 9 — Deterministic effective binding and selector ownership

5d supplies a typed, immutable **effective** binding of:

- package UUID;
- release version;
- mechanical projection UUID — the immutable base projection; and
- override-set UUID — the exact applied effective override set.

Base-projection identity and override-set identity remain distinct and are never collapsed into one
value. The effective binding is **provenance-exact**, not merely mechanically equivalent: the override-set
identity names both the exact effective mechanical state applied and the exact authoritative override
records that supplied it. The canonical identity-bearing representation of every override entry therefore
carries:

- stable override identity (`override_id` or its repository-native successor);
- override origin (`house_rule`, `package_patch`, or its typed successor);
- exact typed target identity;
- operation;
- precedence/order;
- enablement state; and
- complete validated payload.

The override-set UUID is derived deterministically at binding-resolution time from that canonical ordered
state. Adding, removing, enabling, disabling, reprioritizing, retargeting, or changing the payload of an
applicable override yields a different override-set UUID, and so does deleting and recreating an otherwise
identical override under a different identity or origin: a house rule and a package patch with identical
mechanical contents are not the same provenance-exact authority. The no-overrides state has its own
deterministic override-set UUID; it is not the absence of one.

Identity is not silently broadened to incidental audit metadata. Creation timestamps, authors, comments,
and proposal history remain non-identity audit metadata unless they participate in override applicability,
ordering, or resolution. The enclosing package UUID already supplies package scope.

Each override-set UUID is the content-derived identity of one immutable, replayable override-set
**version**. That version preserves — or is deterministically reconstructable from append-only retained
evidence that preserves — the exact canonical ordered override state enumerated above. Historical
override-set versions remain retrievable after the source `RuleOverride` rows are edited, disabled,
reprioritized, retargeted, or deleted. Recording the override-set UUID while retaining only mutable
current override rows is insufficient. Current override rows remain the authoring surface; they are not
historical replay evidence. That version may be retained as a content-addressed snapshot, as append-only
version records, or as append-only events that deterministically reconstruct the canonical version; an
event log need not itself be content-addressed, but its reconstructed canonical version must reproduce and
verify the recorded override-set UUID. Which of those shapes a repository uses is an implementation choice
this ADR does not make. Override-set version retention is runtime state and is separate from the
Decision 8 projection publication lifecycle.

Rule slices, deterministic-consumer views, GameMaster authority views, applied-override provenance,
stale/mismatch validation, and replay/audit evidence identify the exact effective binding — all four
components — that produced them. Two operations follow, and they are distinct:

- **Runtime resolution and adjudication.** A recorded binding whose override-set UUID no longer matches
  the override-set UUID recomputed from current override state is `STALE` and fails explicitly; it is
  never silently re-resolved against current overrides.
- **Audit, replay, and provenance reads.** These resolve against the retained immutable override-set
  version and must succeed, reconstructing the exact effective mechanical authority originally applied
  rather than merely reporting that it differs from current override state. `STALE` is not a valid answer
  here; a failure to reconstruct is a retention defect, not a divergence signal.

Overrides never mutate or remint the base projection UUID.

A human-facing slug may resolve through one code-owned service but cannot serve as canonical authority.
Every rule-slice request carries the exact effective binding plus deterministic selectors or an explicit
whole-package flag. Invalid slugs, accidentally empty selectors, stale bindings, and mismatched releases
fail explicitly.

**Amended by Owner Decision 2026-08-08.** The "complete validated payload" every canonical override entry
already carries explicitly covers a prose-authority payload: the complete authored text of a `REPLACE` or
`APPEND` against prose authority, or the empty payload of a `DISABLE`. Changing that authored text changes
the override-set UUID exactly as changing any other enumerated field does; it never changes
`mechanical_projection_uuid`. Prose authority is targeted at the same grain as a component — stable record
and component identity — but is a distinct target kind (Decision 10), so a prose operation and a component
operation against the same record/component pair are two different targets and never collide.

### Decision 10 — Typed override completion

ADR-0007's entity-targeting override deferral is discharged by 5d.

5d defines typed patch shapes for the new record/component/fact representation and applies them in the
effective mechanical view. Existing override precedence and `DISABLE` / `REPLACE` / `APPEND` semantics
remain unchanged. Overrides never mutate the immutable base projection and never remint its identity;
the applied ordered override state is identified instead by the override-set UUID of the effective
binding (Decision 9), and applied-override provenance is reported against that binding.

Applied-override provenance resolves through the retained immutable override-set version, not through
current override rows, so an effective view recorded earlier remains reconstructable after the source
overrides are edited, disabled, reprioritized, retargeted, or deleted. That provenance is
provenance-exact: it reports the stable override identity and origin of each applied override alongside
its target, operation, order, enablement, and payload, so an audit can name which authoritative override
record supplied each change rather than only what the change was. The base projection and its identity are
unaffected either way.

`DISABLE` suppresses an exact typed target; `REPLACE` supplies a complete validated replacement for a
component or fact; and `APPEND` adds a complete typed component or fact only where the owning schema
permits multiplicity. A whole-record replacement requires an explicit record-kind-specific patch and is
never a generic JSON overwrite.

The obsolete prose-only `MechanicalEntity` target is removed under ADR-005c's pre-release clean-baseline
authority. Unmappable development targets are not guessed into new identities.

**Amended by Owner Decision 2026-08-08 — a first-class authored-authority prose overlay.** `DISABLE`,
`REPLACE`, and `APPEND` now also apply to prose authority: a fourth typed target grain scoped by stable
record and component identity, never a raw chunk, a JSON path, or an unscoped selector. Their existing
meanings extend without changing:

- `DISABLE` on prose authority suppresses that exact component's effective governing prose without
  deleting its base state or altering its typed facts. What that leaves the component's *effective*
  handling as depends on what survives — see the effective-content classification below — not on what the
  component's handling was before the disable.
- `REPLACE` on prose authority replaces the target's complete effective governing prose with exact
  authored prose, superseding both the base projection's 5c-bound prose and any previously applied
  authored prose for that target, resolved in the same ascending `(precedence, override_id)` order every
  other override uses. It also clears any source-derived irreducibility reason the component carried: that
  reason was the base corpus's judgement about the source prose this operation just discarded, and keeping
  it would be exactly the copied irreducibility claim the non-fabricated-provenance rule below forbids.
  `APPEND` and `DISABLE` leave the reason untouched — `APPEND` only adds to existing governing prose, so
  any source prose the reason describes remains effective, and `DISABLE`'s reason-preserving behavior on a
  now-empty `PROSE_BOUND` component is the named exception directly below.
- `APPEND` on prose authority preserves the target's existing effective governing prose — 5c-bound,
  previously authored, or both — and adds one more authored passage after it, in that same order.

Effective governing prose is represented as a closed discriminated form distinguishing at least:

- **source prose** — an exact `chunk_id` and its resolved 5c text; and
- **authored prose** — exact text plus the supplying override's stable identity and origin.

Authored prose is never assigned a fake `chunk_id`, 5c span provenance, or an irreducibility claim copied
from the base source; its provenance is the authored override and the retained override-set version
(Decision 9). Attaching authored prose to a component the base projection classified `STRUCTURED` — which
by definition carries no prose binding — makes that component's *effective* handling `MIXED` in every view
built from it, honestly reflecting that structured facts and authored prose now coexist; the immutable base
projection's own `STRUCTURED` classification and identity are untouched. Complete component additions or
replacements (this decision's existing `REPLACE`/`APPEND` component and record patches) may declare
`PROSE_BOUND` or `MIXED` handling and carry authored prose where their own closed schema permits it, under
the same non-fabricated-provenance rule.

**Amended by Owner Decision 2026-08-09 — final effective-state classification, not historical/sticky or
path-dependent.** An earlier draft of this decision stated that a `DISABLE` of prose authority "does not
demote" an effective `PROSE_BOUND` or `MIXED` component's handling, including a `MIXED` promotion an
earlier override in the same resolved set produced. That was wrong and is superseded:
`EffectiveComponent.handling` describes the authority surviving *after* ordered override application, not
authority that existed earlier in the sequence. It is a classification of each component's own final
`facts` and `governing_prose`, computed once at final assembly, for every component alike — whether its
authority came from a prose operation, a whole-component or whole-record `REPLACE`/`APPEND` declaring
`handling` directly, or the immutable base projection — never remembered as a sticky flag and never
dependent on which of those override families supplied the authority or which operation resolved last.
Concretely, for every component with surviving facts or surviving prose after override application:

- effective facts plus effective prose → `MIXED`;
- effective facts without effective prose → `STRUCTURED`;
- effective prose without effective facts → `PROSE_BOUND`.

A component left with neither is not content-bearing; classifying that state is out of this decision's
scope. The one settled exception is a prose-only component whose sole prose authority is suppressed: it
remains `PROSE_BOUND`, with an empty effective prose surface, because no other category honestly describes
a component with no typed facts — this is the component's already-declared handling, unmutated by the
suppression itself, so it is unaffected by whether the prose or a sibling fact was suppressed first.

So `STRUCTURED → authored prose → MIXED → DISABLE prose` finishes `STRUCTURED`, and a `MIXED` component —
however its facts and prose were supplied — whose prose is suppressed while its facts survive finishes
`STRUCTURED` the same way; a `MIXED` component whose facts are removed while its prose survives finishes
`PROSE_BOUND` the same way. A promotion to `MIXED` is never sticky, and none of this depends on the order in
which the surviving facts and prose were established. This classification affects only the effective
runtime view: the immutable base projection's own classification and identity, and every applied-override's
provenance, are unaffected either way. It does not loosen the unchanged suppression rule directly above — a
later override aimed at the *exact same* already-disabled prose target still does not apply; re-promotion
after a suppression can only come from a different target (a whole-component or whole-record replacement
clears the stale suppression for the semantic key it replaces, exactly as it already does for facts and
components).

This discharges ADR-005d's blanket prohibition on a second prose store (recorded in this ADR's implementing
code — `patches.py`'s prior docstring — and in #137 contract 3, rather than as a prior Decision clause in
this document). The narrower invariant is: there is
no duplicated store for what the SRD source says. 5c source prose remains immutable, resolves only from its
exact `RuleChunk`, and is never copied and relabeled as source authority. A separately identified
authored-authority overlay — carrying its own distinct provenance and never claiming 5c provenance — is
intentional and is exactly what this amendment adds.

Legacy chunk-targeting overrides (the pre-existing `rp_overrides` prose path) remain a distinct, obsolete
pre-release mechanism. They are not a second concurrent mechanical or GameMaster truth: the typed authority
path and views this ADR governs never read them, and their removal remains scheduled for the final
activation/legacy-retirement PR, not the PR that introduces this overlay.

**Amended by Owner Decision 2026-08-19 — an APPEND-only `OPTION` container target.** Representation
schema 2 admits a component that states an exhaustive actor choice: one whose meaning is a set of mutually
exclusive `options`, each holding its own typed facts. That structure created a multiplicity seam this
decision's `APPEND` clause above could not address. A component-scoped `APPEND` adds a fact *beside* the
options, which a choice component's schema forbids, and `(APPEND, FACT)` has never been permitted — so
adding a typed fact to one arm of a choice was a schema-permitted operation with no valid encoding. This
amendment supplies exactly that encoding and nothing more:

- `OPTION` is a **fifth exact typed target grain**, shaped by `record_key`, `component_key`, and a
  nonblank `option_key`, with `fact_key` **forbidden**. It is scoped by stable semantic identity like
  every other grain — never a JSON path, an index, or an unscoped selector — and a container together
  with one of its members is two targets, not one.
- It targets an option **only as the owning container for fact addition**. `OPTION` is not a general
  handle on a choice arm.
- Only `(APPEND, OPTION) → FactAdditionPatch` is permitted. Every other operation/`OPTION` pairing fails
  explicitly as an invalid override, exactly like any other unsupported typed pairing.
- `DISABLE` and `REPLACE` on `OPTION` remain **unsupported**, and deliberately not for the same reason
  `(APPEND, FACT)` is. An option is not missing multiplicity — it holds content that could in principle
  be suppressed or replaced. It is the **exhaustiveness** of the choice that forbids it: the source states
  these options as the complete set of what the actor may do, so removing or rewriting one arm would
  publish a choice the source never authored. That is a falsification of source authority, not a
  permitted narrowing of it.
- `APPEND` on `FACT` remains unsupported on its original grounds, unchanged by this amendment: a fact has
  no multiplicity to append into.

An option is therefore addressable as a fact container and in no other way.

This amendment is **runtime-only and identity-narrow**. `OPTION` reuses the existing `target_option_key`
column that already carries an option-qualified `FACT` target's scope; it introduces no second scope
field. Because a target's exact identity participates in the override-set payload (Decision 9), an
`OPTION` target changes the override-set identity of any state containing one — as any new authority
must. It leaves **every existing direct-target canonical payload and every already-derived override-set
identity unchanged**, so no previously recorded binding is reminted or orphaned from the retained version
it names. It does **not** change representation schema identity: `OPTION` is an override target grain, not
a representation structure, and the representation schema version and hash are unaffected.

### Decision 11 — Downstream ownership remains downstream

5d does not decide:

- Character Sheet Model completeness or storage and revalidation of the typed effective binding (2b);
- adapter capability, certification, or execution (15c);
- how GameMaster-adjudicated outcomes become trusted mechanical state or narrative canon (15c and the
  applicable canon/state owners); or
- frozen #129 / CRD Issue 15b Phase 3 / CRD Issue 19b disposition.

5d exposes exact authority seams for those later decisions.

---

## ADR Reconciliation

### ADR-005c

ADR-005c remains authoritative and is not superseded.

| ADR-005c decision | Reconciliation |
|---|---|
| **D1 — Corpus publication and adapter certification are separate** | Preserved. 5d adds a third explicit state: mechanical-projection publication, which still does not imply adapter certification. |
| **D2 — Source corpus and executable mechanical projection are distinct** | Clarified. "Executable projection" means typed executable-facing authority, not that every represented component is code-executable. Complete 5d scope includes prose-bound GameMaster authority as part of the mechanical projection. |
| **D3 — Ingestion does not generate a rules engine** | Preserved. Typed facts are declarative; execution remains hand-authored adapter code. |
| **D4 — Semantic retrieval is never mechanical authority** | Preserved. GameMaster prose retrieval resolves to exact source-bound authority; retrieval never supplies a trust-relevant value. |
| **D5 — Deterministic binding** | Implemented by 5d's package/release/base-projection/override-set effective binding and selector contract. |
| **D6 — Advertised mechanics fail closed** | Preserved for 15c. 5d supplies typed absence/ambiguity/stale/mismatch failures but does not certify adapter capability. |
| **D7 — #129 remains frozen** | Unchanged. |
| **Pre-release clean-baseline correction** | Governs 5d legacy removal. Obsolete mechanical entities and development rows receive no compatibility guarantee. |

No historical ADR-005c text is deleted. ADR-005c Decisions 2 and 5 carry forward references to this ADR
as of this change.

**Operational reliability amendment (2026-08-03).** ADR-005c is amended prospectively so that CRD Issue
5c is judged by operational reliability rather than adversarial or forensic proof. For 5d this changes
one thing only: the downstream trust boundary in Decision 8, which now verifies the narrow 5c-owned
operational seam instead of reconstructing 5c's complete publication-proof graph. 5d's own ownership is
unchanged — typed interpretation, deterministic Rules Package construction, fail-closed publication, and
provenance all stand. See
[CRD Issue 5c Operational Reliability Amendment](adr-005c-operational-reliability-amendment.md).

### ADR-0007

ADR-0007 remains a correct historical deferral for CRD Issue 5a. This ADR records that CRD Issue 5d is
the first issue requiring typed entity/component/fact override application and therefore **discharges**
the deferral.

ADR-0007 carries this status note as of this change — followed there by a link to Decisions 9 and 10 and
a statement that its historical Context, Decision, and Consequences text is preserved:

> **Discharged by ADR-005d / CRD Issue 5d.** The typed mechanical projection now defines the concrete
> record/component/fact patch families and applies them while preserving existing override precedence and
> operations.

### ADR-015

ADR-015 remains authoritative.

- Decision 3's roll-authorship invariant is unchanged.
- Decision 7's hand-authored bounded-d20 boundary is unchanged.
- 5d supplies the typed Rules Package authority from which later 15c code may verify DCs, modifiers,
  actions, costs, and effects.
- 5d projection publication does not convert ADR-015's `undetermined` behavior into adapter support.
- 15c still distinguishes truly unsupported mechanics from missing/incomplete authority.

ADR-015 Decision 7 carries a forward reference to this ADR as of this change; its historical text and
`Accepted` status are otherwise unchanged.

### ADR-018

ADR-018's semantic-retrieval boundary remains unchanged. Exact governing prose may be located for
GameMaster context, but no semantic retrieval path may author, infer, or select a trust-relevant
mechanical value. No amendment beyond a cross-reference is required, and ADR-018 Decision 10 carries that
narrowly scoped cross-reference as of this change.

---

## Consequences

### Positive

- The shipped SRD Rules Package can support complete basic-game authority without pretending every rule
  is algorithmically resolvable.
- Open-ended mechanics such as Wish and illusion effects remain playable through exact GameMaster
  authority.
- Deterministic consumers receive typed, source-linked facts instead of parsing prose.
- Missing or ambiguous authority becomes visible and typed.
- Mechanical corrections mint new immutable identity rather than silently reusing stale releases.
- Replay and audit reconstruct the exact effective authority — base projection plus the retained
  override-set version — instead of an ambiguous package/release pair that could resolve to different
  trust-relevant values over time, and they keep working after the current override rows are edited or
  deleted. Because the binding is provenance-exact, they also name which override record and origin
  supplied each applied change. Runtime stale detection remains a separate fail-closed check against
  current override state.
- 2b and 15c receive stable upstream contracts.
- A house rule or package-patch author can supply exact authored governing prose through the same typed,
  provenance-exact override path as any other mechanical patch, without corrupting or duplicating 5c
  source authority (Owner Decision 2026-08-08).

### Costs

- The accepted classification and mechanical declaration artifacts are substantial.
- Full semantic review cannot be replaced by a corpus count or unattended classifier.
- Table/stat-block reconstruction and scoped reference resolution require committed domain work.
- Typed fact and override families require maintenance as new authorized Rules Packages add mechanics.
- Every effective override change mints a new override-set identity, so consumers that record or cache an
  effective binding must revalidate it rather than assume stability across override edits.
- Retained override-set versions accumulate alongside override authoring, and pruning them forfeits the
  replay and audit reconstruction they exist to provide.
- Because identity is provenance-exact, recreating an override under a new identity or changing its origin
  mints a new override-set identity even when the mechanical result is unchanged, so authoring churn is
  visible in the binding rather than hidden by it.
- Delivery requires multiple PRs before 5d is complete.
- An effective component's governing prose can now be a mix of immutable 5c-bound passages and
  mutable-until-retained authored passages, ordered by the same precedence rule as every other override;
  operators and auditors reason about one more provenance-exact case (Owner Decision 2026-08-08).

### Rejected alternatives

1. **Treat all 5c represented text as mechanical.** Rejected: 5c includes legal, navigational, flavor, and
   explanatory material.
2. **Default unreviewed text to prose-bound.** Rejected: an empty extraction could pass.
3. **One record per `ENTRY`.** Rejected: real stat blocks, general rules, tables, and nested records
   contradict it.
4. **One component per leaf.** Rejected: real mechanics are many-to-many across spans and cells.
5. **Use extraction floors or prose ceilings as completeness proof.** Rejected: duplicates and omissions
   can satisfy aggregates.
6. **Hash only schema/classification manifests.** Rejected: actual facts could change under stale identity.
7. **Let adapter breadth decide representation breadth.** Rejected: representation and execution are
   independent.
8. **Resolve references by bare name or retrieval.** Rejected: source scope and name collisions make the
   result ambiguous.
9. **Preserve the old `MechanicalEntity` for compatibility.** Rejected: it is obsolete, prose-only, and
   authorized for removal under the pre-release clean baseline.
10. **Compile the SRD into a universal rules engine.** Rejected: many mechanics are contextual or
    open-ended, and execution remains hand-authored.
11. **Bind runtime authority to package, release, and base projection alone.** Rejected by Owner Decision
    2026-07-30 (PR #138): overrides change the effective mechanical view, so one such binding could
    resolve to different DCs, effects, or disabled mechanics over time and neither stale detection nor
    replay could reconstruct the authority actually used.
12. **Record the override-set identity but retain only current override rows.** Rejected in the same
    review: the identifier would name state that no longer exists once an override is edited, disabled,
    reprioritized, retargeted, or deleted, leaving audit and replay able to detect divergence but not to
    reconstruct the authority actually applied. This is the standing auditability invariant — operational
    state must be reconstructable from explicit retained evidence, not inferred from mutable current
    state — applied to override sets.
13. **Identify a retained override-set version by its mechanical contents alone.** Rejected in the same
    review: deleting and recreating an otherwise identical override, or changing only its origin, would
    reuse the same identity and leave no evidence of which authoritative record actually applied, which is
    the applied-override provenance Decision 10 promises. The retained state carries stable override
    identity and origin as well. Identity is not broadened past that: creation timestamps, authors,
    comments, and proposal history stay non-identity audit metadata unless they participate in
    applicability, ordering, or resolution.
14. **Integrate authored prose through the legacy `rp_overrides` chunk-targeting path.** Rejected by Owner
    Decision 2026-08-08: that path targets a raw chunk directly, which is exactly the raw-chunk/unscoped-
    selector targeting this ADR's typed override system exists to replace, and it would leave two
    concurrent, differently-shaped override mechanisms both claiming to patch mechanical authority.
    Authored prose extends the same typed record/component/fact target system instead, at a fourth grain
    scoped by stable record and component identity.
15. **Give authored prose its own irreducibility reason from the closed 5c catalog.** Rejected: that
    catalog exists for 5c's build-time semantic classification of *source* text (Decision 2), a judgment an
    override author is not making. An override-supplied component's `irreducibility_reason_code` stays
    `None`, so it can never be confused with, or copied from, a base-projection classification.

---

## Implementation Authority

The construction-ready CRD Issue 5d specification governs required outcomes, scope, architectural
boundaries, failure behavior, and acceptance evidence. Repository-native schema, module organization,
internal decomposition, implementation phases, migration design, and test organization remain engineering
decisions unless this ADR or the Issue explicitly makes a particular choice contractual.

If implementation discovers a materially better architecture that contradicts this ADR, amend the ADR and
the affected specification in advance of, or in the same PR as, the implementation. Do not merge a quiet
contradiction.
