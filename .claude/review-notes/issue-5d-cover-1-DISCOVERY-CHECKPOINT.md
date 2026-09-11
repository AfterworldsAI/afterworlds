# CRD Issue 5d — batch `cover-1`: source-discovery and schema-adequacy checkpoint

**Status.** Discovery stop, for Codex's review. Nothing is proposed, drafted, accepted,
lifted, published, activated or retired by this checkpoint, and no schema change is
implemented. It ends here.

> **Superseded in part, 2026-09-11.** §§1–8 are the reviewed discovery record and are
> unchanged. Two things they say are now stale and are corrected by later work rather than
> edited here: representation schema 10 was implemented after review (commit `020b268`), and
> a proposal now exists — **§9** records it. Nothing is accepted, published, activated or
> retired, then or now.

**Amended 2026-09-11 — four explanations corrected in place.** Independent review
confirmed the two source locations, the 16 leaves, the 28 clauses and the six schema gaps;
none of those moved. Four pieces of *reasoning* elsewhere in this document overstated what
the governing authority says, and each is corrected where it appears, marked *(corrected
2026-09-11)*:

* §4a inferred **one fact per component** from the duplicate-fact validator. The validator
  does not say that, and it does not decide grouping across different source spans.
* §4c inferred that a missing `ENTRY` and coexistence with an enum **forbid** member
  records. #137 contract 3 and ADR-005d Decision 3 say the opposite — records assemble from
  accepted semantic membership, and a 5c `ENTRY` is structural evidence, not universal
  semantic authority. The conclusion survives on its own evidence: one record is the
  sufficient choice here, not the only permitted one.
* §4 and its G6 row described *"most protective"* as **a total order over three named
  members**. Nothing in the source prints a rank and nothing in this schema carries one.
* §4's G4 row called the recorded value *"the fraction"* and the excluded work
  *"geometry"*. The record states a **printed threshold**, and the boundary is runtime
  *computation*, not geometric subject matter. An exact numeric representation of these
  thresholds would have been permitted — #137 and ADR-005d exclude measuring and
  adjudicating, not carrying exact declarative numbers — so the closed `CoverageThreshold`
  vocabulary is the *sufficient* choice, not the only admissible one. The matching
  rationale in the ADR-005d schema-10 amendment and in `CoverageThreshold`'s docstring is
  corrected the same way.

The findings those passages support are unchanged. Only the reasons are.

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
because it prints the word. Thirty other leaves print `Cover` (§6). Each uses Cover while
stating some *other* rule, or restates a Cover rule from outside a `Cover` entry — `Targets`
(p105) states the spell-targeting rule that a caster needs a clear path, so the target cannot
be behind Total Cover. None of them is attached to a `Cover` entry, so none is in this
population. (Corrected 2026-09-11; see §9.)

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
three-quarters"* and *"the whole"* are exact printed thresholds, not GM latitude; *"most
protective degree"* is a printed selection rule, not a judgment call **(corrected
2026-09-11 — it is not an order).** The source states *that* the most protective degree is
the one that applies and never prints a rank over the three; a record that carried one
would be stating something the page does not. Binding any of
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
| **G4** — offeror and coverage threshold | `combat/6/1`, `combat/9/0`, `combat/11/1` | `Rational(numerator, denominator)` exists and is the exact carrier for the fraction. `AreaOriginKind.CREATURE_OR_OBJECT` is **precedent** that "a creature or an object" is admissible as a closed member — but it is an *area-origin* vocabulary and reusing it here would merge two unrelated vocabularies | what offers each degree, and how much of the target it must cover: `at least 1/2`, `at least 3/4`, `the whole` | the printed asymmetry (§3): Half admits a creature **or** an object, the other two admit an object only. A single shared offeror member would erase it | the record states the offeror kind and the printed coverage threshold; measuring how much of a target an obstacle actually covers is runtime computation, explicitly outside 5d **(corrected 2026-09-11)** |
| **G5** — directionality | `combat/1/2` | **none** | that cover benefits a target *only* when the attack or effect originates on the opposite side | printed at one site only. It is a precondition on the benefit, not a property of the degree, so a degree-only record would lose it entirely | the record states the relation; deciding which side an effect originated on is runtime geometry |
| **G6** — non-stacking / most-protective selection | `glossary/1/5`, `combat/1/3` | **none.** The nearest shapes are `QuantityMultiplierFact` and `ScalingFact`, both about amounts, neither about selecting among applicable states | that multiple applicable degrees resolve to exactly one — the most protective — and explicitly do not sum | `combat/1/3` adds *"the degrees aren't added together"*, which is the same rule stated negatively rather than a second rule | the record states the selection rule and that the degrees do not sum; determining which degrees apply in a situation is runtime, and **(corrected 2026-09-11)** no rank over the three is printed, recorded or implied |

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
case. So: **one fact for the rule, carrying `PRIMARY` provenance from both sites' spans.**
The duplicate-edge check cannot fire (different `span_id`), and every substantive span is
claimed, satisfying `validation.py:637`.

