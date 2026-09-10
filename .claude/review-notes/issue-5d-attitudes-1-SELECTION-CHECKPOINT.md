# CRD Issue 5d — batch `attitudes-1`: selection, membership, and proposal evidence

> **Superseded on 2026-09-10 — this document is the selection record, kept as
> written.** The status line below was true when this checkpoint was authored and
> is preserved rather than rewritten: it is the evidence of what was put in front
> of the Owner. The Owner then authorized acceptance of proposal
> `c571dfd6b829852e58ca066f8735b6d5944cb51c0f4b42c82052d876392bff22` as batch
> `attitudes-1`, and it was accepted. Current acceptance status lives in
> `issue-5d-attitudes-1-ACCEPTANCE-CHECKPOINT.md`. The §7 prior pins below still
> describe the frozen three-batch prior, which the acceptance did not touch.
> Nothing was published, activated or retired then either.

Status: **proposed, not accepted.** Nothing in this batch is accepted, activated,
published or retired. The publication gate is not executed at all. New semantic
acceptance requires explicit Owner authorization, which this checkpoint does not
request and does not assume.

Authority: #137, ADR-005d, `docs/architecture/known_unknowns.md`, `CLAUDE.md`.

---

## 1. Why this batch

The batch is chosen by **complete source membership**, on the rule the three
accepted batches already established: *a source-tagged entry class, plus the
untagged umbrella glossary rule that defines the tag.*

| Batch | Tagged entries | Umbrella | Records | Status |
|---|---|---|---|---|
| `conditions-1` | 15 × `[Condition]` | `Condition` | 16 | accepted |
| `hazards-1` | 5 × `[Hazard]` | `Hazard` | 6 | accepted |
| `actions-1` | 12 × `[Action]` | `Action` | 13 | accepted |
| **`attitudes-1`** | **3 × `[Attitude]`** | **`Attitude`** | **4** | **proposed here** |
| — | 6 × `[Area of Effect]` | `Area of Effect` | 7 | not selected |

`[Attitude]` is the next complete class under that rule and the smallest one
remaining. The class counts in the table are **derived from the bound ledger by
the generator and asserted**, not transcribed:

```
tag classes    {"Action": 12, "Area of Effect": 6, "Attitude": 3, "Condition": 15, "Hazard": 5}
```

### Why not `[Area of Effect]`

It is the only other complete unaccepted class, and it is deliberately deferred.
Representing Cone, Cube, Cylinder, Emanation, Line and Sphere requires an entire
spatial-geometry family that no current fact carries — point of origin, shape
dimensions, whether the origin square is included, line of effect blocked by
Total Cover. That is a schema program, and it sits directly against the settled
"no general rules engine" boundary. It remains the next candidate; this batch
does not touch it.

### Relationship to the five missing reference targets

Accepted authority currently cites five records it does not define:

```
attitude.friendly  attitude.hostile  attitude.indifferent
glossary.concentration  glossary.speed
```

Three of them are attitudes. That is a **consequence** of choosing a complete
source class, not the reason for choosing it. The batch was not assembled to
close a list, and the list is not closed by it: `glossary.concentration` and
`glossary.speed` are untagged entries in other source groups and remain
unresolved after this batch merges. The generator asserts both sets and the
audit reports the residue rather than the headline:

```
unresolved before  ['attitude.friendly', 'attitude.hostile', 'attitude.indifferent',
                    'glossary.concentration', 'glossary.speed']
unresolved after   ['glossary.concentration', 'glossary.speed']
resolved by this   ['attitude.friendly', 'attitude.hostile', 'attitude.indifferent']
```

No Owner Decision is sought for this selection. Ordinary batch selection and
schema work are already authorized by contract 3; nothing here is a new product
semantic.

---

## 2. Exact membership

