# CRD Issue 5d — Equipment review packet, corrected release, one record per named item (UNACCEPTED) (#132, #137)

This packet is for Codex's independent review and the Owner's later semantic acceptance. It does not ask for acceptance.

- Nothing is accepted, recorded, committed, pushed, published or activated. No shared DB or Chroma was written.
- The simulations in §5 ran in memory, or against a private temporary copy of the release DB.
- The approved oracle and `.secrets.baseline` are byte-identical before and after (§1).

**What changed in this pass.** It implements the Owner's approved bounded correction, *Equipment: one item wherever it is displayed* (2026-09-24, "I approve the bounded correction"):
- A named Equipment item or rule has one authoritative record.
- Its section reaches that record as a `CATALOGUE_MEMBER` and no longer reads the member's text itself.
- The section's own text and its members' passages read together in original source order. Each passage reads at its own printed position, so a gear item with an early table row and a later description reads in two runs of one effective record (settled implementation of the approved decision, 2026-09-24 follow-up).
- A disabled member stays gone, a replaced member reads replaced, and a section selected with its member returns the member once.

In-Equipment citations of items (Club, Shield, Bullet, …) now count as cited items. ADR-005d is amended under Decisions 3, 7, 9 and 10.

**Governing-context completion (this pass).** A consolidated authoring finding under the same approved exact-target/one-authority behavior; not a new Owner decision:
- A named record read directly now keeps the section rules that govern it, as CONTEXTUAL bindings on the entry's reviewed spans (the section's, or for Calligrapher's Supplies also the `artisans_tools` member's): each mastery (Nick, Sap, Slow, Topple, Vex) reads the *Mastery Properties* gate (printed 90); each named weapon row reads *Mastery* and *Weapon Proficiency* (printed 89); Padded and Hide Armor read *Armor Training*, its Light/Medium/Heavy clause and *One at a Time* (printed 92), and the Shield reads *Armor Training* around its clause and *One at a Time*; each named tool reads *Utilize* and *Tool Proficiency* (printed 93), the Gaming Set also *Variants*, and Calligrapher's Supplies also the *Artisan's Tools* rule.
- Torch's "Simple Melee weapon" is two pointers: "Simple" → `weapons.category` and "Melee" → `weapons.melee_or_ranged`, as a weapon row's group row cites them. The earlier claim that *Category* defines both was false.
- A pointer is cited from the component's own words that print it; only one its own words do not print is cited from its context (`authoring.py`).

## 1. Exact artifacts

| Artifact | SHA-256 / identity |
| --- | --- |
| Approved oracle `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-626c83f8-209.json` (context; unchanged) | `7b1d6f43c322adbd662f94cb941c58a9ec54dde0fca5bef42465c940459abdd8` |
| `.secrets.baseline` (unchanged) | `ba1478408976dc11aa18103aad3f7bbd5efbe262f45257d40f224fd91420099f` |
| Corrected source `docs/sources/community/dnd-5e-srd-markdown/equipment.md` (unchanged) | `ba4d96bf7c08a44103b11be1ae5385e6e09f3f5478d56c3a2f38f97bd77d645b` |
| `issue-5d-equipment-REGEN-626c83f8-PROPOSAL.json` | `c33e7473c881624a0bc5700369899df69567672bb4cb220e751303f98ce19430` |
| Proposal identity | `e25f7a82617ccca7bdf3282d775917d716fd37c83d35cdebf7bceea8c2758b87` |
| `issue-5d-equipment-resolutions-REGEN-626c83f8-DRAFTS.json` (43 drafts; unchanged by this pass) | `1d92207bf791833464083a77081801eae54fbdbd69f37f897829e32bc6b5c569` |
| `issue-5d-equipment-generator.py` | `732e0da55f23e5ca44e228abe898f7d6c98c573e47098b29f7ba98433e8e43e9` |
| `src/afterworlds/ingestion/mechanical/authoring.py` (modified) | `8a11adeeea1c062c2ba76ef5196f96a13e37916553341aad2eed261947c44a89` |
| `src/afterworlds/services/rules_authority/application.py` (modified) | `f9df3060d0a9a075561e530b6041dcb259891b332c6832df46432f682f945cf4` |
| `src/afterworlds/services/rules_authority/service.py` (modified) | `196408b5507c8eb02afbc4d3a196432cf9ade8dfeacce28e9790164b8cd953fb` |
| `src/afterworlds/services/rules_authority/views.py` (modified) | `49b76a27963290440e307fb141450df2bea779d38e429ff6aa0055e215b7592c` |
| `tests/ingestion/mechanical/test_equipment_proposal.py` (modified) | `b8135b6733e7d1bc23be8dbeec3594cf264c51d8b595a605888c5ce054d90321` |
| `docs/decisions/adr-005d-complete-typed-mechanical-authority.md` (amended) | `c51805846adcee713d436eca4954282c4241d8404fe9ecaa0c23db51691e0bd9` |

