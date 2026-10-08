# CRD Issue 5d — Classes — review packet (UNACCEPTED, consolidated correction)

Status: **proposals and one draft for independent coordinating Codex review, then Owner semantic review.
Nothing is accepted, recorded, committed, pushed or published.**

- The accepted oracle is byte-unchanged (`962d6aee…18b8`). Nothing under `oracles/` changed.
- Composition is in memory only. There are no shared-DB or Chroma writes.
- This revision corrects the unaccepted packet on four consolidated findings: *Defensive Tactics*,
  entry headings, reference destinations and progression (B6). It is not a new product decision and not
  an accepted-material audit.

Release `0b1a965e-28bd-55e6-ac13-bc7786a1bace` / `5.2.1-corpus.626c83f8-209`. Official PDF
`docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf`, pp. 28–82.

## Artifacts

| File | SHA-256 | Notes |
|---|---|---|
| `issue-5d-classes-PROPOSAL.json` | `08c8c91d65e69ba909cc5771aa26352e60d2019363790c21394ee1ddf4002ba7` | 2,889,857 bytes; identity `025016704fbca10a7673e0040309a772d56780da434013588cd34fcafd4ffc87` |
| `issue-5d-class-option-catalogues-PROPOSAL.json` | `7172ae1ab2986a5617722f69dcf0781ddcb0286a86b663f75118e504f913cf82` | 275,726 bytes; identity `3dae09105c4f2e30f0c1c902fef76155974f61320f8283904c2ef241072a3293` |
| `issue-5d-classes-resolutions-DRAFTS.json` | `516e141fd5c66a1146d09fbf4f0c8e8e70859c36e15b42b1c8000ecabcebf63c` | 1 draft resolution, unrecorded; unchanged |
| `issue-5d-classes-generator.py` | `169ca6c4fb7d7a00778d49cbb91adeb33728a8faf88b3f928cf9ea160e673465` | derives all three from the published release |
| `issue-5d-classes-source.py` | `54949f92c563514d7d2bfb86fe1b9607c90a7d3a344fcef6e17cd517294e7cc0` | the 1174 qualified leaf texts; unchanged |
| `tests/ingestion/mechanical/test_classes_proposal.py` | `f9eded1dfa2039471305036c5a546a09801fc6d2e753430fbfcb4a83d82328dd` | 26 tests |
| `src/afterworlds/ingestion/mechanical/authoring.py` | `9f45f5523070585c5de32a09b4fc50910124f148375e3e20c8afdf02418da525` | helper extension, see *Helper change* |

All files are LF with 0 CR. Both proposals re-derive byte-for-byte from the scratch release DB
(`.claude/_rc/newrel/afterworlds.db`), and the test checks this. The generator was re-run after Black
reformatted it: identities, file bytes and the full emit log are unchanged (`gen5.log` = `gen6.log`).

## Scope and source qualification

Unchanged from the previous revision. **Scope is 1174 of the part's 1175 leaves.** The one leaf left out
is the part title `# Classes`, which states no rule.

Every leaf was qualified against the official PDF text (`.claude/_sp/cls/qual.py`, `qual.json`):

| | Checked | Passed |
|---|---|---|
| Prose leaves | 1070 | 1065 |
| Table rows (105 tables) | 1346 | 1339 |

The 12 residues, adjudicated:
- **7 table header rows** carry `——Spell Slots per Spell Level——`. This is the PDF's two-row header with
  a spanning group label (`colspan` 9 for Bard, Cleric, Druid, Sorcerer and Wizard; 5 for Paladin and
  Ranger). It is an extraction artifact with no semantic effect.
- **4 prose leaves** are split in the PDF text by an interleaved feature table. The text matches, so these
  are extraction artifacts too.
- **Leaf 557** is a genuine release-structure finding. It is authored per the PDF by sub-leaf spans (see
  the *Channel Divinity* item under *Retained findings*).

