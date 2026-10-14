# CRD Issue 15c native preview — correspondence T (C5 → schema 19)

REVIEW MATERIAL. **SIMULATION ONLY**: this is not an Owner acceptance, a publication, an activation or a supersession. The raw C5 parts are preserved byte-for-byte. They remain unaccepted source candidates and the reviewed semantic reference for this mapping, not accepted mechanical authority. This file states every way a native payload differs from its C5 source item. `scripts/native_map.py` implements the mapping, and these reports prove it:

- `reports/reconcile.json`: identity-level reconciliation.
- `scripts/native_map.py check_round_trip`: 5,504 payloads are fixed points.
- `reports/invariant-exemplars.json`: each explicit schema-19 invariant row is refused by a real-fact violation and admitted by its control.
- `reports/scalar-diagnostics.json`.

## Conservation

- **5,504 native facts from 5,470 mapped C5 items.** Each item maps to exactly one native payload. The other 34 are the `tool_activity` identities below, one per C5 tool activity option.
- **Reconciliation is by address, not by family total.** Address means batch, record, component, option and the complete normalized payload. Each batch's new proposal adds, over its identity-matched replayed proposal, exactly the expected multiset of (address, payload):
  - **Result:** 0 missing and 0 extra in all 11 batches.
  - **No replayed fact is lost.**
  - **Hard failures.** `build_proposals.py` refuses outright if a mapped component has no owner, if an owner is duplicated (`owner_map`), or if a fact cannot be claimed on a bound span.
- **Provenance is separate.** Each fact gets a `CONTEXTUAL` claim on every bound span of its component that contains its quote, entry lines or profile region (heading through CR). Its quote, file/line, `source_text`, headings, `source_terms`, conditional phrases and clause/piece text stay governed prose and provenance. They are never minted as facts.

## Address corrections (two, both inside their own affected batch)

| Family | C5 address | Native address | Kind |
| --- | --- | --- | --- |
| `temporary_hit_point_absorption` | `play.damage_and_healing` / `temporary_hit_points` | `play.damage_and_healing` / `lost_first` | same record, sibling component (Combat, Damage and Breaking) |
| `shield_training_requirement` | `equipment.armor` / `armor_training` | `equipment.armor.shield` / `shield` | **nested-record** relocation within Equipment (not same-record) |

Both quotes and payloads are unchanged. In each case, no span bound to the C5 component contains the quote, and exactly one bound component in the batch does contain it.

## Tool activities (Codex native tool-selection correction)

The native component contract is a conjunction or a choice, never both. A choice of one option is invalid, and two options may not state identical typed facts. This contract is **unchanged**, and `option_set_violations` is not bypassed. C5 gives 34 tool activity options on 25 tools. Each C5 option key is preserved as a selectable native identity:

- **New schema-19 family `tool_activity`** with one closed field `activity: ToolActivity`. The vocabulary is exactly the 34 reviewed C5 option keys, derived mechanically and asserted equal. Each key appears only on its own C5 tool.
  - It is an identity only. The activity text (C5 `option.text`) stays governed prose, and no rule or selection semantics are added.
  - It is a **review-delta item**. Codex may classify it as material.
- **Two or more activities make a choice.** Each C5 option key becomes a `ComponentOption` with that semantic key. Each option carries its own `ability_check` and `tool_activity`, and **replicates** the tool's common facts (`tool_entry`, and `tool_variants` for Gaming Set and Musical Instrument). The component then states no direct facts.
- **One activity is a direct conjunction.** The activity's `ability_check` and `tool_activity`, plus the common facts, sit on the component. That is the disclosed selection address of a single-activity tool.
- **The three identical-numeric pairs stay distinct.** These are Alchemist's Supplies, Thieves' Tools and Weaver's Tools. Their two options differ only by `tool_activity`, which is exactly what the source distinguishes. The rejected collapse is gone.
- **Negative controls on the unchanged validator** (`reports/reconcile.json`):
  - the same activity identity on two options is refused;
  - the pair without identities is refused;
  - a single option is refused;
  - distinct identities are admitted.

The table below is generated from `reports/reconcile.json`. Multiplicities: one `ability_check` and one `tool_activity` per activity. Common facts are counted as C5 → native.

