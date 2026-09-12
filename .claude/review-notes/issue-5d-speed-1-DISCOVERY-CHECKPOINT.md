# CRD Issue 5d — batch `speed-1`: source-discovery and schema-adequacy checkpoint

**Status.** Discovery stop, for Codex's review. Nothing is proposed, drafted, accepted,
lifted, published, activated or retired by this checkpoint, and no schema change is
implemented. It ends here.

**Authority.** #137; ADR-005d; `docs/architecture/known_unknowns.md`; `CLAUDE.md`. The
accepted six-batch artifact carries exactly two unresolved reference targets,
`glossary.concentration` and `glossary.speed`, recorded at `known_unknowns.md:499-500`;
`glossary.speed` is cited once, by `action.dash`. Selecting `Speed` next is ordinary batch
sequencing under #137. Concentration remains separate and is untouched here.

**The population is not the reference count and not the word.** Neither *every occurrence
of "speed"* (573 leaves in the bound release) nor *the unresolved-target count* is the
population. Membership is derived from the source's own containers and its own printed
reciprocal citations (§2), and everything the derivation excludes is enumerated (§6).

**Reproduce everything here.**

```bash
python .claude/review-notes/issue-5d-speed-1-discovery.py
pytest -q --no-cov tests/ingestion/mechanical/test_speed_1_frozen_prior.py
```

The first writes `.claude/review-notes/issue-5d-speed-1-source-manifest.json` (LF, sha256
`8c8ea8eed38feaeb28d74386690b5ee28e43872b1316517b922fb89afa016b20`, 417,161 bytes,
byte-identical on rerun). Every clause id cited below is a row in its `clauses` array,
addressable as `leaf_id[char_start:char_end)`. No judgment in this document is encoded in
the script: it emits no disposition and no candidate record key, because a discovery run
that shipped its own conclusions would be proposing.

---

## 1. What is frozen, and what did not move

`tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1_areas_of_effect_1_cover_1.json`
is the six accepted batches — `conditions-1`, `hazards-1`, `actions-1`, `attitudes-1`,
`areas-of-effect-1`, `cover-1` — created by
`git cat-file blob b7c0149432072d4a3b151d0f9b2c458252e584da` and pinned by two independent
identities:

| Identity | Value |
|---|---|
| content sha256 (LF) | `391c71b72d7fa9406890c74eed9a505278ea4f8f4536a01cd3db1edf403f6407` |
| git blob | `b7c0149432072d4a3b151d0f9b2c458252e584da` (732,613 bytes) |
| `oracle_identity` | `86cd11c2be330f5962982d8d87dfc1847815710868223257529f30bef8cdb500` |
| representation schema | `5d-representation-schema-10`, hash `c39e3a35e197a1d1db5c2c2b3445ff0cbf03395c91e3426353a4bce589be4be0` |

Fixture blob == live blob is the whole preservation proof: the live accepted artifact under
`src/afterworlds/ingestion/mechanical/oracles/` is untouched, and the copy is the same
content today. Everything else is derived by loading the file rather than transcribed — six
batch ids, per-batch schema anchors 3/5/7/8/9/10, the seven declared lifts
(`5d-lift-schema-3-to-4` … `5d-lift-schema-9-to-10`), 47 records, 558 spans, 558
acceptances, 47 obligations, 136 components, 173 facts, 49 prose bindings, 0 relationships,
53 references, 575 provenance claims, and the exact unresolved residue
`{glossary.concentration, glossary.speed}`.

**Two departures from the `cover-1` frozen prior, both stated rather than papered over.**

* **No crossing is asserted.** The prior declares schema 10 and schema 10 is current, so
  `validate_schema_binding` returns `()` and `lift_path` raises `UnknownSchemaLiftError`.
  Whether this batch needs a schema step is the open question this checkpoint exists to
  answer (§4), not something the contract test may pre-decide. The manifest records
  `current_schema_reached_by: []` for the same reason.
* **The inherited-citation test is inverted.** `cover-1`'s equivalent test pinned a citation
  whose target was *about to be defined*;
  `test_the_one_accepted_citation_of_speed_is_the_reference_this_batch_inherits` pins the
  single accepted citation of `Speed` whole — from `action.dash`, component `""`, scope
  `srd-5.2.1/rules-glossary`, source text `Speed`, target `glossary.speed` undefined — and
  additionally records the precedent that Dash's *own* body says *"such as a Fly Speed or
  Swim Speed"* and emitted **no** reference for it. That asymmetry is the position §5 must
  be measured against.

The five-batch prior and its test are untouched, as are all earlier frozen fixtures.
`.secrets.baseline` gained one additive 123-entry block for the new fixture, copied from the
live oracle's block with the filename swapped; the two files are byte-identical, so the
findings are too. `git diff --numstat .secrets.baseline` reported **863 insertions, 0
deletions**, `generated_at`, every detector setting and every pre-existing block
byte-identical, and the configured pre-commit hook exits 0.

**Source binding, and the exact limit of what a rederivation proves.** The run re-derives
five of the six `release_binding` values from the committed PDF through the existing 5c
pipeline and asserts each: `release_version 5.2.1-corpus.36b786d8-fa2`, `package_uuid
4458fa10-4a66-5e0e-9ecc-ea37530ad2b4`, `authoritative_source_hash 8974902d…`,
`transform_config_hash 77720c2f…`, `bundle_root_hash 03353dfb…`. The sixth,
`persisted_corpus_digest c1f54796…`, is **disclosed rather than rederived**: recomputing it
needs a session over the persisted rows plus read-back vector state
(`persistence.recompute_persisted_digest`), and checking a published release against its
declared values is `operational.load_verified_operational_corpus`, the narrower downstream
trust seam. Neither requires a publish; **this run simply performs neither.** No operational
database evidence is produced here at all — no session, no `rp_sources`, no Chroma, no
persistence layer touched. What the five asserted values prove is that the leaves, clause
offsets and container structure below come from the same bound 5c release the accepted prior
was built against. They do not speak to the operational database's state.

---

## 2. Membership — the label is not the query, the printed citation is