- **Line endings.** Hashes are of the LF working-tree bytes, matching the repository's LF convention. Earlier passes reported CRLF working-copy hashes for `authoring.py` (`18423b4a…`) and `service.py` (`a310dfd0…`); those files' content is otherwise unchanged by this pass. The equipment generator was CRLF in the working copy and is now LF.
- **Superseded.** The one-record-per-item identity `2d2cc613…` (file `4d012616…`, generator `53eb2e0d…`) and the item-grain proposal identity `df9f401e…` (file `0e643861…`) with its generator `212e2a10…` are superseded. The drafts are unchanged, because every draft target was already a named record.
- **Release binding.** Package `0b1a965e-28bd-55e6-ac13-bc7786a1bace`, release `5.2.1-corpus.626c83f8-209`.
- **Hashes against the oracle.** `representation_schema_hash` is `7fb9254b11da1d6772ea6ee72ffde9b5e9d39e8885188777874c65e86ad9a941`, schema 16, equal to the oracle's. No schema version, kind or hash changed. The policy is `5d-semantic-policy-2` / `da63b894…`, equal to the oracle's.
- **Derivation.** The proposal was regenerated from the generator against the published release. `test_the_committed_bytes_are_what_the_published_release_derives` passes.
- **Proposal counts.**

  | Leaves | Spans | Records | Components | Facts | Bindings | References | Relationships | Provenance |
  | --- | --- | --- | --- | --- | --- | --- | --- | --- |
  | 375 | 409 | 80 | 207 | 0 | 512 | 187 | 66 | 768 |

  Against `2d2cc613…`: 43 CONTEXTUAL prose bindings added (8 weapon rows × 2, 5 masteries, Padded and Hide × 3, Shield 2, tools 14); Torch's one pointer became two on the same span; the Shield's "Armor Class" pointer no longer also cites the Armor table head, since its own clause prints it (a misattribution corrected by the owned-first rule). No other reference, relationship or PRIMARY binding changed.

  The 80 records are the 14 section records and 66 named records. Each named record has one `catalogue_member` edge to its section.

## 2. Existing approved context vs new Equipment meaning

**Existing approved context.** None of this changes:
- the 12 accepted batches;
- 136 records and 1016 spans;
- the six recorded resolutions;
- the schema-16 `catalogue_member` vocabulary;
- the 91 retained reference findings. 45 of them are Equipment citations, all accepted with empty targets.

The accepted catalogues (character origins, feats) still read as before. The prior-catalogue tests in `tests/services/rules_authority` and the origins-feats modules pass (§7).

**New Equipment meaning**, which is everything Codex judges here:
- the 14 section records and 66 named records;
- their 207 components and prose handling;
- the membership edges;
- the in-batch pointers;
- the new unresolved pointers and one unknown target;
- the 43 destinations the drafts assign.

## 3. Design

**Contract.** ADR-005d is amended: Decision 9 (main text), with cross-references under Decisions 3, 7 and 10. No schema change, no new relationship kind, and no acceptance carryforward.

