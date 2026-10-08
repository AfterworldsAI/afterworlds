# CRD Issue 5d — Monsters packet, offered for review (#132, #137)

> **Superseded for the current artifacts (2026-09-28).** This round-2 review describes the packet on the
> old release `5.2.1-corpus.574662e9-0ef`, composed over fc62: PROPOSAL `d8508c64…`, 82 drafts `61131f91…`,
> 3140 spans. The current packet is on the Monsters-corrected release `5.2.1-corpus.3fe24ff6-4e3`,
> composed over the unaccepted twenty-batch replacement chain: PROPOSAL `cdf06f43…`, 83 drafts `1733d78c…`,
> 3139 spans. See `issue-5d-monsters-corrections-integration-review.md`. Items 1 (part order), 2 (Succubus
> header order) and 11 (Veteran Warrior, now the Owner's decision and drafted) are resolved there. The
> Young White Dragon INT save is −2. A creature read now opens with its governing rules (§6 there).
> The grain and reference analysis below still describes the packet, apart from those deltas.

**Status: UNACCEPTED proposal plus 82 unrecorded resolution drafts (round 2).** Nothing is accepted,
recorded, committed, pushed, published or activated. `oracles/` is untouched. No shared DB or Chroma was
written: regeneration ran through the isolated `source_release_db` test fixture, not the repository
`afterworlds.db`. The partial-publication block holds. Codex reviews this packet, including the round-2
delta below, before any exact Owner semantic acceptance.

## Round 2: bounded source-fidelity correction

Classification (as given): settled source-fidelity / direct-read implementation defects, not new Owner
decisions. The grain and prose representation are unchanged; no creature facts, no schema change, no
source rewrite, no Animals, no accepted-material audit.

| Item | Change | Evidence |
|---|---|---|
| 1. References follow operative meaning | `PLAIN_SPELLS` adds 5 references printed without italics: *Storm Giant* actions → `spells.detect_magic`, `spells.light`, `spells.control_weather`; *Succubus* actions → `spells.dominate_person`; *Tarrasque* traits → `spells.magic_missile`. Each name must be an accepted spell name and printed (word-bounded, not "Light Crossbow") in its component. | Same-family scan of every A–Z leaf for every accepted spell name outside italics (scratch `.claude/_sp/mon/probe3.py`, retained for rerun). Every other hit is excluded by its printed role: Fly speeds; Bright/Dim Light illumination and "magical Darkness"; Darkvision (glossary); gear (Shield, Holy Symbol, Light Crossbow, Light Hammers); feature labels (Divine Aid, Dread/Baleful Command, Sleep Breath, Web Strand, Deathly/Radiant Teleport, Blazing/Guiding Light, Darkness Aura, Light Sensitivity); the *Nalfeshnee*'s "uses Teleport" (its own **Teleport** action); *Blink Dog* (a creature). |
| 2. Casting is what the text does | A component reads `SPELLCASTING` when its text casts (`\b(?:casts\|to cast\|can cast)\b`), whether or not a spell name was found, less `NOT_CAST`. `NOT_CAST` gains *Tarrasque* traits (a spell that targets it), now 10. Asserted both ways: every `NOT_CAST` member names a spell and does not cast; every other spell-naming component casts. | Round 1's `CASTING` set was 112, but that set included the 9 `NOT_CAST` components, so only **103** actually read the rules. Now **106**: the 103, plus *Storm Giant* actions, *Succubus* actions and *Shield Guardian* traits (*Spell Storing*, "can cast the spell stored", no spell named). 115 components name a spell. |
| 3. Governing-context matrix | Every header now also reads Alignment ("…a default suggestion of how to roleplay…") and the *Running a Monster* sidebar (combat usage rules that the printed CR assumes). Class-tag headers read the *Equipping* class-tag / Attunement leaf. Actions with an ammunition weapon read *Ammunition and Ranged Attacks*. The Languages match ignores case. | Readers asserted at import: Alignment and Running 235 each; class tag 7 (*Druid*; *Lich*, *Mage*, *Archmage* (Wizard); *Mummy Lord*, *Priest Acolyte*, *Priest* (Cleric)); ammunition 19 (label regex `**_Longbow\|Shortbow\|Light/Heavy/Hand Crossbow\|Pistol` followed by space or period, which admits the lycanthropes' "(Humanoid or Hybrid Form Only)" forms and excludes the *Djinni*/golem "Bolt" features). "Understands" capitalised: 19 headers (e.g. *Zombie*, *Skeleton*, *Chimera*), which round 1 missed. Other tags (Demon, Devil, Chromatic, Goblinoid, Angel, Titan…) are descriptive, not classes. Hit Dice by Size / Con and XP stay unread (the printed dice already give the HP). |
| 4. Equipment ambiguity | The *Equipping a Monster with Other Items* container is split into its two whole source leaves: `equipping_a_monster_with_other_items` (the generic "You may equip…" leaf; keeps its latitude; "Equipment" stays an unresolved chapter pointer) and `magic_items_and_class_tags` ("Beware of giving…"; `QUALIFIED` binds its "Equipment" to `equipment.magic_items`). | `equipment.magic_items` is an accepted `general_rule` record in the oracle (checked). The new component's reason is `no_identified_structured_use`. |
| 5. Plural drafts | `PLURAL_DRAFTS`: 10 reviewed, exact (record, component, text) → stat-block mappings. No generic singularisation. | Sources: *Create Undead* ("…**Ghouls**…**Ghasts** or **Wights**…**Mummies**. See "Monsters" for these stat blocks."); *Combat Encounters* examples at stat-block XP (**2 Druids** (450 XP each), **9 Stirges** (25 XP each), **6 Skeletons** (50 XP each), **2 Adult Red Dragons** (18,000 XP each), **2 Fire Giants** (5,000 XP each)), so the *Druid* here is the stat block, not the class; *Bag of Beans* table ("Three Shrieker Fungi sprout."). *Giant Rats*, *Giant Wasps* and *Mastiffs* (Animals) stay unresolved. |

**Still UNDECIDED (not corrected, for Codex / Owner):**

- *Veteran Warrior* (*Deck of Illusions*) vs the printed *Warrior Veteran*: no draft (item 11 below).
- *Young White Dragon* INT `6 −2 2`: official, preserved verbatim, no value inferred (item 3).
- The *Succubus* header leaf order (item 2) and the alphabetical release part order (item 1).

The controlled source and the private release are not rewritten.

**Scope.** The *Monsters* general rules (PDF pp254–257) and the complete *Monsters A–Z* catalogue
(pp258–344) as one consolidated packet with one native composition. There is no entry ceiling. *Animals*
is the next part and is not authored here: no Animals stat block is emitted, and no reference resolves
into it.

**Authority.** CRD Issue 5d / ADR-005d typed contracts, the Library review and prompting guidance of
2026-09-25 (`Prompting Claude Code to do work for us 2026-09-25.txt`, SHA
`355ce12a85350f28c905534e55e04058db2139fe0b530fdc8c4ef7754537c8c5`), and the recorded Owner
source-fidelity decisions. No accepted record key starts with `monsters.`, and no accepted leaf lies in
either part. Accepted creatures and stat blocks printed elsewhere (the scoped stat blocks in *Spells* and
*Magic Items*) keep their own records. An identical name does not make them this packet's creature, and it
does not make them a different one. They are not merged, rewritten or re-pointed.

## Artifacts (exact hashes)

| Artifact | Identity / SHA-256 |
|---|---|
| `issue-5d-monsters-PROPOSAL.json` (8,265,819 bytes) | identity `80b904fbaa7874b8f31552d5293de720bb292033b0a919f43ed4918340d5658a`; SHA `d8508c64a03642ebad1a2be489c2277986c8ed514d8aca8a88f9d244e8bc4e32` (round 1: identity `94d163a7…`, SHA `d24875bd…`) |
| `issue-5d-monsters-resolutions-DRAFTS.json` (82 drafts) | SHA `61131f916f634a9f2eb0f0ea999b713cc42ba506865a2b1e4ac1aeec13d0ed06` (round 1: `289c0d84…`, 72 drafts) |
| `issue-5d-monsters-generator.py` | derives both artifacts from the release |
| `issue-5d-monsters-source.py` | qualified leaf texts, in printed order (unchanged in round 2) |
| `tests/ingestion/mechanical/test_monsters_proposal.py` | 11 tests pinning the above |

The generator binds only to the current accepted oracle. It asserts the oracle SHA and has no fallback:

- oracle: `srd-5-2-1-corpus-574662e9-0ef.json`;
- oracle SHA-256: `fc62c47cde83cd341f714b7e51660354a22b69dc59f214c0a6e5ec379dee5a62`;
- contents: 20 batches, 1250 records, 6450 spans, 950 units and 1099 resolutions;
- findings: 315 reference findings and 4004 uncovered leaves.

Release binding (proposal and drafts):

- `authoritative_source_hash` `8974902d…3d87`;
- `transform_config_hash` `2a7feddf…0e64d`;
- `bundle_root_hash` `3da7b5b3…754689`;
- `persisted_corpus_digest` `df64eb40…596acb02`;
- representation schema `5d-representation-schema-16`;
- semantic policy `5d-semantic-policy-2`.

## Source qualification (before authoring)

Every release leaf of both parts was checked against the pinned official PDF
(`docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf`) before any authoring. There are 3142 leaves in total: 3140
authored leaves plus the two part headings, which are left with the other part headings.

| Check | Result |
|---|---|
| Prose and heading leaves: compacted text found on the printed page (±1) | 2902 of 2904; 2 exceptions below, both faithful |
| Tables: every row's cells, in printed order, contiguous in the PDF | 238 tables, 735 of 735 rows |
| Stat-block ability tables: header `MOD SAVE` ×3; labels STR DEX CON / INT WIS CHA; MOD = ⌊(score−10)/2⌋; SAVE − MOD ∈ {0, PB}, with PB from the block's CR line | 235 tables, 234 clean; 1 official defect below |
| Ownership and order: each leaf found at or after the previous one in the PDF column-order (`cols`) stream | A–Z `cols`: 2 breaks, both the Succubus header (below). The `flow` mode's 19 A–Z breaks are two-column interleave artifacts in multi-column stat blocks (e.g. *Tarrasque* actions, *Couatl* bonus actions); every one of those leaves is qualified on its page above. *Monsters*: breaks come only from the PDF's two-column / sidebar extraction (`flow` mode shows 3: the *Hit Points* heading, the *Running a Monster* sidebar and the p255→p256 page turn), each resolved against the page (see *Surfaced*, items 4 and 5) |

The two prose exceptions:

- **Succubus header (p331).** The release prints `AC 15 / HP 71 (13d8 + 13) / Speed 30 ft., Fly 60 ft.`
  and then `Initiative +3 (13)` as a later leaf. The PDF prints `AC 15 Initiative +3 (13) HP 71 …`.
  The text is exact; only the leaf order inside the header differs. See *Surfaced*, item 2.
- **"Beware of giving a monster…" (p255→p256).** The PDF breaks the paragraph across the page turn after
  "A monster with"; its remainder opens p256 ("a class tag after its creature type…"). The release joins
  it into one leaf. The whole text is verified.

The qualification scripts ran on the PDF extraction. They and their logs are kept uncommitted under
`.claude/_sp/mon/` as review evidence until Codex review:

- extraction: `pdfx.py`, `leaves.py`;
- checks: `qual.py`, `order.py`, with `qual.log` / `qual.json` and `order.log`;
- inputs: `rules.log`, `mksource.py`, `animals.json`, `drafts.py`, `drafts.log`;
- gate logs.

They are not part of the packet.

### Identical names (authority is not inferred from a name)

The accepted chain holds 6 `creature` records:

- `magic_items.figurine_of_wondrous_power.giant_fly`;
- `magic_items.mysterious_deck.avatar_of_death`;
- `spells.animate_objects.animated_object`;
- `spells.find_steed.otherworldly_steed`;
- `spells.giant_insect.giant_insect`;
- `spells.summon_dragon.draconic_spirit`.

None of them shares a key tail with any of this packet's 414 records. The *Animated Objects* group
(*Animated Armor*, *Flying Sword*, *Rug of Smothering*) is a different printed name from the spell's
*Animated Object*, and the two stay separate.

The only accepted record whose key tail equals a packet record's is `classes.druid` (the class), against
`monsters.druid.druid` (the stat block). They are different authorities with the same name, and no
reference crosses between them. The *Druid* stat block's references resolve to spells. The Combat
Encounters "Druids" plural is drafted to the stat block, because its source prints it at the stat
block's 450 XP (round 2, item 5).

All 235 relationships are `catalogue_member` inside this packet. No shared-catalogue appearance is
asserted, because none is source-backed.

## Grain and representation

- **414 records.**
  - 179 `general_rule` records: 2 rules sections (*Stat Block Overview*, *Parts of a Stat Block*) and
    177 catalogue groups (`monsters.<group>`, e.g. `monsters.red_dragons`).
  - 235 `creature` records (`monsters.<group>.<creature>`). Each creature is a `catalogue_member` of its
    group (235 relationships). A group owns only its own printed heading and prose; each stat block owns
    its own.
- **948 components, 3140 spans, 414 review units.** The one new component comes from the *Equipping*
  split. Every span is prose-bound: 7047 bindings and 9733 provenance rows (round 1: 6520 and 9198; the
  increase is the added context reads). There are 0 facts, 0 partition findings and 0 review-unit findings.
- **Creature components follow the printed stat block:**
  - a header component (name, type line, AC/HP/Speed/Initiative, the ability table with separate MOD and
    SAVE columns, skills, resistances, senses, languages, CR);
  - then `traits`, `actions`, `bonus_actions`, `reactions` and `legendary_actions`, only where printed.
  - Each component keeps its printed heading, uses (e.g. "Legendary Action Uses: 3"), recharge
    ("Recharge 5–6"), resources, spellcasting qualifiers and variants verbatim. A repeated heading
    ("#### Actions") stays with its own stat block.
- **Tables** stay whole leaves, in printed order.
- **Typing.** There is no code-owned typed use for creature statistics, so everything is faithful prose.
  No new schema authority is invented.

### Governing context (direct creature reads)

Each creature component carries the *Parts of a Stat Block* rules that govern it, as context. This is by
operative meaning, not typography:

| Context set | Source | Applied to |
|---|---|---|
| `ALIGNMENT` | Parts / Alignment ("…a default suggestion of how to roleplay the monster…") | every header (235) |
| `HIT_POINTS` | Parts / Hit Points (presentation rule) | every header |
| `INITIATIVE` (2) | Parts / Initiative | every header |
| `ABILITY_SCORES` | Parts / Ability Scores | every header |
| `RUNNING` | Parts / *Running a Monster* sidebar (combat usage the printed CR assumes) | every header (235) |
| `SIZE_OPTIONS` | Parts / Size ("A monster is Tiny…") | headers whose type line prints a size choice (e.g. *Commoner*) |
| `CLASS_TAG_RULE` | Parts / Gear / Equipping ("Beware of giving…class tag…Attunement purposes") | headers whose type line prints a class tag (7) |
| `GEAR` (3) | Parts / Gear | headers printing a `Gear` line |
| `LANGUAGES` | Parts / Languages | headers printing `Languages None` or "understands" in any case |
| `TELEPATHY` | Parts / Languages / Telepathy | headers printing telepathy (e.g. *Aboleth*) |
| `CONTAINER_RULES` | Parts / Traits, Actions, Bonus Actions, Reactions, Legendary Actions (2) | each container component |
| `NOTATIONS` | Parts / Actions / attack, saving-throw, damage and Multiattack notation; Limited Usage (X/Day, Recharge) | a container component, only by the notation it prints |
| `AMMUNITION` | Parts / Gear / Ammunition and Ranged Attacks | components attacking with an ammunition weapon (19) |
| `SPELLCASTING` (4) | Parts / Actions / Spellcasting | the 106 components that cast |

The Alignment leaf also prints the rule's own latitude ("Change a monster's alignment…"). That leaf is
classified on its owner component; a creature only reads it as context.

Deliberately **not** read as context:

- the *Hit Dice by Size* table and the Constitution rule, because a stat block prints its own Hit Point
  Dice;
- the Experience Points rules, because awarding XP is not the creature's.

Round 1 also left the *Running a Monster* sidebar unread. That was a defect: its explicit combat rules
govern whether a monster acts at its printed CR. Round 2 reads it on every header.

A component *casts* when its own text matches `\b(?:casts|to cast|can cast)\b`, whether or not a spell
name is found, less the explicit `NOT_CAST` set. `NOT_CAST` holds 10 components that name a spell the
creature does not cast:

- *Black Pudding* traits and actions;
- *Chuul* traits;
- *Gray Ooze* traits and actions;
- *Guardian Naga* traits;
- *Lemure* traits;
- *Rust Monster* actions;
- *Spirit Naga* traits;
- *Tarrasque* traits (*Reflective Carapace*: a *Magic Missile* that targets it is reflected; round 2).

`CASTING` counts actual recipients: 106 components read `SPELLCASTING`. `CASTING` and `NOT_CAST` are
disjoint, which is asserted.

A header names a spell only as a condition and casts nothing there: the *Archmage*'s *Mind Blank*, the
*Rakshasa*'s *Bless*. Such spell names still resolve as references.

## References (2348; round 1: 2342)

| Target | Count |
|---|---|
| Accepted records | 2256: glossary 1806, spells 413 (+5 plain), equipment 25 (+1 `equipment.magic_items`), play 10, character_creation 1, gameplay_toolbox 1 |
| Intra-packet | 7 |
| Unresolved: exact target absent, named and left unresolved | 85 |

- **Intra-packet references:**
  - *Incubus* ↔ *Succubus* (traits);
  - *Troll* ↔ *Troll Limb* (traits);
  - *Vampire* → *Vampire Spawn*;
  - *Wight* → *Zombie*;
  - *Wraith* → *Specter* (actions).
- **Self-named bold runs are not references:** *Black Puddings*, *Ochre Jellies*, *Shadow*, and the five
  lycanthropes.
- **Precise references:**
  - spells by exact name (e.g. *Mage* → `spells.fireball`), including "Long-strider" (see *Surfaced*)
    and the 5 plain (non-italic) spell dependencies of round 2, item 1;
  - glossary terms (e.g. telepathy → `glossary.telepathy`);
  - accepted equipment by exact name (e.g. *Daggers*).
- **Unresolved, 85.** None falls back to a broad section:
  - 76 gear names whose exact Equipment record is not accepted, e.g. *Leather Armor* 7, *Chain Shirt* 6,
    *Longbow* 6, *Battleaxe*, *Pistol*, *Component Pouch*;
  - 9 whole-chapter pointers: "Rules Glossary" 4, "Playing the Game" 2, "Equipment" 2, "Spells" 1.
    One "Equipment" is the generic *Equipping* leaf's pointer, kept unresolved.

## Resolution drafts (82, unrecorded) and what is left (79)

Accepted reference findings whose exact target this packet now provides are drafted. Each draft names the
one stat block its printed text names:

| Source | Drafts |
|---|---|
| `deck_of_illusions` | 31 |
| `combat_encounters` | 9 (4 + 5 plurals) |
| `pact_of_the_chain` | 6 |
| `bag_of_beans` | 5 (4 + *Shrieker Fungi*) |
| `create_undead` | 5 (1 + 4 plurals) |
| `manual_of_golems`, `elemental_gem` | 4 each |
| `figurine_of_wondrous_power`, `awaken`, `animate_dead` | 2 each |
| single-draft sources (e.g. *Mysterious Deck* → *Knight*, *Bag of Tricks* → *Axe Beak*, *Finger of Death*) | 12 |

The 10 plural drafts (round 2, item 5) come from the reviewed `PLURAL_DRAFTS` table, keyed by the exact
(record, component, printed text):

| Printed | Draft target |
|---|---|
| Ghasts / Ghouls / Mummies / Wights | `monsters.ghast.ghast` / `monsters.ghoul.ghoul` / `monsters.mummies.mummy` / `monsters.wight.wight` |
| Skeletons / Druids / Stirges | `monsters.skeletons.skeleton` / `monsters.druid.druid` / `monsters.stirge.stirge` |
| Adult Red Dragons / Fire Giants | `monsters.red_dragons.adult_red_dragon` / `monsters.fire_giant.fire_giant` |
| Shrieker Fungi | `monsters.fungi.shrieker_fungus` |

No draft targets an Animals name.

79 accepted findings are **left**:

- **17 "Monsters" whole-chapter pointers.** No broad-section fallback.
- **Animals names** (e.g. *Elephant*, *Riding Horse*, *Bat*, *Owl*, *Giant Goat*, *Rat*, *Venomous
  Snake*, *Giant Constrictor Snake*, *Swarm of Rats*). Their stat blocks print in *Animals*, which is the
  next part.
- **Animals plurals**, unresolved and unexpanded: *Giant Rats*, *Giant Wasps* (Combat Encounters) and
  *Mastiffs* (Robe of Useful Items).
- ***Veteran Warrior*** (`deck_of_illusions`). *Monsters A–Z* prints *Warrior Veteran*
  (`monsters.warriors.warrior_veteran`), not *Veteran Warrior*. See *Surfaced*, item 11.

## Native outcomes (test only, in memory)

This is the composition against the current accepted chain. It uses `accept_proposal` and
`resolve_references`; nothing is persisted, and `oracles/` stays byte-identical.

| | Before | After |
|---|---|---|
| batches | 20 | 21 |
| records | 1250 | 1664 (+414) |
| spans | 6450 | 9590 (+3140) |
| review units | 950 | 1364 (+414) |
| resolutions | 1099 | 1181 (+82) |
| reference findings | 315 | 318 (315 − 82 drafted + 85 packet-unresolved) |
| uncovered leaves | 4004 | 864 (−3140) |

- The accepted records, spans, approvals, resolutions and times are exactly preserved:
  `REPLACEMENT._preserved(old, new)` is empty.
- There are 0 resolution violations and 0 other failures.
- The batch checks equal the 2341 expected representation findings exactly; `emit` raises on any
  difference. The 2341 is numerically the 2348 references less the 7 intra-packet ones.
- Regeneration: `gen.main` over the isolated `source_release_db` test fixture (scratch driver, deleted),
  exit 0, 227 s. The regenerated PROPOSAL/DRAFTS are the files pinned above.

### Consumer behaviour (actual `RulesAuthorityService`)

These are exercised through `gamemaster_view` / `rule_slice` using the COF test helpers:

- **Creature read (Aboleth).** For each clause, the component's own texts come first, in printed order.
  The governing context not yet read follows, deduplicated across components (`HIT_POINTS` once).
  `TELEPATHY` is read; `SIZE_OPTIONS` and `GEAR` are not. The *Commoner*'s read includes `SIZE_OPTIONS`.
- **Section read (Red Dragons).** The group slices to `[group, *its blocks]`. The read opens
  "## Red Dragons", the printed order holds, `HIT_POINTS` appears once, "#### Actions" appears once per
  block, and span IDs are unique.
- **Component disable.** Disabling `parts_of_a_stat_block/hit_points` removes `HIT_POINTS` from the
  Aboleth read. Selecting the owner together with Aboleth reads it once.
- **Round-2 direct reads**, asserted against literal source text in the test (not the generator's
  context list):
  - *Aboleth* reads the Alignment and *Running a Monster* texts once each, and no class-tag,
    ammunition or spellcasting text;
  - *Mage*, *Priest* and *Druid* read the class-tag ("Beware of giving…") text;
  - *Scout* and *Werewolf* read the ammunition text;
  - *Zombie* (capitalised "Understands", missed by round 1) reads the Languages text;
  - *Storm Giant*, *Succubus* and *Shield Guardian* read the Spellcasting text; *Tarrasque* does not.
- **Round-2 override and dedup.** Disabling `running_a_monster`, `magic_items_and_class_tags` or
  `alignment` removes exactly that text from the *Mage* read. A combined read of the Parts record with
  *Mage* and *Scout* gives each span once, with unique span IDs.

## Surfaced (not silently corrected)

1. **Release part order puts creature text before its rules.** The release orders parts alphabetically,
   so *Monsters A–Z* precedes *Monsters* in source order. A creature read therefore gives the creature's
   own text first and its governing rules after. This is the actual consumer behaviour, tested as such.
   The PDF prints the rules first.
2. **Succubus Initiative leaf order.** The release places `Initiative +3 (13)` after
   `AC/HP/Speed`; the PDF prints it between AC and HP. The text is preserved as released and the leaf is
   not moved.
3. **Young White Dragon INT SAVE (p340, *White Dragons*).** The PDF prints `Int 6 −2 2`, and the
   release prints the same. The SAVE is `2`, with no sign. With PB +3, SAVE − MOD = 4 ∉ {0, 3}. This is
   an official source defect and is preserved verbatim; no value is inferred.
4. **The *Running a Monster* sidebar** is its own component of the *Parts of a Stat Block* record,
   immediately after *Resistances and Vulnerabilities*. The release places it there. In the PDF it is a
   boxed sidebar on that page, so column extraction finds it elsewhere. It stays where the release places
   it. **Round 2:** it is now read as context on every header (see *Governing context*).
5. **The p255 paragraph split** across the page turn is joined by the release. The text is verified
   whole.
6. **"Long-strider".** The *Druid* prints "Long-strider"; the spell is *Longstrider*. It resolves to
   `spells.longstrider` through the explicit `SPELL_FORMS` mapping, and the printed text is unchanged.
7. **GM latitude.** Every component whose text names the GM or "you" is classified in exactly one
   list; the generator asserts this.
   - **Latitude (4).** The source leaves an open ruling:
     - Parts / *Alignment* ("Change a monster's alignment…");
     - Parts / *Equipping a Monster with Other Items* ("You decide how much…");
     - *Aboleth* traits ("another location chosen by the GM");
     - *Commoner* traits ("one skill of the GM's choice"; no options are printed).
   - **Not latitude (8).** The text only chooses among printed options, or says who controls a printed
     outcome:
     - Parts / *Size*;
     - Parts / *Damage Notation*;
     - *Half-Dragon* traits;
     - the five lycanthropes' actions.
8. **"Beware of giving…" → *Magic Items*.** Round 1 left it unresolved because one component held both
   leaves. **Resolved in round 2** (item 4): the leaves are separate components, and "Beware…" binds to
   `equipment.magic_items` while the generic leaf's "Equipment" pointer stays unresolved.
9. **The *Magic Items* "stat block in *Monsters*" vs *Animals* conflict.** The accepted *Magic Items*
   general rule says: "Unless the text states otherwise, the stat block is in 'Monsters.'" But the bold
   creatures *Elephant*, *Riding Horse*, *Giant Goat*, *Lion* and others print their stat blocks in
   *Animals*, not in *Monsters* / *Monsters A–Z*. They stay unresolved here, and no Monsters record stands
   in for them. How they resolve once *Animals* lands is for that packet to surface.
10. **Plurals.** **Resolved in round 2** (item 5) for the 10 source-disambiguated plurals, by the
    reviewed exact `PLURAL_DRAFTS` table, not by generic singularisation. The 3 Animals plurals stay
    unresolved.
11. ***Veteran Warrior* vs *Warrior Veteran*. UNDECIDED.** *Deck of Illusions* names "Veteran Warrior";
    the catalogue prints *Warrior Veteran*. The draft is withheld because the exact printed name matches
    no stat block. Unlike "Long-strider", which differs only in hyphenation, this is a word-order
    difference. Resolving it to `monsters.warriors.warrior_veteran` needs a reviewer or Owner call; it is
    not drafted.
12. **The `NOT_CAST` list (now 10), the header-condition spells and the `PLAIN_SPELLS` exclusions** are
    explicit judgements (see *Governing context* and round 2, item 1). They are listed so review can
    check each one.

Items 1, 2 and 3 remain **UNDECIDED** and preserved verbatim; items 8 and 10 are resolved as settled
defects; item 4's sidebar placement is unchanged.

## Gates (raw, attached, each run to its actual exit)

| Gate | Result | Exit |
|---|---|---|
Round 2 (on the final files):

| Gate | Result | Exit |
|---|---|---|
| `black --check` (generator, test) | clean | 0 |
| `ruff check` (same files) | clean | 0 |
| `mypy src/` | no issues in 235 files | 0 |
| `mypy src/` + monsters source, generator and test (238 files) | only the 3 established pre-existing COF errors (lines 888, 1755, 1759); nothing new | 1 (deferred non-green) |
| `rtk proxy venv\Scripts\python.exe -m pytest tests/ingestion/mechanical/test_monsters_proposal.py -q -p no:cacheprovider --no-cov` | 11 passed (425 s) | 0 |
| `rtk proxy venv\Scripts\detect-secrets-hook.exe --baseline .secrets.baseline` over the 6 packet files (generator, source, PROPOSAL, DRAFTS, test, this packet), after the delta was staged and after this edit | run 1 and run 2, baseline hash stable, index = worktree | 0, 0 |

Round 1: black/ruff 0; `mypy src/` 0; expanded mypy 1 (same 3); pytest 9 passed (308 s) 0; hook 0, 0.

- The full suite was not rerun: nothing outside this packet's files changed.
- `pip-audit` (31 vulnerabilities / 11 packages) stays deferred and non-green.
- The expanded-mypy gate stays non-green (the pre-existing COF errors).

## Secrets baseline (scoped)

The delta is a pure addition: +113 lines, 0 changed or removed. It adds 15 `Hex High Entropy String`
entries, appended after the last existing entry in the Magic Items precedent order (generator, PROPOSAL,
DRAFTS, test). Plugins, filters, metadata, flags, `generated_at` and every existing entry are
byte-identical.

- Baseline SHA-256: `5e69a1089df279deea90e7682eee8338133af04c599ed5a9000422537448cead` →
  `0c8ff152c125ad218174463d59c793585c361c1c5a9f499923be68138b74055a`.
- Staged blob `f28ec1ea5c34519c9ba8dcf30edaa448e32e57d0`; index = worktree.

**Round-2 delta** (moves and verified obsolete prunes/additions only; still 15 monsters entries; order,
settings, flags, metadata and `generated_at` unchanged; DRAFTS entries unchanged):

- Moves (same hash, new line): generator `ORACLE_SHA256` 125 → 129; test `ORACLE_SHA256` 79 → 85;
  PROPOSAL 252665/252666/252668/252670/252673/252676 → 264415/264416/264418/264420/264423/264426.
- Prune + addition (the old values were verified as the SHA-1 of the round-1 pins, and those pins are
  absent from the test):
  - test:95 `753bd52aedfc9d7b6b65d509ce661defa43ed8be` → test:101 `dbfd7df66cacd967cd9d2123ea51d9bbe775a63e` (`IDENTITY`);
  - test:96 `2cc4b1215f918d9ce327db27b679c38a8facf4a9` → test:102 `19020e0f9d4ac475f27b788caa85f13116744a14` (`PROPOSAL_SHA256`);
  - test:97 `67907883d7315cf51f45c0565ef6166ee3361f6c` → test:103 `9b07320fa305dc6bc36e379698e74f2bb0683c35` (`DRAFTS_SHA256`).
- Before the delta the hook exited 1, flagging test lines 101–103; after it, 0 and 0.
- Baseline SHA-256 `0c8ff152c125ad218174463d59c793585c361c1c5a9f499923be68138b74055a` →
  `1d870e184324b076c71637943bb41314f6f4df22bd84bdad9fbcbe7b248bb555`; staged blob `f28ec1e` →
  `9b2d5eac77341659459a601c38cf1a9a9a4f5d77`; index = worktree.

Every value is a public hash named by its own field (round-1 line numbers):

| File:line | Field | Value |
|---|---|---|
| generator.py:125, test:79 | `ORACLE_SHA256` | the accepted oracle file's SHA |
| PROPOSAL.json:252665, DRAFTS.json:12 | `authoritative_source_hash` | release binding |
| PROPOSAL.json:252666, DRAFTS.json:14 | `bundle_root_hash` | release binding |
| PROPOSAL.json:252668, DRAFTS.json:15 | `persisted_corpus_digest` | release binding |
| PROPOSAL.json:252670, DRAFTS.json:13 | `transform_config_hash` | release binding |
| PROPOSAL.json:252673 | `representation_schema.hash` | schema hash |
| PROPOSAL.json:252676 | `semantic_policy_hash` | policy hash |
| test:95, 96, 97 | `IDENTITY`, `PROPOSAL_SHA256`, `DRAFTS_SHA256` | this packet's identity and file SHAs |

The release-binding, schema, policy and oracle values hash to the same `hashed_secret` values already
baselined for the accepted Magic Items files. No `pragma: allowlist secret` was added, and
`scan --baseline` was not run.

## Boundaries

- Nothing is accepted or recorded. The 82 drafts are prepared only.
- No Animals catalogue, no recursive creature expansion, and no accepted-record rewrite.
- Protected `REPLACEMENT-PACKET.md` and the earlier quarantine are untouched.
- Broad accepted review, *Casting Spells* and shared coverage remain after 5d.
