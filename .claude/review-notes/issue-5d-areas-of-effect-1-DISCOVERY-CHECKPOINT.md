# CRD Issue 5d — batch `areas-of-effect-1`: source-discovery and schema-adequacy checkpoint

**Status.** Discovery stop, for Codex's review. Nothing is proposed, drafted, accepted,
lifted, published, activated or retired by this checkpoint, and no schema change is
implemented. It ends here.

**Amended 2026-09-10 — §9.** Discovery membership and the 43-clause inventory passed
independent review unchanged. Four statements elsewhere in this document were wrong or
imprecise and are corrected in place, each marked *(corrected 2026-09-10)*: the G7
quantifier (§4), the reference-collision explanation (§5c), the cover-sequencing
classification (§5b and §8 question 2), and the reading of #137's rules-engine exclusion
(§6). §1's two departure bullets are now historical and carry a superseded note rather
than a rewrite. §9 records what was built against this discovery and what it did not
close. Nothing in §2, §3 or §7 moved.

**Authority.** #137; ADR-005d; ADR-005c Decision 3; `docs/architecture/known_unknowns.md`;
`CLAUDE.md`. The `attitudes-1` selection checkpoint §1 named `[Area of Effect]` as the
remaining complete tagged class and observed a seven-record candidate. That was an
observation; §2 below measures it.

**Reproduce everything here.**

```bash
python .claude/review-notes/issue-5d-areas-of-effect-1-discovery.py
pytest -q --no-cov tests/ingestion/mechanical/test_areas_of_effect_1_frozen_prior.py
```

The first writes `.claude/review-notes/issue-5d-areas-of-effect-1-source-manifest.json`
(LF, sha256 `7fb1cec3a39253fe2e7546f1905a5a13296c5bff8f6b02f982557744a68b13ec`,
byte-identical on rerun). Every clause id cited below is a row in its `clauses` array,
addressable as `leaf_id[char_start:char_end)`. No judgment in this document is encoded in
the script: a discovery run that shipped its own conclusions would be proposing.

---

## 1. What is frozen, and what did not move

`tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1.json`
is the four accepted batches — `conditions-1`, `hazards-1`, `actions-1`, `attitudes-1` —
copied byte for byte from the live accepted artifact and pinned by two independent
identities:

| | |
|---|---|
| Git blob | `2346404005618b0389b4e4f66d2e96c5c35b200f` |
| LF sha256 | `fd390d95dde74498142035d9dde00ccf7effadb372fc13f9662154841bb787ab` |
| `oracle_identity` | `c3b4d4b759441b05418fcbe1d90811e0d7c2535319aa005e64201ce29b5c74fa` |
| Schema | `5d-representation-schema-8` / `8a125f6c…f707afff` |
| Records / spans / obligations | 39 / 487 / 487 acceptances, 39 obligations |
| Collections | records 39, components 109, prose_bindings 49, relationships 0, references 46, provenance 504 |
| Per-batch anchors | `conditions-1`→3, `hazards-1`→5, `actions-1`→7, `attitudes-1`→8 |
| Declared lifts | 3→4, 4→5, 5→6, 6→7, 7→8 |
| Unresolved targets | `glossary.concentration`, `glossary.speed` |

The fixture was produced with `git cat-file blob 2346404005…`, so *fixture blob == live
blob* is the whole preservation proof: the live accepted artifact is unchanged and the
frozen copy is the same content today. `test_areas_of_effect_1_frozen_prior.py` asserts
exactly that as its final test, and every pin above is derived by loading the file rather
than transcribed from the ADR amendment note.

Two departures from the shape of `test_attitudes_1_frozen_prior.py`, both because the
starting position differs and both stated rather than papered over:

* **No crossing is asserted.** The prior declares schema 8 and schema 8 is current, so
  `prior == current`, `validate_schema_binding` is clean, and `lift_path` refuses. Whether
  this batch needs a schema step is what §4 is about; the test states the position instead
  of pre-deciding it.
* **The final test asserts identity, not extension.** Its predecessor did the same until
  `attitudes-1` was accepted. When a fifth batch is accepted this assertion fails first,
  and it is then replaced by the extends-by-exactly-one-batch claim, not deleted.

**Superseded 2026-09-10 — both bullets are historical.** §4 answered the schema question
the first bullet left open, so schema 9 exists and exactly one registered crossing
(`5d-lift-schema-8-to-9`) now separates the prior from the current union.
`test_areas_of_effect_1_frozen_prior.py` was edited to state that — `prior != current`,
`validate_schema_binding` reports a finding on the unlifted prior, `lift_path` returns the
single step, and `oracle_identity` survives it — which is the visible edit the test's own
docstring promised rather than drift. The second bullet still holds: the final test asserts
the live artifact and the frozen copy are the same bytes, because no fifth batch has been
accepted.

The three-batch prior and its test are untouched; their `!=` assertion is still true.

---

## 2. Membership, derived from the tag

`build_candidate(SOURCE_PDF, retrieval_config=RetrievalMemoryConfig())` over
`docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf`, with five binding values re-derived and asserted
by the run: `package_uuid 4458fa10-4a66-5e0e-9ecc-ea37530ad2b4`, `release_version
5.2.1-corpus.36b786d8-fa2`, `authoritative_source_hash 8974902d…`, `transform_config_hash
77720c2f…`, `bundle_root_hash 03353dfb…`. `persisted_corpus_digest c1f54796…` is **not**
derivable without a publish and is disclosed in the manifest as taken from the 5c release
record.