**Authoring** (`authoring.py`):
- A batch declares each named record with its one entry (`EntryBatch.records`).
- A component may name only a record declared for its own entry. Otherwise it raises "X is not a declared record of entry".
- Every text a component reads must be a reviewed text of that same entry. `spans` is keyed by `(entry, text)`, so containment is structural: a row of another section raises "reads unreviewed".
- A member owns its texts as PRIMARY. Its table head and group row, and the section rules governing it, are CONTEXTUAL (`context`). Context may be any reviewed text of the same entry, including another member's (Calligrapher's Supplies reads the *Artisan's Tools* rule).
- A pointer is cited from the component's own texts that print it; only a pointer none of its own texts print is cited from the context texts that do.
- The section may not bind any span a member owns: "section … rereads … owned by …".
- Each record gets one `CATALOGUE_MEMBER` edge, member → section. It carries CONTEXTUAL `RELATIONSHIP` provenance on the member's first owned span, which is the position the section reaches it at.
- Whole-entry catalogue declarations under the 2026-09-23 amendment keep their container check unchanged.

**Consumer** (`application.py`, `views.py`, `service.py`):
- `EffectiveAuthority.readings` gives, per surviving section, runs `(record key, component key, indices into its governing prose)` in source order.
- Every passage the section or a surviving member owns (PRIMARY `PROSE_BINDING`) is placed at its own (leaf order, offset). Consecutive passages of one component form a run, so a member printed in two places reads in two runs of the same effective record.
- Context a member reads (table head, group row, governing rule) is not placed: its owner reads it once, where printed. A direct member read still carries it, in printed order around its own texts. A combined direct read of two members that share context (two masteries, two weapon rows, with no section selected) carries it in each member; that is two direct reads, not a section-view duplicate.
- Authored text has no printed position: it follows the passage it follows in its component or, with none, sits at the member's `CATALOGUE_MEMBER` position. No source provenance is invented for it.
- Members are reached only from `CATALOGUE_MEMBER` edges, after overrides.
- **Context suppression.** After overrides, a span whose PRIMARY owner no longer reads it (disabled or replaced) is stripped from every other component that reads it as context, so it cannot come back through another member.
- The GameMaster view is a flat walk over the readings with a `read` set, so each record appears once; a selected member already reached by its selected section is not read again.
- A section narrowed by a component selector reads only the selected components. Its members are not reached through it.
- A member selected beside a narrowed section is read directly, with its own head and group context, because the narrowed section does not supply them. Probe: `armor/strength` + Shield + Padded Armor reads the armor head once in each member (not pinned by a test).
- A split run carries its component's full `span_ids`, while `governing_prose` holds only that run's passages. Antitoxin's two runs therefore share `span_ids`. This already held for section runs and is new for members.
- The rule slice and typed view still list the section and then its members.

**The 66 named records** (`equipment.<section>.<key>`):

| Section | Records |
| --- | --- |
| weapons (23) | rules: `ammunition`, `category`, `finesse`, `light`, `loading`, `melee_or_ranged`, `nick`, `range`, `sap`, `slow`, `thrown`, `topple`, `two_handed`, `versatile`, `vex`; rows: `club`, `dagger`, `light_hammer`, `musket`, `quarterstaff`, `shortbow`, `sling`, `spear` |
| armor (6) | rules: `armor_class`, `category`, `stealth`; rows: `hide_armor`, `padded_armor`; `shield` (row and clause) |
| tools (5) | `artisans_tools` (rule), `calligraphers_supplies`, `gaming_set`, `herbalism_kit`, `thieves_tools` |
| adventuring_gear (32) | `acid`, `antitoxin`, `arcane_focus`, `arrows`, `backpack`, `ball_bearings`, `barrel`, `basket`, `bell`, `block_and_tackle`, `book`, `bottle_glass`, `bullets_firearm`, `bullets_sling`, `climbers_kit`, `clothes_travelers`, `costume`, `crowbar`, `druidic_focus`, `healers_kit`, `holy_symbol`, `ink`, `jug`, `map`, `parchment`, `poison_basic`, `potion_of_healing`, `pouch`, `quiver`, `rations`, `robe`, `spell_scroll` |

