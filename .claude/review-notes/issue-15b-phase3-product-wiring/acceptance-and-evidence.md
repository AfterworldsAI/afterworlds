# CRD Issue 15b Phase 3 product wiring: acceptance and evidence map

**Candidate:** branch `codex/issue-15b-phase3-product-wiring` (local, unpublished), based on main
`3f59983d` (tree `44bab0b0`, identical to the tested #196 head).
**Authority:** #127 (full), ADR-015b including Group 17 and its status notes, the Owner's Phase 3
authorization (`OWNER-PHASE3-RESUME-2026-10-15.md`), and CRD Issue 19's product conventions.
**Frozen:** #129 stays at `d8233a43`. The full CRD Issue 19b UI remains deferred; the minimum
15b-31/32 controls are described below.

Raw evidence (per labelled run: `stdout.txt`, `stderr.txt`, `meta.json` with args, head, exit and
timings) is under `D:\AI\Claude\scratch\AW docs\issue15b-resumption\phase3-product-evidence\runs\`
and indexed in `phase3-product-evidence\INDEX.md`. Every Python process used
`D:\AI\Claude\issue-15b-resumption\afterworlds\venv\Scripts\python.exe` with this checkout's
`src;root` on `PYTHONPATH` (`afterworlds.__file__` verified in this checkout). Focused runs disable
coverage and are diagnostics, not acceptance gates. Exact-head whole-PR CI follows publication and
has not run.

## What was built

- **Construction.** `api/pipeline_wiring.py::build_pipeline` returns the orchestrator and the one
  `ActionResolutionService` it owns, sharing the adjudication service, dice and sheet resolver.
  `build_orchestrator` keeps its signature. `create_app` exposes the same instance through the
  typed seam `api/rpg_actions.py::RpgActions`.
- **Routes** (Issue 19 conventions, `responses=` declaring the `ApiError` envelope):
  - `GET /api/stories/{id}/rpg/pending-interaction`: none, pending roll (adjustment options ride on
    it), pending decision, or ready;
  - `POST .../rpg/rolls` (raw or aggregate), `.../rpg/adjustments` (parameterless, `StrictInt`
    revision), `.../rpg/decisions` (stored snapshot);
  - `POST .../rpg/sequences/{sequence_id}/resume`: a turn, returning `TurnSubmissionResponse`.
- **One guard.** `deps.run_under_story_lock` replaces the turn route's inline block; ordinary turns,
  rolls, adjustments, decisions and resume all use it (`409 turn_in_flight`, deliberate, 15b-29).
- **Seam.** A submission is delegated only when its id is the story's current pending interaction
  (`current(story_id)`), so another story's id never advances under this story's lock. Backend
  codes map one-to-one to lowercase `ApiErrorCode` values with fixed messages (no backend text, which
  can quote adjudication detail or ranges, reaches a client).
- **Resume.** The turn runner is shared: access-path selection, the orchestrator's
  `orchestrate_rpg_resume` with the current canonical node, ordinary settlement. Typed refusals from
  the orchestrator become the envelope. With no runnable access path, a sequence that is no longer
  the story's unresolved one is classified by the owning service's `prepare_delivery` (already
  completed, or not found) before the block; the story's unresolved sequence keeps the 403 and its
  facts.
- **Client (minimum, Group 13).** `api/client.ts` gains the five calls and aliases `ApiError` /
  `ApiErrorCode` to the generated schema. `StoryView` reads the pending interaction of RPG stories,
  renders `RpgPendingInteraction` (raw faces per term as a physical self-report, offered adjustment
  and decision options, a resume button), resumes at once when an advancement is ready, shows only
  the affordance after a reload, and treats `action_sequence_already_completed` as success with a
  transcript and pending refetch. The turn input stays enabled (OOC). No dice tray, scorecard,
  browser RNG or frontend arithmetic.
- **Generated contract.** `frontend/src/api/schema.ts` regenerated with the pinned interpreter and
  lockfile `openapi-typescript` 7.13.0; regenerating again is byte-identical.

## Hand-authored production files: 11 (split gate: 12)

Backend 8: `api/app.py`, `api/deps.py`, `api/dto.py`, `api/errors.py`, `api/pipeline_wiring.py`,
`api/rpg_actions.py` (new), `api/routes/rpg_actions.py` (new), `api/routes/turns.py`.
Frontend 3: `src/api/client.ts`, `src/StoryView.tsx`, `src/RpgPendingInteraction.tsx` (new).
Generated, not counted: `src/api/schema.ts`. Tests and docs not counted. No backend service,
persistence model, migration, orchestration behavior or business policy changed: the split gate
was not reached.

## Acceptance map (what each layer proves)

| Criterion | Proof |
| --- | --- |
| AC31 product reachability, AC7 narration batching, AC9/11 positive adjustment and decision, AC23–24 | `test_a_linked_action_with_an_adjustment_and_a_decision_is_narrated_once` (HTTP, `create_app`, published store, fake provider): finesse adjustment, attack, damage, stored knockout decision, a reload equal to each response, one Writer call at resume, no Planner or intent pass on resume, effects and both audits with the Turn, credit settled once |
| AC15–16, AC10, AC37 rejections over HTTP | same test: stale and inexact (`true`, `1.0`, `"1"`) revisions, an option not offered, superseded instruction, impossible face, foreign term, inexact faces, impossible aggregate, invalid or stale decision; each leaves the state tuple unchanged |
| AC22 duplicate | same test (an accepted roll resubmitted is not the story's pending roll); service-level races stay Phase 2's |
| 15b-28 no intermediate provider/access/settlement | same test: between announce and resume only the three blocked IC turns' intent passes and readiness probes occur; balance and Turn/audit counts unchanged; live wolf untouched |
| AC29 gate, 15b-31 OOC | IC blocked at roll, decision and ready (linked test); `test_out_of_character_input_never_alters_the_sequence` |
| AC30 shared lock | `test_a_roll_in_flight_holds_every_mutation_of_its_story`, `test_a_turn_in_flight_holds_every_rpg_operation_of_its_story` |
| Story scoping | `test_another_storys_pending_interaction_never_advances_from_this_story` (HTTP) and the seam unit tests |
| AC26 current node, AC25/38/39 failure and retry, no path | `test_resume_refusals_and_failures_keep_the_ready_facts_for_a_retry[writer_error|writer_refusal]`: another node, unknown and foreign sequences, 403 with ready facts intact, failed narration preserving the ledger, identical-facts retry |
| AC27 / 15b-32 | same test after a real `HOSTED_ACCESS_DEACTIVATED` event: completed replay → 409 `action_sequence_already_completed`, nothing called or settled; route tests for completed/not-found and ready/no-access ordering; resume translation tests; client tests (immediate resume, reload affordance without auto-resume, no-error refetch, stale failure banner cleared, no failed-resume loop) |
| AC21 hidden projection, AC32 generated contract | `BACKEND_ONLY` key scans of every player response; contest test reads the resume Writer's `WriterAdjudicationView` (player total 11, no outcome or target from the hidden comparison, no `20` token in the summary) while the hidden event/audit keep total 20; `test_the_generated_contract_exposes_only_deliberate_player_shapes` |
| Group 17 production reachability | `test_a_contest_against_a_hidden_counterpart_is_reachable_and_projected_as_a_check` (S1 in memory only) |
| Migrated unwired assertion | `test_player_roll_configuration_announces_a_pending_roll` replaces the 15c unwired refusal |
| AC33 no scope leakage | no cancellation, expiry, rewind, supersession, adjustment sub-state, form framework or anti-cheat added |

Conserved Phase 2 proofs (unchanged code): validation rules, event shapes and atomicity, audit
projection, contest arithmetic, service-level races, migration and append-only enforcement (AC1–6,
8, 12–14, 17–20, 28, 34–36, 40–59), mapped in
`.claude/review-notes/issue-15b-backend-integration/acceptance-and-evidence.md`.

## Codex review checkpoint dispositions

- **Completed-resume ordering (P2).** Patched as above. Proven by the HTTP replay after real
  deactivation and the route ordering tests.
- **Client reachability.** Implemented (minimum Group 13); broader UI remains CRD Issue 19b.
- **Numeric confidentiality assertion (P2).** Replaced by the semantic Writer-view check; a `20` in
  an unrelated id no longer matters. Defect-family sibling check: the pending-view `"ape"` marker is
  a fixed text marker on the player view and stays.

## Architecture Notes

- **Phase 3 of 3. No drift from ADR-015b or the surviving ADR-015 authority boundaries.** The
  orchestrator remains the sole pipeline owner; routes validate, lock, delegate and translate.
- **Deviation, none.** Route-level story scoping uses the existing `current` read; the completed
  classification uses the existing `prepare_delivery`. No Phase 2 owning pipeline, persistence or
  rules-policy implementation changed; eight API Python files changed.
- **Observation, not changed.** A player's Writer view in a contest against a hidden counterpart
  carries `outcome = None` while its summary narrates the loss (Phase 2 projection).
- **Known Unknown touched, not resolved:** *Pending-roll rewind/cancel policy*; abandoned
  sequences now hold rule changes in production (`known_unknowns.md`).
- **Independent product-wiring consultation.** Read-only Claude session
  `30b897c4-7385-4721-8176-13fe2a7094fd` inspected all eleven production files and found no concrete
  blocking concern or split trigger. Codex checked its source applicability and integrated the
  result. See [the consultation receipt](independent-product-wiring-review.md). Earlier engineer
  self-review statements do not establish separate advisor invocations.
- **Graphify.** Code-only graph built on a scratch copy (the wrapper targets the protected checkout;
  no LLM key for the one doc file).
- **Playwright spine and pip-audit:** see the evidence index for actual results and limitations.
