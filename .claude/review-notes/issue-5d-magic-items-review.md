# CRD Issue 5d — Magic Items packet, offered for review (#132, #137)

**Superseding status (2026-09-27): ACCEPTED and RECORDED.** The Owner accepted this exact proposal and its
one reference resolution, retaining 315 reference findings and the partial-publication block;
`issue-5d-magic-items-ACCEPT.py` recorded both at 23:27:11Z and 23:28:26Z UTC. See
`issue-5d-magic-items-recorded-followup.md`. The status below is kept as written at review.

**Status: UNACCEPTED proposal plus one unrecorded resolution draft (round 5: shared-item fidelity).**
Nothing is accepted, recorded, committed, pushed, published or activated. `oracles/` is untouched. No
shared DB or Chroma was written. Codex reviews it independently before any exact Owner semantic
acceptance. The contract boundary is settled by Owner Decision 2026-09-27 ("allow one authoritative item
to appear in both Equipment and Magic Items, with consistent replacement and disabling behavior"); that
decision does not accept this proposal or authorize recording.

**Scope.** The whole *Magic Items* part (PDF pp204–253) is one consolidated packet with one native
composition. It covers the general rules (categories, rules, rarity and values, activation, command words,
consumables, spells cast from items, charges, "The Next Dawn", curses, resilience, crafting, sentience and
special purposes) and the full *Magic Items A–Z* catalogue, with every printed item, variant, table,
prerequisite, cost and effect. There is no entry ceiling.

**Authority.** CRD Issue 5d / ADR-005d typed contracts, the Library review and prompting guidance of
2026-09-25 (`Prompting Claude Code to do work for us 2026-09-25.txt`, SHA
`355ce12a85350f28c905534e55e04058db2139fe0b530fdc8c4ef7754537c8c5`), and the recorded Owner
source-fidelity decisions. No accepted material in this part existed before: no accepted record key starts
with `magic_items.`, and no accepted leaf lies in the part.

**Round 2** remediates three source-fidelity defect families from review of round 1:
1. references followed typography, not operative meaning (plain-name dependencies were not read);
2. a direct item read lost the general rules governing it;
3. the Potion of Healing / Spell Scroll overlap was left wholly unresolved.

**Round 3** applies the consolidated governing-context correction (see *Round 3* below):
1. a source-backed applicability matrix for the category, activation and Equipment attunement rules;
2. casting context by operative meaning (*Ioun Stone* in, *Mysterious Deck* out);
3. the A–Z catalogue read now carries governing context owned outside it, once;
4. the handoff's *Cube of Force* / *Cubic Gate* wording corrected.

**Round 3 completion** narrows the casting context to the source leaves that cast: the *Figurine of
Wondrous Power*'s Silver Raven and the *Ioun Stone*'s Reserve are each their own component of the one item
record (see *Round 3*, item 2), and completes the interrupted gates.

**Round 4** implements Owner Decision 2026-09-27 (`magic-items-shared-catalogue-owner-decision.md`): the
basic Potion of Healing and the cantrip/level 1 Spell Scroll are each one record printed by both Equipment
and Magic Items (see *One item in two catalogues*). The live accepted oracle is not edited; the two
accepted records reach the composed authority only through this unaccepted proposal.

**Round 5** completes that decision's consumer fidelity, as implementation within the settled contract (no
new Owner decision): A–Z reads the item's replacement where the family prints it; a direct read carries
the family's governing rules and a balanced table; an edge's placement in a catalogue is checked against
the review inventory. See *Round 5 — shared-item fidelity*.

The 1332-leaf / 55-table source qualification was independently reviewed and is not re-audited here. The
source file is byte-identical to round 1.

## Artifacts (exact hashes)

| File | SHA-256 |
|---|---|
| `issue-5d-magic-items-source.py` (unchanged) | `00d14da69222eacd6b4cddc820d3c86451ba23c9da20d69e716f8c9c3dc23a25` |
| `issue-5d-magic-items-generator.py` | `5b5277b90681ac9b124c397bad9f3c95942dcdbd4b6a1dcf9ead33ff65786152` |
| `issue-5d-magic-items-PROPOSAL.json` (3250184 bytes) | `e0f8c657cd0edebc22f8865a0ffffdf16f6a907d7f7d5cbb70f75a6ddf2ab1d0` |
| `issue-5d-magic-items-resolutions-DRAFTS.json` (unchanged) | `2207ddc3db1fae22f8d65471ee2fbb88d6ed96e55fbe91e313a0bbd59548e23c` |
| `tests/ingestion/mechanical/test_magic_items_proposal.py` | `9b143b1c5a16143c8ed3a698248e484b9f64fe1b036d9dd1dc7596b569a30278` |
| `tests/ingestion/mechanical/test_character_origins_feats_proposal.py` (working tree; unchanged this round) | `c140c253a4c1b657b2bf0f04594f32cde0f967760d5c11fe520b23c50df2a4fb` |
| `src/afterworlds/ingestion/mechanical/authoring.py` (working tree; unchanged this round) | `ab9fc1217247080f6993db64d1f45a479239761b67f52ab0cec25e2785e939cf` |
| `src/afterworlds/ingestion/mechanical/validation.py` (working tree; unchanged this round) | `61a721dc30e2f1300cc3b7d7988f1fbaea6be33a14267965271db63835ba2294` |
| `src/afterworlds/ingestion/mechanical/projection.py` (working tree; round 5) | `c89a68e9763633f369c8a21d9de8833099b703c2a8a549e398e114ff78d2f389` |
| `src/afterworlds/services/rules_authority/application.py` (working tree) | `f52ac7bb7ad649953c331448f0d6d676e5f7c2d9174c8d21e2be1150a7798cc3` |
| `src/afterworlds/services/rules_authority/service.py` (working tree; round 5) | `b08ec606c41c086795d01f5ea054c02bb508144395e6056a400538fb08082cd4` |
| `src/afterworlds/services/rules_authority/views.py` (working tree) | `47b6bc6ade0f07d7592f077ed72ca5081382cb3ce395525fccd010fcd587f6ee` |
| `docs/decisions/adr-005d-complete-typed-mechanical-authority.md` (working tree) | `3d585b03de2b32770d06fbc3f0484a6781f24cdb9f2e2001bbca103f6971bafe` |