Four records, sixteen leaves, **sixteen represented, zero policy exclusions**.
The boundary is re-derived at run time from the `[Attitude]` tag under *Rules
Definitions*, then cross-checked against the names the umbrella's own "See also"
prints — so an attitude added or renamed upstream fails the run rather than
silently dropping out of the batch.

| Label | Record key | Kind | Page | Leaves |
|---|---|---|---|---|
| `Attitude` | `glossary.attitude` | `GLOSSARY_RULE` | 177 | 4 |
| `Friendly [Attitude]` | `attitude.friendly` | `GLOSSARY_RULE` | 182 | 4 |
| `Hostile [Attitude]` | `attitude.hostile` | `GLOSSARY_RULE` | 183 | 4 |
| `Indifferent [Attitude]` | `attitude.indifferent` | `GLOSSARY_RULE` | 184 | 4 |

`RecordKind` is a closed vocabulary with no attitude member. `GLOSSARY_RULE` is
what these are — Rules Glossary definitions — and it is the kind `actions-1`
gave both its umbrella and its twelve entries. Minting a kind for a three-member
class would widen a closed vocabulary for one batch's convenience.

---

## 3. The exact partition

Every represented leaf is cut end to end and reconstructs byte for byte
(asserted per leaf, plus `validate_partition`: 0 findings). Twenty-four cells:

| Record | Obl. | Kind | Disposition | Text |
|---|---|---|---|---|
| `glossary.attitude` | T1 | R | supporting | `Attitude` |
| `glossary.attitude` | T2 | R | supporting | `A monster has a starting attitude toward a player character: Friendly, Hostile, or Indifferent.` |
| `glossary.attitude` | T3 | R | supporting | `See also` |
| `glossary.attitude` | T3 | X | supporting | `“Friendly,”` → `attitude.friendly` |
| `glossary.attitude` | T3 | X | supporting | `“Hostile,”` → `attitude.hostile` |
| `glossary.attitude` | T3 | X | supporting | `“Indifferent,”` → `attitude.indifferent` |
| `glossary.attitude` | T4 | X | supporting | `and “Influence.”` → `action.influence` |
| `attitude.friendly` | F1 | R | supporting | `Friendly [Attitude]` |
| `attitude.friendly` | F1 | R | supporting | `A Friendly creature views you favorably.` |
| `attitude.friendly` | F2 | **F** | **substantive** | ` You have Advantage on an ability check` |
| `attitude.friendly` | F3 | **P** | **substantive** | ` to influence a Friendly creature.` |
| `attitude.friendly` | F4 | R | supporting | `See also` |
| `attitude.friendly` | F4 | X | supporting | `“Influence.”` → `action.influence` |
| `attitude.hostile` | H1 | R | supporting | `Hostile [Attitude]` |
| `attitude.hostile` | H1 | R | supporting | `A Hostile creature views you unfavorably.` |
| `attitude.hostile` | H2 | **F** | **substantive** | ` You have Disadvantage on an ability check` |
| `attitude.hostile` | H3 | **P** | **substantive** | ` to influence a Hostile creature.` |
| `attitude.hostile` | H4 | R | supporting | `See also` |
| `attitude.hostile` | H4 | X | supporting | `“Influence.”` → `action.influence` |
| `attitude.indifferent` | I1 | R | supporting | `Indifferent [Attitude]` |
| `attitude.indifferent` | I1 | R | supporting | `An Indifferent creature has no desire to help or hinder you.` |
| `attitude.indifferent` | **I2** | **F** | **substantive** | ` Indifferent is the default attitude of a monster.` |
| `attitude.indifferent` | I3 | R | supporting | `See also` |
| `attitude.indifferent` | I3 | X | supporting | `“Influence.”` → `action.influence` |

Counts: 24 spans = 19 supporting authority + 5 substantive + **0 unresolved**.
3 components (2 `MIXED`, 1 `STRUCTURED`), 3 facts, 2 prose bindings, 7
references (all record-owned), 0 relationships, 24 provenance edges — one per
span, because no span is `UNRESOLVED` and `UNRESOLVED` is the only disposition
that admits no provenance claim.

