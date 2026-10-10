# Committed accepted authority — CRD Issue 5d

One JSON file per published CRD Issue 5c release, holding the accepted
meaning-bearing inputs the production build consumes and the publication gate
judges against: the exact release binding, the declared semantic policy, the
accepted span classification, the review evidence that accepted it, the accepted
record/component/fact/prose-binding/relationship/reference/provenance inventory,
and the accepted per-record obligations.

The schema is whatever `oracle.load_accepted_inputs` accepts; it rejects a
missing key, an extra key, and an undeclared enum value rather than defaulting
any of them.

## What is committed here

**Current: `srd-5-2-1-corpus-8781d4e0-a3b.json`** — accepted authority for the
official-order release (`1299484e-c72d-509b-bd8d-d0169ee1f8d2` /
`5.2.1-corpus.8781d4e0-a3b`), holding the same twenty-four batches, 1835
records and 1486 reference resolutions at representation schema 17 (SHA-256
`def7caa1…`), with no reference findings, no uncovered leaves and no other
findings. The release changes only the cross-file part order to the official
fourteen-file order (Animals now follows its governing Monsters rules); units,
containers and within-file content are unchanged. The Owner accepted the exact
replacement candidate (SHA-256 `8a6a9a9c…`): the chain below re-executed
natively with every input rebound to this release (binding and leaf-keyed
chunk ids) and fresh Owner approvals. Relative to the accepted replacement
candidate, every proposal identity and semantic collection is unchanged.
`.claude/review-notes/issue-5c-release-order-recording/RECORD.py` recorded it
in one write on 2026-10-07 UTC (05:39:49Z) and replays the whole file with
`--verify`; the record is
`.claude/review-notes/issue-5c-release-order-recording/recorded-followup.md`.
The partial-publication block is retained.