`cover-1` could read membership off labels: exactly two `entry` containers were labeled
`Cover` and both stated the rule. **That test fails here.** Four containers in the bound
release are labeled exactly `Speed`, and three of them are not this rule:

| Container labeled `Speed` | Why it is not the rule |
|---|---|
| `Character Origins > Character Species > Speed` | a pointer: a character's species determines the value |
| `Equipment > Mounts and Vehicles > Speed` | a homonym — vehicle speed in miles per hour |
| `Monsters > Parts of a Stat Block > Speed` | a pointer that defers explicitly: *"Rules for Speed and these specials speeds appear in 'Rules Glossary'"* |

The run asserts the four paths as a *set* rather than a count, so a release that renamed one
or grew a fifth fails loudly instead of being carried silently.

**What the source does print is a reciprocal citation, and that is the query.**

* the Rules Glossary entry ends `See also` + a citation naming `“Playing the Game” (“Combat”)`
  — `glossary/2/0` and `glossary/3/5`. The run asserts that citation contains both
  `Playing the Game` and `Combat`, which are the labels of the other entry's own ancestors;
* exactly **one** leaf in the entire bound release prints the sentence
  *See “Rules Glossary” for more about Speed* — `afee8441`, clause `combat/3/5` — and it
  belongs to `Playing the Game > Combat > Movement and Position`.

| Site | Container | Path | Printed page | Leaves |
|---|---|---|---|---|
| `glossary` | `3b338d09-9ce0-5250-9095-46a355d84706` | `Rules Glossary > Rules Definitions > Speed` | p188 (index 187) | 12 |
| `combat` | `e5d903f4-cfd5-59ec-ae0d-073ed3d6cca9` | `Playing the Game > Combat > Movement and Position` | p14 (index 13) | 4 |

**The reciprocal query is narrower than co-occurrence, and the run discloses by how much.**
Three `Combat` entries mention both `Rules Glossary` and `Speed` — `Movement and Position`,
`Dropping Prone`, `Mounting and Dismounting` — because neither of the other two cites the
glossary about Speed: `Dropping Prone` cites it for the Prone condition, and `Mounting and
Dismounting`'s only glossary mention arrives in a bled-in Resting paragraph — *“Rules
Glossary” provides the rules for Short and Long Rests* — which its rule does not print at
all. A naive co-occurrence test would pull in two entries that state no Speed rule. The narrowing is a checked
assertion, not a claim: the exact sentence is located and asserted unique release-wide, and
the wider figure is recorded as `direction.naive_cooccurrence_would_have_matched`.

**Third-party corroboration, printed by neither member.** `Playing the Game > Combat > Your
Turn` restates the allowance in almost the population's words and then hands the movement
rules over by name: `f98dd786` prints *“Movement and Position” later in “Playing the Game”
gives the rules for movement* — asserted unique release-wide and asserted to belong to a
container that is **not** the `combat` site. The source itself nominates `Movement and
Position` as where the movement rules are. `Your Turn` is nonetheless boundary, not
membership (§6): it owns its own entry, and what it states is the turn's action economy —
*move **and take one action***.

**`Movement and Position` states rather than uses.** It is a member because it prints two
rules the glossary entry never states: the per-turn allowance with its explicit option to
decline (`combat/1/0`+`combat/2/0`, `combat/2/1`) and the depletion rule
(`combat/3/2`). This is the same two-chapter shape `cover-1` established, not a new one.

**The source owns the boundary.** A leaf is in this population because the bound release
*attaches* it to one of those two entries — not because it prints the word. 557 other leaves
print `speed` in some case (§6); every one uses the quantity while stating some other rule.

**Structural test, applied consistently — including where it costs this batch.** The four
special-speed glossary entries (`Burrow Speed`, `Climb Speed`, `Fly Speed`, `Swim Speed`)
each own their own `entry` container, so by the same test each states its own rule and none
is a member here, even though the population's prose names all four and each cites `“Speed.”`
back. The rejected alternative is named: `Monsters > Parts of a Stat Block > Speed` prints an
apparently closed list — *"Some monsters have one or more of the following speeds: Burrow,
Climb, Fly, Swim"* — which would look like a class enumeration in the `areas-of-effect-1`
sense — but that container is outside the population, and the *defining*
site is explicitly open (`glossary/5/0` says *"such as"*). Reading the four as members of
this batch would take its membership rule from a page it excluded.

**Extraction artifacts, carried verbatim rather than repaired.** Both are properties of the
frozen 5c release.

* **Three printed sentences arrive split across leaves**, at column and page boundaries —
  see §3. The run reconstructs each and asserts it.
* **Four member leaves extract as `leaf_type: "stat_field"`** — `a2ac2ebd`, `c6d4aae3`,
  `2f12fa72`, `4744f798` — because each begins with the word `Speed` followed by a comma or
  a verb, which is also a stat-block field's shape. They are running prose. No leaf type is
  changed and no extraction is altered.
* **This population owns no printed table**, and the committed `srd_table_inventory.json` is
  the independent witness: the run asserts every member leaf is attached directly to its
  entry, then filters the frozen inventory to the two printed pages the population occupies
  and asserts that none of the three tables on p14 (`8108ad3f…` size/space, `bcd448bc…`
  unseen attackers and targets, `bf31d5fe…` moving through a space) is owned by a member
  container. p188 has none at all. `cover-1`'s table-splitting problem does not arise here.

No source-corpus change is proposed or made.

---

## 3. Clause coverage — 16 leaves, 36 clauses, gap-free and byte-exact

Every leaf is reconstructed byte for byte from its clauses; `policy.exclusion_reason_for`
excludes **none** of the 16. Cuts are located in the bound content at run time and asserted
unique within their leaf, so a re-extraction cannot silently re-cut a clause under a
judgment written about the old one.

`S` = substantive candidate, `A` = supporting authority candidate. These are the
checkpoint's readings for review, not accepted dispositions.

### `glossary` site — p188, 12 leaves

