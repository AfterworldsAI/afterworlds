# CRD Issue 15c — persisted/projection correction check

**Verdict: the remaining P2 persisted-identity regression is closed at `e5d9a684c33d232fd468c9eea705d2b184ecfba8`. No further finding in this bounded correction.** This clears the ordinary creature corrections reviewed here; it does not clear the separate unaccepted C8 prerequisite or final repository/merge gates.

Reviewed only `e5d9a68` versus `f8be6ca`: `services/dnd5e_state/turn.py`, `pipeline/rpg/conditions.py` and affected tests. Reused the governing issue, current-task Library/Review authority and prior numerical, cohort, native and delivery evidence. HEAD stayed at the pinned commit; raw source/test diffs before and after probes were empty.

## Why the fix closes the defect

`TurnCharacter` and `TurnCreature` now carry an ephemeral `speculative` set, defaulting empty (`turn.py:88,113`). `with_possible` assigns fresh instance IDs and records only instances it actually added, on the corresponding subject (`:203–243`). It does not mark an already-present condition merely because its kind appears in a projection request. The condition ID's spelling no longer establishes provenance.

`conditions.established()` removes only explicitly marked projected instances, then derives implications from the retained real conditions (`conditions.py:85–102`). Thus real prefix-named Prone survives; a real prefix-named Unconscious still implies Prone/Incapacitated; projected Unconscious cannot manufacture an established Prone prerequisite.

Lifecycle inspection and checks confirm that `with_effects` preserves the marker set through immutable subject replacement (`turn.py:159–171`), repeated projection unions the correct subject's markers, and original subjects remain untouched. Normal loaders default to empty provenance (`:269,278`). The service uses projected copies only for preflight (`service.py:617–629`) and resolves from the original subject snapshots (`:637`); no speculative state/provenance is persisted or substituted for the delivery snapshots. No source/schema/ownership change is introduced.

## Verification actually run

`owncreature-review/persisted_projection_probes.py`, using this checkout's `venv/Scripts/python.exe -X utf8 -B`, verified its `afterworlds.__file__`. **Exit 0; nine real-service cases plus provenance-lifecycle assertions passed.** Results and log are preserved as `persisted-projection-probes.json` and `persisted-projection-probes.log`.

- Three JSON-round-tripped, shared-state-validated character conditions (`review-real-prone`, `possible:prone`, `possible:legitimate-imported-condition`) all allow standalone Trample and retain their original IDs.
- A similarly validated creature target with real `possible:prone` also executes.
- Real `possible:unconscious` preserves its implied Prone and allows Trample.
- Elephant, Mammoth and Gorgon speculative Gore→Trample each refuse before any die.
- A prior Goblin attack's possible Unconscious, across explicit actor edges, does not establish Prone for a later Trample: zero dice.
- Independent character/creature projection sets, original-state preservation, retained real Prone, exclusion of speculative implications, advancement and repeated projection all passed direct assertions.

Prior 32-case cohort/correction and earlier creature effect proofs were reused, not rerun. No pytest suite, numeric/cohort/native replay, database/store operation, C8 review, network access, source edit or Git mutation was performed. Only this new report and bounded review outputs were written. The fixture emits the previously observed size-enum serializer warning; this did not fail the assertions.

## SHA-256 pins

| File | SHA-256 |
|---|---|
| `services/dnd5e_state/turn.py` | `62c07289af79017a40646df27ffb3da6e62b4aa2a89c846166d573ab53fd71f9` |
| `pipeline/rpg/conditions.py` | `d4103afca88b65195a7dda12bc61ee6ae8e1247fa56575052b4e43619b8bbd03` |
| `tests/pipeline/rpg/test_before_dice.py` | `e25a0cb4b42eeb06fbfe821ee168e46f64416f9b5ff4badcf77c44050f866ef2` |
| Accepted C7 oracle file, unchanged | `2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373` |

No additional remediation prompt is needed for this closed finding. Preserve the separate C8 review/acceptance hold and final stable-head verification boundaries.
