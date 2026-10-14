# CRD Issue 15c C8 presence follow-up — remaining defect closed

Reviewed immutable **`6caa63e36a143feab0d3ddec50175803d24ee8c4`**, relative to correction review `c6c2b2ad295d7d474eaa900a77988af20832e7d5`. **The remaining Familiar-bystander P1 is closed. No residue found within this assigned boundary.** This completes the already classified implementation correction; it creates no new Owner decision or acceptance gate.

`src/afterworlds/pipeline/rpg/bystanders.py:84` now calls the existing `familiars.require_present(subject)` in `_read`, before appending the resolved physical participant. Both Pack Tactics' `allies` and close-combat `enemies` consume that reader. Unknown presence returns `missing_state`; pocket dimension/gone return `invalid_selection`. The unchanged helper recognizes the accepted Familiar source keys; it does not apply a generic presence requirement to ordinary creatures. Eligible present Familiars retain bystander participation. This grants no Familiar attack or lifecycle execution.

## Independent service evidence

`c8-execution-review/presence-final/probe.py` reuses the previous frozen loader, changing its revision to 6caa63. All **140 imported project/test Python modules**, including models and services, came from that revision's Git blobs rather than mutable working imports. The real accepted C8 oracle was hash-checked before and after, unchanged at `ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d`. Full import pins and actual adjudication records are retained in `presence-final/results.json`; its SHA-256 is **`ecac2425f17392f2023f5e683de0aaa58a90a6eec72759c19cb2d1a7359b93fb`**. Actual process exit: **0**.

All **10 controls** passed through `RpgAdjudicationPassService`:

| Named bystander | Pack Tactics ally | Ranged close-combat enemy |
| --- | --- | --- |
| Source-qualified Familiar, unknown presence | `missing_state`, zero dice | `missing_state`, zero dice |
| Source-qualified Familiar, pocket dimension | `invalid_selection`, zero dice | `invalid_selection`, zero dice |
| Source-qualified Familiar, gone | `invalid_selection`, zero dice | `invalid_selection`, zero dice |
| Source-qualified Familiar, present | Accepted; `2d20kh1`, `1d6`; Pack Tactics provenance | Accepted; `2d20kl1`, `1d4`; close-combat provenance |
| Ordinary Cat | Same accepted Advantage behavior | Same accepted Disadvantage behavior |

The new `test_familiar_limits.py` additions cover all three unavailable states at both adapter preflight consumers, check refusal kinds and subject identity, and resolve a present Familiar ally with exact Pack Tactics provenance. The independent service controls additionally exercise the present close-combat enemy and ordinary positive cases, and directly record the zero-dice negative outcomes.

## Changed-input and reuse boundary

Compared c6c2b2 to 6caa63 across source and tests. The presence correction changes only the shared reader and its tests. `familiars.py`, species selection/error handling, service preflight, source/type derivation, model/state-service validation and zero-HP entry-point guards are unchanged. Preserve the earlier **26 successful correction controls**, original type/form/source/native/recording conservation and delivery evidence for those unchanged claims; do not replay their setups.

Two independent production changes in the same interval affect `attacks.py`'s fixed-damage ability modifier and `damage.py`'s damage-at-zero/temporary-HP execution. Their diff was inspected to identify this invalidation boundary; their correctness and expanded coverage remain with the parent's whole-PR coverage track. Neither removes or alters the existing Familiar preflight/zero-HP holds. Earlier ordinary damage results are historical controls, not fresh proof of these changed damage semantics. The new present/ordinary bystander controls execute at healthy HP with rolled weapon damage and verify the assigned presence behavior only.

## Recorded engineer diagnostic

Read and copied the committed `rpg-suites-4.result.json`, stdout and stderr from 6caa63, with exact-byte hashes in `presence-final/evidence-pins.json`. Actual result: **exit 0**, start `2026-10-13T20:22:09.9549780Z`, end `2026-10-13T20:28:49.5243664Z`; **812 passed, 159 warnings in 395.47 seconds**. Stderr records successful formatting validation, `40 files would be left unchanged`. The output explicitly calls this **focused diagnostics only, not acceptance or full-gate evidence**.

No broad suite, native build, store setup, E2E rerun, source/test/baseline/Git mutation or runtime action was performed for this follow-up. The parent retains consolidated whole-PR judgment and verification of the required full-suite/configured coverage, repository gates and exact-head CI. No merge authority is implied.
