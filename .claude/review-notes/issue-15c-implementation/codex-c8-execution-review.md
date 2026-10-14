# CRD Issue 15c C8 execution review — bounded corrections needed

Reviewed immutable `555be9aed30e48bd05a469c73092177bb676e400` on `codex/issue-15c-bounded-d20`. Three settled implementation defects remain. This is a complete bounded target/species-family review, not another Owner acceptance milestone or a whole-PR verdict. The parent integrates the findings with the independent tool/coverage work before final stable-head gates and CI.

## Authority and reproducibility

- Read the complete governing preparation/issue-draft.md, SHA-256 `8ad877861b821aa927c38a39227ea58ea150ff8fdb4d7b2a161044d45727426f`; accepted C8 packet/Owner acceptance; whole-PR workflow correction; Elf/type-domain classification; target-domain planning addendum; source and affected implementation/tests. Applied installed Review 2026-09-25 and routing, reusing the parent-verified current Library Review 2026-09-25 / Prompting 2026-10-05.
- `c8-execution-review/probe.py` loads **all imported project/test Python** from Git blobs at `555be9a`, including changing models, state services, authority and test builders. The result manifests record 139 module hashes. No mutable project Python imports support the reproductions. The real accepted C8 oracle is hash-guarded before and after each run: `ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d`.
- The controls use the existing offline accepted-authority builder and real adjudication service with scripted GameMaster output/dice. No database, source census, native build, recording, broad suite, E2E publication setup, Git/network/Claude mutation or runtime change was performed. Only this note and its assigned review directory were written.
- Actual control-process exits were 0. `results.json` SHA-256 `fb5f4aff1bae71b55102418f9f4e48b943e339e64586b0e6d1d58a35314e12ce`; `source-qualified-results.json` SHA-256 `dba46419e2348cfd3aefddbd930d4851947bc13a0ee253b16c21077f24867bb9`; `visibility-results.json` SHA-256 `caa120ebf9170932cb5af4edd0b95f25d91e6a6c862494d1fd092fc0b4a50439`. Exit 0 means the diagnostic ran successfully; its reported accepted/error behaviors are the evidence, not a passing product gate.

## P1 — repeated species selections are rejected after earlier dice

**MERGE-BLOCKING DEFECT / implementation work.** `creature_types.py:348-399` correctly forbids overwriting a current selection, but `service.py:586-628` validates every proposal against the original species state and only projects possible conditions. Two `creature_species` proposals for the same initially unrecorded Bandit both pass. At `service.py:659-679`, execution records the first, advances state (`:715`), then the second raises `PreflightGapError`.

Independent controls prove both identical duplicates and conflicting Elf/Dwarf choices fail this way. With a valid Wolf Bite before the selections, the service consumes `1d20` and `1d6` before refusing. The same duplicate without the attack still produces the internal preflight-gap error, although it consumed no dice. A single selection succeeds with zero dice.

The first broken contract is AC3: all deterministic invalid selections must refuse before any die. Rollback can discard state but cannot undo the dice or remove retry/reroll bias. Account for this deterministic one-record-per-subject change during whole-turn preflight; retain the runtime and delivery defenses. Prove zero-dice refusal for same/conflicting duplicates, including after an otherwise valid rolled operation, while independent subjects remain admissible.

**Bounded recurrence check:** this is the recurring before-dice family. Sampled the newly introduced selection's original-state preparation, sequential advancement, `effects._creature_species` overwrite guard, same-turn species-plus-Ghoul control, current/stale selection handling and subject-addressed delivery/CAS. Single selections and existing/current-selection refusals are already covered; species-before-Ghoul is already refused before dice. Duplicate same-subject deterministic effects are the missing member. Previous lifecycle/Trample/speculative-condition dispositions are reused; no reopening of those mechanisms or broad sibling audit is needed.

## P1 — accepted Familiar type proof is mistaken for ordinary execution eligibility

**MERGE-BLOCKING DEFECT / implementation work.** C8 correctly derives the Familiar's Celestial/Fey/Fiend type, but the connected attack/damage paths ignore the source's independent restrictions. `creature_types.py:171-211` settles type only; `creature_attacks.py:520-658` and `damage.py:193,265-398` admit ordinary combat consequences without checking the Familiar's recorded presence or source-specific zero-HP consequence. The ordinary attacker path also ignores its source prohibition.

The source is explicit at `docs/sources/community/dnd-5e-srd-markdown/spells.md:2296-2298`: a Familiar cannot attack; a Familiar that reaches zero HP disappears, with its carried/worn items left behind; it can be dismissed to a pocket dimension. The accepted C8 packet expressly grants no Familiar attack or lifecycle engine.

Independent service controls, all with exact accepted Find Familiar source and Fey Cat identity, demonstrate:

| Case | Actual behavior at 555be9a |
| --- | --- |
| Present Familiar, with both `validate_creature == ()` and `creature_readiness == ()`, uses Cat Scratch | Rolls `1d20`, succeeds and stages target HP 40→39 |
| Ghoul targets Familiar whose presence is unrecorded | Rolls attack/damage/save and stages HP 40→37 |
| Ghoul targets Familiar explicitly dismissed to `pocket_dimension` | Same accepted attack/damage/save and HP mutation |
| Ghoul hits present Familiar at 1 HP | Stages HP 0 and `death_state.dead=true`; no disappearance/presence or belongings consequence |

This is one source-qualification family, not four requests for a new engine. Preserve the valid type deduction while enforcing the source's independent applicability/eligibility/consequence holds **before dice**. A type proof must not supply an attack grant, make an absent subject physically targetable, or certify the ordinary monster-death path. Implement only already authorized bounded behavior; otherwise retain a truthful specific unsupported hold rather than silently using ordinary behavior. Do not count that refusal as positive Familiar-lifecycle coverage, and do not expand this correction into general summoning, casting, form changes, allegiance or lifecycle execution. The attack prohibition and known absence are settled source facts, not new Owner Decisions.

The general attacker/damage paths predate this C8 commit; this is a defect present in the whole CRD Issue 15c implementation and exposed by the requested source-qualified family review, not a claim that C8 newly authored every bypass. C8's new Ghoul type path now positively admits these Familiar targets while the independent source restrictions remain unenforced.

**Bounded sibling check:** examined both Familiar actor and target roles, known/unknown presence and the zero-HP branch because they share this exact source boundary. Wild Companion/Pact type refusal and Otherworldly Steed's independent parameterized-AC hold remain separate and are not waived. Other conditional creature families were not reopened.

## P2 — a refusal reveals a previously hidden species selection

**MERGE-BLOCKING DEFECT / implementation work.** `creature_types.py:393-398` includes the *held* species in the current-selection refusal. That detail is public: `orchestrator/service.py:1396` places the exception into `pipeline_error_summary`, `_pipeline_error` preserves it (`:3929-3953`), and `api/routes/turns.py:243` returns it.

The independent control records an Elf with `visibility=hidden`, applies the effect and confirms the normal Writer view contains no Elf identity. A later proposal to record Dwarf then refuses with `already records species character_origins.elf`. Thus the new identity escapes through the failure path despite the successful hidden Writer filter. Keep the explanatory public refusal, but omit the held secret identity; retain exact identity in backend audit where appropriate. Cover a hidden stored selection followed by an invalid repeat. No expensive new disposable-store setup is necessary to prove the string boundary; existing API refusal plumbing is inspected and tested.

## Reusable safe behavior and evidence

- `_ordinary` explicitly rejects `active_effects=None`, assumed forms, and unexecuted effects. It does not treat missing form/type fields or the looser `other_effects` helper as sufficient proof. The certified base type plus recorded effects state establishes the admitted ordinary domain. The Ghoul's non-Humanoid⇒non-Elf deduction is the accepted deduction, not guessed negative taxonomy.
- Character species remain exact typed identities. Contradictory character type, missing/stale creature identity and invalid species options refuse. The accepted current catalogue offers exactly the nine Humanoid species; the eligible fixed-Humanoid creature templates were enumerated in `results.json` and are the source's role/profession population. Template reads go through `certify_template`, and attack certification checks both subjects' bindings. Species selection grants no traits or type changes.
- Independently checked all eleven accepted named Familiar forms against all three allowed type choices: **33 correct type results**. Beast default, unnamed forms, unrepresented familiar sources, missing/conflicting effects and stale identity have targeted existing negative tests. These are type checks, not Familiar execution/lifecycle clearance.
- `test_creature_types.py` supplies meaningful positive Ghast/Ghoul differences, ordinary Beast rider, Elf/non-Elf character and selected Humanoid behavior, Undead damage without save, invalid-domain refusals and species recording. `creature_attacks` decides exclusions before preparation of the spared save; hit damage remains.
- `record_species` emits a subject-addressed typed effect and backend provenance/certificate. Runtime advancement and delivery use the same effect function. The inherited delivery path rechecks every read subject's revision/binding/holdings before audit, applies grouped effects by CAS, and commits them with the delivered Turn. The new application tests prove later-turn consumption and stale-revision rollback. The scene is GameMaster-only; normal shown/hidden Writer labels do not expose species, and the public visible-state builder does not serialize creature documents. The refusal finding above is the remaining new visibility leak.
- Existing C8 native/source/recording/selection/baseline clearances are reused. No new acceptance request or reinterpretation of those artifacts is made.

## Actual engineer result and limits

Inspected the saved `rpg-suites-2.result.json` and terminal output: actual exit 1, **654 passed / 1 failed**, 392.84 s, completed 2026-10-13T18:57:18.5646409Z. The sole failure was the stale-species E2E assertion that raw JSON did not contain the key despite `species:null`. Commit 555be9a changes it to parsed null checking.