The independent source review in the governing instruction (all 1174 leaves and 105 tables parsed,
exception pages render-checked) found no text or table loss beyond these. That is not a claim that the
source is correct everywhere.

## Corrections in this revision

### 1. *Defensive Tactics* — fixed (was B3)

The PDF and the controlled source print `#### Level 7: Defensive Tactics` under *Hunter*.

**Now:** one record, `classes.ranger.hunter.defensive_tactics`.
- It is a `CATALOGUE_MEMBER` of *Hunter*, not *Ranger*.
- It reads its own heading first (`#### Level 7: Defensive Tactics`), then "You gain one of the following
  feature options…", then its options.
- It is not a separate review unit. It is read inside the Hunter unit that prints it, which drops the unit
  count from 37 to 36.

**Consumer reads (tested):**
- A Hunter read returns the five level headings in printed order: 3, 3, 7, 11, 15.
- A Hunter read contains exactly *Defensive Tactics*' own read.
- Selecting Hunter together with *Defensive Tactics* equals the Hunter read.
- A Ranger read does not reach *Defensive Tactics*. This is the settled one-hop reach: selecting Hunter
  reaches it.

**How.** `EntryBatch.record_containers` lets a declared record locate its texts in its own release
container, rather than in the whole entry. This is how *Defensive Tactics* reads the leaf it prints, the
same leaf *Hunter's Prey* prints, without a second entry.
- Existing checks are kept: membership is still one-hop, declared and checked against containment.
- Ambiguous or multiple membership is still refused.
- `locate_span` still requires exactly one occurrence within the container.
- No `parent_key` use was introduced, and no recursive reach.

### 2. Entry headings — fixed (was B3a)

Previously the helper excluded all 77 entry-placement headings. The 77 are the 37 classes-chunk headings
plus the 40 options-chunk headings. Each was classified by what a consumer needs to read:

| Heading family | Count | Consumer meaning | Now |
|---|---|---|---|
| Class name (`## Barbarian`) | 12 | identity | read first by the class record |
| Subclass (`### Ranger Subclass: Hunter`) | 12 | identity and parent class | read first by the subclass record |
| Multiclass (`#### As a Multiclass Character`) | 12 | category | read first by its record |
| *Defensive Tactics* (`#### Level 7: …`) | 1 | level and identity | read first by its record |
| Catalogue and option names (Metamagic, Eldritch Invocations, each option) | 40 | identity | read first by each record |

- A heading the review reads is authority of that record. It is no longer an excluded group, so nothing
  is both read and excluded.
- The only remaining exclusions are the 12 subclass mottos. They are italic lines that name a theme and
  state no rule.
- No heading duplicates governing prose. Each heading is read once, by the record it names.
- **Combined reads:**
  - a class read reads each subclass heading once, whether or not the subclass is selected;
  - a disabled subclass is not read back by its class, nor is its heading;
  - a catalogue reads each option heading once.

**Helper detail.** `authoring.locate` now takes a text that is exactly one whole leaf as that leaf. This is
needed because a longer heading can print it too: `## Barbarian` also occurs inside
`### Barbarian Class Features`. Previously-passing locations are unchanged, because a unique occurrence is
necessarily that same leaf.

### 3. Reference destinations — fixed (was B8)

**The defect.** `CORE_TRAITS` widened named items to broad sections:
- Greataxe, Chain Mail, the packs, Spellbook and others went to `equipment.weapons`, `equipment.armor` or
  `equipment.adventuring_gear`;
- the literal "Equipment" went to `equipment.tools`.

**Now: an exact existing record, or unresolved; never widened.** This follows the *Component Pouch*
precedent.
- 44 equipment references are unresolved:
  - 42 are named items with no record of their own;
  - 2 are the printed "(see Equipment)" part pointers (Bard, Monk).
- Bard's "(see Playing the Game)" is unresolved too.
- Items with records keep them, for example `equipment.weapons.quarterstaff`,
  `equipment.tools.thieves_tools` and `equipment.armor.shield`.
- Weapon and armor categories keep `equipment.weapons.category` and `equipment.armor.category`.

