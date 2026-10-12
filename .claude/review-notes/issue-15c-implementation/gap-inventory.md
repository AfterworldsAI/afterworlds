# CRD Issue 15c — roster gap inventory (supporting evidence)

> **Revised for #191's updated scope (body `8225e1b6…57a2`) and candidate C2.** Where the tables below say "C1-A/B/C", read "C2-A/B/C". The rows marked *superseded* were changed by the Owner-approved scope update; see "Creature attacks and tools (C2)" at the end.

Each roster operation of #191 is listed against the accepted G1 authority (`2ccbaeba…1258`, schema 18). "Typed" means a structured fact exists on an accepted component. "Prose" means the governing component is prose-bound. "Absent" means no accepted identity exists. Dispositions:

* **now**: executable from accepted typed authority plus adapter procedure. Implemented in this branch.
* **C1-A / C1-B / C1-C**: needs the named part of semantic candidate C1 (`candidate/`). Dependent implementation is **held**.
* **refuse**: outside the roster, or not certifiable. The operation refuses visibly.

## Proposed classification rule (for Codex to confirm)

ADR-005d D3 and ADR-015 D7 make typed facts declarative and execution hand-authored adapter code. Two rules follow from that:

1. **Typed authority.** Every comparison target and every number a record prints must be a typed fact. That covers DCs, AC, dice, ranges, thresholds, counts and per-record data. AC4 requires it explicitly.
2. **Adapter procedure.** Universal arithmetic and sequencing are adapter procedure, governed by the component they implement. That covers:
   * the modifier formula `(score − 10) // 2`, which the accepted 2b adapter already uses;
   * Advantage/Disadvantage cancellation and two-d20 selection;
   * Expertise doubling;
   * total ≥ target;
   * crit dice doubling, with the multiplier itself typed in C1-A;
   * damage-type modifier order;
   * temp-HP-first.

   Certification binds each operation to its governing components' `component_schema_id` (override-aware). A house-rule override of any of them therefore invalidates that operation's certification.

If Codex or the Owner place any listed procedure under typed authority instead, the candidate grows by that fact and the operation moves to held.

## Checks, saves, initiative, tools

| Operation | Inputs and target | G1 status | Disposition |
| --- | --- | --- | --- |
| Ability check (any of six), skill check (18) | Ability from `SKILL_ABILITY` (schema-owned, printed Skills table); PB from `proficiency_bonus_band` (typed); `proficiency_application` skill (typed); Expertise (prose, procedure) | Typed except target | **now** for every check whose DC is a source-fixed typed identity (`ability_check` with `dc_kind=fixed`: long jump low obstacle and difficult landing, difficult climb, rough water, Hide, Medicine first aid and stabilize). **C1-A** for a GameMaster-selected difficulty (`typical_dcs` is prose; candidate `difficulty_band` ×6). |
| Six ability saves | Same, plus `proficiency_application` saving throw (typed) | Typed fixed-DC save identities: falling off (Dex 10), starvation (Con 10) | **now** for those identities. **C1-A** otherwise: a save DC comes from the effect, and only C1-A mastery Topple supplies one. A GameMaster-chosen save difficulty is **refuse**: the difficulty table is printed for ability checks only (`playing-the-game.md`:243). |
| Ability adjustments | `ability_adjustments` (amount, maximum, source), recorded | Procedure: sum, then cap at `maximum` or 20 | **now** for an adjustment whose source is a recorded grant. A conditional or unrecognised source refuses. |
| Advantage/Disadvantage | `advantage` facts on recorded conditions (typed); `automatic_outcome` (typed) | Typed; several carry prose applicability (sight, hearing, source of fear in line of sight) | **now** for unconditional condition facts. A fact whose applicability code cannot decide refuses (AC4: unsupported contributing effects refuse). |
| Initiative roll (no order management) | Dex check | `play.combat/initiative_roll` prose | **C1-A** (`initiative_roll`) |
| Tool checks | Tool ability; Utilize DCs; tool proficiency PB; skill-plus-tool Advantage (typed `advantage` with `requires_proficiencies`) | Ability and DCs prose | *Superseded:* **C2-A** covers all 25 tools at their accepted grain (13 records and 12 `equipment.tools` components), plus the variants. The repair to 2b tool validation and the variant addressing are held. |
| Contests, Influence (target Int), Hide's recorded total as a later DC | — | — | **refuse**. Contests are not in the roster. Influence and recorded-total need a second subject's state, and the roster does not admit them. |

## Weapons and masteries

