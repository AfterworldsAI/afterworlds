# Current 23-reference disposition — CRD Issues 5c and 5d

Verified 3 October 2026. This is a read-only disposition and proposed work order, not an accepted target proposal, native candidate, acceptance packet, or publication authorization. All **23 reference findings remain** in the current accepted recording.

## Verified starting point

The [restart summary](../../docs/architecture/issue-5c-5d-clean-restart.md), [21 September Owner Decision](../../docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md), and [latest recorded follow-up](issue-5d-finite-reference-routes-recorded-followup.md) were checked against the current working-tree oracle:

- Release `67c81736-15fd-5e82-8523-e84922f0a7c6` / `5.2.1-corpus.3fe24ff6-4e3`; representation schema 17.
- Oracle SHA-256 `e9678ab30c27ba92deda5757de4be082aba8bfc44690b6bf94f7bc1f747a45ca`; 24 accepted batches, 1,835 records, 10,493 spans, 1,476 review units, and 1,463 reference resolutions.
- Direct JSON inventory: 8,047 representation references, including 1,486 empty-target occurrences. Subtracting accepted resolution identities by `(from_record_key, from_component_key, source_text, scope_key)` leaves exactly 23. Multiple provenance spans do not create extra occurrences.
- The accepted ten finite-reference routes and combat replacement remain complete. Their completed evidence is reused; no material gap or concrete invalidation was identified here.
- The [qualified source pin](../../docs/sources/community/dnd-5e-srd-markdown/source_pin.json) remains SHA-256 `2a68c67af6fbed0bdadb88df990ae56e08fd98ab64b7a565295736e0545dde89`; the [official PDF](../../docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf) remains SHA-256 `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87`. Source qualification does not grant semantic acceptance.

