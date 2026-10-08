> **SUPERSEDED — historical checkpoint record, preserved intact.**
> The stop this packet reports was acted on: the schema-closure PR (#153) closed the typed union against
> the gaps in §7, and the batch was regenerated from the same selection rule. The counts, the proposal
> identity (`dfcee0…`), and the 33 `UNRESOLVED` clauses below describe the **pre-closure** state and no
> longer match `issue-5d-batch-conditions-1-PROPOSAL.json` alongside it. For the current state and the
> per-clause dispositions, see `issue-5d-conditions-schema-closure-log.md`. Nothing here is rewritten —
> this is the record of why the batch stopped.

# CRD Issue 5d — first production-content batch: proposal checkpoint

**Status:** proposal stage only. Nothing here is accepted authority. No branch, commit, PR, oracle,
`AcceptedInputs`, projection, publication, or activation was produced. `accept_proposal` was not called.
Silence, passing validators, and the existence of the generated proposal are **not** acceptance.

**Starting state.** `origin/main` = `c4c7edc2ac9fd7b3b6cb06e7ad9038a5e06b3aac`, which **is** the merge
commit of PR #151 (`feat(mechanical): production-authoring workflow and evidence-backed schema
expansion (#137)`) — not merely an ancestor of it. Local `main` was fast-forwarded from the stale
`b8b42cd` to that exact SHA; all analysis below ran on it.

**Authority applied.** Live GitHub Issue #137; `docs/decisions/adr-005d-complete-typed-mechanical-authority.md`;
`CLAUDE.md`; the merged 5c operational trust seam; the proposal/acceptance/`AcceptedInputs` seam landed
through PR #151.

---

## VERDICT FIRST — this batch cannot be accepted until a schema decision is made

The recommended batch is the right boundary and the generated proposal is structurally valid, but the
task's second stop condition is met: **a new schema/ownership decision is required before acceptance.**

Building the batch surfaced **33 clauses (of 159 accepted-span candidates, across 15 of the 16 records)
whose mechanics the current closed typed fact union cannot faithfully carry**, and which are *not*
affirmatively irreducible. Four of those gaps are not "lossy" — they are demonstrably **false or
structurally invalid** under the current union (§7). Classifying them `PROSE_BOUND` to make the batch
acceptable is exactly the move #137 contract 2 and the task prompt forbid, so they are proposed as
`UNRESOLVED`.

That choice is enforced by the seam, not by this document:
`accounting.validate_acceptance` reports `span …: unresolved classification` for every `UNRESOLVED` span,
so **an `AcceptedInputs` artifact carrying them cannot validate.** The proposal is therefore
un-acceptable by construction until the owner disposes of §7.

**Recommended path:** an evidence-backed schema-expansion PR first (the PR #151 precedent — families
justified by measured corpus need), then this batch as the first content batch. §7 is the decision menu.
**Literal narrower boundary** if that path is rejected: §5.4.

---

## 1. The proposed batch, its exact selection rule, and why it is a natural review unit

**Batch id:** `conditions-1`

**Selection rule (exact predicate, retained as evidence, never re-run):**

> Every 5c leaf of release `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` / `5.2.1-corpus.36b786d8-fa2` whose
> final disposition is `REPRESENTED` and whose `container_path` contains one of the 16 `ENTRY` container
> ids listed in §2.1 — the 15 `… [Condition]` entries and the `Condition` entry of the Rules Glossary.

The predicate resolves to **exactly 134 leaves**, asserted per-entry in the generator (a leaf-count
mismatch aborts generation rather than silently reshaping the batch).

**Why it is a natural review unit, from corpus evidence rather than a size target:**

1. **It is the corpus's own closed set.** The `Condition` entry states *"This glossary defines these
   conditions:"* and enumerates exactly fifteen names. `representation.ConditionKind` is already a closed
   15-member enum with exactly those members. The batch boundary is the source's own enumeration, not a
   slice through it.
2. **It is self-referential and complete.** Every condition-to-condition dependency in the corpus
   (Paralyzed/Petrified/Stunned/Unconscious → Incapacitated; Unconscious → Prone; Petrified → Poisoned;
   `Condition` → all fifteen) has both endpoints inside the batch. Nothing points outward to a condition
   that is not here.
3. **It is the simplest assembly shape in the corpus.** One record per `ENTRY`, 4–16 paragraph/stat-field
   leaves each, no table-cell fragmentation, no composite sibling assembly, no cross-page grids. The
   pre-implementation checkpoint independently measured the Rules Glossary as *"the cleanest assembly
   shape in the corpus"*.
4. **It is legible at review scale.** 16 records / 134 leaves / 159 spans / 20 components / 25 facts.
   Every span's text fits in this document (§2.3, §7.1).
5. **The alternatives are not smaller.** §5 shows the next natural boundary out (the whole Rules Glossary)
   is 1,024 leaves, and that no smaller unit is both meaningful and canary-bearing.

---

## 2. Every included source page, chunk, leaf, and accepted-span candidate

### 2.1 The 16 source entry containers

| Record key | Entry container id | Printed page | Leaves |
|---|---|---:|---:|
| `condition.blinded` | `c32b2121-0435-56e6-a5e2-ad9cf036eff1` | 177 | 6 |
| `condition.charmed` | `f1a479df-23ef-5f59-9832-bced7378d751` | 178 | 6 |
| `glossary.condition` | `d870d1e7-a1e8-5f21-a20f-f6ab75b124ae` | 179 | 6 |
| `condition.deafened` | `4ed2cf15-4ff2-5a7a-b5be-b03191e0b84a` | 181 | 4 |
| `condition.exhaustion` | `f147f80e-d414-5641-82c4-faae86a43fac` | 181 | 10 |
| `condition.frightened` | `ad8e1efe-ca67-57b9-b0ce-14d20fbc1134` | 182 | 6 |
| `condition.grappled` | `bd9e201f-5cca-57d0-93eb-fa733fd65a37` | 182 | 8 |
| `condition.incapacitated` | `f1a9cb48-eebf-5be4-a8a0-cbdf9c21797f` | 184 | 11 |
| `condition.invisible` | `8d94d9c0-49ce-5ab7-8ec6-c77663a0b407` | 184 | 8 |
| `condition.paralyzed` | `c7f995c3-4d6a-515b-98ff-04d100ed0292` | 186 | 12 |
| `condition.petrified` | `26c994eb-fab4-5901-9546-012545a46d0c` | 186 | 16 |
| `condition.poisoned` | `176a6231-487a-529c-8f90-0f85241f54fd` | 186 | 4 |
| `condition.prone` | `376e9f0d-2862-59ce-b685-3497bd5b6e4d` | 186 | 7 |
| `condition.restrained` | `d399423e-818c-55d4-b907-9e96f6139b3d` | 187 | 8 |
| `condition.stunned` | `1cc5f45a-f707-5928-8c1b-69f32a5b7347` | 189 | 8 |
| `condition.unconscious` | `0f3e18ea-fb81-5ef6-a66c-8020e25f5f8b` | 191 | 14 |
| | | | **134** |

**Printed pages touched:** 177, 178, 179, 181, 182, 184, 186, 187, 189, 191 — all inside the
`Rules Glossary` top-level section container `5436892a-8f86-5774-8f2b-09553e1e4fb0` (p176).

### 2.2 Chunks

**134 chunks — one per leaf.** Verified on this build, not assumed: the production release's
`rp_chunks` ↔ `LedgerLeaf` relation is a strict bijection (28,109 chunks, 28,109 projection edges, every
edge covering its whole leaf, all role `authoritative`). The generator never relies on that property: it
calls `BoundCorpusSnapshot.chunk_relative_range` per prose binding, which **fails closed** where the
coordinate mapping would be ambiguous. All 5 prose bindings resolved; none needed a fallback.

Every included leaf id, its chunk id, and every span's exact offsets are in
`issue-5d-batch-conditions-1-PROPOSAL.json`. That payload deliberately carries **no source text** — span
text lives in the 5c corpus and is never copied into a second store — so the per-span text a reviewer
needs to read is in the companion audit trail `issue-5d-batch-conditions-1-audit.json` (record, leaf id,
span id, offsets, exact text, disposition, for all 159 spans).

### 2.3 Accepted-span candidates — 159, over 134 leaves

| Disposition | Spans |
|---|---:|
| `SUPPORTING_AUTHORITY` | 96 |
| `UNRESOLVED` | 33 |
| `SUBSTANTIVE` | 30 |
| `NON_MECHANICAL` | 0 |
| **total** | **159** |

Every one of the 134 leaves is partitioned **gap-free and non-overlapping** over its full canonical text;
`accounting.validate_partition` was run per leaf and reported **0 violations**. Span ids are
`derive_span_id(leaf_id, char_start, char_end)` — content-derived, never positional.

12 of the 134 leaves are cut into more than one span. Every cut is forced by one rule, not by taste: a span may carry
at most one `PRIMARY` provenance claim, so a sentence stating two typed facts must be partitioned at
phrase granularity. Example — Blinded p177:

```
'Attack rolls against you have Advantage, and your attack rolls have Disadvantage.'
 └─ [0,40)  SUBSTANTIVE  → AdvantageFact(advantage, attack_roll)      PRIMARY
 └─ [40,81) SUBSTANTIVE  → AdvantageFact(disadvantage, attack_roll)   PRIMARY
```

**0 spans are `NON_MECHANICAL`.** This batch contains no legal, navigational, flavour, attribution, or
authoring-guidance text, so no closed reason code is used and `semantic_policy_hash()` is untouched.

---

## 3. Proposed semantic dispositions and non-mechanical reasons

**Non-mechanical reasons used: none** (see above). The dispositions actually in play:

| Disposition | What it is proposed for here | Count |
|---|---|---:|
| `SUPPORTING_AUTHORITY` | entry headings (`'Blinded [Condition]'`); frame sentences (`'While you have the Blinded condition, you experience the following effects.'`); effect sub-headings (`'Attacks Affected.'`, `'Speed 0.'`, `'Can't See.'`); the `Condition` entry's definitional paragraph; the 15 condition names in its enumeration | 96 |
| `SUBSTANTIVE` | clauses stating a mechanic the closed union carries exactly (25 fact-bearing spans) plus 5 applicability qualifiers bound as exact governing prose | 30 |
| `UNRESOLVED` | 33 clauses that state a real mechanic the closed union cannot carry faithfully, and which are **not** affirmatively irreducible — §7 | 33 |

`UNRESOLVED` is used here in exactly its contract-2 sense: *"cannot yet be classified safely and blocks
publication."* It is not a backlog bucket for unread text — every one of the 33 is read, quoted, and
dispositioned in §7.1. It is the honest alternative to the forbidden move of calling a crisp deterministic
mechanic `PROSE_BOUND` because the schema is missing.

**Component handling** (20 components):

| Handling | Count | Example |
|---|---:|---|
| `STRUCTURED` | 15 | `condition.poisoned/checks_and_attacks` — two `AdvantageFact`s, no prose |
| `MIXED` | 4 | `condition.frightened/checks_and_attacks` — two `AdvantageFact`s plus the bound qualifier *"while the source of fear is within line of sight"* |
| `PROSE_BOUND` | 1 | `glossary.condition/condition_definition` |

**Irreducibility reasons proposed** (both from the closed frozen catalog, unchanged):

* `contextual_applicability` ×4 — applicability qualifiers whose scope depends on fiction the projection
  cannot enumerate: *"to interact with you socially"* (Charmed), *"while the source of fear is within line
  of sight"* (Frightened), *"against any target other than the grappler"* (Grappled), *"If a creature can
  somehow see you, you don't gain this benefit against that creature"* (Invisible).
* `natural_language_exception` ×1 — `glossary.condition/condition_definition`, bound to
  *"A condition doesn't stack with itself; a recipient either has a condition or doesn't. The Exhaustion
  condition is an exception to that rule."* A stated general rule plus a named exception to it is
  irreducible without executable interpretation. This is an affirmative judgement, not a schema
  workaround.

---

## 4. Proposed records, components, facts, relationships, references, prose bindings, provenance, obligations

| Element | Count |
|---|---:|
| Records | 16 (15 `CONDITION`, 1 `GLOSSARY_RULE`) |
| Components | 20 |
| Typed facts | 25 |
| Prose bindings | 5 |
| Relationships | **0** |
| References | 15 |
| Provenance claims | 126 (25 `PRIMARY` fact, 5 `PRIMARY` prose-binding, 96 `CONTEXTUAL`) |
| Derived obligations | 16 (one per record) |

### 4.1 Typed facts — 25, across 2 of the 20 closed families

| Family | Count | Where |
|---|---:|---|
| `advantage` (`AdvantageFact`) | 19 | Blinded ×2, Charmed ×1, Frightened ×2, Grappled ×1, Incapacitated ×1, Invisible ×3, Paralyzed ×1, Petrified ×1, Poisoned ×2, Prone ×1, Restrained ×2, Stunned ×1, Unconscious ×1 |
| `condition_effect` (`ConditionEffectFact`) | 6 | Paralyzed, Petrified, Stunned → `(incapacitated, applies)`; Petrified → `(poisoned, immunity)`; Unconscious → `(incapacitated, applies)` + `(prone, applies)` |

Only 2 of the 20 declared families are exercised, and 18 are untouched. **That imbalance is itself the
finding**, not a property of the batch: §7 shows the missing mechanics are not exotic — automatic failure,
speed nullification, action prohibition, critical-hit promotion, and unqualified-resistance are the
ordinary content of the SRD condition rules.

### 4.2 Relationships — deliberately zero

*"You have the Incapacitated condition"* is carried **typed**, as
`ConditionEffectFact(INCAPACITATED, APPLIES)`, not as a `RelationshipDraft` edge. No member of the closed
`RelationshipKind` union (`SCOPED_WITHIN`, `GRANTS`, `PREREQUISITE`, `SPELL_LIST_MEMBER`) means
"applies". **Review question, surfaced not decided:** a consumer reading only the relationship graph sees
no edge from Unconscious to Prone. Whether condition-application should also be a relationship kind, or
whether the typed fact is the complete claim, is a modelling decision for the owner.

### 4.3 References — 15, all resolving inside the batch

From `glossary.condition/condition_definition`, scope `srd-5.2.1/rules-glossary`, one per name in the
enumeration (`'Blinded'` → `condition.blinded`, … `'Unconscious'` → `condition.unconscious`).

This makes the batch exercise **build-time reference resolution for real**:
`validation._validate_relationships_and_references` requires every `target_record_key` to be a declared
record, and 15/15 resolve in-batch with no ambiguity (all 155 glossary entry base names are distinct).

### 4.4 Prose bindings — 5

Each names its 5c `chunk_id`, the accepted `span_id` it governs, and chunk-relative offsets **recomputed
from the bound release** by `chunk_relative_range` and re-checked by `validation._validate_prose_extent`.
No text is copied into a second store; all 5 resolve to `SUBSTANTIVE` spans.

### 4.5 Obligations — 16, derived not hand-written

`oracle.derive_obligations` produces one `RecordObligation` per record from the representation itself
(`load_oracle` requires the committed file's obligations to equal it exactly). Notable: **`condition.deafened`
and `condition.exhaustion` carry no components at all**, so both derive an obligation with an empty
`structured_fact_families` and no `prose_bound_components` — records that assert nothing. Exhaustion is the
starker case: all four of its effect clauses are `UNRESOLVED` (§7.1 #4–#7), so a whole SRD condition
reaches the projection as headings only. That is the correct, honest consequence of §7 and another reason
the batch must not be accepted as-is.

---

## 5. Complete dependency closure, and what is deliberately excluded

### 5.1 Closed inside the batch

* **Condition→condition**: all 6 edges have both endpoints in-batch (§1.2).
* **References**: 15/15 resolve to in-batch records.
* **Prose**: 5/5 bind to in-batch chunks of in-batch leaves.
* **Provenance**: every fact, prose binding, and reference carries ≥1 edge to a 5c leaf subspan;
  `validation` reported no unclaimed substantive span, no unlinked supporting span, and no conflicting
  primary claim.

### 5.2 Outbound lexical targets — measured, and each dispositioned

A candidate extractor over all 155 glossary entry base names finds **16 depth-1 outbound targets** from
the 16-record seed. None becomes a `ReferenceDraft`, and each disposition is stated rather than assumed:

| Outbound term | Disposition in this proposal |
|---|---|
| Advantage, Disadvantage | **carried by closed enum** `AdvantageState` — a typed fact, not a name lookup |
| Initiative | **carried by closed enum** `RollContext.INITIATIVE` |
| Immunity, Resistance | **carried by closed enum** `DamageResponseKind` / `ConditionEffectKind.IMMUNITY` |
| Long Rest | **carried by closed enum** `RecoveryTrigger.LONG_REST` — but the clause using it is `UNRESOLVED` (§7.1 #7) |
| Damage | **carried by closed enum** `DamageType` — but the clause using it is `UNRESOLVED` (§7.1 #21) |
| Action, Bonus Action, Reaction | enum `ActionCost` exists but states a **cost**, not a prohibition → `UNRESOLVED` (§7.1 #11) |
| Speed | no recipient-effect family; `CreatureSpeedFact` is stat-block authority → `UNRESOLVED` (§7.1 #9/15/19/26/30) |
| Critical Hit | **no family** — the deferred *critical changes* group → `UNRESOLVED` (§7.1 #17/32) |
| D20 Test | **no family** → `UNRESOLVED` (§7.1 #5) |
| Concentration | **no family** → `UNRESOLVED` (§7.1 #12) |
| Surprise | not cited as a record; the mechanic is the Initiative advantage fact |
| Attack [Action] | not cited as a record; the mechanic is the attack-roll advantage fact |

### 5.3 Why the closure is not taken lexically — the evidence against "quiet narrowing"

If every capitalized glossary term in the seed were made a `ReferenceDraft`, the transitive closure is:

| Closure rule | Entries | Leaves | Share of the 155-entry / 941-leaf glossary |
|---|---:|---:|---:|
| seed only | 16 | 134 | 10% / 14% |
| case-sensitive lexical closure | **90** | **628** | 58% / 67% |
| case-insensitive lexical closure | **114** | **702** | 74% / 75% |

So lexical reference closure does not stop anywhere useful — it swallows most of the glossary, and the
next honest stopping point is the whole `Rules Glossary` section (1,024 represented leaves). **That is the
concrete evidence that the recommended boundary is derived, not chosen for size.**

### 5.4 Deliberately excluded

* **The 83 Rules Glossary leaves outside every `ENTRY` container** (3 headings, 14 paragraphs, 66
  table cells) — including `'Rules Glossary'`, `'Glossary Conventions'`, and the conventions prose
  (*"Tags in Brackets."*, *"You."*, *"See Also."*, *"No Obsolete Terms."*). Excluded because they belong
  to the glossary-wide `GENERAL_RULE`/`GLOSSARY_RULE` assembly, not to any condition record. They are
  adjacent to the boundary and would surprise a reviewer if unstated.
* **The other 139 glossary entries** (807 leaves).
* **The narrower literal boundary**, required by the prompt and reported honestly: the smallest unit with
  **zero** §7 gaps is `{glossary.condition, condition.poisoned}` — 10 leaves, 13 spans, 2 records, 2 facts,
  1 prose binding, 15 references (14 of which would then **fail** reference closure). It still exercises
  canary 7. It is **not recommended**: with 14 dangling references it is not dependency-closed, and two
  records are not a meaningful review unit. It is reported because the prompt asks for a narrower candidate
  boundary, not because it is a better one. The recommended narrowing is the **schema-decision-first path**
  in the verdict.
* **Everything downstream**: conditions applied by spells, creatures, and magic items are elsewhere in the
  corpus and reference these records; nothing here forward-declares them.

---

## 6. Required canaries this batch exercises

**Canary 7 — supporting authority: exercised, at scale.** 96 of 159 spans are `SUPPORTING_AUTHORITY`
preserved rather than discarded, in all three of the forms #137 names:

* **headings** — all 16 entry headings (`'Blinded [Condition]'`, …), plus 49 effect sub-headings
  (`'Attacks Affected.'`, `'Speed 0.'`, `'Automatic Critical Hits.'`, `'Can't Harm the Charmer.'`) — 20 of
  which link to the component they label, and 29 to their record because §7 left that effect with no
  component;
* **explanatory clauses** — 15 frame sentences (*"While you have the Blinded condition, you experience the
  following effects."* — one per condition; the `Condition` entry has none) plus that entry's definitional
  paragraph; and
* **cross-references** — the 15 condition names in the enumeration, each linked to its record's reference.

None is discarded as non-mechanical, and none is counted as the primary statement of a mechanic
(`_ADMISSIBLE_ROLES` permits supporting spans `CONTEXTUAL` links only, and validation confirmed every
supporting span is linked).

**Canaries 1–6 are not exercised**, stated plainly rather than stretched:

| Canary | Why not here | Where its closure lands |
|---|---|---|
| 1 Wish | Spells section, p175 | batch over Spells |
| 2 Illusion | 38 Illusion-school spells, p147–152 | batch over Spells |
| 3 Composite creature | Monsters A–Z, e.g. Mummy p309 (57 leaves + 6 sibling entries) | batch over Creatures |
| 4 Spell-scoped creature | Find Steed p130 / Otherworldly Steed p131 | Spells + Creatures |
| 5 Progression table | Classes, 27 `Level \| Features` tables | batch over Classes |
| 6 Scoped collision | needs the *other* side of a collision: `Armor Class` p177 (glossary) vs p254 (Monsters); the glossary side is in this batch's section but the entry itself is not, and the colliding target is out of batch | Creatures batch closes it |

Nothing about this batch is offered as evidence toward the full-corpus gate. Per #137 acceptance
criterion 17, the canaries prove difficult shapes; the gate proves completion.

---

## 7. Evidence that the closed typed union cannot faithfully represent included mechanics

**This is the stop condition.** Four findings were verified by running the repository's own code, not by
inspection.

### 7.1 The 33 `UNRESOLVED` clauses

| # | Record | Clause | Missing capability |
|---:|---|---|---|
| 1 | blinded | *"You can't see and automatically fail any ability check that requires sight."* | automatic failure; sense-dependent applicability |
| 2 | charmed | *"You can't attack the charmer or target the charmer with damaging abilities or magical effects."* | **targeting restrictions** (deferred) |
| 3 | deafened | *"You can't hear and automatically fail any ability check that requires hearing."* | automatic failure |
| 4 | exhaustion | *"This condition is cumulative. … You die if your Exhaustion level is 6."* | cumulative levels; death state |
| 5 | exhaustion | *"When you make a D20 Test, the roll is reduced by 2 times your Exhaustion level."* | roll modifier scaled by a condition level; no `ScalingBasis` for it, no `ScalingEffect` for a d20 roll |
| 6 | exhaustion | *"Your Speed is reduced by … 5 times your Exhaustion level."* | same |
| 7 | exhaustion | *"Finishing a Long Rest removes 1 of your Exhaustion levels. …"* | `ResourceRecoveryFact` would need `resource_key="exhaustion_level"` — a free-string escape hatch ADR-005d Decision 4 forbids |
| 8 | frightened | *"You can't willingly move closer to the source of fear."* | movement restriction |
| 9, 15, 19, 26, 30 | grappled, paralyzed, petrified, restrained, unconscious | *"Your Speed is 0 and can't increase."* (×5) | speed nullification **on the recipient**; `CreatureSpeedFact` is stat-block authority and using it is a category error |
| 10 | grappled | *"…every foot of movement costs it 1 extra foot unless you are Tiny or two or more sizes smaller than it."* | movement cost; creature-size vocabulary; **eligibility** (deferred) |
| 11 | incapacitated | *"You can't take any action, Bonus Action, or Reaction."* | action **prohibition**; `ActionEconomyFact` states what an effect *consumes* |
| 12 | incapacitated | *"Your Concentration is broken."* | concentration state effect |
| 13 | incapacitated | *"You can't speak."* | typed state effect |
| 14 | invisible | *"You aren't affected by any effect that requires its target to be seen …"* | **targeting restrictions** (deferred) |
| 16, 20, 28, 31 | paralyzed, petrified, stunned, unconscious | *"You automatically fail Strength and Dexterity saving throws."* (×4) | automatic failure, scoped to named abilities |
| 17, 32 | paralyzed, unconscious | *"Any attack roll that hits you is a Critical Hit if the attacker is within 5 feet of you."* (×2) | **critical changes** (deferred) |
| 18 | petrified | *"You are transformed … into a solid inanimate substance … you cease aging."* | typed state effect |
| 21 | petrified | *"You have Resistance to all damage."* | **see 7.3 — structurally unrepresentable** |
| 22, 23 | prone | *"Your only movement options are to crawl or to spend … half your Speed (round down) …"* / *"Speed is 0, you can't right yourself."* | movement options and cost. Also: one sentence split across two 5c leaves |
| 24, 25 | prone | *" An attack roll against you has Advantage if the attacker is within 5 feet …"* / *" Otherwise, that attack roll has Disadvantage."* | **see 7.2 — validation rejects the representation** |
| 27 | restrained | *"You have Disadvantage on Dexterity saving throws."* | **see 7.4 — the nearest typed form is false** |
| 29 | unconscious | *" and you drop whatever you're holding. When this condition ends, you remain Prone."* | object drop; condition persistence after end |
| 33 | unconscious | *"You're unaware of your surroundings."* | perception state |

### 7.2 `AdvantageFact` carries no subject polarity — verified

`AdvantageFact(state, context)` records *which roll* and *advantage or disadvantage*, but not **whose
roll** — the source's "attack rolls against you" vs "your attack rolls" distinction has no field. Run
against the repository's own `fact_key`:

```
Blinded   'Attack rolls against you have Advantage, and your attack rolls have Disadvantage.'
Invisible 'Attack rolls against you have Disadvantage, and your attack rolls have Advantage.'

Blinded   typed fact keys: ['c9be56c271d0a63a', 'eaabf3cd8d9b0651']
Invisible typed fact keys: ['c9be56c271d0a63a', 'eaabf3cd8d9b0651']
IDENTICAL TYPED AUTHORITY, OPPOSITE MEANING: True
```

**A deterministic consumer reading the typed surface cannot tell Blinded from Invisible.** Both readings
are put to the owner rather than adjudicated here:

* *family defect* — subject polarity is not an applicability qualifier; it is which roll the fact is
  about, a different axis, and it belongs in the family; or
* *accepted `MIXED` fidelity* — `AdvantageFact`'s own docstring says the condition under which it applies
  is governing prose, so a `MIXED` component with bound prose may be the designed representation.

This proposal takes neither position: these 19 facts are proposed as-is and the finding is surfaced. If
the second reading is chosen, every `STRUCTURED` component carrying a polarity-bearing clause must become
`MIXED` with bound prose, which changes the proposal.

**Also unresolved by that choice:** `Prone` #24 and Blinded/Invisible/Restrained cannot be told apart even
*with* prose, because the typed halves collide (§7.3).

### 7.3 Prone's attack clause cannot be represented at all — verified

The source states three distinct mechanics in one leaf. Two produce the **same** typed payload:

```
component condition.prone/attacks_affected: duplicate typed fact eaabf3cd8d9b0651
```

`validation._validate_components` rejects it: *"Facts are identified by content, so a repeat is not a
second claim — it is the same claim counted twice."* The rule is correct; the family is what makes two
different statements look like one. So the clause cannot be `STRUCTURED`, and it is not irreducible
(*"within 5 feet"* is a crisp deterministic test) — hence `UNRESOLVED`.

### 7.4 *"Resistance to all damage"* is structurally invalid, not merely lossy — verified

`DamageResponseFact(damage_type, response)` requires exactly one of 13 `DamageType` members; there is no
`ALL`. Enumerating all thirteen is not a workaround: all 13 facts would need a `PRIMARY` provenance claim
on the same span, and `validation._validate_provenance` rejects that as *conflicting primary claims*. The
enumeration is **structurally rejected by the repository's own validators**, not merely inelegant.

### 7.5 `AdvantageFact` cannot scope a saving throw to an ability — verified

Restrained: *"You have Disadvantage on Dexterity saving throws."* The nearest typed form is
`{'family': 'advantage', 'context': 'saving_throw', 'state': 'disadvantage'}` — which asserts disadvantage
on **every** saving throw. That is not a lossy representation; it is a false one. `RollContext` has no
ability qualifier and `AbilityScore` does not reach this family.

### 7.6 Not a schema finding, recorded anyway

Two mechanics are split across 5c leaf boundaries mid-sentence — Incapacitated `'If you're Incapacitated
when you roll'` + `'Initiative, you have Disadvantage on the roll.'`, and Prone `'… If your'` +
`'Speed is 0, you can't right yourself.'`. 5c segmentation is explicitly out of 5d scope; 5d assembles
around it, and it does (the Incapacitated pair is one component with the leading leaf contextually
linked). Recorded so it is not later mistaken for a 5d defect.

---

## 8. Pressure on the deferred families

PR #151 deferred nine contract-3 family items *"to batch-driven accounting, due no later than full-corpus
closure"*. **The first content batch already presses on four of them, with corpus evidence now in hand:**

| Deferred family | Pressed by this batch? | Evidence |
|---|---|---|
| **targeting restrictions** | **Yes** | Charmed *"can't attack the charmer or target the charmer with damaging abilities or magical effects"*; Invisible *"any effect that requires its target to be seen"*; Frightened *"while the source of fear is within line of sight"* (currently absorbed as `contextual_applicability` prose) |
| **critical changes** | **Yes** | Paralyzed and Unconscious: *"Any attack roll that hits you is a Critical Hit if the attacker is within 5 feet of you."* Deterministic, no GM judgement — a promotion rule with no family |
| **eligibility** | **Yes** | Grappled: *"unless you are Tiny or two or more sizes smaller than it"* — an eligibility predicate over creature size, with no size vocabulary either |
| **sequencing** | **Weakly** | Unconscious: *"When this condition ends, you remain Prone"* — ordering of a condition's end relative to another's persistence |
| contests | No | none observed in this batch |
| explicit probability | No | none observed (Wish's clause is in the Spells batch) |
| random-table selection | No | no `dN`-indexed table in this batch; PR #151 could not locate one corpus-wide |
| choices | No | none observed |

**Deferring the first three past this batch is no longer neutral**: the batch cannot be honestly completed
without them. That is a scope-confirmation item for the owner, not an engineering decision, and it is the
substance of the verdict.

**Not pressed and not touched:** no `RecordKind`, `RelationshipKind`, `NON_MECHANICAL_REASONS`, or
`IRREDUCIBILITY_REASONS` member was added, proposed, or needed. `semantic_policy_hash()` is unchanged, so
no previously committed authority is invalidated.

---

## 9. ADR-015b Known Unknown — confirmed untouched

**Spell-slot upcasting and variable-resource parameter semantics remain the recorded ADR-015b Known
Unknown and were not invented here.** Concretely:

* the batch contains **no spell, no spell slot, and no upcasting clause** — `SpellSlotProgressionFact`,
  `ScalingFact`, `SpellDescriptorFact`, and `ResourceRecoveryFact` are all **unused** in this proposal
  (only `advantage` and `condition_effect` appear);
* `ScalingBasis.HIGHER_LEVEL_SPELL_SLOT` is not referenced;
* the nearest adjacent case — Exhaustion's *"the roll is reduced by 2 times your Exhaustion level"* and
  *"Speed is reduced by … 5 times your Exhaustion level"* — is **variable-amount scaling by a condition
  level**. It is proposed `UNRESOLVED` (§7.1 #5/#6) and **no adjustment parameter is defined for it**.
  If the owner treats condition-level scaling as within the same Known Unknown, that is an owner call;
  this proposal does not resolve it in either direction, and invents nothing;
* likewise Exhaustion's Long Rest removal (§7.1 #7) is left `UNRESOLVED` rather than forced into
  `ResourceRecoveryFact` via a free-string `resource_key`.

---

## 10. The generated proposal artifact and the semantic diff a human must review

### 10.1 The artifact

* **`.claude/review-notes/issue-5d-batch-conditions-1-PROPOSAL.json`** — 117,584 bytes, the exact output of
  `proposal.proposal_payload`.
* **`.claude/review-notes/issue-5d-batch-conditions-1-audit.json`** — 159 rows: record, leaf id, span id,
  offsets, **exact span text**, disposition. This is what a reviewer reads clause by clause.
* **`.claude/review-notes/issue-5d-batch-conditions-1-generator.py`** — the generator, whose clause table
  is the reviewable statement of every proposed judgement. To rerun it, place the `dump_corpus.py`
  outputs (`leaves.json`, `containers.json`, `edges.json`, `binding.json`) beside it; that dump script
  rebuilds them from the committed PDF via `build_candidate` → `finalize_release` (~2 min). As placed
  here, alone, it will not run.
* **Proposal identity** (`proposal.proposal_identity`, the value `accept_proposal` would retain as the
  evidence of *what was reviewed*):

  ```
  dfcee03dd93d76e109ec932641a367119f63f8fc82d68836d2c817400610a662
  ```

* **Bound release** — all six values reproduced from a fresh `build_candidate` → `finalize_release` on
  this SHA, matching PR #151's table exactly:

  | | |
  |---|---|
  | `package_uuid` | `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` |
  | `release_version` | `5.2.1-corpus.36b786d8-fa2` |
  | authoritative source SHA-256 | `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87` |
  | transform-config SHA-256 | `77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e` |
  | bundle root hash | `03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685` |
  | persisted-corpus digest | `c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b` |

* **Declared policy** — `5d-semantic-policy-1` and the committed `semantic_policy_hash()`, read from
  source, not restated.

### 10.2 It is unmistakably non-authoritative — verified by running the loaders

```
load_accepted_inputs : OracleLoadError: artifact_kind 'machine_proposal' is not
                       'accepted_authority'; this file is not accepted authority
load_oracle          : OracleLoadError: (same)
artifact_kind edited
to lie                : OracleLoadError: missing ['acceptance', 'obligations',
                        'representation', 'spans']
```

Structural incompatibility at every level, as PR #151 designed: `proposed_spans` (each carrying
`proposal_origin` and `rationale`) not `spans`; `proposed_representation` not `representation`; no
`acceptance` block; no `obligations` block. The file is **not** in `oracles/` and nothing in `src/` writes
there.

### 10.3 The semantic diff a human must review

There is **no prior accepted authority for this release** — `committed_oracle_for` was called with the
exact production package/release on this SHA and returned `None`, and `oracles/` holds no `*.json`. So the
diff `accept_proposal` would record is
all-new: 159 entries, each `prior_disposition = None`, `prior_reason_code = None`.

**No diff artifact was constructed**, because constructing one means calling `accept_proposal`, which
produces `AcceptedInputs`. The reviewable diff is therefore presented as its content:

| Δ | `accepted_disposition` | `accepted_reason_code` | Spans | Review burden |
|---|---|---|---:|---|
| all-new | `supporting_authority` | `None` | 96 | confirm each preserves rather than discards (canary 7) |
| all-new | `substantive` | `None` | 30 | confirm each is exactly what its 25 facts / 5 prose bindings claim |
| all-new | `unresolved` | `None` | 33 | **§7 — each blocks acceptance** |
| all-new | `non_mechanical` | — | 0 | — |

**What a reviewer must decide, in order:**

1. **§7 first.** Until the schema decision lands, 33 spans are `UNRESOLVED` and `validate_acceptance`
   refuses the artifact. Nothing below matters until this is answered.
2. **§7.2's two readings** — family defect or accepted `MIXED` fidelity. The answer changes 15 components.
3. **§4.2** — whether condition-application should also be a relationship kind.
4. **§3** — the 5 irreducibility judgements, one by one.
5. **§4.3** — whether the `Condition` enumeration is the right owner of the 15 reference edges.
6. **§5.4** — whether the 83 non-entry glossary leaves are correctly out of this batch.

---

## Verification actually run

Pure validators only. **No persistence, no publication gate, no acceptance, no database.**

| Check | Result |
|---|---|
| `accounting.validate_partition` per leaf ×134 | **0 violations** — gap-free, non-overlapping, ids match ranges |
| `accounting.validate_reason_codes` | **0 violations** |
| `validation.validate_representation` (records, components, prose bindings, relationships, references, provenance) | **0 violations** |
| `bound_corpus.chunk_relative_range` ×5 | resolved unambiguously; none fell back |
| `oracle.load_accepted_inputs` / `load_oracle` on the proposal | rejected (§10.2) |
| `oracle.committed_oracle_for('4458fa10-…', '5.2.1-corpus.36b786d8-fa2')` | returned `None`, asserted — no accepted authority exists (`oracles/` holds only `README.md`) |
| production release rebuild | all six binding values reproduce PR #151's table exactly |

**Not run, deliberately:** `persist_draft`, `reconstruct_candidate`, `run_publication_gate`,
`publish_from_committed_oracle`, `accept_proposal`. The full-corpus gate would (correctly) reject this
batch with `POPULATION_MISMATCH` for 27,975 uncovered represented leaves; that is the designed
intermediate state, not a defect.

---

## Hard stop

This packet is delivered for Owner review. **It is not approved by its author.** No production
`AcceptedInputs` was created or committed, no projection was published or activated, no legacy authority
was removed, no 2b/15c work began, and PR #129 remains frozen. The generated proposal is disposable
review material.

**Nothing proceeds until §7 is dispositioned by an explicit owner decision.** Test success, validator
silence, and the existence of a structurally valid proposal are not acceptance.