**Matcher-family audit.**
- The row label "Starting Equipment" is not a citation, so its 10 references were removed.
- Printed citations were checked against substrings of labels. Term matches inside a label's markup were
  found. Only one produced a wrong target: "Temporary Hit Points" → `hit_points`, in Druid *Wild Shape* and
  Ranger *Tireless*. It is now matched on the label's plain text, so both spurious references are gone.
- The printed label "Cantrips" now keeps its printed capitalisation. The target is unchanged.
- The existing ambiguous multi-class, feature and part references stay unresolved.
- Accepted *Equipment* is not rewritten, and no equipment records were added.

### 4. Progression (was B6) — supplied as existing typed facts

Decision 4, and Issue #137's publication requirement and Canary 5 (*"Progression table: level-indexed
entitlements and feature references reconstruct correctly"*), identify a v1 structured use of class
progression. The existing contract already has `ProgressionEntryFact` and `SpellSlotProgressionFact`.

**What each class now has:** a `progression` component with MIXED handling. It holds the facts, and it
binds the exact table prose with one reason, `no_identified_structured_use`. 12 components, 1432 facts:

| Fact | Count | From |
|---|---|---|
| `ProgressionEntryFact(level, <feature record key>, quantity?)` | 752 in total with the count rows below | each *Class Features* cell. `(one use)` / `(two uses)` / `(three uses)` become `quantity`. |
| `ProgressionEntryFact(level, "subclass_feature")` | (included) | "Subclass feature" cells. The subclass's own records carry their levels. |
| `ProgressionEntryFact(level, <column>, n)` | (included) | count columns: Rages, Weapon Mastery, Channel Divinity, Wild Shape, Cantrips, Prepared Spells, Second Wind, Focus Points, Favored Enemy, Sorcery Points, Eldritch Invocations |
| `SpellSlotProgressionFact(character_level, slot_level, slots)` | 680 | the slot grids. Warlock's *Spell Slots* uses its *Slot Level* column for `slot_level`. |

**First use.** No earlier proposal or the accepted oracle uses either fact family. The keys are:
- a feature's record key;
- a count column's slug (`rages`, `weapon_mastery`, …);
- `subclass_feature`.

The `ProgressionEntryFact` docstring permits a semantic key. None of these keys encodes a second
dimension.

**Proof.** A test reconstructs every table's level and feature and count cells, and every slot grid, from
the facts alone.

**Retained as prose, with evidence.** Only `no_identified_structured_use` applies, and no new semantics were
invented:
- **Proficiency Bonus.** A single authority already exists in the accepted `play.proficiency` bands. A
  second copy would duplicate canon.
- **Bardic Die, Martial Arts, Sneak Attack.** These are dice expressions, not a quantity. There is no
  existing progression field for dice.
- **Rage Damage.** A damage bonus, not an entitlement count.
- **Unarmored Movement.** A distance, not a count.
- **The Mystic Arcanum spell level** (`(level N spell)`) is a second dimension. `entitlement_key` must not
  smuggle it. The key is the feature record `classes.warlock.mystic_arcanum`, and the spell level stays
  in prose.

## What the proposals author

**Chunk `classes`**

| | Count |
|---|---|
| Leaves | 1039 |
| Spans | 1028 |
| Review units | 36 |
| Records | 268: 12 `class`, 12 `character_advancement`, 244 `class_feature` |
| Components | 512 (12 MIXED `progression`; the rest prose-bound) |
| Facts | 1432 (752 `ProgressionEntryFact`, 680 `SpellSlotProgressionFact`) |
| Relationships | 256 `CATALOGUE_MEMBER` |
| References | 1683 |

**Chunk `class-option-catalogues`**

| | Count |
|---|---|
| Leaves | 135 |
| Spans | 135 |
| Review units | 40 |
| Records | 40: 2 catalogues and 38 options |
| Components | 51 |
| Relationships | 38 |
| References | 85 |

