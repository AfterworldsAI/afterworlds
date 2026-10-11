# CRD Issue 2b — character and continuing-creature state: traceability

Approved scope: the concise CRD Issue 2b issue, together with the Owner
directions on explicit adoption, holding shared changes, independent creatures
and a clean baseline. G1 semantics were accepted by the Owner on 11 October
2026 (proposal `8a8a737b…`); the recording record is in
`.claude/review-notes/issue-2b-g1-recording/`.

## What it is

| Concern | Where |
| --- | --- |
| Typed state: one document per character or creature, schema-versioned, every family optional (`None` = not recorded) | `src/afterworlds/models/dnd5e_state.py` |
| Source-backed vocabularies the accepted schema lacks: language, alignment, creature type, armor category | `src/afterworlds/models/dnd5e_vocabulary.py` |
| Persistence: state rows carrying the exact four-part binding and an integer `revision`; parties; creature associations; item instances (CHECK: exactly one holder); binding history; adoption requests; turn leases; held shared changes | `src/afterworlds/persistence/orm/dnd5e_state.py`, `SharedRuleChangeORM` in `persistence/orm/rules_authority.py`, migration `0038` |
| Exact binding, current-binding check, historical authority index | `services/dnd5e_state/authority.py` |
| Validation of identities, kinds, choice schemas and structured bounds; readiness (missing applicable state) | `services/dnd5e_state/validation.py` |
| Production entry points (create, update, readiness) and recorded-binding maintenance reads | `services/dnd5e_state/service.py`, `store.py` |
| Shared rule changes held until affected events resolve | `services/dnd5e_state/shared_changes.py`, `leases.py`, `turn.py` |
| Deliberate per-subject adoption | `services/dnd5e_state/adoption.py` |
| Creatures, party, items | `services/dnd5e_state/holdings.py` |
| Turn integration: lease, commit recheck, compare-and-swap effects, visible state, refusing proficiency-aware checks | `pipeline/orchestrator/service.py`, `pipeline/rpg/adapter.py`, `pipeline/rpg/visible_state.py`, `api/pipeline_wiring.py` |

## Inventory families → state → tests

Families are those of the supporting source inventory (coverage routes F1–F20,
plus X for transient state, which is out of scope).

| Family | State | Tests (`tests/services/dnd5e_state/` unless noted) |
| --- | --- | --- |
| F1 alignment | `alignment` (`Alignment`) | `test_state_validation`, `tests/models/test_dnd5e_vocabulary` |
| F2 species, background | `species`, `background` (`OriginSelection`) | `test_invalid_identities_and_wrong_kinds_are_typed` |
| F3 classes, subclass, levels, XP | `classes` (`ClassLevel`), `level_history`, `experience_points` | twelve classes × 4 tiers; multiclass; subclass catalogue; `test_structural_integrity_rules` |
| F4 abilities and sourced adjustments | `ability_scores` (base only), `ability_adjustments` | adapter refuses adjusted totals (`tests/pipeline/rpg/test_adapter`) |
| F5 proficiencies, expertise, training, languages | skill/save/weapon/armor/tool grants, `languages` | G1 weapon identities; vocabulary tests |
| F6 feats | `feats` (`FeatSelection`) | round trip; validation |
| F7 feature choices | `choices` (`ChoiceRecord` + source `schema_id`) | `test_a_choice_made_under_a_changed_source_schema_is_refused` |
| F8 traits | `size`, `creature_type`, `speeds`, `senses`, `damage_responses`, `condition_immunities` | round trip; sense identities |
| F9 HP | `hit_points` (maximum stored; no current floor) | `test_current_hit_points_have_no_floor…`; `tests/pipeline/rpg/test_sheet_effects` |
| F10 Hit Point Dice | `hit_point_dice` | round trip |
| F11 death | `death_state` | round trip |
| F12 heroic inspiration | `heroic_inspiration` | missing vs `False` test |
| F13 conditions, hazards | `conditions` (distinct instances, Exhaustion level, hazard source, visibility) | integrity; visible state |
| F14 active effects | `active_effects` (distinct concurrent instances, cast level, form) | `test_concurrent_effects_are_separate_instances` |
| F15 usage counters | `usage_counters` (structured maximum from `progression_entry`) | maximum and missing-counter tests |
| F16 spell slots | `spell_slot_pools` (distinct pools, stored totals) | slot table; Pact Magic; multiclass |
| F17 spell access | `spell_access` (per-pool, mode) | multiclass distinct pools |
| F18 items, currency, attunement | `dnd5e_item_instances`, `currency` | `test_holdings` (one holder, transfer, attunement, the G1 twelve) |
| F19 creatures | `dnd5e_creatures`, associations, `summon` | `test_holdings`, adoption |
| F20 rest anchors | `rest_anchors` | round trip |

## Acceptance criteria → evidence

