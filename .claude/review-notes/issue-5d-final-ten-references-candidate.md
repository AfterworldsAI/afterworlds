# CRD Issues 5c/5d - final-ten reference candidate (review packet)

Prepared 6-7 October 2026 for Codex review and exact Owner acceptance.
**SIMULATED candidate. Nothing is accepted, recorded, committed or published.**
The simulation's ten approvals are labelled `SIMULATION - not an Owner approval`
(the ten approval lines of `DELTA.txt`; `PROPOSAL.json` carries `simulated_only: true`).
They are not attributed to the Owner.

The live accepted oracle is unchanged throughout:
`src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json`,
SHA-256 `5909e5bdd8c73bf32525b17942924364871146d648b83681518561361a434c0d`,
schema `5d-representation-schema-17`. It still holds 1,476 resolutions and ten
reference findings.

## What is proposed

Ten additive `reference_resolutions` clear the ten held citations: 10 to 0
reference findings, with uncovered leaves staying at 0. There are 201
destinations in total.

There is **no contract, schema, reader or route-model change**. Every
resolution uses the existing native shape:
- a single destination becomes a plain `target_record_key`;
- two or more destinations become all-labelled `destinations` validated by
  `reference_resolution_violations`.

The ten citation identities equal Codex's independent capture in
`.claude/_sp/final-ten/codex-held-citations.json` (`held-citations-match.log`,
exit 0). Each committed citation identity, including its printed scope, is
immutable and unchanged. Record-owned 87/88 keep an empty `from_component_key`
and receive distinct ids.

| Row | Citation (record / component / text / scope) | Shape | Destinations |
|---|---|---|---|
| 34 | `magic_items.magic_item_rarity.magic_item_values_by_rarity` / `magic_item_values_by_rarity` / `a purchase cost in "Equipment"` / equipment | 1 labelled route | 6 records: `equipment.weapons`, `.armor`, `.tools`, `.adventuring_gear`, `.mounts_and_vehicles`, `.food_drink_and_lodging` |
| 36 | `monsters.parts_of_a_stat_block` / `gear` / `Equipment` / equipment | 39 routes `Gear: {Name}` | 40 (Wand adds `equipment.adventuring_gear.arcane_focus`) |
| 39 | `classes.wizard` / `core_traits` / `Spellbook` / equipment | plain target | `classes.wizard.spellcasting` |
| 48 | `classes.warlock.eldritch_invocation_options.pact_of_the_chain` / `pact_of_the_chain` / `Monsters` / monsters | 32 routes | 25 `Normal form: X` + 7 `Special form: X` |
| 54 | `magic_items.magic_items_a_z` / `magic_items_a_z` / `the stat block is in "Monsters."` / monsters | 42 routes `{Item}: {Variant}: {Creature}` | 84: each route reads the creature block, then its item record |
| 57 | `spells.awaken` / `effect` / `Monsters` / monsters | 2 routes | Awakened Shrub, Awakened Tree (`GM's choice, SRD example: ...`) |
| 60 | `spells.find_familiar` / `effect` / `Monsters` / monsters | 25 routes | the 25 SRD CR 0 Beasts |
| 76 | `play.d20_tests` / `add_modifiers` / `Rules Glossary` / rules-glossary | 3 routes | 9 glossary records |
| 87 | `glossary.cantrip` / (empty) / `Spells` / spells | plain target | `spells.casting_spells` (id `cited-87-glossary.cantrip-`) |
| 88 | `glossary.ritual` / (empty) / `Spells` / spells | plain target | `spells.casting_spells` (id `cited-88-glossary.ritual-`) |

The exact JSON is in `.claude/_sp/final-ten/candidate/issue-5d-final-ten-references-PROPOSAL.json`.
The full-text delta is in `issue-5d-final-ten-references-DELTA.txt`.

### Per-row source basis and boundaries