**(Corrected 2026-09-11.)** An earlier form of this paragraph read *"one fact per
component"* and attributed that to the validators. It does not follow from them.
`_validate_duplicated_fact_authority` rejects two components of one record holding
equivalent facts **drawn from the same substantive span**; it says nothing about how many
distinct facts a component may hold, and it does not decide grouping across different
source spans. What the validators require is only that the rule be stated once — not that
each statement occupy a component of its own. Component organization is ordinary
engineering, and this build groups the eight facts into four components: one per printed
column of the Cover table (`degree_benefit`, `degree_provision`) and one per qualifying
prose rule (`benefit_origin`, `degree_selection`). That grouping is also what makes the
closure statement below representable. The alternative — typing one site and classifying the other's
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

**(Corrected 2026-09-11 — the second and third bullets were arguments about what is
*permitted*, and they were wrong about that.)** #137 contract 3 requires the projection to
support *"non-entry rules and free-standing tables"* and forbids *"assuming one 5c `ENTRY`
equals one mechanical entity"*; ADR-005d Decision 3 states that *"a 5c `ENTRY` is
structural evidence, not universal semantic authority"* and that records are assembled from
a committed accepted inventory. So the absence of an `ENTRY` for a table row does **not**
forbid a record sited on it, and nothing in either authority forbids a record coexisting
with an enum that names the same distinction. Both bullets are restated below as what they
actually are: reasons one record is the *sufficient* choice, not reasons three are
impossible.

The evidence decides this, and it decides it against an umbrella:

* **Accepted authority already names the target.** `glossary.area_of_effect` cites
  `(srd-5.2.1/rules-glossary, "Cover") → glossary.cover`. Defining anything else leaves an
  accepted reference dangling.
* **The source did not print the degrees as definable units.** They are untagged table rows
  (`combat/5/0`, `combat/7/0`, `combat/10/0`) with no `See also`, no heading and no
  container of their own. Member records would therefore be sited on a boundary this
  discovery drew rather than one the page prints — permitted, but not *derived*, and the
  smallest faithful extension prefers the boundary the source printed.
* **Degree is already a vocabulary the schema carries.** `Applicability.cover: CoverDegree`
  and `BlockedLineExclusionFact.blocking_cover: CoverDegree` both consume it as an enum in
  accepted authority. Member records would add a second place the same three names live,
  and nothing in this population needs one: every printed distinction between the degrees
  is a field of a fact keyed to the degree.

So: one record, `glossary.cover`, with degree as a closed enum — the sufficient choice, on
the evidence, rather than the only permitted one. The umbrella shape
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
2. **§4a — how the doubly-printed rules are disposed.** The checkpoint proposes one fact for
   each doubly-printed rule, with `PRIMARY` provenance from both sites, and says why the
   alternative is dishonest rather than merely different: the source stated the rule once.
   No validator rejects the two-copy shape on its own. This is the first
   two-chapter record in the build and is where a reviewer should push hardest.
3. **§4 — do the six gaps read as ordinary closed declarative schema work?** G2 is the one
   with the most surface: it is a defensive bonus family that does not exist, and half of it
   (AC) has no roll context to hang on. G4 is next, because `AreaOriginKind.CREATURE_OR_OBJECT`
   is a tempting reuse that would merge two unrelated vocabularies.

---

## 9. Proposal record — 2026-09-11

This section supersedes §8's "not done … any proposal": one exists now. Nothing else in this
checkpoint changed — the two sites, the 16 leaves, the 28 clauses and the six gaps are the ones
independent review confirmed, now carried by an executable artifact instead of only by prose.
Still true, and restated because it is the point: **nothing is accepted, published, activated or
retired**, no acceptance script was run, no source corpus changed, machine rows are `PROPOSED`,
and #137's full-corpus obligation is undischarged.

**(Corrected 2026-09-11.)** Five explanations in this section, in the generator's docstring and
in the generated audit were inaccurate and are corrected here as one consolidated evidence
correction. The population, schema, spans, facts and provenance are unchanged, and
`PROPOSAL.json` is byte-identical — every correction was narrative.

