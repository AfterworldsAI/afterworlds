# `finite-reference-routes` review packet — CRD Issue 5d (#132, #137)

**Status: UNACCEPTED CANDIDATE.** Nothing here is accepted, recorded, published or activated. Exact
candidate acceptance is required before any recording. It must cover both the combat-damage-breaking
replacement and the routes.

**Authority.** The Owner instructions "Next finite reference routes candidate" and "Finite routes:
consolidated source corrections" (2026-10-01); CRD Issue 5d; ADR-005d, including the accepted schema-17
route amendment (Decision 7); and the recorded reference-alternatives follow-up. Inventory IDs are from
`issue-5d-remaining-references-review.md`. The current oracle is authoritative for which occurrences
survive.

## Composition

| | |
|---|---|
| Constructor | `issue-5d-finite-reference-routes-REPLACEMENT.py`, sha `afb1cf88…e9fe3ec`. `--write` writes the three artifacts; with no arguments it checks them |
| Accepted base | `srd-5-2-1-corpus-3fe24ff6-4e3.json`, sha `cc994e1b…c1f190`, schema 17. It is not modified |
| Combat replacement | `issue-5d-combat-damage-breaking-finite-reference-routes-PROPOSAL.json`, sha `1cc561616526b271728f0d8b0b5f2c7490b76ee76cf684e33903512daecf48f5`, 8560 lines. Identity `cfd193513e8c769d45b42f4a6dfa420481b43f064b45fef564f1e5c5eaac8c23`; it replaces `ce7a80ff…a7de2` (REGEN-3fe24ff6) |
| Chain | Composed afresh (acceptance has no supersession): the 24 batches in recorded order at recorded evidence, with combat replaced under the simulated reviewer; every recorded resolution step; then the recorded schema-17 step (`RA.recorded`: lift plus the Owner's 13 resolutions, at its recorded time) |
| Action | One native `resolve_references` call for the routes, under the simulated reviewer. This is not a recording |
| Candidate bytes (in memory, simulated) | sha `b6caeb91e7886d3e0747290751315e59a2852f6e904090b34c2f5a7d14f00f28`. They reload to the same bytes |
| `…-PROPOSAL.json` | sha `404bee285f9695bfdffe5ff5b21d2a2ef2b443cf370a1bdfb3df5332470482d8`, 1194 lines. It pins the combat replacement's file, sha and identities |
| `…-DELTA.txt` | sha `e90abfff64caae94ac4f0fe16f5bc8ef2099ccb702e874fc41a6b874a01d9bca`, 191 lines: the full-text delta from the accepted artifact (evidence blanked), then the effective reference lines (10 removed, 121 added) |
| Counts (batches, records, spans, units, resolutions) | (24, 1835, 10492, 1476, 1453) → **(24, 1835, 10493, 1476, 1463)** |
| Resolutions / routes / destinations | 10 / 94 / 121 |
| Findings (refs, leaves) | (33, 0) → **(23, 0)**: 10 cleared, 0 new. The combat replacement alone changes no finding |

**Controls.**
- The unchanged combat generator rebuilds the recorded REGEN-3fe24ff6 proposal byte for byte.
- The same composition without the replacement is the accepted artifact byte for byte (`cc994e1b`).

**Destination conditions.** Every destination is label-only: no situation, no `class_record_key` and no
minimum level (`_sources` asserts this). None of these conditions is the reader's class. That includes
the Pact of the Tome list's class and the focus users. A class selection therefore removes no route; the
tests pin this with the Elemental Gem and with the Musical Instrument.

**Source check.** `_sources` re-reads each group from the pinned SRD markdown, row by row:
- the spell-list headings;
- the "usable as a Spellcasting Focus" items in Equipment, and every class feature that grants a focus
  (exactly those three plus the Bard's Musical Instrument);
- the Mounts table;
- the three bag tables, the Deck table and its footnote, and the gem and golem tables;
- the Ranged Attacks introduction, verbatim, and the order of the Ranged and Melee sections;
- every sense printed in any stat block, including the six embedded in spells.md and magic-items.md.

It also checks that each destination record or component exists in the candidate, and that each creature
destination is a creature record keyed by its printed name.

## The combat-damage-breaking replacement (#71's landing)

The `### Ranged Attacks` introduction (playing-the-game.md 1072, leaf `90f944fc-9e9b-523a-9098-2ef823d3baf4`)
was framing in the accepted combat batch, so no component held it. `combat_edit` changes the
generator's batch with `dataclasses.replace`; the generator file itself is not edited. The edit:
- removes that one `FRAMING` entry;
- adds the clause `("combat", "ranged", (PROSE,), (<the whole paragraph>,))` before `range`;
- adds the component `play.combat/ranged` (prose-bound, `no_identified_structured_use`) before `range`.
  It equals `melee`'s component except for its key, and it has no references, because the paragraph
  cites nothing.

The leaf, its identity and its ownership are unchanged. It is now a substantive span (`772e5bf8…`,
characters 0–169, the whole leaf) bound to `ranged`. There is no new text, alias, fallback or second
source.

**Dependent changes (all in the full-text delta).**
- **Combat batch.** Its proposal identity and diff (+1 span), and its schema anchor's
  `proposal_identity`. The schema is still 15.
- **Oracle.** One span, one component, one prose binding and one provenance claim. The combat review
  unit drops the leaf from its supporting framing. The combat general-rule obligation lists `ranged`
  among its prose-bound components.
- **Combat acceptance evidence.** The batch rule and 163 span acceptances plus 5 unit acceptances are
  now under the simulated reviewer and time. Recording would put them under the Owner's acceptance.
- **Unchanged.** Every other item is carried verbatim, evidence included, compared as multisets:
  - the 23 other batches and their acceptances;
  - all 1453 resolutions and their 1453 approvals;
  - the lifts and policy transitions;
  - the binding and schema.

  `_preserved` asserts that every differing item belongs to the combat batch or is one of the ten new
  resolutions.
- **Not touched.** No historical approval, generator, protected packet or index is changed.

## Dispositions (all ten resolved)

Routes are listed in drafted order. Within a route, the first destination is the landing and the rest
are support, all in source order. A destination with no component (`""`) is the whole record.

| Row | Citation (exact occurrence) | Routes → destinations | Meaning |
|---|---|---|---|
| #23 | `classes.warlock.eldritch_invocation_options.pact_of_the_tome/cantrips_and_rituals`, "any class's spell list" | 8 routes (22 destinations): `<Class> spell list: cantrips; level 1 spells with the Ritual tag` → `classes.<c>/spell_list`, `/cantrips`, `/level_1_spells`, for Bard, Cleric, Druid, Sorcerer, Warlock and Wizard. Paladin and Ranger use the label "no cantrips;" and have no `cantrips` destination | The class is the *list's*, so none is class-gated. The intro defines the R tag, and the tables are exactly the cantrip and level-1 tables the source restricts the choice to. The source's "don't already have prepared" restriction stays in the citing text |
| #38 | `spells.components/component_pouch_and_focus`, `see "Equipment" for descriptions` | 5 routes (6 destinations), in equipment.md order: **Musical Instrument** → `equipment.tools.musical_instrument` (landing), then `classes.bard.spellcasting/spellcasting_focus`; Arcane Focus, Component Pouch, Druidic Focus, Holy Symbol → `equipment.adventuring_gear.<item>` | "Descriptions" (plural) closes the sentence on both the pouch and the focus. Each focus label quotes who may use it. The instrument's grant is printed in the Bard's Spellcasting feature (classes.md 846), not in its Equipment entry (equipment.md 746–749). That feature is therefore the companion that carries the condition, as text and label; it is not a class gate. The spell rule's "a feature that allows that substitution" stays in the citing text. These are alternatives, not a requirement to own every item. The resolved sibling `'Component Pouch'` has different `source_text`, so the two do not collide |
| #49 | `equipment.mounts_and_vehicles/mounts`, "Monsters" | 8 routes, in table order: Camel, Elephant, Horse Draft, Horse Riding, Mastiff, Mule, Pony, Warhorse → `animals.<x>` | All of "the animals' stat blocks" |
| #51 | `magic_items.bag_of_tricks/bag_of_tricks`, "Monsters" | 24 routes `<Colour> Bag of Tricks, 1d8 roll <n>: <creature>` → 23 `animals.*` + `monsters.axe_beak.axe_beak` | Labelled by bag colour and roll. There is no roll selector |
| #52 | `magic_items.deck_of_illusions/deck_of_illusions`, "Monsters" | 32 routes `Deck of Illusions, 1d100 <band>: <creature>` → the creature record | One creature per card in this release. **97–00 "The card drawer" has no route**, because the footnote excludes it ("except the card drawer") |
| #53 | `magic_items.elemental_gem/elemental_gem`, "Monsters" | 4 routes `<gem>: <elemental>` → `monsters.<x>_elemental.<x>_elemental` | Labelled by gem type. There is no gem selector |
| #55 | `magic_items.manual_of_golems/manual_of_golems`, "Monsters" | 4 routes `<Golem> manual (1d20 <band>, or the GM's choice)` → `monsters.<x>_golem.<x>_golem` | The label keeps the source's "GM chooses or rolls" |
| #71 | `monsters.parts_of_a_stat_block/attack_notation`, "Playing the Game" | 3 routes (14 destinations): **Melee attack** → `play.combat/melee`, `reach`, `opportunity_attacks`; **Ranged attack** → `ranged` (landing: the section introduction), `range`, `long_range`, `close_combat`; **Melee or Ranged attack** → all seven, Ranged first (source order 1070 < 1084) | Each route is a whole `###` section, its introduction first, through its bound components. Opportunity Attacks is included because it is part of `### Melee Attacks`. The combined route is for stat blocks that print "Melee or Ranged Attack Roll" (19 do in monsters-A-Z). The "Spells" sibling was already resolved |
| #73 | `monsters.parts_of_a_stat_block/senses`, "Rules Glossary" | 5 routes: `Passive Perception: every Senses entry` → `glossary.passive_perception`; `Special sense, when listed: <S>` → `glossary.<s>` for Blindsight, Darkvision, Tremorsense, Truesight | Passive Perception applies to every monster. Each special sense is a separate route that applies when the sense is listed. Routes are not exclusive. The four are every special sense printed in any stat block in the release: monsters-A-Z.md, animals.md, and the six embedded in spells.md (4) and magic-items.md (2), which add no kind. The glossary itself does not close the set |
| #54 (explanatory only) | `magic_items.magic_items_a_z/magic_items_a_z`, `How to read and use a stat block is explained in "Monsters."` | 1 route, 2 destinations: `monsters.stat_block_overview` (landing), then `monsters.parts_of_a_stat_block` | This is the whole Monsters chapter. Challenge Rating is a CATALOGUE_MEMBER of Parts, so it is reached without a third destination |

**Out of scope.** The other #54 occurrence, `the stat block is in "Monsters."`, is not drafted and stays
unresolved; the findings and a test confirm it.

## Verification

| Check | Result |
|---|---|
| Constructor `--write` (logged via `rtk proxy`, `.claude/_sp/frr/write.log`) | exit 0; prints `OK` |
| Constructor check mode on the final constructor (`check.log`) | exit 0; the same three artifact hashes |
| Black, Ruff, mypy `--strict` on the constructor and the test | clean |
| `scripts/run_focused_tests.py --check <constructor> tests/ingestion/mechanical/test_finite_reference_routes_candidate.py` | **17 passed** (`focused.log`, exit 0). This is FOCUSED DIAGNOSTICS ONLY, not acceptance evidence |

The test composes the candidate natively and persists it into a private release copy. It then reads it
through `RulesAuthorityService.citation_view`:
- every row's routes equal the drafted ones, in order;
- a class selection keeps all 4 gem routes;
- Ranged reads `ranged`, `range`, `long_range`, `close_combat`, and Melee or Ranged reads those then
  Melee. The `ranged` governing prose equals the source paragraph exactly, and each other scoped rule
  carries its text;
- the Musical Instrument route lands on the instrument, with its `musical_instrument` component, then
  the Bard grant ("Musical Instrument as a Spellcasting Focus for your Bard spells"). This holds both
  with no selection and under a Wizard selection;
- the stat-block route lands on the overview and reaches Challenge Rating;
- a disabled destination (`animals.camel`) refuses, while an unrelated override applies;
- the out-of-scope occurrence is undrafted.

Reused unchanged: the earlier native and preservation evidence for the eight unaffected mappings, and the
accepted source, schema, consumer and serialization evidence. The only chain work was two in-memory
compositions per run (the control and the candidate, about two minutes each). No historical recording
was rebuilt or rewritten.

**Not green / not run:**
- pip-audit, expanded mypy, the coverage threshold and the broad suite.
- The scoped detect-secrets result and the final hooks are reported in the completion report.

## Boundaries

There are no retained findings and no new semantics: the existing schema-17 fields and consumer, and the
existing schema-15 combat authoring, are used unchanged. The source-supported limits are:
- the card-drawer result has no stat block;
- the special-senses set is closed by release usage, not by the glossary;
- the "Melee or Ranged" route is a labelled reading aid, not a selector;
- the Bard grant is a companion destination and label, not a class gate.

Recording this candidate would replace the accepted combat batch's acceptance. That needs the exact
candidate acceptance named above.