**Superseded: `srd-5-2-1-corpus-3fe24ff6-4e3.json`** (unchanged, kept in this
directory as test and replay evidence only and excluded from the wheel and sdist; the committed-authority selector refuses
its release through `oracle.SUPERSEDED_RELEASE_VERSIONS`. Correction,
2026-10-07: the earlier statement that its retirement needs its own Owner
authorization was wrong. The 21 September 2026 Owner Decision already
authorizes retiring superseded artifacts and forbids inventing approval gates
for it; see
`.claude/review-notes/issue-5c-release-readiness/correction-followup.md`) — accepted
authority for the Monsters-corrected release (`67c81736-15fd-5e82-8523-e84922f0a7c6` /
`5.2.1-corpus.3fe24ff6-4e3`), holding twenty-four batches, 1835 records and
1486 reference resolutions at representation schema 17 (SHA-256 `e6f5f36a…`),
with no reference findings, no uncovered leaves, no other findings, and the
partial-publication block retained. The cross-release check refuses to
extend the file below onto this release, so the Owner approved a fresh chain:
the twenty batches regenerated against it, accepted in the original order
under one approval with the same 1099 resolutions (SHA-256 `86652ac9…`), then
the `monsters` batch (414 records) and its 83 resolutions.
`.claude/review-notes/issue-5d-monsters-corrections-ACCEPT.py` recorded them
in three steps on 2026-09-28 UTC (09:39:56Z, 09:41:27Z, 09:42:23Z) and replays
the whole file with `--verify`; the record is
`.claude/review-notes/issue-5d-monsters-corrections-recorded-followup.md`.
Over those twenty-one batches (SHA-256 `02f3a11b…`),
`.claude/review-notes/issue-5d-animals-ACCEPT.py` appended the `animals` batch
(95 records) and its 65 resolutions in two steps on 2026-09-28 UTC (17:28:00Z,
17:28:58Z) and replays them with `--verify`; the record is
`.claude/review-notes/issue-5d-animals-recorded-followup.md`. That
twenty-two-batch result held 1759 records and 1247 resolutions (SHA-256
`4ad85dab…`). The Owner then accepted the exact replacement Equipment proposal
(cited targets split to their own rows) and its 161 reference resolutions over
it, the other twenty-one batches and their evidence kept byte-identical;
`.claude/review-notes/issue-5d-equipment-cited-targets-ACCEPT.py` recorded them
in two steps on 2026-09-28 UTC (21:51:03Z, 21:52:52Z) and replays the whole file
with `--verify`; the record is
`.claude/review-notes/issue-5d-equipment-cited-targets-recorded-followup.md`.
That result held 1826 records and 1408 resolutions (SHA-256 `76a16103…`). The
Owner then accepted the exact remaining-references replacement candidate — eight
proposals replaced (checks-actions-rests, core-play-completion,
core-play-dependencies, character-creation-foundations, spellcasting,
gameplay-toolbox, magic-items, monsters), three resolutions re-keyed and 29
resolved — as a fresh chain in the same batch order, the other fourteen batches
and every kept resolution byte-identical with their evidence;
`.claude/review-notes/issue-5d-remaining-references-ACCEPT.py` recorded them in
two steps on 2026-09-29 UTC (07:34:50Z, 07:37:07Z) and replays the whole file
with `--verify`; the record is
`.claude/review-notes/issue-5d-remaining-references-recorded-followup.md`.
That result held 1832 records and 1434 resolutions (SHA-256 `e0fd7690…`). The
Owner then accepted the exact Animals catalogue replacement proposal
(`228726d2…5e38`: the part-level `animals.animals` record catalogues the 95
stat blocks in printed order) and its four reference resolutions, the other
twenty-one batches and every kept resolution byte-identical with their
evidence; `.claude/review-notes/issue-5d-animals-part-catalogue-ACCEPT.py`
recorded them in two steps on 2026-09-29 UTC (10:41:28Z, 10:44:29Z) and
replays the whole file with `--verify`; the record is
`.claude/review-notes/issue-5d-animals-part-catalogue-recorded-followup.md`.
That result held twenty-two batches, 1833 records and 1438 resolutions (SHA-256
`96e90f71…`). The Owner then accepted the exact framing-coverage proposal
(`a7a98598…a70`: Glossary Conventions as one prose-bound section, the other 20
framing leaves covered by review units alone), its glossary conventions and
reviewed framing exclusions; the batch was appended with no resolution, every
earlier batch and resolution byte-identical with its evidence. The exclusions
do not waive the licensing obligations the Legal Information states.
`.claude/review-notes/issue-5d-framing-coverage-ACCEPT.py` recorded it in one
step on 2026-09-29 UTC (12:47:38Z) and replays the whole file with `--verify`;
the record is
`.claude/review-notes/issue-5d-framing-coverage-recorded-followup.md`.
That result held twenty-three batches, 1834 records and 1438 resolutions
(SHA-256 `15478aa5…`). The Owner then accepted the exact Character Creation
catalogue proposal (`cee3b640…a5be`: the part-level
`character_creation.character_creation` record catalogues the six accepted
Character Creation sections in printed order) and its two reference
resolutions (Character Sheet's and Player Character's "Character Creation"
pointers); the batch was appended, every earlier batch and resolution
byte-identical with its evidence, the framing-coverage unit over the part
heading included.
`.claude/review-notes/issue-5d-character-creation-catalogue-ACCEPT.py`
recorded it in one write of two native steps on 2026-09-29 UTC (18:51:30Z,
18:51:34Z) and replays the whole file with `--verify`; the record is
`.claude/review-notes/issue-5d-character-creation-catalogue-recorded-followup.md`.
That result held twenty-four batches, 1835 records and 1440 resolutions
(SHA-256 `ea0c219f…`), retaining 62 reference findings. The Owner then accepted
the exact five finite-reference replacement proposals (classes,
character-origins-feats, spell-descriptions, magic-items, monsters: ten chapter
or multi-class pointers replaced by one citation per printed destination) as a
fresh chain in the same batch order, no resolution added, the other nineteen
batches and all 1440 resolutions byte-identical with their evidence;
`.claude/review-notes/issue-5d-finite-reference-atoms-ACCEPT.py` recorded it in
one step on 2026-09-30 UTC (00:18:19Z) and replays the whole file with
`--verify`; the record is
`.claude/review-notes/issue-5d-finite-reference-atoms-recorded-followup.md`.
That result held the same counts (SHA-256 `005768c2…`), retaining 52 reference
findings. The Owner then accepted the exact two Playing the Game replacement
proposals (core-play-dependencies, monsters: the three *Playing the Game*
chapter pointers replaced by seven atom citations) as a fresh chain in the
same batch order, no resolution added, the other twenty-two batches and all
1440 resolutions byte-identical with their evidence;
`.claude/review-notes/issue-5d-playing-the-game-atoms-ACCEPT.py` recorded it in
one step on 2026-09-30 UTC (05:09:01Z) and replays the whole file with
`--verify`; the record is
`.claude/review-notes/issue-5d-playing-the-game-atoms-recorded-followup.md`.
That result held the same counts (SHA-256 `92b7a68f…`), retaining 49 reference
findings. The Owner then accepted the exact Equipment class-eligibility
replacement proposal (the three class-eligibility phrases of Holy Symbol,
Druidic Focus and Arcane Focus removed as classes-scope references, the prose
kept) as a fresh chain in the same batch order, no resolution added, the other
twenty-three batches and all 1440 resolutions byte-identical with their
evidence; `.claude/review-notes/issue-5d-equipment-class-eligibility-ACCEPT.py`
recorded it in one step on 2026-09-30 UTC (07:55:56Z); the record is
`.claude/review-notes/issue-5d-equipment-class-eligibility-recorded-followup.md`.
That result held the same counts at schema 16 (SHA-256 `5f37fb08…`), retaining
46 reference findings. The Owner then accepted the exact thirteen-finding
reference-routes batch and its schema/route reconciliation (ADR-005d Decision 7
amendment): one native action lifted the file 16 -> 17 and appended thirteen
resolutions (132 routes, 197 destinations), no batch changed, all 1440 earlier
resolutions and their approvals byte-identical;
`.claude/review-notes/issue-5d-reference-alternatives-ACCEPT.py` recorded it in
one step on 2026-10-01 UTC (19:01:31Z) and replays the whole file with
`--verify`; the record is
`.claude/review-notes/issue-5d-reference-alternatives-recorded-followup.md`.
That result held 10492 spans and 1453 resolutions (SHA-256 `cc994e1b…`),
retaining 33 reference findings. The Owner then accepted the exact
ten-reference route batch and its combat-damage-breaking replacement (one
ranged-attack prose span and component added under the same source leaf and
ownership): one native action replaced that proposal in its recorded place
and appended ten resolutions (94 routes, 121 destinations), the other
twenty-three batches and all 1453 earlier resolutions and their approvals
byte-identical; `.claude/review-notes/issue-5d-finite-reference-routes-ACCEPT.py`
recorded it in one step on 2026-10-02 UTC (10:00:20Z) and replays the whole
file with `--verify`; the record is
`.claude/review-notes/issue-5d-finite-reference-routes-recorded-followup.md`.
That result held 1463 resolutions (SHA-256 `e9678ab3…`), retaining 23
reference findings. The Owner then accepted the exact thirteen-reference
candidate (the Equipment chapter, four cursed items and the spellcasting
rules as destinations) and its reader correction (record-owned supporting
citations read while their source record survives un-overridden): one native
action appended thirteen resolutions (15 routes, 62 destinations), no batch
changed, all 1463 earlier resolutions and their approvals byte-identical;
`.claude/review-notes/issue-5d-equipment-spell-references-ACCEPT.py` recorded
it in one step on 2026-10-03 UTC (09:30:23Z) and replays the whole file with
`--verify`; the record is
`.claude/review-notes/issue-5d-equipment-spell-references-recorded-followup.md`.
That result held 1476 resolutions (SHA-256 `5909e5bd…`), retaining 10 reference
findings. The Owner then accepted the exact final-ten reference candidate
(constructor, PROPOSAL and DELTA kept byte for byte under
`.claude/review-notes/issue-5d-final-ten-references/candidate/`): one native
action appended ten resolutions (144 routes, 201 destinations), no batch
changed, all 1476 earlier resolutions and their approvals byte-identical;
`.claude/review-notes/issue-5d-final-ten-references-ACCEPT.py` recorded it in
one step on 2026-10-07 UTC (01:30:07Z) and replays the whole file with
`--verify`; the record is
`.claude/review-notes/issue-5d-final-ten-references-recorded-followup.md`.
The Monsters, Animals, Equipment, remaining-references, Animals catalogue,
framing-coverage, Character Creation catalogue, finite-reference atoms,
Playing the Game atoms, Equipment class-eligibility, reference-alternatives
and finite-reference-routes scripts' `--verify` now refuse the file (exit 1),
as do the reference-routes, finite-reference-routes and
equipment-spell-references constructors' check modes. The
equipment-spell-references script's `--verify` and the final-ten constructor's
check mode pin the prior bytes (`5909e5bd…`) and so also refuse it; they were
not rerun against the new file.
The release's cross-file part order is not declared correct: Animals still precedes its
governing Monsters rules, tracked for one bounded correction before
publication or activation. That correction is the official-order release
recorded above.
Nothing below was rewritten as if accepted against the new binding.