| Clause | Range | Text | Read | What it states / why |
|---|---|---|---|---|
| `glossary/0/0` | `193c5f92[0:5)` | `Speed` | A | entry heading; navigational |
| `glossary/1/0` | `bef2033c[0:23)` | `A creature has a Speed,` | A | the possession claim — every creature has one. States no quantity, unit or window |
| `glossary/1/1` | `bef2033c[23:103)` | ` which is the distance in feet the creature can cover when it moves on its turn.` | **S** | **G1** — the definition proper: unit (feet), quantity kind (distance), and window (on its turn). §4a argues both readings |
| `glossary/2/0` | `b469c79c[0:8)` | `See also` | A | cross-reference heading; the reading `areas-of-effect-1` and `cover-1` both gave their own |
| `glossary/3/0` | `88acf51c[0:11)` | `“Climbing,”` | A | §5b — cites a glossary **entry** that exists |
| `glossary/3/1` | `88acf51c[11:23)` | ` “Crawling,”` | A | §5b |
| `glossary/3/2` | `88acf51c[23:33)` | ` “Flying,”` | A | §5b |
| `glossary/3/3` | `88acf51c[33:44)` | ` “Jumping,”` | A | §5b |
| `glossary/3/4` | `88acf51c[44:55)` | ` “Swimming”` | A | §5b |
| `glossary/3/5` | `88acf51c[55:90)` | ` and “Playing the Game” (“Combat”).` | A | §5c — cites a **chapter and section**, not a record. This is also the membership derivation (§2) |
| `glossary/4/0` | `ac4db61a[0:15)` | `Special Speeds.` | A | subsection heading |
| `glossary/5/0` | `05dabf62[0:76)` | `Some creatures have special speeds, such as a Burrow Speed, Climb Speed, Fly` | **S** | **G6**, first of three parts of one sentence (see below). Establishes the open category *special speed* |
| `glossary/6/0` | `a2ac2ebd[0:46)` | `Speed, or Swim Speed, each of which is defined` | **S** | **G6**, second part — the four named members, and the explicit pointer §5d turns on |
| `glossary/7/0` | `a4accfca[0:17)` | `in this glossary.` | **S** | **G6**, third part |
| `glossary/7/1` | `a4accfca[17:89)` | ` If you have more than one speed, choose which one to use when you move;` | **S** | **G4** — selection among speeds |
| `glossary/7/2` | `a4accfca[89:141)` | ` you can switch between the speeds during your move.` | **S** | **G4** — mid-move switching. Cut at the semicolon because selecting and switching are two claims |
| `glossary/7/3` | `a4accfca[141:218)` | ` Whenever you switch, subtract the distance already moved from the new speed.` | **S** | **G4** — the switching cost rule |
| `glossary/7/4` | `a4accfca[218:271)` | ` The result determines how much farther you can move.` | **S** | **G4** — what the subtraction yields |
| `glossary/7/5` | `a4accfca[271:352)` | ` If the result is 0 or less, you can’t use the new speed during the current move.` | **S** | **G4** — the printed floor, and a prohibition rather than an arithmetic note |
| `glossary/7/6` | `a4accfca[352:494)` | ` For example, if you have a Speed of 30 and a Fly Speed of 40, you could fly 10 feet, walk 10 feet, and leap into the air to fly 20 feet more.` | A | worked example; the `Cone/1/2` precedent in `areas-of-effect-1` and `combat/1/4` in `cover-1` |
| `glossary/8/0` | `a1ebf029[0:23)` | `Changes to Your Speeds.` | A | subsection heading |
| `glossary/9/0` | `8421e19c[0:150)` | `If an effect increases or decreases your Speed for a time, any special speed you have increases or decreases by an equal amount for the same duration.` | **S** | **G5 — printed only here.** The propagation rule. §4b is the whole of why this clause matters to accepted authority |
| `glossary/9/1` | `8421e19c[150:260)` | ` For example, if your Speed is reduced to 0 and you have a Climb Speed, your Climb Speed is also reduced to 0.` | A | worked example |
| `glossary/9/2` | `8421e19c[260:279)` | ` Similarly, if your` | A | worked example, part 1 of 3 (see below) |
| `glossary/10/0` | `c6d4aae3[0:50)` | `Speed is halved and you have a Fly Speed, your Fly` | A | worked example, part 2 |
| `glossary/11/0` | `2f12fa72[0:21)` | `Speed is also halved.` | A | worked example, part 3 |

### `combat` site — p14, 4 leaves

| Clause | Range | Text | Read | What it states / why |
|---|---|---|---|---|
| `combat/0/0` | `8f05389a[0:21)` | `Movement and Position` | A | entry heading |
| `combat/1/0` | `b93abccd[0:51)` | `On your turn, you can move a distance equal to your` | **S** | **G2**, part 1 of one sentence |
| `combat/2/0` | `4744f798[0:14)` | `Speed or less.` | **S** | **G2**, part 2. *"or less"* makes the allowance an upper bound, not an amount |
| `combat/2/1` | `4744f798[14:45)` | ` Or you can decide not to move.` | **S** | **G2** — the explicit permission to move zero. A separate printed claim, not a restatement of *"or less"* |
| `combat/3/0` | `afee8441[0:105)` | `Your movement can include climbing, crawling, jumping, and swimming (each explained in “Rules Glossary”).` | **S** | **G6** — the printed mode list. `MovementMode.CRAWL`'s own comment and `MovementPermissionFact`'s docstring already cite *this clause* as their vocabulary evidence (§4). The parenthetical names a **chapter**, so §5c applies: no reference |
| `combat/3/1` | `afee8441[105:224)` | ` These different modes of movement can be combined with your regular movement, or they can constitute your entire move.` | **S** | **G6** — modes compose with the base move, up to the whole of it |
| `combat/3/2` | `afee8441[224:394)` | ` However you’re moving with your Speed, you deduct the distance of each part of your move from it until it is used up or until you are done moving, whichever comes first.` | **S** | **G3 — printed only here.** Depletion: the allowance is a pool, each part of the move is subtracted from it, and the move ends at the earlier of exhaustion or choice |
| `combat/3/3` | `afee8441[394:455)` | ` A character’s Speed is determined during character creation.` | A | sourcing, not a mechanic. States where the value comes from |
| `combat/3/4` | `afee8441[455:511)` | ` A monster’s Speed is noted in the monster’s stat block.` | A | sourcing. Points at exactly the shape `CreatureSpeedFact` already carries (*"``Speed 20 ft.``"*), so it is a pointer to an existing schema shape rather than a gap |
| `combat/3/5` | `afee8441[511:635)` | ` See “Rules Glossary” for more about Speed as well as about special speeds, such as a Climb Speed, Fly Speed, or Swim Speed.` | A | the membership citation (§2). Names a **chapter** and uses *"such as"* — Dash-identical, so §5c and the Dash precedent both give it no reference |