| Tool (record / component) | Shape | C5 activity option → native address | Activity facts | Common facts (C5 → native) |
| --- | --- | --- | --- | --- |
| `equipment.tools` / `brewers_supplies` | choice | `detect_poisoned_drink` → option detect_poisoned_drink<br>`identify_alcohol` → option identify_alcohol | ability_check intelligence DC 15, tool_activity<br>ability_check intelligence DC 10, tool_activity | tool_entry 1→2 |
| `equipment.tools` / `carpenters_tools` | direct (single activity) | `seal_or_pry_open_a_door_or_container` → component (direct) | ability_check strength DC 20, tool_activity | tool_entry 1→1 |
| `equipment.tools` / `cartographers_tools` | direct (single activity) | `draft_a_map_of_a_small_area` → component (direct) | ability_check wisdom DC 15, tool_activity | tool_entry 1→1 |
| `equipment.tools` / `cobblers_tools` | direct (single activity) | `modify_footwear_to_give_advantage_on_the_wearers_next_dexterity_acrobatics_check` → component (direct) | ability_check dexterity DC 10, tool_activity | tool_entry 1→1 |
| `equipment.tools` / `cooks_utensils` | choice | `detect_spoiled_or_poisoned_food` → option detect_spoiled_or_poisoned_food<br>`improve_foods_flavor` → option improve_foods_flavor | ability_check wisdom DC 15, tool_activity<br>ability_check wisdom DC 10, tool_activity | tool_entry 1→2 |
| `equipment.tools` / `disguise_kit` | direct (single activity) | `apply_makeup` → component (direct) | ability_check charisma DC 10, tool_activity | tool_entry 1→1 |
| `equipment.tools` / `forgery_kit` | choice | `duplicate_a_wax_seal` → option duplicate_a_wax_seal<br>`mimic_10_or_fewer_words_of_someone_elses_handwriting` → option mimic_10_or_fewer_words_of_someone_elses_handwriting | ability_check dexterity DC 20, tool_activity<br>ability_check dexterity DC 15, tool_activity | tool_entry 1→2 |
| `equipment.tools` / `glassblowers_tools` | direct (single activity) | `discern_what_a_glass_object_held_in_the_past_24_hours` → component (direct) | ability_check intelligence DC 15, tool_activity | tool_entry 1→1 |
| `equipment.tools` / `masons_tools` | direct (single activity) | `chisel_a_symbol_or_hole_in_stone` → component (direct) | ability_check strength DC 10, tool_activity | tool_entry 1→1 |
| `equipment.tools` / `navigators_tools` | choice | `determine_position_by_stargazing` → option determine_position_by_stargazing<br>`plot_a_course` → option plot_a_course | ability_check wisdom DC 15, tool_activity<br>ability_check wisdom DC 10, tool_activity | tool_entry 1→2 |
| `equipment.tools` / `painters_supplies` | direct (single activity) | `paint_a_recognizable_image_of_something_youve_seen` → component (direct) | ability_check wisdom DC 10, tool_activity | tool_entry 1→1 |
| `equipment.tools` / `potters_tools` | direct (single activity) | `discern_what_a_ceramic_object_held_in_the_past_24_hours` → component (direct) | ability_check intelligence DC 15, tool_activity | tool_entry 1→1 |
| `equipment.tools.alchemists_supplies` / `alchemists_supplies` | choice | `identify_a_substance` → option identify_a_substance<br>`start_a_fire` → option start_a_fire | ability_check intelligence DC 15, tool_activity<br>ability_check intelligence DC 15, tool_activity | tool_entry 1→2 |
| `equipment.tools.calligraphers_supplies` / `calligraphers_supplies` | direct (single activity) | `write_text_with_impressive_flourishes_that_guard_against_forgery` → component (direct) | ability_check dexterity DC 15, tool_activity | tool_entry 1→1 |
| `equipment.tools.gaming_set` / `gaming_set` | choice | `discern_whether_someone_is_cheating` → option discern_whether_someone_is_cheating<br>`win_the_game` → option win_the_game | ability_check wisdom DC 10, tool_activity<br>ability_check wisdom DC 20, tool_activity | tool_entry 1→2, tool_variants 1→2 |
| `equipment.tools.herbalism_kit` / `herbalism_kit` | direct (single activity) | `identify_a_plant` → component (direct) | ability_check intelligence DC 10, tool_activity | tool_entry 1→1 |
| `equipment.tools.jewelers_tools` / `jewelers_tools` | direct (single activity) | `discern_a_gems_value` → component (direct) | ability_check intelligence DC 15, tool_activity | tool_entry 1→1 |
| `equipment.tools.leatherworkers_tools` / `leatherworkers_tools` | direct (single activity) | `add_a_design_to_a_leather_item` → component (direct) | ability_check dexterity DC 10, tool_activity | tool_entry 1→1 |
| `equipment.tools.musical_instrument` / `musical_instrument` | choice | `improvise_a_song` → option improvise_a_song<br>`play_a_known_tune` → option play_a_known_tune | ability_check charisma DC 15, tool_activity<br>ability_check charisma DC 10, tool_activity | tool_entry 1→2, tool_variants 1→2 |
| `equipment.tools.poisoners_kit` / `poisoners_kit` | direct (single activity) | `detect_a_poisoned_object` → component (direct) | ability_check intelligence DC 10, tool_activity | tool_entry 1→1 |
| `equipment.tools.smiths_tools` / `smiths_tools` | direct (single activity) | `pry_open_a_door_or_container` → component (direct) | ability_check strength DC 20, tool_activity | tool_entry 1→1 |
| `equipment.tools.thieves_tools` / `thieves_tools` | choice | `disarm_a_trap` → option disarm_a_trap<br>`pick_a_lock` → option pick_a_lock | ability_check dexterity DC 15, tool_activity<br>ability_check dexterity DC 15, tool_activity | tool_entry 1→2 |
| `equipment.tools.tinkers_tools` / `tinkers_tools` | direct (single activity) | `assemble_a_tiny_item_composed_of_scrap_which_falls_apart_in_1_minute` → component (direct) | ability_check dexterity DC 20, tool_activity | tool_entry 1→1 |
| `equipment.tools.weavers_tools` / `weavers_tools` | choice | `mend_a_tear_in_clothing` → option mend_a_tear_in_clothing<br>`sew_a_tiny_design` → option sew_a_tiny_design | ability_check dexterity DC 10, tool_activity<br>ability_check dexterity DC 10, tool_activity | tool_entry 1→2 |
| `equipment.tools.woodcarvers_tools` / `woodcarvers_tools` | direct (single activity) | `carve_a_pattern_in_wood` → component (direct) | ability_check dexterity DC 10, tool_activity | tool_entry 1→1 |