### Honest obligation accounting

Fifteen source obligations, all discharged — and "all discharged" alone would be
misleading, so the audit classifies by **carriage**, not by whether a span
exists:

```
typed=3   prose_bound=2   supporting_authority_only=10   unresolved=0
```

Ten of fifteen clauses are naming, framing and citation — which is what a
glossary umbrella and three one-sentence entries actually are.

---

## 4. Typed vs. prose dispositions

**One schema extension, and only where the source forced it.** Two of the three
typed clauses land on an already-accepted shape and widen nothing; the third is
schema stop S-2, which schema 8 closes (§5).

`condition.charmed/social_advantage` is the load-bearing precedent, read back
off the same projection rather than quoted:

| | `condition.charmed/social_advantage` | `attitude.friendly` | `attitude.hostile` |
|---|---|---|---|
| handling | `mixed` | `mixed` | `mixed` |
| reason code | `contextual_applicability` | `contextual_applicability` | `contextual_applicability` |
| roll actor | `against_subject` | `against_subject` | `against_subject` |
| roll context | `ability_check` | `ability_check` | `ability_check` |
| roll ability | `None` | `None` | `None` |
| **state** | `advantage` | `advantage` | **`disadvantage`** |

One axis differs. `RollActor`'s own docstring names this exact case: the
charmer's actor restriction "is applicability prose on a `MIXED` component, and
admitting a member for it would have widened the union on speculation." Friendly
and Hostile are the same sentence with the polarity flipped, so they take the
same shape and widen nothing.

The prose-bound half is *which* ability check — the one made to influence this
creature. That predicate ranges over fiction the projection cannot enumerate,
which is what `contextual_applicability` means. Widening `RollContext` for it is
precisely what was already declined for the identical Charmed clause.

`attitude.indifferent` holds one `STRUCTURED` component, `default_attitude`,
carrying a single `DefaultAttitudeFact(attitude=indifferent)` — the whole clause
is typed, so there is no governing prose and no reason code. The umbrella holds
**no components**, which is `glossary.hazard`'s accepted shape: a record that
defines a term and cites its members states no mechanic of its own.

### The four-entry composition, reassessed

Reassessed beside the new family so each of the four entries keeps its own
source authority rather than being pulled into it:

| Source clause | Where its authority lives | Why not somewhere else |
|---|---|---|
| **T2** — *"A monster has a starting attitude toward a player character: Friendly, Hostile, or Indifferent."* | supporting authority on `glossary.attitude`, **and** the closure of the `Attitude` vocabulary | The sentence's mechanical content *is* the closure; the vocabulary manifest is where a closure is stated and where the schema hash covers it. Emitting a fact as well would state it twice. The accepted umbrellas are the check: `glossary.condition`'s definition is prose-bound and carries no fact, and `glossary.action` carries exactly one — `action_allowance`, a distinct mechanic, not an enumeration of the class it heads. "Starting attitude" is scope, not a second mechanic: it says an attitude is a property a monster begins an encounter with, which is what makes the Indifferent clause a *default* rather than a current state. |
| **F2/H2** — the influence-check bias | `AdvantageFact` on a `MIXED` component, `condition.charmed`'s accepted shape | Unchanged by this batch. The beneficiary stays `RollActor.AGAINST_SUBJECT`: the check is made *at* the creature the record is about. |
| **F3/H3** — *which* ability check | prose-bound, `contextual_applicability` | Unchanged. Widening `RollContext` for the purpose restriction is exactly what was declined for the identical Charmed clause. |
| **F1/H1/I1** — the qualitative definitions (*views you favorably* / *unfavorably* / *no desire to help or hinder you*) | supporting authority on their own records | They frame the term. Typing "views you favorably" would need a vocabulary of dispositions the source never enumerates, and none of the six irreducibility reasons is true of them either — they state no mechanic to be irreducible about. |
| **I2** — *"Indifferent is the default attitude of a monster."* | `DefaultAttitudeFact` on `attitude.indifferent` (schema 8) | §5. |