**Three printed sentences cross leaf boundaries.** Carried verbatim; the run names each
group of clause ids and asserts the reconstruction, so a judgment about a whole sentence
cites the exact subspans it rests on instead of implying a leaf boundary the source does not
print.

| Clauses | Reconstructed sentence |
|---|---|
| `glossary/5/0` `glossary/6/0` `glossary/7/0` | *Some creatures have special speeds, such as a Burrow Speed, Climb Speed, Fly Speed, or Swim Speed, each of which is defined in this glossary.* |
| `glossary/9/2` `glossary/10/0` `glossary/11/0` | *Similarly, if your Speed is halved and you have a Fly Speed, your Fly Speed is also halved.* |
| `combat/1/0` `combat/2/0` | *On your turn, you can move a distance equal to your Speed or less.* |

Each group is asserted three ways: no non-final part ends in `.`, the final part does, and
the parts come from distinct leaves. This is new relative to `cover-1`, whose 28 clauses
never crossed a leaf.

---

## 4. Schema adequacy against representation schema 10

**Nothing here is irreducible prose.** `ProseBindingDraft` requires one of the six closed
reasons in `policy.IRREDUCIBILITY_REASONS` (`policy.py:86`) — `contextual_applicability`,
`subjective_judgment`, `open_ended_effect`, `gamemaster_latitude`,
`natural_language_exception`, `fiction_dependent_consequence`. Each substantive clause was
checked against all six and matches none. No clause delegates to the GM, none states an
unbounded effect space, none requires a judgement call, and none has a consequence that
follows from fiction: *"the distance in feet"*, *"a distance equal to your Speed or less"*,
*"subtract the distance already moved"*, *"by an equal amount for the same duration"* and
*"until it is used up"* are exact, printed, closed statements. `glossary/7/5`'s *"0 or
less"* is a printed threshold. Binding any of them as irreducible would be the defect #137
contract 3 names, so each is reported as a missing vocabulary instead.

**What schema 10 already has, and it is a great deal.** `Speed` is the most heavily
*consumed* vocabulary in the accepted corpus, and two schema shapes already cite **this very
population** as their evidence:

* `MovementMode` (`representation.py:600`) carries `WALK, BURROW, CLIMB, CRAWL, FLY, SWIM`,
  and `CRAWL`'s comment names its source outright: *"Playing the Game > Movement and
  Position prints the mode list — 'Your movement can include climbing, crawling, jumping,
  and swimming' — and Rules Glossary > Speed cross-references the same set."* That is
  `combat/3/0` and this entry.
* `MovementPermissionFact` (`:2912`) says the same: *"the mode list is printed at Playing the
  Game > Movement and Position."*
* `MovementAllowanceBasis.OWN_SPECIAL_SPEED` (`:1139`) already reads *"such as"* as
  non-exhaustive — *"The source names no single mode — 'such as' — so neither does this."*
* `SpeedModificationFact` (`:2748`), `CreatureSpeedFact` (`:2651`), `SpeedChange` (`:826`),
  `MovementCostFact` (`:2867`), `MovementCostKind`/`MovementAmount` (`:906`/`:915`),
  `MovementTransportFact`, `MovementInterleaveFact` (`:3237`) and
  `MovementAllowanceFact` (`:3218`) all exist.

The prior *uses* them: 5 `speed_modification`, 3 `movement_allowance`, 2 `movement_cost`, 1
`movement_permission`, 1 `movement_transport`, 1 `movement_interleave` — 13 accepted facts
about movement, walked out of the frozen prior by the run and emitted as
`prior_movement_facts` (`by_family` counts, and every row with its record key,
component key and fields). `area_origin_movement`, 1, matches the same family pattern
and is reported beside them rather than folded in: it is about an area's origin moving,
not a creature's. So the
question is not whether the schema knows about Speed. It is whether it can state what Speed
**is** and what a turn's movement budget **does**, which is a different claim from every one
of those thirteen.