1. §9.1 called the proposal identity a *projection* identity. `proposal.py:161` expressly
   distinguishes the two; the value is right and its scope is now named correctly.
2. §9.4 reversed the disposition split. The generator asserts `{substantive: 16,
   supporting_authority: 12}` (`generator.py:1084`, again at `:2550`), matching §9.2.
3. §9.2, the generator docstring and the audit said that two equivalent facts in two
   components is what `_validate_duplicated_fact_authority` rejects. `validation.py:652`
   also requires the **same substantive source span**; two copies taken from the two
   *distinct* printings would pass it. §4a had this right already. The single-fact shape is
   chosen because the source stated one rule, not because a validator forces it.
4. The boundary's universal *"every excluded leaf uses the rule, none states it"* — in this
   section, in §3's boundary paragraph, in the generator docstring and in the audit — was false:
   manifest leaf `7322a0d0-afaf-5df9-97f6-a0e428c81097` (`Spells > Casting Spells > Targets`)
   **states** the spell-targeting rule that a caster needs a clear path, so the target cannot
   be behind Total Cover. The reviewed two-entry population is unchanged; the exclusions are
   now described as other-rule uses or restatements sited outside a `Cover` entry, and the
   claim that #137 forbids selecting them is withdrawn — they simply stay outside this
   reviewed population.
5. §9.3 and the audit said `persisted_corpus_digest` cannot be rederived without a publish.
   `persistence.recompute_persisted_digest` recomputes it from existing persisted rows plus
   read-back vector state, and `operational.load_verified_operational_corpus` is the narrower
   downstream trust seam; neither publishes. The disclosure itself stands unchanged: this run
   rederived five binding values from the PDF, carried the sixth from the 5c release record,
   and performed **no operational database evidence**. No publish or operational run was
   launched for this correction.

The generator and audit rows in §9.1 move with the corrected text; the proposal row does not.

### 9.1 What was built

Three files, all under `.claude/review-notes/`:

| Path | Bytes | sha256 |
| --- | --- | --- |
| `issue-5d-batch-cover-1-generator.py` | 147,714 | `b0f16434d99a12128cd7873340b390c8fdfe37535d07b613896d14354f45786b` |
| `issue-5d-batch-cover-1-PROPOSAL.json` | 23,610 | `132bbc9f47104cc5e768ef3a5ee48101ba3c6e8fcdbbaaec8029b3b36083d07e` |
| `issue-5d-batch-cover-1-audit.json` | 103,621 | `927ca2d9985efce3fdcc2c851cff1f4a88d8c7021d15c2cd87f8f9d9abcd97ab` |

**Proposal identity:** `1d8a51164f9be0a1559aba93fb076ee0e8c262dda183791491bc339e3ebfec01`.

That is the content-derived identity of *this proposal* (`proposal.py:161`): what a review note
names to say which object it reviewed, and what an acceptance would record it accepted *from*.
It is expressly **not** a projection identity and never becomes one, and it is not the identity
of accepted authority — a proposal that is never accepted leaves no trace in any published
authority. Reporting it here changes none of that.

**Where `PROPOSED` lives.** A reviewer looking for a review state inside `PROPOSAL.json` will not
find one: `accounting.span_payload` deliberately omits it, because a span set that means the same
thing must compare equal however it was reviewed. The state is on the objects and is asserted
there — `{p.span.review_state for p in PROPOSAL.proposed_spans} == {ReviewState.PROPOSED}` — and
the payload is asserted to carry no `acceptance` and no `obligations` key at all.

### 9.2 Span scope

One composite record, `glossary.cover`, `RecordKind.GLOSSARY_RULE` in scope
`srd-5.2.1/rules-glossary`, assembled from **two printed sites in two chapters**:

* `Rules Glossary > Rules Definitions > Cover` — p179, 4 leaves
* `Playing the Game > Combat > Cover` — p15, 12 leaves

Sixteen leaves, zero policy exclusions. Twenty-eight reviewed clauses become twenty-eight spans:
**16 `SUBSTANTIVE`, 12 `SUPPORTING_AUTHORITY`, 0 `NON_MECHANICAL`, 0 `UNRESOLVED`.** The extents
partition all sixteen leaves gap-free; the generator re-proves the partition against the bound
leaves rather than trusting the manifest's arithmetic, and the manifest's own digest
(`f82163ee…`) is re-pinned before it is read. Spans carry no retyped text.