The file below is **superseded** and kept in this directory as historical
evidence only; the committed-authority selector refuses its release through
`oracle.SUPERSEDED_RELEASE_VERSIONS`. Correction, 2026-10-07: retiring it needs
no further Owner authorization; the 21 September 2026 Owner Decision already
authorizes it (see the correction note above).

**Superseded: `srd-5-2-1-corpus-574662e9-0ef.json`** (kept in this directory as
test and replay evidence only and excluded from the wheel and sdist) — accepted authority for the
spell-table-corrected release (`ebdd9333-eeed-5df1-b3e1-8b97c2f65f80` /
`5.2.1-corpus.574662e9-0ef`), holding twenty batches, 1250 records and 1099
reference resolutions (SHA-256 `fc62c47c…`). The Owner accepted the
`magic-items` batch (270 new records, plus one component on each of the
accepted Potion of Healing and Spell Scroll Equipment records; 1339 spans, 271
review units) and its one resolution, `gameplay_toolbox.travel_pace`'s
"Carpet of Flying" to `magic_items.carpet_of_flying`, over the nineteen-batch
result below (SHA-256 `671f47d7…`), retaining 315 reference findings and the
partial-publication block;
`.claude/review-notes/issue-5d-magic-items-ACCEPT.py` recorded them on
2026-09-27 UTC (23:27:11Z, 23:28:26Z) and replays the whole file with
`--verify`; the record is
`.claude/review-notes/issue-5d-magic-items-recorded-followup.md`.

The nineteen-batch result held 980 records and 1098 reference resolutions.
The Owner accepted the `gameplay-toolbox` batch (33 records, 285 spans, 34
review units) and its one resolution, `glossary.challenge_rating`'s "Combat
Encounters" to `gameplay_toolbox.combat_encounters`, over the eighteen-batch
result below (SHA-256 `b1f8718f…`), retaining 166 reference findings;
`.claude/review-notes/issue-5d-gameplay-toolbox-ACCEPT.py` recorded them on
2026-09-27 UTC (09:46:01Z, 09:46:44Z); its own `--verify` now refuses the
extended file's batch set as unrecognized, and the Magic Items script's
`--verify` replays the whole file over that rebuild. The record is
`.claude/review-notes/issue-5d-gameplay-toolbox-recorded-followup.md`.

