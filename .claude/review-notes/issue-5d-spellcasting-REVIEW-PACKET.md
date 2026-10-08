# CRD Issue 5d — General spellcasting rules review packet (UNACCEPTED) (#132, #137)

This packet is for Codex's independent review and the Owner's later semantic acceptance. It does not ask for acceptance.

- Nothing is accepted, recorded, committed, pushed, published or activated. No shared DB or Chroma was written.
- The simulations in §5 ran in memory, or against a private temporary copy of the release DB.
- The thirteen-batch oracle and `.secrets.baseline` are byte-identical before and after (§1).
- Remediation round 1 changed the consumer (`application.py`, `service.py`) so a record reads its components in printed order, and ADR-005d Decision 9's descriptive consumer text to match (§5, §6). The authoring module is the one recorded with Equipment.

**Batch.** The complete general spellcasting rules of *Spells* that precede *Spell Descriptions*, plus the unauthored Rules Glossary entries those rules point at directly: *Area of Effect*, its six shapes (Cone, Cube, Cylinder, Emanation, Line, Sphere) and *Cover*. The *Classes*, individual spells, *Monsters* and *Magic Items* are not expanded. Out-of-scope citations stay explicitly unresolved.

## 1. Exact artifacts

| Artifact | SHA-256 / identity |
| --- | --- |
| Thirteen-batch oracle `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-626c83f8-209.json` (context; unchanged) | `08cca0b77b6554f585af471de242c81f58502490f9832840a44c32998c7803fb` |
| `.secrets.baseline` (unchanged) | `971e66b2f8fc326788d6462fb76e5697863a45c18496c089835d105430c34899` |
| Source `docs/sources/community/dnd-5e-srd-markdown/spells.md` (unchanged) | `767d50542d8f26a9fff4a0c101ab48df4845a055d70734fee6e9e37d2e821aeb` |
| Source `docs/sources/community/dnd-5e-srd-markdown/rules-glossary.md` (unchanged) | `3fa8904be1e84bfafda24bf673c5e30ad899bd4135809a4c4dfd1d738f0d5ead` |
| `issue-5d-spellcasting-REGEN-626c83f8-PROPOSAL.json` | `3dbdae694829b37cae91f929e3fe552f750178276f5f338f80e208c341764af3` |
| Proposal identity | `0b7f14ffbea2240adbbd7a88ac439a3955ca417b563f89ee1b35e15f94ec1d55` |
| `issue-5d-spellcasting-resolutions-REGEN-626c83f8-DRAFTS.json` (1 draft; bytes unchanged by remediation) | `72bcdc5ff1849acef5c15bb1606921ee8a2cd61ab5756ddac7841122e852fc2a` |
| `issue-5d-spellcasting-generator.py` | `20c759dcf0f9c5097238b942e60429d5c72e186fba80803f8c55e657d6258aae` |
| `tests/ingestion/mechanical/test_spellcasting_proposal.py` (new) | `e893ff34ab36b85e7a46fb41d0d38ee3ae5da74025629fb7f0359484e458e2a0` |
| `src/afterworlds/ingestion/mechanical/authoring.py` (unchanged by this batch) | `8a11adeeea1c062c2ba76ef5196f96a13e37916553341aad2eed261947c44a89` |
| `src/afterworlds/services/rules_authority/application.py` (changed; Equipment packet `f9df3060…`) | `67688a5c5f107e9c2a042f764c7f55920728dda2e107a24534bf4b088f02813b` |
| `src/afterworlds/services/rules_authority/service.py` (changed; Equipment packet `196408b5…`) | `bd9c82975a9c3581793bc97ba0c7b3fbfec5b020f9c3a7d3d4d2d53c448e8b3f` |
| `src/afterworlds/services/rules_authority/views.py` (unchanged; = Equipment packet) | `49b76a27963290440e307fb141450df2bea779d38e429ff6aa0055e215b7592c` |
| `docs/decisions/adr-005d-complete-typed-mechanical-authority.md` (Decision 9 consumer bullet, descriptive) | `64ffa0496d3ada432d690adc0ea4bab220be71d25160b52ceb130d069f16dc9f` |
| `issue-5d-source-correction-REPLACEMENT-PACKET.md` (denied; untouched) | `e462e235b01f8d3ffb8d879724504a9a3243479262a5600d33e92705c410cae1` |

