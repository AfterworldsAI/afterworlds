# CRD Issue 15c — creature execution final review

**Verdict: two bounded implementation corrections remain.** Reviewed implementation HEAD `b5051d8433ac2be7336daa41f2aae038b9d21c9e`; the governing issue SHA-256 is `8ad877861b821aa927c38a39227ea58ea150ff8fdb4d7b2a161044d45727426f`. No Owner Decision is needed for these findings. No implementation, acceptance, Git, publication or shared-store changes were made.

Applied the installed Afterworlds Review and task-routing skills and reused the parent task's verified-current Library Review 2026-09-25 / Prompting 2026-10-05 authority. Read the full issue, current traceability, prior C7 certification review and Bloodied/linked-condition classification. The C5/C7 accepted identities and minimal Bloodied/linked-condition classification remain intact.

## P1 — creature preflight permits predictable refusals after rolling

**Class:** merge-blocking before-dice validation defect. **Disposition:** implementation work under AC3/AC5 and the already accepted sequencing contract.

`creature_attacks.prepare` (`creature_attacks.py:587–605`) checks damage and rider shape, but never validates applicability of each prospective condition immunity and never evaluates the source HP needed by conditional Bloodied damage. Those refusal-capable reads occur only in `_clause_effects` (`:711`), `_rider` (`:811,821`) and `_rider_damage_applies` (`:332–351`, called from `roll` at `:913`). A legitimate character-state document may record an immunity whose mechanical source this adapter does not execute; that must refuse before dice, just as the present runtime policy already requires.

The reviewer probe uses the real adjudication pass service with a legal active creature turn, accepted native authority, typed/validated state and deterministic dice. All four proposals pass `require_supported` and then fail inside `service.adjudicate` after these rolls:

| Accepted attack and input | Actual refusal | Dice already consumed |
| --- | --- | --- |
| Wolf Bite; target records Prone immunity | unsupported capability | `1d20`, `1d6` |
| Purple Worm Bite; target records Restrained immunity | unsupported capability | `1d20`, `3d8` |
| Allosaurus Claws with qualifying charge; target records Prone immunity | unsupported capability | `1d20`, `1d8` |
| Swarm of Rats Bites; source HP absent | missing state | `1d20` |

The production subject loader returns the creature's readiness information without rejecting it (`api/pipeline_wiring.py:293–320`), so missing source HP is not intercepted upstream. The source does not need HP for ordinary fixed damage, but the admitted swarm predicate does.

Expected: these exact selected operations refuse with the existing typed reasons and **zero dice**, irrespective of whether an attempted roll would hit or miss. The pass currently treats a refusal within its first operation as ordinary because it checks completed `records`, rather than whether that operation already rolled (`service.py:636–647`). No effects commit, but failed-turn retries can discard drawn dice. The primary correction is complete preflight, not widening that catch or claiming rollback closes AC3.

**Bounded sibling result:** direct rider, linked rider and clause condition paths all reproduce the same family. `creature_effects.py:541` also defers condition-immunity evaluation to after save/damage dice; static inspection shows the same missing preflight read, but that sibling was not separately run. Include it in the same narrow correction. Size/predicate applicability must remain respected; do not reject a condition that cannot apply. Bloodied arithmetic and subject identity themselves are correct; validate needed state early and retain evaluation from the operation's actual advanced state.

## P1 — newly admitted creature entries remain unexecutable while the roster test passes

**Class:** merge-blocking source-predicate/positive-coverage defect. **Disposition:** implementation work plus correcting the capability evidence under AC2/AC4/AC7.

`roster.EXECUTABLE` adds entries whose C5 blockers appear in `SETTLED` (`test_creature_roster.py:19–52`). The traceability declares those blockers executed and the admitted roster complete. However, the test named `test_every_admitted_shape_executes_and_every_other_entry_refuses` requires success only for the old C5 `executable_once_accepted` flag (`:227`); a newly admitted entry with `positive=False`, `admitted=True`, and any refusal satisfies every assertion (`:227–236`).