The eighteen-batch result held 947 records and 1097 reference resolutions.
The cross-release check refuses
to extend the file below onto the corrected release, so the Owner approved a
fresh chain: the seventeen batches regenerated against it, accepted in the
original order with the same 51 resolutions, then the `spell-descriptions`
batch and its 1046 resolutions. `.claude/review-notes/issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py`
recorded it in three steps on 2026-09-27 UTC (03:34:02Z, 03:34:46Z,
03:35:13Z); its own `--verify` now refuses the extended file's batch set as
unrecognized, and the Gameplay Toolbox script's `--verify` replays the whole
file over that rebuild. The record is
`.claude/review-notes/issue-5d-spell-corrections-and-descriptions-recorded-followup.md`.
Nothing below was rewritten as if accepted against the new binding.

The file below is **superseded** and was retired on 2026-09-27 under Owner
authorization, together with its twenty-seven superseded construction inputs
(`.claude/review-notes/issue-5d-spell-retirement-followup.md`); it is no longer
in this directory. What follows records it as it was accepted.

**Clean restart: `srd-5-2-1-corpus-626c83f8-209.json`** — accepted authority for
the source-corrected release (`0b1a965e-28bd-55e6-ac13-bc7786a1bace` /
`5.2.1-corpus.626c83f8-209`), holding seventeen batches and fifty-one
reference resolutions under schema 16.

It replaces `srd-5-2-1-corpus-883aabdf-462.json`, which bound the release the
source correction superseded. The Owner approved one replacement chain, recorded
at 2026-09-24T10:02:36Z under a single approval: the twelve batches regenerated
against the corrected release, accepted in the original order with the same six
resolutions. The Owner then accepted the `equipment` batch over that chain,
and then the `spellcasting` batch over the Equipment result, both recorded on
2026-09-25, and then the `rules-glossary-completion` batch over the Spellcasting
result, recorded on 2026-09-26, and then the Classes packet (the `classes` and
`class-option-catalogues` batches and one resolution) over the glossary
result, recorded later the same day (below).
`.claude/review-notes/issue-5d-classes-ACCEPT.py --verify` replays the whole
file: it rebuilds the twelve-batch chain from those proposals
through `issue-5d-source-correction-REPLACEMENT-ACCEPT.py`, then both Equipment
steps at their recorded times through `issue-5d-equipment-ACCEPT.py`, pinned to
the thirteen-batch bytes, then both Spellcasting steps at their recorded times
through `issue-5d-spellcasting-ACCEPT.py`, pinned to the fourteen-batch bytes,
then the glossary acceptance at its recorded time through
`issue-5d-rules-glossary-completion-ACCEPT.py`, pinned to the fifteen-batch
bytes, then the three Classes steps at their recorded times. The four earlier
scripts' own `--verify` now check only the prefix each rebuilds (twelve,
thirteen, fourteen and fifteen batches), held to its recorded bytes, and point
onward to the script for the current file.
The first twelve bullets below describe each
batch's content as the Owner originally accepted it; the proposal identities
they quote belong to the superseded chain, whose per-batch scripts, proposals and
intermediate digests are retired (see history at `5ed0657`):

- `conditions-pilot`: 15 Conditions, the Condition index and Grappling, 79
  accepted spans and 17 review units. The Owner accepted proposal
  `b16c7af9…ed474` exactly, with the `glossary.unarmed_strike` target left
  unresolved. It was recorded over no prior, so nothing from the quarantined
  artifact below is inherited.
- `actions-pilot`: the twelve glossary [Action] entries and Unarmed Strike, 75
  accepted spans and 13 review units. The Owner accepted proposal
  `930da21b…fb9b` exactly, on 2026-09-22 UTC over the Conditions pilot as
  `prior`, re-derived from its proposal rather than read from this file.
- `reference-closure`: Concentration, the three [Attitude] entries, Speed, the
  four special speeds, and Climbing, Crawling, Flying, Jumping and Swimming. It
  holds 53 accepted spans and 14 review units. The Owner accepted proposal
  `5197e5e6…cbc2` exactly, over both pilots as `prior`, re-derived from their
  proposals.
- `movement-closure`: Difficult Terrain, Falling [Hazard], High Jump, Hover and
  Long Jump, 29 accepted spans and 5 review units. The Owner accepted proposal
  `7ab85d26…cdc9` exactly, retaining the unresolved Combat target, over the
  three prior batches as `prior`, re-derived from their proposals.
- `combat-turn-1`: Initiative, Occupied Space, Opportunity Attacks, Reach,
  Surprise and Unoccupied Space, 16 accepted spans and 6 review units. The Owner
  accepted proposal `624f799c…fbbf` exactly, retaining the unresolved Combat
  target, over the four prior batches as `prior`, re-derived from their
  proposals.
- `damage-and-hit-points`: Damage, Damage Roll, Hit Points, Immunity,
  Resistance, Temporary Hit Points and Vulnerability, 16 accepted spans and 7
  review units. The Owner accepted the selected arm-A proposal `5cdc86e3…435a`
  exactly, retaining its unresolved targets, over the five prior batches as
  `prior`, re-derived from their proposals.