## Normalizations (all mechanical, all in `native_map.py`)

1. **Absent and `null` are one state.** A native optional field is `null`, or `[]` for a sequence. Registered omit-when-empty fields stay absent. `reports/prechecks.json` lists every C5 field where both occur. None has a different reading.
2. **Closed vocabularies for printed phrases.** Tables in `native_map.py` map each phrase to one member:
   - `ADVANTAGE_WHEN`, `APPLIES_WHEN`, `COUNT_FORMULA`, `OBSERVER_*`, `SURFACES` and `CHOICE_SOURCE`;
   - `ONE_WORD` number words (two…ten, including eight);
   - `ABBREVIATION`: `STR` → `strength` and the like (Disciplined Survivor).

   No member is a reading C5 does not state.
3. **Unions become two fields.** For example `attack_bonus` / `attack_bonus_formula`. Each pair is constrained exactly-one or at-most-one by the invariant manifest.
4. **Nested accepted facts drop their `family` tag.** The declared type carries it, and the accepted builder and check rebuild them.
5. **Reserved words are renamed:**
   - `from` → `from_skills` / `options` / `chosen_from`;
   - `while` → `while_state`;
   - `class` → `class_key`.
6. **Clause pieces** are prefixed `clause_` and carry their locus: entry, section, part, piece, branch and effect addresses.
7. **The stat-block profile decomposes into accepted families:**
   - `creature_ability_score` (C5 "save" → `save_modifier`);
   - `damage_response`;
   - `condition_effect` immunity.

   Qualified entries go to `creature_conditional_defense`, and sizes to `creature_size`.
8. **The Archmage's qualified Charmed immunity.** Its condition is read from the C5 `conditional` phrase (*"charmed, while under Mind Blank"*), because the predicate does not repeat it.
9. **Duration `possessor` is not minted.** It is redundant with the retained `turn_of`:
   - all 25 dropped possessors sit on boundaries whose `turn_of` is `source` (`reports/reconcile.json`);
   - each names the record's own creature (`reports/prechecks.json`).

   Likewise, "Grappled by the X" collapses into `target_grappled_by_source` only where X is the record's creature.
10. **Weakening Breath.** C5's ability on a D20 Test becomes `ability_based: AbilityBasedD20Tests` on `clause_roll_modifier`, with an exactly-one invariant against `effects`. No accepted `AdvantageFact` rule is loosened.
11. **`WeaponPropertyFact` gains four omit-when-empty fields in schema 19:** `ammunition`, `ammunition_range_normal_feet`, `ammunition_range_long_feet` and `unless`. Every accepted payload keeps its canonical form, as `reports/lift.json` proves.
12. **Grant `gain_levels`** reference the accepted G1 `progression_entry` by entitlement key.
    - **Observation (not relied on):** G1's quantity-bearing `weapon_mastery` progression entry merges the Barbarian and Fighter counts under one unqualified key. C5 recorded this under capability `observations`. The native preview does not change it.

## Not in this preview

- Capability, runtime grant validation, `checks.py`, gameplay execution.
- Any accepted-family change.
- Anything C5 holds or excludes.
