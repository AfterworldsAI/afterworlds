# CRD Issue 5d — Spell Descriptions packet (UNACCEPTED, for Codex review then Owner decision)

Scope: the complete *Spell Descriptions* section of the qualified *Spells*
part, SRD 5.2.1 pp107-175, over the Owner-corrected release
`ebdd9333-eeed-5df1-b3e1-8b97c2f65f80` / `5.2.1-corpus.574662e9-0ef` (built in
a private scratch store only; see
`issue-5d-class-spell-tables-REPLACEMENT-REVIEW.md`). One consolidated proposal plus unrecorded
resolution drafts. Nothing here is accepted, recorded, committed, pushed or
published. The general spellcasting rules (`spells.casting_spells` and its ten
siblings) are accepted and are not reauthored.

Green tests do not prove full source fidelity. They prove the packet derives
from the release, claims every word it scopes, restates what the typed arms
say, and composes over the accepted oracle. What the source *means* is for
Codex and the Owner to review against the PDF.

## Artifacts

| Artifact | Identity / SHA-256 |
|---|---|
| `issue-5d-spell-descriptions-PROPOSAL.json` | identity `6361cf7f6f5015cc43a2870df50647d76589fd4d0d68f93327804aa890049783`; file `acf1965acebb8ee1e8c1801cddea4ce8d55bfd586659fecb40c30ce9bc13e4b2` |
| `issue-5d-spell-descriptions-resolutions-DRAFTS.json` (1046 drafts, unrecorded) | file `5c4373a30a34b74d17a02be2cf3eadebe659e284e1cb7d63962dd3e0aeb75c3a` |
| `issue-5d-spell-descriptions-source.py` | the 2036 qualified leaves, in printed order |
| `issue-5d-spell-descriptions-generator.py` | derives both artifacts from the corrected release over the replacement chain |
| `tests/ingestion/mechanical/test_spell_descriptions_proposal.py` | 20 tests (3 for the class-table correction) |
| `src/afterworlds/ingestion/mechanical/authoring.py` | additive helper change (below) |
| `issue-5d-class-spell-tables-owner-correction.diff` | the Owner-decided class-table source correction, now applied to the controlled source; file `03bbeedb584ea2b621aed532bcec65310b46ab55a7c9d5314d04a8bb98ad2c39` |

Composed over the **replacement chain**, simulated in memory on the corrected
release (`issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py`, serialized
`4aaa37b04c61fdc182a7fed60478ff02dc5b45a952f9bd1bfef5f392887d2e2d`, *not* an
acceptance) — 17 batches, 603 records, 2776 spans, 305 units, 51 resolutions,
1157 reference findings, 7657 uncovered leaves, no other findings. The
accepted oracle `a3b81a03c41abf8495634f5118841db2b1f6cfb1759f06a5b88be05d3edaa1e7`
is unchanged and replayable, and binds the pre-correction release; this packet
cannot be accepted over it.

## Source qualification

* All 2036 leaves from `## Spell Descriptions` to the end of *Wish* were read
  against the official PDF (`docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf`, text
  extracted with pdfplumber by page and by column). The release text is the
  PDF's, with these extraction artifacts noted and not corrected: three
  column/page splits inside one paragraph (source-list leaves 70, 84, 730:
  *Antilife Shell*, *Antipathy/Sympathy*, *Find the Path*) and one
  comma difference in *Protection from Evil and Good* (leaf 1480). None
  changes meaning.
* 339 spells, each `#### Name`, then its level line, then the four descriptor
  lines. The release prints the descriptor as one leaf, as two, or fused with
  the first body paragraph in one leaf (11 spells); a fused leaf is cut at the
  printed line break. Three body leaves (*Giant Insect*, *Ice Storm*, *Wall of
  Ice*) print `_Using a Higher-Level Spell Slot._` after a line break inside
  the effect's last paragraph; they are cut at that break the same way (see
  Correction). 2036 leaves yield 2050 spans, each exact source text.
