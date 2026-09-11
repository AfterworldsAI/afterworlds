# CRD Issue 5d — batch `cover-1`: source-discovery and schema-adequacy checkpoint

**Status.** Discovery stop, for Codex's review. Nothing is proposed, drafted, accepted,
lifted, published, activated or retired by this checkpoint, and no schema change is
implemented. It ends here.

**Authority.** #137; ADR-005d; `docs/architecture/known_unknowns.md`; `CLAUDE.md`. The
`areas-of-effect-1` discovery checkpoint §5b recorded `Cover` as a confirmed external
citation with an undefined target, and `known_unknowns.md:465` records the disposition
verbatim: *"Sequencing a batch that states `Cover` is ordinary engineering under #137, not
an Owner Decision, and nothing in this document anticipates that entry's content."* This
checkpoint is that sequencing exercised. It anticipates nothing from that sentence and
measures the entry from the bound release instead.

**Reproduce everything here.**

```bash
python .claude/review-notes/issue-5d-cover-1-discovery.py
pytest -q --no-cov tests/ingestion/mechanical/test_cover_1_frozen_prior.py
```

The first writes `.claude/review-notes/issue-5d-cover-1-source-manifest.json` (LF, sha256
`f82163ee2fc6b6c1805974e6e7404eca45fd6b48452a64a91f9e6a4f0e0cdcad`, byte-identical on
rerun). Every clause id cited below is a row in its `clauses` array, addressable as
`leaf_id[char_start:char_end)`. No judgment in this document is encoded in the script: it
emits no disposition and no candidate record key, because a discovery run that shipped its
own conclusions would be proposing.

---

## 1. What is frozen, and what did not move

`tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1_areas_of_effect_1.json`
is the five accepted batches — `conditions-1`, `hazards-1`, `actions-1`, `attitudes-1`,
`areas-of-effect-1` — created by `git cat-file blob 467fcc62c8fb64e54cf74e73a6f55c384129eef7`
and pinned by two independent identities:

| Identity | Value |
|---|---|
| content sha256 (LF) | `9f3802514298f519120680db4a9a20805f5dcb8a4b00dd8686ed6faddec1e738` |
| git blob | `467fcc62c8fb64e54cf74e73a6f55c384129eef7` |
| `oracle_identity` | `8e08ac48f2a57a4498557990a07270f9abd855b246c1039da68cc9ec82d44b40` |
| representation schema | `5d-representation-schema-9`, hash `f5a5e30817e64f019e31aa7f4692d72611215e4294e7da36242e492bca6b336e` |

Fixture blob == live blob is the whole preservation proof: the live accepted artifact under
`src/afterworlds/ingestion/mechanical/oracles/` is untouched, and the copy is the same
content today. Everything else is derived by loading the file rather than transcribed —
five batch ids, per-batch schema anchors 3/5/7/8/9, the six declared lifts, 46 records over
six collections, 530 spans, 46 obligations, and the exact unresolved residue
`{glossary.concentration, glossary.cover, glossary.speed}`.

**Two departures from the `areas-of-effect-1` frozen prior, both stated rather than papered
over.**

* **No crossing is asserted.** The prior declares schema 9 and schema 9 is current, so
  `validate_schema_binding` returns `()` and `lift_path` raises `UnknownSchemaLiftError`.
  Whether this batch needs a schema step is the open question this checkpoint exists to
  answer (§4), not something the contract test may pre-decide.
* **One test is new.** `test_the_one_accepted_citation_of_cover_is_the_reference_this_batch_inherits`
  pins the single accepted citation whole — from `glossary.area_of_effect`, component `""`,
  scope `srd-5.2.1/rules-glossary`, source text `Cover`, target `glossary.cover` undefined —
  because that citing-without-defining asymmetry is the position §5 must be measured
  against.

The four-batch prior and its test are untouched. `.secrets.baseline` gained one additive
114-entry block for the new fixture, copied from the live oracle's block with the filename
swapped; the two files are byte-identical, so the findings are too.
`git diff --numstat .secrets.baseline` reported **800 insertions, 0 deletions**,
`generated_at`, every detector setting and every pre-existing block byte-identical, and the
configured pre-commit hook exits 0.

---