**Emit checks:** 0 partition findings and 0 review-unit findings in both chunks. The representation
findings (1653 and 79) equal the expected list: the unresolved references and the known cross-chunk
targets.

**Grain.** Unchanged except for the corrections above.
- **Class.** One `class` record. It reads its name, the core traits, *Becoming a … / As a Level 1
  Character*, the *Class Features* intro, `progression`, and the spell-list tables.
- **Class feature.** Each `#### Level N: Name` is a `class_feature` record and a member of its class, read
  under its own heading.
- **Subclass.** One `class_feature` record per subclass, with its own features as members.
- **Multiclass.** A `character_advancement` member of the class.
- **Options.** Each option is a member of its catalogue. Cost and prerequisite leaves are read first.

## References

**Resolved**

| Target | Classes | Options |
|---|---|---|
| Rules Glossary | 461 | 54 |
| Equipment (exact records only) | 73 | — |
| Feats | 41 | 2 |
| Character Creation | 10 | — |
| Classes (in-batch) | 33 | 6 |

**Kept unresolved: 1088** (classes 1065, options 23)

| Scope | Classes | Options | Why |
|---|---|---|---|
| Spells | 1012 | 14 | no SPELL records yet (the external Spells catalogue) |
| Equipment | 44 | — | a named item with no record of its own, or a part pointer; never widened |
| Monsters | 1 | 8 | external catalogue |
| Animals | 5 | — | external catalogue |
| Classes | 2 | 1 | several classes in one phrase |
| Playing the Game | 1 | — | part pointer |

Previous revision: 1043 unresolved. The difference is +44 equipment and +1 Playing the Game.

**Accepted references now in reach.** Unchanged: the Elf "Wizard spell list" draft → `classes.wizard`, and
the other 15 accepted Classes references stay unresolved (multi-class lists, "Fighting Style Feature",
"Spellcasting Feature", six part pointers).

## Consumer evidence

These are actual reads through the native rules-authority service over one draft holding both chunks,
persisted into a private copy of the release DB. The tests are in `test_classes_proposal.py`.

- **Direct reads start with the record's own heading:**
  - a class read starts `## Barbarian`, then `**Core Barbarian Traits**`;
  - features read in printed order, with their level headings;
  - the multiclass read starts `#### As a Multiclass Character` and reads its own bullets, not level 1's.
- **Subclass and *Defensive Tactics*:** see Correction 1.
- **Catalogue:** each option read starts with its heading, then the cost or prerequisite.
- **Section and combined reads:**
  - the same order whatever the selector order;
  - narrowing keeps printed order;
  - nothing is read twice (no row repeats in a combined read);
  - a disabled record and its heading stay gone (no resurrection);
  - a replaced component reads, replaced, in its place.
- **Progression:** reconstructs from facts; MIXED is admitted by the native seam.

**Printed order** means the release's normalised order. The PDF floats some progression tables after the
first feature heading (Ranger, Monk, Rogue, Sorcerer, Warlock). The release keeps each table with its
*Class Features* intro. Governing association, relative rule order and meaning are unchanged, so this is
not a defect, and the release is not reordered for page layout.

**Composition, in memory:**
- `accept_proposal` is chained over the committed oracle. The prior state is exactly 15 batches, 295
  records and 50 resolutions. The composed total is 295 + 268 + 40 records, and the resolutions equal the
  prior 50.
- The oracle files on disk are byte-identical before and after, and the oracle SHA is pinned.
- `validate_candidate` over the oracle, both chunks and the draft reports that in-batch targets close,
  1174 leaves gain coverage, and there are 0 resolution violations.
- A dropped feature component is reported.

## Retained findings and settled items (B labels reclassified)