Running the test's existing `_results()` confirms all original C5-positive selections preflight successfully, **but these eight roster-admitted entries unconditionally refuse source semantics**:

| Entries | Accepted source qualification that runtime refuses |
| --- | --- |
| Elephant Trample; Mammoth Trample; Gorgon Trample | target has the stated condition (`creature_effects._fact`, `:321`) |
| Ghast Claw; Ghoul Claw | rider save excludes specified target types (`creature_attacks._check_rider`, `:433–437`) |
| Dragon Turtle Steam Breath | same-entry `clause_damage_qualification`, preserving the underwater Fire Resistance exception (`creature_effects._fact`, `:298–307`) |
| Sphinx of Lore Mind-Rending Roar; Sphinx of Valor Third Roar | typed target types/exclusions (`creature_effects._fact`, `:320`) |

These are unconditional shape refusals, not a lack of suitable test inputs. The accepted source already carries the predicates. Their admission cannot be proven by calling the earlier timing/area blocker settled while leaving other typed source restrictions unexecuted. The manifest's stale “not yet” wording does not reconcile its roster or the architecture's completion claim.

**Smallest sufficient correction:** implement the admitted source predicates/qualification in their existing operation path using the exact target state and binding, maintaining typed refusal for missing or unvalidated inputs. Test the complete admitted roster, not just original positives; supply each scenario's real required state (usage counters, target condition/relation), and check successful resolution/effects rather than only preparation. Do not silently remove these ordinary bounded shapes to make a green coverage assertion. Retain genuinely excluded spell/general-engine compositions and their named refusals.

**Inventory limits:** the raw `_results` helper marks all Multiattack rows `admitted=True`, even excluded selections, and initializes limited-use creatures without usage counters. Consequently the larger raw refusal inventory is **not** a defect count. The eight entries above exclude those artifacts and are independently identifiable by membership in `roster.EXECUTABLE` and unconditional source-shape guards.

## Reused and unaffected verification

- Every original C5-positive attack/save entry and selected Multiattack passes the existing inventory's adapter preflight at this head. This is preparation evidence, not full positive end-to-end coverage.
- `defense.template` now checks each subject's own template; overrides are refused by `certify_template`, and audited template digests accompany execution. The earlier omitted-template certification finding is addressed in the inspected path.
- Bloodied compares typed current HP against half the reduced maximum, excluding temporary HP. Berserker attack/save consumers and swarm damage consumers are present. The new defect is the missing-state preflight seam, not a new source-acceptance gate.
- Linked Grappled/Restrained creation ties the dependent to the same hit's Grappled instance. Model validation checks the same subject's Grappled referent, and `clear_condition` removes only dependents of removed instances. Existing focused tests cover both creatures, separate grapples, unrelated restraint, immunity, serialization and malformed links. No new defect was found in those inspected persistence rules.
- No speculative stale rider-save finding is raised: current rider-save entries already refuse on target exclusions, so that concern is unreachable in the reviewed implementation.

## Bounded handoff

Continue CRD Issue 15c's accepted creature scope. Close the before-dice family across direct/linked/clause conditions and conditional damage, including the save-effect sibling. Preserve per-subject binding/revision and delivered-turn atomicity; a missing or unsupported input must be detected before any die on both hit and miss paths. Complete the eight admitted typed source shapes above and repair the roster assertion so every claimed admission needs a valid positive execution scenario. Demonstrate the corrected behavior through the adjudication/public turn path with accepted source in disposable stores, plus the focused wrong-target/missing-state/immunity regressions. Reuse unaffected C5/C7 and template/linkage evidence; no new source candidate or Owner policy is required. Keep merge and shared-runtime publication/activation held.

Evidence: `owncreature-review/review_probes.py` and `owncreature-review/review-probes.json`. The probe ran under this checkout's `venv/Scripts/python.exe` and confirmed its `afterworlds.__file__`. Its five-case pass used the real service; the Ghast service diagnostic stops earlier on the deliberately absent aura reader, so that case establishes the independent adapter shape refusal only. No full suite or new acceptance gates were run. Engineer E2E edits were present but uncommitted and outside this review's immutable implementation head.