* Four spells print a stat block (*Animate Objects*, *Find Steed*, *Giant
  Insect*, *Summon Dragon*), each under its own heading with Traits / Actions
  / Bonus Actions containers.
* **Level lines against the accepted class spell tables.** For every (class,
  spell) the level, Concentration flag (C), Ritual flag (R) and costly-or-
  consumed material flag (M, a GP price or "consumes") agree. Seven pairs
  differ; the PDF prints both sides:

  | Class | Spell | Level line (PDF page) | Class table (PDF page) |
  |---|---|---|---|
  | Druid, Sorcerer, Wizard | Flaming Sphere | Level 2 **Conjuration** (p132) | **Evocation** (pp44, 68, 80) |
  | Sorcerer | Mind Spike | names the Sorcerer (p149) | not listed (only Warlock p75, Wizard p80 list it) |
  | Bard, Sorcerer, Wizard | Phantasmal Force | names all three (p151) | not listed in any table |

  **Owner-decided:** the descriptions are correct and the class tables are
  wrong in these cases (see Owner items). The controlled source now carries
  the seven Owner corrections, so on the corrected release
  `CLASS_LIST_DISAGREEMENTS` is empty and `class_list_disagreements()`
  re-derives `()`.
* An independent reviewer checked the 339 spells / 2036 leaves, the 17 tables,
  the four embedded stat blocks and the 1042 exact draft references (before
  the correction added four), with targeted visual checks against the official
  PDF.

## What the packet proposes

* `spells.spell_descriptions` — `general_rule`, reads `## Spell Descriptions`;
  each spell a `CATALOGUE_MEMBER` of it, in printed order (339).
* 339 `spell` records `spells.<slug>`; no key collides with an accepted
  `spells.*` key.
* Per spell:
  * `descriptor` — `mixed`: heading, level line, the four descriptor lines, and
    one `SpellDescriptorFact` (ADR-005d Decision 4). The prose keeps the
    material description, its cost and consumption wording, and any reaction
    or bonus-action trigger.
  * `effect`, then `using_a_higher_level_spell_slot` / `cantrip_upgrade` where
    printed — `prose_bound`. Option labels and tables stay inside the
    component that prints them, in printed order.
  * *Wish* (Canary 1): `effect`, then each printed option as its own component
    (`object_creation`, `instant_health`, `resistance`, `spell_immunity`,
    `sudden_learning`, `roll_redo`, `reshape_reality`), then `stress`.
    `instant_health` is `mixed` with `HealingFact(restores_all_hit_points=True)`,
    the case that field documents. The stress's "1d10 Necrotic damage per level
    of that spell" stays prose: `DamageInterval` is limited to distance bases.
* 4 `creature` records `spells.<spell>.<creature>`, each `SCOPED_WITHIN` its
  spell (Canary 4), prose-bound by printed container. The spell's "uses the …
  stat block" text references it.
* 879 `SPELL_LIST_MEMBER` edges `classes.<class> → spells.<spell>`, one per
  class a level line names, cited on that level line.