Tag-class sizes, re-measured this run:

| Tag | Entries | Accepted |
|---|---|---|
| Action | 12 | yes |
| Area of Effect | 6 | **no — this batch** |
| Attitude | 3 | yes |
| Condition | 15 | yes |
| Hazard | 5 | yes |

Membership is `sorted(lab for lab in ENTRY_BY_LABEL if lab.endswith(" [Area of Effect]"))`
plus the untagged umbrella entry `Area of Effect` — the same rule the four accepted batches
were selected by. The seven-record observation holds:

| Label | Candidate record key | Kind | Page | Leaves | Clauses |
|---|---|---|---|---|---|
| `Area of Effect` | `glossary.area_of_effect` | `GLOSSARY_RULE` | 176 | 8 | 16 |
| `Cone [Area of Effect]` | `area_of_effect.cone` | `GLOSSARY_RULE` | 178 | 2 | 6 |
| `Cube [Area of Effect]` | `area_of_effect.cube` | `GLOSSARY_RULE` | 178 | 2 | 4 |
| `Cylinder [Area of Effect]` | `area_of_effect.cylinder` | `GLOSSARY_RULE` | 179 | 2 | 4 |
| `Emanation [Area of Effect]` | `area_of_effect.emanation` | `GLOSSARY_RULE` | 180 | 2 | 5 |
| `Line [Area of Effect]` | `area_of_effect.line` | `GLOSSARY_RULE` | 183 | 2 | 4 |
| `Sphere [Area of Effect]` | `area_of_effect.sphere` | `GLOSSARY_RULE` | 187 | 2 | 4 |
| | | | | **20** | **43** |

**Policy exclusions inside the boundary: none.** Listed with reasons rather than asserted
away — `membership.policy_excluded` is an empty array, and a member that lost a body leaf
would appear there rather than silently vanish.

**Cross-check, both directions.** The umbrella prints its own membership across three
flattened two-column leaves (`Cone Cube` / `Cylinder Emanation` / `Line Sphere`) under
*"These shapes are defined elsewhere in this glossary:"*. The six names it prints and the
six the tag yields are asserted equal. In the other direction, **none of the six shapes
prints a "See also" leaf** (`membership_cross_check.shapes_printing_a_see_also` is empty),
so no back-citation to the umbrella is derivable from the source; all six bodies do use the
term *"area of effect"* definitionally, which is a §5 candidate, not a citation.

`RecordKind` is a closed vocabulary with no area-of-effect member. All seven are Rules
Glossary definitions, which is what `GLOSSARY_RULE` means and what `actions-1` gave both
its umbrella and its twelve entries; minting a kind for one class would widen a closed
vocabulary for one batch's convenience. Record keys above are a naming convention carried
forward from `attitude.*`, not a decision.

---

## 3. Clause coverage

Every one of the 20 represented leaves is partitioned end to end and the partition is
asserted to reconstruct the leaf byte for byte. Cuts are located in the bound content at
run time and fail loudly if the source moved, so a re-extraction cannot re-cut a clause
under a judgment written about the old one.

Column *5c* is the ADR-005d Decision 2 disposition (`substantive` / `supporting_authority`
are the only two the four accepted batches use; there are no non-mechanical spans here).
Column *Representation* is §4's judgment, keyed to the gap ids defined there.

### `glossary.area_of_effect` — p176, leaves `8b1fed74 4ff9e24f a93806db 7613fd31 af6478d2 638724ef f7fc8e1e 5ef92f4d`

| Clause | Range | Text | 5c | Representation |
|---|---|---|---|---|
| `Area of Effect/0/0` | `8b1fed74[0:14)` | *Area of Effect* | supporting | title span — existing shape |
| `Area of Effect/1/0` | `4ff9e24f[0:131)` | *The descriptions of many spells and other features specify that they have an area of effect, which typically has one of six shapes.* | supporting | definitional framing — existing shape, precedent `glossary.hazard`'s *"A hazard is an environmental danger."* |
| `Area of Effect/1/1` | `4ff9e24f[131:184)` | *These shapes are defined elsewhere in this glossary:* | supporting | enumeration lead-in — existing shape |
| `Area of Effect/2/0` | `a93806db[0:4)` | *Cone* | supporting | `ReferenceDraft` → `area_of_effect.cone` — existing shape |
| `Area of Effect/2/1` | `a93806db[4:9)` | *Cube* | supporting | `ReferenceDraft` → `area_of_effect.cube` |
| `Area of Effect/3/0` | `7613fd31[0:8)` | *Cylinder* | supporting | `ReferenceDraft` → `area_of_effect.cylinder` |
| `Area of Effect/3/1` | `7613fd31[8:18)` | *Emanation* | supporting | `ReferenceDraft` → `area_of_effect.emanation` |
| `Area of Effect/4/0` | `af6478d2[0:4)` | *Line* | supporting | `ReferenceDraft` → `area_of_effect.line` |
| `Area of Effect/4/1` | `af6478d2[4:11)` | *Sphere* | supporting | `ReferenceDraft` → `area_of_effect.sphere` |
| `Area of Effect/5/0` | `638724ef[0:90)` | *An area of effect has a point of origin, a location from which the effect's energy erupts.* | substantive | **G1** |
| `Area of Effect/5/1` | `638724ef[90:160)` | *The rules for each shape specify how to position its point of origin.* | supporting | pointer to the per-shape rules — existing shape |
| `Area of Effect/5/2` | `638724ef[160:318)` | *If all straight lines extending from the point of origin to a location in the area of effect are blocked, that location isn't included in the area of effect.* | substantive | **G7** |
| `Area of Effect/5/3` | `638724ef[318:376)` | *To block a line, an obstruction must provide Total Cover.* | substantive | **G7** — vocabulary present (`CoverDegree.TOTAL`), predicate absent |
| `Area of Effect/6/0` | `f7fc8e1e[0:8)` | *See also* | supporting | See-also lead-in — existing shape |
| `Area of Effect/7/0` | `5ef92f4d[0:8)` | *"Cover."* | supporting | `ReferenceDraft` → `glossary.cover` — existing shape; **target undefined**, see §5 |
| `Area of Effect/7/1` | `5ef92f4d[8:221)` | *If the creator of an area of effect places it at an unseen point and an obstruction—such as a wall— is between the creator and that point, the point of origin comes into being on the near side of the obstruction.* | substantive | **G8** |

