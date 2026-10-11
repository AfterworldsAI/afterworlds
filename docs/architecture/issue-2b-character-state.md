# CRD Issue 2b — character and continuing-creature state: traceability

Approved scope: the concise CRD Issue 2b issue, plus the Owner directions on:

- explicit adoption;
- holding shared changes;
- independent creatures;
- a clean baseline.

The Owner accepted the G1 semantics on 11 October 2026 (proposal `8a8a737b…`). The recording record is in `.claude/review-notes/issue-2b-g1-recording/`.

## What it is

| Concern | Where |
| --- | --- |
| Typed state. One schema-versioned document per character or creature. Every family is optional; `None` means not recorded. | `src/afterworlds/models/dnd5e_state.py` |
| Source-backed vocabularies the accepted schema lacks: language, alignment, creature type, armor category, and five origin-choice sets (draconic ancestor, elven lineage, gnomish lineage, giant ancestry, fiendish legacy). | `src/afterworlds/models/dnd5e_vocabulary.py` |
| Persistence. The tables are: state rows carrying the exact four-part binding and an integer `revision`; parties, each recording the Rules Package that governs its items; creature associations; item instances (a CHECK enforces exactly one holder; each can record an applied poison); binding history; adoption requests; owner-recorded turn leases; and held shared changes. | `src/afterworlds/persistence/orm/dnd5e_state.py`, `SharedRuleChangeORM` in `persistence/orm/rules_authority.py`, migration `0038` |
| Exact binding, the current-binding check and the historical authority index | `services/dnd5e_state/authority.py` |
| Validation of identities, kinds, typed selections, choice schemas, hazards and structured bounds. Readiness reports missing applicable state. | `services/dnd5e_state/validation.py` |
| Production entry points (create, update, readiness), story-scoped reference checks and recorded-binding maintenance reads | `services/dnd5e_state/service.py`, `store.py` |
| Shared rule changes held until affected events resolve | `services/dnd5e_state/shared_changes.py`, `leases.py`, `turn.py` |
| Deliberate per-subject adoption, including held items | `services/dnd5e_state/adoption.py` |
| Creatures, parties and items, all under the holder's own authority | `services/dnd5e_state/holdings.py` |
| Turn integration: the lease, the readiness gate, the commit recheck, compare-and-swap effects, binding-enforced display, and refusal of proficiency-aware checks | `pipeline/orchestrator/service.py`, `pipeline/rpg/adapter.py`, `pipeline/rpg/service.py`, `pipeline/rpg/visible_state.py`, `api/visible_state.py`, `api/pipeline_wiring.py` |

## Inventory families → state → tests

Families follow the supporting source inventory's coverage routes F1–F20. Route X, transient state, is out of scope. Tests are in `tests/services/dnd5e_state/` unless noted.