The composition is **4 components, every one `ComponentHandling.STRUCTURED`, carrying 8 typed
facts, 0 prose bindings, 0 references and 0 relationships**:

| Component | Facts |
| --- | --- |
| `degree_benefit` | `cover_defensive_bonus` ×2 (Half, Three-Quarters), `cover_targeting_prohibition` (Total) |
| `degree_provision` | `cover_provision` ×3 (the *Offered By* column) |
| `benefit_origin` | `cover_benefit_origin` — the opposite-side requirement |
| `degree_selection` | `cover_degree_selection` — most protective, degrees not added together |

Sixteen substantive clauses yield eight facts because **four rules are printed at both sites**
(`half_benefit`, `three_quarters_benefit`, `total_prohibition`, `most_protective`). Each is
represented **once**, with `PRIMARY` provenance from *both* sites' spans — the source printed one
rule twice, and provenance is per span, so several spans claiming one target is the ordinary
shape. No validator forces this: `validation.py:159` rejects two equal-keyed facts inside one
component, and `_validate_duplicated_fact_authority` (`validation.py:652`) rejects sibling
components holding an equivalent fact drawn from the **same** substantive span — two
components each holding a copy taken from the two *distinct* printings would pass both. One
fact is chosen because both sites state one rule, as §4a settles: two copies would publish two
claims where the source made one. Each of the four is
asserted to be claimed `PRIMARY` by exactly two spans, one per site, and the site pair is
asserted to be `["combat", "glossary"]`.

Provenance is **28 claims, exactly one per span**: 8 `RECORD`/`CONTEXTUAL`, 1
`COMPONENT`/`PRIMARY`, 3 `COMPONENT`/`CONTEXTUAL`, 15 `FACT`/`PRIMARY`, 1 `FACT`/`CONTEXTUAL`.

**The three-degree closure statement** is the single component-scope `PRIMARY` claim.
`glossary/1/1` — *"There are three degrees of cover, each of which provides a different benefit to
a target"* — states that the printed vocabulary is closed at three members. That is true of a
whole column of rule and of no single fact in it, so it is claimed at component scope on
`degree_benefit`. Grouping the degrees into one component is what gives the sentence something to
claim; the 19 accepted component-scope claims in the frozen prior are the precedent for the shape.

### 9.3 Architecture Notes

**No drift from design principles.** Six disclosures a reviewer should not have to discover:

1. **Standalone and combined reference resolution are kept apart, and the distinction matters.**
   This batch emits **zero** references — the population prints one citation and it names a
   chapter, not a record, and it points at this record's own second site. Standalone validation of
   the candidate's representation produces **0** findings (asserted as an exact empty tuple).
   Merged with the lifted prior it produces exactly **2**: `glossary.speed` and
   `glossary.concentration`, both inherited. The prior's own `Cover` citation — asserted to be
   exactly one inbound row, from `glossary.area_of_effect`, source text `Cover`, target
   `glossary.cover` — **resolves in the merged candidate only**. Accepted authority still carries
   three unresolved targets and will until an acceptance that has not happened. Resolving a
   citation in a candidate is not a change to current accepted authority.
2. **The six-part release binding is verified through the canonical seam, and rederivation is
   distinguished from database evidence.** `release_binding_payload(BINDING)` is asserted to have
   exactly six parts, and those six are asserted to equal five **rederived in this run from the
   source PDF** (`package_uuid`, `release_version`, `authoritative_source_hash`,
   `transform_config_hash`, `bundle_root_hash`) plus one **disclosed** from the committed 5c
   release record (`persisted_corpus_digest`). The sixth is disclosed rather than rederived
   because recomputing it needs a session over the persisted rows plus read-back vector state
   (`persistence.recompute_persisted_digest`), and verifying a published release against
   declared values is `operational.load_verified_operational_corpus`, the narrower downstream
   trust seam. Neither requires a publish; this run simply performs neither. The audit labels
   each value as such. **No operational database evidence was performed by this run**: no
   session, no `rp_sources`, no Chroma, no persistence layer was touched, and the audit says so in
   those words rather than leaving it to be inferred.