- **Line endings.** All new files are LF with zero `\r` bytes.
- **Release binding.** Package `0b1a965e-28bd-55e6-ac13-bc7786a1bace`, release `5.2.1-corpus.626c83f8-209`.
- **Hashes against the oracle.** Schema `5d-representation-schema-16` / `7fb9254b…`, policy `5d-semantic-policy-2` / `da63b894…`, both equal to the oracle's. No schema, kind or policy change.
- **Derivation.** The proposal is regenerated from the generator against the published release; `test_the_committed_bytes_are_what_the_published_release_derives` passes. The draft was written by the scratch script `.claude/_sp/regen_spellcasting_drafts.py` (not committed) and `test_the_committed_drafts_are_what_the_generator_drafts` pins it.
- **Proposal counts.**

  | Leaves | Spans | Records | Components | Facts | Bindings | References | Relationships | Provenance | Units |
  | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
  | 104 | 72 | 19 | 55 | 0 | 70 | 39 | 0 | 115 | 19 |

## 2. Existing approved context vs new meaning

**Existing approved context.** None of this changes:
- the 13 accepted batches, 216 records and 1425 spans;
- the 49 recorded resolutions;
- the accepted glossary entries this batch cites (Attack Roll, Concentration, Hostile, Incapacitated, Long Rest, Magic, Reach, Study);
- the accepted `play.combat` record, and the accepted Equipment part (no Equipment record is cited or changed).

No leaf of this batch is owned by an accepted unit, and no record key collides (tested).

**New meaning**, which is everything Codex judges here:
- 11 `GENERAL_RULE` section records (`spells.<slug>`) and 8 `GLOSSARY_RULE` records (`glossary.<slug>`);
- their 55 prose-bound components;
- 39 references;
- one resolution draft for an accepted citation.

## 3. Design

**Records and units.** One record and one review unit (`spellcasting/<slug>`) per section or entry:

| Record | Unit leaves | Components (printed order) |
| --- | --- | --- |
| `spells.gaining_spells` | 8 | gaining_spells, preparing_spells (+ Spell Preparation by Class table), monster_prepared_spells, always_prepared_spells |
| `spells.casting_spells` | 22 | casting_in_armor, spell_level, spell_slots, slot_recovery, casting_without_slots, cantrips, rituals, special_abilities, magic_items, higher_level_slot, school_of_magic (+ Schools of Magic table), class_spell_lists |
| `spells.casting_time` | 8 | casting_time, one_slot_per_turn, triggers, longer_casting_times |
| `spells.range` | 7 | range, distance, touch, self, movable_effects |
| `spells.components` | 9 | components, verbal, somatic, material, component_pouch_and_focus |
| `spells.duration` | 5 | duration, concentration, instantaneous, time_span |
| `spells.effects` | 2 | effects |
| `spells.targets` | 8 | targets, clear_path, targeting_yourself, areas_of_effect, awareness_of_being_targeted, invalid_targets |
| `spells.saving_throws` | 3 | spell_save_dc |
| `spells.attack_rolls` | 3 | spell_attack_modifier |
| `spells.combining_spell_effects` | 3 | combining_spell_effects, identifying_an_ongoing_spell |
| `glossary.area_of_effect` | 5 | area_of_effect (+ shapes table), point_of_origin, unseen_point |
| `glossary.cone`, `cube`, `cylinder`, `line`, `sphere` | 3 each | one component each |
| `glossary.emanation` | 4 | emanation |
| `glossary.cover` | 2 | cover |

- **Excluded:** only headings. That is the 19 unit headings plus 14 subsection headings (33); the part title `# Spells` is owned by no unit.
- **Framing** (supporting, not a rule): only "Each spell description has a series of entries…".
- **Excluded headings keep their meaning in read prose** (remediation guard). Two introductions that were framing qualify what follows, so they are now read:
  - *Casting without Slots*: "There are several ways to cast a spell without expending a spell slot:" is its own component, `casting_without_slots`, printed before the four ways (cantrips, rituals, special abilities, magic items);
  - *Range*: "A range usually takes one of the following forms:" is the second passage of the `range` component, keeping "usually".

  The other excluded headings' bodies state their rule without the heading: Preparing Spells, Always-Prepared Spells, Spell Level, Spell Slots, Using a Higher-Level Spell Slot, School of Magic, Class Spell Lists, the three Casting Time headings, and Verbal (V)/Somatic (S)/Material (M), whose abbreviations the Components introduction states.
- **Examples stay inside their clauses**, as in Equipment. Spell names in examples (*Magic Missile*, *Cure Wounds*, …) are not references.
- **See-also sentences** (`_See also_ "Cover."`, `_See also_ "Playing the Game" ("Combat").`) are record-owned supporting spans with a record reference, following the core-play-dependencies convention. They are excluded from the clause text.
- **Latitude:** `gamemaster_latitude` for monster prepared spells and Effects (the GM adjudicates the effect); `contextual_applicability` for awareness of being targeted; `no_identified_structured_use` for the other 52.
- **Glossary inclusion rule:** author only the unauthored entries these rules explicitly point at. See §6.1 for what was excluded.