- `combat-damage-breaking`: Playing the Game's Combat, Damage and Healing and
  Exploration › Breaking Objects, and the glossary's Breaking Objects and
  Damage Threshold: 5 records, 162 accepted spans and 5 review units. The Owner
  approved proposal `05374a97…9227` exactly, with its findings, retaining all
  unresolved references, over the six prior batches as `prior`, re-derived
  from their proposals.
- `checks-actions-rests`: Playing the Game's D20 Tests, Proficiency and
  Actions, and the glossary's Damage Types, Dead, Long Rest and Short Rest: 7
  records, 125 accepted spans and 7 review units. The Owner accepted proposal
  `b23a5712…7c2c` exactly and, in the same decision, approved the drafted
  attack-roll resolution. It ran in two native steps over the seven prior
  batches as `prior`, re-derived from their proposals: `accept_proposal`, then
  `resolve_references`.
- `core-play-completion`: Playing the Game's Rhythm of Play, The Six Abilities,
  Social Interaction and Exploration (less its Breaking Objects subsection,
  which `play.exploration.breaking_objects` already owns, Marching Order
  sidebar included), and the glossary's Armor Class, Challenge Rating and
  Expertise: 7 records, 71 accepted spans and 7 review units covering 85
  leaves. The Owner approved proposal `4a95a5e5…f299` exactly. It was accepted
  through `accept_proposal` over the eight prior batches *with* the
  resolution as `prior`, re-derived from their proposals; the resolution and
  its authorization are carried unchanged. No resolution was added.
  Every leaf of the Playing the Game chapter now has one owner except its
  `# Playing the Game` title, which sits outside every section.
- `core-play-dependencies`: the eleven Rules Glossary entries the accepted core
  play cited and nothing defined — Attack Roll, Stat Block, Carrying Capacity,
  Blindsight, Darkvision, Tremorsense, Truesight, Burning, Dehydration,
  Malnutrition and Suffocation: 11 records, 66 accepted spans and 11 review
  units covering 52 leaves. The Owner accepted proposal `47a1a7a5…2b85`
  exactly, "with the twenty reference findings retained and partial
  publication/activation blocked". It was accepted through `accept_proposal`
  over the nine prior batches *with* the resolution as `prior`, re-derived
  from their proposals; the resolution and its authorization are carried
  unchanged. No resolution was added.
- `character-creation-foundations`: the whole Character Creation part
  (character sheet, the five creation steps, Level Advancement and Tiers of
  Play, Starting at Higher Levels, Multiclassing and Trinkets) and the five
  Rules Glossary entries the accepted Stat Block cited — Alignment, Creature
  Type, Experience Points, Passive Perception and Size: 11 records, 69
  components, 152 accepted spans and 11 review units covering 179 leaves. The
  Owner accepted proposal `f9b41b22…2d64` exactly and approved both drafted
  resolutions, "retaining the 29 remaining reference findings and blocking
  partial publication/activation". It was accepted through `accept_proposal`
  over the ten prior batches *with* the attack-roll resolution as `prior`,
  re-derived from their proposals, and the two resolutions were then recorded
  by one `resolve_references` action over that result.
- `character-origins-feats`: the whole Character Origins part (backgrounds and
  species, the four backgrounds and nine species with their traits, lineages,
  legacies and tables) and the whole Feats part (feat structure, categories,
  prerequisites, repeatability and all seventeen feats): 33 records, 149
  components, 172 accepted spans and 33 review units covering 208 leaves, with
  30 `catalogue_member` relationships linking each of the three catalogue
  sections to the entries it prints. The Owner accepted proposal
  `b15decd5…de5c6` exactly and authorized its three drafted resolutions
  ("I accept both 1. and 2.", answering item 1 of the Owner review: retain
  the 91 remaining findings and block partial publication/activation). The
  prior declares schema 15 and this proposal schema 16, so `accept_proposal`
  carried the eleven prior batches *with* their three resolutions across the
  one registered lift, `5d-lift-schema-15-to-16`, by identity, and recorded
  the crossing; the three resolutions were then recorded by one
  `resolve_references` action over that result.
- `equipment`: the whole Equipment part less its title (coins, weapons with
  their properties and mastery, armor, tools, adventuring gear, mounts and
  vehicles, lifestyle, food, lodging, hirelings, spellcasting services, the
  general magic-item rules, and crafting, brewing and scribing): 80 records,
  207 components, 409 accepted spans and 14 review units covering 375 leaves,
  with 66 `catalogue_member` relationships linking each section to the named
  items and rules it prints. The Owner accepted proposal `e25f7a82…58b87`
  exactly and approved its 43 drafted resolutions ("I accept it.", answering
  the review's decision item: retain the 58 remaining reference findings and
  block partial publication/activation). It was accepted through
  `accept_proposal` over the twelve prior batches *with* their six resolutions
  as `prior`, re-derived from their proposals, at 2026-09-25T05:47:17Z, under
  the same schema, so no lift was needed; the 43 resolutions were then
  recorded by one `resolve_references` action over that result at
  2026-09-25T05:47:29Z.