## 2. Membership, derived from the source's containers — there is no tag

`areas-of-effect-1` re-derived its class from a printed tag: the Rules Glossary preamble
names five tag values and `[Area of Effect]` is one of them, so the six shapes are a query.
**`Cover` has no tag.** Membership here is therefore a structural claim, and the run states
it as one and fails loudly if the structure moved:

* exactly **two** `entry` containers in the bound release are labeled `Cover`;
* one descends from `Rules Definitions`, the other from `Combat`;
* the glossary entry's last two leaves are a bare `See also` and a citation naming the
  section and subsection of the other.

| Site | Container | Path | Printed page | Leaves |
|---|---|---|---|---|
| `glossary` | `6295e463-969f-597b-b07d-6f9665cf13ed` | `Rules Glossary > Rules Definitions > Cover` | p179 (index 178) | 4 |
| `combat` | `e973a828-0b83-547b-979c-f93dc7fa5888` | `Playing the Game > Combat > Cover` | p15 (index 14) | 12 |

The direction is the source's own, not a reader's judgment:
`08f63b16[0:8)` = `See also`, `297ec10b[0:30)` = `“Playing the Game” (“Combat”).` — and the
run asserts that citation contains both `Playing the Game` and `Combat`, which are the
labels of the Combat entry's own ancestors. **The glossary entry points at the Combat
entry.** That is why the two sites are one population.

**The source owns the boundary.** A leaf is in this population because the bound release
*attaches* it to an entry labeled `Cover`, directly or through a table beneath it — not
because it prints the word. Thirty other leaves print `Cover` (§6). Every one of them
*uses* the rule; none *states* it. Pulling any of them in would be the batch expansion this
invocation's scope forbids.

**Extraction artifacts, carried verbatim rather than repaired.** Both are properties of the
frozen 5c release, and the committed `srd_table_inventory.json` is an independent witness
to the second:

* the Three-Quarters degree label extracts as `ThreeQuarters` where the source prints
  *Three-Quarters*;
* the printed Cover table arrives as **two logical tables** — `c6a4eedc…` (header row plus
  the Half row, 3 columns, 2 logical rows) and `18c5361c…` (the Total row, 3 columns, 1
  logical row) — plus the three Three-Quarters leaves and the prose paragraph attached
  directly to the entry rather than to any table. Both logical tables record
  `printed_pages: [15]`, and the run asserts the inventory agrees.

Two cells arrive fused, benefit run together with *Offered By*: `0b5a0f13` (Half) and
`ae0d54f5` (Total). The partition cuts them at the printed column boundary without altering
a byte. No source-corpus change is proposed or made.

---

## 3. Clause coverage — 16 leaves, 28 clauses, gap-free and byte-exact

Every leaf is reconstructed byte for byte from its clauses; `policy.exclusion_reason_for`
excludes none of the 16. Cuts are located in the bound content at run time and are asserted
unique within their leaf, so a re-extraction cannot silently re-cut a clause under a
judgment written about the old one.

`S` = substantive candidate, `A` = supporting authority candidate. These are the
checkpoint's readings for review, not accepted dispositions.

### `glossary` site — p179, leaves `4d39043d 77f2f462 08f63b16 297ec10b`

| Clause | Range | Text | Read | What it states / why |
|---|---|---|---|---|
| `glossary/0/0` | `4d39043d[0:5)` | `Cover` | A | entry heading; navigational |
| `glossary/1/0` | `77f2f462[0:60)` | `Cover provides a degree of protection to a target behind it.` | A | frames the rule; states no threshold, benefit or condition of its own |
| `glossary/1/1` | `77f2f462[60:150)` | ` There are three degrees of cover, each of which provides a different benefit to a target:` | S | the closed cardinality of the vocabulary — **three** degrees. No *fact* carries it; §4a names the carrier |
| `glossary/1/2` | `77f2f462[150:207)` | ` Half Cover (+2 bonus to AC and Dexterity saving throws),` | S | G1 + G2 |
| `glossary/1/3` | `77f2f462[207:274)` | ` Three-Quarters Cover (+5 bonus to AC and Dexterity saving throws),` | S | G2 |
| `glossary/1/4` | `77f2f462[274:320)` | ` and Total Cover (can’t be targeted directly).` | S | G3 |
| `glossary/1/5` | `77f2f462[320:417)` | ` If behind more than one degree of cover, a target benefits only from the most protective degree.` | S | G6 |
| `glossary/2/0` | `08f63b16[0:8)` | `See also` | A | the cross-reference heading; `area_of_effect-1` gave its own `See also` the same reading |
| `glossary/3/0` | `297ec10b[0:30)` | `“Playing the Game” (“Combat”).` | A | §5c — a citation of a **section**, not of a record |