| Gap | Witnesses | Existing shape | Represented distinction | Residue | Record ends / runtime begins |
|---|---|---|---|---|---|
| **G1** — what a Speed *is* | `glossary/1/1` (with `glossary/1/0`) | `CreatureSpeedFact(mode, feet)` states what a **stat block prints** — its docstring is literally *"``Speed 20 ft.``"*. Nothing states the definition: that a Speed is a distance, measured in feet, coverable when the creature moves on its turn | the unit, the quantity kind and the window, none of which a per-creature value carries | §4a — whether this is definitional framing (`A`, the `cover-1` reading of *"Cover provides a degree of protection"*) or a substantive definition is the first question for review | if substantive, the record states the definition; nothing computes |
| **G2** — the per-turn movement allowance | `combat/1/0`+`combat/2/0`, `combat/2/1` | `MovementAllowanceFact(basis)` exists with **three** accepted instances, and every one is a *grant from another rule*: `action.dash/dash_movement/standard_speed` (`own_speed`), `…/special_speed` (`own_special_speed`), `action.ready/ready_response/move_up_to_speed` (`own_speed`). Ready's wording — *"move up to your Speed"* — is nearly identical to `combat/2/0` | that the base allowance exists **unconditionally, every turn**, rather than being granted by taking an action or a reaction; that it is an **upper bound** (*"or less"*); and that declining entirely is explicitly permitted | §4c. Reusing `movement_allowance` for the base would state that the turn's movement is granted by a rule, which inverts the source: Dash and Ready *add to* this budget, they do not create it. `basis` names where a quantity comes from and carries no conditionality; `combat/2/1` has no carrier at all | the record states the allowance, its bound and the option to decline; deciding a route is runtime |
| **G3** — depletion | `combat/3/2` | **none.** `MovementCostFact`'s own docstring draws the line: *"it states the cost, never what the cost buys."* It is the debit; there is no shape for the pool, for subtracting each part of a move from it, or for the printed stopping condition *"until it is used up or until you are done moving, whichever comes first"* | that movement is a depleting budget with two termination conditions, whichever is earlier | none in the clause; the whole claim is unrepresentable today | the record states the depletion rule and both terminators; performing the subtraction is runtime computation, exactly the `cover-1` G4 boundary |
| **G4** — multi-speed selection and mid-move switching | `glossary/7/1`, `7/2`, `7/3`, `7/4`, `7/5` | `MovementInterleaveFact(between=REPEATED_ATTACKS)` is **precedent that a movement sequencing permission is typeable** — and, per `known_unknowns.md:356`, one member with one instance, *"the weakest closure evidence this document admits."* No shape reaches selection among a creature's own speeds, switching mid-move, the subtract-distance-already-moved cost, or the 0-or-less prohibition | that possessing several speeds is a *choice* resolved per move, revisable mid-move at a printed cost, with a printed floor that forbids rather than clamps | `glossary/7/5` is a **prohibition** (*"you can't use the new speed"*), not an arithmetic clamp to zero. A shape that only recorded the subtraction would lose it | the record states the selection permission, the switching permission, the cost rule and the prohibition; doing the arithmetic per move is runtime |
| **G5** — propagation of a Speed change to special speeds | `glossary/9/0` | `SpeedModificationFact(change, mode, feet, can_increase)` states **one** change to **one** mode, with `mode=None` when unqualified. Nothing propagates one change across a creature's other speeds | that a change to Speed is *by construction* a change to every special speed the creature has, by an equal amount and for the same duration | §4b. This is the clause that gives five already-accepted facts their real meaning | the record states the propagation rule; applying it to a creature's actual speed list is runtime |
| **G6** — *special speed* as a category, and the printed mode list | `glossary/5/0`+`6/0`+`7/0`, `combat/3/0`, `combat/3/1` | `MovementMode` has six members and `MovementAllowanceBasis.OWN_SPECIAL_SPEED` already treats the set as open. But **nothing partitions the enum**: no shape distinguishes `WALK` (the base Speed) from the four special speeds, which is precisely the set G5's rule ranges over. Separately, `JUMP` is absent from `MovementMode` while `CRAWL` is present, and both come from the same printed list at `combat/3/0` | that *special speed* is a named category with four printed members and an open boundary (*"such as"*), and that modes compose with the base move up to the whole of it (`combat/3/1`) | the four special-speed entries are adjudicated boundary (§6), so this batch would name the category without defining its members — an honest asymmetry, and the same one `cover-1` accepted in reverse when `CoverDegree` predated the entry that defines the degrees. `JUMP`'s absence is scoped to the enum member; Jumping's own rules are a separate entry and a separate batch | vocabulary only; nothing evaluates |

**None of the six is an Owner Decision.** Each is a closed, printed, enumerable distinction
with no product decision, no ownership move and no contradiction between authorities. Per
this invocation's governing instruction, missing vocabulary alone is ordinary declarative
schema work. ADR-005d Decision 4 and ADR-005c Decision 3 forbid *executable* mechanics;
every gap above is satisfied by named closed members a hand-authored adapter interprets, and
none of them evaluates anything. **Zero of the six is a genuine unresolved product or
ownership question.** Whether they require a schema 11 is not prejudged here: that is a
proposal-time judgment and §8 leaves it open.

### 4a. The definition sentence — two readings, neither prejudged

`cover-1` read *"Cover provides a degree of protection to a target behind it"* as `A`:
framing that states no threshold, benefit or condition of its own. The parallel reading here
makes `glossary/1/0`+`glossary/1/1` supporting authority and lets the *rules* carry the
mechanics.

The reading against it is that `glossary/1/1` carries more than framing. It states a **unit**
(feet), a **quantity kind** (distance), and a **window** (*"when it moves on its turn"*) —
and the window is the thing `combat/1/0` then builds the allowance on. `CreatureSpeedFact`
already assumes all three without any accepted span stating them: its `feet: int` field is
meaningful only because *this clause* says the unit is feet. A schema whose only Speed
carrier is a stat-block value has no span anywhere claiming what the value means.

Both readings are recorded; the checkpoint does not choose. If `A` is right, G1 disappears
and the gap surface is five. If `S` is right, G1 needs a carrier and there is none.

### 4b. What `glossary/9/0` does to five already-accepted facts

Accepted authority holds five `speed_modification` facts — `condition.grappled`,
`condition.paralyzed`, `condition.petrified`, `condition.restrained`,
`condition.unconscious`, each `{change: set_to, feet: 0, mode: null, can_increase: false}` —
walked out of the frozen prior and asserted field-for-field by the run, in
`prior_movement_facts.rows`. Each condition's own page prints *"Your Speed is 0
and can't increase"* and nothing more. **The rule that makes those five reach a creature's
Climb Speed is printed here, at `glossary/9/0`, and nowhere on any of those five pages.**

This is stated deliberately as *"the prior stated what its pages print"* and **not** as a
hole in the prior. `mode: null` is the faithful record of an unqualified statement; it is
not a claim about special speeds either way. What is new is that the entry which *does*
state the propagation is now in front of review, and a batch that typed it would make five
accepted facts mean something they do not currently say on their own. That is authority
composing correctly, which is what the reference graph is for — but it is worth naming
explicitly, because it is the first time in this build that a new record's rule would change
the reach of accepted facts in other records.

### 4c. `MovementAllowanceFact` — reuse is available, and the question is fidelity

The family exists and its `OWN_SPEED` basis is already accepted on two records. Ready's
*"move up to your Speed"* and `combat/1/0`+`combat/2/0`'s *"move a distance equal to your
Speed or less"* are close to the same sentence. So reuse is not blocked by any validator,
and the checkpoint does not claim it is.

What it claims is that reuse would state something the source does not. The three accepted
instances are all **granted** allowances — Dash's *"you gain extra movement for the current
turn"* and Ready's reaction-conditioned move. `MovementAllowanceBasis`'s docstring describes
exactly that: *"Never a number… states a quantity no integer can carry."* It names where a
quantity comes from. It does not carry, and has no field for:

* **unconditionality** — the base allowance is not granted by anything; it is what a turn
  *is*. Dash's increase is measured *against* it;
* **boundedness** — *"or less"* makes the value a ceiling. Ready's *"up to"* is the same
  shape, so this one distinction may already be implicit in the family; `combat/2/1`'s
  *"Or you can decide not to move"* is not;
* **the pool** — G3. An allowance that nothing depletes is not the rule the source prints.

Whether that distinction should live in the fact (a new basis member, or a new field), in
the component's structure, or in a new family is a proposal-time choice this checkpoint does
not make. It records that the distinction is real and printed, and that a bare
`MovementAllowanceFact(OWN_SPEED)` on `combat/2/0` would publish the base allowance as a
grant.

---

## 5. References — enumerated, none closed

No validator was run; nothing below is a validator result.

**(a) Inbound — one, and it is the reason this batch exists.** The frozen prior contains
exactly one citation of `Speed`, derived from the prior rather than transcribed:

| From | Component | Scope | Source text | Target | Defined in prior |
|---|---|---|---|---|---|
| `action.dash` | `""` | `srd-5.2.1/rules-glossary` | `Speed` | `glossary.speed` | **no** |

**(b) Outbound — five candidates, and the rule that produces them was found, not invented.**
`actions-1` cut its `See also` citation leaf **per cited term** and emitted one
`ReferenceDraft(from_record_key, from_component_key, source_text, scope_key,
target_record_key)` for each term naming a glossary **entry**. `glossary/3/0`–`3/4` are that
shape exactly: five quoted terms, each with a glossary entry of that label existing in the
bound release — `Climbing`, `Crawling`, `Flying`, `Jumping`, `Swimming`. The run reports the
per-term cut and, for each, whether an entry with that label exists; it emits no reference
and no target key.

**The residue arithmetic, reported as a consequence and not as a goal.** Defining
`glossary.speed` closes the one inbound target. Five outbound references would name five
targets no accepted record defines. If both happen, the unresolved residue moves from
`{glossary.concentration, glossary.speed}` — two — to six. **The residue direction moves
up.** That is what following the established rule produces, and it is reported rather than
avoided; `known_unknowns.md:504-505` already records that the residue has moved in both
directions across batches and that residue movement is a consequence of accepting complete
source classes, not a reason for choosing one.

**(c) Citations naming a chapter emit nothing — `cover-1`'s precedent, twice more.**
`glossary/3/5` names `“Playing the Game” (“Combat”)`; `combat/3/0`'s parenthetical and
`combat/3/5` both name `“Rules Glossary”`. Every one of the prior's 53 references targets a
record key and there is no record for a chapter, so all three are record-owned supporting
authority. `combat/3/5` is additionally *self-directed* — it points at the population's own
other site — which is the same reason `cover-1` gave for emitting zero.

**(d) The open question: an explicit pointer inside substantive prose.**
`glossary/5/0`+`6/0`+`7/0` names four capitalized entry labels — `Burrow Speed`, `Climb
Speed`, `Fly Speed`, `Swim Speed` — and then says *"each of which is defined in this
glossary."* All four entries exist. That pointer is **stronger than Dash's bare *"such
as"***, and the Dash precedent is the one being leaned on: Dash's own body says *"such as a
Fly Speed or Swim Speed"*, it was dispositioned into `dash_movement` as substantive prose,
and it emitted **no** reference. The checkpoint's reading follows Dash — a `See also`
citation leaf emits references, substantive prose stating a rule does not, however explicit
its pointer — because the alternative makes reference emission depend on how helpfully a
rule sentence is worded. But the difference from `glossary/3` is a wording difference, not a
structural one, and §8 puts it to review rather than burying it. `combat/3/5`'s *"such as a
Climb Speed, Fly Speed, or Swim Speed"* is Dash-identical and needs no argument.

**(e) Inbound-in-waiting, recorded as a manifest fact.** Five glossary entries print
`“Speed.”` as their own `See also` citation — `Burrow Speed`, `Climb Speed`, `Fly Speed`,
`Swim Speed` and `Crawling`. None is in this population and none emits anything here; when
their batch comes, each would cite `glossary.speed`. Noted so that "this batch closes one
target" is not read as "one record ever cites it."

**(f) The scope convention, measured.** All 53 accepted references carry
`scope_key = "srd-5.2.1/rules-glossary"` — counted, not remembered. The five candidates in
(b) come from the glossary site's own `See also` leaf, so they are glossary-scoped too and
**no second scope arises for `speed-1`.** Whether a future batch citing from a non-glossary
chapter needs one is left open and untouched.

**(g) The substring scan is not a citation list.** The manifest reports nine glossary entry
labels occurring anywhere in the population's text with the clause ids where they occur —
`Burrow Speed` (`glossary/5/0`), `Climb Speed` (`glossary/5/0`, `9/1`, `combat/3/5`),
`Climbing` (`glossary/3/0`), `Crawling` (`glossary/3/1`), `Fly Speed` (`glossary/7/6`,
`10/0`, `combat/3/5`), `Flying` (`glossary/3/2`), `Jumping` (`glossary/3/3`), `Swim Speed`
(`glossary/6/0`, `combat/3/5`), `Swimming` (`glossary/3/4`). Most of those occurrences are
worked examples and running prose. The manifest labels the field
`glossary_entry_labels_occurring_in_population_text` and says so; the same rule that governs
the boundary governs here.

---

## 6. Boundaries, stated from the text that states them

**The rule, once:** a leaf is in the population when the bound release attaches it to one of
the two entries §2 derives. Printing the word is *use*, not definition. **557** leaves
outside the population print `speed` in some case; all 557 are enumerated in the manifest
with their container, section, 5c representation state, whether they print the capitalized
term, and any accepted record that already owns that container. `already_accepted_as` is
**derived** from the frozen prior — accepted span → leaf → owning container → provenance
target key — not transcribed. Every boundary leaf is represented by 5c
(`boundary_all_represented_by_5c: true`).