### `area_of_effect.cone` — p178, leaves `9208b6e4 8d464d21`

| Clause | Range | Text | 5c | Representation |
|---|---|---|---|---|
| `Cone/0/0` | `9208b6e4[0:21)` | *Cone [Area of Effect]* | supporting | title span — existing shape |
| `Cone/1/0` | `8d464d21[0:117)` | *A Cone is an area of effect that extends in straight lines from a point of origin in a direction its creator chooses.* | substantive | **G1**, **G2** (creator-chosen direction) |
| `Cone/1/1` | `8d464d21[117:222)` | *A Cone's width at any point along its length is equal to that point's distance from the point of origin.* | substantive | **G5** |
| `Cone/1/2` | `8d464d21[222:328)` | *For example, a Cone is 15 feet wide at a point along its length that is 15 feet from the point of origin.* | supporting | worked example — existing shape; ADR-005d Decision 2 names examples first-class |
| `Cone/1/3` | `8d464d21[328:389)` | *The effect that creates a Cone specifies its maximum length.* | substantive | **G3** (one parameter: maximum length) |
| `Cone/1/4` | `8d464d21[389:489)` | *A Cone's point of origin isn't included in the area of effect unless its creator decides otherwise.* | substantive | **G4** (excluded-unless-creator-includes) |

### `area_of_effect.cube` — p178, leaves `74587a82 ebc0f678`

| Clause | Range | Text | 5c | Representation |
|---|---|---|---|---|
| `Cube/0/0` | `74587a82[0:21)` | *Cube [Area of Effect]* | supporting | title span |
| `Cube/1/0` | `ebc0f678[0:121)` | *A Cube is an area of effect that extends in straight lines from a point of origin located anywhere on a face of the Cube.* | substantive | **G1**, **G2** (any point on a face) |
| `Cube/1/1` | `ebc0f678[121:206)` | *The effect that creates a Cube specifies its size, which is the length of each side.* | substantive | **G3** (one parameter: side length) |
| `Cube/1/2` | `ebc0f678[206:306)` | *A Cube's point of origin isn't included in the area of effect unless its creator decides otherwise.* | substantive | **G4** (excluded-unless-creator-includes) |

### `area_of_effect.cylinder` — p179, leaves `16894c5c 4954b589`

| Clause | Range | Text | 5c | Representation |
|---|---|---|---|---|
| `Cylinder/0/0` | `16894c5c[0:25)` | *Cylinder [Area of Effect]* | supporting | title span |
| `Cylinder/1/0` | `4954b589[0:154)` | *A Cylinder is an area of effect that extends in straight lines from a point of origin located at the center of the circular top or bottom of the Cylinder.* | substantive | **G1**, **G2** (center of circular top or bottom) |
| `Cylinder/1/1` | `4954b589[154:260)` | *The effect that creates a Cylinder specifies the radius of the Cylinder's base and the Cylinder's height.* | substantive | **G3** (**two** parameters: base radius, height) |
| `Cylinder/1/2` | `4954b589[260:324)` | *A Cylinder's point of origin is included in the area of effect.* | substantive | **G4** (included, no exception) |

### `area_of_effect.emanation` — p180, leaves `a38fd7d6 8834ac19`

| Clause | Range | Text | 5c | Representation |
|---|---|---|---|---|
| `Emanation/0/0` | `a38fd7d6[0:26)` | *Emanation [Area of Effect]* | supporting | title span |
| `Emanation/1/0` | `8834ac19[0:112)` | *An Emanation is an area of effect that extends in straight lines from a creature or an object in all directions.* | substantive | **G1**, **G2** — and the one place the origin is **not a point**: a creature or an object |
| `Emanation/1/1` | `8834ac19[112:184)` | *The effect that creates an Emanation specifies the distance it extends.* | substantive | **G3** (one parameter: distance) |
| `Emanation/1/2` | `8834ac19[184:304)` | *An Emanation moves with the creature or object that is its origin unless it is an instantaneous or a stationary effect.* | substantive | **G6** |
| `Emanation/1/3` | `8834ac19[304:422)` | *An Emanation's origin (creature or object) isn't included in the area of effect unless its creator decides otherwise.* | substantive | **G4** (excluded-unless-creator-includes) |