### `combat` site — p15, leaves `9dbd5ece ac18c3da d194524d 75c546c7 f4d2934b 21bff720 0b5a0f13 ea44211d 7e6312ab 3d1bf5fb 165e6e6c ae0d54f5`

| Clause | Range | Text | Read | What it states / why |
|---|---|---|---|---|
| `combat/0/0` | `9dbd5ece[0:5)` | `Cover` | A | entry heading |
| `combat/1/0` | `ac18c3da[0:103)` | `Walls, trees, creatures, and other obstacles can provide cover, making a target more difficult to harm.` | A | exemplification inside a framing sentence — *"and other obstacles"* is open by construction. **Not** an offeror enumeration; the same reading `areas-of-effect-1` gave *"such as a wall"* (its G8 residue) |
| `combat/1/1` | `ac18c3da[103:222)` | ` As detailed in the Cover table, there are three degrees of cover, each of which gives a different benefit to a target.` | A | restates `glossary/1/1` and points at the table; carries no distinct claim — `SUPPORTING_AUTHORITY` with a link, §4a |
| `combat/1/2` | `ac18c3da[222:336)` | ` A target can benefit from cover only when an attack or other effect originates on the opposite side of the cover.` | S | **G5 — printed only here.** The glossary site does not state directionality |
| `combat/1/3` | `ac18c3da[336:470)` | ` If a target is behind multiple sources of cover, only the most protective degree of cover applies; the degrees aren’t added together.` | S | G6, second statement — §4a |
| `combat/1/4` | `ac18c3da[470:625)` | ` For example, if a target is behind a creature that gives Half Cover and a tree trunk that gives Three-Quarters Cover, the target has Three-Quarters Cover.` | A | worked example; the `Cone/1/2` precedent in `areas-of-effect-1` |
| `combat/1/5` | `ac18c3da[625:631)` | ` Cover` | A | **the table caption**, absorbed into the end of the prose leaf by extraction. Cut apart so a judgment about the rule cannot accidentally cover a caption |
| `combat/2/0` | `d194524d[0:6)` | `Degree` | A | column header |
| `combat/3/0` | `75c546c7[0:17)` | `Benefit to Target` | A | column header — and the sole hit of the substring scan (§5d) |
| `combat/4/0` | `f4d2934b[0:12)` | `Offered By …` | A | column header, printed with the ellipsis |
| `combat/5/0` | `21bff720[0:4)` | `Half` | S | degree label — G1 |
| `combat/6/0` | `0b5a0f13[0:42)` | `+2 bonus to AC and Dexterity saving throws` | S | G2, second statement of `glossary/1/2` |
| `combat/6/1` | `0b5a0f13[42:112)` | ` Another creature or an object that covers at least half of the target` | S | **G4 — printed only here**, and the only clause naming a creature as an offeror |
| `combat/7/0` | `ea44211d[0:13)` | `ThreeQuarters` | S | degree label; extraction artifact for *Three-Quarters* |
| `combat/8/0` | `7e6312ab[0:42)` | `+5 bonus to AC and Dexterity saving throws` | S | G2, second statement of `glossary/1/3` |
| `combat/9/0` | `3d1bf5fb[0:59)` | `An object that covers at least three-quarters of the target` | S | G4 |
| `combat/10/0` | `165e6e6c[0:5)` | `Total` | S | degree label |
| `combat/11/0` | `ae0d54f5[0:26)` | `Can’t be targeted directly` | S | G3, second statement of `glossary/1/4` |
| `combat/11/1` | `ae0d54f5[26:65)` | ` An object that covers the whole target` | S | G4 |

