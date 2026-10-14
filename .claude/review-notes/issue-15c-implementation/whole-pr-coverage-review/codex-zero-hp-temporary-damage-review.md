# CRD Issue 15c — temporary HP and damage at zero

**Verdict: P1 merge-blocking correctness defect; settled implementation work.** Frozen review of `c6c2b2ad295d7d474eaa900a77988af20832e7d5` reproduces two linked zero-HP errors in the existing shared `take_damage` path. This is the concrete interaction within the already identified AC4/AC7 temporary-HP and zero-HP family, not a new Owner policy or broader engine request. Claude implements; this review changed no production or test inputs.

The accepted source at `docs/sources/community/dnd-5e-srd-markdown/playing-the-game.md:1239` says any damage at zero HP causes death-save failure and damage at least the HP maximum causes death; `:1245` says damage ends Stable; `:1253` says temporary HP absorbs damage first; `:1267` says temporary HP does not heal a zero-HP subject. The frozen authority's typed facts agree: `TemporaryHitPointAbsorptionFact(absorbed_first=True, overflow_to_hit_points=True)`, `DamageAtZeroHitPointsFact(failures=1, critical_hit_failures=2, dies_when_damage_at_least=hit_point_maximum)`, and `StableStateFact(damage_ends_stable=True)`. The governing issue explicitly admits temporary-HP absorption, damage at zero, stability loss and death-save consequences.

`src/afterworlds/pipeline/rpg/damage.py:313-328` reduces `remaining` by temporary HP and returns `absorbed` when `remaining == 0`, before the zero-HP branch at `:333-367`. The latter compares `remaining >= maximum` at `:352`, even though the source's at-zero threshold refers to damage taken. This distinction matters only after a positive post-response damage amount has been absorbed by temporary HP; actual immunity or zero damage must remain harmless. Use the existing `taken`/post-response damage and current HP state to judge at-zero consequences once per hit while still spending temporary HP first. Preserve ordinary above-zero absorption and typed damage-response rules.

Frozen direct production-path results (`damage_interaction_probe.py`, `damage-interaction-results.json`; process exit 0):

| Case | Observed at `c6c2b2a` | Required by accepted source |
| --- | --- | --- |
| Dying, 0/11 HP, 5 temporary HP, 3 Piercing damage | `taken=3`, temporary HP 5→2, `absorbed`; no `death_state` effect | One death-save failure; retain the temporary-HP expenditure |
| Stable, 0/11 HP, 5 temporary HP, 3 Piercing damage | Same `absorbed` result; Stable and recovery instance remain untouched | Stability ends and the damage-at-zero failure applies |
| Dying, 0/11 HP, 5 temporary HP, **11** Piercing damage | `taken=11`, remaining after absorption 6, only one failure, alive | Dead, because damage equals HP maximum |
| Dying, 0/11 HP, 5 temporary HP, 9 Piercing damage | One failure, alive | Correct threshold control: below maximum |
| Dying/Stable at zero, 3 damage, no temporary HP | Both receive `death_save_failure`; Stable ends | Existing non-temporary path is safe |
| Dying at zero with 0 incoming, or poison-immune Skeleton at zero with 3 incoming | `taken=0`, no death-state mutation | Correct no-damage controls |
| 7/11 HP, 5 temporary HP, 3 damage | Temporary HP 5→2; current HP unchanged | Correct above-zero absorption control |

The probe loaded every imported `afterworlds` and `tests` Python module from Git blobs at `c6c2b2a` (139 modules captured in the result), including the ordinary `_dying`/`_stable` fixtures and production `damage.take_damage`. The C8 oracle and cited SRD source matched the same immutable revision byte-for-byte before and after. Recorded oracle SHA-256 `ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d`; `damage.py` SHA-256 and all loaded module hashes are in the JSON. The first invocation stopped before a verdict because the probe used an incorrect Skeleton template key; the corrected invocation above exited 0. No store, native build, source census, pytest suite or mutable project/test import was used.

**Boundary/invalidation:** This proof is exact for the frozen `c6c2b2a` damage module and its captured dependencies. A later edit to damage, state effects or authoritative inputs invalidates the affected behavior and needs focused positive/negative recheck at that revision, then the parent's final stable-head gates. Other previously verified weapon/mastery/delivery evidence is unaffected by this isolated diagnosis unless its imported code changes. The finding asks for bounded tests of the shown interactions and no general healing, rest or inventory engine.
