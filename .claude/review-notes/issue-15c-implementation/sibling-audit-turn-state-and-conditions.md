# CRD Issue 15c — sibling audit: turn-state sequencing and condition coverage

**Trigger.** A narrow fix to `86c0436` (weapon attacks) turned up two defect families, each with siblings beyond the quoted line. The advisor review classified the first family as merge-blocking.

## Family 1: effects computed from a stale snapshot

**Symptom.** Every operation of a turn was prepared and resolved against the snapshot the turn first read.
- Two hits on one target each wrote `current_hp = initial − own damage`. The later write won, so the first hit was lost.
- A second hit at 0 HP was computed as a fresh fall, not a death-save failure.

**Fix.**
- `service._normal` threads an in-memory advanced view (`turn.advanced`) through the turn's operations, in proposal order.
- The result keeps the snapshots as they were read. The orchestrator rechecks their revisions and applies every effect to them in order, so absolute `set` values land last-wins on the cumulative value.

| Sibling inspected | Disposition |
| --- | --- |
| `effects.py` targets `current_hp`, `temporary_hp`, `death_state`, `spell_slot.*` (`set`/`delta`) | patched (threaded view) |
| `effects.py` `apply_condition` / `clear_condition` | patched (threaded view) |
| Actor effects (`subject_id is None`) | patched (`advanced` addresses them to the actor) |
| Creature effects | patched |
| Planned actor-edge, expiry and death-save effects | will use the same threaded path (§G of `boundary-input-contracts.md`) |
| Orchestrator `_apply_subject_effects`, which applies to the snapshots read | already safe (ordered, compare-and-swap on the read revision) |

**Paired invariant.** Refusing before any die is preserved. Each later operation is preflighted with every condition earlier operations *could* apply already present (`adapter.possible_conditions`, `turn.with_possible`).
- **Why this is sound.** The attack, save, check and damage refusal paths each check conditions independently. Adding a condition can only add refusals or Advantage/Disadvantage sources, so passing the union covers every dice outcome.
- **Guard.** A refusal raised after any die of the turn is a `PreflightGapError` that names the gap. It is never an ordinary refusal, because a discarded post-roll turn would let a retry reroll (Invariant 10).

**Regressions:**
- `test_turn_sequencing.py`: compounding, preflight before dice, and the post-roll guard;
- `test_weapon_attacks.py`.

## Family 2: condition facts silently skipped

**Symptom.** The attack's condition scan read only `advantage` and `automatic_outcome` facts on *recorded* conditions. It silently skipped:
- Paralyzed's and Unconscious's automatic Critical Hit;
- Prone's prose-bound "attacks against" rule;
- Incapacitated's action restriction;
- Charmed's "can't attack the charmer";
- Petrified's resistance;
- every condition *implied* by another (Unconscious gives Incapacitated and Prone; Paralyzed, Petrified and Stunned give Incapacitated).

**Fix.**
- **`conditions.effective` (new)** returns recorded plus implied conditions. Implied ones are typed `condition_effect` `applies` facts on structured components with no circumstance.
- **`attacks._ATTACK_RULES`** classifies every condition component explicitly (`rolls`, `no_action`, `charmer`, `auto_critical`, `prone_against`, `damage`, `none`). A component that isn't listed refuses.
- **New approved spatial input `target_within_5_feet`** (OD-15c-1). A 5-foot melee attack implies it, and a contradiction is invalid.

| Sibling inspected | Disposition |
| --- | --- |
| `attacks._condition_sources` | patched (reviewed classification) |
| `checks._advantage` implied conditions: an Unconscious or Stunned subject's Initiative misses Incapacitated's Disadvantage | patched (`effective`) |
| `checks._advantage` other families | already safe: an automatic outcome refuses, and Incapacitated doesn't forbid ability checks |
| `saves._conditions` implied conditions | patched (`effective`); no implied condition bears on saves today |
| `damage.preflight`: a condition's damage response (Petrified) | patched; refuses for every damage caller |
| `defense.armor_class`: conditions changing AC | already safe (no SRD condition changes AC) |
| Death-save and Stabilize operations | out of scope here; they must read `effective` when implemented |

**Regressions:** `test_weapon_attacks.py` (automatic critical, Prone both ways, missing 5-foot fact, the 5-foot contradiction, Incapacitated attacker, Charmed attacker, Petrified target) and `test_bounded_checks.py` (implied Incapacitated on Initiative).

## Surfaced, not decided

- **Action economy (owner decision needed or Codex classification).** Nothing bounds how many `weapon_attack` proposals one character makes in a delivered Turn. Light's extra attack and Nick ("once per turn", "as part of the Attack action") assume code can tell which attack belongs to the Attack action. Light and Nick are held until this is classified.
- **Contributors held by another creature (Codex classification).** An ally's Aura of Protection, Boon of Fate and Countercharm can't be seen by a save that loads only its saver (`saves/save-contributor-scan.md`).