| Criterion | Evidence |
| --- | --- |
| Families round-trip on real DB, all twelve classes, multiclass, pools, choices, concurrent effects | `test_round_trip_and_readiness`, `test_state_validation` |
| G1 identities and facts, source-derived, prior bytes intact | `tests/ingestion/mechanical/test_srd_equipment_catalogue`, `test_oracle_succession`, `test_holdings::test_all_twelve_g1_items…`, recording follow-up |
| Typed failures; explicit empty valid; changed schemas refused; readiness ≠ legality | `test_state_validation`, `test_readiness_never_certifies_legality` |
| Bindings enforced; stale, unpublished or invalid refused; unsupported proficiency checks refused; historical replay | `test_store_and_binding`, `tests/pipeline/orchestrator/test_service::…refused_character_binding…`, `tests/pipeline/rpg/test_adapter` |
| Explicit adoption; state preserved; refusals without partial change | `test_hold_and_adoption` |
| Shared changes wait across stories, creatures and packages; no race; held adoption; rejection and withdrawal visible | `test_hold_and_adoption`, `tests/pipeline/orchestrator/test_rpg_turn_hold` |
| Concurrency, rollback, crash and retry; stale work cannot commit | `test_store_and_binding` (two connections), crash/retry and conflicting-write tests, `test_rpg_turn_hold` |
| Creatures independent through save/load, absence, sharing, transfer and ended associations | `test_holdings`, `test_a_creature_adopts_on_its_own…` |
| Display and turn paths; obsolete paths unreachable; empty-store migration both ways | `tests/pipeline/rpg/*`, `tests/api/test_visible_state`, `tests/persistence/test_migration_0038_dnd5e_state` |

## Architecture Notes

**Drift and boundaries, stated explicitly:**

- **Same-release oracle succession.** The resolver previously admitted one
  committed file per release. G1 needed a successor for the *same* release
  while preserving the prior file byte-for-byte. `SUPERSEDED_ORACLE_SHA256`
  skips a predecessor by exact digest. This is a bounded extension of
  ADR-005d's committed-authority selection, recorded in the oracles README and
  in the ADR-005d schema-18 amendment.
- **No production writer of override rows existed.** The shared-change
  service is now the only one. A held change never touches
  `rp_mech_overrides`. Activation inserts the rows in one write-locked
  transaction only when no affected pending roll or turn lease exists, and
  only if the result is the exact override-set identity fixed at request
  time. Otherwise it is rejected, never retargeted.
- **In-progress adjudication was not durable.** `rpg_turn_leases` makes it
  durable: the lease commits before any binding read and is released after
  the turn's transaction ends. Releasing late can only delay activation.
  - Leases left by a stopped process are cleared at application start. This
    relies on the single-worker deployment already used for the per-story
    lock (Binding Decision 8).
  - Clearing them recovers leases with no committed event behind them.
    Pending rolls are never cancelled or expired.
  - A multi-worker deployment would need leases owned by a process identity.
- **The commit recheck runs through the hold.** It runs when the turn hold is
  wired, and production wires it. Unit tests that use fabricated characters
  without a database row leave it unwired.
- **Readiness replaces `is_adjudicable`.** It reports missing or invalid
  recorded inputs for the binding and never certifies legality.
- **Proficiency-aware checks are refused.** Skill checks, saving throws and
  any other proficiency-aware or unrecognized check raise `UnsupportedCheckError`,
  surfaced as `AdjudicationPassError`, instead of being rolled ability-only.
  Pure ability checks on unadjusted base scores remain.
- **No current-HP floor at any write.** The turn's effect application removes
  its `max(0, …)`; only ADR-0003's `current ≤ maximum` remains.
- **Retired.**
  - The free-text `rules_package_id`.
  - `Dnd5eCharacterSheet`, with its stored skill totals and free-text class,
    background and equipment.
  - `Dnd5eActiveCondition`.
  - The free-text-reference resolver in the orchestrator.
  - The `dnd5e_character_sheets` and `dnd5e_active_conditions` tables, in an
    empty-store-only migration.
- **Not changed.** `CharacterState` (`character_states`) is story-world state
  used by the Extractor, not the mechanical sheet, and is outside this scope.
- **Item identities beyond G1.** Every table row that can be held as an item
  has an accepted record or component, except focus forms (Crystal, Orb, …),
  saddles, drawn vehicles, large vehicles, feed and stabling. These are
  refused with `UnsupportedIdentityError` rather than authored. Mounts are
  creature instances of the accepted Animals templates.
- **No production creation route.** Production code previously never created
  a full sheet. The typed service (`create_character`) is the creation path;
  a creation or advancement UI is out of scope.
- **Choice schema identity is derived from the effective component.** It
  covers the component's facts, options and prose provenance, and is
  independent of prose order.

No other drift from the design principles.