`DefaultAttitudeFact` deliberately does **not** carry a beneficiary, a subject
or a creature category. It states a default, not an assignment: no creature is
given an attitude by it and nothing is adjudicated at runtime. The "monster"
scope is carried by the **declared vocabulary** — `Attitude` is declared as a
monster's stance toward a player character — so the fact states a
monster-scoped default in the typed contract itself, and that enum member is
all either consumer view delivers: the typed view carries the fact, and the
GameMaster view carries it in `structured_context` on a `STRUCTURED` component
that resolves no prose and cites no span of its own — the fact entry there names
the clause by span id, never as text. Provenance establishes the **source** of that contract — I2, *"Indifferent
is the default attitude of a monster."* (`Indifferent`, p184), at T2's closure
on `glossary.attitude` — rather than carrying the scope to a consumer; the
componentless umbrella contributes no GameMaster component at all. The scope is
not in the family's name, which says only `DefaultAttitudeFact`, and it is not
in a creature-kind field, because `RecordKind` and `EligibilitySubject` have no
such member and minting one for a single source instance is the generic escape
hatch ADR-005d Decision 4 forbids.

---

## 5. Schema stop S-2, closed by representation schema 8

> "Indifferent is the default attitude of a monster."

This states a determinate rule — absent other specification a monster's attitude
is Indifferent, which then feeds `action.influence`'s check with neither
Advantage nor Disadvantage. Schema 7 carried no shape for it, and no composition
of accepted families states it: a default is not an effect, a duration, an
allowance, a roll, or a state transition.

**The governing rule is #137 contract 3**: *if a substantive family cannot be
represented by the current union, add a specific typed family or classify the
affected component honestly as prose-bound.* Two branches, and one of them is
closed here.

**Not prose-bound.** None of the six closed irreducibility reasons is
affirmatively true of the clause — nothing about it is contextual, subjective,
unbounded, delegated to the GM, an exception, or fiction-dependent. The
generator prints the catalog with a per-code disposition and checks the keys
against the live catalog, so this is a demonstration rather than a blanket
"none of them fit". Binding it anyway would record a vocabulary gap as an
irreducibility, which is exactly the misfiling the closed catalog exists to
prevent.

**So the typed branch is the one left open**, and schema 8 takes it with the
minimum that states the clause:

| | |
|---|---|
| fact family | `default_attitude` → `DefaultAttitudeFact(attitude: Attitude)` |
| vocabulary | `Attitude` = `friendly`, `hostile`, `indifferent` |
| registered transition | `5d-lift-schema-7-to-8` |
| accepted families changed | none — no added, required or nullable field, no ownership form |
| schema hash | `8a125f6c4c9929109879ad98a8f14a4ec1d0c7f5fe56fe4f894dafbdf707afff` |

The vocabulary is admitted at its **printed closure**, not at the one member
this batch uses: *"A monster has a starting attitude toward a player character:
Friendly, Hostile, or Indifferent."* enumerates the class in one line. That is
`MovementMode`'s accepted reasoning. ADR-005d Decision 4 is satisfied — a
specific typed family with a closed vocabulary, schema and tests; no generic
numeric or key-value escape hatch, no runtime-interpreted script, no rules DSL.

### Correction: sibling count is not an admission gate

An earlier revision of this checkpoint and of the generator asserted that "the
typed vocabularies are evidence-bound: a member is admitted only with siblings
in more than one section", and treated S-2 as blocked on an Owner Decision. That
claim was wrong, and it is corrected here rather than quietly dropped.