- **Proposal identity:** `aecc9ea52a8af77a62a29ee720211489d29d64eece057d9927b754e3934dcc39`
  (round 4: `5edcb225…`, proposal `0f6728eb…`; round 3 completed: `10d30474…`, proposal `34cf9667…`;
  round 3 before completion: `738bdc9d…`; round 2: `7f227027…`; round 1: `7db1bfae…`).
- **Composed over:** `srd-5-2-1-corpus-574662e9-0ef.json`, SHA
  `671f47d706f5eb484c70d8bacaa9d169801c014689d7fd400e018e3d999eae95` (19 batches, 980 records, 5111
  spans, 679 units, 1098 resolutions; findings: 166 refs, 5336 uncovered, 0 other). The generator
  asserts this SHA and fails closed on any other file. It is read only.
- **Generated with** `.claude/_rc/corr/rel/afterworlds.db`. Regenerated after the final Black pass:
  byte-identical. The prior recorder (`issue-5d-gameplay-toolbox-ACCEPT.py --verify`) stays the prefix
  provider; nothing was re-recorded.

**Shared helper change (`authoring.py`).** This round adds to the earlier uncommitted toolbox extension,
which is kept:
- `EntryComponent.context_from`: `(text, printing entry)` pairs, so a `CONTEXTUAL` text is located in
  the exact leaf of the entry that prints and owns it, not searched for in the reading entry. It is
  validated: each printer is an entry of the batch, each pair's text is in `context`, and a
  `context_from` text is never claimed as the reader's own leaf.
- A reference citation also matches its text through `**` markup. This is needed to cite "Giant Goat"
  where the release prints "Giant **Goat**".

Round 3 adds, after them and without changing them, `read_accepted` and `accepted_read_findings` (see
*Round 3*). No schema, no new `RelationshipKind` and no new binding kind. The service change is described
under *Round 3*. The pinned accepted-batch proposal/acceptance tests and `test_oracle.py` pass on the
current helper bytes: 748 passed in five attached groups, each `exit=0` (`pins-g0.log`…`pins-g4.log`, file
lists in `pins-g*.txt`). The earlier single run (`pins.log`) was interrupted at 9% and is superseded.

## Source qualification (before authoring)

This section is unchanged from round 1 and was independently reviewed.

The 1334 release leaves below `# Magic Items` were compared leaf by leaf with the pinned official PDF:
1277/1279 prose leaves and 413/415 table rows across 55 tables match. The four disagreements are
extraction artifacts that lose no meaning, kept byte-exact:
- the header asterisks of *Magic Item Values by Rarity* (`Value*`) and *Time and Cost* (`Time*`, `Cost*`);
- the `<br>` joins in the *Avatar of Death* stat block (leaves 729, 731).

Bounded source disagreements, reported and not corrected:
1. **Heading ownership.** The release prints *Time and Cost* as a sibling of *Crafting Magic Items*, and
   *Sentient Magic Item Traits* and *Special Purpose* as siblings of *Sentient Magic Items*. By their
   meaning they belong inside. Each keeps its own `section` review unit over its own release container,
   and its components are read into the parent record (`READ_INTO`) in printed order. No record, edge or
   membership is added.
2. **Floated tables.** The release floats the four *Sentient Item's …* tables under *Special Purpose*,
   while the trait subsections cite them by name. Each is its own component.
3. **Part intro.** The `# Magic Items` heading and its intro paragraph (leaves 3055/3056) stay uncovered.
   Shared part coverage is Owner-deferred until after 5d.

## Grain and representation

**270 records and 271 review units.**
- 10 `general_rule` section records, in printed order.
- 258 `magic_item` records, each a `CATALOGUE_MEMBER` of `magic_items.magic_items_a_z`, in printed order.
- 2 `creature` stat-block records, `SCOPED_WITHIN` their item (*Figurine of Wondrous Power* → *Giant
  Fly*; *Mysterious Deck* → *Avatar of Death*). `SCOPED_WITHIN` is used as before, not reinterpreted.

The build has:
- 1332 leaves and spans;
- 304 components, all prose-bound, with 0 facts: one per record, plus the *Figurine*'s `silver_raven`
  and the *Ioun Stone*'s `reserve` and `ioun_stone_after_reserve` (see *Round 3*, item 2);
- 2169 bindings: 1332 `PRIMARY` (one per leaf), 277 in-batch `CONTEXTUAL` and 560 cross-batch
  `CONTEXTUAL` (140 attuned items × 4 accepted Equipment rules);
- 1278 references;
- 3875 provenance claims (1332 primary, 2543 contextual).

Partition and review-unit checks report 0 findings. The representation check reports 2923 findings, all
expected and enumerated by the generator: accepted targets the packet alone cannot see, the unresolved
references below, and 3 per cross-batch read (1680), which all vanish on composition.

**Rarity, attunement and charges stay faithful prose (ADR-005d Decision 4).** No code-owned consumer of
typed rarity, attunement or charges is identified. A hypothetical magic-item schema is not a present
acceptance blocker, and none is invented.

**GM latitude** is unchanged from round 1: 19 `LATITUDE` rows pinned to their delegating words, and 16
reducible `NOT_LATITUDE` rows.

## Defect 1 — references by operative meaning

A name an effect depends on is now read whatever its typography:
- a cast-spell table cell;
- a rolled-creature table cell;
- a spell or creature the item's effect produces.

Examples and category labels are not read. Spells resolve to the exact accepted `spells.*` record, and
every target was verified to exist. Absent creatures stay explicit unresolved named references in
`srd-5.2.1/monsters` scope. There is no Monster/Animal authoring and no broad fallback. `PLAIN` declares
the reads per component, and the generator asserts that each printed name occurs as a whole word in that
component's own texts.