3. **`validate_candidate` is classified, never filtered.** It returns 27,818 findings for a
   one-record candidate. Every one is classed by the literal prefixes the three validators emit,
   counted, and given a worked example in the audit; the tally is asserted exhaustive and the
   `other` class is asserted empty, so an unrecognised finding fails the run instead of being
   quietly dropped. **`release_binding_disagreement` is 0** — the class this run has to be clean
   at. `corpus_leaf_not_yet_classified` is 27,788, one per leaf of the bound release that the five
   accepted batches plus this proposal do not cover; that is #137's undischarged obligation
   reported honestly, not a defect of this batch. `inherited_unresolved_reference` is the same 2
   as above, asserted equal to that list rather than merely counted. **`span_not_accepted` is 28,
   asserted by span id and not merely by count, and they are exactly this batch's proposed rows** —
   the merged ledger carries the accepted prior's batches and acceptance records, so the prior's
   530 accepted spans clear the check and only the machine rows proposed here do not. That is the
   machine-readable form of *keep machine rows `PROPOSED`*.
4. **Two identity scopes are reported separately.** The frozen five-batch prior keeps
   `8e08ac48f2a57a4498557990a07270f9abd855b246c1039da68cc9ec82d44b40` on disk and is asserted
   byte-, blob- and content-unchanged across the run. The in-memory copy lifted to schema 10 has
   identity `34128ca4c3dd8060cd43e1a0b1097d8abe40b029c03c02d556748a21e86b1d6a`, **computed and
   deliberately not pinned**. The live accepted artifact is read only as a mutation sentinel and
   is asserted byte-unchanged. Every accepted span, record, component, fact, provenance
   coordinate, acceptance record and per-batch schema anchor survives the lift: the five anchors
   are asserted to remain `conditions-1 → schema-3, hazards-1 → schema-5, actions-1 → schema-7,
   attitudes-1 → schema-8, areas-of-effect-1 → schema-9`, schema 10 appears in no anchor, and
   `representation_schema` is asserted to be the **only** payload key the lift moves.
5. **Disjointness from the prior is proven, not assumed.** Zero span-id overlap, zero leaf
   overlap, and zero overlap in all six representation collections. The prior's measured
   collections (`records 46, components 132, prose_bindings 49, relationships 0, references 53,
   provenance 547`), its 530 spans and 46 obligations are re-measured by the generator and
   asserted against the pinned values.
6. **`black` and `ruff` are not run against the generator, by scope not by exception.** The
   repository gates are `black src/ tests/` and `ruff check src/ tests/`; `.claude/review-notes/`
   is outside them, and the already-accepted `areas-of-effect-1` generator fails the same
   checks. Reformatting review-notes scripts would be churn with no gate behind it.

**The six gaps read as ordinary closed declarative schema work.** Each is witnessed by at least
one clause (`gap_witnesses` in the audit) and closed by schema 10: G1 the three-degree closure,
G2 the defensive bonus, G3 the direct-targeting prohibition, G4 the provision polarity, G5 the
opposite-side requirement, G6 most-protective selection. Schema 10 mints **5 fact families over 8
new closed vocabularies** and adds **one member (`half`) to the accepted `CoverDegree`** — whose
own schema-6 docstring said Half Cover *"is outside this batch's cut and is admitted by the batch
that states it"*; this is that batch. It declares **zero intrinsic invariants**, adds no field to
an accepted family, makes nothing required or nullable, and changes no ownership form, which is
what makes the crossing a re-declaration rather than a rewrite. Succession from schema 9
(`f5a5e30817e64f019e31aa7f4692d72611215e4294e7da36242e492bca6b336e`) to schema 10
(`c39e3a35e197a1d1db5c2c2b3445ff0cbf03395c91e3426353a4bce589be4be0`) is the single registered step
`5d-lift-schema-9-to-10`, exercised element by element rather than described.

Nothing here computes or adjudicates geometry. The record states printed thresholds and printed
benefits; choosing a degree for a scene, measuring a line, executing an attack and adapter
ownership all remain outside.

### 9.4 Obligations

Twenty-eight expected obligations are **typed from this checkpoint's clause tables** — clause,
disposition, carrier and witnessed gaps — and only then compared against what the emission loop
produced. Deriving them from generated output would have made the check circular. Each of the 28
is discharged by exactly one span at exactly the reviewed extent with the expected carrier;
omission, duplication and carrier drift each fail the run. The literal table is asserted to split
`{substantive: 16, supporting_authority: 12}` before emission and the gap witnesses are
cross-checked against the checkpoint's own list.

Tally: `typed=15, typed_component_scope=1, supporting_authority_record_owned=8,
supporting_authority_bounding_a_component=3, supporting_authority_bounding_a_fact=1`. Zero
prose-bound, zero unresolved. **Zero prose bindings is a positive claim**: no clause in this
population matches one of the six closed irreducibility reasons, and each of the six is disposed
by name in the audit, so binding one would have recorded a vocabulary gap as an irreducibility.