The rule it invoked was **explicitly withdrawn** by
`issue-5d-actions-1-SCHEMA-STOP-CHECKPOINT.md` §6, "The admission rule,
corrected". The accepted union records the counterexample in its own source:
`MovementPermissionFact` is "the thinnest family admitted here", two instances,
and its docstring states that "its vocabulary is stronger than its sibling
count." `BenefitUseLimit` has one member; `EligibilitySubject` has two. The
`StateEffectKind` evidence standard and the full-corpus closure standard are
about *those* families' own admissions; neither is a universal prohibition on
every other family.

So this is ordinary issue-scoped engineering under contract 3 and ADR-005d
Decision 4, not a new product decision, and no Owner Decision is sought for it.

The corpus sweep is **retained**, rekeyed, and reported as what it measures:

```
schema stop    S-2 closed by representation schema 8; exact-phrase sweep
               1 leaf in 1 section over 28109 represented leaves
               (disclosure, not an admission test)
```

It is an exact-phrase count of `is the default` over the represented leaves. It
shows this clause is the only leaf that states a default *in those words*. A
paraphrase would not match it, so it is **not** evidence that no semantically
related default exists elsewhere in the corpus, and no broad corpus program is
needed to justify the family — the withdrawn count rule was the only thing that
would have required one.

S-1 was closed in schema 7 by `actions-1`; S-2 is this batch's own stop, and it
is closed the same way: with a specific typed family, not engineered away and
not deferred.

---

## 6. Reference scope

Seven references, **all record-owned** (`from_component_key == ""`), all sited
where the source *cites a record as a defined term* — not at every place it says
the word. That is the accepted rule, not a new one:

- `glossary.hazard` emits its five references from its quoted "See also" list;
  *"A hazard is an environmental danger."* is supporting authority.
- `action.dash` emits `Speed` from its "See also" leaf while its body's other
  mentions of Speed carry facts.
- `glossary.condition` and `glossary.action` emit from their printed
  enumerations, the only place they cite their members.

So `glossary.attitude`'s four references come from its "See also" leaf, and its
body sentence is the record's own definitional framing. Siting the same terms in
both places would also have **collided**: `reference_target_key` keys on
`source_text`, and the term is spelled identically in both leaves.

All four cross-batch citations target `action.influence`, which accepted
authority already carries. This batch therefore adds **no unresolved citation of
its own**:

| Gate | Findings | Targets |
|---|---|---|
| standalone | 4 | `action.influence` ×4 (defined by the prior, absent from this draft alone) |
| merged with the accepted prior | 2 | `glossary.speed`, `glossary.concentration` |

Both counts are derived from the drafts by the generator, not pinned in advance.

---

## 7. Preservation of the accepted prior

The frozen three-batch prior, read only, by content identity:

```
tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1_actions_1.json
content sha256  87864b6ac81e4f8baf57eddf9524dade1b2045a5fc804c79b3d57412c87f46fc
blob            a729a797594e1156b279fac76c3073c733707a2f
oracle identity 8c41b01e92878c614fad5c039c006c66221a4cc55cfab68698ef9302865a6eee
batches         actions-1, conditions-1, hazards-1
schema          5d-representation-schema-7 / 80e853ef…
35 records · 463 spans · 106 components · 47 prose bindings · 39 references · 480 provenance
```

Digest and blob asserted before **and** after the run; the live committed oracle
is read as a **mutation sentinel only** and asserted byte-identical afterwards.
Never loaded, lifted, merged, or recorded as an input.

**Zero movement**, over all six representation collections:

```
disjointness   {"span_overlap": [], "leaf_overlap": [],
                "collection_overlap": {"records": 0, "components": 0, "prose_bindings": 0,
                                       "relationships": 0, "references": 0, "provenance": 0}}
```

plus, per collection: the merged prefix is byte-identical to the prior, no prior
payload is absent from the merge, and element counts sum exactly.