**The printed offeror asymmetry is real and must survive representation.** Half is
*"Another creature **or** an object"*; Three-Quarters and Total are *"An object"* only.
A single offeror slot that assumed "creature or object" everywhere would state a rule the
source does not print.

---

## 4. Schema adequacy against representation schema 9

**Nothing here is irreducible prose.** `ProseBindingDraft` requires one of the six closed
reasons in `policy.IRREDUCIBILITY_REASONS` (`policy.py:86`) — `contextual_applicability`,
`subjective_judgment`, `open_ended_effect`, `gamemaster_latitude`,
`natural_language_exception`, `fiction_dependent_consequence`. Each substantive clause was
checked against all six and matches none: every one states a closed, printed, non-delegated
rule with a stated threshold or a stated value. *"at least half"*, *"at least
three-quarters"* and *"the whole"* are exact fractions, not GM latitude; *"most protective
degree"* is a total order over three named members, not a judgment call. Binding any of
them as irreducible would be the defect #137 contract 3 names, so each is reported as a
missing vocabulary instead.

**What schema 9 already has, and it is more than nothing.** `Cover` is not a stranger to
the schema — it is already *consumed* as a vocabulary by accepted authority:

* `ApplicabilityKind.COVER = "cover"` exists (schema 6, from `Hide` p183), and
  `Applicability` carries a `cover: CoverDegree | None` field. *Cover as a precondition on
  another rule* is already stateable and already accepted.
* `BlockedLineExclusionFact(blocked=…, blocking_cover=CoverDegree.TOTAL)` is accepted on
  `glossary.area_of_effect`.
* `CoverDegree` therefore already exists — carrying `THREE_QUARTERS` and `TOTAL`.

What has never existed is a carrier for what cover *is*: the schema can say *"this rule
applies when you are behind Three-Quarters Cover"* and cannot say *"Three-Quarters Cover
grants +5 to AC and Dexterity saving throws."* That is the whole of this batch's gap
surface.

| Gap | Witnesses | Existing shape | Represented distinction | Residue | Record ends / runtime begins |
|---|---|---|---|---|---|
| **G1** — `CoverDegree.HALF` | `glossary/1/2`, `combat/5/0` | `CoverDegree` carries `THREE_QUARTERS` and `TOTAL` only. Its own docstring already anticipates this: Half Cover *"is outside this batch's cut and is admitted by the batch that states it."* This is that batch | that the printed vocabulary has **three** members, which `glossary/1/1` states outright | none | pure vocabulary widening; nothing evaluates |
| **G2** — the degree's defensive benefit | `glossary/1/2`, `glossary/1/3`, `combat/6/0`, `combat/8/0` | **none.** `CreatureDefenseFact(armor_class, hit_points, hit_point_dice)` is a stat block's own AC, not a bonus to someone else's. `AttackRollFact.to_hit_bonus` is a stat block's attack. `AdvantageFact(state, roll, use_limit)` is advantage state, not a numeric bonus. `DerivedQuantityFact(base, modifier, unit, …)` derives from an ability modifier. `RollSpec(actor, context, ability, skill)` **can** name the saving-throw half — `RollContext.SAVING_THROW` + `AbilityScore.DEXTERITY` — but AC is not a roll and `RollContext` has no member for it | one printed benefit that is **two** modifications at once: `+N` to AC **and** `+N` to Dexterity saving throws | the conjunction is the rule. Splitting it into two facts would be faithful only if the shape kept them keyed to one degree; a shape that could state only the saving-throw half would silently drop AC | the record states the degree, the amount and what it modifies; applying it to a specific roll is adapter work |
| **G3** — targeting prohibition | `glossary/1/4`, `combat/11/0` | **none.** `ActionRestrictionFact(cost)` restricts *action-economy slots*, not targeting. `Targets` (p105) states the same prohibition from the other side and is outside this population (§6) | that Total Cover's benefit is categorically different from the other two: not a bonus at all, but *"can't be targeted directly"* | *"directly"* is load-bearing and printed — the prohibition is on direct targeting, not on all effects. A shape that dropped it would state a stronger, wrong rule | the record states the prohibition; deciding whether a given effect targets directly is adjudication |
| **G4** — offeror and coverage threshold | `combat/6/1`, `combat/9/0`, `combat/11/1` | `Rational(numerator, denominator)` exists and is the exact carrier for the fraction. `AreaOriginKind.CREATURE_OR_OBJECT` is **precedent** that "a creature or an object" is admissible as a closed member — but it is an *area-origin* vocabulary and reusing it here would merge two unrelated vocabularies | what offers each degree, and how much of the target it must cover: `at least 1/2`, `at least 3/4`, `the whole` | the printed asymmetry (§3): Half admits a creature **or** an object, the other two admit an object only. A single shared offeror member would erase it | the record states the offeror kind and the fraction; measuring how much of a target an obstacle actually covers is geometry, explicitly outside 5d |
| **G5** — directionality | `combat/1/2` | **none** | that cover benefits a target *only* when the attack or effect originates on the opposite side | printed at one site only. It is a precondition on the benefit, not a property of the degree, so a degree-only record would lose it entirely | the record states the relation; deciding which side an effect originated on is runtime geometry |
| **G6** — non-stacking / most-protective selection | `glossary/1/5`, `combat/1/3` | **none.** The nearest shapes are `QuantityMultiplierFact` and `ScalingFact`, both about amounts, neither about selecting among applicable states | that multiple applicable degrees resolve to exactly one — the most protective — and explicitly do not sum | `combat/1/3` adds *"the degrees aren't added together"*, which is the same rule stated negatively rather than a second rule | the record states the selection rule and the order over three named members; determining which degrees apply in a situation is runtime |

