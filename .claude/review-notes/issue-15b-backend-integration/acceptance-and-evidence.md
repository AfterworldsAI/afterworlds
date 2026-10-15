# CRD Issue 15b Phase 2 backend: acceptance and evidence map

**Candidate:** branch `codex/issue-15b-backend-integration` (local, unpublished), based on main `f6f39721`.
**Governing authority:** #127, ADR-015b including Group 17 (15b-37), and Owner Decision 15b-36.
**Frozen:** #129 stays at `d8233a43`. Its shapes were reused; its numeric-label authority was not.

Raw evidence (stdout, stderr and `meta.json` per labelled run, failures included) is in
`D:\AI\Claude\scratch\AW docs\issue15b-resumption\phase2-backend-evidence\` and indexed in its `INDEX.md`.
Earlier runs are historical checkpoints on their own recorded heads. They are not final-head proof.
Exact-head full CI is the whole-candidate gate once Codex publishes the PR.

## What was built

- **Sequence engine** (`pipeline/rpg/sequence.py`, `steps.py`, `ids.py`).
  - One unresolved action-resolution sequence per story, persisted with its plan, its reads and one
    pending interaction.
  - Completed operations are folded from their records. Only the in-flight operation is replayed.
  - A regenerated snapshot must equal the stored one.
  - Identities are deterministic per sequence operation.
  - `PlayerInputRequired` pauses the turn for a player die or decision.
- **Described dice** (`pipeline/rpg/dice.py`).
  - Every adapter die is a `RollRequest`: purpose, roller, modifiers, target, naturals and options.
  - The term engine covers sum, keep-highest and keep-lowest of N, several terms, repeated dice and
    subtracted terms. Kept and omitted dice stay reconstructable.
  - `chosen_die_range` is retired.
- **Event ledger.**
  - Roll events are `player_roll`, `ai_roll` and `hidden_roll`. There are also `adjustment` and
    `mechanical_decision` events.
  - Events are append-only (triggers) and kind-safe. Each event's envelope agrees with its payload's
    snapshot.
  - Channel and shape combinations are enforced on construction and on reconstruction.
  - The final `rpg_roll_audit` comes from roll events alone.
- **Accepting transaction** (`ActionResolutionService._advance`). In order:
  1. A dice-free preparation outside the write.
  2. In one write transaction: the revision claim; for a roll, the conditional consume; the recheck of
     every prepared read; only then any new backend die; then events and advancement together.
- **Positive mechanics.**
  - Finesse Strength/Dexterity is a pre-roll adjustment: revision plus 1, an `ADJUSTMENT` event, and the
    same ability used for damage.
  - The knockout is a stored yes/no decision, with snapshot-only membership validation followed by a
    state-guarded continuation.
  - Contests (Group 17) run with S1 in memory only. A contest with no player input completes its
    ledger inside its originating Turn.
  - A Stable recovery interval is a `DURATION` step.
  - A creature Recharge die has `RollPurpose.RECHARGE`.
- **Orchestration.**
  - A sequence-aware in-character gate, the OOC pending-interaction state and announce-turn starts.
  - `orchestrate_rpg_resume`: ready-only, typed refusals before any provider call, the shared delivery
    core, the code-owned continuation frame and the refusal-buffer hooks.
  - `action_sequence_error` codes, including `ACTION_SEQUENCE_ALREADY_COMPLETED`.
- **Migration 0043.**
  - One head after 0042.
  - The 15b-36 empty-table guard runs first. Then 8 legacy columns are dropped and 6 structured ones
    added by direct `ALTER`.
  - New tables: sequences (with a partial unique index) and events (with triggers).
  - New audit columns, including `contest_resolution_json`.
  - Downgrade refuses before any DDL while lifecycle data exists.
- **Legacy retirement.** Removed:
  - `pipeline/rpg/pending.py`;
  - the adapter's announce and consume paths and the label assembler;
  - the orchestrator's reported-total intercept and its precedence over OOC;
  - `chosen_die_range`;
  - `rpg_pending_roll_service`.
- **Phase 3 held.** `create_app()` and `api/pipeline_wiring.py` are unchanged. The construction delta is
  kept as scratch: `phase2-graphify/phase3-handoff/pipeline_wiring-sequence-construction.diff`.

## Acceptance map (Codex review map surfaces)

| Surface | Proof |
| --- | --- |
| Sequence and adapter: linked attack and damage, the next attack, the contest opponent | `test_action_resolution_on_published_release` (spike); lifecycle `finesse`, `knockout`, `contest` tests; `test_multiattack_compositions::…in_a_sequence…` (ordered linked backend steps; replay draws nothing) |
| Positive AC8 contests | `tests/pipeline/rpg/test_contests.py` (30; includes the completed ledger of an all-backend contest and the unwired refusal): comparison, tie, printed creature total, Action cost, refusals, visibility in both roles, the nonparticipant fallback, whole-hidden. Lifecycle: player against a shown, hidden or unperceived counterpart, with reload, stale, duplicate, concurrent, rollback and tamper cases; `test_an_all_backend_contest_persists_both_participants_with_its_turn` (two `ai_roll` events, resolution on the completing one, sequence completed with the Turn, one audit row per participant, ordinary-narration marker); `test_a_failed_all_backend_contest_turn_leaves_no_ledger` (Writer error, output block: no sequence, event, audit row or Turn) |
| Finesse revision | lifecycle `test_a_finesse_adjustment_revises_the_pending_attack_and_its_damage`: stale, inexact (`True`, `1.0`) or not-offered requests refuse; the superseded instruction refuses; Dex is used for damage |
| Knockout decision and stored non-roll events (AC41–46) | lifecycle `test_a_knockout_choice…` (both options; the decision event's whole `decision_snapshot` equals the stored one, with its decision id, revision and string option, and is rebuilt from its row alone after the working copies are blanked and the wolf moved); finesse test (the adjustment event's resulting snapshot equals the stored revised instruction, string option, same row-only reconstruction); `test_action_resolution_models.py` (29; non-roll payload round trips, 7 cross-kind refusals, step agreement); `test_a_stored_decision_is_validated_by_snapshot_then_state_guarded`, `test_an_ai_rolled_hit_starts_a_decision_first_sequence`; `test_zero_hp_lifecycle::…never_takes_the_knockout…` |
| Dice selection and provenance (AC2–3) | `test_sequence_engine.py` (22). `test_the_executor_keeps_and_sums_its_whole_pool` runs `SystemRandomDiceService.roll` with only its RNG seam scripted: 4d6kh3, 4d6kl3, 3d20kh2, 5d8kl2, 10d6, 3d12, with the whole raw pool kept and `chosen` summing every kept die. Plus kh3/kl3 with ties, mixed, repeated and subtracted terms, the aggregate range, naturals, term validation, a field-complete audit row, aggregate-only rows, backend pool integrity |
| Duration | lifecycle `test_stabilizing_draws_the_recovery_interval_in_the_accepting_write` |
| Projected state and linked order (AC6–7/23) | lifecycle `test_a_later_attack_resolves_against_the_earlier_hits_projected_state`. The Club's 3 damage is provisional, and the live wolf keeps 4 HP. The Dagger's Light extra attack then deals 2 against the projected 1 HP, so the knockout decision is offered; against the live 4 HP it would not be. The test reloads at every step and counts Writer calls: 0 during the intermediate steps and 1 at delivery. The announce Turn's own Writer call narrates only the request (Group 7). The sheet changes only at delivery. Also the spike; the lifecycle gate test |
| Intermediate transaction | lifecycle race, stale, duplicate, state-moved-after-preparation, failed-event-write rollback, malformed-input and quiet-intermediates tests (no provider, Turn, effect, audit, usage or settlement row); `test_action_resolution_models.py` (19) |
| Final delivery | spike (delivery and typed already-completed); lifecycle typed resume refusals (not ready, not found, other node); a failed narration (Writer error, provider refusal, output block) keeps the ledger, buffers and then writes the refusal log, and the retry delivers identical facts once; event-only audit with corrupted working copies |
| Legacy retirement | `affected-3` (285 orchestration, 160 retrieval, RPG and model suites); `test_pending_roll_db.py`; the retrieval marker tests, including a decision-first sequence |
| Migration | `test_action_resolution_migration.py` (11): drop and add, ledger triggers, seeded-row abort, round trip, downgrade refusal, one unresolved sequence per story |
| Unwired product behaviour | `test_bounded_d20_on_published_release.py` through the unchanged `create_app` (`player_roll_unsupported`); a contest refuses unwired (`test_an_unwired_pass_refuses_a_contest_before_any_die`); knockout preselection with no decision source (`test_zero_hp_lifecycle`, including the `decisions=False` branch); `test_adjudication_service` unwired refusal; orchestrator unwired guard |

## Codex findings, rounds 3 and 4

| Finding | Disposition |
| --- | --- |
| 1. Backend dice inside the accepting transaction; a losing submission draws none | patched: claim first, then dice. Proven by the race and rollback tests |
| 2. Participant-level hidden rolls leak through a shown contest | patched (`contests.prepare`, `writer_view`). Proven for both roles, the nonparticipant and whole-hidden |
| 3. Exact-integer ingress | patched: `StrictInt` on faces, aggregate and both expected revisions; `type(x) is int` in `apply_adjustment` (sibling) |
| 4. Impossible event provenance | patched: payload channel and shape rules, contest-resolution linkage, envelope step and sequence agreement |
| 5. Two contest resolutions | patched: one resolution on the completing event, reused by the record; `_check_contests` compares both. Proven by tamper tests |
| 6. Missing C9 Skills fact bypass | patched: every creature contest check requires the single Skills fact |
| 7. Flaky hidden-AC assertion | patched: structural key check |
| Consolidated residue P1, all-backend contest persistence (`CODEX-PHASE2-CONSOLIDATED-RESIDUE-DISPOSITION.md`) | patched: `CompletedSequence` from adjudication; `record_completed` in the originating Turn's transaction; the retrieval predicate, whose decision lookup is correlated per sequence (a completed in-turn ledger is not a procedural request); unwired contest refusal; the unwired guard; and `_write_rpg_audit` refusing a contest record before writing. Proven by `lifecycle-6`, `affected-4` and `final-batch-*`: the Writer refusal case, `test_a_completed_sequence_counts_only_if_the_sojourner_decided_in_it` and `test_a_contest_never_takes_the_one_row_record_audit` |
| Consolidated residue, proof reachability (AC2–3, AC6–7/23, AC41–46) | added: executor, linked-dependency and stored non-roll event proofs (rows above) |
| Read/accepting transaction (`CODEX-PHASE2-READ-TRANSACTION-DISPOSITION.md`) | patched: preparation outside the write; the recheck right after the claim, before any die. Proven by `test_state_moved_after_preparation_refuses_before_any_die`. The rollback seam is now the event write, not the recheck |

## Sibling audits

- **Exact-integer ingress.**
  - Trigger: finding 3.
  - Inspected: `PlayerRollTermResult.values`, `PhysicalAggregateRollSubmission.reported_aggregate`, both
    `expected_instruction_revision` fields, `MechanicalDecisionSubmission.expected_decision_revision`,
    `apply_adjustment(expected_instruction_revision)`, and `_validate_roll`'s face check.
  - Disposition: patched (5 fields plus the adjustment argument). `_validate_roll` was already safe:
    the admission mechanism is `type(v) is int` before the range check.
  - Out of scope: `DerivedRollTermResult.values`, which is derived by code and never ingress.
- **Accepting-transaction ordering.**
  - Trigger: findings 1 and the read-transaction disposition hit `_advance` twice.
  - Inspected: `_advance` (roll, adjustment, decision), `start` (it runs inside the announce Turn's
    transaction and its dice were drawn by the adjudication before it), `prepare_delivery` and
    `complete` (reads before the delivery transaction, CAS inside it).
  - Disposition: `_advance` patched. The other three were already safe: no new die is drawn under
    their writes, and `complete` is a status-and-revision CAS.

- **Generated steps dropped on a no-pause turn.**
  - Trigger: the consolidated residue P1.
  - Inspected: `adjudicate(sequences=True)`'s no-pause return; the orchestrator's 5b branches (start,
    complete, audit); `_write_rpg_audit`; the unwired guard; the retrieval predicate.
  - Patched: contests (Group 17 requires their ledger); the guard and the predicate.
  - Out of scope: other all-backend 15c operations keep their record audit. No accepted authority
    requires events for them, and changing it would rewrite ordinary 15c delivery.
  - Note: a turn that combines a contest with other operations records all of its dice on the completed
    ledger, because one turn is one sequence.

## Architecture Notes

- **Deviation, Phase 3 boundary.** The Phase 2 sequence service is constructed only by tests
  (`tests/ingestion/mechanical/sequence_stack.py`). Production keeps the 15c unwired behaviour until
  Phase 3 wires it. This is by design, not drift.
- **Deviation, knockout.** The knockout is always the Sojourner's decision wherever decisions can be
  offered. A preselection or a hidden melee attack refuses there. The ADR's status note records this as
  the PRE-ROLL disposition's positive case.
- **Contest audit (Group 17 as written, corrected after Codex's consolidated residue review).** An
  earlier draft let a contest whose dice are all backend dice audit as one record row. That contradicted
  accepted Group 17 and is removed. Every contest persists both participants' roll events and the one
  combined resolution on the completing event, and audits one row per participant from its event:
  - with player input, through the sequence and resume;
  - with none, through `ActionResolutionService.record_completed` inside the originating Turn's own
    transaction.

  Unwired adjudication refuses a contest before any die.
- **Resume Turn input.** The delivered Turn's user input is the originating announce input (the bundle).
  No new Sojourner text exists.
- **Refusal buffering proof.** The fake provider resolver binds a bare adapter. The proof gives its test
  binding the production `RefusalFallbackRouter` and `RefusalLogProxy` hooks. Product wiring is not
  changed.
- **Graphify.** The orientation ran on a scratch copy, because the wrapper writes into the protected
  checkout.
- **Interpreter.** Every test, gate and tool process used
  `D:\AI\Claude\issue-15b-resumption\afterworlds\venv\Scripts\python.exe` with this checkout's
  `src;root` on `PYTHONPATH`. A delegated test-migration helper used a system Python only to rewrite
  test text. Its pytest, Black and Ruff runs used the pinned interpreter.
- **Known Unknown touched, not resolved.** An abandoned sequence holds shared rule changes and adoption
  (`known_unknowns.md`, *Pending-roll rewind/cancel policy*).
- **Preserved holds.** Familiar, CR0, mist, conditional, parameterized and source-open Humanoid holds
  are unchanged. Parameterized adjustments still need an ADR-015b amendment.

## Final local gates (15 October 2026)

- **Lifecycle.** `lifecycle-6`: 26 passed. It was rerun because the accepting transaction and the
  contest persistence changed.
- **Suites invalidated by the final source change.** `affected-4`: 1141 passed, 1 skipped (RPG,
  orchestrator, retrieval, markers, models).
- **Unwired product path and spike.** `published-unwired-2`: 25 passed through the unchanged
  `create_app`.
- **Reused unaffected proofs.** `affected-3` (services, API and persistence suites at `56c75bab`), the
  migration tests (11) and `affected-units-final`.
- **Static gates.** `black --check`, `ruff check` and `mypy` (strict, 271 files) are clean.
- **detect-secrets.** No new or removed baseline entries. The tracked baseline is unchanged.
- **pip-audit (`static-pip-audit-1`).** Exit 1. It finds chromadb 1.5.9 (5 IDs, no fix version
  published) and pip 25.0.1 in the pinned interpreter's environment.
  - No dependency file differs from main. `pyproject.toml` bounds chromadb only as `>=0.5`.
  - CI's pip-audit may therefore flag the same chromadb IDs on main too. That depends on the version
    CI resolves, and these IDs have no fixed release.
  - This is a pre-existing finding, not introduced or changed here. Dependency remediation is
    outside this issue.
- **Not run locally.** The whole local coverage suite was not run, per Codex's instruction. Exact-head
  full CI is the whole-candidate gate after publication.