**One registered crossing, exercised rather than described.** The prior is
anchored at schema 7; this batch proposes under schema 8, which S-2 required.
The step is looked up in the registry rather than named, and `verify_lift_path`
re-proves the accepted content element by element under the new contract:

```
succession     5d-representation-schema-7 -> 5d-representation-schema-8
               via ['5d-lift-schema-7-to-8'], verified element by element
```

**Accepted bytes are never restamped.** The frozen prior still declares schema 7
after this run and is asserted unchanged, digest and blob, before and after. The
crossing is a property of the *pair*, not a field the file gains — and
performing it against committed authority is part of acceptance, which this run
does not do and does not request.

---

## 8. Evidence

Deterministic native loading and validation, re-executed in a separate process:

```
identity       c571dfd6b829852e58ca066f8735b6d5944cb51c0f4b42c82052d876392bff22
schema         5d-representation-schema-8 / 8a125f6c4c9929109879ad98a8f14a4ec1d0c7f5fe56fe4f894dafbdf707afff
prior schema   5d-representation-schema-7 / 80e853ef9433ba2e7232c384a7192235692463c9954f5ff766be1fafade6f43d
policy         5d-semantic-policy-1 / e6363968d6ee8ec288e6c7e3382907a1afd8bf2aad0b18e153aec439b5aa9454
deterministic  True  (final bytes, parent vs separate process)
newlines       LF (asserted: no CR byte in either artifact)
final proposal sha256  b310565f60374e8d169ceb992fb73e6c9f82768ee7664673c48bd56180d80763
final audit    sha256  d59ced7472fb21491ecf5e32233dd5121bbf83d4815c8b7841ed8b58dfd80a8c
```

| Seam | Findings |
|---|---|
| build-time draft shape (`representation_draft_violations`) | 0 |
| held authority shape (`held_structure_violations`) | 0 |
| component rules (damage + roll outcome + option sets) | 0 |
| fact invariants (`fact_invariant_violations`, per fact) | 0 |
| partition accounting (`validate_partition`) | 0 |
| reason codes (`validate_reason_codes`) | 0 |
| committed-loader round trip (`representation_payload` → `_representation`) | passes |
| representation gate, standalone | 4 (unresolved `action.influence`, expected) |
| representation gate, merged with the accepted prior | 2 (`glossary.speed`, `glossary.concentration`) |

**Consumer boundary.** `_base_records` — the function every consumer of
mechanical authority goes through — is applied to the merged candidate **in
memory**, and the values above are read back off the resulting objects. Nothing
is persisted, published or activated. `action.influence`'s three citations now
assemble:

```
consumer       action.influence -> ['attitude.friendly', 'attitude.hostile', 'attitude.indifferent'] all present
```

Each typed fact carries exactly the span that states it; each `MIXED` component
carries exactly one governing prose extent. The schema-8 family is read back the
same way — `attitude.indifferent` → `default_attitude` → one fact whose
`attitude` is the closed vocabulary member `indifferent`, off a `STRUCTURED`
component with no governing prose and no reason code. That is the addition's
entire consumer-visible effect: a vocabulary member, not prose to parse and not
an inference off the record key.

**Zero validator findings is necessary and insufficient.** These checkers judge
shape, not fidelity. This is material for semantic review.

### Artifacts

| File | Role |
|---|---|
| `src/afterworlds/ingestion/mechanical/representation.py` | `Attitude`, `DefaultAttitudeFact`, its `FactFamily` member and the schema-8 payload/manifest |
| `src/afterworlds/ingestion/mechanical/schema_lift.py` | `SCHEMA_8_VERSION` / `SCHEMA_8_HASH` and the registered `5d-lift-schema-7-to-8` step |
| `src/afterworlds/ingestion/mechanical/projection.py` | the family's projected form, so `_base_records` hands it back as a vocabulary member |
| `.claude/review-notes/issue-5d-batch-attitudes-1-generator.py` | executable proposal generator |
| `.claude/review-notes/issue-5d-batch-attitudes-1-PROPOSAL.json` | the proposal |
| `.claude/review-notes/issue-5d-batch-attitudes-1-audit.json` | full per-span audit, partitions, sweep, precedent, zero-movement evidence |
| `tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1_actions_1.json` | the frozen three-batch prior |
| `tests/ingestion/mechanical/test_attitudes_1_frozen_prior.py` | pins that prior, its anchors, its residue and the one registered crossing to this build |
| `tests/ingestion/mechanical/test_schema_8_default_attitude.py` | the source-case module for the new family |