**None of the six is an Owner Decision.** Each is a closed, printed, enumerable distinction
with no product decision, no ownership move and no contradiction between authorities. A new
fact family plus closed enums is ordinary declarative schema work, and per this
invocation's governing instruction missing vocabulary alone is not an Owner Decision.
ADR-005d Decision 4 and ADR-005c Decision 3 forbid *executable* mechanics; every gap above
is satisfied by named closed members a hand-authored adapter interprets, and none of them
evaluates anything. **Zero of the six is a genuine unresolved product or ownership
question.**

### 4a. The same rule is printed twice, and the schema has an opinion about that

Four rules are stated at **both** sites: the three degree benefits (`glossary/1/2`↔`combat/6/0`,
`glossary/1/3`↔`combat/8/0`, `glossary/1/4`↔`combat/11/0`) and non-stacking
(`glossary/1/5`↔`combat/1/3`). This is not a nuisance — it is the first time in this build
that one record's authority would be drawn from two chapters, and two validators bear on it:

* `validation.py:159` rejects two facts with the same `fact_key` **within one component
  scope**.
* `_validate_duplicated_fact_authority` (`validation.py:652`) rejects two *different*
  components of one record holding equivalent facts **drawn from the same substantive
  span**. Its docstring is explicit that facts drawn from *different* spans are left alone —
  *"the same mechanic stated by two genuinely different rules is normal authority."* These
  are not two different rules; they are one rule printed twice, so leaning on that
  exemption to hold two copies would pass validation while publishing two claims where the
  source made one.

**The available shape, and it is already supported.** Provenance is per-span → target
(`ProvenanceClaim(target_kind, target_key, span_id, role)`), edges are keyed by
`(kind, key, span_id, role)`, and `validation.py:621` rejects only a span with **more than
one** primary owner. Several spans claiming the *same* target is exactly the permitted
case. So: **one fact per component, with `PRIMARY` provenance from both sites' spans.** The
duplicated-fact rule cannot fire — there is only one component — the duplicate-edge check
cannot fire (different `span_id`), and every substantive span is claimed, satisfying
`validation.py:637`. The alternative — typing one site and classifying the other's
restatement as `SUPPORTING_AUTHORITY` with a linked edge — is also available and is the
shape `areas-of-effect-1` used for two of its spans. The first is the honest one here,
because both sites genuinely state the rule.