- **34.**
  - *Condition and basis.* magic-items.md:181 adds the cost of an incorporated
    item "that has a purchase cost in Equipment", and only when one exists. The
    route covers every Equipment section pricing incorporable objects, in
    printed order.
  - *Food, Drink, and Lodging (Codex correction).* This section prices goods
    alongside its services: Ale 4 CP, Bread 2 CP, Cheese 1 SP, and Common and
    Fine Wine. Its table is routed whole, keeping the Inn Stay and Meal service
    sections and its lifestyle prose. The label names only its *priced goods*,
    so no lodging or meal price is presented as an object's purchase cost.
  - *Excluded sections.* Coins, Lifestyle Expenses, Hirelings and Spellcasting
    are services or upkeep. Magic Items, Crafting, Brewing and Scribing are
    procedures. Scribing remains the Spell Scroll adjustment's own accepted
    pointer.
  - *Unchanged.* The consumable and Spell Scroll adjustments, the 5,500 GP
    (+1 Plate Armor) and 4,020 GP (Glaive of Wounding) examples, and Instant
    Fortress's Rare guidance with no invented base cost are untouched.
    Glaive's 20 GP is only the Weapons table's row, because no glaive record
    exists.
  - *No new machinery.* There is no price calculator, availability guarantee or
    hypothetical item.
- **36.** The 45 explicit `**Gear**` entries normalize to 39 names, each routed
  to its ordinary Equipment item. Wand's price row lives in its own record, and
  its route adds the Arcane Focus record for the focus rules. The outside-Gear
  default and the GM's latitude stay in the citing prose. Nothing is marked
  unretrievable.
- **39.** The target is Wizard-owned spellbook rules. There is no Equipment
  Spellbook, Book substitute, price or resale prohibition.
- **48/60.** The 25 SRD CR 0 Beasts are 24 Animals plus the local Giant Fly,
  which is read from its Magic Items block and labelled
  `Giant Fly (Magic Items stat block)`. The Pact route also keeps its seven
  named special forms. The Pact does not recurse through Find Familiar, and no
  non-SRD block is invented.
- **54.** Only actual creature stat-block references are routed: the PDF bold
  cues, giving 18 items and 42 (item, creature) pairs. These equal the accepted
  per-item creature citations.
  - *Bestiary by default.* Each route reads the base block first, then the item
    record, which preserves local modifying prose. For example, the Onyx Dog's
    Mastiff has "an Intelligence of 8 and can speak Common".
  - *Local blocks.* The Ebony Fly's Giant Fly and the Mysterious Deck Skull's
    Avatar of Death are read locally.
  - *Exclusions.* Bag of Tricks, Deck of Illusions, Elemental Gem and Manual of
    Golems print their creatures unbolded. Each already has its own accepted
    Monsters route, so they are excluded.
  - *Static review.* Codex's static review (`codex-static-review.md`) found no
    material omission. The route was not broadened to optional reviewer
    candidates.
- **57.** The Awakened Shrub and Awakened Tree are offered as SRD examples of
  the GM's choice. The citation route does not enumerate eligibility
  exhaustively. The Owner's Awakened Plant is not an SRD destination (see the
  house-rule section below).
- **76.** The three routes keep three things distinct:
  - *Which ability:* D20 Test, Ability Check, Saving Throw and Attack Roll.
  - *Applying the modifier:* Ability Score and Modifier.
  - *Examples:* specific rules naming their own ability (Hide, Search, Study,
    Unarmed Strike).

  Proficiency is excluded because it is the component's separate accepted
  `play.proficiency` pointer. There is no universal ability selector, new
  skill or improvised-action taxonomy, and no recursive See Also.
- **87/88.** These use the general Cantrips and Rituals rules in
  `spells.casting_spells` (PDF p.104), not the spell-description catalogue.

### Scope reconciliation (explicit)

The scope of each committed citation is historical identity and stays
immutable. Targets keep their existing ownership; nothing is moved, duplicated
or re-scoped. Native validation does not enforce a destination namespace from the citation
scope, so `CANDIDATE.py` asserts
that every out-of-scope destination is exactly a declared exception and that
every exception is used:

- **#39:** `classes.wizard.spellcasting`. Spellbook rules are Wizard-owned
  (Owner Decision 2026-10-06, wizard-spellbook-reference).
- **#48 and #60:** `magic_items.figurine_of_wondrous_power.giant_fly`. Giant
  Fly's only SRD block is local to the Figurine (Owner Decision 2026-10-06,
  srd-familiar-reference-scope).