### `area_of_effect.line` — p183, leaves `9e2d76bb ed92551f`

| Clause | Range | Text | 5c | Representation |
|---|---|---|---|---|
| `Line/0/0` | `9e2d76bb[0:21)` | *Line [Area of Effect]* | supporting | title span |
| `Line/1/0` | `ed92551f[0:140)` | *A Line is an area of effect that extends from a point of origin in a straight path along its length and covers an area defined by its width.* | substantive | **G1**, **G2** (straight path along its length) |
| `Line/1/1` | `ed92551f[140:203)` | *The effect that creates a Line specifies its length and width.* | substantive | **G3** (**two** parameters: length, width) |
| `Line/1/2` | `ed92551f[203:303)` | *A Line's point of origin isn't included in the area of effect unless its creator decides otherwise.* | substantive | **G4** (excluded-unless-creator-includes) |

### `area_of_effect.sphere` — p187, leaves `dafddf9b 32cb0337`

| Clause | Range | Text | 5c | Representation |
|---|---|---|---|---|
| `Sphere/0/0` | `dafddf9b[0:23)` | *Sphere [Area of Effect]* | supporting | title span |
| `Sphere/1/0` | `32cb0337[0:110)` | *A Sphere is an area of effect that extends in straight lines from a point of origin outward in all directions.* | substantive | **G1**, **G2** (outward in all directions) |
| `Sphere/1/1` | `32cb0337[110:206)` | *The effect that creates a Sphere specifies the distance it extends as the radius of the Sphere.* | substantive | **G3** (one parameter: radius) |
| `Sphere/1/2` | `32cb0337[206:277)` | *A Sphere's point of origin is included in the Sphere's area of effect.* | substantive | **G4** (included, no exception) |