| Section | Leaves |
|---|---|
| Monsters A–Z | 288 |
| Animals | 101 |
| Rules Glossary | 45 |
| Magic Items | 33 |
| Spells | 25 |
| Classes | 19 |
| Character Origins | 15 |
| Playing the Game | 11 |
| Gameplay Toolbox | 9 |
| Equipment | 7 |
| Monsters | 3 |
| Creation | 1 |

**545 print the capitalized term; 12 are lowercase-only.** Unlike `cover-1` — where three of
thirty hits matched only the longer word *"Covering"* — **every one of the 557 contains a
standalone `speed`/`speeds` token**. Each boundary row carries `prints_standalone_token`,
the run asserts it row by row, and the total is emitted as
`boundary_standalone_token_leaf_count` (557). No substring artifact exists in this scan.

**Twenty-two boundary leaves are already owned by accepted authority**, derived from the
prior: `Dash [Action]` 6, `Exhaustion` 2, `Grappled` 2, `Paralyzed` 2, `Petrified` 2,
`Prone` 2, `Restrained` 2, `Unconscious` 2, `Dodge [Action]` 1, `Ready [Action]` 1. These are
the consumers §4 measures against — the rule they consume is the one this batch would define.

**The `Playing the Game` eleven, named individually**, because they are the nearest
neighbours and the ones a reviewer will test the membership rule against:

* **`Combat > Your Turn` (p12–13, 42 leaves)** — restates the allowance: *"On your turn, you
  can move a distance up to your Speed and take one action."* Out, by the same structural
  test and for a stated reason: it owns its own entry, and what it states is the **turn's
  action economy** — move *and* act — not what Speed is or how the budget depletes. It then
  defers the movement rules to `Movement and Position` by name (§2), which is corroboration
  for membership rather than a claim on it. This is the strongest exclusion in the set and
  the run records the deferral as a derived, release-unique fact.
* **`Combat > Breaking Up Your Move` (p13)** — *"using some of its movement before and after
  any action"*. A rule about how the budget is **distributed across the turn**. It presumes
  the budget; it does not state it. Own entry, own rule, out.
* **`Combat > Difficult Terrain` (p13)** — a per-foot surcharge against the budget. Its
  glossary twin is already-typed vocabulary territory (`MovementCostKind.PER_FOOT_SURCHARGE`).