| Label | Now |
|---|---|
| B1 — no SPELL records | **Retained finding.** 1026 spell references are unresolved until the external Spells catalogue exists. |
| B2 — class → catalogue by reference | **Settled** packaging. The options repeat whole leaves, so they form a second chunk, and membership follows printed containment. |
| B3 — *Defensive Tactics* | **Fixed** (Correction 1). |
| B3a — placement headings | **Fixed** (Correction 2). |
| B4 — no subclass `RecordKind` | **Settled.** `class_feature` under existing semantics. |
| B5 — one-hop reach | **Settled** accepted semantics. |
| B6 — progression | **Supplied** as existing typed facts. The retained columns have evidence (Correction 4). |
| B7 — leaf 557 | **Settled in authoring.** Channel Divinity's DC sentence is its own sub-leaf span, read last in `channel_divinity`, and meaning is preserved. **The release-marker defect remains recorded separately**: the sentence sits inside the sidebar blockquote, which belongs to the source-correction track. |
| B8 — starting equipment | **Fixed** (Correction 3). Absent item records are retained findings. |
| B9 / B10 — ambiguous references | **Retained findings.** 15 accepted Classes references plus 3 class-list phrases, one reference, several targets. |
| B11 — chunking | **Settled** packaging. |
| B12 — per-component expected findings | **Settled.** The generator computes them per component. |
| Floated tables | **Not a defect** (see *Printed order*). |

Absent Spell, Monster, Animal and Equipment item records are retained unresolved findings, not decided
here.

## Helper change (`authoring.py`)

`authoring.py` already carried uncommitted modifications before this run. The before-copy is
`.claude/_sp/cls/authoring-before.py` (`8a11adee…4a89`). This run's delta, taken against that copy, is
**60 insertions and 10 deletions**, in `.claude/_sp/cls/authoring-mine.diff`:
- `EntryBatch.record_containers`, with a check for stray containers;
- `locate(..., record=)`, restricted to that record's container;
- the whole-leaf rule;
- contained-record components are located as SUBSTANTIVE, and it is an error if they read nothing;
- `at()`, so a contained record's spans are keyed by that record, in the unreviewed check, the spans,
  ownership and the expected rules;
- a heading a record reads is no longer an excluded group.

Existing batches do not use `record_containers`, and all 19 test files that import the helper pass. mypy
is clean.

**Qualification limit.** No test exercises the two new error branches: a stray container, and a
contained record that reads nothing. Only the success paths are covered, through Classes.

## Gates

Gate commands ran through `rtk proxy venv\Scripts\python.exe …`, with pytest `-p no:cacheprovider --no-cov`,
each attached. The logs are in `.claude/_sp/cls/`.

| Gate | Result |
|---|---|
| `test_classes_proposal.py` (final bytes) | **26 passed** (`t_classes4.log`). An earlier run had 2 failures, both test-expectation errors rather than product defects, described below. |
| Helper regression: the 18 other test files importing `authoring` | 495 passed (`t_reg1`–`t_reg4.log`: 132, 51, 75, 237) |
| Generator re-run after Black | byte-identical (`gen6.log`) |
| Black, Ruff (generator, test, `authoring.py`) | clean |
| mypy strict (`src/`) | clean |
| CR check | 0 in every file |
| pip-audit | **deferred, not green** (31 findings in 11 packages) |

The two test-expectation errors:
- Core traits reference each target once per component, so Barbarian's weapon category is cited through
  "Simple". This was also true of the before-copy.
- Selecting Ranger together with Hunter also reaches Hunter's own features, one hop from the selected
  subclass. The test now asserts no duplicates, and that the result is a superset of the Ranger read.

Broad accepted-material suites, *Casting Spells* and shared coverage were not run. That is scheduled after
5d, and the only production change is the helper, whose importers were all run.

### Secrets baseline (scoped maintenance)

See `issue-5d-classes-coherent-review.md` for the before/after SHA, the delta and the hook exit codes.

## Unfinished and next

1. Independent coordinating Codex review of this revision.
2. Owner semantic acceptance of both proposals and the draft. Nothing is recorded until then.
3. Owner choices remain open only where listed as retained findings (B7 release marker, B9/B10).
4. Later catalogues (Spells, Monsters, Animals) close most retained references. After 5d: the broad
   accepted-material review.