`test_schema_8_default_attitude.py` is the executable half of §5, on the
precedent of `test_schema_7_casting_time_gate.py`: the mint declares one family
and one vocabulary and no other kind of row; the vocabulary is its printed
closure; schema 7 refuses the fact and schema 8 admits it, so the lift carries
something; the wire contract round trips and refuses an attitude outside the
closure rather than repairing it; and `_base_records` hands a consumer the
vocabulary member.

---

## 9. Unresolved residue

1. **`glossary.concentration` and `glossary.speed`** — still cited and still
   undefined after this batch merges. Untagged entries in other source groups;
   a later glossary batch.
2. **`[Area of Effect]`** — the remaining complete tagged class, deferred on the
   spatial-geometry family it would require.

S-2 is **not** residue: it is closed above. No `UNRESOLVED` span remains in this
batch. What remains Owner-facing is acceptance itself, which is also what would
carry committed authority across `5d-lift-schema-7-to-8`; this run proves the
crossing and performs none of it.

## 10. Architecture Notes

No drift from design principles. Rules Package remains mechanical canon
(invariant 8); nothing crosses into Story Bible persistence or authority. The
one schema extension follows the registered transition path — `SCHEMA_LIFTS`
gains `5d-lift-schema-7-to-8`, and the affected production consumers
(`projection`, the committed loader, the override seam, `_base_records`) are
covered rather than assumed. Scope boundaries are surfaced rather than resolved
in code (invariant 12): `[Area of Effect]` is named as deferred, not quietly
narrowed away.

**Recorded correction.** A prior revision of this batch reinstated a universal
cross-section sibling-count precondition on admitting typed families, and used
it to classify S-2 as blocked on an Owner Decision. That rule had been
explicitly withdrawn by `issue-5d-actions-1-SCHEMA-STOP-CHECKPOINT.md` §6, and
`MovementPermissionFact` is the counterexample in the union's own source. The
claim is removed from the generator, the audit and this checkpoint, and the
corpus sweep is retained only as the exact-phrase measurement it actually is
(§5). This is an authority-overgeneralization defect, not a product question:
under #137 contract 3 and ADR-005d Decision 4 the work was always ordinary
issue-scoped engineering.

**No conflicting authority remains open.** The only competing texts were the
withdrawn admission rule and contract 3; the withdrawal is explicit and dated in
the actions-1 schema-stop checkpoint, so there is nothing left for the Owner to
adjudicate here.

The sweep behind that verdict is stated rather than implied. Every occurrence of
the sibling-count language in `docs/` and in the committed review notes was read
and classified: `known_unknowns.md` lines 281, 353 and 421 all state a standard
for **discharging a Known-Unknown group** — 421 says so in as many words, *"This
document's standard for that…"* where *that* is discharge — and 353 is a factual
description of `EligibilitySubject`. None of them is an admission gate on a new
family, so none competes with contract 3. The earlier draft's error was reading
the discharge standard as an admission gate; a note at that paragraph in
`known_unknowns.md` now says which of the two it is. The remaining hits are in
uncommitted `.claude/review-notes/` drafts from earlier batches, which are
working material and not authority — and the newest of them,
`issue-5d-schema-evolution-across-batches-CHECKPOINT.md` line 288, already
records the same correction: *"the ≥2-rules/≥2-sections bar is a review
heuristic."*