The public Claude **tool-result**, not a narrative claim, records the affected-case rerun: **1 passed**, 5 warnings, 347.97 s, `Focused diagnostics PASSED (exit 0)`. Captured in `c8-execution-review/engineer-corrected-case-result.json`, tool use `toolu_01MBraMoYejiWedQVsXc2HAX`, `is_error=false`. The earlier 31-test target-unit diagnostic is also present in the public stream. These focused results and the three other passing E2E cases are reusable evidence, not a full-suite/coverage/CI verdict.

The workspace remains on HEAD 555be9a while the independent engineer changes tool-related models, services, caller/prompt, certification and tests. Those current files differ from the reviewed revision. Frozen import/result manifests define this review's boundary; the later integrated commit needs affected regression checks and final whole-PR review. Full configured-coverage suite, unchanged repository gates and exact-head CI remain due. No merge/runtime authority is implied.

## Consolidated Claude-ready correction

You are completing CRD Issue 15c on the existing branch under the accepted C8/species decision and the Owner's one-complete-PR workflow. Fix the three execution defects reproduced at 555be9a in `codex-c8-execution-review.md`; use its frozen-source evidence rather than repeating native/store/broad diagnostics.

1. Detect repeated same-subject species selections during whole-turn preflight, including identical repeats, so no preceding valid operation can consume dice before their rejection. Preserve independent-subject selections, current-selection protection and delivery CAS.
2. Keep C8 type proof separate from source-qualified Familiar execution. Enforce the settled attack prohibition and known/unknown presence boundary; refuse any unsupported source-specific consequence before dice instead of applying ordinary monster death. Preserve valid type deductions and existing independent holds. This does not authorize general Familiar casting, form, disappearance, item-transfer or lifecycle execution, and a specific hold is not positive coverage.
3. Make current-selection errors informative without exposing the held species identity when that identity was hidden. Preserve backend provenance and normal hidden/shown filtering.

Add the smallest meaningful regression controls for the reproduced family, update only affected capability/traceability claims and run changed-path diagnostics. Continue the independent whole-PR tool/coverage work. No new Owner slice gate, candidate regeneration, gate weakening, merge, runtime publication/migration/activation or app launch.

## Bounded sibling addendum — shared damage and direct zero-HP operations

At the parent's request, extended only the already-reproduced Familiar source-consequence family at frozen **555be9a**, before its consolidated correction. `probe.py siblings` reuses the Git-blob importer and hash-guarded oracle; actual process exit **0**, five service controls in `c8-execution-review/sibling-results.json`. It does not repeat the actor/type/33-form controls, native/store/E2E setup or any suite. All constructed Familiar snapshots pass both state validation and readiness; those checks intentionally do not establish execution legality.

Result SHA-256: `fc2f3a2f6b80d808775f46317c39169bd78142a252113fa5a272c1f04134f96c`.

| Additional reachable member | Actual result |
| --- | --- |
| Present Familiar at 1 HP, struck by a held Club | Attack/damage dice, HP 0 and ordinary `dead=true` |
| Present Familiar at 1 HP, targeted by direct Acid Breath save | Damage/save dice, source usage spent, HP 0 and ordinary `dead=true` |
| Familiar recorded `presence=gone`, HP 0, explicit monster-to-character treatment exception, first aid | Medicine/recovery dice; writes Stable and a recovery interval |
| Same gone Familiar, explicit actor-turn begin and death-save natural 20 | Death-save die; restores HP 1 and clears dying/Unconscious state |
| Gone Familiar with recorded Stable recovery instance, elapsed-time attestation | No die; restores HP 1 and clears the recovery/Unconscious state |

The shared repair boundary is now concrete. Weapon damage (`attacks.py:1239,1419`, including Graze at `:914`), creature damage and direct-save damage (`creature_effects.py:529,622`) converge on **`damage.preflight` / `take_damage`**. A guard only in `creature_types` or Ghoul preparation cannot cover them. The independent **`lifecycle.dying/prepare`**, **`prepare_first_aid`** and **`attest`** paths (`lifecycle.py:103,181,420,524`; actor-turn call sites `adapter.py:333-335,794-795`) also need the same source/presence eligibility enforced before dice or effects. `_named` at `lifecycle.py:391` currently resolves identity without that eligibility.

**Disposition: same P1 fail-closed implementation family, not five new policies.** Recorded generic character-style treatment/counters cannot waive Find Familiar's source-specific disappearance rule or make a gone subject available to first aid. Existing ordinary-monster/character lifecycle must keep working. Source-qualified unavailable, contradictory or unexecuted Familiar lifecycle paths remain explicit holds; this authorizes no general Familiar disappearance, reappearance, casting, belongings-transfer or lifecycle engine, and holds are not positive coverage. No blanket conclusion about a present Familiar's otherwise valid 1-HP knockout state is drawn from these zero-HP/absence controls. The shared sites and reachable path set are established; stop this sibling search and correct the family coherently.