**A fifth statement is printed twice and is *not* this case.** `glossary/1/1` and
`combat/1/1` both print the cardinality — *"there are three degrees of cover."* It is
excluded from the four above because the four are rules printed twice, and this one is not
a rule: what it states is the **closure of a vocabulary**, and `ProvenanceTargetKind` has
no vocabulary member (`record`, `component`, `fact`, `fact_qualifier`, `prose_binding`,
`relationship`, `reference`). Read substantive with no element to claim it, the span would
trip `validation.py:637` — *substantive but unclaimed*. The carrier that does exist is a
**component-level `PRIMARY` claim**: a span stating something about a component as a whole
rather than about any one of its facts. That is precedent, not invention — the frozen
prior holds **19** `component/primary` claims and **0** `record/primary`, a distribution
the run now derives from the prior and the manifest records as `prior_provenance_shapes`.
So the reading is `glossary/1/1` claiming `PRIMARY` on the component that carries the three
degrees, while `combat/1/1` defers rather than states — *"As detailed in the Cover
table"* — and is `SUPPORTING_AUTHORITY` with a link. That is why §3 reads the two
differently, and the asymmetry is the point rather than an oversight.

### 4b. First non-glossary provenance — checked, not assumed

This is the first batch whose source population leaves the Rules Glossary.
**No schema gap arises**, and this is a checked claim:

* `SemanticSpan(span_id, leaf_id, char_start, char_end, disposition, review_state,
  non_mechanical_reason_code)` is leaf-based and carries no scope. A span over a
  `Playing the Game` leaf is the same shape as a span over a glossary leaf.
* `scope_key` lives only on references, is a plain `str`, and `validation.py:396-421`
  requires only that it be non-blank and that `(scope_key, source_text)` resolve to exactly
  one target.
* `accounting.py` works from the resolved scope/manifest order, not from a hardcoded
  chapter.

Drawing provenance from `Playing the Game > Combat` is therefore representable today.

### 4c. One record or three

The evidence decides this, and it decides it against an umbrella:

* **Accepted authority already names the target.** `glossary.area_of_effect` cites
  `(srd-5.2.1/rules-glossary, "Cover") → glossary.cover`. Defining anything else leaves an
  accepted reference dangling.
* **Every accepted member record is its own glossary entry** — `condition.*`, `action.*`,
  `attitude.*`, `area_of_effect.*`. The three degrees are not entries; they are untagged
  table rows (`combat/5/0`, `combat/7/0`, `combat/10/0`) with no `See also`, no heading and
  no container of their own. There is nothing for a member record to be sited on.
* **Degree is already a vocabulary, not a record.** `Applicability.cover: CoverDegree` and
  `BlockedLineExclusionFact.blocking_cover: CoverDegree` both consume it as an enum in
  accepted authority. Minting `cover.half` as a record would put the same distinction in
  two places at once.

So: one record, `glossary.cover`, with degree as a closed enum. The umbrella shape
`glossary.area_of_effect` uses is not available here because the source did not print
members to enumerate.

### 4d. This mints schema 10

`representation_schema_payload` emits *"vocabularies by their sorted admitted values"* and
its docstring states the rule directly: *"altering an admitted vocabulary value changes
it."* Measured rather than assumed — `three_quarters` appears 8 times in the current
payload. **G1 alone moves the hash**, and G2–G6 add families.

Stated plainly, not implemented: **schema 9 cannot state this population.** One registered
crossing 9→10 is implied, and
`test_no_registered_crossing_separates_the_prior_from_this_build` — which today asserts
`validate_schema_binding` is clean and `lift_path` refuses — is the test that flips first.
No schema change is made by this checkpoint.

---

## 5. References — enumerated, none closed

No validator was run; nothing below is a validator result.

**(a) Inbound — one, and it is the reason this batch exists.** The frozen prior contains
exactly one citation of `Cover`:

| From | Component | Scope | Source text | Target | Defined in prior |
|---|---|---|---|---|---|
| `glossary.area_of_effect` | `""` | `srd-5.2.1/rules-glossary` | `Cover` | `glossary.cover` | **no** |

Representing `glossary.cover` closes exactly that one target. The residue would become
`{glossary.concentration, glossary.speed}`. **Reported as a consequence of the record key,
not as a goal** — the count follows from the source evidence in §4c and nothing was chosen
to make it come out at two.