**Totals.** 43 clauses: 19 `supporting_authority` (12 in the umbrella, one title span per
shape, plus Cone's worked example), 24 `substantive`. All 19 supporting clauses have a
faithful existing shape. Of the 24 substantive, **zero** have a faithful existing shape and
**zero** are irreducible prose; all 24 land in the eight gaps below.

---

## 4. Schema adequacy against representation schema 8

Eight gaps. Each row states the witness clause, the existing shape if any, the distinction a
typed shape would represent, the residue it would not, and — because this is the crossing
Codex's `actions-1` review asked to be made explicit — **where the declarative record ends
and runtime evaluation begins**.

None of the 24 substantive clauses is irreducible prose. `ProseBindingDraft` requires one of
the six closed reasons in `policy.IRREDUCIBILITY_REASONS` — `contextual_applicability`,
`subjective_judgment`, `open_ended_effect`, `gamemaster_latitude`,
`natural_language_exception`, `fiction_dependent_consequence` — and no clause in this class
matches one. Every clause states a closed, printed, non-delegated rule. Binding any of them
as irreducible would be the defect #137 contract 3 names, so each is reported as a missing
vocabulary instead.

| Gap | Witnesses | Existing shape | Represented distinction | Residue | Record ends / runtime begins |
|---|---|---|---|---|---|
| **G1** — a shape has a point of origin | `Area of Effect/5/0`, and the opening clause of all six shapes | **none.** `SpellRange(kind: RangeKind, feet)` is the nearest and is about *range* — where an effect can reach — not about an *area*; `RangeKind` has no area member. `SpellDescriptorFact.spell_range` carries it for spells only | that each shape record has an origin, and what kind of thing the origin is | none identified | the record says an origin exists and what type it is; *where it is placed in play* is chosen at cast time |
| **G2** — per-shape origin placement rule | `Cone/1/0`, `Cube/1/0`, `Cylinder/1/0`, `Emanation/1/0`, `Line/1/0`, `Sphere/1/0` | none | a closed six-member vocabulary drawn from the printed clauses: creator-chosen direction; anywhere on a face; center of the circular top or bottom; a creature or object; a straight path along the length; outward in all directions | none identified. **Emanation is the discriminating witness:** its origin is *a creature or an object*, not a point, so a vocabulary that assumed a point origin would silently lose it | the record names the placement rule; resolving it to coordinates is adapter work |
| **G3** — dimension parameters supplied by the creating effect | `Cone/1/3`, `Cube/1/1`, `Cylinder/1/1`, `Emanation/1/1`, `Line/1/1`, `Sphere/1/1` | `DistanceUnit.FOOT` exists and is exact, and is the vocabulary the *value* would carry — but no substantive clause here prints a unit (the only “feet” in the class is `Cone/1/2`, the worked example). The *parameter set* has no carrier | which parameters each shape requires, and that the value comes from the effect rather than from the shape | **arity varies:** Cylinder needs two (base radius, height) and Line needs two (length, width); the other four need one. A single-slot shape would defeat itself on Cylinder and Line | the record declares the required parameter *names*, which are what this class prints; the unit and the values arrive with the spell or feature that creates the area |
| **G4** — origin-inclusion polarity | `Cone/1/4`, `Cube/1/2`, `Cylinder/1/2`, `Emanation/1/3`, `Line/1/2`, `Sphere/1/2` | none | a closed two-member state, printed and complete over the class: **included** (Cylinder, Sphere) and **excluded unless its creator decides otherwise** (Cone, Cube, Line, Emanation) | none identified | the record states the default and that the creator may override it; *whether the creator did* is a per-cast choice |
| **G5** — Cone's width relation | `Cone/1/1` | none | a named closed taper rule — *width at a point equals that point's distance from the origin* | this is the sharpest declarative/runtime crossing in the class; see the note below | the record names the rule; computing a width at a distance is adapter arithmetic |
| **G6** — Emanation movement and its exception | `Emanation/1/2` | `DurationKind.INSTANTANEOUS` exists and is exact for half the exception | that an Emanation moves with its origin, and the two effect kinds that suspend it | **"stationary effect" has no vocabulary member** anywhere in schema 8 — not in `DurationKind`, not in `SustainedState`, not in `EffectTerminationFact`. It is a distinct printed kind, not a synonym for instantaneous | the record states the movement rule and its two exceptions; tracking an origin's motion is runtime state |
| **G7** — line-of-effect blocking *(corrected 2026-09-10)* | `Area of Effect/5/2`, `Area of Effect/5/3` | `CoverDegree.TOTAL` exists and is exactly the printed degree. The **predicate** that binds it has no carrier | that a location is excluded when **all** straight lines from the point of origin to it are blocked, and that Total Cover is what blocks a line | none identified. **The quantifier is the whole rule.** The shorthand used earlier in this document — *"a blocked line excludes that location"* — drops it and states a strictly stronger, wrong rule: one blocked line among many does not exclude anything. The represented shape must distinguish *all blocked* from *some blocked*, so the quantifier is a named closed member rather than an implicit reading | the record states the rule and the threshold; *which* locations are blocked in a given situation is geometry the adapter computes and is explicitly outside 5d |
| **G8** — unseen-point origin relocation | `Area of Effect/7/1` | none | a closed conditional: creator places the area at an unseen point **and** an obstruction is between them → the origin comes into being on the near side of the obstruction | *"such as a wall"* is inline exemplification, not a closed obstruction vocabulary; it is supporting text inside a substantive clause and must not be read as an enumeration | the record states the relocation rule; identifying the obstruction and the near side is adapter work |

**On G5, and on what the governing text actually forbids.** ADR-005d Decision 4 prohibits,
in the projection, *"arbitrary executable expressions; runtime-interpreted scripts or a
general rules DSL; model-authored mechanical logic; generic numeric/key-value escape
hatches; or mechanically authoritative values inferred from source prose at runtime,"* and
states *"The projection is declarative data consumed by hand-authored code."* ADR-005c
Decision 3 says *"The ingestion pipeline may produce declarative, typed mechanical facts. It
must not produce or execute generated application code, arbitrary executable expressions,
dynamic scripts, model-authored mechanical logic, or an inferred universal rules engine.
Each supported adjudicated game system requires a hand-authored Rules System Adapter that
interprets only approved and bounded typed mechanic shapes."*

Encoding the Cone taper as a formula the projection evaluates would be an executable
expression and is forbidden. Encoding it as a **named closed member** — one value in a
closed vocabulary that a hand-authored adapter interprets — is precisely the "approved and
bounded typed mechanic shape" both decisions describe. The same reading disposes of G7: the
projection records *"a location is excluded when all straight lines from the point of origin
to it are blocked, and Total Cover is what blocks a line,"* and never computes which lines
are blocked in a given situation. *(Quantifier corrected 2026-09-10; the earlier phrasing
here said "a blocked line excludes the location", which is a different and wrong rule.)*

**Distinguishing a missing vocabulary from an open question.** All eight gaps are missing
vocabulary. Each is a closed, printed, enumerable distinction with no product decision, no
ownership move, and no contradiction between authorities; a new fact family plus closed
enums is ordinary declarative schema work, and per the governing instruction a new family
alone does not require an Owner Decision. **Zero of the eight is a genuine unresolved
product or ownership question.** The one item in this batch that plausibly wants an Owner
call is a sequencing question, not a schema one — see §5.

---

## 5. References — enumerated, none closed

Four buckets, kept apart because collapsing them is how a validator count comes to stand in
for a claim. No validator was run; nothing below is a validator result.

**(a) In-batch, source-authored.** Six `ReferenceDraft`s from the umbrella's printed
enumeration (`Area of Effect/2/0` … `4/1`) to the six shape records this batch would define.
Emitted from the enumeration rather than from every prose mention, which is the siting rule
the accepted batches already follow (`glossary.condition` and `glossary.action` emit from
their printed enumerations).

**(b) Confirmed external citation, target undefined.** One: `Area of Effect/7/0` — *"Cover."*
in the umbrella's "See also" — targeting `glossary.cover`. The manifest reports it as
`in_this_batch: false`, `in_frozen_prior: false`, `source_entry_exists: true`: `Cover` is a
real untagged Rules Glossary entry (p179) that no accepted batch has represented.
`CoverDegree`'s own docstring already anticipates this — it carries `THREE_QUARTERS` and
`TOTAL` and says Half Cover *"is outside this batch's cut and is admitted by the batch that
states it."*

**This batch would add a third unresolved reference target, not remove one.** Accepted
authority's residue is `glossary.concentration` and `glossary.speed`, both publication
blockers; `areas-of-effect-1` resolves neither and adds `glossary.cover`. That is a stated
consequence of picking a complete source class, exactly as `attitudes-1` resolving three
targets was a consequence rather than a reason. **Corrected 2026-09-10: this is ordinary engineering under #137, not an Owner
Decision.** #137 already owns build-time reference resolution and already carries two
unresolved targets through four accepted batches; adding a third changes nothing about
ownership, product semantics or any accepted contract, and no authority conflicts with any
other. Batch sequencing is a scheduling choice the implementer makes. This batch therefore
continues and retains `glossary.cover` as unresolved residue alongside
`glossary.concentration` and `glossary.speed`. Cover ingestion is not in this batch, the
batch was not expanded to reach it, and no reference closure was invented for it — the
composition's single validator finding is that citation, quoted in §9. It remains a
publication blocker and is discharged by the batch that states `Cover`.

**(c) Candidate in-text terms, unclassified.** All six shape bodies use the term *"area of
effect"* definitionally (`membership_cross_check.shape_bodies_naming_the_umbrella_term`
lists all six). None of the six prints a "See also" leaf. Under the accepted siting rule the
source does not cite the umbrella as a defined term from the shape entries, so no
back-reference is derivable; recording one would be the projection asserting a citation the
source does not make. Left as a candidate for the proposal stage rather than decided here.
The same applies to *"Total Cover"* inside `Area of Effect/5/3`, which is a term in use
inside a substantive clause and is not a citation the source authors. *(Corrected
2026-09-10.)* The earlier reason given here — *"siting it twice would collide, since
`reference_target_key` keys on `source_text`"* — was wrong on both counts and is withdrawn:
two references with different `source_text` do not thereby share a
`reference_target_key`, so no collision follows. The criterion is the siting rule the
accepted batches already use: the projection emits a reference where the **source** authors
a citation, and the source authors exactly one here — the *"Cover."* under *See also* at
`Area of Effect/7/0`. Emitting a second from a term in running prose would be the
projection asserting a citation the source does not make. That is also why the blocking
threshold in `Area of Effect/5/3` is represented as a typed `CoverDegree` member inside the
fact rather than as a second reference.

