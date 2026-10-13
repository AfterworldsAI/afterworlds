# CRD Issue 15c C8 correction review — original reproductions closed; one presence-reader residue

Reviewed immutable **`c6c2b2ad295d7d474eaa900a77988af20832e7d5`**, against the three findings and bounded shared-path addendum in `codex-c8-execution-review.md`. The original reproduced paths are corrected. One concrete member of the same Familiar-presence family remains: an absent Familiar can still contribute as a physical bystander. This is settled implementation work, not an Owner Decision or another acceptance milestone.

## Independent evidence and closed findings

`c8-execution-review/correction/probe.py` preserves the original probe/results and imports all **143** project/test Python modules from Git blobs at c6c2b2, including the changed ToolGrant models/services. It hash-checks the unchanged real C8 oracle before and after. The run completed with actual process **exit 0** and **27 service controls**: 26 confirm correction/retained positive behavior; the final one demonstrates the residue below. Results SHA-256: `987d466cb730d559537dac72de555ac59076835df2c8d2dd29f83dce2c1b86d7`. Per-module and evidence pins are retained alongside the results.

| Original finding/path | Corrected evidence at c6c2b2 |
| --- | --- |
| Duplicate/conflicting species selection after an otherwise valid Wolf Bite | Both now raise typed `invalid_selection` with **zero dice**, through `service._species_once` (`service.py:230,588`). |
| Independent subjects | Two Bandits record Elf/Dwarf together through the real service, zero dice, exactly two separately addressed effects. This goes beyond the engineer's direct helper-only independence test. |
| Hidden species in repeat error | A hidden Elf record is applied; normal Writer view remains identity-free; a later Dwarf proposal refuses without exposing `elf`. Backend selection/effect identity remains intact. |
| Familiar actor prohibition | Present Find Familiar Cat Scratch refuses before dice. |
| Familiar direct target, unknown/absent/present | Unknown presence returns `missing_state`; pocket dimension/gone return `invalid_selection`; present Ghoul damage returns the explicit unsupported source-consequence hold. All before dice. |
| Shared weapon and direct-save damage | Club and Acid Breath now refuse before attack/damage/save dice. The guard is in both `damage.preflight` and `take_damage`, also covering creature damage and Graze's shared execution. |
| First aid, actor-turn death save, Stable recovery and knockout recovery | Present Familiar paths return the explicit source-consequence hold; gone Familiar paths refuse presence. All produce no dice or effects. |
| Ordinary controls | Club, Acid Breath and Ghoul damage remain executable. Ordinary first aid stabilizes; natural-20 death save and elapsed Stable recovery restore HP; knockout recovery clears Unconscious and retains Prone. |

The new `familiars.py` keeps source-qualified type separate from attack/lifecycle permission. The corrected architecture note labels these refusals as holds, not Familiar-lifecycle coverage. No general Familiar engine was introduced. The original 33 named-form/type results, native/source/recording conservation, certification proof and delivery/API transaction evidence are reused where unchanged. Type derivation itself changed only in the hidden-repeat error text; no repeat of its 33 combinations was needed.

## P1 — an absent Familiar still changes attack odds as a bystander

**MERGE-BLOCKING DEFECT / implementation work; remaining member of the existing source-presence family.** The new presence guard checks direct attackers/targets/edges and zero-HP entry points, but `bystanders._read` (`src/afterworlds/pipeline/rpg/bystanders.py:63-85`) resolves and returns physical participants without checking their recorded presence. `allies` (`:115-127`) excludes only Incapacitated subjects. `creature_attacks.py:292-296` then uses that list for Pack Tactics.

The independent control supplies an exact Find Familiar Fey Cat with `presence=pocket_dimension` as the Wolf's named ally within five feet of its target. The **whole service accepts**, rolls **`2d20kh1`, `1d6`**, damages the ordinary character and stages Prone. Thus the GameMaster's supplied proximity overrides the source-qualified recorded absence. The state's validation/readiness passes, which does not establish physical availability. This contradicts the new `familiars.py` and architecture-note claim that naming a Familiar not recorded present refuses.

The same common `_read` feeds `enemies` (`:89-112`), used by ranged close-combat Disadvantage. That parallel is established statically; no second expensive setup or wider creature census is needed. Enforce the existing presence eligibility at this physical-bystander boundary before dice, for missing/gone/pocket-dimension states, while retaining present Familiar and ordinary bystander participation where independently permitted. This grants no Familiar attack or lifecycle behavior and requires no allegiance, spatial or source-policy redesign.

**Boundary disposition:** the original actor/target/lifecycle reproductions are closed; do not re-fix or replay them. This residue is the same missing source-presence validation on another already implemented physical-participant reader. Source/ownership semantics are settled, so no new Owner vote is justified. The common reader identifies both affected consumers; stop the sibling search after correcting/testing that boundary.

## Actual engineer diagnostic and review boundary

Read and captured the **committed** `rpg-suites-3.result.json`, output and stderr from c6c2b2. Actual result: **exit 0**, start `2026-10-13T19:39:02.1636980Z`, end `2026-10-13T19:40:22.8928951Z`; pytest **675 passed, 52 warnings in 77.23 s**. Terminal output explicitly states focused diagnostics only. Stderr reports formatter success (`43 files would be left unchanged`), not a failure. Exact copied bytes and their hashes are in `c8-execution-review/correction/evidence-pins.json`.

No broad suite, configured-coverage run, CI, E2E store, native build, source census, recording, runtime operation or code/Git mutation was performed. The separately reviewed tool-family changes are not re-reviewed here; their models/services were frozen to prevent mixed-version probes. Required full-suite/configured coverage, unchanged repository gates, exact-head CI and consolidated whole-PR review still remain. No merge or runtime authority is implied.

## Bounded Claude-ready completion

At c6c2b2 the original C8 correction cases pass independent frozen-source controls. Complete only the remaining Familiar-presence boundary in `bystanders._read` or its equivalent shared physical-participant validation: an absent/unrecorded Familiar must not provide Pack Tactics Advantage or close-combat Disadvantage. Preserve ordinary and present qualified bystanders; do not authorize familiar attacks or lifecycle operations. Prove zero-dice refusal for the missing/absent contextual participants and positive unchanged participation. Reuse the 26 successful correction controls and unchanged evidence; no new native/store/E2E or Owner acceptance step. Continue the existing whole-PR work, with no merge/runtime changes.