- **#54:** the 18 item records plus the two local blocks (20 keys). The items
  carry the modifying prose and the local blocks are the supplied statistics
  (reference-54 clarification).

All other destinations lie within their printed scope (`monsters.`/`animals.`
for Monsters).

## Awakened Plant house rule (row 57) - exact integration status

Only a **draft presentation, tested in isolation**, exists. It has not been
installed, persisted as an override, activated or published.
`test_the_awakened_plant_house_rule_appends_in_isolation` applies the supplied
`docs/house-rules/awakened-plant.md` content as one in-memory
`HOUSE_RULE`/`PROSE`/`APPEND` override (`append_prose`) on `spells.awaken`
`effect`. The content runs from the title through the full stat block, stopping
before the authoring notes, and includes HP **3 (1d6)**, False Appearance and
"None. Non-combatant.".

The production GameMaster view then shows:
- Awaken's SRD `SourceProse` entries, unchanged and identical to the
  un-overridden read;
- followed by one `AuthoredProse` with the exact text,
  `supplied_by_override_id` and `supplied_by_origin = HOUSE_RULE`;
- `applied_overrides` naming that override alone.

Reference 57 still resolves to the same two SRD routes and records with the
override present. No SRD creature record, citation destination or oracle
content is added.

A standalone, queryable Awakened Plant creature would need a
supplemental-content path. The current override families cannot add records,
so that remains out of scope.

## Evidence

All logs are under `.claude/_sp/final-ten/candidate/` and record raw commands
and exits. Every run used `RTK_DISABLED=1 PYTHONUTF8=1` and the repository venv.

| Check | Log | Result |
|---|---|---|
| Native simulation, write | `candidate-write.log` | exit 0 |
| Native simulation, check (earlier, unhashed header) | `candidate-check.log` | exit 0 |
| Held-citation identity vs Codex capture | `held-citations-match.log` | exit 0, identical |
| Black / Ruff / mypy --strict (earlier, unhashed header) | `static-gates.log` | all exit 0 |
| **Hash-bound rerun:** Black, Ruff, mypy --strict and native check on `2f84d877...` / `fec853b8...` | `bound-gates.log` (`f587a8fb...`) | all exit 0 |
| Focused reader diagnostics (`scripts/run_focused_tests.py`) | `reader-focused.log` | see below |
| detect-secrets scope scan and final hooks | `bl/`, `final-hook.log` | see below |

**Native simulation** (`CANDIDATE.py`) loads the accepted oracle, drafts the
ten resolutions and resolves them through `resolve_references`. It then checks
the following:
- 10 to 0 findings, with no new findings;
- every source pin (line-pinned markdown, the 45 to 39 Gear normalization, the
  familiar inventory hash and the CR 0 scan, and the row-54 pairs equal to the
  accepted per-item citations);
- the scope exceptions;
- deterministic reload to identical bytes;
- whole-payload preservation: all 24 batches, 1,835 records, 10,493 spans,
  1,476 resolutions and 1,476 approvals verbatim, with only the ten additions
  and ten SIMULATION approvals;
- an isolated persistence round trip;
- the live oracle hash unchanged.

**Effective reader** (`tests/ingestion/mechanical/test_final_ten_references_candidate.py`)
persists the simulated candidate, and the accepted oracle as a control, into
private copies of the session's isolated 5c source release. It reads both
through `RulesAuthorityService.citation_view` and `gamemaster_view`. Each
citation's unfiltered candidate read is taken once and shared. Changed
selections, overrides and controls are fresh native reads. Coverage:

- **Fail-closed controls.** The control refuses all ten citations
  (INVALID_REFERENCE). A disabled `spells.casting_spells` refuses #87. An
  unrelated disable keeps #39.
