# PR #126 Remediation Log — CRD Issue 19

Archive of detailed Codex/Claude review-remediation history for PR #126 (CRD Issue 19), moved out of
`.claude/pr_body_issue19.md` to keep the PR body focused on merge-relevant summary, acceptance
coverage, durable Architecture Notes, and current gate status. This is a faithful copy of what was
previously in the PR body, not a rewrite — round-specific gate output, sibling audits, negative
controls, and reviewer-history commentary are preserved as originally written.

---

## Remediation (review round 1, head `acc95cf591` → this head)

Codex posted 2×P1 + 2×P2 against `acc95cf591`; the classification summary judged two in-scope
merge-blocking defects and two boundary/owner-decision items. Fixes below address the two
defects plus the review's third P1 (startup schema bootstrap), which the owner elected to fix in
this PR rather than defer. The Writing-provenance P2 is explicitly *not* fixed, per Binding
Decision 7.

- **Per-turn context Session ownership (P1).** `build_orchestrator()` previously opened one
  `context_session = session_factory()` at app-construction time and shared it — captured inside
  `StoryBibleService`, `RollingSummaryService`, `SQLiteRecentTurnsProvider`, and
  `RulesPackageService` — across every turn, every story, for the app's entire lifetime. Real
  turns run inside `asyncio.to_thread`, and Binding Decision 8 deliberately permits concurrent
  turns for *different* stories to run without serializing, so two cross-story turns could drive
  the same non-thread-safe SQLAlchemy `Session` from separate worker threads; the same long-lived
  session also never committed/rolled back, so it could hold a stale SQLite read snapshot even
  single-threaded. Fixed with `_PerTurnContextBuilder` (`api/pipeline_wiring.py`): a narrow,
  duck-typed `assemble()` substitution (same pattern as `FakeProviderResolver`, passed with a
  documented `# type: ignore[arg-type]`) that opens one short-lived session per call, builds a
  throwaway session-bound `ContextBuilderService`, delegates, and closes the session — mirroring
  the per-call session pattern the mode session resolvers already used. Stable-prefix-once-per-turn
  is unaffected: `assemble()` still builds it exactly once per call, and the orchestrator calls
  `assemble()` exactly once per turn. `ChromaRetrievalMemoryProvider` continues to be shared (it
  wraps a `chromadb.PersistentClient`, not a SQLAlchemy `Session` — verified by reading
  `pipeline/retrieval/client.py` and `chroma_provider.py` before reusing it). Regression coverage:
  `tests/api/test_pipeline_wiring.py` (fresh session per call, session closed even when `assemble()`
  raises, independent sessions across concurrent stories).
  - *Sibling audit* (same defect family: a captured/shared session or a session used across an
    unsafe boundary): `placeholder_session` used to construct `WriterService`/`ExtractorService` in
    the same function — **already safe**, verified against `pipeline/orchestrator/service.py`'s
    call sites, which pass `session=` explicitly at every `writer_service.write(...)` and
    `extractor_service.extract(...)` call; the constructor-time session is never touched for real
    turn processing. `ProviderResolver` — **already safe**, constructed with `session_factory`, not
    a session. The three mode session resolvers (`_make_rpg_session_sheet_resolver`,
    `_make_branching_session_resolver`, `_make_writing_session_resolver`) — **already safe**, each
    already opens a fresh session per call (the pattern this fix now mirrors).
    `ByokCredentialReadinessProvider` (`app.py`) — **already safe**, constructed with
    `session_factory`. `deps.py`'s `get_session` (per-request FastAPI dependency) and
    `provision_sojourner_id` (one-shot at `create_app()` construction, session closed immediately,
    single-uvicorn-worker per Binding Decision 8) — **already safe**.
- **Migration-based schema bootstrap (P1).** `create_app()` called
  `Base.metadata.create_all(engine)` against whatever ORM modules `app.py` happened to import at
  module scope. That silently skipped every Alembic-only DDL statement — including the
  append-only audit triggers on `entitlement_event`, `provider_refusal_log`, and `rpg_roll_audit`
  — and, verified by diffing `app.py`'s import list against `alembic/env.py`'s, omitted several
  tables entirely on a fresh database (`entitlement.orm`, `pipeline.provider._refusal_log`,
  `persistence.orm.story_bible`, `persistence.orm.rules_package`,
  `persistence.orm.rolling_summary`, `pipeline.provider._route_config`,
  `pipeline.provider.credentials._metadata` were never imported by `app.py`). This is a real
  Architecture Invariant 11 (auditability / money-adjacent event logs) gap. Fixed with
  `api/db_bootstrap.py::upgrade_to_head()`, which runs the repo's real Alembic migrations against
  `settings.database_url` (idempotent — a no-op against an already-current database) before
  `create_session_factory()`. The now-redundant ORM mass-import block in `app.py` was removed;
  removing it did not break mapper configuration or any test (full suite green), since CRUD
  modules already import their own ORM classes and Alembic's `env.py` imports the complete set
  independently. No new migrations were added — the existing migrations already define the full
  schema and triggers; this was a wiring gap, not a missing-migration gap. Regression coverage:
  `tests/api/test_db_bootstrap.py` (real `create_app()` reaches Alembic head; all previously-missing
  tables now exist; the append-only triggers exist in `sqlite_master` and a direct UPDATE/DELETE on
  `entitlement_event` is rejected by the DB layer, not just by application code).
- **`RequestValidationError` → single error envelope (P2).** FastAPI/Pydantic validation failures
  (an `extra="forbid"` rejection, an invalid setup enum, a malformed UUID path parameter, a
  non-integer transcript `limit`) previously fell through to FastAPI's default `{"detail": [...]}`
  422 body instead of the `ApiError` envelope, violating Binding Decision 10 and silently skipping
  the frontend's typed `ApiRequestError` branch. Fixed with a `RequestValidationError` handler in
  `create_app()` returning `ApiErrorCode.VALIDATION_FAILED` at 422; `detail` carries only the
  dotted field path and message per offending field, never `exc.errors()`'s raw `"input"` value
  (which can echo client-supplied data). Regression coverage: `tests/api/test_validation_envelope.py`
  (all four representative cases, asserting the actual envelope shape, not just the status code).
- **Writing-mode turn provenance (`work_product_kind`) — deliberately not fixed here
  `[OWNER DECISION]`.** Codex correctly identified that every Writing turn is recorded with default
  non-canon eligibility because `TurnSubmissionRequest` never carries `work_product_kind`/canon
  eligibility, suppressing extractor/Story Bible/retrieval-memory routing that should apply to
  eligible prose. Codex's proposed remedy — add these fields to the HTTP request contract — was not
  implemented: Binding Decision 7 explicitly forbids the API from accepting client-supplied
  `work_product_kind`/canon-eligibility metadata (a browser-supplied value would become the canon
  trust boundary) and directs this to be derived server-side through the owning mode service, or
  stopped and flagged. This PR does not attempt a server-side derivation seam, since that is a
  larger Issue-17/mode-service question the owner should settle rather than have HTTP-layer code
  guess at. Deferred pending an owner decision: either wire an existing Issue 17 derivation seam if
  one already exists, or open a follow-on issue. Not resolved silently, not patched around.

## Remediation round 2 (new Codex findings on `abd6b7a` → this head)

- **Retrieval query/write services now wired into the real product orchestrator (P1).**
  `build_orchestrator()` constructed `RetrievalMemoryConfig`/`ChromaRetrievalMemoryProvider` but
  never passed `retrieval_query_builder`/`retrieval_write_service` to `OrchestratorService`, so
  production turns silently ran with no Issue 18 Retrieval Memory query and no post-commit
  ingestion — both stayed at their `None` defaults with no error, a silent capability loss, not a
  crash. Fixed by wiring the existing `RetrievalQueryBuilder` and `RetrievalMemoryWriteService`
  exactly as they already exist, sharing one Chroma client/config with the existing
  `ChromaRetrievalMemoryProvider`. `RetrievalQueryBuilder` needs a session-bound
  `SQLiteRecentTurnsProvider`; since it is constructed once at app-lifetime like the context
  builder, a shared session would reintroduce the same cross-story-concurrency defect round 1
  fixed for `ContextBuilderService` — so it gets an identical per-call-session wrapper
  (`_PerTurnRecentTurnsProvider`). No new eligibility predicate, ID builder, or query-gate logic
  was added; the orchestrator's own existing post-commit ingestion gate
  (`pipeline/orchestrator/service.py`) already owns eligibility/session lifecycle for the write
  path untouched. Regression coverage: `tests/api/test_pipeline_wiring.py` (constructor-spy
  proving `build_orchestrator()` passes non-None, correctly-typed instances; a session-safety
  proof for `_PerTurnRecentTurnsProvider` mirroring the round-1 context-builder test) and
  `tests/api/test_fake_provider_product_path.py` (two real delivered turns through the actual
  `create_app()` wiring with the fake provider, proving the query/write path runs end-to-end
  without crashing — including a second turn where the query builder has a real prior committed
  turn in its eligibility window).