**(d) Targets supplied by the frozen prior.** None. No clause in this class cites a record
`conditions-1`, `hazards-1`, `actions-1` or `attitudes-1` defines. The prior's 39 record
keys are listed in `review_prior.record_keys`.

---

## 6. Boundaries, stated from the text that states them

* **`docs/architecture/known_unknowns.md` contains no entry for area of effect, geometry,
  grid, line of effect, or any of the six shapes.** Verified:
  `grep -nEi "area of effect|geometr|grid|cone|cylinder|emanation|line of effect|sphere|cube" docs/architecture/known_unknowns.md`
  exits 1 with no output. No Known Unknown is cited here and none is invented. If Codex
  judges that one belongs, that is an addition to make deliberately, not a boundary this
  checkpoint may lean on.
* **#137 excludes a generic rules engine explicitly, and this build does not approach it.**
  *(Corrected 2026-09-10. The earlier bullet here argued that "no general rules engine" was
  not accepted-authority wording. It is: #137's own Out of scope list carries it, and the
  argument is withdrawn as beside the point — the exclusion is real and the reconciliation
  below is what actually matters.)* #137 Out of scope reads *"Generated executable
  mechanics, a runtime rules language, a generic rules engine, or a cross-system plugin
  framework."* The same issue's In scope reads *"Typed deterministic-consumer and
  GameMaster-facing authority views"* and *"Typed record/component/fact `RuleOverride`
  application with existing precedence semantics."* Both are true at once, and the line
  between them is **declarative representation versus runtime execution**: what a rule
  *says*, in closed typed members a hand-authored adapter interprets, is in scope; anything
  that *evaluates* a rule at runtime is not. Every schema-9 family states a printed rule as
  named members. None carries an expression, a predicate to evaluate, a formula, a
  free-form value or a dispatch table; the vocabularies are closed and exhaustively
  enumerated, so a consumer that met a member it did not handle would fail rather than
  interpret. Cone's taper is the name of the printed relation, not arithmetic; G7 is the
  name of the printed condition, not a line-of-sight test; G8 is the name of the printed
  relocation, not obstruction detection. ADR-005d Decision 4 and ADR-005c Decision 3, both
  quoted verbatim in §4, draw the same line in the same place.
* **The `attitudes-1` deferral rationale is a starting observation, and it was measured.**
  It reads *"point of origin, shape dimensions, origin inclusion, line of effect blocked by
  Total Cover."* All four are real (G1/G3/G4/G7). What it does **not** survive is the
  framing: the source contains **no grid language at all**. The strings `square`, `grid`,
  `battle`, `map`, `token` and `space` appear in zero of the 43 clauses. The selection
  checkpoint's *"whether the origin square is included"* is grid vocabulary the bound source
  does not use; the source says *point of origin* and *feet*. The distinction matters
  because "does the origin square count" sounds like a grid-simulation question, and
  *"A Cylinder's point of origin is included in the area of effect"* is a printed
  declarative state.
* **Runtime geometry stays outside.** ADR-005d Decision 11 leaves adapter capability,
  certification and execution to 15c. Nothing here proposes a geometry engine, grid
  simulation, adapter execution or downstream adjudication, and the scope line of this
  invocation forbids all four.