- `spellcasting`: the general spellcasting rules of *Spells* that precede
  *Spell Descriptions*, plus the Rules Glossary entries they point at directly
  (Area of Effect, its six shapes and Cover): 19 records, 55 components, 72
  accepted spans and 19 review units covering 104 leaves. The Owner accepted
  proposal `0b7f14ff…1d55` exactly and approved its one drafted resolution
  ("I accept the exact 19-record proposal and approve its one reference
  resolution, retaining 59 reference findings."). It was accepted through
  `accept_proposal` over the thirteen prior batches *with* their 49
  resolutions as `prior`, rebuilt natively, at 2026-09-25T18:05:59Z, under the
  same schema, so no lift was needed; the resolution was then recorded by one
  `resolve_references` action over that result at 2026-09-25T18:06:11Z.
- `rules-glossary-completion`: every *Rules Definitions* entry no earlier batch
  authored, *Improvised Weapons* among them: 60 records, 72 components, 116
  accepted spans and 60 review units covering 133 leaves; only the section's
  heading and introduction stay unowned. The Owner accepted proposal
  `6cafaf57…ce16` exactly ("I accept this exact proposal, retaining 66
  reference findings."); no resolution was drafted or approved. It was
  accepted through `accept_proposal` over the fourteen prior batches *with*
  their 50 resolutions as `prior`, rebuilt natively, at 2026-09-26T08:50:19Z,
  under the same schema, so no lift was needed.
- `classes`: the twelve classes, their features, progression and spell-list
  tables, multiclass instructions and their twelve included subclasses: 268
  records, 1028 accepted spans and 36 review units. `class-option-catalogues`:
  the *Metamagic Options* and *Eldritch Invocation Options* catalogues and
  their 38 options: 40 records, 135 accepted spans and 40 review units.
  Together they cover 1174 of the *Classes* part's 1175 leaves (all but
  `# Classes`). The Owner accepted proposals `02501670…fc87` and
  `3dae0910…3293` exactly and approved their one resolution ("I accept the
  exact Classes proposals and approve the one reference resolution,
  retaining 1,153 reference findings."). They were accepted through
  `accept_proposal` over the fifteen prior batches *with* their 50
  resolutions as `prior`, rebuilt natively, at 2026-09-26T21:34:59Z and
  2026-09-26T21:35:14Z in that order, under the same schema, so no lift was
  needed; the resolution was then recorded by one `resolve_references` action
  over that result at 2026-09-26T21:35:31Z.

**The fifty-one reference resolutions.** `resolve-attack-roll-playing-the-game-1`
sends the accepted `play.combat/attack_structure` citation "Playing the Game"
(scope `srd-5.2.1/playing-the-game`) to `play.d20_tests`, with its reviewed
provenance span and the Owner's authorization recorded beside it. The accepted
citation keeps its empty target; the effective representation, which the build
persists and the gate judges, carries the destination. Stat Block's two
"Playing the Game" pointers share that wording and scope but are distinct
citations (ADR-005d Decision 7, as amended by the Owner's citation-identity
decision), so they stay unresolved and the resolution still applies.
`resolve-armor-class-character-creation-1` sends the accepted
`play.d20_tests/armor_class` citation "Character Creation" to
`character_creation.create_your_character` (Step 5, Armor Class), and
`resolve-proficiency-bonus-character-creation-1` sends the accepted
`play.proficiency/proficiency_bonus` citation "Character Creation" to
`character_creation.level_advancement` (the Character Advancement table and
Gaining a Level), both in scope `srd-5.2.1/character-creation`, each with its
reviewed provenance span and the Owner's authorization. Both accepted
citations keep their empty targets, as above.
`resolve-choose-background-character-origins-1` and
`resolve-choose-species-character-origins-1` send the accepted
`character_creation.create_your_character` citations `choose_background` and
`choose_species`, "Character Origins" (scope `srd-5.2.1/character-origins`),
to `character_origins.backgrounds` and `character_origins.species`, and
`resolve-background-feat-feats-1` sends its `background_feat` citation
"Feats" (scope `srd-5.2.1/feats`) to `feats.feat_descriptions`, each with its
reviewed provenance span and the Owner's authorization. The three accepted
citations keep their empty targets, as above; naming a catalogue section
reads its introduction and then its members in printed order.
The 43 Equipment resolutions each send one accepted citation in scope
`srd-5.2.1/equipment` to the Equipment record it names, with its reviewed
provenance span and the Owner's authorization: 29 from the Character Origins
backgrounds (their starting equipment and tool proficiencies, such as
"Calligrapher's Supplies" to `equipment.tools.calligraphers_supplies`), six
from the Archery, Defense, Great Weapon Fighting and Two-Weapon Fighting
feats, four from Character Creation and four from Playing the Game. The
accepted citations keep their empty targets, as above.
`resolve-play-d20-tests-attack-ability-modifier-spells-spellcasting-1` sends
the accepted `play.d20_tests/attack_ability_modifier` citation "Spells" (scope
`srd-5.2.1/spells`) to `spells.attack_rolls`, with its reviewed provenance span and the Owner's authorization; the accepted citation
keeps its empty target, as above.
`resolve-character-origins-elf-elven-lineage-wizard-spell-list-classes-1`
sends the accepted `character_origins.elf/elven_lineage` citation "Wizard
spell list" (scope `srd-5.2.1/classes`) to `classes.wizard`, whose reading
includes that list, with its reviewed provenance span and the Owner's
authorization; the accepted citation keeps its empty target, as above.

The Actions pilot defined `glossary.unarmed_strike`; the reference-closure batch
defined the five targets the pilots left undefined; the movement-closure batch
defines four of the five it left; the combat-turn-1 batch defines Reach for its
own Opportunity Attacks; the damage-and-hit-points batch defines Hit Points for
its own Damage and Temporary Hit Points; the combat-damage-breaking batch
defines `play.combat`, `play.damage_and_healing` and
`glossary.breaking_objects`, the three targets the earlier batches left, by
holding their content; the checks-actions-rests batch defines `play.actions`,
`glossary.short_rest`, `glossary.long_rest`, `glossary.damage_types` and
`glossary.dead` the same way, and the resolution above answers the
"Playing the Game" pointer; the core-play-completion batch defines
`glossary.armor_class`, `glossary.challenge_rating` and `glossary.expertise`
the same way; the core-play-dependencies batch defines the eleven glossary
entries the core play cited the same way; the character-creation-foundations
batch defines the five Stat Block glossary targets the same way, and its two
resolutions answer the two "Character Creation" pointers; the
character-origins-feats batch defines the three catalogue sections those
Character Creation pointers name, and its three resolutions answer them;
the equipment batch defines the Equipment records the earlier batches cite,
and its 43 resolutions answer them; the spellcasting batch defines the
general spellcasting rules and the glossary entries they cite, and its one
resolution answers one "Spells" pointer; the rules-glossary-completion batch
defines `glossary.improvised_weapons`, so Equipment's "Improvised Weapons"
citation closes by key; the Classes packet defines the class records, and its
one resolution answers the Elf's "Wizard spell list" pointer. 1,153 reference
findings remain, none given a guessed destination: 1,088 unresolved pointers
the Classes packet keeps (1,026 spells, 44 equipment items and "(see
Equipment)" pointers, 9 monsters, 5 animals, 3 class-list phrases and one
"Playing the Game"), and 65 from the earlier batches — the 66 below less the
Elf's, now resolved:

- eighteen broad pointers from the earlier batches, each naming a part rather
  than one record: "Playing the Game" (×4, `srd-5.2.1/playing-the-game`; two
  from Stat Block, two from Character Creation), "Classes" (×6,
  `srd-5.2.1/classes`, Character Creation), "Spells" (`srd-5.2.1/spells`),
  "Equipment" (×3, `srd-5.2.1/equipment`, one each from Character Creation,
  Playing the Game and `spells.components`, naming the whole part),
  "Monsters" (`srd-5.2.1/monsters`),
  "Rules Glossary" (`srd-5.2.1/rules-glossary`), and "Gameplay Toolbox" and
  "Combat Encounters" (`srd-5.2.1/gameplay-toolbox`);
- thirty catalogue members Character Origins and Feats cite and no record
  defines: 23 spells (`srd-5.2.1/spells`) and 7 class features or spell lists
  (`srd-5.2.1/classes`);
- nine Equipment pointers into parts nobody has authored: three classes,
  "Gameplay Toolbox" (×2), "Magic Items" (×2, `srd-5.2.1/magic-items`),
  "Monsters" and the spell "Identify";
- one `spells.components` pointer to the Component Pouch
  (`srd-5.2.1/equipment`), which no accepted record is;
- eight part-level pointers the rules-glossary-completion batch keeps:
  "Character Creation" (×3, `srd-5.2.1/character-creation`), "Casting
  Spells" (×2) and "Spells" (×3, both `srd-5.2.1/spells`).

Their keys are provisional until those sections are authored. The accepted
Resistance and Vulnerability factors carry no typed "has this damage type"
applicability or once-per-instance limit, and Hit Points has no typed tracked
quantity; that meaning is kept in exact governing prose.

The release **cannot publish**, and the 1,153 remaining references are
not corpus completion: 7 657 of the release's 10 465 leaves carry no accepted
authority at all, one finding each. Nothing is merged, published or activated,
partially or otherwise.

**Removed under Step 5 of the Recorded Owner Decision of 21 September 2026.** The artifact described below was quarantined on 21 September and deleted from this directory once the replacement authority above existed; Git history retains it. Its release identity is still refused at every authority seam by `afterworlds.quarantine`, so a copy or stored row naming it meets a typed refusal rather than an absence. What follows records what it was. See `docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md` and `.claude/review-notes/issue-5c-quarantine-retirement.md`.

`srd-5-2-1-corpus-36b786d8-fa2.json` — accepted authority for the SRD 5.2.1
release (`4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` /
`5.2.1-corpus.36b786d8-fa2`), currently holding **batches `conditions-1`,
`hazards-1`, `actions-1`, `attitudes-1`, `areas-of-effect-1`, `cover-1`,
`speed-1`, `proficiency-destinations-1` and `proficiency-1`** — 53 accepted
records over 761 accepted spans.

The file is named for the release, not for the batch, because the resolver
matches on the release binding and refuses outright when two artifacts claim one
release. A later batch therefore **extends this file** — `accept_proposal` takes
the loaded artifact as `prior` and merges, so an added batch cannot silently
discard an earlier one's reviewed work — rather than adding a second file. That
is how `hazards-1` was accepted on 2026-09-03 over the `conditions-1` prior,
how `actions-1` was accepted on 2026-09-09 over both, how `attitudes-1` was
accepted on 2026-09-10 over all three — that one also crossing a schema, from 7
to 8, through the registered lift rather than by restamping the file — and how
`areas-of-effect-1` was accepted on 2026-09-11 over all four, crossing from 8 to
9 the same way, how `cover-1` was accepted later the same day over all five,
crossing from 9 to 10, how `speed-1` was accepted on 2026-09-12 over all six,
crossing from 10 to 11, and how the two Proficiency batches were accepted on
2026-09-20 UTC over all seven — `proficiency-destinations-1` first and
`proficiency-1` three seconds later, both reviewed under schema 15, crossing
from 11 to 15 through the four registered lifts and crossing the semantic
policy from `5d-semantic-policy-1` to `5d-semantic-policy-2` through its one
registered transition. That order is load-bearing: the `Expertise`
destination cites `Proficiency`, which `proficiency-1` is the batch to
define.

**The CRD Issue 5d corpus is incomplete, so this release still cannot publish.**
Batches beyond `proficiency-1` have not begun, ten cross-batch reference targets
named by accepted content are still unresolved, four accepted citations name no
target at all, and nothing is published or activated:
`glossary.concentration`, inherited and untouched since `conditions-1`, plus the
nine movement entries `speed-1` cites without defining — `glossary.burrow_speed`,
`glossary.climb_speed`, `glossary.climbing`, `glossary.crawling`,
`glossary.fly_speed`, `glossary.flying`, `glossary.jumping`,
`glossary.swim_speed` and `glossary.swimming`. The residue moves in both
directions and `speed-1` moved it both ways at once: it defines `glossary.speed`,
so the `Speed` citation `actions-1` printed in Dash now resolves, and it emits
nine citations of its own, so the count went from two to ten. Those nine are
cited, not ingested — no record, component, fact or span was created for any of
them, and no target was invented. Accepting a complete source class can widen
the residue as well as narrow it, and neither direction is a reason to accept or
withhold a batch.

The two Proficiency batches left those ten **unchanged** and added a residue of
the second kind: four accepted citations whose target key is empty — *Stat
Block* in the Rules Glossary, *Combat Encounters* in the Gameplay Toolbox, and
*Combat* and *Opportunity Attack* in Playing the Game. Review read each
citation the source plainly makes and could state no destination key, so none
was invented and no destination was ingested for them. They are honest empties,
not resolutions: `reference_resolutions` is empty in this artifact, so no
reviewed reference resolution was invoked for any of the fourteen. Those four
stay open obligations until genuinely reviewed destinations exist; they close
only through an explicit reviewed resolution under ADR-005d Decision 7, never
by a later batch happening to mint a plausible target. What the Proficiency
batches did close is internal: all four references `proficiency-1` prints
resolve uniquely against the destinations batch accepted immediately before it.
Accepted authority now exists and resolves, but the publication gate compares it
against the *whole* persisted projection: a projection carrying any record this
artifact does not accept fails with `MISSING_AUTHORITY` / `UNEXPECTED_AUTHORITY`.
Nothing here publishes, activates, or retires anything — committing an accepted
artifact is the acceptance action of record and nothing more.

Files here are review artifacts, not build output. Nothing in `src/` writes to
this directory, and no accepted artifact may be generated from a candidate or
from persisted projection state: an oracle derived from the thing it checks
proves only that the code agrees with itself.

## The workflow

```text
machine proposal  →  human semantic review  →  explicit acceptance  →  commit
```

**Propose.** A tool builds a `MechanicalProposal`
(`afterworlds.ingestion.mechanical.proposal`) and writes `proposal_payload` to a
working path — never to this directory. A proposal is a *different shape* from
accepted authority at every level: a different `artifact_kind`, spans under
`proposed_spans` carrying a per-span origin and rationale, representation under
`proposed_representation`, and no `acceptance` or `obligations` blocks at all.
It therefore cannot be loaded as accepted authority by renaming it, moving it
into this directory, or editing one field.

**Review.** A human reads the proposal and decides the exact scope to accept.
The rationale on each proposed span is what makes that reviewable.

**Accept.** `acceptance.accept_proposal` records the action: the exact resolved
scope, the full semantic diff of what it changed, the selection rule as
evidence, and who accepted it when. Only spans named in the scope are accepted —
silence is never acceptance. Accepting over a prior artifact merges rather than
replaces, so a later content batch cannot silently discard an earlier one's
reviewed work.

**Commit.** `oracle.accepted_inputs_payload` writes the artifact; the reviewer
commits it here. That commit *is* the acceptance action of record.

## One artifact, two halves

The file carries both the accepted result and the review evidence, and the
loader keeps them separate:

* `AcceptedInputs.oracle` is what the publication gate judges against. It
  excludes reviewer, timestamp, batch grouping, and diff, because review process
  is not identity-bearing — re-reviewing an unchanged classification must not
  remint a projection (#137 acceptance criterion 11).
* `AcceptedInputs.batches` / `.acceptances` are the auditable evidence. The
  build carries them into persistence, because the gate requires an explicit
  acceptance record for every span in reconstructed state.

They live in one file so they cannot drift apart. The independence that matters
is untouched: this is committed bytes a reviewer accepted, never anything
derived from a candidate or from persisted output.
