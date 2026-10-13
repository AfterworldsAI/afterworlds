# CRD Issue 15c — creature correction review

**Verdict: bounded correction still required at `41f892cc9d1e2ce235fc4334b4b63a3fd2d71650`.** The original direct/linked/clause immunity and source-HP preflight failures are closed. All six repaired entries resolve individually, but speculative Trample sequencing still violates AC3, and the Sphinx enemy qualification is missing from the model-facing selection contract. Ghast/Ghoul remain promised but held for the independently reviewed and exactly accepted C8 prerequisite; they are not positive coverage. No full merge clearance is claimed.

Applied installed Afterworlds Review/task routing and reused this task's verified Library Review 2026-09-25 / Prompting 2026-10-05. Read the complete governing issue, original execution review, Bloodied/linkage classification, adopted type-boundary classification and C8 preparation request. Reused C7 semantic/native/recording proof. The actual source-shape implementation commit is `ed18d22`; `3accd1b` updates its documentation. Raw diffs before and after probes confirm source/tests/config unchanged from the pinned head; HEAD remained pinned.

## P1 — speculative Prone is treated as an established Trample prerequisite

**Class:** merge-blocking before-dice validation defect. **Disposition:** ordinary implementation correction; no new Owner Decision or C8 dependency.

`service.py:581–585,617–629` projects every condition an earlier operation *might* impose into later preflight. `turn.py:194–221` creates synthetic `possible:<condition>` instances. The new positive predicate in `creature_effects.py:477–484` accepts that synthetic Prone as proof of Trample eligibility. This invalidates the service's assumption that adding conditions can only increase refusal paths.

Through the real adjudication service, each of Elephant, Mammoth and Gorgon can propose a legal Gore Action followed by Trample Bonus Action against an initially standing target. All three pass preflight; a natural-1 Gore miss consumes `1d20`, then Trample raises `PreflightGapError` because its actual target is not Prone. With a hit and qualifying charge, the same compositions resolve. The counter at `service.py:667–678` detects the defect but does not prevent the forbidden draw.

Smallest correction: an unconditional later operation must validate its positive prerequisites independently of speculative prior outcomes. Refuse an independently proposed Trample relying on a yet-unrolled Gore before any die, while preserving valid initially-Prone targets. Use conditional outcome handling only where an already admitted bounded composition actually owns it; do not add general conditional planning, a pending sequence, or CRD Issue 15b/19b machinery. Do not catch and discard the miss after dice.

**Bounded sibling audit:** repeated before-dice family triggered this review. All three Trample entries reproduce it. Glabrezu Pummel's `related_to_source` check (`creature_effects.py:444–459`) rejects a synthetic Grappled without the required source referent; direct preparation confirmed this sibling safe. Existing creature follow-up attacks already have explicit conditional skip handling (`service.py:643–654`); no broad redesign requested. Initially-Prone Elephant and Gorgon Gore-miss/Trample compositions complete; standalone initially-Prone Mammoth Trample completes. The supplemental Mammoth composition omitted its required within-5-feet fact and is not counted as positive proof.

## P2 — Sphinx enemy restriction is discarded by the selection contract

**Class:** merge-blocking source-selection/prompt-contract inconsistency under AC3/4. **Disposition:** ordinary implementation and prompt correction within approved bounded relationship inputs.

The accepted source requires **each enemy**, for Mind-Rending Roar and Third Roar (`monsters-A-Z.md:16058,16160`). `creature_effects.py:332–337` merely exempts `TargetTag.ENEMY` from refusal; no subsequent check consumes that qualification. Meanwhile `caller.py:326–329` requests “every creature in its area”; `rpg_adjudication.md:65–67,122–125` repeats that unrestricted request. `scene.py:57–60` supplies save-effect entry names only. `CreatureSaveEffectSelection` has source, entry, targets and aura membership (`models/rpg.py:181–192`), with no separately declared enemy cohort. A model following the actual supplied contract can therefore include allies/neutral creatures and damage or disable them. Correct damage on the selected targets does not prove the enemy restriction.

Expose the exact source qualification in the code-generated options and model-facing contract, carry an auditable operation/source-bound enemy selection, and validate subject/source/relationship consistency before dice. Reuse the bounded named hostile/ally input model (`bystanders.py:4–8,22–24`) and approved spatial-input safeguards; do not infer every selected area member is an enemy. No general allegiance/faction engine or new GM taxonomy authority is required. Add a meaningful non-enemy/missing-or-conflicting-selection control; the present wrong-self tests cannot establish enemy filtering.

## Verified closures and positive effects