* **No source re-extraction.** The run reads the committed PDF through the existing 5c
  pipeline and asserts the five derivable binding values; it changes no extraction, no
  retrieval config and no corpus artifact.

---

## 7. Checks that were actually run

| Check | Result |
|---|---|
| `pytest -q --no-cov tests/ingestion/mechanical/test_areas_of_effect_1_frozen_prior.py` (7 tests) + the three-batch prior's 7 | 14 passed |
| Five release-binding values re-derived from the committed PDF and asserted | pass |
| Tag-class sizes re-measured | `{Action: 12, Area of Effect: 6, Attitude: 3, Condition: 15, Hazard: 5}` |
| Umbrella enumeration ⇔ tag membership, asserted equal both directions | pass |
| Every cut located in bound content, asserted unique within its leaf | pass, 43 cuts |
| Partition reconstructs each leaf byte for byte | pass, 20 leaves |
| Any leaf in the boundary without a cut table entry | refused by assertion; none |
| Policy exclusions inside the boundary | 0, listed rather than asserted away |
| Frozen prior digest, blob and `oracle_identity` before and after the run | unmoved |
| Live accepted artifact read as a mutation sentinel, never as an input | unmoved |
| Every other file in `.claude/review-notes/` digested before and after | unmoved |
| Manifest reproducibility | rerun byte-identical, sha256 `7fb1cec3a39253fe2e7546f1905a5a13296c5bff8f6b02f982557744a68b13ec` |
| Manifest reproduced from a clean `git archive HEAD` export, outside the working tree | byte-identical, same sha256 |

Not run, and not implied: the publication gate (there is no persisted projection to run it
over), the semantic validator (there is no draft), any acceptance script, any lift.

---

## 8. Where this stops

Delivered: the four-batch frozen prior and its contract test; the reproducible discovery
run and its manifest; this checkpoint. Not done, and not to be done before Codex reviews:
any schema change, any proposal, any draft, acceptance, push, merge, publication,
activation, retirement or parent-issue state change.

**The two questions this checkpoint puts to review:**

1. Do the eight gaps in §4 read as ordinary closed declarative schema work — one new fact
   family with four or five closed vocabularies — or does any of them read to Codex as a
   product or ownership question this checkpoint has under-called? G5 and G7 are where a
   reasonable reviewer would push.
2. ~~`glossary.cover` (§5b). Sequence `cover-1` first, together, or after?~~ **Settled
   2026-09-10 as ordinary engineering, not an Owner Decision** — see the corrected §5b.
   This batch continues and retains `glossary.cover` as unresolved residue; cover ingestion
   is a later batch and nothing here anticipates its content.

---

## 9. Implementation record — 2026-09-10

Written after the review this checkpoint was raised for. Discovery membership and the
43-clause inventory are unchanged; this section records what was built against them.

**Representation schema 9.** Seven fact families over eleven closed vocabularies, one per
gap in §4 except that G1 and G2 share `area_origin` — the general point-of-origin rule and
the per-shape placement rule are one fact's fields, so the two coexist on a shape record
without either restating the other, and Emanation states a creature-or-object origin in the
same field where the other five state a point. `REPRESENTATION_SCHEMA_VERSION` is
`5d-representation-schema-9`; the derived hash is
`0be1696e0d5167f764a25c3faea8d16dc886b751425683468b1e0bad284f83f9`. One registered crossing,
`5d-lift-schema-8-to-9`, joins it to schema 8. Accepted bytes are not re-declared: the
committed artifact still says schema 8, still records its own five lifts, and
`oracle_identity` is unmoved on both frozen priors after lifting.

**Vocabulary boundaries chosen here.** Each vocabulary holds exactly the members the 43
clauses print, spelled as the source spells them. `blocking_cover` is typed as the whole
`CoverDegree` from schema 6 rather than pinned to `TOTAL`, because the field's type is the
*kind* of thing that blocks and the printed threshold is the *value*; `CoverDegree` is
therefore deliberately not a schema-9 vocabulary. No parameter value, unit, coordinate or
grid semantic is represented anywhere: `AreaDimension` names the parameters the source
prints and says the creating effect supplies them, and Cylinder's two and Line's two arrive
as an ordered tuple rather than a fixed slot.

**Clause to fact, all 23.** Twenty-four substantive clauses become twenty-three facts:
`Area of Effect/5/2` and `5/3` jointly state one `BlockedLineExclusionFact`, and both claim
it as PRIMARY on their own spans. The remaining 19 clauses are supporting authority and
claim CONTEXTUAL. Generated from the committed composition, not transcribed.

