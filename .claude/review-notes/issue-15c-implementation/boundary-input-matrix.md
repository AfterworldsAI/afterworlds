# CRD Issue 15c — input matrix and persisted-state boundary note (for Codex)

Written 12 October 2026, after the native C5 successor was recorded locally. #191 admits "the minimum explicit mechanical target, position and timing state required" for weapons and masteries, and "explicit actor-turn or elapsed-time authority" for the zero-HP lifecycle. It excludes a general encounter engine, initiative-order management and a competing persisted pending/sequence model (ADR-015b).

The operations below need inputs that 2b state does not record. Choosing **how** to persist them changes the persisted model, so this note surfaces it before implementation instead of deciding it silently. The proposal in §3 is what I intend to implement unless Codex classifies it otherwise.

## 1. Operation → inputs → 2b today → authority → refusal

| Operation | Required inputs | In 2b state? | Authority for the number/rule | Refusal when absent |
| --- | --- | --- | --- | --- |
| Ability/skill check vs GM difficulty | ability, skill, a GM-selected `difficulty_band` identity | yes (scores, grants) | `difficulty_band` (C5-A), typed grants | `INVALID_SELECTION` (unknown identity); `MISSING_STATE` |
| Saving throw | ability, a DC from a typed source: a creature `save_effect`, a mastery DC formula or a GM difficulty identity whose `applies_to` covers saves | scores, save grants | the causing fact; `saving_throw_proficiency_grant` | `MISSING_AUTHORITY` when no typed DC source exists |
| Tool check | tool record/component, `tool_activity` identity, ToolGrant | ToolGrant (record/component) | `tool_entry` + `tool_activity` + `ability_check` | `INVALID_SELECTION` (activity not on that tool) |
| Initiative | Dexterity, Advantage/Disadvantage contributors | yes | `initiative_roll` | outcome `undetermined` (admitted) |
| Weapon attack | attacker, weapon item instance, target subject, **distance band** (within reach / normal / long range), target AC | item, scores, grants; AC derivable from C5-C armor facts; **distance: not recorded** | weapon rows (C5-A), AC formulas (C5-C) | `MISSING_STATE` (no position) |
| Mastery Cleave/Graze/Nick/Vex/Sap | first target; second target within 5 ft and within reach (Cleave); same-turn limits | **adjacency and per-turn use counter: not recorded** | `mastery_effect` | `MISSING_STATE` |
| Mastery Push/Topple/Slow | target size, a forced-move distance, a save, a speed reduction lasting to the start of the attacker's next turn | **turn boundary: not recorded** | `mastery_effect` + `TurnBoundary` | `MISSING_STATE` |
| Creature attack / Multiattack | creature subject, entry identity, target, distance band | creature document; distance not recorded | `creature_attack`, `creature_multiattack` | `MISSING_STATE`; per-piece `UNSUPPORTED_CAPABILITY` |
| Creature save effect | area/targets, origin, visibility predicates | **area membership: not recorded** | `creature_save_effect.targets` | `MISSING_STATE` |
| Damage, temporary HP, zero HP, massive damage | target HP, temporary HP, damage responses, character-vs-monster classification | HP, temp HP, responses; classification via document kind plus a recorded GM exception | `damage_response`, `temporary_hit_point_absorption`, `zero_hit_point_outcome`, `massive_damage` | `MISSING_STATE` (unresolved classification) |
| Death saving throw | dying subject, **the start of its turn** | death_state; **actor-turn event: not recorded** | `death_saving_throw`, `death_save_natural_roll` | `MISSING_STATE` (no actor-turn authority) |
| Stabilize | Help/Medicine DC 10 against a subject at 0 HP | yes | `stabilization` | as for checks |
| Stable recovery (1d4 hours) | elapsed time since becoming Stable | **fiction-time markers only (strings)** | `stable_state.recovery` | `MISSING_STATE` |
| Knockout alternative | melee attack that reduces to 0, attacker's choice | yes | `knockout_alternative` | — |

## 2. What is missing, as one list

1. **Pairwise distance** between subjects taking part in a mechanical exchange. It needs a closed, discrete form: within 5 ft, within reach, within normal range, within long range, beyond. Distance must never be a GameMaster-authored number.
2. **Actor-turn state**: whose turn it is now, a round counter, and the events "start of X's turn" and "end of X's turn". These are needed to expire `TurnBoundary` effects (Slow, Vex, Sap, rider durations) and to trigger death saves.
3. **Per-turn use limits**: Cleave and Nick are once per turn, the Light-property extra attack once per turn.
4. **Area membership** for creature save effects.
5. **Elapsed-time authority** for Stable recovery.

## 3. Proposal (intended implementation unless Codex classifies otherwise)

- **A new story-scoped `encounter_state` document**, one per story, persisted in its own table with a revision. It is neither a 2b character/creature state family nor a `STATE_SCHEMA_VERSION` bump. It records only:
  - `participants`: subject references;
  - `active_turn`: subject and round;
  - `distances`: pairwise discrete bands;
  - `areas`: named area membership sets;
  - `turn_effects`: timed effects keyed to a `TurnBoundary`, with source provenance;
  - `turn_uses`: per-turn limit counters.
- **Authority for its contents:**
  - The GameMaster may *select* a band or membership from the closed vocabulary. This uses the same rule as a difficulty identity.
  - Code validates participants and story scope and records provenance.
  - Code alone advances the turn and expires boundary effects. The advance itself is an explicit GameMaster-selected operation (`begin_turn` / `end_turn` for an identified participant) validated by code, never inferred from narrative turns.
  - No initiative order is managed: `active_turn` is set explicitly.
- **It commits atomically with the delivered Turn,** under the same revision recheck and delivery gate as subject state. It is not a pending/sequence model (ADR-015b).
- **Cross-binding rule.** When the attacker and target are bound to different projections:
  - each subject's own binding governs its own facts (the attacker's weapon row, the target's AC and responses);
  - shared procedure must certify under both bindings;
  - otherwise the operation refuses with `INCOMPATIBLE_CERTIFICATION`.

## 4. Open classification questions for Codex

1. Is a new story-scoped encounter table, outside 2b's state contract, acceptable as "minimum explicit target/position/timing state"? Or does any persisted addition here need an Owner Decision?
2. Is GameMaster *selection* of a closed distance band and area membership acceptable authority, given the issue's rule that the GameMaster selects among code-admitted identities?
3. Is an explicit `begin_turn`/`end_turn` operation acceptable actor-turn authority for death saves and `TurnBoundary` expiry, given the exclusion of initiative-order management?

Unaffected work continues meanwhile: checks, saves, tools, initiative, grant validation and single-subject damage plumbing.