- Wolf direct Prone, Purple Worm linked Restrained, Allosaurus charged-clause Prone and Lion Roar Frightened recorded-immunity refusals occur with zero dice. Attack probes use both would-hit and would-miss dice. Nonqualifying Allosaurus charge and a too-large Wolf target correctly avoid an inapplicable immunity read and resolve.
- Missing Swarm source HP and Blood Hawk target HP refuse with zero dice. Blood Hawk reads the target independently: above half uses `1d4`, at half uses `1d8`, temporary HP does not alter the branch. A legal sequence of two attacks separated by explicit actor edges crosses half HP and changes the next damage die from `1d4` to `1d8` using advanced state.
- Elephant/Mammoth/Gorgon Trample each applies correct failed-save damage and rounded half on success to an already-Prone target. Standing, missing-condition and source-as-target controls refuse before dice.
- Dragon Turtle Steam Breath applies full/half Fire damage and spends Recharge. Its underwater exception adds no resistance; native Fire Resistance on another Dragon Turtle still halves damage. No new underwater resistance mechanism was introduced.
- Both Sphinx entries resolve numerical/effect branches: Lore imposes Incapacitated until the source's next turn start on failure and no damage/condition on success; Valor imposes Prone/full damage on failure and half damage/no condition on success. Lore spends Recharge. This proves effects only, not the missing enemy-selection contract above.
- The roster test now resolves all admitted attack/save entries except the explicit Ghast/Ghoul holds. The original C5-positive checks and linked-condition regressions passed. No new source/template/linkage defect is reported.
- A static size-order concern in save-effect resolution (`creature_effects.py:580`) was sampled against the only represented size-gated save riders, Giant Ape Boulder Toss and Gladiator Shield Bash. Both are outside the executable roster and refuse before dice. This is **out of current admission scope**, not a claimed reachable defect; do not broaden remediation to admit them.

## Evidence and limits

Selected interpreter: this checkout's `venv/Scripts/python.exe -X utf8 -B`; `afterworlds.__file__` verified as this checkout's `src/afterworlds/__init__.py`.

Actual focused pytest command: `rtk proxy venv\Scripts\python.exe -X utf8 -B -m pytest tests/pipeline/rpg/test_before_dice.py tests/pipeline/rpg/test_creature_roster.py tests/pipeline/rpg/test_bloodied.py tests/pipeline/rpg/test_linked_conditions.py tests/pipeline/rpg/test_creature_effects.py -q -p no:cacheprovider`. **54 passed, 22 serializer warnings, 129.64 seconds; process exit 1 because the repository-wide coverage floor is 80% and this narrow selection produced 44.53%.** This is diagnostic assertion evidence, not a green repository gate. Default coverage ran accidentally; no rerun merely to change exit status and no gate weakened.

New evidence under `owncreature-review/`: `correction_probes.py`, `correction-probes.json`, `correction-probes.log` (45 real-service cases); `supplemental_probes.py`, its JSON/log (8 service cases and one direct preparation sibling); `verify_saved_results.py` and `saved-evidence-verification.txt` (successful assertions over saved damage, conditions, provenance, timing, refusals and dice). Initial reviewer harness field/serialization errors were corrected; the final saved evidence has no unexpected exceptions. Original `review_probes.py` and `review-probes.json` were preserved. Tests/probes do not exercise delivered-turn database commit; prior unaffected delivery proof is reused. No source, Git, shared-store, authority, network or Claude writes; no full suite or native replay repeated.

SHA-256 pins:

| Input | SHA-256 |
|---|---|
| Governing issue draft | `8ad877861b821aa927c38a39227ea58ea150ff8fdb4d7b2a161044d45727426f` |
| Accepted C7 oracle file | `2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373` |
| C5 capability roster | `6037ea70246c24e478d97c5f7938f3d695802bf6b19284c0c883864af9e3efe6` |
| animals.md | `c42082103eb868c5b8b2f6c0cbdcc8146545c149cfc7af32524f9938eed658f9` |
| monsters-A-Z.md | `e6581e2a330cd900dacbc321d9cb9533362f3b81e3f4adef342baf1b1a4864c2` |
| creature_attacks.py | `b107429692df19323328b6e6886fa2b97680c516fb9e0152b2b75d4469ecad1d` |
| creature_effects.py | `773f4ce3248c37150a8bd89bceec2c42fde9a12cab5a093319b64bfbc985c895` |
| service.py | `19410903645809b6f1f900997b7586a2f1c36ece1c34bb2669acc93ef5d3da82` |

## Claude-ready bounded correction

Continue CRD Issue 15c under the full governing issue and this correction review. Preserve accepted C7 and the separate held C8 prerequisite. Correct optimistic condition projection so independent Trample proposals cannot use a speculative Gore outcome as established target state; initial-Prone positive controls must remain executable, and miss/false-prerequisite paths must refuse before every die unless an existing admitted composition owns conditional handling. Reconcile Sphinx source-bound enemy selection with the actual tool/prompt/options contract and auditable named relationship inputs; prove wrong/missing/conflicting targets do not execute. Reuse unaffected immunity, Bloodied, linkage, six-shape effect, delivery and native evidence. Update traceability to distinguish these corrections and the still-held Ghast/Ghoul admissions. No general allegiance or conditional-sequence engine, new type truth, scope exclusion, acceptance mutation, shared-runtime publication or merge. Run focused regressions for the changed seams; final stable-head gates remain due.