Scope: the named targets of the 43 drafts, the items and rules Equipment's own pointers cite, and the rules needed to interpret the cited rows. The latter are each property, mastery, category, range and loading/slow cited by a named weapon row, and the armor category, Armor Class and Stealth cited by the named armor rows. Uncited items remain the section's own components.

**Split tables.**
- The Weapons, Armor, Adventuring Gear and Ammunition tables are cut at row boundaries into contiguous pieces. The pieces rejoin byte-for-byte to the release table (tested).
- A named row is its own span, owned by its record. The head and group rows are the section's, and the member reads them as context.
- Column headers, group rows, units, prices, quantities and qualifications are preserved.
- A named gear item's row reads among the gear-table rows and its priced heading and body read where printed. Read directly, the item reads its table head, row, heading and body.
- **Source-order observation.** In the release's leaf order, the descriptions of Acid, Alchemist's Fire and Ammunition precede the gear table, so Acid's description reads before its row.

## 4. Source coverage and table/group correctness

- **Scope.** 375 leaves in 14 section records, one review unit each. These are the 14 `##` sections of *Equipment*, pp. 89–103, in printed order. The only excluded leaf is the part title `# Equipment`.
- **Handling.** Every component is prose-bound, and none carries structured facts.
- **Corrected release (families I and J).** Food, Drink, and Lodging has 21 rows. The Tack "Saddle" group and the vehicles caption are present.
- **Test pins** (`test_equipment_proposal.py`):
  - each table is the release's own rows, and split tables rejoin;
  - named rows are held by their record alone, and every other piece by the section;
  - each priced heading stays with its item (81 gear entries: 52 section, 29 named);
  - every word of every spanned leaf is claimed;
  - the whole-package GameMaster view reads exactly the PRIMARY spans, each once, in printed order (409 passages; 120 components read more than one passage, 81 across unlike chunks);
  - a row missing from the middle of a piece is a loud locate failure (the test now asserts the cut is a real gap);
  - the membership behaviors in §5.

## 5. Native simulation and regressions

**Composition** (in memory, against the approved chain):
1. `through()`, byte-equal to the approved oracle `7b1d6f43…`.
2. `accept_proposal` of this proposal.
3. `resolve_references` with all 43 drafts.
4. `reference_resolution_violations` and `validate_candidate` of the composed oracle.

Results:
- 216 records and 49 resolutions (6 approved + 43 drafts). `reference_resolution_violations` is empty.
- `validate_candidate` gives 9,126 findings:
  - **9,068 leaf findings**: the corpus outside accepted batches. This includes Equipment's own no-acceptance-record findings until acceptance.
  - **58 reference findings:**
    - 57 unresolved references: spells 26, classes 16, gameplay-toolbox 4, playing-the-game 4, monsters 2, magic-items 2, rules-glossary 1, equipment 2.
    - 1 unknown target, `glossary.improvised_weapons`.
  - The only Equipment-scope findings are the two whole-part "Equipment" citations, intentionally unresolved.
- The durable evidence is `test_composed_every_glossary_target_closes_and_375_leaves_gain_coverage` and `test_once_accepted_all_drafts_resolve_through_the_native_seam`. The scratch probe `.claude/_rc/probe_compose.py` (not committed) corroborates them.

**Consumer behavior** through `RulesAuthorityService` over a draft persisted into a private copy of the release. Only binding resolution is stood in. Each row is a test:

| Test | Pins |
| --- | --- |
| `test_a_section_reads_its_members_where_they_are_printed` [weapons, armor, adventuring_gear, tools] | slice = section, then members in printed order; the **complete resolved passage sequence** equals the sorted printed positions of every PRIMARY span of section and members, and no passage is read as context |
| `test_the_weapons_table_reads_its_rows_in_printed_order` | Simple Melee rows read Club…Spear in source order, member rows (Club, Spear) owned by their records, Greatclub by the section |
| `test_direct_section_and_combined_selections_read_a_member_once` | spear alone = *Mastery*, *Weapon Proficiency*, head, group row, Spear row; `weapons`+`spear` in either order = `weapons` alone, spear once |
| `test_a_component_selector_on_a_section_reads_no_member` | `armor/strength` reads only that component; with all armor members also selected, every passage is read once (Shield reads in two runs) and the section still contributes only `strength` |
| `test_a_disabled_member_is_not_brought_back_by_its_section` | DISABLE spear: absent from slice and view, its row text gone, neighbouring rows kept; direct selection is `invalid_reference` |
| `test_a_replaced_member_reads_replaced_where_it_is_printed` | REPLACE `weapons.spear/spear` with authored prose: it reads at spear's position, between the Sickle row and the *Simple Ranged Weapons* group row; the source row is not read |
| `test_a_gear_item_reads_its_row_and_description_each_where_printed` | gear head read once, by the section; Antitoxin reads two runs: its row between the gear-table rows before it and the Arcane Focus row, its description after the Ammunition component and before Arcane Focus's; Acid mirrors this with its description first; direct Antitoxin = head, row, heading, body; `adventuring_gear`+`antitoxin` = section alone |
| `test_a_disabled_or_replaced_gear_item_leaves_the_sequence_whole` | DISABLE Antitoxin: whole sequence minus exactly its owned positions; REPLACE: one authored run at the row position, same neighbours, otherwise equal to the disabled sequence |
| `test_a_suppressed_row_is_not_read_again_as_another_row_s_context` | with Spear made to read the Club row as context, the row is read once, by Club; after DISABLE or REPLACE of Club it is absent from Spear's effective prose and from the whole view |
| `test_each_named_record_is_a_catalogue_member_of_its_section` | edges are exactly `catalogue_member` member → declared section; no `scoped_within` |
| `test_a_named_component_outside_its_declaration_fails_loudly` (7 cases) | undeclared record; record of another section ("not a declared record of weapons"); unreviewed text; another section's row ("reads unreviewed"); context not read; STRUCTURED; section rereading a member's rows |
| `test_a_citation_naming_an_item_or_rule_targets_that_record` | every draft target is a named record owning the cited wording |
| `test_in_batch_pointers_name_the_record_of_what_they_cite` | Club, Shield, Musket, Padded Armor, Light Hammer, both Bullets, Potion of Healing name their records; Torch's "Simple" → `weapons.category` and "Melee" → `weapons.melee_or_ranged`; only 7 section-as-such pointers target sections |
| `test_a_named_record_read_directly_keeps_the_rules_governing_it` | exact direct `governing_prose`: Gaming Set = *Utilize*, *Variants*, *Tool Proficiency*, its clause; Thieves' Tools = *Utilize*, *Tool Proficiency*, its clause; Calligrapher's adds *Artisan's Tools*; Sap/Nick/Slow/Topple/Vex = *Mastery Properties*, the effect; Club = *Mastery*, *Weapon Proficiency*, head, group, row; Padded Armor = head, group, row, *Armor Training*, LMH clause, *One at a Time*; Shield = head, group, row, *Armor Training*, Shield clause, *One at a Time*; in the section views each of those rules is read once, by its section component |
| `test_a_pointer_cites_its_own_words_before_its_context` | every Equipment pointer cites exactly its own spans that print it, or else the context spans that do; Padded's "Disadvantage" cites only its row |
| `test_a_suppressed_governing_rule_is_not_read_through_a_named_record` | DISABLE `tools.artisans_tools`: Calligrapher's direct read loses that rule; REPLACE `armor/armor_training`: Padded's direct read loses the training text and does not read the replacement |

## 6. Codex fidelity questions