**References (39).**
- **In batch (25):**
  - Effects → *Targets*, *Saving Throws*, *Attack Rolls* sections;
  - Targets/Areas of Effect → *Area of Effect* and the six shapes; Clear Path "Total Cover" → Cover;
  - Area of Effect's table → the six shapes; its point of origin's "Total Cover" → Cover; its see-also → Cover;
  - each shape's "area of effect" → Area of Effect.
- **Accepted glossary (11, from prose only):** Magic action, Study action, Long Rest, Concentration, Hostile, Incapacitated, attack roll, Reach. "Reach" is cited only in Touch ("within their reach"); "reach into it" is a verb. The Effects "attack rolls" pointer goes to the in-batch section, and the glossary citation of the same words is suppressed.
- **Accepted outside (1):** Cover's see-also "Combat" → `play.combat`.
- **Unresolved, Equipment scope (2):** "Component Pouch" and its "(see "Equipment")" name one item. No accepted record is that item, and the whole Adventuring Gear section does not stand in for it, so both stay unresolved under `srd-5.2.1/equipment`. Accepted Equipment was not expanded. An item record can come with a later coherent group.
- **None** name the *Classes*, individual spells, *Monsters* or *Magic Items*.

## 4. Source coverage and table correctness

- 104 leaves: 78 contiguous leaves of *Spells* from the first leaf after `# Spells` to the last before `## Spell Descriptions`, and 26 glossary leaves. Every word of every spanned leaf is claimed (residue test).
- The Spell Preparation by Class table (9 rows: head + Bard…Wizard, with its "Change When You…" column), the Schools of Magic table (9 rows) and the Area of Effect shapes table (2 rows) are whole release leaves, read after the prose that introduces them.
- A dropped table, a dropped rule, a dropped component, or a table missing a row fails loudly (tested).

## 5. Native simulation and consumer evidence

**Composition** (in memory, `test_composed_every_target_closes_and_104_leaves_gain_coverage`, `test_the_recorded_resolutions_still_apply_composed`):
- The thirteen-batch oracle loads at its pinned SHA: 216 records, 1425 spans, 13 batches, 49 resolutions.
- Composed with this proposal, all 12 accepted out-of-batch targets close. The new non-leaf findings are the 72 `span …: no acceptance record` findings and the two unresolved Equipment citations. Otherwise the retained reference findings are unchanged, including the 26 "Spells" citations.
- Exactly the batch's 104 leaves gain coverage. The 49 recorded resolutions still apply.

**Draft** (1, `resolve-play-d20-tests-attack-ability-modifier-spells-spellcasting-1`):
- It targets the accepted citation `play.d20_tests / attack_ability_modifier / "Spells"` → `spells.attack_rolls`, and names its provenance span exactly.
- Before acceptance, `resolve_references` refuses it ("states no record for").
- After in-memory `accept_proposal` it resolves. The effective authority then leaves the other 25 "Spells"-scope citations unresolved: `play.damage_and_healing / "Spells"` (a whole-part pointer) and 24 individual-spell citations. The oracle files on disk are unchanged.

**Consumer** (`RulesAuthorityService` over a draft persisted into a private copy of the release; only binding resolution is stood in):
- **Consumer fix.** `_base_records` places each component at the printed position of the first passage it owns (its `PRIMARY` prose binding): leaf order, then character offset. That is the same placement the catalogue reading already uses, and it comes from the corpus coordinates, not from UUIDs or names. Context a component also reads does not place it. A component owning no passage reads after the placed ones, by key. Other behaviour:
  - an appended authored component reads after the source's;
  - a replaced component keeps its source position;
  - a component-selector narrowing keeps the record's order;
  - record-selection order is unchanged (key order, ADR-005d Decision 9);
  - catalogue readings are unchanged.
- **Whole-batch GameMaster view:** records in key order, each record's components in `CLAUSES` (printed) order, each component's passages whole and in printed order.
- **`test_a_section_reads_its_rules_as_the_source_prints_them`** (actual service → GameMaster view):
  - `spells.components` reads `components, verbal, somatic, material, component_pouch_and_focus`;
  - `spells.casting_spells` reads `casting_in_armor, spell_level, spell_slots, slot_recovery, casting_without_slots, cantrips, …`;
  - Range, Targets and Area of Effect likewise.