| Record | Clauses | Component | Family | What the fact states |
|---|---|---|---|---|
| `glossary.area_of_effect` | `Area of Effect/5/0` | `area_origin` | `AreaOriginFact` | origin = `point` |
| `glossary.area_of_effect` | `Area of Effect/5/2`, `Area of Effect/5/3` | `blocked_line_exclusion` | `BlockedLineExclusionFact` | blocked = `all_straight_lines_from_the_point_of_origin`; blocking_cover = `total` |
| `glossary.area_of_effect` | `Area of Effect/7/1` | `unseen_origin_relocation` | `UnseenOriginRelocationFact` | placement = `at_an_unseen_point`; obstruction = `between_the_creator_and_the_point`; relocated_to = `near_side_of_the_obstruction` |
| `area_of_effect.cone` | `Cone/1/0` | `area_origin` | `AreaOriginFact` | origin = `point`; extent = `straight_lines_in_a_direction_its_creator_chooses` |
| `area_of_effect.cone` | `Cone/1/1` | `area_width_relation` | `AreaWidthRelationFact` | relation = `equal_to_that_points_distance_from_the_point_of_origin` |
| `area_of_effect.cone` | `Cone/1/3` | `area_dimension_requirement` | `AreaDimensionRequirementFact` | dimensions = `maximum_length` |
| `area_of_effect.cone` | `Cone/1/4` | `area_origin_inclusion` | `AreaOriginInclusionFact` | inclusion = `excluded_unless_its_creator_decides_otherwise` |
| `area_of_effect.cube` | `Cube/1/0` | `area_origin` | `AreaOriginFact` | origin = `point`; extent = `straight_lines`; placement = `anywhere_on_a_face_of_the_cube` |
| `area_of_effect.cube` | `Cube/1/1` | `area_dimension_requirement` | `AreaDimensionRequirementFact` | dimensions = `size_the_length_of_each_side` |
| `area_of_effect.cube` | `Cube/1/2` | `area_origin_inclusion` | `AreaOriginInclusionFact` | inclusion = `excluded_unless_its_creator_decides_otherwise` |
| `area_of_effect.cylinder` | `Cylinder/1/0` | `area_origin` | `AreaOriginFact` | origin = `point`; extent = `straight_lines`; placement = `center_of_the_circular_top_or_bottom` |
| `area_of_effect.cylinder` | `Cylinder/1/1` | `area_dimension_requirement` | `AreaDimensionRequirementFact` | dimensions = `radius_of_the_base`, `height` |
| `area_of_effect.cylinder` | `Cylinder/1/2` | `area_origin_inclusion` | `AreaOriginInclusionFact` | inclusion = `included` |
| `area_of_effect.emanation` | `Emanation/1/0` | `area_origin` | `AreaOriginFact` | origin = `creature_or_object`; extent = `straight_lines_in_all_directions` |
| `area_of_effect.emanation` | `Emanation/1/1` | `area_dimension_requirement` | `AreaDimensionRequirementFact` | dimensions = `distance_it_extends` |
| `area_of_effect.emanation` | `Emanation/1/2` | `area_origin_movement` | `AreaOriginMovementFact` | suspended_by_any_of = `instantaneous_effect`, `stationary_effect` |
| `area_of_effect.emanation` | `Emanation/1/3` | `area_origin_inclusion` | `AreaOriginInclusionFact` | inclusion = `excluded_unless_its_creator_decides_otherwise` |
| `area_of_effect.line` | `Line/1/0` | `area_origin` | `AreaOriginFact` | origin = `point`; extent = `straight_path_along_its_length_covering_the_area_its_width_defines` |
| `area_of_effect.line` | `Line/1/1` | `area_dimension_requirement` | `AreaDimensionRequirementFact` | dimensions = `length`, `width` |
| `area_of_effect.line` | `Line/1/2` | `area_origin_inclusion` | `AreaOriginInclusionFact` | inclusion = `excluded_unless_its_creator_decides_otherwise` |
| `area_of_effect.sphere` | `Sphere/1/0` | `area_origin` | `AreaOriginFact` | origin = `point`; extent = `straight_lines_outward_in_all_directions` |
| `area_of_effect.sphere` | `Sphere/1/1` | `area_dimension_requirement` | `AreaDimensionRequirementFact` | dimensions = `distance_it_extends_as_the_radius` |
| `area_of_effect.sphere` | `Sphere/1/2` | `area_origin_inclusion` | `AreaOriginInclusionFact` | inclusion = `included` |

**Evidence.** `tests/ingestion/mechanical/test_schema_9_areas_of_effect.py` composes the
class from the reviewed manifest — clause text is read byte-exact from
`issue-5d-areas-of-effect-1-source-manifest.json`, never retyped — and carries it through
construction, `validate_representation`, serialization, persistence and reconstruction,
`_base_records`, both consumer views, and identity. Refusals cover the all-versus-some
quantifier, the Total Cover threshold, out-of-closure members, a placement without an
extent, field deletion from the unseen-origin conjunction, malformed collections, and the
claim that schema 8 can state none of it. The GameMaster view is asserted to render no
clause text. Override-seam cases live in
`tests/services/rules_authority/test_expanded_families_overrides.py`: one appending
area-of-effect fact reaches the typed view with no span ids and its override id attached,
and three widening payloads are `INVALID_OVERRIDE`.

**The validator result, stated exactly.** The composition does **not** validate clean. It
produces exactly one finding:

```
reference srd-5.2.1/rules-glossary:'Cover': unknown target record glossary.cover
```

That tuple is asserted exactly rather than filtered, so a second finding cannot hide behind
the first. It is the §5b residue and it clears when `Cover` is ingested. Accepted authority
carries two findings of precisely this class today, for `Speed` and `Concentration`;
`_validate_relationships_and_references` was run against the committed artifact to confirm
that rather than assumed.

**What this section does not claim.** No proposal exists, nothing is accepted, published,
activated or retired, and no parent-issue state changed. The full-corpus work #137 governs
is untouched and undischarged: this batch represents one tagged class. Architecture Notes
for the eventual PR are carried by this checkpoint until proposal generation, which is a
later invocation.
