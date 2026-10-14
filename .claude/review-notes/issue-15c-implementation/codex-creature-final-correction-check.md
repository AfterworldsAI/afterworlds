# CRD Issue 15c — final creature correction check

**Verdict: the original sequencing and enemy-selection findings are corrected; one P2 persisted-identity regression remains.** Reviewed immutable HEAD `f8be6caa8b6d3dc7e86c2d7c23b50718869ee2ba`, including `78e0efa8b2750544be1a5b004bd1fb3cc658572e`. HEAD remained unchanged and raw before/after diffs showed no source/test/prompt changes. C8 remains unaccepted, non-native and outside this check. No merge clearance.

Applied the existing Review/routing guidance and reused this task's verified Library authorities and prior governing-issue read. Only the coherent correction diff and its directly affected contracts were reviewed; original native, delivery, damage, Bloodied and linkage evidence was reused.

## P2 — a legitimate persisted condition ID is mistaken for speculative state

**Class:** merge-blocking positive-coverage/state-identity defect. **Disposition:** ordinary bounded implementation correction; no Owner Decision or new source authority.

`conditions.established()` removes every recorded condition whose ID starts with `possible:` (`src/afterworlds/pipeline/rpg/conditions.py:100–106`). The persisted `ConditionInstance.instance_id` contract only requires a nonempty string (`models/dnd5e_state.py:497`), and shared state validation reserves no such prefix (`services/dnd5e_state/validation.py:329–333`). A caller can therefore record a real Prone instance with that valid ID; it is incorrectly erased from the positive prerequisite even when there was no prior operation or projection.

The real-service probe constructs, serializes, deserializes and validates the same character state with three distinct IDs. `validate_character` returns no failures in every case:

| Actual recorded Prone instance | Standalone Elephant Trample |
|---|---|
| `review-real-prone` | Executes, damage and save dice |
| `possible:prone` | Invalid-selection refusal, zero dice |
| `possible:legitimate-imported-condition` | Same false refusal, zero dice |

This loses an already-valid prerequisite because of incidental ID text. Distinguish temporary projection provenance from persisted identity without discarding valid recorded instances. Do not silently reserve a formerly legal prefix or rewrite stored identities as a shortcut. Regression proof must preserve serialized/validated real prefix-named conditions while continuing to reject genuinely speculative prerequisites. This is a representation correction within the settled before-dice rule, not a request to revisit its semantics or introduce a new sequencer.

## Cleared behavior

- **Speculative prerequisites:** real-service Gore→Trample against initially standing targets refuses with zero dice for Elephant, Mammoth and Gorgon, under both configured miss and hit rolls. All six initially-Prone controls execute with the required range fact supplied, including a Gore miss followed by valid Trample. `established()` also removes implications of projected conditions, addressing the original projection defect for ordinary IDs.
- **Enemy cohort:** both Lore Mind-Rending Roar and Valor Third Roar now require a named cohort and exact equality with selected targets (`creature_effects.py:401–444,479`). Missing cohort, a selected non-enemy, an untargeted enemy, source-as-enemy, duplicate enemy and extra selected target all refuse before dice. A cohort on Lion Roar also refuses. A valid cohort preserves each effect's success/failure numerical and condition branches.
- **Source options and audit:** scene options expose typed `enemy_only_effects`; caller schema and prompt supply the new contract (`scene.py:53–63`, `caller.py:319,328–332`, `rpg_adjudication.md:125–130`). `adapter.py:486–495` includes cohorts in spatial dependencies. Successful cohorts equal targets, so every admitted member is loaded through the existing target path under its binding/revision. Provenance records source, target identities, certificate and outcomes; together with the source-bound enemy-only contract this reconstructs the accepted cohort. Unmatched extra enemies may refuse as missing state before set-equality validation because they are not loaded as targets; this does not permit an invalid execution.
- No source, damage, defense, service sequencing or persistent effect-application changes beyond the inspected seams were found. Ghast/Ghoul holds and all prior numeric/native evidence remain unaffected.

## Verification and pins

New evidence: `owncreature-review/final_correction_probes.py`, `final-correction-probes.json`, `final-correction-probes.log`. **32 real-service cases; assertions passed; exit 0.** This includes deliberate assertions confirming the prefix-ID defect, not an assertion of readiness. The selected checkout's `venv/Scripts/python.exe -X utf8 -B` and `afterworlds.__file__` were verified. No database commit/store test, full suite, native replay or C8 review was repeated. No source, Git, authority, network or Claude writes; only this report and new review evidence were written.

Engineer test claims were checked against `.claude/review-notes/issue-15c-preparation/c8-type-preparation-run/stream.jsonl`:

- Line 683: **13 passed, 7 warnings**, from `test_before_dice.py` plus `test_creature_roster.py`; these are **not 13 enemy-specific tests**.
- Lines 686/692: RPG tests split into two focused invocations, **275 passed** and **158 passed**, both recorded `EXIT 0` (433 total). `scripts/run_focused_tests.py` runs pytest with `--no-cov` and explicitly labels its output diagnostic, not acceptance/full-gate evidence. This review did not rerun those suites.

SHA-256:

| Input | Digest |
|---|---|
| `conditions.py` | `87ff24b6158e4429b42be86d057dbfe7e3c7fe30df044461c6da1a94edcd5cfc` |
| `creature_effects.py` | `4b5c1c430cf9fb2733ce77a2c7b0ba050b886ba1de9c2a76e1d1dd05875ae8cb` |
| C7 oracle file, unchanged | `2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373` |

The JSON evidence additionally pins adapter, scene, caller, model and prompt bytes. Original reviewer scripts/results were preserved.

## Claude-ready correction

Preserve the settled zero-dice treatment of speculative Gore→Trample and the cleared enemy-cohort implementation. Correct `conditions.established()` so actual persisted conditions retain their meaning regardless of valid instance-ID text; temporary projection provenance must be distinguishable without treating every `possible:` ID as temporary. Show serialized, state-validated real-prefix Prone positive controls and zero-dice speculative controls. Do not change accepted IDs, candidate authority, C8 holds, allegiance policy, sequencing scope or gates. Reuse unaffected proof; no merge or shared-runtime publication.