- **`test_narrowing_to_some_rules_keeps_their_printed_order`:** component selectors given as pouch, material, components read as components, material, pouch.
- **`test_an_authored_rule_reads_after_the_source_s`:** an APPEND whose key sorts first (`aaa_house_rule`) reads last, as authored prose.
- A multi-record slice lists its records in key order (Decision 9).
- A DISABLE of `glossary.cone` removes it from the slice and view; a direct request is `invalid_reference`.
- A REPLACE of `spells.components/material` reads the authored prose at material's printed position (index 3). The source clause is not read, and every other component is source prose.

## 6. Codex / Owner questions

Settled in remediation round 1 (no new Owner decision):
- **Glossary scope.** Limiting the batch to direct dependencies is appropriate. There is no recursive or reverse-dependency authoring: Cantrip, Ritual, Spell and Spell Attack are not authored.
- **Table-cited references.** The shape names in the Area of Effect table are valid explicit source citations.
- **Component Pouch.** Explicitly unresolved under Equipment scope (§3).
- **Consumer reading order.** Fixed as settled source fidelity (§5). The descriptive text of ADR-005d Decision 9 now says components read as printed and authored components follow. The record-selection key order it decides is kept.

Still open for Codex's final source review:
1. **Attack-rolls draft.** D20 Tests' "Spells" citation under *Attack Ability Modifier* → `spells.attack_rolls`. That section states the spell attack modifier. The draft bytes are unchanged, and no semantic acceptance is claimed.
2. **Prose-bound lift path.** Everything is prose-bound, with no facts. Structured lifts are out of scope.
3. **Coordinate limitation.** None found for this batch: every source component owns at least one `PRIMARY` passage, so each has an unambiguous printed position. A component with no owned passage (none here) would read after the placed ones by key. That is stated behaviour, not an inference.

## 7. Boundaries and gate status

Remediation round 1 gates ran once, on the settled delta, through `rtk proxy venv\Scripts\python.exe -m pytest … -p no:cacheprovider`.
- **Spellcasting module:** 39 passed.
- **Consumer suite** (`tests/services/rules_authority`, `tests/persistence/test_rules_authority_migration.py`, `tests/pipeline/orchestrator/test_service.py`, `tests/test_quarantine_5c_5d.py`, with `--cov=afterworlds.services.rules_authority`): 792 passed. The exit code is 1 only because this partial run cannot reach the global 80% fail-under (60.10% total).
  - Coverage: `application.py` 89%, `service.py` 92%, `views.py` 84%.
  - The new ordering, append and narrowing lines are not in the missing list.
- **Mechanical consumer-family** (every `test_schema_*`, recurrence persistence, runtime production release, subclass refusal): 1343 passed, 6 skipped.
- **Proposal suites that read through the service:** 322 passed. These are character-creation-foundations, character-origins-feats, checks-actions-rests, core-play-completion, core-play-dependencies, equipment and spellcasting.
- **Accepted-authority consumer test** `test_character_origins_feats_acceptance.py::test_the_accepted_authority_reaches_each_catalogue_in_printed_order`: 3 passed.
- **Also run:** `test_character_creation_foundations_acceptance.py::test_the_committed_authority_reads_in_printed_order`, which calls `_base_records` over every accepted record: passed.
- **Not rerun:** the full accepted-batch acceptance suites. A run of all 47 consumer-importing files projected several hours, and the acceptance files do not read component order apart from the test above. **No full-suite claim is made.**
- **Black / Ruff / mypy strict:** clean on `src/` and `tests/` plus the generator (black 537 files unchanged; ruff all passed; mypy no issues in 235 files).
- **detect-secrets.** The pre-commit hook against a temporary baseline copy (deleted afterwards; `.secrets.baseline` unchanged, SHA above) exits 1 only on public, non-secret hashes:
  - PROPOSAL lines 4659, 4660, 4662, 4664, 4667, 4670 (the release binding, schema and policy hashes);
  - DRAFTS lines 12–15;
  - test lines 128 (`IDENTITY`) and 136 (`ORACLE_SHA256`).

  `application.py`, `service.py`, the ADR, the generator and this packet are clean. This is the Owner terminal hash delta. The baseline was not edited or rescanned.
- **Line endings:** every changed file has zero `\r` bytes.
- **pip-audit:** still deferred and non-green (31 findings in 11 packages), unchanged.
- **Not committed.** Required gates are unresolved: pip-audit, and the detect-secrets delta awaiting Owner terminal handling.
- **Remaining review.** Codex's full official-PDF source verification and final native review, then the Owner's semantic acceptance. The batch stays unaccepted.