**(b) Outbound — zero.** This is a real finding, not an omission. The population prints
exactly one citation, `glossary/3/0` = `“Playing the Game” (“Combat”).`, and it names a
**section**, not a record. Every one of the prior's 53 references targets a record key
(`ReferenceDraft.target_record_key`), and there is no record for a chapter. It is also
*this record's own second site* — a pointer from one half of the population to the other —
so a reference would be self-directed even if a target existed. The honest shape is
record-owned supporting authority — the reading `areas-of-effect-1` gave its own
`See also` lead-in at `f7fc8e1e[0:8)`. Its *citation* differed and became a reference
because it named a glossary term (`Cover`); this one names a chapter, which is the
whole difference. **Consequently no `scope_key` decision arises for `cover-1` at all.**

**(c) The scope convention, measured.** All 53 accepted references carry
`scope_key = "srd-5.2.1/rules-glossary"` — verified by counting, not remembered. `scope_key`
is a free `str` with no closure anywhere in the schema (§4b), so the fact that this batch
adds no reference means it also proposes no second scope. Whether a future non-glossary
batch needs one is left open and untouched.

**(d) The substring scan is not a citation list.** The manifest reports one glossary entry
label occurring in the population text: `Target`, at `combat/3/0` — which is the column
header *"Benefit to Target"*. It is not a citation. The manifest labels the field
`glossary_entry_labels_occurring_in_population_text` and says so; the same rule that governs
the boundary governs here.

---

## 6. Boundaries, stated from the text that states them

**The rule, once:** a leaf is in the population when the bound release attaches it to an
entry labeled `Cover`. Printing the word is *use*, not definition. Thirty leaves print it
and are excluded; all thirty are enumerated in the manifest with their container, section,
5c representation state, and any accepted record that already owns that container. The
`already_accepted_as` column is **derived** from the frozen prior — accepted span → leaf →
owning container → provenance target key — not transcribed, so "accepted authority already
represents the citing entry" is read out of the prior rather than asserted about it.

| Section | Leaves | Containers |
|---|---|---|
| Spells | 7 | `Targets`, Arcane Hand, Blade Barrier, Darkness, Daylight, Light, Sacred Flame |
| Magic Items | 6 | Handy Haversack, Mirror of Life Trapping, Oathbow, Portable Hole, Ring of Shooting Stars, Wand of the War Mage |
| Monsters A–Z | 6 | Behir, Gelatinous Cube, Kraken, Purple Worm, Remorhaz, Tarrasque |
| Rules Glossary | 4 | Area of Effect ×2, Blindsight, Hide [Action] |
| Classes | 4 | Druid 14, Monk 3, Paladin 15, Rogue 9 |
| Animals | 2 | Frog, Toad |
| Playing the Game | 1 | Making an Attack |

Four of these are worth naming individually:

* **`Area of Effect` (2 leaves) — `already_accepted_as: ['glossary.area_of_effect']`.** The
  citer. Accepted authority already represents it and already consumes `CoverDegree.TOTAL`.
* **`Hide [Action]` (1 leaf) — `already_accepted_as: ['action.hide']`.** Already accepted,
  and it already consumes **two of the three degrees**: *"behind Three-Quarters Cover or
  Total Cover."* This is the strongest evidence that the degree vocabulary belongs to the
  schema rather than to records (§4c).
* **`Making an Attack` (p15) — a consumer that points *at* this rule.** *"The GM determines
  whether the target has Cover (see the next section)."* It directs the reader to the very
  entry this batch would represent. It is still out: it states no part of the rule.
* **`Targets` (p105) — the same prohibition from the other side.** *"a caster must have a
  clear path to it, so it can't be behind Total Cover."* It consumes `CoverDegree.TOTAL`;
  it does not define it.

The boundary scan is a case-sensitive *substring* match on `Cover`, so **three** of the
thirty — Darkness, Daylight, Light — match only the longer word *"Covering"* and
print no standalone `Cover` at all. Disclosed rather than filtered: a filter would be a
judgment inside the run. The run derives this per row (`prints_standalone_word`) and
asserts that every non-standalone hit is *"Covering"*, so the figure is read out of the
release rather than eyeballed. A separate count is reported for lowercase-only
occurrences of `cover` — **43 leaves** — which are likewise all use.

**Other boundaries:**

* **No Known Unknown is created, narrowed or leaned on.** `known_unknowns.md` contains no
  entry for cover, visibility, occlusion or line of sight; its only mentions of `Cover` are
  the three residue lines (`:463-467`, `:476-478`) recording `glossary.cover` as an
  unresolved reference target and its sequencing as ordinary engineering. This checkpoint
  resolves nothing in that document and proposes no edit to it.