| Item / component | Now read |
|---|---|
| *Wand of Wonder* | 11 spells (incl. *Fireball*, *Greater Restoration*, *Enlarge/Reduce* → `spells.enlarge_reduce`, *Darkness* → `spells.darkness`, replacing the glossary "Darkness" the cell does not mean); 6 creatures |
| *Dragon Orb* | 5 cast-spell table spells |
| *Necklace of Prayer Beads* | 6 bead spells |
| *Efreeti Bottle* | *Wish* → `spells.wish` |
| *Cube of Force* | 6 spells (*Mage Armor*, *Shield*, *Tiny Hut*, *Private Sanctum*, *Resilient Sphere*, *Wall of Force*) |
| *Cubic Gate* | 2 spells (*Gate*, *Plane Shift*) |
| *Bag of Tricks* | the 24 rolled creatures (the Gray/Rust/Tan tables) |
| *Deck of Illusions* | the 32 illusion creatures (table cells, "The card drawer" excluded) |
| *Robe of Useful Items* | Riding Horse, Mastiffs (the Riding Saddle is equipment, not a creature) |
| *Bag of Beans* | Treant, Shrieker Fungi, Bulette, Mummy, Mummy Lord |
| *Bowl* / *Brazier* / *Censer* of controlling elementals; *Elemental Gem* | their elementals (1 / 1 / 1 / 4) |
| *Manual of Golems* | the 4 golems |
| *Pipes of the Sewers*; *Cloak of the Bat* | Swarm of Rats; Bat |
| `magic_item_categories` / `potions` | "see Poison in Gameplay Toolbox" → exact accepted `gameplay_toolbox.poison`; *Dispel Magic* → `spells.dispel_magic`; Potion of Invisibility → `magic_items.potion_of_invisibility` |

**Giant Goat.** The whole printed name is read where the bold covers only part of it
(`BOLD_PREFIXES = {"Goat": "Giant "}`, with an assertion that the prefix is printed). Both *Goat of Travail*
and *Goat of Terror* now cite "Giant Goat" through the `**`-insensitive citation. The source bytes are
unchanged, and no bare "Goat" reference remains from the goats. The one remaining monsters "Goat" is the
*Bag of Tricks* table cell "Goat", which is a different creature.

**Scope note.** Accepted classes reference Rat and Riding Horse under `srd-5.2.1/animals`. This packet
uses `srd-5.2.1/monsters`, per the part's own statement ("Unless the text states otherwise, the stat block
is in 'Monsters'"). A future resolution picks the exact destination. Nothing is guessed here.

**Tests.** The round-1 assertions that codified the omissions (*Fireball* not read, and the like) are
replaced. `test_plain_names_an_effect_depends_on_are_read` pins the concrete reads above.
`test_giant_goat_is_read_by_its_whole_printed_name` pins the Travail leaf cited, 2 cited spans, and no bare
goat reference. The set of monster names referenced is pinned exactly to the bold names, the declared
plain names and the "Monsters" pointer.

**Sibling audit** (defect family: operative name not read because of typography; bounded to the current
Magic Items operative tables and effects; stopped there).
- Trigger: the review's confirmed omissions.
- Method: a scan of every component's own texts against every accepted spell name, and against the
  release's Monsters A–Z / Animals container labels. Each hit was reviewed by phrase.

| Hit | Disposition |
|---|---|
| The confirmed items above, plus Cube of Force, Cubic Gate, Bag of Beans, the elemental items, Manual of Golems, Pipes, Cloak of the Bat and Deck of Illusions | patched |
| Light, Fly, Divination, Symbol, Bane as plain words; Shield/Invisibility in the categories table; "Invisibility" inside "Potion of Invisibility" | already safe: English words, category examples or part of a longer read name, matched by the whole-word/phrase review above, not a spell dependency |
| "Fungi" inside "Shrieker Fungi"; "Animals" inside spell names; Druid (a class); Mage; Ogre (*Gauntlets of Ogre Power*); Crab | already safe: a substring of a read name, a class, or an item name, not a creature the effect produces |
| Magic Item Categories table example names | already safe: examples, not dependencies |
| Accepted records outside this part | out of scope (not rewritten) |

## Defect 2 — governing context on direct item reads

An item's component now also reads, as `CONTEXTUAL` and in source order before the item's own text, the
exact general-rule leaves that govern it. Each leaf is bound to the span that its section's component owns
(`PRIMARY`). Nothing is copied, no rules are duplicated as primary, and no whole section is used as
context.