| Family | State | Tests |
| --- | --- | --- |
| F1 alignment | `alignment` (`Alignment`) | `test_state_validation`, `tests/models/test_dnd5e_vocabulary` |
| F2 species, background | `species`, `background` (`OriginSelection`) | `test_invalid_identities_and_wrong_kinds_are_typed` |
| F3 classes, subclass, levels, XP | `classes` (`ClassLevel`), `level_history`, `experience_points` | All twelve classes at four tiers; multiclass; the subclass catalogue; `test_structural_integrity_rules` |
| F4 abilities and sourced adjustments | `ability_scores` (base only), `ability_adjustments` | The adapter refuses adjusted totals (`tests/pipeline/rpg/test_adapter`) |
| F5 proficiencies, expertise, training, languages | Skill, save, weapon, armor and tool grants; `languages`. A weapon grant names a weapon (an accepted record with a weapon category) or a category; a tool grant names a member of the Tools catalogue. | `test_identity_domains` (armor as a weapon, a weapon as a tool, a rule as a sense: refused by validation, the service and adoption; all 38 SRD weapons, categories, tools and senses stay valid); vocabulary tests |
| F6 feats | `feats` (`FeatSelection`) | Round trip; validation |
| F7 feature choices | `choices` (`ChoiceRecord` with source `schema_id` and typed `selected`). A selection is a record, a component option or a closed-vocabulary member. | `test_selections_and_parameters` (invalid record, invalid option, misplaced or unknown vocabulary, untyped value, schema drift, Metamagic, Fighting Style, Skilled, Magic Initiate); origin vocabularies against the source (`tests/models/test_dnd5e_vocabulary`) |
| F8 traits | `size`, `creature_type`, `speeds` (`hover` on fly only), `senses` (telepathy is a sense grant), `damage_responses`, `condition_immunities`, `base_armor_class` | Round trip; `test_telepathy_is_a_sense_grant…`; `test_parameter_structure_is_enforced`; `test_a_selected_base_armor_class_source_is_validated` |
| F9 HP | `hit_points`: the stored maximum; no current floor; a `maximum_reduction` kept apart from the maximum; `temporary_source` | `test_current_hit_points_have_no_floor…`; `tests/pipeline/rpg/test_sheet_effects` (effects keep reduction and provenance); `test_recorded_parameters_round_trip…` |
| F10 Hit Point Dice | `hit_point_dice` | Round trip |
| F11 death | `death_state` | Round trip |
| F12 heroic inspiration | `heroic_inspiration` | Missing differs from `False` |
| F13 conditions | `conditions`: distinct instances with Exhaustion level, source, visibility, referent (grappler, charmer, source of fear), Grappled's escape DC, Hide's recorded check total, item instance and duration | `test_selections_and_parameters` (DB round trip; out-of-story references refused); visible state |
| F13 hazards | `hazards`: burning; dehydration (day, gallons drunk); malnutrition (day, pounds eaten, days without food); suffocation (breath remaining, suffocating); magical contagion (infection, onset, saves, suppression, cure anchors). Exhaustion a hazard caused is a condition whose `source` names the hazard. | `test_hazards_and_familiars` (DB round trip and update; readiness; wrong or unknown record; structure) |
| F14 active effects | `active_effects`: distinct concurrent instances with cast level, form, caster, targets, typed selections (Hex's ability), item instance, curse link and duration | `test_concurrent_effects_are_separate_instances`, `test_selections_and_parameters` |
| F15 usage counters | `usage_counters`: structured maximum from `progression_entry`; optionally per item instance | Maximum and missing-counter tests; per-item counter round trip |
| F16 spell slots | `spell_slot_pools`: distinct pools with stored totals | Slot table; Pact Magic; multiclass |
| F17 spell access | `spell_access`, per pool and mode | Multiclass distinct pools |
| F18 items, currency, attunement | `dnd5e_item_instances` (equipment, magic items, accepted Poison catalogue members with doses as quantity, applied poison); `currency` | `test_holdings` (one holder, transfer, attunement, the G1 twelve, poisons, the holder's binding, the destination package, stale holders, adoption of held items); `tests/ingestion/mechanical/test_srd_state_on_published_release` |
| F19 creatures | `dnd5e_creatures`, associations, `summon`, `creature_type`, `speeds`, `presence` | `test_holdings`, adoption; `test_hazards_and_familiars` (familiar readiness); `test_a_familiar_records…` |
| F20 rest anchors | `rest_anchors` | Round trip |

## Acceptance criteria → evidence

| Criterion | Evidence |
| --- | --- |
| Families round-trip on a real database: all twelve classes, multiclass, pools, choices, concurrent effects | `test_round_trip_and_readiness`, `test_state_validation`, `test_selections_and_parameters`, `test_hazards_and_familiars`, `tests/ingestion/mechanical/test_srd_state_on_published_release` |
| G1 identities and facts are source-derived; the prior bytes are intact | `tests/ingestion/mechanical/test_srd_equipment_catalogue`, `test_oracle_succession`, `test_holdings::test_all_twelve_g1_items…`, the published-release test, the recording follow-up |
| Typed failures; explicit empty is valid; changed schemas are refused; readiness is not legality | `test_state_validation`, `test_selections_and_parameters`, `test_readiness_never_certifies_legality`, the familiar and hazard readiness tests |
| Bindings are enforced; stale, unpublished or invalid authority is refused; unsupported proficiency-aware checks are refused; historical replay works | `test_store_and_binding`, `test_display`, `tests/pipeline/orchestrator/test_service::…refused_character_binding…`, `tests/pipeline/rpg/test_adapter` (mixed kinds, tags and labels on every entry path), `tests/pipeline/rpg/test_adjudication_service` (every proposal is checked before any dice), `tests/pipeline/orchestrator/test_rpg_turn_hold` (the readiness gate) |
| Explicit adoption preserves state; refusals change nothing | `test_hold_and_adoption`; `test_holdings::test_adoption_refuses_a_target_that_removed_a_held_item` |
| Shared changes wait for affected events across stories, creatures, parties and packages; there is no race; held adoption works; rejection and withdrawal are visible | `test_hold_and_adoption` (party context, the write lock taken first, the trial applying the effective set), `test_lease_recovery`, `tests/pipeline/orchestrator/test_rpg_turn_hold` |
| Concurrency, rollback, crash and retry; stale work cannot commit | `test_store_and_binding` (two connections); crash/retry and conflicting-write tests; `test_lease_recovery` (real processes: live, crashed, starting during recovery, concurrent recoverers, proof kept for a starting owner); `test_rpg_turn_hold` |
| Creatures stay independent through save/load, absence, sharing, transfer and ended associations | `test_holdings`, `test_a_creature_adopts_on_its_own…` |
| Display and turn paths work; obsolete paths are unreachable; empty-store migration works both ways | `tests/pipeline/rpg/*`, `test_display`, `tests/api/test_visible_state`, `tests/persistence/test_migration_0038_dnd5e_state` |

## Architecture Notes

Drift and boundaries are stated explicitly below.

### Authority and bindings

- **Same-release oracle succession.**
  - The resolver previously admitted one committed file per release. G1 needed a successor for the *same* release while preserving the prior file byte-for-byte.
  - `SUPERSEDED_ORACLE_SHA256` skips a predecessor by its exact digest.
  - This is a bounded extension of ADR-005d's committed-authority selection. It is recorded in the oracles README and in the ADR-005d schema-18 amendment.
- **No production writer of override rows existed.** The shared-change service is now the only one.
  - A held change never touches `rp_mech_overrides`.
  - At request time, a trial inside a savepoint resolves the change and applies the whole effective authority. An override that cannot take effect is refused then, not after activation.
  - Activation inserts the rows in one transaction that takes the write lock first. It does so only when no affected pending roll or turn lease exists, and only if the result is the exact override-set identity fixed at request time. Otherwise the change is rejected, never retargeted.
- **Party authority.**
  - A party records the Rules Package that governs its items. A party has no binding of its own and no adoption; membership and governance are not modelled.
  - Party-held items are validated under that package's current exact binding at every item operation.
  - A story with such a party is affected by that package's changes. The party counts for every release of its package, which errs toward holding.
- **Item authority is the holder's.**
  - Creating, using and transferring items validates against the holder's own exact current binding. A transfer validates against the destination. A caller-supplied index is checked, never trusted.
  - Adoption also validates the identities, components and applied poisons of the items the subject holds.
- **Live display reads through the binding.** The RPG visible-state snapshot is unavailable (`None`) when the character's binding is refused. The OOC path uses the binding-enforcing resolver. Historical replay and recorded-binding maintenance stay explicit service paths.

### Holds and turn leases

- **In-progress adjudication was not durable.** `rpg_turn_leases` makes it durable: the lease commits before any binding read and is released after the turn's transaction ends. Releasing late can only delay activation.
- **Lease recovery requires proof of ownership.**
  - This was the defect family *ownership proof separated from the lease-deletion transaction*. It is classified, and the boundary is closed.
  - Every lease records its owner. Each process holds an exclusive OS lock on its own owner file for life.
  - At app start, recovery deletes a foreign owner's leases only when it can take that owner's lock, and it holds the lock until the deletion commits.
  - Live leases, this process's own leases, and leases whose owner file is missing are kept. So are leases on a database that is not a file.
  - An owner that is still starting and meets a held proof refuses before writing its first lease.
  - Recovery removes only the files of owners whose leases it deleted. A file whose owner had no lease is kept, because that owner may be starting and lease later; on POSIX, removing it would lose the proof after a crash.
  - None of this depends on a single worker.
  - Pending rolls are never cancelled or expired.
- **The commit recheck runs through the hold.** It runs when the turn hold is wired, and production wires it. Unit tests that use fabricated characters without a database row leave it unwired.

### Turns and adjudication

- **Readiness gates in-play turns.** An in-play character whose recorded state is not ready fails the turn with a typed error that names the missing state. Mechanics are never silently skipped. Readiness never certifies legality.
- **The supported check shape is closed.** The adapter assembles only one shape: kind `ability_check` (optionally `advantage`/`disadvantage`), one ability label, and a check label naming that same ability on an unadjusted base score.
  - Any other kind, label or combination is refused with `UnsupportedCheckError`, surfaced as `AdjudicationPassError`. That includes skill, save, attack, tool and initiative checks, and any mixed or unknown label.
  - Every proposal of a turn is checked before any dice, pending roll or record.
  - The prompt contract (`docs/prompts/rpg_adjudication.md`) does not mention `ability_check`; it is unchanged here. Production does not yet wire an adjudication service. Both are CRD Issue 15c's.
- **No current-HP floor at any write.** Turn effects change only their target field; ADR-0003's `current ≤ maximum` remains. A recorded maximum reduction is not applied here: that is 15c.

### What state records

- **Selections and parameters are typed and story-scoped.**
  - A choice's selected identities and an effect's chosen parameters are records, component options or source-backed vocabulary members. Nothing is free text.
  - Validation checks only that each identity exists. Origin-choice vocabularies are valid only under the component that offers them.
  - References to characters, creatures, Story Bible cast entries and items are checked against the subject's story on every production write, including turn writes. Cast entries are read-only references and write no canon.
- **Identity domains are narrower than record kinds.**
  - Defect family: a broad accepted record kind mistaken for a field's narrower structural identity domain.
  - A weapon proficiency names a record the accepted authority gives a weapon category (the G1 schema-18 facts).
  - A tool proficiency names a member of the accepted Tools catalogue.
  - A sense grant names a special sense the source lists (`playing-the-game.md`:756), or Telepathy.
  - Other identity fields were sampled and were already safe. They are closed vocabularies, exact record kinds, the subclass catalogue, or the Poison and Contagion catalogues.
  - A record selected in a choice is checked for identity only. Deciding which records a choice admits is selector work, which belongs to CRD Issue 15c.
- **Hazards are recorded inputs.**
  - Exhaustion and damage are not derived.
  - The requirements by size, the breath a Constitution modifier allows, and contagion saves are not executed.

### Retired and unchanged

- **Retired.**
  - The free-text `rules_package_id`.
  - `Dnd5eCharacterSheet`, with its stored skill totals and free-text class, background and equipment.
  - `Dnd5eActiveCondition`.
  - The free-text-reference resolver in the orchestrator.
  - The `dnd5e_character_sheets` and `dnd5e_active_conditions` tables, removed by an empty-store-only migration.
- **Not changed.** `CharacterState` (`character_states`) is story-world state used by the Extractor. It is not the mechanical sheet and is outside this scope.

### Gaps and test boundaries

- **Item identities beyond G1.**
  - Every table row that can be held as an item has an accepted record or component, except focus forms (Crystal, Orb, …), saddles, drawn vehicles, large vehicles, feed and stabling.
  - These are refused with `UnsupportedIdentityError` rather than authored.
  - Mounts are creature instances of the accepted Animals templates.
  - Poisons are the members of the accepted Poison catalogue. No other gameplay tool is an item.
- **No production creation or request route.** The typed services are the only entry points for creating characters and creatures, requesting shared changes and adoption. There is no HTTP route or UI for any of them, which is out of scope.
  - `request_change` only holds a change. It activates when a caller invokes `activate`, or during a later turn's post-event processing in an affected story.
- **Test seam.** The 2b service suite runs on a bounded published projection that has no item records.
  - Tests that need SRD items seed the binding-keyed authority cache with the committed SRD's records. Production code still resolves, requires and looks up the exact binding.
  - The same paths are proven against the genuinely published SRD in `tests/ingestion/mechanical/test_srd_state_on_published_release.py`.

No other drift from the design principles.