* **`Combat > Dropping Prone`, `Combat > Mounting and Dismounting` (p13–15)** — both *spend*
  Speed (*"without using … any of your Speed"*; *"an amount of movement equal to half your
  Speed (round down)"*). `MovementCostFact`'s docstring already names Mounting and
  Dismounting's wording as identical to Prone's, so this is known consumer territory.
* **`Actions > Action | Summary` (p8–9, two table cells)** — the action table's Dash and
  Dodge summaries. Already-accepted records (`action.dash`, `action.dodge`) own the entries
  those cells summarize.
* **`Exploration > Vehicles` (p11–12, three leaves)** — prints the **grid translation**:
  *"using your Speed in 5-foot segments… dividing it by 5"*, plus square-entry costs and the
  corner rule. Runtime geometry and an optional presentation convention; explicitly outside
  5d, and not a statement of what Speed is.
* **`Combat > Impeded Weapons` (p15)** — consumes `Swim Speed` as a precondition on an
  attack roll. Attack adjudication, out.

**The adjudicated boundary — 21 containers whose exclusion a reader would question.** The
manifest carries a second, named table with every leaf's full text and facts only: path,
container id and type, leaf count, printed pages, policy-excluded leaves, whether the
population's citation leaf names it, whether it prints the reciprocal citation sentence,
whether it names the capitalized term, whether it cites `“Speed.”` back, whether it defers
the movement rules to the population, and `already_accepted_as`. The run asserts that **none
of the 21 prints the membership citation**, and `already_accepted_as` is **empty for all
21** — no accepted record owns any of them.

| Group | Containers |
|---|---|
| the three other `Speed` labels | `Character Origins > Character Species > Speed`; `Equipment > Mounts and Vehicles > Speed`; `Monsters > Parts of a Stat Block > Speed` |
| the four special-speed entries the population names | `Burrow Speed`, `Climb Speed`, `Fly Speed`, `Swim Speed` — each cites `“Speed.”` back |
| the five entries the `See also` citation names | `Climbing`, `Crawling`, `Flying`, `Jumping`, `Swimming` — `Crawling` is the only one of the five that also cites `“Speed.”` back |
| the seven `Combat` siblings | `Your Turn`, `Difficult Terrain`, `Breaking Up Your Move`, `Dropping Prone`, `Moving around Other Creatures`, `Creature Size`, `Mounting and Dismounting` |
| the two sites that convert Speed to a travel rate | `Playing the Game > Exploration > Travel Pace`; `Gameplay Toolbox > Travel Pace > Special Movement` |

Four leaves inside those containers are policy-excluded by 5c and are listed rather than
asserted away: `3a7db508…` (`Equipment > Mounts and Vehicles > Speed`), `2f55c45c…`
(`Swim Speed`), `9980e82a…` (`Climbing`), `c97a4856…` (`Mounting and Dismounting`), plus
`3ca8b0f3…` (a `header_footer` in `Your Turn`).

**Other boundaries:**

* **No Known Unknown is created, narrowed or leaned on.** `known_unknowns.md` records
  movement residue in three places and this checkpoint touches none of it: *"movement
  options and per-foot movement cost"* (`:296`, conditions-1 residue), *"Ratio-form movement
  costs"* (`:332`, Gust of Wind / Plant Growth / Wall of Thorns), *"Applicability over a
  capability predicate"* (`:339`, Swimming's and Climbing's *"if you have a Swim Speed and
  use it to swim"*) and the sequencing deferral (`:356`). The capability-predicate item
  concerns `Swimming` and `Climbing`, which are **adjudicated boundary** here — it is cited
  in §4's G4 row as evidence about `MovementInterleaveFact`'s closure strength and is
  neither resolved nor narrowed. `:499-500` records `glossary.speed` as an unresolved target
  and its sequencing as ordinary engineering. No edit to that document is proposed.
* **Runtime movement stays outside.** No movement engine, no pathfinding, no grid or square
  arithmetic, no route selection, no per-move subtraction. §4 names the crossing for each
  gap. ADR-005d Decision 11 leaves adapter capability and execution to 15c.
* **Character state stays outside.** Nothing mutates a character's Speed, and `combat/3/3`'s
  *"determined during character creation"* is read as sourcing (§3), not as a hook into
  character creation.
* **The special speeds, travel pace and Jumping are adjacent batches, not this one.**
  Naming them in §6 is enumeration, not sequencing.
* **No source re-extraction.** The run reads the committed PDF through the existing 5c
  pipeline and asserts five of the six binding values; it changes no extraction, no
  retrieval config and no corpus artifact. The extraction properties in §2 are reported
  verbatim, with the frozen table inventory as an independent witness that the
  no-table-in-population claim is a property of the bound release rather than an assumption.

---

## 7. Checks that were actually run

| Check | Result |
|---|---|
| `pytest -q --no-cov tests/ingestion/mechanical/test_speed_1_frozen_prior.py` (8 tests) | 8 passed in 0.84s |
| Five release-binding values re-derived from the committed PDF and asserted | pass; the sixth disclosed, §1 |
| The four containers labeled `Speed` asserted as an exact set of paths | pass |
| *See “Rules Glossary” for more about Speed* asserted to occur in exactly one leaf release-wide, and that leaf's entry asserted to be `Movement and Position` | pass |
| The glossary `See also` citation asserted to name the Combat entry's own section and subsection labels | pass |
| The naive co-occurrence alternative computed and disclosed | 3 entries, not 1 |
| `Your Turn`'s deferral sentence asserted unique release-wide and asserted to belong to a non-member container | pass |
| Every cut located in bound content, asserted unique within its leaf | pass, 36 clauses |
| Partition reconstructs each leaf byte for byte | pass, 16 leaves |
| Three cross-leaf sentences reconstructed and asserted (no non-final part ends in `.`, final part does, distinct leaves) | pass |
| Policy exclusions inside the population | 0, listed rather than asserted away |
| Every member leaf asserted attached directly to its entry; committed table inventory filtered to the population's printed pages and asserted to name no member-owned table | pass |
| No member leaf is already represented by the accepted prior | pass |
| Every boundary leaf represented by 5c; every boundary row carries `prints_standalone_token` and is asserted true | pass, 557 rows, `boundary_standalone_token_leaf_count` 557, 0 substring artifacts |
| The prior's own movement and speed facts walked out of the frozen prior over components and their options | pass, 14 matching facts, 13 about a creature's own movement; the five `speed_modification` rows asserted field-for-field |
| Accepted-record ownership of boundary containers derived from the prior's spans and provenance | pass; every derived key asserted present in the prior |
| No adjudicated-boundary container prints the membership citation | pass, 21 containers |
| Frozen prior digest, blob and `oracle_identity` before and after the run | unmoved |
| Live accepted artifact read as a mutation sentinel, never as an input | unmoved |
| Every other file in `.claude/review-notes/` digested before and after | unmoved |
| `black --check` and `ruff check` on the discovery script | clean |
| Manifest reproducibility | rerun byte-identical, sha256 `8c8ea8eed38feaeb28d74386690b5ee28e43872b1316517b922fb89afa016b20` |
| Manifest reproduced from a clean `git archive` export of this checkpoint's own tree, run outside the working tree | byte-identical (`cmp`). The export is hermetic: the script's own `assert PACKAGE_ROOT.resolve() == IMPORTED_FROM` holds there, so the exported `src/` is what ran. No untracked file in `.claude/review-notes/` is an input |

Not run, and not implied: the publication gate (there is no persisted projection to run it
over), the semantic validator (there is no draft), any acceptance script, any lift, any
schema mint, any operational-database read. No full repository gate suite was run for this
checkpoint and none is claimed; `.claude/review-notes/` is outside the `black src/ tests/`
and `ruff check src/ tests/` paths, and the two files this branch added under `tests/` were
gated by the freeze commit (`496201a`: black, ruff, 8 tests, detect-secrets exit 0).

---

## 8. Where this stops

Delivered: the six-batch frozen prior and its contract test (commit `496201a`); the
reproducible discovery run and its manifest; this checkpoint. Not done, and not to be done
before Codex reviews: any schema change, any proposal, any draft, acceptance, push, merge,
publication, activation, retirement or parent-issue state change. Parent tracking issue #137
remains in progress. Whether a schema 11 is needed is deliberately left open.

**The four questions this checkpoint puts to review:**

1. **§2 — is `Movement and Position` a member, or boundary?** The checkpoint calls it a
   member on the source's own reciprocal citation, asserted unique release-wide, and on the
   substantive test that it states two rules the glossary does not (`combat/2/1`,
   `combat/3/2`). `Your Turn`'s deferral corroborates. The alternative — a glossary-only
   population of 12 leaves — would move G2 and G3 out of this batch entirely and leave the
   base movement allowance unstated by any batch. If Codex reads the citation as navigation
   rather than as joint authorship, that is the largest single change to this checkpoint.
2. **§5b/§5d — do five references get emitted, and does the explicit pointer at
   `glossary/5/0`–`7/0` emit a sixth through ninth?** The checkpoint follows the `actions-1`
   rule for the `See also` leaf (five) and the Dash precedent for substantive prose (none),
   which makes the residue move **up**, from two to six. Both halves are the found rule
   rather than a chosen one, but the second half distinguishes *"each of which is defined in
   this glossary"* from a `See also` on structural grounds alone, and that is worth pushing
   on.
3. **§4c — can `MovementAllowanceFact` carry the base per-turn allowance faithfully?** The
   family exists, `OWN_SPEED` is accepted twice, and Ready's wording is nearly identical. The
   checkpoint says reuse would publish the base allowance as a *grant* and has no carrier for
   `combat/2/1`. This is where a reviewer should push hardest, because the lazy answer —
   reuse the family — is also the one that quietly changes what the source says.
4. **§4a and §4 generally — do the gaps read as ordinary closed declarative schema work?**
   G1 is the one that could vanish entirely under the `cover-1` framing reading. G3
   (depletion) has no existing shape of any kind and is the widest surface. G6 asks whether
   *special speed* can be a named category while its four members stay in later batches.
