# CRD Issue 15c — combat and lifecycle implementation design (engineering record)

**Governing:** #191, the Owner context decisions of 2026-10-12 (bounded GameMaster spatial facts and timing attestations), `boundary-input-contracts.md` as corrected, and `codex-input-contract-classification.md`. This file records ordinary engineering choices so a reviewer can check them against those authorities. It decides no product policy.

## Subjects and atomicity

- **A turn's subjects** are the acting character, plus every character or creature an operation names. Each is loaded with its own exact binding, revision and authority (`TurnCharacter` / `TurnCreature`, `services/dnd5e_state/turn.py`). A subject outside the story refuses.
- **Effects are addressed to a subject** (`SheetEffect.subject_kind` / `subject_id`; `None` means the acting character).
- **At commit:**
  - every subject the turn read is rechecked against its revision and binding;
  - each subject's effects are applied by compare-and-swap;
  - the Turn, the audit rows and every subject's effects commit together, or none do.
- **Cross-binding:** when subjects are bound differently, every shared procedure component that contributes to the operation is compared under each binding; any difference refuses.

## Approved contextual inputs (OD-15c-1/2)

- **Spatial facts** are operation-scoped selections from code-generated options, bound to the operation's subjects and source thresholds:
  - the range band (within reach, within normal range, beyond normal and within long range);
  - cover degree;
  - a hostile creature within 5 ft of a ranged attacker;
  - Cleave's two relationships;
  - area membership, including heavily obscured areas;
  - qualifying movement;
  - Push direction and distance.

  They are recorded in the operation's audit provenance only. A subject that moves during a delivered turn invalidates every later spatial fact that involves it; a later operation then needs fresh facts or it refuses.
- **Visibility for Unseen Attacker / Unseen Target** is derived in code from:
  - recorded conditions (Invisible, Blinded);
  - senses (Darkvision, Blindsight, ...);
  - the approved area-membership fact (heavily obscured or darkness).

  *Classification flagged for Codex:* visibility is treated as area membership under OD-15c-1, not as a separate GameMaster sight assertion.
- **Timing:** explicit `begin_turn` / `end_turn` actor edges drive `TurnBoundary` expiry, per-turn limits and death-save timing. There is no round scheduling. Elapsed-time and Short Rest completion attestations are tied to a recovery or knockout instance and consumed once.

## Zero-HP treatment

- A creature's treatment is recorded per subject (`CreatureState.zero_hit_point_treatment`): the source `zero_hit_point_outcome` subject (character or monster), plus any GameMaster `treat_as_character` exception.
- An unrecorded treatment refuses an operation that would reduce the creature to 0 HP.
- Characters use character treatment.
- Overflow is computed before the 0 bound (massive damage). No persistence floor is applied (ADR-0003); `current` is written at the bound the source states.

## Contributors

- Attack, damage, AC and save contributors are compiled as the check contributors were: a phrase scan of the source, then each entry read.
- Each is executed or refuses; none is ignored.
- Fighting Style feats, Savage Attacker and Defense refuse until typed and executed. This is a coverage boundary raised with Codex.
