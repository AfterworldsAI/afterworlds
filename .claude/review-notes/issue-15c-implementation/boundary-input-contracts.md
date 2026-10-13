# CRD Issue 15c — corrected input contracts (answering `codex-combat-state-boundary.md` and the acquisition-order classification)

This note supersedes `boundary-input-matrix.md` §2–§4; §1's operation table stays as context. It states, for every trust-relevant input the held operations need, what supplies it and where its authority comes from. Where no existing accepted contract supplies an input, it isolates the exact Owner Decision instead of deciding it in code.

Nothing here is implemented. The dependent operations stay held and refuse as `unsupported_capability`, naming what they wait on:
- weapon attacks and masteries;
- creature attacks, Multiattack and save effects;
- the death-save turn trigger;
- Stable recovery.

## A. Corrections accepted from the classification

- **No generic pairwise range bands.**
  - Each spatial predicate is bound to one operation, one subject pair and one source threshold. Examples: "target within this weapon's reach (5 ft, 10 ft with Reach)" and "target beyond this attack's normal range (80 ft) and within its long range (320 ft)".
  - A predicate is never stored as a durable distance and never reused for another operation.
- **Zero-HP treatment is not decided by document kind or template location.** *(Corrected per `codex-input-contract-classification.md`.)*
  - A creature document is not thereby a monster, and a pet using an Animals stat block is not thereby a monster either.
  - Treatment is a recorded, source-backed subject classification:
    - the source's `zero_hit_point_outcome` subject (`character` or `monster`);
    - plus any recorded per-subject GameMaster exception (`treat_as_character`, scope `individual_monster`).
  - A subject with no recorded classification refuses. No pet-treatment policy is chosen.
- **Cross-binding agreement is checked, not assumed.** Two valid certifications do not establish agreement. For a multi-subject operation, code compares, under every participating subject's exact binding, every shared-procedure component that actually contributes to that operation, and refuses on any disagreement. The attack roll, damage, critical hits, temporary HP, saves and effects, and the zero-HP rules are examples of such components, not an exhaustive list. No precedence is chosen.

## B. Spatial inputs: what code can and cannot establish

| Predicate | Source threshold (typed) | What would establish it | Existing authority? |
| --- | --- | --- | --- |
| Melee target within reach | weapon reach 5 ft; Reach property +5; creature `reach_ft` | the two subjects' relative position | **none**: no accepted state records position |
| Ranged target within normal / long range | weapon or creature `normal_range_ft` / `long_range_ft` | relative position | **none** |
| Cleave: second target within 5 ft of the first and within reach | `mastery_effect.second_target_within_ft` | positions of three subjects | **none** |
| Push: target moved up to 10 ft straight away | `mastery_effect.distance_ft_up_to` | a resulting position | **none** |
| Creature save effect: who is in the area | `SaveTargets.area` and origin | area membership | **none** |
| Charge-style bonus (`source_moved_straight_toward_target_ft_min`) | typed minimum | the source's movement | **none** |

Neither 2b nor any accepted contract records where subjects are.

**Owner Decision OD-15c-1 (spatial input origin).** May the GameMaster, per operation, select a spatial predicate from a closed set that code generates from that operation's exact source thresholds?
- **What the selection is:** for example, "within reach (5 ft)" or "beyond normal range (80 ft) and within long range (320 ft)" for this attack against this target.
- **Recording:** stored with the operation's provenance, not as a durable world position.
- **Validation:** code checks that the predicate is one the operation admits, and derives Disadvantage and impossibility from it.
- **Without this power,** every attack, mastery and area effect refuses as missing state. Any alternative, such as a persisted coordinate or zone model, would be a larger new contract.
- **Requirements if it is approved** *(corrected per the classification)*:
  - **The full predicate set,** not only weapon range:
    - Cleave's two relationships among three subjects;
    - area origin, shape and membership;
    - movement toward a target over the source-required distance;
    - Push's direction and resulting displacement, preserving the source's "up to" choice rather than always taking the maximum.
  - **Code derives every distance and effect.** A GameMaster choice never authors a numeric mutation.
  - **Each assertion is bound** to its exact subjects, operation, source and current contextual revision.
  - **Movement invalidates spatial assertions,** including between linked attacks within one delivered turn. Downstream operations need consistent, refreshed facts.
  - **An assertion is operation-scoped audit evidence,** never a reusable hidden position record.

## C. Actor-turn edges (in scope per the classification)