Current Library guidance was retrieved through connected Chrome. The latest available [Review Afterworlds Issues source](https://chatgpt.com/space/file/libfile_fb156109fdd081919830350dd2e4fa07), titled `review-afterworlds-issues-SKILL-2026-09-25.md`, matches the installed review instructions after newline normalization; no installed-skill update was needed. [Prompting Claude Code to do work for us — 2026-09-28](https://chatgpt.com/space/file/libfile_9dedab6fa0008191880b48596be6c70a) states its revision and identifies the 25 September guide as its prior version. Selection used document contents and available version history, not upload time alone.

The [accepted route contract in ADR-005d, Decision 7](../../docs/decisions/adr-005d-complete-typed-mechanical-authority.md) permits source-grounded labelled groups over existing records with source-order landing and supporting destinations. Existing one-hop catalogue behavior may be reused. It does not authorize a new aggregate record, invented item, taxonomy, recursive consumer, or acceptance of any new exact mapping.

## Exact current inventory

Numbers retain the row identities in the [earlier inventory](issue-5d-remaining-references-review.md). An em dash means record-owned, with an empty `from_component_key`. Scope values below omit the common `srd-5.2.1/` prefix. Proposed disposition is separate from accepted status.

| Row | From record | Component | Source text | Scope | Proposed disposition |
|---|---|---|---|---|---|
| 24 | `character_creation.create_your_character` | `starting_equipment` | Equipment | equipment | Next four-citation candidate: Equipment chapter route |
| 34 | `magic_items.magic_item_rarity.magic_item_values_by_rarity` | `magic_item_values_by_rarity` | a purchase cost in "Equipment" | equipment | Hold for precise priced-item inventory |
| 35 | `monsters.parts_of_a_stat_block` | `equipping_a_monster_with_other_items` | Equipment | equipment | Next four-citation candidate: Equipment chapter route |
| 36 | `monsters.parts_of_a_stat_block` | `gear` | Equipment | equipment | Hold for precise retrievable-gear inventory |
| 37 | `play.exploration` | — | See "Equipment" for rules on many items | equipment | Next four-citation candidate: Equipment chapter route |
| 39 | `classes.wizard` | `core_traits` | Spellbook | equipment | Retain source/target-scope deferral; no invented Equipment item |
| 46 | `gameplay_toolbox.curses_and_magical_contagions` | `cursed_magic_items` | Magic Items | magic-items | Next four-citation candidate: curse-bearing item descriptions |
| 48 | `classes.warlock.eldritch_invocation_options.pact_of_the_chain` | `pact_of_the_chain` | Monsters | monsters | Hold for full familiar-form source inventory |
| 54 | `magic_items.magic_items_a_z` | `magic_items_a_z` | the stat block is in "Monsters." | monsters | Hold for precise named-stat-block inventory and exceptions |
| 57 | `spells.awaken` | `effect` | Monsters | monsters | Open GM choice of appropriate Plant statistics; boundary residue |
| 60 | `spells.find_familiar` | `effect` | Monsters | monsters | Hold for full familiar-form source inventory |
| 76 | `play.d20_tests` | `add_modifiers` | Rules Glossary | rules-glossary | Hold for exact ability-modifier selection coverage |
| 79 | `classes.bard.spellcasting` | `spellcasting` | Spells | spells | Following ordinary batch: Gaining + Casting Spells |
| 80 | `classes.cleric.spellcasting` | `spellcasting` | Spells | spells | Following ordinary batch: Gaining + Casting Spells |
| 81 | `classes.druid.spellcasting` | `spellcasting` | Spells | spells | Following ordinary batch: Gaining + Casting Spells |
| 82 | `classes.paladin.spellcasting` | `spellcasting` | Spells | spells | Following ordinary batch: Gaining + Casting Spells |
| 83 | `classes.ranger.spellcasting` | `spellcasting` | Spells | spells | Following ordinary batch: Gaining + Casting Spells |
| 84 | `classes.sorcerer.spellcasting` | `spellcasting` | Spells | spells | Following ordinary batch: Gaining + Casting Spells |
| 85 | `classes.warlock.pact_magic` | `pact_magic` | Spells | spells | Following ordinary batch: Gaining + Casting Spells |
| 86 | `classes.wizard.spellcasting` | `spellcasting` | Spells | spells | Following ordinary batch: Gaining + Casting Spells |
| 87 | `glossary.cantrip` | — | Spells | spells | Hold for complete Spells-part coverage |
| 88 | `glossary.ritual` | — | Spells | spells | Hold for complete Spells-part coverage |
| 89 | `glossary.spell` | `spell` | Spells | spells | Following ordinary batch: Casting Spells entry characteristics |

## Smallest useful next candidate: four citations

Prepare rows **24, 35, 37, and 46**, using the accepted labelled-group route mechanism and existing records. This groups four citations with bounded, source-defined coverage; it does not claim that a candidate already exists or has passed consumer checks.

For the three general Equipment pointers, propose the chapter's existing section records in printed source order:

`equipment.coins`, `equipment.weapons`, `equipment.armor`, `equipment.tools`, `equipment.adventuring_gear`, `equipment.mounts_and_vehicles`, `equipment.lifestyle_expenses`, `equipment.food_drink_and_lodging`, `equipment.hirelings`, `equipment.spellcasting`, `equipment.magic_items`, `equipment.crafting_nonmagical_items`, `equipment.brewing_potions_of_healing`, `equipment.scribing_spell_scrolls`.

Source anchors are [Equipment](../../docs/sources/community/dnd-5e-srd-markdown/equipment.md), [character creation](../../docs/sources/community/dnd-5e-srd-markdown/character-creation.md), [Monsters](../../docs/sources/community/dnd-5e-srd-markdown/monsters.md) lines 169–185, and [Playing the Game](../../docs/sources/community/dnd-5e-srd-markdown/playing-the-game.md) lines 732–734. Row 37 is the current second Equipment occurrence; its earlier Weapons-related sibling is already resolved. General chapter pointers must retain complete chapter coverage rather than silently collapsing to Adventuring Gear. Prove that the selected section records and existing one-hop reader actually expose the required rules and members before claiming any finding clears.

For row 46, propose the four source descriptions that identify their items as cursed, in source order: `magic_items.armor_of_vulnerability`, `magic_items.berserker_axe`, `magic_items.demon_armor`, and `magic_items.shield_of_missile_attraction`. [Gameplay Toolbox](../../docs/sources/community/dnd-5e-srd-markdown/gameplay-toolbox.md) lines 195–197 points to item details. [Magic Items](../../docs/sources/community/dnd-5e-srd-markdown/magic-items.md) lines 245–249 states that item descriptions specify curses; relevant descriptions are at 855/861, 1171/1177, 1735/1741, and 4044/4050. Deck of Many Things' Euryale effect curses the drawer; it does not identify the Deck itself as a cursed item. This mapping concerns item descriptions, not a new curse-identification or removal policy.

Claude should produce the native candidate and exact packet with source/consumer coverage, preservation of the 24 accepted batches and existing 1,463 resolution identities, normal resolution-view evidence, fail-closed evidence with proposed overrides absent, and reload evidence. Reuse unaffected completed evidence; run only the checks invalidated by this candidate plus binding gates. Independent review and **exact Owner acceptance of the final candidate** precede recording. If all four clear, 19 would remain; that is a planning projection, not a measured result.

## Following ordinary batch: nine spell references

Rows **79–86** concern the general spellcasting rules cited by eight class features. Propose one source-order route over `spells.gaining_spells` and `spells.casting_spells`. [Classes](../../docs/sources/community/dnd-5e-srd-markdown/classes.md) lines 826, 2148, 3418, 5554, 6323, 7532, 8911, and 10146 and the [Spells introduction](../../docs/sources/community/dnd-5e-srd-markdown/spells.md) establish the scope. The official PDF pages 104–106 distinguish Gaining Spells from Casting Spells. Casting alone omits the sibling learning/preparation rules; do not revive that narrow proposal. Verify Casting's own text and nine existing catalogue members through the current reader.

Row **89** is qualified by the characteristics described in Spells. `spells.casting_spells` is the proposed target: the Spells introduction at line 73 says that section explains the spell-entry information, and [Rules Glossary](../../docs/sources/community/dnd-5e-srd-markdown/rules-glossary.md) line 1317 supplies the qualified citation. Keep this distinct from the unqualified whole-part See Also pointers in rows 87–88.

These nine are ordinary candidate scopes under existing authority, still requiring exact candidate evidence and acceptance. Their disposition does not imply a new route capability or a new Owner policy decision.

## Ten findings held outside that next work

- **34, 36, 54 — exact-target extraction.** Price-bearing actual items, retrievable actual gear with its item rules, and named monster stat blocks in item descriptions require bounded inventories. Row 54's “unless otherwise” exception and already-resolved explanatory sibling must be respected. Broad chapter/category targets would lose source precision. The missing inventories are implementation/evidence work, not automatically Owner Decisions.
- **48, 60 — familiar-form source completeness.** [Find Familiar](../../docs/sources/community/dnd-5e-srd-markdown/spells.md) lines 2281–2303 names eleven forms, then permits another Beast with challenge rating 0. The eleven names are already resolved; row 48's seven special Pact of the Chain forms are also already resolved. Inventory the additional qualifying forms and the intended source extent before retiring either general Monsters occurrence. Do not assert a closed finite list merely from the already-recorded names, or silently decide how an open external option is represented.
- **76 — modifier-selection coverage.** [Playing the Game](../../docs/sources/community/dnd-5e-srd-markdown/playing-the-game.md) line 186 points to which ability modifier applies across D20 tests. An ability-score-to-modifier table alone does not answer that question. Build the precise bounded target route before judging it complete.
- **87, 88 — complete Spells-part coverage.** [Cantrip and Ritual](../../docs/sources/community/dnd-5e-srd-markdown/rules-glossary.md) lines 379 and 1226 have unqualified See Also pointers. Preserve Gaining, Casting, and Spell Descriptions scope. The existing 339 spell records and four embedded creature records with `SCOPED_WITHIN` relationships require a coverage plan; those embedded records are not automatically included by one-hop catalogue traversal. Preserving full scope is coverage work under existing authority. Narrowing the references, inventing a chapter aggregate, or adding recursive consumer behavior would require separate reconciliation.
- **57 — open GM choice.** [Awaken](../../docs/sources/community/dnd-5e-srd-markdown/spells.md) lines 686–687 asks the GM to choose appropriate Plant statistics, “such as” Shrub or Tree. The two examples are already resolved; they do not close the general reference. The treatment of this open choice is a real target/meaning boundary, to be surfaced before implementation rather than patched into an examples-only closed list.
- **39 — retained Spellbook deferral.** The accepted Equipment source does not supply a Spellbook item. Wizard-owned spellbook rules exist, but do not silently satisfy an Equipment-scoped item reference. Keep the explicit deferral; do not invent an item or price or substitute Book. Any remapping outside that accepted scope needs authority reconciliation.

## Preserved gates and workflow

This work adds only this disposition note and updates the restart document's opening summary. It changes no accepted oracle, source, production code, index, secret baseline, stash, protected packet, quarantine, launcher, provider configuration, or automation. No Claude run, acceptance recording, test suite, commit, push, merge, publication, activation, or shared-database write was performed for this disposition.

The partial-publication block remains. The scheduled bounded Owner release-order pass remains **after packets and before publication**, not a prerequisite to preparing or recording an accepted bounded candidate. No other target-contract proposal is accepted. The prior hook's real exit was 1 because the baseline was unstaged; the private-copy exit 0 established content coverage only. Broad-suite success remains unclaimed; pip-audit, expanded mypy, and coverage remain deferred/non-green as described in the linked recorded follow-up. Dependency-vulnerability repairs remain deferred until the CRD Issue 5c Restart is complete.

The local restart-document edit and this supporting evidence belong in the normal restart commit/publication workflow when its gates permit it. Do not extract the document into a standalone PR against main. Preserve all existing in-progress edits and the historical body.