| Rule (owner) | Read by | Count |
|---|---|---|
| *Attunement Prerequisites* paragraph (`magic_item_rules`), which says a spell from a magic item does not qualify | items whose type line requires attunement by a class or a Spellcaster (derived from the type line; not the Belt of Dwarvenkind's creature prerequisite) | 20 |
| *Command Word* (`activating_a_magic_item`), which says a spoken word fails where sound is suppressed | every item printing "command word", asserted equal to the declared list | 10 |
| *Spells Cast from Items*, first paragraph (`activating_a_magic_item`): no slot, no components, normal casting time, range and duration, Concentration, unless the item says otherwise | items whose bearer casts a spell from them (declared by operative meaning; round 3 adds *Ioun Stone* and removes *Mysterious Deck*; for *Figurine* and *Ioun Stone* it governs only the casting variant's component, see *Round 3*) | 60 |
| *Spells Cast from Items*, second paragraph (own spellcasting ability) | those of the 60 that cast with the user's own ability (staffs, *Spell Scroll*, *Hat of Many Spells*, *Necklace of Prayer Beads*) | 11 |

**Proved through the production rules-authority service** (private DB copy):
- `test_an_item_read_directly_carries_the_rules_governing_it`:
  - *Wand of Fireballs* reads `[PREREQUISITES, CAST_FROM_ITEMS, *own]`. The spans' owners are
    `magic_item_rules` and `activating_a_magic_item/spells_cast_from_items`.
  - *Broom of Flying* reads *Command Word* first.
  - *Staff of Fire* starts `[PREREQUISITES, CAST_FROM_ITEMS, OWN_ABILITY]`.
  - *Bag of Holding* reads only itself.
- `test_suppressing_a_governing_rule_suppresses_it_on_the_item`:
  - A component DISABLE of `spells_cast_from_items` leaves Fireballs `[PREREQUISITES, *own]`.
  - Adding a REPLACE of `magic_item_rules` leaves only `own`.
  - A record DISABLE of `magic_item_rules` leaves `[CAST_FROM_ITEMS, *own]`.
  - This works through the native `_without_suppressed_context`.
- Round 2's `test_the_catalogue_does_not_repeat_the_rules_its_items_read`, which codified a catalogue
  read carrying none of the context, is replaced in round 3 (see *Round 3*, item 3).

**Round-2 sibling disposition, superseded.** Round 2 held the per-category, *Charges* and *Consumable
Items* rules back as an Owner decision. Round 3's governing-context correction settles them as source
applicability, not as Owner decisions, and binds each only where the source makes it apply (matrix below).

## Defect 3 — Potion of Healing / Spell Scroll: one effective identity

Findings:
- Accepted *Equipment* holds the basic potion, `equipment.adventuring_gear.potion_of_healing` (2d4 + 2).
  It also holds the cantrip/level-1 scroll subset and `equipment.scribing_spell_scrolls`.
- This packet adds the wider families `magic_items.potions_of_healing` (a four-row table whose first row
  is exactly "Potion of Healing … 2d4 + 2") and `magic_items.spell_scroll` (levels 0–9).

**Resolution, no replacement candidate needed.** `SHARED` routes each unqualified name to the one record
that is that item:
- An unqualified "Potion(s) of Healing" → the accepted equipment potion (the same 2d4 + 2 item). The
  "(greater)/(superior)/(supreme)" variants are excluded by the pattern and read as the family.
- An unqualified "Spell Scroll(s)" → `magic_items.spell_scroll`. Magic Items never names the equipment's
  cantrip/level-1 subset, so an unqualified scroll here is the family.
- The quoted "Scribing Spell Scrolls" stays a pointer to the accepted `equipment.scribing_spell_scrolls`.
- An item naming itself is not a reference.

Result: magic-items-scope unresolved references drop from 12 to 0. No accepted Equipment record, identity,
approval or resolution changed. No carryforward or alias authority was built. Pinned by
`test_potion_of_healing_and_spell_scroll_keep_one_identity`.

**Remaining identity boundary — resolved in round 4.** Round 3 left the family table's own rows for the
basic potion (and, on re-reading the source, the scroll family's "Cantrip" and "1" rows, which print the
equipment scroll's subset) inside the family, so an Equipment override did not reach them. Owner Decision
2026-09-27 settles it; see *One item in two catalogues*. The family's own "Potion of Healing" reference
(its row naming the item) is gone, because the row is now that item's own authority.

## Round 3 — governing context, casting, catalogue read

### 1. Applicability matrix (direct reads)

Each rule is bound as `CONTEXTUAL` only to the items the source makes it govern, at leaf grain, in source
order ahead of the item's own text. No rule text is copied, no whole section is used as context, and an
item's own words stay its authority. A rule is not bound because many items happen to match a keyword.

| Rule (exact leaf; owner) | Source basis for applicability | Read by | Count |
|---|---|---|---|
| *Potions* — "_Using a Potion._ … requires a Bonus Action … it is used up" (`magic_item_categories`) | the category's own rule for every item of it | every *Potion*-category item (oils included; the leaf itself defers oil timing to the item) | 24 |
| *Rings* — "must be worn on a finger … unless its description notes otherwise" | category rule | every *Ring* | 22 |
| *Scrolls* — "_Using a Scroll_. … requires the user to read the scroll … can't be used again" | category rule | *Spell Scroll* (the only Scroll) | 1 |
| *Staffs* — "Unless its description notes otherwise, a staff can be used as a nonmagical Quarterstaff and an Arcane Focus" | category default | every *Staff* | 12 |
| *Wands* — "… a wand can be used as an Arcane Focus" | category default | every *Wand* | 13 |
| *Rods* — "… a rod can be used as an Arcane Focus" | category default | every *Rod* | 7 |
| *Armor* — "An item in the Armor category …" | category rule | every *Armor* item | 19 |
| *Consumable Items* — "Once used, a consumable item loses its magic" (`activating_a_magic_item`) | the category rules call potions and scrolls consumable; two items say they are consumed | 24 potions, *Spell Scroll*, *Dust of Disappearance* ("the dust is consumed"), *Manual of Golems* ("the book is consumed") | 27 |
| *Charges* — Identify reveals the remaining charges; the attuned creature knows them (`activating_a_magic_item`) | the item prints a number of charges (`\d+(d\d+)? charges`; *Luck Blade* prints "1d3 charges") | every charged item, asserted | 51 |
| Round-2 rules (*Attunement Prerequisites*, *Command Word*, *Spells Cast from Items* ×2) | unchanged, see Defect 2 | — | 20 / 10 / 60 / 11 |
| Accepted `equipment.magic_items` — *Attunement*, *Attune during a Short Rest*, *No More Than Three Items*, *Ending Attunement* | the item's type line prints "Requires Attunement" | the 140 attuned items | 4 × 140 |

**Item exceptions preserved (not rewritten).**
- **Staffs.** Six staffs (*Power*, *Striking*, *the Magi*, *the Woodlands*, *Thunder and Lightning*,
  *Withering*) print themselves a *magic* Quarterstaff. The staff leaf is one sentence whose own
  "unless its description notes otherwise" hands that point to the item; the Arcane Focus default still
  applies. The leaf is bound; the item's own text, read after it, governs the Quarterstaff point. No
  sub-leaf split is invented.
- **Scroll readability — not bound.** "Any creature that can understand a written language can read a
  scroll … unless its description notes otherwise" is the default; the only Scroll, *Spell Scroll*, notes
  otherwise ("If the spell is on your spell list, you can read the scroll … Otherwise, the scroll is
  unintelligible"). The exception governs, so the default is not read into it.
- **Consumed by own words.** An item that states its own end (a *Feather Token* disappears, a *Mysterious
  Deck* card vanishes) is read by its own words; *Consumable Items* is not added by keyword.

**Deliberately not read.** What a category merely describes (a rod's weight, a potion's typical volume);
*Mixing Potions* and the Potion Miscibility table (they apply only when potions are combined, not to each
potion's use); the armor/weapon type choice and *Ammunition* (they turn on a type the item may leave
open).

**Cross-batch Equipment context.** *Magic Item Rules* says "Rules for identifying, attuning to, and using
magic items appear in 'Equipment'". That qualified pointer now resolves precisely to the accepted
`equipment.magic_items` (`QUALIFIED` in the generator; equipment-scope unresolved 42 → 41). The seven other
bare "Equipment" pointers stay unresolved. The four attunement leaves are read in place from the accepted
batch that owns them:
- **Representable at contract level.** `authoring.read_accepted` copies the accepted binding under the
  reader's record/component keys and reasons, with a `CONTEXTUAL` provenance claim; it refuses a reader
  without a component-wide binding, an unaccepted owner, or a span this proposal proposes.
- **Findings.** Standalone, each copy yields 3 expected findings (the span is unknown to the packet alone);
  `accepted_read_findings` enumerates them (1680), and the composition test proves all of them vanish.
- **Not bound.** Identifying, wearing and wielding, and multiple/paired items are reached through the
  resolved pointer; they are not bound as context. Accepted Equipment is not mutated.

### 2. Casting context by operative meaning

| Item | Disposition |
|---|---|
| *Ioun Stone* | **added, Reserve only**: the Reserve says "you can cast any spell stored in it", like the already-included *Ring of Spell Storing*. Its three leaves are the `reserve` component; the other stones are not governed |
| *Mysterious Deck* | **removed**: the Moon grants future *Wish* casts and the card vanishes; nothing is cast from the deck |
| *Figurine of Wondrous Power* | **kept, Silver Raven only**: the Raven grants *Animal Messenger* in raven form; its one leaf is the `silver_raven` component. The other figurines transform creatures and are not governed |

**Casting variant components (round 3 completion).** The native path already supports this:
`Chunk.section` binds a keyed subset of an entry's leaves, and a record may hold several components
(the general-rule sections already do). `CASTING_VARIANTS` in the generator names each casting variant
and its leaf count; `item_components` locates its unique leaf and splits the item's leaves, in printed
order, into:

| Item | Components (leaves) | Context |
|---|---|---|
| *Figurine of Wondrous Power* | `figurine_of_wondrous_power` (17), `silver_raven` (1) | *Charges* on the item's own key; *Spells Cast from Items* on `silver_raven` alone |
| *Ioun Stone* | `ioun_stone` (17), `reserve` (3), `ioun_stone_after_reserve` (2: Strength, Sustenance) | attunement (cross-batch) on the item's own key; *Spells Cast from Items* on `reserve` alone |

- It is still one record, one `CATALOGUE_MEMBER`, read whole in printed order. Cross-batch attunement
  stays on the item's own key, and the Reserve's GM latitude row moves to `reserve`.
- No other variant is split, and no other variant's text is bound to casting context. Every other item
  is one component (asserted).
- The generator asserts the variant's leaves say "cast" and that the next leaf opens the next variant.

`test_casting_context_governs_the_casting_variant_alone` (both items), through the production service:
- one record, every printed leaf in order;
- *Spells Cast from Items* read once, immediately ahead of the variant's leaves;
- no other component carries it, and the variant carries nothing else;
- disabling the variant component drops its leaves and the rule only;
- disabling `spells_cast_from_items` drops the rule and keeps every leaf.

It replaces the round-3 assertions of whole-item casting context for these two items.

### 3. The A–Z catalogue read carries external governing context

`application.py` skipped context owned outside the read record on the assumption that its owner reads it
in place. For Magic Items the rules and category owners (and Equipment) are outside the A–Z catalogue, so
a catalogue read dropped them.

- **Fix.** `EffectiveAuthority.context_owners` records `(span, owner record, owner component)`. `_readings`
  places context owned outside the catalogue once, at the first member that reads it, ahead of that
  member's own passages. The `build_gamemaster_view` dedup shows context at its owner when the owner is
  selected, otherwise once at its first reader.
- **Overrides.** DISABLE or REPLACE of an owner suppresses the context in every reader; the replacement
  text stays with its owner and is not carried into readers.
- **Equipment unchanged.** An owner inside the read section still reads its context in place.
- **Tests.** `test_governing_context_is_read_once_by_its_owner_or_first_reader` (replacing the test that
  codified the missing context) covers a direct item, the catalogue alone, combined selections
  (*Fireballs* + *Lightning Bolts*, deduped by span id), selected and unselected owners (`RULES`,
  `EQUIPMENT_RULES` + catalogue). The suppression test adds DISABLE of Equipment `attunement` and REPLACE
  of `ending_attunement` (the owner shows the replacement; the catalogue drops the span).

### 4. Preserved

The independently reviewed plain-name reference fixes, source bytes, accepted identities and approvals
are unchanged. No broad re-audit, recursive external catalogue expansion or schema work.

## One item in two catalogues (round 4, Owner Decision 2026-09-27)

**Representation (smallest native form).** No new relationship kind, schema, alias or carryforward.
- `equipment.adventuring_gear.potion_of_healing` and `equipment.adventuring_gear.spell_scroll` are
  declared in this batch byte-identical to the accepted records (kind `EQUIPMENT`). Each gains one
  component, `magic_items_table`: the rows that are the item (PRIMARY) — "Potion of Healing" (2d4 + 2,
  Common); "Cantrip" and "1" for the scroll — read with what governs them (CONTEXTUAL; round 5 widened
  this from the table head alone, see *Round 5*). Each also gains a
  `CATALOGUE_MEMBER` edge to its family, cited on its first owned row. `acceptance.py`'s keyed union
  keeps the identical record and adds the disjoint component and edge; the accepted
  `CATALOGUE_MEMBER` edge to `equipment.adventuring_gear` is unchanged.
- The families `magic_items.potions_of_healing` and `magic_items.spell_scroll` stay their own records.
  Their table is cut, byte for byte, into head / shared rows / the rest / close (the close its own piece
  since round 5). They keep the head, the
  greater/superior/supreme and level 2–9 rows, prices and every shared rule (the scroll's casting,
  save DC and attack rules) as PRIMARY, and read the shared rows in place as CONTEXTUAL. Nothing wider is
  collapsed into the Equipment subset, and nothing of the subset is left with two PRIMARY owners.
- Membership is declared by the generator's `SHARED_ROWS` (family name → record, the rows' first cells),
  never by key prefix. No recursive catalogue expansion: a section reaches its members one hop.

**Validation (`validation.catalogue_parts`, reconciling ADR-005d's second-parent refusal).** A member of
more than one catalogue must say which catalogue prints which of its components. Each edge's
`RELATIONSHIP` provenance must cite spans the member's own components own as PRIMARY. The components
owning them are that catalogue's part. Every span-owning component is in exactly one part; a component
with no source span belongs to every catalogue. It refuses:
- an edge citing no span of the member's own components ("cites no span of its own components");
- a component two edges name ("printed by both");
- a span-owning component no edge names ("printed by none of its catalogues");
- any membership cycle ("a catalogue member of itself").

At runtime `application.py` recomputes the parts and raises `PersistedStateReconstructionError`
(`STALE`) when persisted parts no longer satisfy the rule. `authoring.py`'s "section … rereads … owned
by …" check now ignores the section's CONTEXTUAL reads, so a family may read the item's rows as context
and still may not bind them as its own (`test_equipment_proposal.py`'s refusal still passes).

**Consumer (production service).**
- `_readings`: a section reaches a multi-catalogue member only for the components that section prints.
  Context owned outside the reading component is now placed immediately ahead of the next passage that
  component prints, not at the component's anchor. Before this fix, the family's own table head sorted
  after the family's passages, because the anchor of the section itself is `(1, 0, 0)`.
  Since round 5 it also reaches, one hop through a member, the parts that member declares it prints
  (A–Z → family → the item's `magic_items_table`).
- `build_gamemaster_view`: the guard against a second reading is per (record, component). A covered
  member's components that no selected catalogue prints are read once, after the selected catalogues'
  readings, in the order they list their members.

| Selection | Reads (as of round 5) |
|---|---|
| the item directly | Equipment component, then `magic_items_table`: the family's governing rules, type line and rule paragraphs, and the table head, its rows and close, in printed order |
| the family | its context rules, its table with the shared rows in place (attributed to the item's `magic_items_table`), its rules; then the item's Equipment component at the item's place |
| `equipment.adventuring_gear` | Equipment as accepted; after it, in the order Equipment lists them, each shared item's `magic_items_table` as read directly (a rule both items share is read once) |
| Adventuring Gear + a family | each component once: Equipment rows in Equipment, the family's rows in the family, the other item's family rows after Equipment's reading |
| *Magic Items A–Z* | the whole catalogue; the shared rows read in place as the item's `magic_items_table` (one hop through the family); the slice holds each shared item narrowed to that component |

**Overrides (tested for both items).** Targets are the one record and its components (Decision 10):
- DISABLE the record: gone from both catalogues and A–Z with its rows; every other variant row and rule
  stays; a direct read is `INVALID_REFERENCE`.
- DISABLE `magic_items_table`: its rows leave the family, A–Z and the Adventuring Gear read; the
  Equipment component stays.
- DISABLE the Equipment component: the family and A–Z read unchanged.
- REPLACE `magic_items_table` ("House rows."): the family, A–Z, the direct read, Adventuring Gear and
  Adventuring Gear + family each read the authored text once, as the item's, where the rows were printed
  (round 4's A–Z drop is corrected in round 5).
- DISABLE the family, or REPLACE its reading: the family's head, close and paragraphs leave the item's
  read; the item keeps its rows and the rules owned elsewhere.
- DISABLE the governing category rule (`magic_items.magic_item_categories` `potions` / `scrolls`): only
  the rule is dropped, from the family read and from the item's direct read.
- REPLACE an unrelated variant (the other family's reading): the item's read is unchanged.

**Tests** (`test_magic_items_proposal.py`):
- `test_an_item_equipment_sells_is_one_record_in_both_catalogues` (×2);
- `test_membership_in_two_catalogues_is_declared_never_guessed` — the four refusals above on mutated
  drafts;
- `test_each_catalogue_reads_the_shared_item_once_in_printed_order` (×2) — direct, family, Adventuring
  Gear, combined, A–Z;
- `test_overrides_of_the_shared_item_hold_from_either_catalogue` (×2).

Pins changed accordingly: scope, record kinds (+2 `EQUIPMENT`), members, subheadings, one-identity
(the family no longer cites "Potion of Healing") and composition. `test_character_origins_feats_proposal.py`'s
second-parent refusal becomes `test_a_second_catalogue_citing_nothing_of_the_record_is_refused` and
expects the new findings.

**ADR.** ADR-005d is amended in place: Decision 3's one-record note, the schema-16 second-parent
refusal, and a new "Amended by Owner Decision 2026-09-27" block under Decision 9.

## Round 5 — shared-item fidelity (within Owner Decision 2026-09-27)

One defect family: how the shared item is presented, what context it carries, and where it may be placed.
The four defects were fixed together.

**1. A–Z REPLACE consistency: patched.** Round 4 had A–Z read the shared rows as the family's context,
so an owner REPLACE (which suppresses the span in readers) dropped them with no House rows. Round 4's test
encoded that. Now `application._readings` also anchors a member's member (one hop, never recursive), but
only where that member declares, through `catalogue_parts`, that it prints them. It reads only those
declared components, at the member's printed place. `service._select` adds those components (narrowed)
to the section's slice. `views.build_gamemaster_view` counts the records a non-reached section reads as
covered. No PRIMARY authority is copied and no unrelated catalogue is expanded. The test now asserts:
- the House rows at the rows' place in the family, A–Z, the direct read, Adventuring Gear and the combined
  read;
- DISABLE, the other variants, printed order and dedup, which are preserved.

**2. Direct governing context: patched.** `magic_items_table` now reads, as CONTEXTUAL, what governs the
rows:
- the rules a direct family read carries (`item_context`: the category, activation and casting rules,
  owned where printed);
- the family's type line;
- every paragraph that states a rule the rows are subject to (the generator's `SHARED_FAMILY_TEXTS`,
  asserted to be found).

For the scroll, those paragraphs are: the scroll is not lost when a casting is interrupted (source
paragraph 7590); the check to cast a spell of a higher level, with the scroll lost on a failure (7597);
the level that sets the save DC and attack bonus; and copying a Wizard spell (7618). For the potion, it is
"You regain Hit Points…".

The potion's "red liquid glimmers" is description that rules nothing, so it is not read. The test pins
this: it is the only family text left out.

Owner suppression holds:
- a disabled category rule leaves the item's read;
- a disabled or replaced family takes its own paragraphs, head and close with it;
- an unrelated variant replaced changes nothing.

**3. Table completeness: patched.** Round 4 left the table's closing `</tbody></table>` inside the
family's residual piece, so a direct read opened a table it never closed. The generator's `closer_of`
checks that the source table ends with the close and cuts it as its own span. The family owns it
(PRIMARY) and the item reads it (CONTEXTUAL). No text is synthesized and no unrelated row is imported.

The test checks:
- the rendered direct read is balanced (`<table>`…`</table>`, as many `<tr>` as `</tr>`, head + rows);
- the family's cut rejoins byte for byte, close last, with each piece one PRIMARY owner;
- the greater/superior/supreme and level 2–9 rows stay the family's.

**4. Placement: patched, after seams were inspected.** `catalogue_parts` checks each edge against the
member's own spans; it does not check the catalogue. The negative evidence is empirical for
`validate_candidate`, which runs `catalogue_parts`, the relationship checks and `review_unit_violations`.
It is by code reference for the other three seams: acceptance, oracle load and authoring each call
`review_unit_violations` or `catalogue_parts` and add no placement check of their own. No separate probe
was run on them.

The probe (`.claude/_sp/mi/r5/seams.py` → `seams.log`) moved the potion's edge, citing the same span, to
Crafting, to a class feature and to the other family, and moved its Equipment edge to a class feature.
Each move gave 0 new `validate_candidate` findings against a base of 4197.

The fix is in `projection.review_unit_violations` (`_catalogue_placement_violations`). It applies to each
member of more than one catalogue. Every span an edge cites must lie in a leaf that a review unit reviews
while expecting a rule of that section. That is review-backed and source-backed. It uses no key prefix
and no special name, and it does not broaden the approved ownership.

After the fix (`seams2.log`), each probe gave exactly one new `validate_candidate` finding. By code
reference, the same function also runs at acceptance (`acceptance.py:628`), oracle load
(`oracle.py:1690`) and authoring (`authoring.py:929`).

The test `test_a_shared_item_is_placed_only_where_review_found_it_printed` covers the same four moves. It
asserts one finding each, and that the finding reaches `validate_candidate`. The containment, release
and provenance checks are unchanged, and the unmutated composition has no placement finding.

**Supplemental-tail layout.** This was not made an Owner question. Equipment keeps its local order, and
what it does not print reads after its reading. The ADR and the table above now describe that read as it
is.

**ADR-005d.** The Decision 9 amendment was reconciled with the final paths:
- the direct read's governing context and the table close;
- the new **Placement** bullet;
- the **Consumer** one-hop A–Z read and slice narrowing;
- the read of what no selected catalogue prints;
- REPLACE across every view.

## References (1277; round 3: 1278)

| Kind | Count |
|---|---|
| to exact accepted records | 1086 (glossary 842, spells 205, equipment 38, gameplay toolbox 1) |
| intra-packet (italic items, printed variants, `SHARED` Spell Scroll) | 35 |
| intra-packet to the Potion of Healing record this batch now declares | 6 |
| unresolved, equipment scope (priced without a record, plus the bare "Equipment" pointers) | 41 |
| unresolved, monsters scope (named creatures and the "Monsters" pointer) | 109 |
| unresolved, magic-items scope | 0 |

Equipment 45 → 38 + 6: the potion's seven references were to an accepted record and now name the same
record declared in this batch (targets unchanged); the family's own row reference is dropped (−1).
Glossary is 843 → 842 (round 3) because the *Wand of Wonder* "Darkness" now resolves to the spell.

**Generator delta vs round 3** (`gen2.log`; a second run is byte-identical): spans +5 (1332 → 1337, the
cut table pieces), records +2 (270 → 272), components +2 (304 → 306), bindings +10, references −1,
provenance +11, units and leaves unchanged. Standalone findings 2923 → 2916: exactly the seven
"unknown target record equipment.adventuring_gear.potion_of_healing" findings, now in-batch.

**Generator delta vs round 4** (`r5/pdelta.py` → `pdelta.log`, against the round-4 snapshot
`r5/PROPOSAL-r4.json`):
- Spans 1337 → 1339 (+4 / −2). Each family's residual piece `[226, 572)` / `[352, 1138)` is split at its
  table close (`[553, 572)` / `[1119, 1138)`). No text was added.
- Prose bindings 2179 → 2196, and provenance 3886 → 3903 (+19 / −2 each). The two families re-bind the
  split pieces as PRIMARY, and the two items' `magic_items_table` gain their CONTEXTUAL reads.
- Review units: 271, of which 2 are re-cited for the split spans. Records, components, relationships and
  references are unchanged.
- Drafts are byte-identical.
- Regeneration after the final Black pass is byte-identical (`gen3.log`).

**Resolution draft (unrecorded), unchanged:**
`resolve-gameplay-toolbox-travel-pace-special-movement-carpet-of-flying-magic-items-1`
maps "Carpet of Flying" → `magic_items.carpet_of_flying`. The accepted "Magic Items" part pointers stay
unresolved.

## Native outcomes (test only, in memory)

**Accept then resolve** (`accept_proposal` → `resolve_references`):

| | Before | After |
|---|---|---|
| Batches / records / spans / units / resolutions | 19 / 980 / 5111 / 679 / 1098 | 20 / 1250 / 6450 / 950 / 1099 |
| Uncovered leaves | 5336 | 4004 (exactly the 1332 cleared) |
| Reference findings | 166 | 315 = 166 − 1 drafted + 150 packet-own, all unresolved |

Records stay 1250 (980 + 270 new): the two shared records are the accepted ones, merged by key. Spans
are 6450 (round 4: 6448; round 3: 6443). Refs 315, uncovered 4004 and 0 other are unchanged from round 4
(pinned in the composition test, which passes).

- `REPLACEMENT._preserved`, with `obligations` compared separately, finds no dropped or changed accepted
  byte, identity, approval, resolution or time. The first 19 batches are identical, and `oracles/` is
  byte-identical before and after. The two shared records compose equal to the accepted records, with
  components `[their accepted key, magic_items_table]`.
- **Derived obligations delta (pinned exactly).** Only the two shared records' `RecordObligation`s
  change: `prose_bound_components` grows from `{accepted key}` to `{accepted key, magic_items_table}`. It
  is derived from the added component, not an edit of accepted authority, and the test asserts that no
  other obligation changes.
- 0 other findings; the 1680 cross-batch read findings are gone once composed.

**Service consumer behaviour** (unchanged from round 1 and still passing):
- The catalogue reaches its 258 items once, in printed order; since round 5 its slice also holds the
  two shared items, each narrowed to `magic_items_table`.
- A disabled item is gone, and a replaced item reads replaced in place.
- The read-into sections read in printed order.
- A stat block is its own scoped record.

## Gates (round 5; raw, attached, each to its actual exit status)

Logs are in `.claude/_sp/mi/r5/`, and each one opens with its command line. The `final-*` runs began
after the last source edit.

| Gate | Result |
|---|---|
| Generator regeneration (`venv\Scripts\python.exe .claude\review-notes\issue-5d-magic-items-generator.py .claude/_rc/corr/rel/afterworlds.db`) | proposal `e0f8c657…` / identity `aecc9ea5…`; drafts `2207ddc3…` unchanged. After Black it is byte-identical, `exit=0` (`gen3.log`) |
| `test_magic_items_proposal.py`, 33 tests in three node-id groups | `final-gA` 13 passed (191.9 s); `final-gB` 16 passed (463.0 s); `final-gC` 4 passed (524.0 s). After a mypy-only `is not None` guard, `final-gC2` reran the 2 changed tests: 2 passed (287.8 s). Each run `exit=0` |
| `tests/services/rules_authority/`, `test_review_units.py`, `test_projection.py`, `test_runtime_production_release.py`, `test_equipment_proposal.py`, `test_quarantine_5c_5d.py` | 660 passed, 6 skipped, `exit=0` (`final-dep1.log`) |
| `test_character_origins_feats_proposal.py` | 71 passed, `exit=0` (`final-cof.log`) |
| Black `--check`, Ruff (the four changed `src/` files, the MI test, the generator) | clean. Black reformatted four of those files after the first runs; the tests and the generator above were rerun on the formatted bytes |
| `mypy src/` | `Success`, 235 files, `exit=0` (`mypy.log`) |
| `mypy src/ <source> <generator> <MI test>` (238 files, round-4 scope) | only the 3 pre-existing errors in the imported `test_character_origins_feats_proposal.py` (lines 888, 1755, 1759), `exit=1` (`mypy3.log`). mypy is not green at this scope |

- **Failures along the way (all resolved).**
  - The first full MI run (backgrounded, not counted as a gate) had 4 failures in the new read tests.
    The cause was a test helper that deduplicated by text. The two tables' closes are the same text on
    different spans, so it dropped the second close, and it also deduplicated the other item's rules in
    the combined and disabled views. The helper now deduplicates only the shared rules (`t3`/`t4`). A
    span-count pin moved from 1337 to 1339.
  - mypy flagged two name rebinds introduced this round (`at`, `chosen`); both were renamed.
- **Not run:** no full or near-full suite, and no unchanged broad accepted-batch pins. The new placement
  check fires only for a member of more than one catalogue. The accepted oracle has none: 754
  `catalogue_member` edges, each from a distinct record. The oracle-load and runtime-release tests above
  pass. pip-audit stays
  deferred and non-green. Nothing here is an all-green claim.

## Secrets baseline (scoped, round 5)

| | |
|---|---|
| Before | `bd49f0e8787a87b7d3c044ae0bd469bc8fb6aaaec9e0ed5149616a5a6eb4830f` (round 4's staged result; index = worktree, asserted by the apply script before writing; copy `r5/baseline-before.json`) |
| After | `5f5a5f1983be261d80e0618fc627e2c5beb1ef1aed7d29354ad5b896eda9c9db` (one scoped step, `r5/bl_apply_r5.py` → `r5/apply.log`, `r5/baseline-delta.json`) |
| Added / pruned / line-refreshed | 2 / 2 / 8 |
| Entries / files | 3305 → 3305 / 80 → 80 |
| Preserved | top-level settings, plugins, filters, version and `generated_at`; every other file's entries identical; existing key order; `is_verified` false on added entries; LF only |

- **Added:** the test's new `IDENTITY` (`aecc9ea5…`, line 130) and `PROPOSAL_SHA256` (`e0f8c657…`, line
  131). Each was recovered from its line and verified public by recomputation: `proposal_identity`, and
  the SHA-256 of the proposal (`r5/verify.log`).
- **Pruned:** round 4's `IDENTITY` (`5edcb225…`) and `PROPOSAL_SHA256` (`0f6728eb…`), whose hashed
  secrets are the SHA-1 of those two values. The rescan no longer finds them, and neither value occurs in
  the test any more (0 matches).
- **Refreshed:** 6 proposal lines, from the added CONTEXTUAL bindings, and the test's `ORACLE_SHA256` /
  `DRAFTS_SHA256` lines.
- **Scanned:** fourteen files, under the baseline's own plugins and filters and on a private copy that
  was deleted afterwards (`r5/scan.log`). They were the nine hook files, the COF test, `validation.py`,
  and this round's `projection.py`, `service.py` and the ADR. Only the packet files and the MI test carry
  findings.
- **Staged and hooked:** `git add -- .secrets.baseline`, by name, with the other staged changes kept.
  `detect-secrets-hook --baseline .secrets.baseline` then ran twice over the nine files of
  `sb/files.txt`. It ran again over the fourteen files of `sb/files-r5.txt`, and again after this note's
  last edit. The command, the arguments and `exit=` are in the same log (`r5/hook*.log`); see the
  handoff.
- No `scan --baseline` was run, and no allowlist pragma was added.

## Boundaries

- **Owner decisions:**
  - multiple-catalogue identity: settled by Owner Decision 2026-09-27 and implemented here; the proposal
    still awaits Codex review and exact Owner semantic acceptance;
  - shared part-intro coverage (deferred).
- **For review:**
  - The composed oracle changes two accepted records' derived `obligations` (`prose_bound_components` +
    `magic_items_table`). This is a consequence of the added component and is pinned exactly.
  - Accepting the proposal adds components to two records accepted in an earlier batch (by keyed union,
    with the accepted bytes unchanged). No prior approval is rewritten.
- **Service semantics to note:** an owner REPLACE still suppresses the span in context readers. Since
  round 5, no catalogue reads the shared rows as context: the family and A–Z read them as the item's
  component, so every view carries the replacement.
- **Placement scope:** the review-backed placement check covers members of more than one catalogue, the
  only case `catalogue_parts` admits. Single-catalogue membership keeps its existing checks.
- **Not an Owner boundary now:** a typed magic-item schema (no identified code-owned use).
- Nothing was committed, pushed, merged, published or activated. There is no acceptance in this run.
- Left untouched:
  - the quarantined `36b786d8-fa2` oracle;
  - the protected `issue-5d-source-correction-REPLACEMENT-PACKET.md`;
  - the 36 pre-existing staged deletions;
  - the unrelated modified files;
  - the four stashes.
- The broad accepted review, Casting Spells and shared coverage come after 5d.