* Reason codes: `gamemaster_latitude` on the 21 components whose text names
  the GM (e.g. *Wish*'s Reshape Reality, *Augury*, *Commune*); everything
  else `no_identified_structured_use`. Saves, attack rolls, damage and slot or
  cantrip scaling stay prose: no code-owned use is identified for them here,
  and the slot-level basis of scaling is a Known Unknown.

Totals: 344 records, 824 components (340 mixed, 484 prose-bound), 340 facts,
1173 references, 2050 spans, 340 review units, 5577 provenance claims.

### References

| Kind | Count | Target |
|---|---|---|
| Rules Glossary terms (the Classes term list plus Spell Attack, Cone, Line, Passive Perception) | 1074 | accepted `glossary.*` |
| Italic spell names, and each stat block a spell uses | 63 | in-packet `spells.*` |
| Holy Symbol, Club, Quarterstaff, Artisan's Tools | 4 | accepted `equipment.*` |
| Holy Water (priced, but no record of its own) | 1 | unresolved (equipment) |
| Bold creatures (Awaken, Find Familiar, Create Undead, Animate Dead, Finger of Death), plain "Riding Horse" (Phantom Steed), and the "Monsters" pointer | 30 | unresolved (monsters) |
| "Animals" pointer (Polymorph) | 1 | unresolved (animals) |

No Monster / Animal / MagicItem target is guessed, stubbed, widened or
expanded. "Arrows, bolts" (Wind Wall) is generic prose, not an item pointer.

## Correction: fused scaling labels (component boundary)

Defect: `body_groups` opened a scaling component only when a leaf *began*
with its label. *Giant Insect*, *Ice Storm* and *Wall of Ice* print a line
break then `_Using a Higher-Level Spell Slot._` inside one release leaf, so
their scaling rule stayed inside `effect`: the text was retained, but a
component-selected read or override could not address it as it can for every
other spell.

Fix (generator only; `authoring.py` untouched): each body leaf is cut at a
printed line break that opens a trailing label (`FUSED_TRAILING`), exactly as
a fused descriptor leaf is cut. Both pieces are exact source subspans (the
break is the only character between them, as for descriptors); text, order
and context are unchanged and each passage has one owning component. Effect:
+3 spans, +3 `using_a_higher_level_spell_slot` components, and *Giant
Insect*'s "stat block" glossary reference now sits on its scaling component
(+1 reference, +1 glossary target finding). The drafts are byte-identical.

Matcher-family check (this batch only): every line-break-then-label
occurrence in the 2036 leaves was listed.

| Occurrence | Disposition |
|---|---|
| `_Using a Higher-Level Spell Slot._` in Giant Insect, Ice Storm, Wall of Ice | patched |
| `_Cantrip Upgrade._` after a break | none printed |
| *Wish* option labels / stress after a break | none: every *Wish* body leaf is single-line, so the leaf-start matcher sees each |
| `**Daylight.**` in *Hallow*, `_Turn 4._` in *Storm of Vengeance* | already safe: option labels inside the effect; `body_groups` opens components only for the trailing scaling labels (and *Wish*'s), so these stay in `effect` with their unfused sibling options, as the packet states |

Coverage (`test_a_scaling_rule_fused_into_a_leaf_is_its_own_component`,
production service over the persisted draft): the fused set is exactly those
three; no component text keeps a fused label; a `component_selectors` read of
the three scaling components returns each rule alone; no `effect` passage
still prints it; a COMPONENT `REPLACE` override of each scaling component
reads the authored text in its place while every other passage reads as
printed.

## Helper change (`authoring.py`), this packet's own delta

The file already carries the reviewed uncommitted Classes diff; this packet
adds only (34 changed lines against the pre-packet snapshot):

1. `EntryBatch.scoped_records` — declared records whose edge is
   `SCOPED_WITHIN` in place of `CATALOGUE_MEMBER`; a scoped key that is not a
   declared record raises.
2. `EntryBatch.edges` — `(source, target, kind, entry, text)` edges the entry's
   reviewed text states, cited contextually on that span; an uncited or
   duplicate edge raises. Never inferred from keys.

Both default empty, so every earlier batch derives byte-identically (gate
below). Independent review found no helper blocker for `scoped_records` or
`edges`. `SCOPED_WITHIN` and `SPELL_LIST_MEMBER` are existing
`RelationshipKind`s with existing validation (the latter requires class →
spell); no schema change.

## Owner items and classifications

### Owner-decided: the descriptions are right, the class tables are wrong

Owner decision (`spell-descriptions-source-conflict-owner-decision.md`): "From
my own play experience, I see that the spell descriptions contain the correct
information. The class tables are wrong." This settles the meaning; it is not
publisher text, and the PDF still prints both sides.

| Spell | Description (correct) | Class table (wrong) | Correct AW reading |
|---|---|---|---|
| Flaming Sphere | Level 2 **Conjuration** (p132) | **Evocation** for Druid, Sorcerer, Wizard (pp44, 68, 80) | Conjuration everywhere |
| Mind Spike | names the **Sorcerer** (p149) | Sorcerer table omits it (Warlock p75, Wizard p80 list it) | on the Sorcerer list |
| Phantasmal Force | names **Bard, Sorcerer, Wizard** (p151) | no class table lists it (pp33-34, 68, 80) | on all three lists |

The packet's descriptors and 879 edges already state the correct reading. The
accepted Classes batch's Level 2 tables do not; the correction below is how
they come to agree.

### Class edges from accepted records

The 879 `SPELL_LIST_MEMBER` edges (including the four above) have a
`classes.*` record of the replacement chain as source. This packet changes no
prior record, component, span or identity; accepting the packet is accepting these edges, each cited on its
spell's level line. No consumer expands this kind today.

### Representation limits (source meaning is clear; no schema change here)

Each arm below is `None` in the `SpellDescriptorFact`; the exact printed
descriptor line, retained as governing prose in the same component, states
the meaning:

* *Plant Growth* casting time "Action (Overgrowth) or 8 hours (Enrichment)":
  `SpellCastingTime` holds one time. A representation limit; general casting
  eligibility remains deferred, and no current production evaluator call on
  this arm was identified.
* Mile ranges (*Clairvoyance*, *Meteor Swarm*, *Storm of Vengeance*,
  *Tsunami*: 1 mile; *Project Image*: 500 miles): `RANGED` holds feet.
* "Until dispelled or triggered" (*Glyph of Warding*, *Symbol*).
* "Up to N" without Concentration (*Etherealness*, *Prestidigitation*,
  *Thaumaturgy*).

These are clear source meanings, not Owner decisions. Any future duration /
time / range schema work should be tied to an identified use; none is
implemented here.

### Kept as prose (no field; no identified use)

Reaction and bonus-action triggers (`ActionCost` carries the cost), material
costs (consumption is typed), saves, attacks, damage and scaling (the
`chosen_slot_level` Known Unknown).

## Resolution drafts (unrecorded)

1046 drafts, each an unresolved `srd-5.2.1/spells` pointer of the chain whose
printed text is exactly one spell's name, to that spell's record, with the
span ids the oracle cites it from; ids `resolve-…-spell-descriptions-1`,
unique, none a recorded resolution's pointer. Of the 1061 unresolved spell
pointers, 15 stay unresolved as printed: "Spells" ×13 and
"Casting Spells" ×2 (a part and an accepted section heading, not a spell;
"Casting Spells" was already reachable and is only noted).

## Composition (test-only, in memory)

Over the simulated replacement chain: accept the packet, then record the 1046
drafts.

* Every prior batch, record, span, unit, acceptance and resolution is
  preserved; totals become 18 batches, 947 records, 4826 spans, 645 units,
  1097 resolutions; `reference_resolution_violations` is empty.
* Exactly the 2036 section leaves gain coverage (7657 → 5621 uncovered).
* All 879 class edges validate (their `unknown record classes.*` batch
  findings close), every glossary and equipment target closes.
* 143 findings remain, every one an unresolved reference: the chain's 1157
  less the 1046 drafted, plus the packet's own 32.
* The oracle directory is byte-identical before and after.

## Native consumer (production rules-authority service)

Over one persisted draft of the packet accepted over the simulated chain:

* `spells.spell_descriptions` reaches exactly its 339 spells, in printed order;
* *Barkskin* reads heading, level line, both descriptor leaves, then effect;
* a class does not reach its spells, nor a spell its classes — no consumer
  expands `SPELL_LIST_MEMBER`, as the kind documents;
* *Find Steed* does not read its stat block; the scoped record reads its own
  heading through `bonus_actions`;
* a disabled spell is gone from the section and refused by key;
* the three fused scaling rules are component-selectable and replaceable
  (Correction);
* the four corrected Level 2 class tables read heading then table, in place
  in the whole class, alphabetically, with exactly the descriptions' Level 2
  members and schools; a component `REPLACE` of one leaves every other
  passage as printed, and a disabled class is refused `INVALID_REFERENCE`.

## Owner correction: class spell tables (applied locally, not accepted)

The seven Owner edits (`issue-5d-class-spell-tables-owner-correction.diff`)
are applied to the controlled source, and the release, the seventeen
replacement proposals, their 51 resolution drafts and this packet are
regenerated on it. The consolidated packet, exact hash manifest, full
order-aware comparison against the accepted oracle, expected reds and
boundaries are in `issue-5d-class-spell-tables-REPLACEMENT-REVIEW.md`. This
packet is accepted only after that replacement chain is.

## Gates (uncommitted working tree)

| Gate | Result |
|---|---|
| `pytest tests/ingestion/mechanical/test_spell_descriptions_proposal.py` | 20 tests: 19 passed, 1 failed on a test-only key bug; fixed; `-k corrected` on the final bytes 3 passed |
| Black, Ruff (generator, test) | clean |
| CR check | 0 `\r` in every changed file |
| pip-audit | not run: deferred, non-green (31/11), as standing |

Carried from the pre-correction head (`authoring.py` unchanged since): byte
re-derivation of every earlier proposal built through `authoring.py` (15
passed); mypy `src/` no issues.

## Secrets baseline (scoped maintenance)

Scoped, through the normal staged hook; no `scan --baseline`, no allowlist
pragma. The scanner (the baseline's own plugins and filters) was run over the
seven packet files; this note raises no finding. Every new value was verified
public by recomputing it natively, and every pruned entry was verified
obsolete. Settings, filters, `is_verified` flags, every other file's entries
and key order are preserved.

1. Packet: `4b0bcdd0366c8f7fa2ebdde5b9f7c0e8352f0d0819a9fbf3905f18e186a8fe4e` →
   `34e3bde4488baaa9a8b17c48b18287933017db6ad9cc27911ac979499fd7f21d`:
   277 added (proposal 269, drafts 4, test 4), 0 pruned; entries
   2749 → 3026, files 71 → 74.
2. Correction, from `34e3bde4…fd7f21d`: 2 added (the test's new proposal
   identity and file SHA), 2 pruned (the superseded identity and file SHA:
   their SHA-1s equal the pruned `hashed_secret`s and neither value remains in
   the file), 271 line numbers refreshed (proposal 269, test 2); entries
   3026 → 3026; after `5e357dcb02ce773f21c50d7b68d8921a0dd801a6d21dced7c52342824343fc13`.
3. `detect-secrets-hook` over the seven files and the staged baseline: exit 0
   on consecutive runs, baseline hash stable.
4. Owner correction, from `5e357dcb…4343fc13`: 3 added, all in the new
   `issue-5d-class-spell-tables-owner-correction.diff` (lines 91, 93, 95: the
   upstream, committed and candidate `classes.md` SHA-256s, each recomputed
   natively and SHA-1-matched), 0 pruned, 0 line refreshes; this note raises
   no finding; entries 3026 → 3029, files 74 → 75; after
   `dfe18386ee503b687a826f30552b21507a4d0163ea7e340727dadbd70342ef68`.
   `detect-secrets-hook` over the diff, this note and the staged baseline:
   exit 0 on consecutive runs, baseline hash stable.
5. Replacement packet, from `dfe18386…42ef68` to
   `a91b874db24e9015e4caeafe5b259eb86f56f4df87df8a4f5b8c2cd997017084`: see
   `issue-5d-class-spell-tables-REPLACEMENT-REVIEW.md`.