1. **Shared context — settled.** In a section view the head and group rows read once, where printed; a direct member read keeps them. (Settled implementation of the approved source-order requirement, not a new rule.)
2. **Torch "Simple Melee weapon" — corrected.** The earlier single target `weapons.category` was wrong for Melee. "Simple" → `weapons.category`, "Melee" → `weapons.melee_or_ranged`. Codex should confirm the correction.
3. **Shield — resolved by Codex** (row under its group row, with its clause).
4. **Bullets — resolved by Codex.**
5. **Gear member position — settled.** Each owned passage reads at its own printed position (two runs for a row-plus-description item). The earlier ADR sentence saying the Owner had not decided this was reconciled: the approved decision requires original source order.
6. **Armor-category target — resolved by Codex.**
7. **Governing context.** Codex should confirm the passages each named record reads directly (the `test_a_named_record_read_directly_keeps_the_rules_governing_it` row above) are the applicable rules, and that none is missing or extra.

Questions 2 and 7 are open for Codex and are not pre-approved. Codex still completes the full source, table and reference review.

## 7. Boundaries and gate status

- **No publication or activation.** No shared DB/Chroma write, commit or push.
- **Gates (final tree, governing-context pass).** Black and Ruff are clean on `src/`, `tests/` and the generator. mypy strict on `src/` reports no issues (235 files). pytest (`--no-cov`, attached, run once on the settled bytes): gate A 739 passed, EXIT 0, for the Equipment module (102 tests), `tests/services/rules_authority`, schema identity, committed accepted authority, oracle and accepted-inputs; gate B 424 passed, EXIT 0, for every other batch's proposal and acceptance module, rerun because `authoring.py` is shared; it proves the accepted batches' bytes and replay unchanged. The earlier 736/424 logs are superseded. The unchanged full suite was not repeated.
- **Owned-first citation coverage.** Both branches of the changed `authoring.py` rule run on real proposal data under `test_a_pointer_cites_its_own_words_before_its_context`: owned (e.g. Padded's "Disadvantage" → its row) and the context fallback (18 pointers, e.g. each weapon row's "Simple"/"Melee" from its group row, Padded's "Light Armor"). Argued from the proposal, not a separate coverage run.
- **Coverage** (previous pass; the consumer is unchanged by this one. Equipment module + `tests/services/rules_authority`, 529 passed): `application.py` 96%, `service.py` 96%, `views.py` 99%. The run exits 1 only on the repository-wide `fail-under=80` for a partial run. Two new defensive lines are uncovered: `application.py:1026`, a member component with no passage left to place, and `views.py:258`, a run of a record already read, which only nested membership could reach (none exists in either proposal).
- **Guard gap at the touched seam — closed in the consumer.** A disabled or replaced member's owned passage is stripped from every other component's context after overrides (`_without_suppressed_context`), tested with Spear made to read Club's row. Authoring still does not refuse a member's `context` naming another member's span, and this batch now has one such read: Calligrapher's Supplies reads the `artisans_tools` record's rule. The consumer strips it when that record is disabled or replaced (tested for disable). The broader authoring check was not audited, by instruction.
- **pip-audit.** Still deferred and non-green (31/11), unchanged.
- **detect-secrets.** The pre-commit hook (baseline unchanged) exits 1 only on public, non-secret hashes: PROPOSAL lines 24925, 24926, 24928, 24930, 24933, 24936 (`authoritative_source_hash 8974902d…`, `bundle_root_hash 0f49f740…`, `persisted_corpus_digest 81009ec8…`, `transform_config_hash eaa19d76…`, schema hash `7fb9254b…`, `semantic_policy_hash da63b894…`); DRAFTS lines 12–15 (the same binding hashes); test line 136 (`IDENTITY e25f7a82…`). The source files, ADR and this packet are clean. These are collected for Owner terminal handling; the baseline was not edited or rescanned.
- **Not committed.** Nothing is committed, because required gates are unresolved (pip-audit, and the detect-secrets delta awaiting Owner terminal handling).
- **Stale file left untouched.** `issue-5d-source-correction-REPLACEMENT-PACKET.md` is untracked and stale. Its edits were denied (Auto-Mode Bypass), and it is untouched by instruction.
- **Remaining review.** Codex independently reviews this result, then the Owner decides semantic acceptance. Equipment stays unaccepted.