- **The operations.** `begin_turn(subject)` and `end_turn(subject)` are explicit operations the GameMaster selects for an identified participant of a story-scoped encounter coordination record. There is no initiative order: the GameMaster selects which participant's turn begins.
- **What code enforces:**
  - Only one turn is active.
  - `begin_turn` requires no active turn. `end_turn` requires the named subject's turn to be active.
  - **No round or scheduling rule.** *(The earlier automatic round advancement was rejected: it let one participant take successive turns while another never acted.)* Only the explicitly selected actor edges are implemented, with source-timed effects keyed to them. A specific admitted rule that needs round scheduling would identify that rule and its exact authority.
  - Every edge is consumed exactly once, with a revision check. A duplicate or retried edge refuses, so no edge can reset a budget or trigger death saves twice.
- **What edges drive,** each per its source fact:
  - `TurnBoundary` expiry for Slow, Vex, Sap and rider durations;
  - per-turn limits for Cleave, Nick and the Light extra attack;
  - the death save at the start of a dying subject's turn (`DeathSaveTiming`: at 0 HP, start of the subject's turn).
- **What edges never do:** be inferred from narrative turns, or turn round counts into hours.

## D. Elapsed time

The 2b `EffectEnd.expires_marker`, `RestAnchors` and `applied_marker` values are fiction-time **strings**. No accepted contract makes them comparable.

**Owner Decision OD-15c-2 (elapsed-time authority).** Stable recovery says a Stable creature that isn't healed regains 1 Hit Point after 1d4 hours. That needs an elapsed-time input.
- **The question:** may the GameMaster assert "N hours have passed for this subject since it became Stable" from a closed selection? Or must elapsed time come from a new code-owned story clock?
- **Until decided,** Stable recovery refuses as missing state.
- **The knockout alternative is affected too.** *(Corrected; the earlier text said it was not.)*
  - Its initial application needs no elapsed time.
  - Its Unconscious ends only on completing a Short Rest, or earlier on regaining Hit Points or a successful first aid (`playing-the-game.md:1203`). A Short Rest is a qualified one-hour period (`rules-glossary.md:1277-1293`).
  - Ending it therefore needs the same kind of instance-linked attestation: "a qualifying Short Rest was completed by this subject since this knockout instance began". Code consumes that attestation once.
  - Until decided, the Short Rest ending refuses as missing state. The early-ending events need no time authority.
- **Requirements if approved:**
  - Attestations are bound to the recovery or condition instance and its anchor.
  - Code draws and retains the source duration (1d4 hours) and derives the due result.
  - No cumulative re-assertion; no inference from narrative turns or rounds; the GameMaster never selects the outcome.
- Death saves and stabilizing need no elapsed time and are unaffected.

## E. Acquisition order of ability increases

- **What is implemented now:** increases apply only when every acquisition order of their cap groups gives the same score (`grants._order_independent`). Otherwise they refuse as missing state.
- **Why that is needed:** each increase applies up to its own cap, so increases with different caps can give different scores in different orders. Codex's example is a multiclass Epic Boon before a later ASI.
- **What existing state supplies:**
  - `level_history` orders class levels;
  - a feat feature's typed `gain_levels` give the class levels at which a selection could be made.
- **What it lacks:**
  - which gain instance a `FeatSelection` used;
  - the order of origin increases relative to feats (origin increases are taken at character creation, so they come first; that is source-stated in `character-creation.md`, not a heuristic).
- **Minimum contract to execute order-sensitive cases:** an optional `gained_at_character_level` on `FeatSelection`, validated against `level_history` and the source feature's `gain_levels`. This is ordinary state representation, an additive 2b field, but it changes the persisted 2b contract. **Proposed, not implemented,** pending Codex classification. Nothing chooses a default chronology.

## F. Other state-contract gaps found while implementing

- **Gaming Set and Musical Instrument.** Proficiency is per kind (`tool_variants`, separate proficiency), but a 2b `ToolGrant` and an item instance record no kind. Their tool checks refuse as missing state. A minimal fix would be an optional `variant` on `ToolGrant` and on the item instance (a state-contract change, for classification).
- **Origin and Fighting Style feats.** Their category is prose-bound in the accepted authority. Eligibility through a category or "any feat you qualify for" choice therefore refuses as missing authority. Skilled has no certifiable path today: no SRD background grants it, and its Origin category is untyped. A typed category for these feats would need a separately reviewed source candidate.