| Operation | Needs | G1 status | Disposition |
| --- | --- | --- | --- |
| Weapon identity, category, mastery property | `weapon_category`, `weapon_mastery` (G1) | Typed | Used as-is |
| Damage dice and type, Melee/Ranged class, properties and their parameters (range, versatile dice, ammunition type) | Weapons table | Absent | **C1-A** (`weapon_damage`, `weapon_range_class`, `weapon_property`; 38 rows, source-derived) |
| Attack ability (Str melee, Dex ranged, Finesse choice, Thrown) | Attack Roll Abilities table; property rules | Prose | **C1-A** |
| Proficiency on attacks | `proficiency_application` weapon (typed); `WeaponProficiencyGrant` | Typed | Used as-is |
| Natural 20/1 on attacks, crit damage | `natural_20`, `natural_1`, `critical_hits` | Prose | **C1-A** |
| Damage modifier and minimum 0 | `damage_rolls` | Prose | **C1-A** |
| Heavy, Range, Reach, Two-Handed, Versatile, Light, Loading, Ammunition | Property definitions | Prose | **C1-A**. Lance "Two-Handed (unless mounted)": mount state is not recorded, so its attacks refuse unless wielded two-handed. Ammunition recovery after a fight is excluded. |
| Mastery eligibility | Class `weapon_mastery` feature plus `progression_entry` count (typed); `ChoiceRecord` selecting weapon kinds | Typed | Used as-is. Possession does not establish eligibility. |
| Eight mastery effects | Mastery definitions | Prose | **C1-A** (`mastery_effect` ×8) |
| Target AC, character | Base AC 10 + Dex; armor table; Shield; Armor Training | Prose/absent (`BaseArmorClass`: "the AC value is 15c's") | **C1-C**. A non-default `BaseArmorClass.source` (Unarmored Defense etc.) refuses. |
| Target AC, size, save modifiers and defenses, creature | Stat block | 336 creature records, **zero facts** | **C1-B** (defensive profile only) |
| Damage resistance, vulnerability, immunity | Character `damage_responses` (recorded); creature: stat block; modifier factors typed (`glossary.resistance`, `glossary.vulnerability`) | Character typed; creature absent | Character: with C1-A. Creature: **C1-B** |
| Monster stat-block actions (their own to-hit and damage) | Printed bonus, reach/range, damage, rider; save DC and effect; Multiattack | Prose (all 336 creature records carry zero facts) | *Superseded:* in scope, and covered by **C2-B**. Each entry is classified individually. |
| Position, distance, reach, range bands; Push/Cleave geometry | Explicit mechanical position state | Not recorded | State work held with C1-A dependents. Proposed placement: an additive 15c-owned per-subject table; the 2b document schema is not bumped. |
| Unconscious "within 5 ft" automatic crit | Position | Typed with prose applicability | Held with position state |

## Zero-HP lifecycle

| Operation | G1 status | Disposition |
| --- | --- | --- |
| Temporary HP absorbed first | Prose (`temporary_hit_points`) | **C1-A** |
| Reaching 0; adjudication clamp after overflow (ADR-0003: no persistence floor) | Prose (`hit_points`) | **C1-A** (`hit_point_bound`, executed after overflow is computed) |
| Monster dies at 0; per-subject GameMaster exception | Prose | **C1-A**, plus an explicit, recorded per-subject classification. Unresolved classification refuses. A creature table row is not a classification. |
| Hit Point maximum 0; effective maximum (`maximum − maximum_reduction`) | Prose | **C1-A** |
| Massive damage | Prose | **C1-A** |
| Unconscious and dying | Typed `condition_effect` unconscious (`falling_unconscious`) | Condition typed. The dying/death-save start is **C1-A**. |
| Death saves (d20 ≥ 10, 3/3, nat 1 = two failures, nat 20 = regain 1 HP, start-of-turn timing, resets) | Prose | **C1-A**, and needs explicit actor-turn authority |
| Damage at 0 HP (1 failure, 2 on crit, instant death at ≥ maximum) | Prose | **C1-A** |
| Stabilizing (Help + Medicine DC 10) | Check typed; "becomes Stable" prose | Check **now**; Stable effect **C1-A** |
| Stable: no saves, stays Unconscious, damage ends it, regains 1 HP after 1d4 hours unless healed | Prose | **C1-A**, and needs elapsed-time authority |
| Knockout alternative (melee; set 1 HP and Unconscious; ends after Short Rest, on regaining HP, or on first aid) | Condition and Medicine DC typed; 1 HP and Short Rest prose | **C1-A** (`knockout_alternative`, `rest_duration`) |
| General healing, rests, resurrection | — | **refuse** (non-goal) |

## Delivery, authority and state (independent of C1)

| Concern | Disposition |
| --- | --- |
| Production wiring after Planner and before Writer; backend shown/hidden dice; no pending-roll service | **now** |
| Player-roll configuration refuses before any pending request | **now** |
| Capability manifest, certification and six-way refusal taxonomy | **now** |
| Prompt reconciliation: the unsupported-to-narration rule is replaced by visible refusal; the narratively-impossible rule is kept | **now** |
| Filtering of hidden state; `gm_cheating = off` immutability | **now** (existing records, extended to new outcomes) |
| Multi-subject atomic application and subject identity on effects | Held with C1-B/C1-C. The first multi-subject operation is an attack. |
| Explicit actor-turn and elapsed-time authority | Held with C1-A dependents (death saves, mastery timing, Nick/Cleave limits). Placement is recorded above. |

## Creature attacks and tools (C2)

| Family | Status | Disposition |
| --- | --- | --- |
| Ordinary creature attacks (weapon, natural, special) | 423 parsed, equal to the source count | **C2-B**: supported or conditional per entry, each with exact reasons |
| Bounded save effects | 159 typed; 28 special effects named | **C2-B** |
| Multiattack | 179 compositions | **C2-B**. A spellcasting substitution is a named deferral. |
| Usage limits (X/Day, Recharge, rest, lair, form-only) | Typed per entry | **C2-A** rules plus C2-B entries. Timing and state prerequisites are named. |
| Contributors | 4 recurring contributors typed with predicates; 57 named | **C2-B**. Operations they can affect refuse until accepted. |
| Spellcasting, reactions, Shape-Shift, Berserk, Coven Magic | Deferred, named | Spellcasting is a non-goal; the others are new mechanics surfaced individually |
| The six creatures printed in Spells or Magic Items | Giant Fly fixed; five parameterized | **C2-B**, as assessed creatures |
| Half-Dragon, Archmage, Rakshasa, Vampire Familiar | Conditional | **C2-B**. The Vampire Familiar's master relation is a surfaced prerequisite. |
| All 25 tools | Typed at their accepted grain | **C2-A**. The validation and variant repair is held. |