- **`WritingVisibleStateService` now wired (P1, same finding).** Writing IN_PLAY turns hard-require
  `writing_visible_state_service` to validate the session's `persona_id` against the registry
  before Writing output proceeds (`pipeline/orchestrator/service.py` line ~666) — unlike
  `rpg_visible_state_service`/`branching_visible_state_service`, which the orchestrator treats as
  optional enrichment via `is not None` guards. Left unwired, every Writing story already IN_PLAY
  returned `PIPELINE_ERROR` ("writing visible state service not wired for IN_PLAY turn"). Fixed by
  constructing `WritingVisibleStateService(get_default_registry())` — the exact same
  `get_default_registry()` singleton `api/visible_state.py` and `api/routes/personas.py` already
  use, not a new registry instance or provider. Regression coverage:
  `tests/api/test_fake_provider_product_path.py::test_writing_in_play_turn_does_not_fail_for_missing_visible_state_service`.
  Note: nothing in Issue 19's product HTTP path currently promotes a Writing story's `play_status`
  from SETUP to IN_PLAY — that write only happens via the Writing OOC config extractor pass
  SERVICE (`self._writing_ooc_config_extractor`), which is deliberately unwired per this file's
  existing "mode-specific pass SERVICES... out of scope" note. The regression test promotes
  `play_status` directly via the same typed CRUD the orchestrator itself would eventually call, to
  construct the IN_PLAY-with-valid-persona precondition without adding new mode policy.
  - *Sibling audit* (constructor dependencies required for a real product path vs. deliberately
    unwired mode-specific pass services): every other `OrchestratorService` optional parameter was
    checked against its usage in `pipeline/orchestrator/service.py`. `rpg_visible_state_service`/
    `branching_visible_state_service` — **already safe**, optional enrichment (`is not None`
    guards), not a hard gate like Writing's. `rpg_adjudication_service`, `branching_writer_service`,
    `branching_selection_service`, `branching_ooc_config_extractor`, `writing_ooc_config_extractor`
    — **out of scope**, genuine mode-specific pass SERVICES per this file's existing docstring, not
    touched. `rpg_dice_service`, `rpg_pending_roll_service` — **already safe / unreachable**: both
    hard-gates live behind `player_reported_total is not None` (the RPG dice-consume path) or
    `rpg_adjudication_service is not None`, and neither is reachable through Issue 19's
    `TurnSubmissionRequest` (no `player_reported_total` field exists on it — the RPG dice UI and
    consume adapter are explicitly deferred to Issue 19b per this file's existing note above).
    `mode_resolver`, `executor`, `parallel_pass_timeout_seconds`, `parallel_pass_max_workers` —
    **already safe**, sensible internal defaults, no product requirement to override them here.
- **Legacy/pre-API anchor bootstrap now commits before orchestration (P2).**
  `ensure_story_turn_anchor_node` now returns a typed `StoryTurnAnchorResult(node_id, created)`
  instead of a bare `UUID`. In `_submit_turn_sync` (`api/routes/turns.py`), when `created=True` the
  route session commits immediately, before calling `orchestrate_turn`. Without this, a story
  created before this anchor-bootstrap concept existed (or by any path other than `POST /stories`)
  would have its anchor only flushed, not committed, in the route's session; `orchestrate_turn`
  opens its own separate session immediately afterward, and `WriterService`'s
  `node_belongs_to_story` check in that second session could not see the just-flushed row — the
  first turn failed as `PIPELINE_ERROR`, and only a retried turn (after the eventual end-of-request
  commit) would succeed. The commit is scoped to bootstrap state only: it fires before entitlement
  settlement and before any turn output exists, so it cannot accidentally commit settlement or
  turn-result state. When an anchor already exists (`created=False`, the common case for every
  story created through this API), no extra commit happens. The anchor is idempotent v1 bootstrap
  state, not narrative output, canon, or a delivered Turn — it may legitimately survive a later
  `PIPELINE_ERROR` from the same request. Regression coverage:
  `tests/api/test_fake_provider_product_path.py::test_first_turn_for_anchor_less_legacy_story_does_not_fail`
  (constructs a story via CRUD only, bypassing `POST /stories`'s own anchor-creation call, to
  reproduce the pre-anchor-bootstrap shape; verified with a negative control that the test fails
  without the commit fix and passes with it restored). Existing story-created-through-`POST
  /stories` tests remain green (that path already committed the anchor as part of its own
  single-transaction creation flow, so `created=True` there was already safe; unaffected either
  way).
- No client-supplied Writing trust-boundary fields were added in this remediation round. Codex's
  round-2 findings did not include the Writing-provenance defect again (already logged as
  `[OWNER DECISION]` above); this section only fixes the two new findings.

## Remediation round 3

- RPG setup turns no longer require a completed `Dnd5eCharacterSheet`. A fresh RPG story only has
  `RpgCharacterSheetBase` bootstrapped at creation; `OrchestratorService` gained a new
  `rpg_session_resolver` seam (session-state-only, no sheet lookup) that the mandatory RPG
  turn-retrieval-marker classification now prefers, falling back to the existing
  session+sheet resolver only when the newer one is not wired. Sheet-dependent paths
  (adjudication, pending-roll consume) are unaffected and remain unreachable in this PR since RPG
  adjudication stays unwired.
- Branching/Writing setup handoff now survives reload/resume: `StoryView` derives a
  `structuredSetupPersisted` signal from the fetched visible state (non-null once structured
  fields are configured) in addition to the in-memory `structuredSetupSaved` flag, so a reload
  between saving setup and submitting the confirmation turn no longer bounces the Sojourner back
  to the setup form. RPG is excluded from this signal (its visible state stays null until a
  concrete sheet exists).
- Retry after a failed initial story load now clears the stale error screen on success: the
  initial `useEffect` load and the Retry button share one `loadStory()` function.

## Remediation round 4

- `WritingSetupRequest` now validates `dialogue_narration_ratio` (0-100) and rejects blank/
  whitespace-only `beat_constraints` entries at the API boundary, matching `WritingSessionState`'s
  own validators. Previously the route flushed unvalidated values via `apply_writing_config_update`
  (whose docstring assumes its one production caller, `WritingConfigUpdate`, already validated
  them — true for the OOC extractor path, not for this route) and then immediately re-read the row
  through `build_visible_state`, which raised while reconstructing `WritingSessionState` — an
  unhandled 500, not the typed 422 envelope. Sibling audit of every other `WritingSessionState`
  validator against `WritingSetupRequest`: `form=OTHER` without `form_other` — `already safe`,
  `apply_writing_config_update` already skips that write to avoid an unreadable row (not
  overcorrected here, per explicit scope); the two `IN_PLAY`-gated validators (`persona_id`,
  `specific_goals` required) — `already safe`/unreachable, this route never sets `play_status`.
  OpenAPI schema changed (docstring only) and was regenerated; no frontend code changes needed.

## Remediation round 5

- **Server-derived Writing turn provenance (P1) — boundary resolved with an owner decision, not
  silently.** This is the same Writing-provenance hotspot flagged `[OWNER DECISION]` in round 1;
  per CLAUDE.md's boundary rule (repeated rounds hitting the same invariant), the fix was not
  decided in code. The review comment's own "preferred" mechanism — promote `WritingSessionState
  .play_status` to `IN_PLAY` once `persona_id` is configured — turned out to be blocked by an
  existing invariant: both `WritingSessionState._in_play_requires_goal` and the
  `apply_writing_config_update` CRUD guard (PR #116 owner decision) also require nonblank
  `specific_goals` before `IN_PLAY` can be persisted, and the real `WritingSetupForm` only ever
  collected `persona_id` — `specific_goals` stayed permanently blank for every story created
  through the frontend. `specific_goals` is not neutral bootstrap state: it is injected directly
  into the Writer's system prompt (`pipeline/writing/context.py`) and rendered in the
  visible-state sidebar, so a synthesized placeholder would fabricate Sojourner-authored content.
  This was surfaced to the owner as an explicit fork (promote-to-`IN_PLAY`-with-a-real-goal vs.
  relax the `IN_PLAY` invariant via an ADR revision vs. defer) rather than resolved silently.
  **Owner decision:** add a required, user-authored `specific_goals` field to Writing setup; do
  not invent a placeholder; do not relax the `IN_PLAY` invariant.
  - `WritingSetupForm` (frontend) now collects a required "What are you trying to write, revise,
    or accomplish?" field and submits it as `specific_goals`.
  - `WritingSetupRequest.specific_goals` (`api/dto.py`) changed from optional to required, with a
    nonblank field validator (matching the existing `beat_constraints` validator pattern).
  - `routes/setup.py`'s `_apply_writing_setup` now passes `play_status=WritingPlayStatus.IN_PLAY`
    to `apply_writing_config_update` on every call. This is safe and idempotent precisely because
    persona_id and nonblank specific_goals are both required and both applied earlier in the same
    call, so the CRUD guard's "cannot enter IN_PLAY without persona_id + a goal" precondition is
    always genuinely satisfied here — this route is the one legitimate place that can promote
    play_status, per the owner's explicit direction.
  - `routes/turns.py` no longer needs any "promote before orchestrating" bootstrap-commit dance
    (the round-3 anchor-commit pattern was considered but not needed): promotion now happens
    entirely inside `POST .../setup`, a separate call from turn submission. `_submit_turn_sync`
    calls a new typed seam, `story_bootstrap.py::derive_writing_turn_request(session, story_id,
    mode)`, which returns a server-derived `WritingTurnRequest(work_product_kind=
    PROSE_CONTINUATION, canon_eligibility_override=EXTRACTOR_ELIGIBLE)` only when the story is
    Writing mode AND its persisted `play_status` is genuinely `IN_PLAY`; otherwise it returns
    `None` (fail closed, no invented defaults), leaving the orchestrator's existing SETUP-forcing
    logic in `_narrative_persist` in control unchanged.
  - **Binding Decision 2 note:** the derivation logic lives in `api/story_bootstrap.py`, not
    inline in `routes/turns.py`, because `tests/api/test_handler_thinness.py` forbids route
    modules from importing `afterworlds.pipeline.writing` directly (only the orchestrator may
    invoke mode-specific pass services). The first implementation attempt imported
    `WritingTurnRequest` straight into `turns.py` and correctly failed that test; moved to the
    existing `story_bootstrap.py` seam (already home to `ensure_story_turn_anchor_node`/
    `ensure_mode_session_state`/`resolve_play_status`) instead of a new module, per "fewest files."
  - `TurnSubmissionRequest` gained no new fields — `work_product_kind`/`canon_eligibility_override`
    are still rejected by `extra="forbid"` (regression test:
    `tests/api/test_turns.py::test_turn_submission_rejects_client_supplied_writing_provenance`).
    This does **not** reopen the rejected client-supplied trust-boundary approach from Binding
    Decision 7 — provenance is derived entirely from persisted server-side state, never from the
    HTTP request body.
  - Tests: `tests/api/test_setup.py` (specific_goals required/nonblank, play_status promotion
    verified via CRUD read); `tests/api/test_fake_provider_product_path.py` (full product-path
    test asserting a turn submitted after real `/setup` is `PROSE_CONTINUATION`/
    `EXTRACTOR_ELIGIBLE` in the durable `WritingNodeMetadata` record AND
    `gather_turn_eligibility(...).eligible is True`, i.e. Retrieval Memory eligibility is not
    suppressed; a SETUP-status regression test confirming turns before setup completes still stay
    `NON_CANON_SUPPORT`; a missing-session-state fail-closed test). All new tests verified with a
    negative control (temporarily reverted the fix, confirmed the tests fail, restored).
  - Manually verified end-to-end in a browser against the real (un-mocked) `create_app()`: created
    a Writing story, completed setup with a real persona and goal, confirmed the `/setup` response
    showed `play_status: "in_play"`.

- **RPG setup no longer resets to defaults on reload (P2).** `RpgSetupForm` previously always
  initialized `dice_handling`/`tone` from hardcoded defaults (`ai_rolls`/`balanced`); since RPG
  visible state stays null until a concrete character sheet exists (by design — sheet-dependent),
  RPG cannot use the `structuredSetupPersisted` signal Branching/Writing already use to bypass
  their setup forms on reload, so RPG's setup form always re-rendered fresh, and the next save
  silently overwrote any previously-chosen non-default values. Fixed with a new
  `GET /api/stories/{story_id}/setup` endpoint (mode-discriminated, mirroring the existing
  `GET .../visible-state` pattern) that reads the persisted mode session-state config directly —
  never sheet-dependent, since RPG session state exists from story creation
  (`ensure_mode_session_state`), independent of sheet completeness. New DTOs: `RpgSetupStateDTO`,
  `BranchingSetupStateDTO`, `WritingSetupStateDTO` (all-optional mirrors of the existing
  `*SetupRequest` field sets, since persisted state may be partial), wrapped in
  `SetupStateResponse`. `RpgSetupForm` now hydrates `diceHandling`/`tone` from this endpoint on
  mount instead of relying only on hardcoded initial state.
  - *Sibling audit* (PR #126 review round 5, P2's explicit instruction): checked whether
    Branching/Writing setup forms have the same "defaults overwrite persisted config on reload"
    defect. **Already safe** — both already bypass `SetupForm` entirely on reload once
    `structuredSetupPersisted` is true (persisted visible state non-null), a fix from round 3; they
    never re-render their setup forms with default state once configured, so there is no
    defaults-overwrite path to fix. The new `GET .../setup` endpoint still returns
    `BranchingSetupStateDTO`/`WritingSetupStateDTO` for symmetry/honesty across all three modes
    (cheap: the CRUD reads already existed), but no frontend hydration consumes it for those two
    modes today, since nothing needs to.
  - Did not: treat `visibleState !== null` as the RPG setup-persisted signal (RPG's `GET
    .../setup` is a dedicated, session-state-only read, unrelated to `RpgVisibleState`); store this
    only in React state or only in localStorage; fabricate a partial `RpgVisibleState` before a
    concrete sheet exists; expand into full setup-editing UX beyond `dice_handling`/`tone` (the
    only fields `RpgSetupForm` currently exposes, though the new DTO carries every field
    `RpgSetupRequest` already owns for future use).
  - Tests: `tests/api/test_setup.py` (fresh RPG story returns creation defaults, not 404; saved
    non-default values reflected on a fresh GET simulating reload; 404 for a missing story;
    Branching/Writing GET symmetry); `frontend/src/StoryView.test.tsx` (RpgSetupForm hydrates from
    persisted state; a save after hydration submits the hydrated values, not the hardcoded
    defaults). Negative-control verified (temporarily reverted the fix, confirmed both new backend
    tests fail, restored).
  - Manually verified end-to-end in a browser: created an RPG story, saved `dice_handling=
    player_rolls`/`tone=gritty`, reloaded the page, confirmed the setup form showed "Player rolls"/
    "Gritty" (not the AI rolls/Balanced defaults).

- OpenAPI schema regenerated (`specific_goals` now required on `WritingSetupRequest`; new
  `RpgSetupStateDTO`/`BranchingSetupStateDTO`/`WritingSetupStateDTO`/`SetupStateResponse` schemas;
  new `GET /api/stories/{story_id}/setup` operation) — `frontend/src/api/schema.ts` regenerated,
  drift gate passes.
- Full gate suite green on the exact branch head: `black`, `ruff`, `mypy --strict`, `pytest -q`
  (2266 passed, 10 skipped, 91.78% coverage) for Python; `tsc --noEmit`, `eslint`, `prettier
  --check`, `vitest run` (21 passed), production `vite build` for the frontend.

### Round 5 follow-up: Branching/Writing setup-handoff signal tightened for Writing

Owner follow-up after round 5 landed: `StoryView`'s `structuredSetupPersisted` (the round-3 signal
that bypasses `SetupForm` on reload once structured setup is persisted) used `visibleState !==
null` identically for both Branching and Writing. For Writing this was no longer correct once
round 5 shipped: `visibleState !== null` only means `persona_id` is set — it says nothing about
`specific_goals`. A pre-round-5 row (or any row with `persona_id` set but `specific_goals` still
blank) has non-null visible state while `play_status` never promotes past `SETUP`, so the old
signal would silently reopen the play view for a story whose turns stay forced to
`SETUP_CONFIRMATION`/`NON_CANON_SUPPORT` forever — the exact defect round 5 fixed, resurfacing via
this bypass instead of the original path.

Fixed by making Writing's branch check `visibleState.play_status === "in_play"` instead of mere
non-null presence — the same durable signal `turns.py`'s `derive_writing_turn_request` uses, which
can only be true once both `persona_id` and a real, Sojourner-authored `specific_goals` are
persisted (`WritingVisibleState` already exposes `play_status`, a property unique to it among the
three `VisibleState` union members, so this narrows safely in TypeScript via `"play_status" in
visibleState`). Branching is deliberately left unchanged — its `play_status` only flips once the
confirmation turn itself lands (ADR-016 Decision 3), which happens *from* the play view, so gating
Branching's bypass on `play_status` would prevent ever reaching the play view to submit that turn.

Tests: `StoryView.test.tsx` updated — the existing "Writing story with persisted visible state"
test now uses `play_status: "in_play"` (representing a genuinely round-5-complete row); a new test
asserts a `persona_id`-set-but-`play_status: "setup"` row still shows `SetupForm`, not the play
view. Both directions negative-control verified (temporarily reverted to the old
`visibleState !== null` check and confirmed the new test fails; temporarily disabled the Writing
branch entirely and confirmed the existing positive-case test fails; restored). Full frontend
gate suite re-run green (22 tests, up from 21).

### CI catch: Playwright E2E spine required a matching fix

CI's `spine.spec.ts` failed after round 5 landed: two tests (`entitlement-blocked rendering...`,
`story create with mode selection, Writing setup, and a delivered turn`) select a Writing persona
and click "Save setup" without ever filling the new required `specific_goals` textarea. `WritingSetupForm`'s
submit button is `disabled={submitting || !personaId || !goalsReady}`, so the button never becomes
clickable and Playwright's `.click()` timed out at 30s waiting for it -- a genuine sibling-audit
miss in round 5 (the Vitest unit tests were updated for the new required field; the E2E spec, a
sibling caller of the same form, was not checked). Fixed by filling the specific_goals textarea
(`getByPlaceholder("e.g. Draft the opening chapter of a mystery novel")`) before clicking "Save
setup" in both tests. The other three Writing-mode E2E tests only assert the setup heading renders
and never click "Save setup", so they were unaffected. Verified by running the full Playwright
suite locally against a fresh build (`npx playwright test`) -- all 6 tests pass, including both
previously-timing-out tests.

## Remediation round 6

Boundary note honored per the reviewer's own framing: this round again touches
`pipeline_wiring.py`/`routes/turns.py`, but each comment named a concrete, distinct defect, not a
repeat of a prior finding, so all three were implemented directly (no owner escalation needed this
round).

- **Intent Classification routed through the selected access path (P1) -- architectural fix, not a
  patch.** `_default_intent_model_caller()` read process-level `ANTHROPIC_API_KEY` and called
  Anthropic directly, bypassing `TurnProviderBinding`/`ProviderResolver` entirely. For BYOK turns
  this either failed outright (no hosted key set) or -- worse -- would have silently spent a
  hosted/server key outside the Sojourner's BYOK pool had one been present, crossing the
  hosted/BYOK boundary the entitlement model exists to enforce.
  - **Architecture Note (per the reviewer's explicit instruction):** Intent Classification is a
    model call and is now routed through the selected access path in the product path, exactly
    like Planner/Writer/Extractor/Contradiction/Safety. It is no longer a standalone seam outside
    `ProviderResolver`/`ProviderAdapter`.
  - Added `PipelinePassId.INTENT_CLASSIFIER` (`entitlement/enums.py`) and
    `PassIdentifier.INTENT_CLASSIFIER` (`pipeline/_refusal.py`), registered in the Anthropic
    adapter's `_PASS_PROFILE` (Haiku tier) and `_pass_id_to_pass_identifier` map, and in
    `entitlement/policy.py::PASS_TIER_DEFAULTS` for the documented "MUST agree" invariant between
    those two dicts -- both regression-tested by the existing exhaustive
    `test_all_pipeline_pass_ids_have_pass_profile_entry` / `..._pass_identifier_mapping` tests,
    which now cover this pass id for free.
  - `IntentClassifierService.classify()` gained a small, typed protocol widening: an optional
    `*, model_caller: ModelCallerT | None = None` per-call override, falling back to the
    constructor-injected caller when omitted. This is backward compatible with every existing
    `tests/services/test_intent_classifier.py` test (all construct the service with a caller and
    call `classify()` with no override).
  - `orchestrate_turn()`'s step 1 now builds a provider-routed caller from the `binding` already
    resolved in step 0 (`_make_intent_classifier_caller`, `pipeline/orchestrator/service.py`) and
    passes it as that per-call override on every classification. The caller wraps the prompt in a
    `ProviderCallRequest(pass_id=INTENT_CLASSIFIER, ...)`, delegates to
    `ScopedProviderAdapter(binding.adapter, sojourner_id).call(...)` -- the same wrapper every other
    pass uses for refusal-log scoping -- and extracts the returned `ProviderTextPart`. No second,
    hidden provider resolver is created. Hosted turns get hosted credentials via `ProviderResolver`;
    BYOK turns get only Sojourner-configured BYOK credentials -- both simply follow from reusing the
    same `binding` step 0 already resolved.
  - `build_orchestrator()` (`api/pipeline_wiring.py`) now constructs `IntentClassifierService`
    uniformly in both fake and real provider mode with `_unrouted_intent_caller`, a
    constructor-required placeholder that raises loudly if ever actually invoked -- the orchestrator
    always supplies the provider-routed override, so this placeholder proves a missing override
    fails loudly instead of silently reading process credentials or returning a wrong response.
    `_default_intent_model_caller()` is deleted, not deprecated.
  - Fake-provider CI mode continues to use `fake_intent_model_caller`'s canned response, per the
    reviewer's explicit allowance -- but now reached uniformly through `FakeProviderAdapter`'s new
    `"intent_classifier"` branch (`api/fake_pipeline.py`), which extracts the prompt from
    `request.rendered_blocks` and returns `fake_intent_model_caller(prompt)` wrapped in a
    `ProviderTextPart`. `FakeProviderResolver` already resolved to `FakeProviderAdapter`
    unconditionally, so this required no resolver changes.
  - No classifier-specific refusal routing was added: a `ProviderRefusalError` (or any other
    exception) raised during classification is still caught by `orchestrate_turn()`'s existing
    step-1 broad `except Exception`, preserving the current fail-closed `PIPELINE_ERROR` behavior --
    exactly the reviewer's fallback instruction when no classifier-specific refusal result exists.
    **Superseded in round 7 below:** a later round added explicit `ProviderRefusalError` handling
    for this exact step, mapping it to `REFUSED_BY_PROVIDER` instead. This bullet describes round 6
    as implemented at the time, not current behavior.
  - **Known scope boundary, named rather than silently absorbed:** `IntentClassificationResult`
    still carries no token/telemetry fields, so no `PassUsageSnapshot` is ever built for this pass
    and `TurnCostPolicy.compute_deduction()` never consumes the new `PASS_TIER_DEFAULTS` entry --
    classification's token cost is not yet included in hosted settlement. Widening
    `IntentClassificationResult` to carry usage was out of scope per the reviewer's own "avoid
    broad rewrites of Issue 7" guidance; flagged here for a future round rather than done silently.
  - Tests (`tests/pipeline/orchestrator/test_intent_classifier_routing.py`, new): classification
    uses the per-call override, never the constructor-default guard caller; the request carries
    `pass_id=INTENT_CLASSIFIER`; a BYOK-selected turn classifies successfully with
    `ANTHROPIC_API_KEY` unset (regression, monkeypatched absent); the BYOK-resolved adapter (not a
    hidden hosted one) receives the call; a hosted-selected turn still classifies via hosted
    resolver config; a provider refusal during classification still fails closed as
    `PIPELINE_ERROR`. `tests/api/test_fake_provider_product_path.py` gained an end-to-end test
    (real `create_app()` -> `build_orchestrator()` wiring, fake provider, `ANTHROPIC_API_KEY`
    unset) proving the fake-provider CI path classifies and delivers with no external calls.
    `tests/pipeline/orchestrator/conftest.py`'s `FakeIntentClassifier` test double widened to accept
    (and ignore) the new `model_caller` kwarg -- every orchestrator test using it would otherwise
    raise `TypeError` now that the orchestrator always passes it.

- **Settlement write failures preserve the delivered turn on every error class, not just one
  (P2).** `routes/turns.py` caught only `EntitlementSettlementError`, but
  `settle_hosted_turn_cost()` can also raise `EntitlementSettlementConflictError` (same `turn_id`,
  different deduction amount) and `EntitlementConcurrencyError` (optimistic-concurrency retries
  exhausted) -- either would have escaped as an uncaught exception, surfacing as an HTTP 500 and
  hiding an already-committed, delivered turn (a direct violation of "settlement failure survives
  the turn," Binding Decision 5 / DoR-D). `EntitlementIdempotencyConflictError` is also now caught:
  investigation confirmed it is not currently reachable from this call path (`settle_hosted_turn_cost`'s
  tail call to `receive_entitlement_event()` does not pass `idempotency_key`, and that error is only
  raised when one is supplied) -- included anyway as cheap, explicit forward-looking defense on the
  same settlement write path, per the reviewer's explicit "at minimum catch" list. Replay/payload-version
  errors were deliberately *not* added to the catch, since `settle_hosted_turn_cost()` cannot raise
  them.
  - Added a local `SETTLEMENT_WARNING_ERRORS` tuple alias (`routes/turns.py`) so future sibling
    catches are explicit, not implicit in a single `except` clause.
  - Behavior preserved exactly: structured error log (including `error_class`), non-blocking
    `settlement_warning` field, the successful `TurnSubmissionResponse` still returned, the
    delivered/OOC turn never rolled back or hidden.
  - Tests (`tests/api/test_turns.py`): each of the four error classes forced from a mocked
    `settle_hosted_turn_cost` (parametrized), verifying the HTTP response stays 200 with
    `settlement_warning` set and `turn_id`/disposition preserved, and that the structured log call
    includes the correct `error_class`. A separate test confirms an unrelated exception
    (`RuntimeError`) still surfaces as an internal error, not silently absorbed -- using a second
    `TestClient(raise_server_exceptions=False)` on the same app, since the default test client
    re-raises exceptions that `app.py`'s registered `Exception` handler already turned into a 500
    response (Starlette's `ServerErrorMiddleware` re-raises after building the handler response so
    ASGI servers/test clients can still observe it).

- **Packaged (wheel) launch no longer silently serves an API-only server while claiming to serve
  the frontend (P2) -- fail-loud deferral, not full asset packaging.** `_DEFAULT_FRONTEND_DIST`
  (`api/config.py`) is a repo-relative path (`parents[3]`) that does not exist under a
  site-packages install, and `app.py`'s mount is a bare `if dist.is_dir(): mount(...)` with no
  `else` -- a packaged `python -m afterworlds.main` would previously boot successfully with no
  warning while never actually serving the Issue 19 product UI.
  - **Direction chosen:** of the two reviewer-sanctioned options, fail loudly at launch rather than
    package frontend assets under the Python package this round. Full asset packaging needs a build/
    release-pipeline change (copying `frontend/dist` into `src/afterworlds/static/frontend/`,
    `pyproject.toml` package-data, `importlib.resources.files()` wiring), which is a larger,
    separable piece of work; more importantly, the sibling audit below found that packaging the
    frontend alone would not make a wheel install actually work, so partial packaging this round
    would have been misleading. Tracked as a follow-up, not silently deferred.
  - `load_settings()` (`api/config.py`) now raises a clear `RuntimeError` when
    `AFTERWORLDS_FRONTEND_DIST` is unset AND the default repo-relative path does not exist. An
    explicit override is always trusted as-is, even if that path doesn't exist yet at load time --
    an operator who sets it made a deliberate choice.
  - **Scoped to the production launch path only**, per explicit design intent: `create_app()`'s
    `settings.frontend_dist_dir.is_dir()` mount check and `ApiSettings`'s direct construction are
    both untouched. `main.py`'s bare `create_app()` (no settings passed) is the only real caller of
    `load_settings()` -- every test fixture and `scripts/dump_openapi_schema.py` already construct
    `ApiSettings` directly with a throwaway/nonexistent dist dir (by design, to avoid needing a
    real frontend build for backend-only tests), so none of them call `load_settings()` and none
    were affected.
  - Tests (`tests/api/test_config.py`, new): default resolves to the (mocked) default path when it
    exists; an explicit override is trusted even when that path is missing; missing default + no
    override raises `RuntimeError` mentioning `AFTERWORLDS_FRONTEND_DIST`; `create_app()` still
    mounts and serves `index.html` when the configured dist genuinely exists.

- **Sibling audit (CLAUDE.md gate, run before closing this round):**
  - *Direct model SDK calls in the product turn path* -- searched all `import anthropic`/
    `import openai` sites. `pipeline/provider/adapters/_anthropic.py` and `_openrouter.py` are the
    `ProviderAdapter` implementations themselves (legitimate). `pipeline/provider/credentials/
    _validator.py` validates a BYOK key's liveness at credential-save time, not a turn-path model
    call (legitimate, different concern). **Found and flagged, not touched:**
    `pipeline/{planner,contradiction,extractor,safety}/caller.py` each define an
    `Anthropic*Caller` class (`AnthropicPlannerCaller`, etc.) that constructs its own
    `anthropic.Anthropic()` client directly -- but grepping every reference to each class name
    confirms none is imported anywhere outside its own defining file, in `src/`, `tests/`, or
    `scripts/`. These four classes are dead code left over from before the Issue 14a
    `ProviderAdapter` refactor (each service's real product method only imports tool-name/tool-spec
    *constants* from the same `caller.py`, not the caller class). Not a live sibling of the
    classifier bypass -- it was never wired into the product path -- so `patched` does not apply;
    disposition: `out of scope` (dead-code removal is a separate, non-blocking cleanup, not part of
    this remediation round).
  - *Settlement exception catches* -- grepped every call site of `settle_hosted_turn_cost()`:
    `routes/turns.py` is the only caller. Disposition: `patched` (this round's P2 fix above).
  - *Other repo-relative runtime defaults that break in wheel installs* -- grepped all
    `Path(__file__).parents[N]` uses in `src/`. Beyond `api/config.py` (`patched` above), found:
    `api/db_bootstrap.py`'s `_REPO_ROOT` (locates `alembic.ini`/`alembic/` to run migrations -- would
    raise a clear file-not-found error under a wheel install, not silently misbehave, so lower
    severity than the frontend-dist defect but still repo-relative); and a `_PROMPT_DIR =
    Path(__file__).parents[N] / "docs" / "prompts"` pattern repeated in `services/context_builder.py`
    and `pipeline/{extractor,planner,orchestrator,contradiction,rpg,safety}/service.py` (seven
    files). Disposition for all of these: `out of scope` / `Known Unknown` -- fixing wheel
    packaging properly needs a single coherent packaging decision (bundle `docs/prompts` and
    `alembic/` as package data, or resolve them via `importlib.resources` like the deferred frontend
    packaging option above), not seven independent one-off patches. Recommended as a dedicated
    follow-up issue: "package Afterworlds for a proper wheel/pip install," scoped to cover the
    frontend dist, prompt files, and Alembic migration directory together.

- Gates on the exact branch head: `black`, `ruff`, `mypy --strict` (173 source files, no issues),
  `pytest -q` (2283 passed, 10 skipped, 91.88% coverage) for Python; `eslint --max-warnings=0`,
  `tsc --noEmit`, `vitest run` (22 passed), production `vite build` for the frontend (unaffected --
  no frontend files changed this round; run for gate completeness). `pip-audit` findings are
  pre-existing and unrelated to this round's changes (no dependencies added or changed). No API
  schema changes in this round, so no OpenAPI/TS regeneration was needed.

## Remediation round 7

Boundary note: this round's own classification named the defect families precisely (mode setup
completion parity; provider-refusal parity) rather than repeating a prior finding, so both were
implemented directly.

- **Branching structured setup now promotes play_status to IN_PLAY (P1) -- mirrors the Writing
  pattern exactly.** `apply_branching_config_update()` updated `interaction_style`/`branching_cadence`
  but never touched `play_status`, so a frontend-created Branching story could save both required
  fields, show fully configured visible state, and still have every subsequent turn treated as
  setup/prose forever -- the orchestrator's in-play Branching rails (`INTERACTION_REJECTED` for True
  CYOA freeform input, branch-choice validation) gate on `BranchingPlayStatus.IN_PLAY`, which could
  never be reached.
  - `apply_branching_config_update()` (`persistence/crud/session_state.py`) gained an optional
    `play_status: BranchingPlayStatus | None = None` parameter, mirroring
    `apply_writing_config_update()`'s existing `play_status` guard precisely: promotion only actually
    happens when the *effective* (post-field-update) row has both `interaction_style` and
    `branching_cadence` non-null -- not the incoming request body alone, since either field may
    already be persisted from an earlier partial setup call rather than supplied on this one. A
    non-`IN_PLAY` status is always applied unconditionally; only `IN_PLAY` is gated.
  - `_apply_branching_setup()` (`api/routes/setup.py`) now requests `play_status=BranchingPlayStatus.IN_PLAY`
    on every call, exactly as `_apply_writing_setup()` already does -- the CRUD-level guard, not the
    route, decides whether promotion actually applies. Idempotent: an already-`IN_PLAY` story is
    simply reassigned the same status.
  - Tests (`tests/api/test_setup.py`): both required fields present promotes to `IN_PLAY`; a partial
    setup call (one field only) does not promote; two successive partial calls (each supplying only
    the still-missing field) correctly promote using the effective persisted state, not either call's
    body in isolation; repeated setup calls after promotion remain idempotent.
  - Tests (`tests/api/test_fake_provider_product_path.py`): an end-to-end regression through the real
    HTTP setup route + a real turn submission -- a True CYOA story, once set up, correctly returns
    `INTERACTION_REJECTED` for freeform input instead of falling through to ordinary prose (this
    would have been impossible before the fix, since `play_status` could never reach `IN_PLAY` through
    the real route).
  - Tests (`tests/pipeline/orchestrator/test_service.py`, new `TestBranchingSetupPromotionReachesInPlayRails`):
    unlike every other Branching-rail test in this file (which hand-constructs `BranchingSessionState`
    directly), this one promotes state through the real `apply_branching_config_update()` call and
    reads it back through the real `get_branching_session_state_by_story` resolver, proving the actual
    persisted-state path -- not just an in-memory stand-in -- feeds the orchestrator's in-play
    branch-choice gate correctly.
  - **Sibling audit (setup completion parity across all three modes):** Writing already has this
    exact pattern (round 5). RPG's setup route (`_apply_rpg_setup`) never touches `play_status`, and
    grepping every write of `RpgPlayStatus.IN_PLAY` in `src/` found none -- `RpgSessionState`'s own
    docstring documents the intended transition condition explicitly: "`play_status` transitions from
    SETUP to IN_PLAY when the character sheet passes `D20RulesSystemAdapter.is_adjudicable()` and
    setup_phase reaches COMPLETE" -- a condition tied to RPG adjudication, which Issue 19's product
    wiring deliberately leaves unwired (Architecture Notes, prior rounds). Disposition: `Known
    Unknown` / `out of scope` -- RPG has an explicit, documented reason not to transition yet, not a
    silent gap; wiring RPG adjudication is a separate, larger piece of work. Also checked: the
    frontend's `StoryView.tsx` `structuredSetupPersisted` check for Branching already uses
    `visibleState !== null` as its completion signal (unlike Writing's explicit `play_status ===
    "in_play"` check) -- `build_visible_state()`'s Branching branch (`api/visible_state.py`) already
    returns `None` unless both `interaction_style` and `branching_cadence` are non-null, the exact
    same condition this round's backend fix uses to promote `play_status`. Disposition: `already safe`
    -- no frontend change needed, the existing signal was already semantically equivalent.

- **Provider refusals from Intent Classification now preserved, not collapsed into PIPELINE_ERROR
  (P2).** Once round 6 routed classification through the selected provider adapter, a content-policy
  refusal from that adapter surfaced as `ProviderRefusalError`, but the classification step's `except
  Exception` caught it along with every other failure and returned `PIPELINE_ERROR` -- dropping
  `provider_refusal` and making a content-policy decision look like an infrastructure failure, in
  tension with Architecture Invariant 5 ("Provider refusals are typed pass failures, not Safety
  verdicts").
  - `orchestrate_turn()`'s step 1 (`pipeline/orchestrator/service.py`) now catches `ProviderRefusalError`
    before the broad exception handler and returns `PipelineDisposition.REFUSED_BY_PROVIDER` via the
    same `_build_result(...)` pattern Planner/Writer/Extractor/Contradiction/RPG Adjudication/Branching
    Writer already use, with `provider_refusal=exc.refusal` populated. No real `IntentClassificationResult`
    exists yet at this point (classification itself failed), so `_synthesize_intent(user_input)` -- the
    same neutral placeholder every other pre-classification failure path already uses -- supplies
    `intent_classification`. All other classifier failures (parser/schema/transport/unexpected) still
    map to typed `PIPELINE_ERROR`, unchanged.
  - No hosted/BYOK boundary crossing was reintroduced: this is purely a catch-and-map change at the
    call site already wired to the per-turn `binding.adapter` since round 6; no new provider call path
    was added.
  - Tests (`tests/pipeline/orchestrator/test_intent_classifier_routing.py`): a classifier
    `ProviderRefusalError` now maps to `REFUSED_BY_PROVIDER` with `provider_refusal` populated,
    `pipeline_error_summary` absent, `turn_id`/`delivered_output` both `None` (the round-6 test that
    asserted the old `PIPELINE_ERROR` behavior was updated in place -- it exercised exactly the
    behavior this round intentionally changes); a non-refusal classifier error (plain `RuntimeError`)
    still maps to `PIPELINE_ERROR` with `provider_refusal` absent; a classifier refusal stops the turn
    immediately -- Planner/Writer/Extractor/Contradiction all recorded zero calls afterward.
  - **Sibling audit (`ProviderRefusalError` parity across every provider-backed pass):** grepped all
    `except ProviderRefusalError` sites in `pipeline/orchestrator/service.py` -- 9 total (Intent
    Classification, Planner, RPG Adjudication, Branching Writer, Writer ×2 call sites, Extractor,
    Contradiction ×2 for the parallel-pass path). Every site maps to `REFUSED_BY_PROVIDER` via
    `_build_result(...)` (or the parallel-path's `_ContradictionRefusalWithExtractor` wrapper, which
    preserves the same contract) with `provider_refusal` populated -- confirmed parity, no stragglers.
    Safety (`pipeline/safety/service.py`) is intentionally different: its `check()` wraps *all*
    exceptions, including `ProviderRefusalError`, into its own `SafetyPassError` (fail-closed by
    design, per its own docstring) rather than surfacing `REFUSED_BY_PROVIDER` -- this is the existing,
    correct divergence Architecture Invariant 5 describes (a Safety pass's own refusal is a Safety
    concern, not a narrative-pass refusal), not a defect. Disposition: `already safe`. Confirmed
    `ProviderCallError` (operational failures) cannot be misclassified as a refusal: it and
    `ProviderRefusalError` are sibling `Exception` subclasses, not parent/child, so the new
    `except ProviderRefusalError` clause structurally cannot catch a `ProviderCallError` -- it falls
    through to the unchanged broad `except Exception` → `PIPELINE_ERROR` path, verified by the
    non-refusal regression test above.

- Gates on the exact branch head: `black`, `ruff`, `mypy --strict` (173 source files, no issues),
  `pytest -q` (2291 passed, 10 skipped, 91.93% coverage). No frontend files changed this round, so
  frontend gates were not re-run. No API schema changes, so no OpenAPI/TS regeneration was needed.

### CI catch: Playwright E2E spine required a matching fix (again)

CI's `spine.spec.ts` failed after round 7 landed: `Branching mode: setup and a delivered turn` sets
both `interaction_style=true_cyoa` and `branching_cadence=interactive` during setup, which -- per
this round's P1 fix -- now genuinely promotes `play_status` to `IN_PLAY`. Its freeform submission
then correctly hit the orchestrator's True CYOA `INTERACTION_REJECTED` gate (pure core-dispatch
logic, never gated on `BranchingWriterService`/`BranchSelectionValidationService` despite the test's
own stale comment claiming otherwise) instead of falling through to the prose Writer path the test
asserted on -- that gate simply could never be reached through the real setup route before this
round's fix. Fixed by splitting into two tests: the original "delivered turn" coverage now uses
`FREEFORM_ONLY` (which never rejects freeform input); a new "True CYOA setup rejects freeform input"
test asserts the rejection banner text and that the draft is preserved (Binding Decision 6) --
closing exactly the gap the old comment flagged as untestable. Verified locally: full Playwright
suite (7/7 passing) against a fresh production build, matching CI's exact invocation.

## Remediation round 8

Boundary note (owner-supplied, preserved verbatim from the review comment): "Do not expand into
wiring BranchingWriterService unless the owner explicitly changes the current Issue 19 architecture
note. The narrow fix is to stop the minimal UI from defaulting users into an unwired interaction
style." All three fixes below respect this -- `BranchingWriterService` remains unwired, and the
orchestrator's fail-closed guard for in-play HYBRID/TRUE_CYOA with no branching writer is untouched.

- **Branching setup no longer defaults to unwired Hybrid (P1).** `BranchingSetupForm` defaulted
  `interactionStyle` to `"hybrid"`. That default was inert through round 6 (Branching could never
  reach `IN_PLAY`), but round 7's fix (setup now promotes to `IN_PLAY`) made it live: accepting the
  default setup created a story whose first Branching turn deterministically hit the orchestrator's
  fail-closed `PIPELINE_ERROR` ("branching writer service not wired for in-play HYBRID/TRUE_CYOA
  session").
  - `frontend/src/SetupForm.tsx`: `BranchingSetupForm`'s `interactionStyle` state now defaults to
    `"freeform_only"`.
  - Additional guard (required per the review comment -- "Do not rely only on a frontend default if
    the API can still create the same broken state"): the Hybrid and True CYOA `<option>` elements are
    now `disabled` with an "(unsupported in this build)" label, so a Sojourner cannot select them
    through the minimal UI at all. A server-side/API-level guard was deliberately **not** added on top
    of this: the orchestrator's existing fail-closed `PIPELINE_ERROR` for a direct API call configuring
    HYBRID/TRUE_CYOA is itself the correct backstop (the review comment affirms this: "Do not silently
    route HYBRID/TRUE_CYOA through the prose Writer; the orchestrator's fail-closed guard is correct"),
    and a route-level guard rejecting HYBRID/TRUE_CYOA setup would regress round 7 -- it would make the
    `INTERACTION_REJECTED` path unreachable again and break
    `test_true_cyoa_freeform_turn_after_setup_is_interaction_rejected`
    (`tests/api/test_fake_provider_product_path.py`), which configures True CYOA via HTTP and expects
    setup to succeed. Direct API configuration of HYBRID/TRUE_CYOA remaining possible (and failing
    closed on the first turn, not silently) is treated here as an intentional boundary of this fix, not
    a residual defect -- flagged explicitly rather than resolved silently, per CLAUDE.md's Known
    Unknown rule.
  - Tests (`frontend/src/StoryView.test.tsx`, new describe block): the Branching setup form's
    interaction-style select defaults to `freeform_only` with Hybrid/True CYOA options disabled;
    submitting without changes sends `interaction_style: "freeform_only"` to `submitSetup`.
  - Tests (`frontend/e2e/spine.spec.ts`): the prior round-7 "True CYOA setup rejects freeform input"
    E2E test could no longer exercise the True CYOA path through the UI once its `<select>` option
    became disabled (a real collision, caught locally before pushing rather than by a second CI
    failure) -- converted in place to "Hybrid and True CYOA are unsupported and not selectable",
    asserting the default and both disabled options. The `INTERACTION_REJECTED` coverage this test used
    to provide still lives at the API level
    (`test_true_cyoa_freeform_turn_after_setup_is_interaction_rejected`), so no coverage was lost, only
    relocated to the layer that can still reach it. Playwright's `toBeDisabled()` does not evaluate an
    `<option>` element's own `disabled` DOM property (options aren't independently "actionable"), so
    the assertion uses `toHaveJSProperty("disabled", true)` instead -- discovered by a local run
    failing with `Received: enabled` against a manually-confirmed-disabled element.

- **Branch-card clicks now submit resolver-supported tokens instead of free-text labels (P2).**
  `VisibleStatePanel`'s branch-card `onClick` submitted `` `I choose: ${opt.action_text}` ``.
  `BranchSelectionValidationService` resolves only exact `opt_N`, explicit `"option/choice N"`,
  ordinal words, or a bare operative number -- never a free-text action label -- so every UI
  branch-card click became `INVALID_BRANCH_SELECTION`.
  - `frontend/src/VisibleStatePanel.tsx`: added `branchSelectionToken(optionId)`, which derives `N`
    from an `opt_N`-shaped `option_id` and returns `"I choose option N."` (matches
    `_EXPLICIT_NUM_RE`), falling back to `` `I choose ${optionId}.` `` (matches `_OPT_ID_RE`) if the
    id doesn't match that shape. The branch-card `onClick` now calls this instead of echoing
    `action_text`. The displayed button label is unchanged (`opt.action_text`) -- only the submitted
    payload changed. The `onBranchOptionClick` prop parameter was renamed from `actionText` to
    `selectionText` to match what it now actually carries.
  - Tests (`frontend/src/VisibleStatePanel.test.tsx`, new file): clicking a branch card with
    `option_id: "opt_2"` submits a string containing `option 2`/`opt_2`, not the action label
    (regression test that it no longer submits `"Climb the wall."` or the old `"I choose: ..."`
    shape); the displayed button label stays `action_text`; a non-`opt_N` id falls back to
    `"I choose {id}."`.

- **Request DTOs now carry `schema_version`, matching every response DTO (P2).** `dto.py`'s own module
  docstring already claimed every DTO carries `schema_version: Literal[1]` (Binding Decision 9), but
  this was only true for the 10 response DTOs -- none of the 5 request DTOs had it, so clients had no
  way to send a version and the contract was one-sided.
  - `src/afterworlds/api/dto.py`: added `schema_version: Literal[1] = 1` to `CreateStoryRequest`,
    `TurnSubmissionRequest`, `RpgSetupRequest`, `BranchingSetupRequest`, and `WritingSetupRequest` --
    the exact field/type/default already used on every response DTO. `extra="forbid"` is unchanged on
    all five; the `SetupRequest` discriminated union still keys on `mode`, unaffected by adding a
    sibling field.
  - **Sibling audit (all request-shaped DTOs, not only the three named in the review comment):**
    grepped every FastAPI route handler signature across `api/routes/*.py` for a non-path/query body
    parameter. Confirmed exactly 3 POST routes exist (`POST /api/stories`, `POST
    .../{story_id}/setup`, `POST .../{story_id}/turns`), consuming exactly the 5 DTOs above (the setup
    route via the `SetupRequest` union) -- no 6th request DTO exists. The other embedded/nested DTOs in
    `dto.py` (`ProviderRefusalSummaryDTO`, `RpgSetupStateDTO`, `BranchingSetupStateDTO`,
    `WritingSetupStateDTO`, `PersonaDTO`, `TranscriptTurnDTO`) are never deserialized directly from a
    client request body -- they're embedded inside response envelopes -- so versioning them as
    "requests" would be a category error; disposition `out of scope`, not a gap.
  - Tests (`tests/api/test_request_schema_version.py`, new file): each of the 5 request DTOs, exercised
    through the real HTTP routes, accepts an omitted `schema_version` (defaults to 1), accepts an
    explicit `schema_version: 1`, and rejects `schema_version: 2` through the existing
    `VALIDATION_FAILED` envelope (not a bespoke error shape) -- 15 tests total.
  - OpenAPI/TS regenerated (`npm run generate-api-types`) since request schemas changed, per this
    round's run gates. `frontend/src/api/schema.ts` diff is exactly the 5 new `schema_version` fields
    (plus their read-only `*StateDTO` mirrors, which are generated from the same route's response
    model and were not hand-edited). `npm run check-api-types-drift` confirmed no further drift after
    committing.
  - **Frontend call-site sibling audit (per the review comment's own instruction to check generated
    types and call sites after regeneration):** openapi-typescript renders `schema_version: 1` as a
    *required* field on request types (not optional, despite the Pydantic-side default) because it
    treats single-value `const`/`Literal` fields as always-present regardless of the OpenAPI `required`
    list -- discovered via a `tsc --noEmit` failure after regeneration, not assumed. This broke three
    call sites statically typed against the generated request types: `StoryList.tsx`'s `createStory`
    call and all three `SetupForm.tsx` `onSubmit(...)` calls (RPG/Branching/Writing). Fixed by adding
    `schema_version: 1` explicitly at each of those four call sites. `client.ts`'s `submitTurn` builds
    its body as an untyped inline object literal (never statically checked against
    `TurnSubmissionRequest`), so it was not forced by the compiler -- `schema_version: 1` was added
    there too anyway, for consistency across all five request bodies rather than leaving one silently
    diverging from the other four's explicit-`1` behavior.

- Gates on the exact branch head: `black`, `ruff`, `mypy --strict` (173 source files, no issues),
  `pytest -q` (2307 passed, 10 skipped, 91.93% coverage, up from 2291/91.93% -- the 15 new
  `test_request_schema_version.py` tests plus one more pulled in by the round-7 baseline). Frontend:
  `tsc --noEmit`, ESLint, Prettier, Vitest (27 passed), `npm audit --audit-level=high` (0
  vulnerabilities), production build, and the full Playwright E2E spine (7/7 passing) against a fresh
  build -- all clean. OpenAPI/TS regenerated and drift-checked as noted above.

## Remediation round 9

Two concrete defects (P2, P2) -- no boundary/ownership fork this round.

- **Writing visible-state lookup failure is now non-fatal (P2).** `build_visible_state()`'s own module
  docstring claims it "never raises," but the Writing branch only guarded `writing_state is None` and
  `writing_state.persona_id is None` before calling `WritingVisibleStateService.build()`, which also
  raises `ValueError` when a persisted `persona_id` no longer resolves in the current persona registry
  (e.g. the persona catalog changed after this story's setup ran). `build_visible_state()` is called
  from three routes (`GET .../visible-state`, `GET .../setup`, and `POST .../turns`'s
  post-orchestration re-fetch); an unguarded raise there surfaces as an unhandled 500.
  - `src/afterworlds/api/visible_state.py`: the Writing branch now catches `ValueError` around the
    `WritingVisibleStateService(...).build(writing_state)` call and returns `None`, logging a warning
    with `story_id`, `mode`, and the exception's class name only -- no persisted content (goals,
    persona fields) is logged. Matches the module's own documented "never raises" contract, which was
    previously false for this one path.
  - Tests (`tests/api/test_visible_state.py`, new): a Writing story with a persisted `persona_id` that
    doesn't resolve in the registry (simulated by mutating the persisted row directly, since the real
    setup route validates against the live registry and would reject it) -- `GET .../visible-state`
    returns `200` with `visible_state: null`, not a 500. A valid persona (`chiron`) still returns the
    normal populated `WritingVisibleState` (existing test, unaffected).
  - Tests (`tests/api/test_fake_provider_product_path.py`, new): `POST .../turns` for a story whose
    Writing session has a stale `persona_id` still returns `200` with `disposition: delivered` and
    `visible_state: null`, not a 500. This required a SETUP-phase-with-persona-already-set fixture
    shape (also only reachable via direct persistence, not the real setup route, which always sets
    `persona_id` and `specific_goals` together and promotes straight to `IN_PLAY`) -- discovered while
    writing the test that the orchestrator (`pipeline/orchestrator/service.py` step 2c) has its own,
    independent persona-registry guard that already fails closed with `PIPELINE_ERROR` (no turn
    created) for IN_PLAY Writing turns with an unresolvable `persona_id`, so the exact "turn delivered,
    then visible-state crashes" scenario is only reachable for a SETUP-phase turn, where that guard
    doesn't fire (it's gated on `play_status is IN_PLAY`) but `build_visible_state()`'s own weaker
    precondition (`persona_id is None`) doesn't cover a persona set-but-stale row either. The fix in
    `visible_state.py` protects this path regardless of which route reaches it.
  - **Sibling audit (stale-registry/stale-config visible-state build failures across all three
    modes):** `RpgVisibleStateService.build()` takes a plain, already-fetched `Dnd5eCharacterSheet` row
    and does no external registry/catalog lookup -- no equivalent failure mode exists; disposition
    `already safe`. `BranchingVisibleStateService.build()` raises `ValueError` only for
    `interaction_style is None` / `branching_cadence is None`, but `build_visible_state()`'s own
    Branching branch already checks both of those exact conditions before calling `build()` (confirmed
    by re-reading, not assumed) -- the raise is structurally unreachable through this call site;
    disposition `already safe`. Only Writing has an external-catalog dependency
    (`JsonPersonaRegistry`) that can drift independently of the persisted session-state row, which is
    exactly why only Writing needed a fix.

- **Setup-state union members now carry `schema_version` (P2).** `SetupStateResponse` (the envelope)
  already had `schema_version`, but its three discriminated-union members --
  `RpgSetupStateDTO`, `BranchingSetupStateDTO`, `WritingSetupStateDTO` -- did not, inconsistent with
  every other DTO in `dto.py` (all ten response DTOs plus, as of round 8, all five request DTOs).
  - `src/afterworlds/api/dto.py`: added `schema_version: Literal[1] = 1` to all three. `extra="forbid"`
    and the `mode` discriminator are unchanged. Confirmed all three construction sites
    (`api/routes/setup.py`'s `_build_setup_state` function) never pass `schema_version`
    explicitly, so every response relies on the default -- no call-site changes needed.
  - Tests (`tests/api/test_setup.py`, new): `GET /api/stories/{story_id}/setup` returns
    `setup_state.schema_version === 1` for a freshly-created story in each of the three modes (RPG,
    Branching, Writing).
  - OpenAPI/TS regenerated (`npm run generate-api-types`); diff is exactly the three new
    `schema_version` fields on the generated `RpgSetupStateDTO`/`BranchingSetupStateDTO`/
    `WritingSetupStateDTO` types. These are response-only types (never constructed client-side), so
    unlike round 8's request-DTO regeneration, no frontend call sites needed updating --
    `tsc --noEmit` was clean immediately after regeneration, confirmed rather than assumed.

- Gates on the exact branch head: `black`, `ruff`, `mypy --strict` (173 source files, no issues),
  `pytest -q` (2310 passed, 10 skipped, 91.96% coverage, up from 2307/91.93% -- 3 new tests: one
  Writing-visible-state-stale-registry test, one POST-turns non-500 regression test, one setup-state
  schema_version test across all three modes). Frontend: `tsc --noEmit`, ESLint, Prettier, Vitest (27
  passed, unchanged), `npm audit --audit-level=high` (0 vulnerabilities), production build, and the
  full Playwright E2E spine (7/7 passing) against a fresh build -- all clean. OpenAPI/TS regenerated
  and drift-checked.

## Remediation round 10

One P1 and two P2s. The DTO-versioning comment includes an explicit sibling-audit-gate note (rounds
8-9 each added `schema_version` to a named subset of DTOs and each round missed a sibling class) --
addressed by a full enumeration, not another named-subset patch, plus a standing test that fails on
any future omission.

- **BYOK readiness failure no longer blocks hosted access (P1).** `_submit_turn_sync()`
  (`api/routes/turns.py`) called `byok_readiness_provider.is_byok_runnable(sojourner_id)` unguarded.
  `ByokCredentialReadinessProvider.is_byok_runnable()`'s own docstring claims it "never raises," but
  `_collect_available_byok_keys()` (`pipeline/provider/_readiness.py`) calls
  `credential_store.get(sojourner_id, provider_name)` with no `try/except` around it -- a
  keyring/credential-retrieval failure propagates uncaught. For a Sojourner with both hosted and BYOK
  access, this turned a should-succeed hosted turn into an unhandled 500 instead of silently falling
  back to hosted.
  - `api/routes/turns.py`: wrapped only the `is_byok_runnable(...)` call in `try/except Exception`;
    on failure, logs a structured warning (`sojourner_id`, `story_id`, `error_class` only -- no raw
    credentials, provider secrets, key names, or keyring payloads) and treats `byok_ready = False`,
    then proceeds through `select_access_path(status, byok_ready)` exactly as before. Entitlement
    state is untouched; this route does not mark BYOK credentials invalid (not its ownership) --
    matches the review comment's suggested shape exactly.
  - Tests (`tests/api/test_turns.py`, new): hosted available + BYOK readiness raises -- still selects
    hosted (`access_path.value == "hosted"`), turn delivers, no 500. Hosted unavailable + BYOK
    readiness raises -- returns the normal typed `entitlement_blocked` 403, not a 500. A warning-log
    test spies on the route module's logger directly (not `caplog` -- `_submit_turn_sync` runs on a
    worker thread, and `caplog`'s handler attachment is not reliably observed across that boundary,
    per the existing pattern in `test_each_settlement_write_failure_survives_turn`) and asserts the
    logged `extra` carries only `sojourner_id`/`story_id`/`error_class`, with the raised exception's
    own message text confirmed absent from the log.
  - Not touched: `_readiness.py`'s own "never raises" docstring is technically inaccurate (the
    unguarded `credential_store.get(...)` call can raise), but the review comment scopes the required
    fix to the route-level pre-selection probe only ("This fix is only for the pre-selection readiness
    probe") -- flagged here as a residual note, not fixed, since patching `_readiness.py` itself was
    out of the requested scope and touches the shared predicate `ProviderResolver._resolve_byok` also
    depends on (which *is* supposed to raise, per its own docstring).

- **Identity ORM registered with Alembic metadata (P2).** `SojournerIdentityORM`
  (`persistence/orm/identity.py`, `sojourner_identity` table) was never imported by `alembic/env.py`,
  so `Base.metadata` was populated only when something else happened to import the module first (true
  in every current test/app path, which is why this was latent, not currently broken) -- a future
  `alembic revision --autogenerate` would see `sojourner_identity` as unmanaged and could emit a
  destructive DROP. The table itself is already covered by migration 0016 (DoR-A, CRD Issue 19); this
  is purely an autogenerate-tracking fix, not a new migration.
  - `alembic/env.py`: added `import afterworlds.persistence.orm.identity  # noqa: F401` alongside the
    other ORM imports.
  - Verified manually (no established repo command for this): ran `alembic revision --autogenerate`
    against a fresh throwaway DB at `main` migration head -- the generated diff does not mention
    `sojourner_identity` at all (confirmed by grep, not assumed), only pre-existing, unrelated
    SQLite-vs-model cosmetic drift (index-name / UUID-column-type differences on other tables, present
    before this change). The throwaway migration file was deleted, not committed.
  - Sibling audit: compared every `persistence/orm/*.py` (+ `entitlement/orm.py`) module against
    `alembic/env.py`'s import list -- `identity` was the only gap; every other ORM module was already
    imported. (`pipeline/provider/normalization.py` matched a naive path grep for "orm" but is not an
    ORM module -- no `Base` subclass, no `__tablename__` -- confirmed, not assumed.)
  - Tests (`tests/api/test_identity.py`, new): `test_sojourner_identity_table_in_base_metadata`
    mirrors the existing `test_provider_tables_in_base_metadata`
    (`tests/pipeline/provider/test_migration.py`) pattern from the CRD Issue 14a provider-tables fix
    for the same defect family (ORM module never imported by `alembic/env.py`) -- a recurring defect
    shape in this codebase, now covered for identity too by a standing assertion.

- **Every public API DTO now carries `schema_version` (P2).** Rounds 8 and 9 each added
  `schema_version` to a named subset (5 request DTOs; 3 setup-state union members) and each round's
  own fix missed a sibling class still lacking it: `ProviderRefusalSummaryDTO`, `PersonaDTO`,
  `TranscriptTurnDTO` -- all embedded response items, never top-level request/response bodies
  themselves, which is presumably why they were missed by the narrower "request DTO" / "setup-state
  union" framing of the prior two rounds.
  - `src/afterworlds/api/dto.py`: added `schema_version: Literal[1] = 1` to all three. `extra="forbid"`
    unchanged. Confirmed all three construction sites (`routes/personas.py`'s `_to_dto`,
    `routes/turns.py`'s `provider_refusal_dto`/`TranscriptTurnDTO` list comprehension) never pass
    `schema_version` explicitly -- every response relies on the default.
  - **Full enumeration, not another named-subset patch:** hand-audited every `class X(BaseModel)` in
    `dto.py` (21 total) against the review comment's instruction to check "every remaining `BaseModel`"
    -- confirmed these were the only 3 gaps left after rounds 8-9.
  - Added `tests/api/test_dto_versioning.py` (new file): enumerates every `BaseModel` subclass actually
    *defined* in `dto.py` (via `obj.__module__ == dto_module.__name__`, so imported models like
    `RpgVisibleState` aren't swept in) and fails if any lacks `schema_version` -- with a local,
    currently-empty `_EXEMPT` set for any future deliberate exception, so a class can only skip
    versioning with an explicit, reviewable justification in this file, not by silent omission. Also
    asserts the field is exactly `Literal[1]` defaulting to `1` on every DTO (not just present), and
    that the `SetupRequest` union members still key on `mode`. This closes the sibling-audit-gate
    CLAUDE.md flagged: a third round hitting the same defect family (DTO versioning) now gets a
    standing regression test instead of a fourth manual audit.
  - Tests (`tests/api/test_personas.py`, `tests/api/test_transcript.py`, `tests/api/test_turns.py`,
    new): `GET /api/personas` gallery items carry `schema_version: 1`; `GET .../turns` transcript items
    carry it; a `POST .../turns` response with a populated `provider_refusal` (via a new
    `make_refused_by_provider_result()` fixture in `tests/api/_fixtures.py`) carries it on the embedded
    `provider_refusal` object.
  - OpenAPI/TS regenerated; diff is exactly the 3 new `schema_version` fields on `PersonaDTO`,
    `ProviderRefusalSummaryDTO`, `TranscriptTurnDTO`. All three are embedded response types (never
    constructed client-side), so -- matching round 9, unlike round 8 -- no frontend call sites needed
    updating; `tsc --noEmit` confirmed clean immediately after regeneration.

- Gates on the exact branch head: `black`, `ruff`, `mypy --strict` (173 source files, no issues),
  `pytest -q` (2320 passed, 10 skipped, 91.97% coverage, up from 2310/91.96% -- 10 new tests: 3 BYOK
  readiness tests, 1 turn-response provider_refusal schema_version test, 1 identity-metadata test, 1
  personas schema_version test, 1 transcript schema_version test, 3 DTO-enumeration tests). Frontend:
  `tsc --noEmit`, ESLint, Prettier, Vitest (27 passed, unchanged), `npm audit --audit-level=high` (0
  vulnerabilities), production build, and the full Playwright E2E spine (7/7 passing) against a fresh
  build -- all clean. OpenAPI/TS regenerated and drift-checked as noted above.

## Remediation round 11

Two P2s, both classified as valid product-path defects requiring no owner decision.

- **Transcript refresh now shows the latest turns, not always the first page (P2).**
  `GET /api/stories/{story_id}/turns` defaulted to `limit=50&offset=0`, and
  `list_turns_by_story()` orders oldest-first -- once a story passed 50 turns, every refresh
  (including the one immediately after submitting turn 51) re-fetched the *first* 50 turns, so a
  newly delivered turn was correctly persisted but never became visible without manual pagination.
  - `persistence/crud/node.py`: `list_turns_by_story()` gained `newest_first: bool = False`. When
    `True`, it queries newest-first internally (`ORDER BY timestamp DESC`), applies `limit`/`offset`
    to select from the *end* of the transcript, then reverses the page back to chronological order
    before returning -- callers always see oldest-to-newest within the page either way. Existing
    oldest-first callers (no `newest_first` arg) are untouched.
  - `api/routes/turns.py`: `GET .../turns` gained a `latest: bool = False` query parameter, per the
    review comment's preferred implementation (not the total-count-pagination alternative, which was
    explicitly more surface area than needed here). `latest=true` calls
    `list_turns_by_story(..., newest_first=True)`; `offset` is rejected with a typed 422 when combined
    with `latest=true` (the two pagination modes have different meanings for "offset" and mixing them
    would be ambiguous) -- explicit `limit`/`offset` pagination without `latest` is completely
    unchanged, preserving it for backfill.
  - `frontend/src/api/client.ts`: added `api.getLatestTranscript(storyId, limit)` (additive, not a
    signature change to `getTranscript`) calling `.../turns?limit=...&latest=true`.
  - `frontend/src/StoryView.tsx`: both `refresh()` (shared by initial load, the Retry button, and
    setup-completion handoff) and the post-submit refresh now call `getLatestTranscript` instead of
    `getTranscript` -- the play view shows the latest page from first load, not only after a
    resubmission happens to trigger a refresh.
  - Rejected alternative: raising the frontend's page size (e.g. to 200) was explicitly named in the
    review comment as *not* a fix -- it only raises the turn count at which the bug reappears, not
    fixes the ordering defect itself. Not attempted.
  - Tests (`tests/api/test_transcript.py`, new): 60 seeded turns, `limit=50&latest=true` returns
    exactly turns 11-60 in chronological order (not turns 1-50); a 51st turn is the last item on the
    very next `latest=true` page (the review comment's own named regression scenario); `latest=true`
    with a nonzero `offset` returns a typed 422; explicit `limit`/`offset` pagination without `latest`
    is unchanged (verified against the same seeded data).
  - OpenAPI/TS regenerated; diff is exactly the new `latest?: boolean` query parameter on the
    transcript GET operation.

- **Mutation success is now separated from post-submit refresh failure (P2).** `StoryView.submitTurn()`
  wrapped `api.submitTurn(...)` and the follow-up transcript/visible-state refresh in one `try/catch`
  -- a refresh failure (the turn already succeeded and was persisted) surfaced through the same
  `turnError` path as an actual submission failure, misreporting a successful turn as failed and
  offering no way to recover without re-submitting.
  - `frontend/src/StoryView.tsx`: split into two boundaries. The outer `try/catch` now covers only
    `api.submitTurn(...)` -- a failure there means the turn was never persisted, so `turnError` and
    draft preservation are unchanged from before. On success, `lastResponse` is set and the draft
    clears only for `delivered`/`ooc_handled` exactly as before, then a new
    `refreshTranscriptAndVisibleState()` helper (its own internal `try/catch`) runs unconditionally.
    Its failure sets a new `refreshError` state -- never `turnError` -- with a `Retry` button that
    re-runs the same helper without re-submitting the turn. A failed refresh leaves the prior
    transcript/visible-state untouched (not reset to empty), since `refreshTranscriptAndVisibleState`
    only calls `setTurns`/`setVisibleState` after both reads succeed.
  - **Sibling audit (mutation success / follow-up read coupling in other frontend flows):** grepped
    every `async function` with a `try` block across `frontend/src/*.tsx`. Found one sibling:
    `SetupForm`'s `submit()` calls `onComplete()` only after `api.submitSetup(...)` already succeeded;
    `StoryView`'s `onComplete` callback called `refresh()` without awaiting or catching it -- a refresh
    failure there was an unhandled promise rejection, not merely a shared-catch-block misreport (a
    different failure mode in the same defect family, arguably worse since nothing was surfaced to the
    user at all). Disposition: `patched`, minimally -- `onComplete` now awaits `refresh()` and routes
    any failure into the same `refreshError` state/Retry button the main fix added, reusing the
    existing surface rather than inventing a second one (the review comment's own scope boundary: "do
    not broaden into full offline queue/retry UX"). No other `try` blocks in the frontend combine a
    mutation with a follow-up read.
  - Tests (`frontend/src/StoryView.test.tsx`, new describe block): POST failure keeps the draft, shows
    `turnError`, and never calls the refresh path (`getLatestTranscript` called exactly once, from
    initial load only). POST success + refresh success clears the draft and shows no error. POST
    success + refresh failure still clears the draft (disposition-driven, not refresh-outcome-driven),
    preserves the prior transcript, and shows a refresh-specific error that never contains "submission
    failed" wording. The refresh-retry button recovers without incrementing `submitTurn`'s call count.
    A fifth test covers the `SetupForm`-`onComplete` sibling directly. (This suite needed
    `vi.clearAllMocks()` in its own `beforeEach` -- the file's shared `vi.hoisted` mocks don't reset
    call counts between tests, which no prior test in this file had asserted on until now.)

- Gates on the exact branch head: `black`, `ruff`, `mypy --strict` (173 source files, no issues),
  `pytest -q` (2324 passed, 10 skipped, 91.97% coverage, up from 2320/91.97% -- 4 new
  `test_transcript.py` tests). Frontend: `tsc --noEmit`, ESLint, Prettier, Vitest (32 passed, up from
  27 -- 5 new `StoryView.test.tsx` tests), `npm audit --audit-level=high` (0 vulnerabilities),
  production build, and the full Playwright E2E spine (7/7 passing) against a fresh build -- all
  clean. OpenAPI/TS regenerated and drift-checked.

## Remediation round 12

Two P2s, both classified as valid and in scope for Issue 19, requiring no owner decision.

- **RPG setup saves are now blocked until hydration finishes (P2).** `RpgSetupForm` initialized
  `diceHandling`/`tone` to hardcoded defaults (`ai_rolls`/`balanced`), then asynchronously hydrated
  them from `GET .../setup` -- but the Save button was enabled the entire time that request was in
  flight, and its failure was silently swallowed (`.catch(() => {})`). A quick Save right after reload
  could submit the hardcoded defaults and overwrite persisted non-default setup (e.g.
  `player_rolls`/`gritty`) before hydration ever applied it.
  - `frontend/src/SetupForm.tsx`: `RpgSetupForm` gained `hydrationStatus: "loading" | "ready" |
    "error"`, starting at `"loading"`. The hydration effect (extracted into a named `hydrate`
    function so a Retry button can re-invoke it) sets `"ready"` after applying whatever persisted
    values exist (or none, for a brand-new story), or `"error"` on failure -- no longer silently
    swallowed. The Save button's `disabled` condition is now `submitting || hydrationStatus !==
    "ready"`. On `"error"`, a visible message ("Could not load saved RPG setup. Retry before saving.")
    with its own Retry button is shown; Save stays disabled until a retry succeeds.
  - Tests (`frontend/src/StoryView.test.tsx`, new, in the existing RPG-setup-reload describe block):
    Save is disabled while `getSetupState()` is still pending (a never-resolving promise). A
    regression test drives the exact reported scenario -- clicking Save while hydration is pending
    submits nothing (`submitSetup` not called), then after hydration resolves to
    `player_rolls`/`gritty`, Save becomes enabled and submits those persisted values, never the
    defaults. A hydration-failure test confirms Save stays disabled with the visible error text, and
    that clicking its Retry button (a successful second `getSetupState()` call) clears the error and
    enables Save.
  - This suite's `beforeEach` needed `vi.clearAllMocks()` for the same reason round 11's did (call-count
    assertions against this file's shared, never-auto-reset `vi.hoisted` mocks).

- **E2E database is now isolated per run (P2).** `playwright.config.ts` and `e2e/seed-entitlement.ts`
  each separately hardcoded `sqlite:///./_e2e.db` -- two independent literals, not one source of
  truth, exactly what the sibling-audit instruction asked to check for. Tests seeding hosted
  entitlement mutated the same fixed repo-local database file that the "fresh install, no runnable
  access path" test depended on being empty; a local rerun, a partial run, or a prior failed run left
  entitlement state behind and could silently invalidate that scenario regardless of test order.
  - Went with the review comment's **preferred** option (a wrapper script), not the "acceptable"
    delete-before-start option, after the first attempt at the acceptable-tier fix (computing the
    per-run path directly at the top of `playwright.config.ts`) demonstrably failed: Playwright
    reloads `playwright.config.ts` once per worker process, so a top-level `mkdtempSync()` there
    produces a *different* temp directory per worker than the one the webServer process got --
    verified empirically (not assumed) by a failing first run: the seed script connected to a
    directory the webServer's Alembic migrations had never touched (`sqlite3.OperationalError: no
    such table: sojourner_identity`).
  - `frontend/e2e/run-isolated.mjs` (new): computes one unique temp directory
    (`mkdtempSync(tmpdir())`) exactly once, then spawns `playwright test` (plus any passthrough CLI
    args) as a child process with `AFTERWORLDS_DATABASE_URL`/`AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY`
    set on its env -- every descendant process (the webServer Playwright itself spawns, and every test
    worker) inherits the same values via ordinary OS process-env inheritance, sidestepping Playwright's
    internal config-reload semantics entirely rather than fighting them.
  - A second bug surfaced while verifying: `spawnSync` with `shell: true` and array-form `args` does
    not reliably re-quote an argument containing a space for the Windows shell it spawns (a `--grep
    "delivered turn"` pattern silently split into two argv entries, `No tests found`). Fixed by
    building one pre-quoted command string instead of an args array -- the documented-safe pattern for
    `shell: true` -- and verified the exact failing repro (`--grep "delivered turn"`) resolves
    correctly to 2 matching tests afterward.
  - `frontend/playwright.config.ts`: now reads `AFTERWORLDS_DATABASE_URL`/
    `AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY` from `process.env` (set by the wrapper), falling back to
    its own unique temp path only for the unsupported direct-invocation case (`npx playwright test`,
    bypassing the wrapper) -- documented in-file as best-effort/non-guaranteed-consistent-across-workers
    for that fallback path specifically, since direct invocation is no longer the supported entry
    point.
  - `frontend/e2e/seed-entitlement.ts`: reads `process.env.AFTERWORLDS_DATABASE_URL` instead of
    duplicating the literal; throws a clear, actionable error if unset (rather than silently using a
    wrong/stale path) so a future direct-invocation regression fails loudly instead of quietly
    reintroducing shared state.
  - `frontend/package.json`: `"e2e"` script changed from `playwright test` to `node
    e2e/run-isolated.mjs`. `.github/workflows/ci.yml`: the E2E job's `run: npx playwright test` step
    changed to `run: npm run e2e` -- CI must go through the wrapper too, not just local runs.
  - **Sibling audit (per the review comment's own instruction):** grepped every `_e2e.db`/`_e2e_chroma`
    literal across the repo (excluding `node_modules`) -- found exactly the two named above, both now
    replaced by the single `run-isolated.mjs` source of truth; no third hardcoded reference exists.
    `scripts/seed_e2e_entitlement.py`'s `--db-url` is a required CLI argument with no hardcoded
    default -- disposition `already safe`, it was never part of the duplication. `.gitignore`'s
    `_e2e.db*`/`_e2e_chroma/` entries are left in place as harmless legacy coverage (the fallback path
    could still theoretically write there if literally nothing else changes about how someone invokes
    Playwright, though in practice it now always resolves to an OS temp directory) -- not removed,
    since leaving an unused ignore pattern carries no cost and removing it isn't part of the requested
    fix.
  - Tests/checks (all run manually per the review comment's own list, empirically, not assumed):
    full Playwright suite run twice in a row via `npm run e2e` -- both runs 7/7 green, each with a
    distinct seeded sojourner id, confirming no shared state; `entitlement-blocked` run standalone via
    `npm run e2e -- --grep "entitlement-blocked"` immediately after two prior seeded runs still saw no
    runnable access path; a seeded-only filtered run (`--grep "delivered turn"`) still received hosted
    entitlement correctly; confirmed zero `_e2e.db`/`_e2e_chroma` artifacts exist anywhere in the repo
    tree after multiple runs (`ls` came back empty at both the repo root and `frontend/`).

- Gates on the exact branch head: frontend `tsc --noEmit`, ESLint, Prettier, Vitest (35 passed, up from
  32 -- 3 new `StoryView.test.tsx` tests), `npm audit --audit-level=high` (0 vulnerabilities),
  production build, and the full Playwright E2E spine run twice via `npm run e2e` (7/7 passing both
  times) -- all clean. No backend/API code changed this round, so `black`/`ruff`/`mypy`/`pytest` were
  not re-run (per the review comment's own run-gates instruction: "backend tests only if helper
  scripts or API behavior changed"). No OpenAPI/TS schema changes.

## Remediation round 13

A review-loop boundary problem (a genuine architecture contradiction between two prior owner
decisions, not an ordinary next patch) plus one concrete P2, classified and handled per CLAUDE.md's
boundary rule: paused before patching, surfaced the fork to the owner, waited for the decision, then
implemented exactly what was chosen -- no scope drift into fixing it in code first and asking after.

- **Writing `play_status` promotion vs. ADR-017 Decision 9 setup-confirmation semantics (P1,
  boundary decision).** Round 5 made `POST /setup` promote Writing `play_status` straight to
  `IN_PLAY` once `persona_id`/`specific_goals` were both persisted (an owner decision at the time).
  Codex's round-13 review correctly identified that this contradicts two things simultaneously: (1)
  ADR-017 Decision 9 / ADR-018 D6, which require the turn taken *while `play_status` is still
  SETUP* to be classified `SETUP_CONFIRMATION`/`NON_CANON_SUPPORT`, not ordinary prose -- an
  orchestrator guard (`_narrative_persist`, `if _wss.play_status is WritingPlayStatus.SETUP: ...`)
  that existed specifically to enforce this, made permanently unreachable for Writing by round 5's
  immediate promotion; and (2) the PR body's own (accurate, at the time) Architecture Notes claim
  that "Setup route writes structured config only... never advances play_status/setup_phase
  itself" -- true for RPG and (structurally, for different reasons) Branching, but not actually
  true for Writing since round 5. Verified directly in code before escalating, not assumed: read
  `_apply_writing_setup`, `derive_writing_turn_request`, and the orchestrator's SETUP-forcing
  branch to confirm the contradiction was real, not a stale review comment.
  - **Owner decision (Option A, of the two presented):** remove Writing `play_status` promotion
    from `POST /setup`; the story stays SETUP after structured setup; the next `/turns` call is
    genuinely recorded `SETUP_CONFIRMATION`/`NON_CANON_SUPPORT`; the orchestrator itself promotes to
    `IN_PLAY` once that confirmation turn lands; `derive_writing_turn_request()` is untouched (it
    already only derives `PROSE_CONTINUATION`/`EXTRACTOR_ELIGIBLE` once `play_status` is genuinely
    `IN_PLAY`, so no change was needed there). No React-side transition, no client-supplied
    `work_product_kind`/canon fields, no fabricated setup content -- all per the owner's explicit
    constraints.
  - `api/routes/setup.py`: `_apply_writing_setup` no longer passes `play_status=
    WritingPlayStatus.IN_PLAY` to `apply_writing_config_update`. The now-unused `WritingPlayStatus`
    import was removed.
  - `pipeline/orchestrator/service.py`: `_narrative_persist`'s Writing Phase G block now promotes
    `play_status` to `IN_PLAY` via `apply_writing_config_update(session, story_id,
    play_status=WritingPlayStatus.IN_PLAY)` whenever `writing_session_state.play_status is
    WritingPlayStatus.SETUP` -- i.e., whenever this turn was itself the setup-confirmation turn.
    Same session/transaction as the rest of the turn, so the promotion is atomic with the turn's
    own commit. Deliberately placed *outside* the existing provenance `try/except: pass` a few
    lines above it: a missing audit record is an acceptable best-effort loss, but a silently
    swallowed promotion failure would strand the story in SETUP forever -- a materially worse
    outcome, so it must surface as a real error if it ever fails. The CRUD-level guard in
    `apply_writing_config_update` (nonblank `persona_id`/`specific_goals` required to enter
    `IN_PLAY`) is a structural no-op here, not a live risk: both fields are always already
    persisted together by `WritingSetupRequest` before this turn is reachable.
  - **Sibling audit (the same "promote play_status inside /setup" pattern, used for Branching
    since round 7):** grepped every Branching `play_status` check in the orchestrator -- all five
    gate on `IN_PLAY` (enabling in-play rails: True CYOA rejection, branch-choice validation,
    HYBRID/TRUE_CYOA's `BranchingWriterService` requirement), none gate on `SETUP` to force a
    special turn classification the way Writing's `work_product_kind`/`canon_eligibility` model
    does. Branching has no `SETUP_CONFIRMATION`-equivalent concept to bypass, and its confirmation
    pass is meant to be an ordinary `DELIVERED` turn per ADR-016 Decision 3, not something requiring
    SETUP-phase forcing. Disposition: `already safe` -- structurally a different mechanism, not the
    same defect.
  - **Sibling regression found and fixed during implementation, not from a review comment:**
    `StoryView.tsx`'s `structuredSetupPersisted` signal for Writing (round 5 follow-up) checked
    `visibleState.play_status === "in_play"` as the "structured setup genuinely complete" proxy.
    That stopped being correct the moment `POST /setup` stopped promoting `play_status` itself --
    a Sojourner who reloads between completing setup and submitting the first (confirmation) turn
    would now be bounced back to `SetupForm`, even though setup was already genuinely complete
    (the exact defect shape round 3 and round 5's follow-up already fixed twice, resurfacing via a
    signal that was correct until this round's change invalidated its premise). Fixed by switching
    the discriminator to a nonblank `specific_goals` (persisted atomically with `persona_id` on
    every `WritingSetupRequest`, and therefore unaffected by when `play_status` changes) instead of
    `play_status`.
  - Tests (`tests/api/test_setup.py`): renamed/rewrote
    `test_writing_setup_promotes_play_status_to_in_play` to
    `test_writing_setup_no_longer_promotes_play_status_itself`, asserting `play_status` stays
    `"setup"` immediately after `POST /setup`.
  - Tests (`tests/api/test_fake_provider_product_path.py`): rewrote
    `test_writing_setup_via_api_yields_extractor_eligible_turn` into
    `test_writing_setup_confirmation_turn_then_promotes_to_in_play` -- a two-turn end-to-end test:
    the first turn's `mode_metadata` is `SETUP_CONFIRMATION`/`NON_CANON_SUPPORT` and ineligible for
    Retrieval Memory, and its own response's `visible_state.play_status` is already `"in_play"`
    (the promotion is atomic with that same turn, so the *response* reflects the post-promotion
    state even though the turn's own classification correctly used the pre-turn state); the second
    turn is ordinary `PROSE_CONTINUATION`/`EXTRACTOR_ELIGIBLE` and eligible. Also fixed
    `test_writing_in_play_turn_does_not_fail_for_missing_visible_state_service`, whose single
    submitted turn was no longer actually IN_PLAY (its own guard is gated on
    `play_status is IN_PLAY`) after this change -- it would have silently stopped exercising the
    regression it claims to test without failing outright, since the literal assertions
    (`disposition == "delivered"`, `pipeline_error_summary is None`) hold regardless of which guard
    path is taken. Now submits the confirmation turn first, then asserts the true IN_PLAY guard
    behavior on the second.
  - Tests (`frontend/src/StoryView.test.tsx`): updated the two existing Writing
    `structuredSetupPersisted` tests to use `specific_goals` instead of `play_status` as their
    framing, and added a new test asserting the play view shows even while `play_status` is still
    `"setup"`, once `specific_goals` is genuinely persisted -- the direct regression test for the
    sibling fix above.

- **Writing setup persona-gallery load failure is now non-fatal (P2) -- same read-failure class as
  round 12's RPG setup hydration guard and round 11's post-submit refresh handling.**
  `WritingSetupForm` silently swallowed `api.listPersonas()` failures (`.catch(() =>
  setPersonas(null))`), rendering as an empty gallery with no explanation and no recovery path
  short of a full page reload.
  - `frontend/src/SetupForm.tsx`: `WritingSetupForm` gained `personaLoadStatus: "loading" | "ready"
    | "error"`, mirroring round 12's RPG `hydrationStatus` pattern exactly. The load effect is now
    a named, retriable `loadPersonas()` function. On error, a visible "Could not load Writing
    companions. Retry before saving." message with its own Retry button is shown. Save's `disabled`
    condition gained `personaLoadStatus !== "ready"` alongside the existing `!personaId`/
    `!goalsReady` checks -- unlike RPG's form (where the *entire* form is submittable defaults
    before hydration), Writing's Save was already unreachable until a persona was selected, so this
    mainly closes the window where a stale/successful prior load's persona selection could still be
    submitted while a subsequent reload was silently failing.
  - **Sibling audit (per the review comment's own instruction -- other setup-form async reads with
    swallowed errors and no retry path):** `SetupForm.tsx`'s RPG `hydrate()` -- `already safe`
    (round 12 fix). `StoryView.tsx`'s initial `loadStory()` -- `already safe` (round 3, has a
    visible error + Retry button). `StoryView.tsx`'s `refresh().catch()` inside `SetupForm`'s
    `onComplete` and the dedicated `refreshTranscriptAndVisibleState()` -- `already safe` (round 11
    fixes, both have `refreshError` + Retry). `BranchingSetupForm` -- N/A, no async read exists
    (Branching setup never needed a `GET .../setup` hydration call; it already bypasses `SetupForm`
    entirely on reload once configured, per existing Architecture Notes). `StoryList.tsx`'s
    `listStories()` load -- has a visible error but no dedicated Retry button; disposition `out of
    scope`, not the same component family (the top-level story list/creation screen, not a "setup
    form"), and the review comment's own instruction was scoped to setup-form async reads plus an
    explicit "do not broaden into a general loading framework."
  - Tests (`frontend/src/StoryView.test.tsx`, new describe block): persona-load failure shows the
    visible error and keeps Save disabled; clicking Retry reloads personas (a second, successful
    `listPersonas()` call) and clears the error without a page reload; a successful load renders
    persona cards, allows selection, and Save becomes enabled once goals are also filled.

- Gates on the exact branch head: `black`, `ruff`, `mypy --strict` (173 source files, no issues),
  `pytest -q` (2324 passed, 10 skipped, 91.98% coverage, up from 91.97% -- net-zero test count
  change from the P1 backend fix, since it edited three existing tests rather than adding new
  ones; the coverage increase reflects the new orchestrator promotion branch and route comment
  being exercised). Frontend: `tsc --noEmit`, ESLint, Prettier, Vitest (39 passed, up from 35 -- 3
  new persona-load tests, 1 new structuredSetupPersisted regression test), `npm audit
  --audit-level=high` (0 vulnerabilities), production build, and the full Playwright E2E spine
  (7/7 passing) against a fresh build via `npm run e2e` -- all clean. `check-api-types-drift`
  confirmed no OpenAPI/TS schema changes this round.

## Remediation round 14

Codex posted 2×P2, both classified up front by the review comment itself as valid frontend
product-path defects, no owner decision needed, fix in the current PR. Both are framed as a
sibling-audit miss from earlier rounds: settlement failure surviving the turn (round 6) never
got a frontend rendering path, and mutation-success-vs-refresh-failure (round 10/11) never
consumed the fields the successful mutation itself already returned.

- **P2 -- preserve settlement warnings on successful turns.** `TurnSubmissionResponse` carries
  `settlement_warning` for a hosted DELIVERED/OOC_HANDLED turn whose settlement write failed
  (round 6's "settlement failure survives the turn" fix), but `DispositionBanner` returned `null`
  unconditionally for `delivered`/`ooc_handled` before ever looking at it -- the backend's
  non-blocking warning was silently dropped. Fixed in `frontend/src/DispositionBanner.tsx`: a new
  check ahead of the disposition switch renders a `settlement-warning` banner when
  `response.settlement_warning` is present on a `delivered`/`ooc_handled` response; falls through
  to the existing `null` return (no banner) when it isn't. Not converted into an error state, does
  not block the transcript/draft-clearing/play view -- purely an additional read of a field the
  switch below never inspected.
- **P2 -- use turn response `visible_state` before retryable refresh.** `TurnSubmissionResponse`
  already carries server-refreshed `visible_state` from the successful mutation, but
  `StoryView.submitTurn()` only ever set `visibleState` from the separate, retryable
  `refreshTranscriptAndVisibleState()` read -- if that follow-up read failed, the sidebar kept
  stale (or, on first turn, null) state even though the mutation response already had the current
  value. Fixed in `frontend/src/StoryView.tsx`: `setVisibleState(response.visible_state ?? null)`
  now runs immediately after `setLastResponse(response)`, regardless of disposition, before the
  retryable refresh call. Coalesced to `null` (not left stale) when the response itself carries no
  visible state, so this never invents state the backend didn't report. The follow-up refresh call
  is unchanged and still overwrites this with the read path's own value as the eventual
  reconciliation; a failed follow-up refresh no longer regresses the sidebar to stale/null.

- Sibling audit (per the review comment's own instruction): checked every `TurnSubmissionResponse`
  field meant to be surfaced immediately.
  - `settlement_warning` -- patched (this round).
  - `visible_state` -- patched (this round).
  - `provider_refusal`, `pipeline_error_summary`, `pending_roll_redirect_message`,
    `interaction_rejection_message` -- already safe; each already has its own `DispositionBanner`
    branch (rounds 1/7/8) unaffected by this round's changes.
  - `stable_prefix_cache_warmed` -- never rendered anywhere in the frontend (grepped
    `frontend/src` for `cache_warmed`/`stable_prefix`; the only hits are the generated OpenAPI
    schema and test fixtures defaulting it to `false`). This is a real gap against the original
    Issue 19 plan's Phase 3 note ("`stable_prefix_cache_warmed` badge rendering closes the
    session-resumption known unknown"), but adding that rendering is a new UI surface, and the
    review comment's own sibling-audit instruction explicitly says "do not broaden into new UI
    surfaces beyond this PR's minimal shell." Disposition: `out of scope`, flagged here rather than
    silently fixed or silently dropped -- an owner call on whether/when to land the badge.

- Tests: `frontend/src/DispositionBanner.test.tsx` -- two new cases (`delivered`, `ooc_handled`)
  asserting the settlement-warning banner renders with the warning text; the pre-existing "renders
  nothing for %s" case (both dispositions, `settlement_warning: null` in the shared fixture) already
  covers "no settlement warning still renders no banner," and the existing non-success-disposition
  cases were untouched by this change. `frontend/src/StoryView.test.tsx` -- new describe block
  (`StoryView consumes turn-response visible_state before refresh`) with four cases: response
  carries non-null `visible_state` + refresh fails -> the returned state renders; response carries
  `visible_state: null` + refresh fails -> stale prior state is cleared, not left stale (asserted
  against a story that had non-null state before the turn); response succeeds and refresh also
  succeeds -> the refresh read's value is the final state, not the mutation response's; POST failure
  -> visible state is untouched.

- Gates: frontend `tsc --noEmit`, ESLint, Prettier (clean), Vitest (45 passed, up from 39 -- 2 new
  `DispositionBanner` cases + 4 new `StoryView` cases), `npm audit --audit-level=high` (0
  vulnerabilities), production build -- all clean. No backend code changed this round, so backend
  gates were not re-run per the review comment's own instruction ("Backend tests only if backend
  code changes, which should not be necessary").