* **Runtime geometry and visibility stay outside.** Measuring what fraction of a target an
  obstacle covers, deciding which side an effect originated on, and resolving which degrees
  apply are all runtime. §4 names the crossing for each gap. ADR-005d Decision 11 leaves
  adapter capability and execution to 15c.
* **Attack adjudication stays outside.** `Making an Attack` is boundary, not population.
* **No source re-extraction.** The run reads the committed PDF through the existing 5c
  pipeline and asserts the five derivable binding values; it changes no extraction, no
  retrieval config and no corpus artifact. The two extraction artifacts in §2 are reported
  verbatim, with the frozen table inventory as an independent witness that they are
  properties of the bound release rather than defects this batch introduced.

---

## 7. Checks that were actually run

| Check | Result |
|---|---|
| `pytest -q --no-cov tests/ingestion/mechanical/test_cover_1_frozen_prior.py` (8 tests) | 8 passed |
| Five release-binding values re-derived from the committed PDF and asserted | pass |
| Exactly two `Cover` entry containers, one under `Rules Definitions`, one under `Combat` | pass |
| Glossary `See also` citation names the Combat entry's own section and subsection labels | pass |
| Every cut located in bound content, asserted unique within its leaf | pass, 28 clauses |
| Partition reconstructs each leaf byte for byte | pass, 16 leaves |
| Policy exclusions inside the population | 0, listed rather than asserted away |
| Committed table inventory agrees with the two observed logical tables | pass |
| Accepted-record ownership of boundary containers derived from the prior's spans and provenance | pass; every derived key asserted present in the prior |
| Frozen prior digest, blob and `oracle_identity` before and after the run | unmoved |
| Live accepted artifact read as a mutation sentinel, never as an input | unmoved |
| Every other file in `.claude/review-notes/` digested before and after | unmoved |
| `black --check` and `ruff check` on the discovery script | clean |
| Manifest reproducibility | rerun byte-identical, sha256 `f82163ee2fc6b6c1805974e6e7404eca45fd6b48452a64a91f9e6a4f0e0cdcad` |
| Manifest reproduced from a clean `git archive` export of this checkpoint's own tree, run outside the working tree | byte-identical (`cmp`). The export is hermetic: the script's own `assert PACKAGE_ROOT.resolve() == IMPORTED_FROM` and the manifest's `IMPORTED_FROM.relative_to(REPO)` both hold there, so the exported `src/` is what ran. No untracked file in `.claude/review-notes/` is an input |

Not run, and not implied: the publication gate (there is no persisted projection to run it
over), the semantic validator (there is no draft), any acceptance script, any lift, any
schema mint.

---

## 8. Where this stops

Delivered: the five-batch frozen prior and its contract test; the reproducible discovery
run and its manifest; this checkpoint. Not done, and not to be done before Codex reviews:
any schema change, any proposal, any draft, acceptance, push, merge, publication,
activation, retirement or parent-issue state change. Parent tracking issue #137 remains in
progress.

**The three questions this checkpoint puts to review:**

1. **§4c — one record with a degree enum, or three member records?** The checkpoint calls
   one, on three grounds: the accepted citation already names `glossary.cover`; the degrees
   are untagged table rows with no entry of their own; and `CoverDegree` is already consumed
   as a vocabulary by two accepted facts. If Codex reads the printed table as an enumeration
   in the `glossary.area_of_effect` sense, that changes the shape of every gap in §4.
2. **§4a — how the doubly-printed rules are disposed.** The checkpoint proposes one fact per
   component with `PRIMARY` provenance from both sites, and names the validator rule that
   makes the alternative dishonest rather than merely different. This is the first
   two-chapter record in the build and is where a reviewer should push hardest.
3. **§4 — do the six gaps read as ordinary closed declarative schema work?** G2 is the one
   with the most surface: it is a defensive bonus family that does not exist, and half of it
   (AC) has no roll context to hang on. G4 is next, because `AreaOriginKind.CREATURE_OR_OBJECT`
   is a tempting reuse that would merge two unrelated vocabularies.