### 9.5 The three questions §8 put to review — disposition

1. **§4c, one record or three.** Built as **one composite record**, on the three grounds §8 gave
   and no others: accepted authority already cites `glossary.cover` by name, the three degrees are
   untagged table rows with no entry of their own, and `CoverDegree` is already consumed as a
   vocabulary by two accepted facts. §8's correction stands — this is the *sufficient* choice
   under #137 contract 3 and ADR-005d Decision 3, not the only permitted one. It is the first
   record in this build whose authority is drawn from two chapters.
2. **§4a, the doubly-printed rules.** Disposed as **one fact each with `PRIMARY` provenance from
   both sites**, asserted per rule rather than argued: four rules, two primary claimants each, one
   per site. Where the second printing *defers* rather than states (*"As detailed in the Cover
   table"*) it is `SUPPORTING_AUTHORITY` linked to what it defers to, not a second statement of
   the rule.
3. **§4, the six gaps.** They read as ordinary closed declarative schema work: 5 families, 8
   vocabularies, 1 widened member, **0 declared invariant rows**, no accepted family touched. G2
   and G3 are two families rather than one because a bonus has a number and Total Cover's benefit
   is a prohibition. G4 records the printed phrase *an object that covers the whole target* rather
   than reusing `AreaOriginKind.CREATURE_OR_OBJECT`, which would have merged two unrelated
   vocabularies.

### 9.6 Reproduction and gates

From the repository root, on this branch:

```bash
python .claude/review-notes/issue-5d-batch-cover-1-generator.py
pytest -q --no-cov tests/ingestion/mechanical/test_schema_10_cover.py
pytest -q --no-cov tests/ingestion/mechanical/test_cover_1_frozen_prior.py
```

The run re-derives membership from the bound release's containers, re-derives the 30-leaf
boundary and cross-checks it against the manifest, re-pins the manifest digest, rebuilds the
composition, writes both artifacts with LF endings (asserted: no `CR` byte in either), and then
spawns itself once in a clean child process (`COVER1_RERUN=1`) and asserts the final bytes and the
minted identity are identical — **deterministic: True**. Inputs are repository-relative only: the
source PDF, the source manifest, the frozen review prior, the `afterworlds` package. The live
accepted artifact is not an input.

**Test evidence.** `tests/ingestion/mechanical/test_schema_10_cover.py` gained one test:
`test_the_committed_proposal_is_the_composition_this_module_states`, which asserts the committed
`proposed_representation` equals the draft that module composes independently. The generator never
imports the test module and the test module never imports the generator, so the equality is
agreement between two independent statements of one composition — same four components, same eight
facts, same 28 provenance claims at the same coordinates — not a tautology. Identity is
deliberately not pinned in the test: asserting it would make an ordinary re-run of a
reviewed-and-unchanged composition look like a regression.

`pytest tests/ingestion/mechanical -q --no-cov` → **2633 passed** (149.77s) on the working tree
that became this commit. `black --check` and `ruff check` are clean on the changed test module.
**`mypy src/` was not re-run and `pytest -q` was not re-run in full on this head, and no claim is
made that they were.** `src/` is byte-unchanged since `bd11cf6` (`git diff bd11cf6 -- src/` is
empty), and everything this commit changes is outside it: one test in
`tests/ingestion/mechanical/`, two artifacts and one generator under `.claude/review-notes/`, this
section, and an additive `.secrets.baseline` splice. The package suite that covers the changed
test is the 2633-test run above. `detect-secrets` ran through the configured
pre-commit hook (`python -m detect_secrets.pre_commit_hook --baseline .secrets.baseline`) against
the staged files; the baseline grew additively for entropy hits in the two large JSON artifacts
and no detector setting or unrelated entry changed.

### 9.7 Where this still stops

Independent semantic review of this proposal has not happened, and the Owner has not been asked
for exact semantic acceptance. No `accept_proposal`, no live accepted artifact written, no push,
no merge, no publication, no activation, no retirement, no runtime geometry, no adapter work, no
other batch, no dependency maintenance, and no change to parent #137's state. `glossary.speed` and
`glossary.concentration` remain unresolved cross-batch targets belonging to a later glossary
batch. Accepted authority still carries three unresolved targets, including `Cover`. The
full-corpus obligation #137 governs is undischarged: this is one record of it.