- **Routes.** Every route matches its drafted label, order and destinations.
  One representative class selection (#54, Wizard 5) changes nothing.
- **Content per row:**
  - *#34:* Glaive and 20 GP in the Weapons table, Plate Armor and 1,500 GP,
    Food and Drink rows (Ale, Bread, Cheese, Wine) with their service sections
    intact, and Lifestyle Expenses excluded.
  - *#36:* the Wand 10 GP row plus the Arcane Focus rule.
  - *#39:* the spellbook text and the spellbook as Spellcasting Focus.
  - *#48 and #60:* 25 normal forms (plus 7 special for #48), the local Giant
    Fly block, and no Find Familiar recursion.
  - *#54:* the Mastiff block plus "Intelligence of 8", the local Giant Fly and
    Avatar of Death.
  - *#57:* the SRD examples only.
  - *#76:* the three labels, with no Proficiency.
  - *#87 and #88:* the Cantrips and Rituals casting rules.
- **House rule:** the isolated Awakened Plant prose addition described above.

**Result:** `reader-focused.log` (SHA-256
`ebdbdc41ba01dcac848a8d4a70974e55fbeb1627f41416f5a45c375b2999e51c`).

- *Command:* `RTK_DISABLED=1 PYTHONUTF8=1 venv/Scripts/python.exe
  scripts/run_focused_tests.py --check .claude/_sp/final-ten/candidate/CANDIDATE.py
  --check tests/ingestion/mechanical/test_final_ten_references_candidate.py
  tests/ingestion/mechanical/test_final_ten_references_candidate.py`. The log
  header records both input hashes, `2f84d877...` and `fec853b8...`.
- *Outcome:* the Black check is clean, and **33 passed in 512.69 s**. The
  pytest exit is recorded directly with no pipe: `exit=0`. The run went from
  00:51:30Z to 01:00:05Z on 7 October.
- *Status:* this is FOCUSED DIAGNOSTICS ONLY, not full-gate or acceptance
  evidence.

**Secrets scan.** The committable files are the test, this report and the
restart doc. A scoped detect-secrets scan under the baseline's own plugins
flags nothing in any of them (`bl/`). The private `CANDIDATE.py` has two
findings, `ACCEPTED_SHA256` and `FAMILIAR_INVENTORY_SHA256`. Both are public
file hashes, and the file stays under `.claude/_sp` and is never committed, so
**no baseline change is made**. In `final-hook.log` the real hook exits 1
because `.secrets.baseline` is unstaged, while the private-copy content-only
hook exits 0. The baseline is unchanged at `ae2268b6...`.

**Preservation** (`preservation.log`). The index, `.secrets.baseline`, the live
oracle and all 4 stashes are unchanged. `git diff HEAD` equals the pre-edit
capture except for the restart doc's opening line 8.

### Evidence reused, invalidated and not run

- **Reused unchanged.** The thirteen-reference recording evidence
  (`issue-5d-equipment-spell-references-owner-acceptance.md`,
  `-recorded-followup.md`, `-recording-codex-review.md`,
  `.claude/_sp/esr/recording/`) still applies. The live oracle and every prior
  resolution, approval and payload are byte-for-byte preserved, so none of it
  is invalidated. No old recording script was rerun.
- **Invalidated by the reference-34 correction (Food, Drink, and Lodging, +1
  destination):**
  - the earlier draft's PROPOSAL `1951357e...` (200 destinations);
  - Codex's `codex-simulation.log` and `codex-payload-verification.json` pins.

  Codex's final whole-payload comparison is refreshed against the hashes below
  in `codex-payload-verification.json`; the earlier simulation log is retained
  as historical evidence. See the [final Codex review](issue-5d-final-ten-references-codex-review.md).
  `codex-static-review.md` reviewed `CANDIDATE.py` `c50e240b...`. Its rows 54
  and 76 are unchanged in content, but the script hash has moved.
- **Not green.** The interrupted Codex reader attempt
  (`codex-interrupted-reader.log`) never completed. My first focused attempt
  (`reader-focused-attempt1-failed.log`, exit 1) had 5 test-side failures,
  which were corrected:
  - *Rows 39, 87 and 88:* single destinations read with an empty label.
  - *Wand:* the price row is the Wand record's.
  - *Row 54:* the labels carry the item prefix.

  Neither run is claimed as evidence.
- **Not run (deferred under the restart limits).** The broad suite, coverage,
  expanded mypy and pip-audit. No shared store or database was written.

## Pins

| Artifact | SHA-256 |
|---|---|
| `.claude/_sp/final-ten/candidate/CANDIDATE.py` | `2f84d877037b865121bd502a9c92ae365f44cf82dc6d312d814759200433fd57` |
| `issue-5d-final-ten-references-PROPOSAL.json` (1,799 lines) | `46808846b0ad6712393b0f058a71e03d6e664a2ffdf8734de7d046bf4b4d68e3` |
| `issue-5d-final-ten-references-DELTA.txt` (247 lines) | `465a17f7d749c512aed45848874576a6c2a839e1eaf0ea595da6a6c11c827851` |
| Simulated candidate oracle (in memory, deterministic) | `6302adbe7b09fab0a26d60e5526d72fa5269214e3911b0362486ad9e705d85ff` |
| `tests/ingestion/mechanical/test_final_ten_references_candidate.py` | `fec853b8ed1d84146248aa19d5f92b1c60b14aea226cf281a31dba6a07ba3dbe` |
| Live accepted oracle (unchanged) | `5909e5bdd8c73bf32525b17942924364871146d648b83681518561361a434c0d` |
| FRR loader `issue-5d-finite-reference-routes-REPLACEMENT.py` | `afb1cf886296c59693aebd07fa97fb29a3bab85621e3d94fa57622b83e9fe3ec` |
| Reader `services/rules_authority/service.py` (pre-existing working tree) | `4a33bf3c5f07120623c943b06f22e327f53d47dafba820677d5780b008877e2d` |
| Reader `services/rules_authority/views.py` | `47b6bc6ade0f07d7592f077ed72ca5081382cb3ce395525fccd010fcd587f6ee` |
| Reader `services/rules_authority/application.py` | `f52ac7bb7ad649953c331448f0d6d676e5f7c2d9174c8d21e2be1150a7798cc3` |
| `ingestion/mechanical/acceptance.py` | `3f2b08b1603b3c02f2e5958fb115012bb9a6d0880cfe0ebe31d1667c05cb292d` |
| FRR reader test helpers `test_finite_reference_routes_candidate.py` | `6296ce849dc621f2274b03653859a7617e48bb20c87dfd93f7bff7358edb57a6` |
| Official PDF | `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87` |
| `source_pin.json` | `2a68c67af6fbed0bdadb88df990ae56e08fd98ab64b7a565295736e0545dde89` |
| Familiar CR 0 inventory JSON | `2b7c3e4ec210a6ff30618dfbbda891191f3bf0d52ca46a9779aa6d0e256d14b0` |
| `docs/house-rules/awakened-plant.md` | `72096d8e54a1b18392788ab696ff24a758c2379f01a6a60ec1b220bb55dcdc89` |
| Git index (unchanged) | `40473ee3d69a67442602f4b0d83ec4b3cefce7ad7c3011489ff8970289661c6c` |

## Architecture Notes

There is no drift from design principles and no reader or contract change.
- *Separation of canon.* Rules Package mechanical canon and Story Bible
  narrative canon stay separate.
- *Ownership.* Targets keep their existing ownership.
- *Scope exceptions.* These are explicit and asserted, not silent.
- *House rule.* The house-rule supplement uses the existing house-rule prose
  path in isolation, with Afterworlds provenance, outside the SRD oracle.
- *No new authority.* No new aggregates, routes, targets or approvals were
  invented to pass validation.
- *Deferred residue.* Pre-existing out-of-scope reader-retention residue
  remains deferred.

## Remaining limits and stop point

- [Codex review](issue-5d-final-ten-references-codex-review.md) is complete,
  with no blocking candidate finding. Exact Owner acceptance of this pinned
  candidate is required before recording. Recording must reproduce PROPOSAL
  `46808846...` with real approval metadata; simulation approvals are not
  authorization. The final independent payload proof is refreshed.
- The publication block, release-order bounded Owner pass, broad gates
  (broad suite, coverage, expanded mypy, pip-audit) and dependency repairs
  remain outstanding or deferred.
- The reader test loads `CANDIDATE.py` from the never-committed `.claude/_sp`
  path. Recording or delivery must re-home the script or rewrite the test
  against the recorded oracle before the test is committed.
- A runtime installation of the Awakened Plant house rule, or a standalone
  supplemental creature, is not implemented.
- No commit, stage, push, merge, publication, activation, recording or
  shared-database write was performed.
