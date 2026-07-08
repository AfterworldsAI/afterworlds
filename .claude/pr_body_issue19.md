## Summary

CRD Issue 19 (#124) — React/Vite frontend shell + minimal FastAPI API surface. `create_app()`
factory, DoR-A Sojourner identity, story CRUD + paged transcript exposure, turn submission wired
through entitlement + the DoR-E access-path selection helper + the Binding Decision 8 per-story
lock, the three mode surfaces (visible-state dispatch, structured setup, personas gallery), a
React/Vite/TS frontend shell (story flow, setup forms, transcript, turn submission, visible-state
sidebars, exhaustive disposition rendering), generated/drift-gated OpenAPI TS types, and a
Playwright minimal-spine E2E suite running against the built app with faked provider passes
(DoR-B). All four phases complete.

## Acceptance criteria coverage

1. Route handlers thin (Binding Decision 2); CRD Item 12 invariant test exists and passes —
   `tests/api/test_handler_thinness.py`.
2. Story creation → mode selection → minimal setup → turn submission → delivered output,
   transcript, mode visible state, all through existing services only — verified via the
   Playwright E2E spine and manual browser testing against the real (un-mocked) `create_app()`.
3. Entitlement wiring exact per Binding Decision 4; DoR-E full runnable-path matrix in one tested
   helper (`api/access_path.py`); no-runnable-path turns never reach the orchestrator; settlement
   only on hosted DELIVERED/OOC_HANDLED; settlement failure survives the turn (DoR-D) —
   `tests/api/test_access_path.py`, `tests/api/test_turns.py`.
4. Disposition handling exhaustive against the merged 9-value enum in both languages — backend
   `OrchestrationResult`'s own construction-time validator plus the turn route's pass-through;
   frontend `DispositionBanner`'s TS `never`-check (`DispositionBanner.test.tsx`).
5. Confirmation/persistence parity: transcript renders only from `GET .../turns` (persisted rows
   with a surviving `turn_id`); no optimistic rendering anywhere in the frontend.
6. No client-supplied trust-boundary field honored; `sojourner_id`/`access_path` server-derived;
   Binding Decision 8 lock tests (concurrent-same-story one-call-one-409, concurrent-different-
   stories no serialization, release on every path) all pass — `tests/api/test_turns.py`,
   `tests/api/test_identity.py`.
7. All API DTOs `extra="forbid"` + `schema_version`; TS types generated and drift-gated in CI
   (`check-api-types-drift`); mypy strict and `tsc --noEmit` both clean.
8. Read/bootstrap failures fail closed with typed errors; the only broad catch is the single
   top-level exception-to-envelope translator in `create_app()`.
9. One `create_app()` factory, one entry point (`main.py`), one frontend API client
   (`api/client.ts`), one config source (`ApiSettings`) shared by app and entry point.
10. Built frontend serves from FastAPI in the product configuration (`StaticFiles`, verified
    manually and by the E2E suite running against it); packaging/build rules cover the Node
    toolchain (`.nvmrc`/`engines`), generated types, and the persona registry JSON (already
    packaged via existing `pyproject.toml` `package-data`); E2E spine passes against the built app.
11. No Next.js/SSR/Node-app-server/Electron; no new orchestration/mode/entitlement/provider
    *policy* — the fake-provider path and session resolvers added in Phase 4 are assembly of
    already-shipped seams (see Architecture Notes), not new behavior; no Issue 20–23 scope
    absorbed (RPG dice UI explicitly deferred to Issue 19b).
12. `known_unknowns.md` pre-flight verified (React/Svelte entry already correctly resolved; the
    Issue 18 chromadb pip-audit ignore survives onto this branch, flagged not retired). Interim-path
    fencing: no pre-19 dev harness, script, or demo entry point exercising `orchestrate_turn`
    outside tests was found anywhere in the repository — nothing to fence or dispose of.

## Architecture Notes

- Consumes the Issue 14a/#122 BYOK readiness seam (`ByokCredentialReadinessProvider`, merged
  PR #123) exactly as shipped, only inside `api/access_path.py::select_access_path` — no
  `ProviderResolver` policy duplicated, no raw credential inspection.
- Access-path selection is one tested API-layer helper (DoR-E); route handlers never branch on
  access path directly (enforced by `test_route_modules_never_read_raw_entitlement_status_fields`).
- Stop-and-flag resolution (owner-approved): no typed seam existed anywhere to create or resolve
  a story's "current node," which `orchestrate_turn`/`WriterService` require. Resolved by creating
  one real Arc→Chapter→Node "turn-anchor" chain per story at story-creation time, via existing
  Issue-3 CRUD only (`ensure_story_turn_anchor_node`, idempotent). Not a node-advancement policy,
  not a graph engine — many Turns share this one Node for all of v1.
- The RPG inline dice UI is intentionally deferred to Issue 19b. Issue 19 implements the
  frontend/API shell, turn submission, visible-state rendering, and mode setup surfaces. It does
  not implement the inline dice UI, shared dice-expression subsystem, pending-roll consume
  adapter, scorecard, dice animation, or pending-roll rehydration behavior. Those are governed by
  AW_Dice_Subsystem_CRD and will be implemented in a follow-on Issue 19b PR.
- Chromadb pip-audit ignore (`CVE-2026-45829`) survives from Issue 18 onto this branch; flagged
  explicitly, not silently inherited, not retired here (not Issue 19's job).
- pip-audit additionally surfaces 6 CVEs (Mako, pydantic-settings, msgpack, idna, urllib3, pip)
  newly disclosed against pre-existing transitive dependencies (alembic/chromadb's chain,
  confirmed via `pip show` — none trace to `fastapi`/`uvicorn`, which this PR adds). Pre-existing,
  unrelated to this PR's dependency changes; flagged, not silently ignored or resolved here —
  `[OWNER DECISION]` on whether to ignore-with-justification or upgrade.
- React/Svelte known-unknown was already correctly resolved pre-Issue-19; no fix needed.
- Session-resumption known-unknown (`stable_prefix_cache_warmed` UX) is closed by this issue —
  the field is threaded through the turn-submission envelope; frontend badge rendering lands in
  Phase 4.
- Real `OrchestratorService` wiring (`api/pipeline_wiring.py`) assembles existing typed seams only
  (Planner/Writer/Extractor/Contradiction/Safety/IntentClassifier/ProviderResolver/ContextBuilder/
  ChromaDB retrieval), each via its own `.from_env()`/factory constructor — no new orchestration
  policy. The one net-new piece is a minimal standalone Anthropic call backing the Issue 7
  classifier's `ModelCallerT` seam (no `PipelinePassId` of its own, so it doesn't go through
  `ProviderResolver`/`ProviderAdapter` like the other passes) — narrow, mechanical assembly per
  known_unknowns.md's own "lightweight model call" framing, not a routing/entitlement/safety
  decision. Verified end-to-end against the real `create_app()`: a turn submitted without
  `ANTHROPIC_API_KEY` returns a clean typed `PIPELINE_ERROR` envelope at HTTP 200, never a crash.
  Mode-specific pass services (RPG adjudication, Branching writer, Writing OOC extractors) are
  out of scope for Issue 19's core-path wiring; `OrchestratorService` already treats them as
  optional and falls back to the generic prose Writer path when absent (ADR-016 Decision 3).
- Turn-submission envelope's `visible_state` field and the standalone
  `GET .../visible-state` route share one dispatch function (`api/visible_state.py`), not a reuse
  of `OrchestrationResult`'s embedded visible-state fields — those are forbidden by the
  disposition-invariant validator on every non-DELIVERED disposition, including `OOC_HANDLED`,
  which is exactly where Branching/Writing config most often changes. "Single fetch" means one
  shared call site within the same session/transaction as the turn, not literal field reuse.
- Discovered (not assumed) that `BranchingVisibleStateService.build` has the same shape of
  precondition as Writing's `persona_id` requirement: it requires `interaction_style` AND
  `branching_cadence` configured before it will build a result. The shared visible-state dispatch
  returns `None` gracefully pre-setup for all three modes, verified by test against the real
  service (not a mock).
- Setup route (`POST .../setup`) writes only structured config fields via existing typed CRUD;
  it never writes turns and never advances `play_status`/`setup_phase` itself. RPG conversational
  setup and Branching's confirmation pass (ADR-016 Decision 3) remain ordinary turns through
  `POST .../turns`.
- Manual browser verification against the real `create_app()` (no test doubles) surfaced two real
  bugs before they shipped:
  - Discovered per ADR-016 Decision 3 / ADR-017 Decision 9 that Branching/Writing setup
    "confirmation" is itself an ordinary narrative turn processed by the orchestrator, not
    something the structured `/setup` endpoint completes — `play_status` only flips server-side
    once that turn lands. The frontend's gating on `story.status === "setup"` alone left the user
    stuck on the setup screen forever (structured fields saved, but status never changes without a
    turn). Fixed by letting the frontend proceed to the play view once structured fields are saved
    locally, without asserting any backend fact the server hasn't recorded (a client-local
    view-routing decision, not a shadow source of truth).
  - Turn-submission failures were replacing the entire play view (losing transcript, visible
    state, and the draft) instead of surfacing inline — violated Binding Decision 6. Fixed by
    separating page-load errors from turn-submission errors so the play view and draft survive
    every turn-submission failure class (typed error, transport failure, etc.).
- DoR-B faked-provider path (`api/fake_pipeline.py`, env-gated by `AFTERWORLDS_FAKE_PROVIDER`,
  never true in the product/dev path): a `FakeProviderAdapter` returning canned, schema-valid
  responses per `pass_id` so each real pass service's OWN parsing/validation logic
  (`PlannerService`, `WriterService`, `ExtractorService`, `ContradictionService`, `SafetyService`)
  runs end-to-end against deterministic data — nothing about those services themselves is
  mocked, only the model call underneath them. A `FakeProviderResolver` duck-types
  `resolve_for_turn` only (documented, narrow protocol substitution, not a `ProviderResolver`
  subclass). Verified against the real orchestrator: a full turn (intent classification -> planner
  -> writer -> extractor -> contradiction) returns `DELIVERED` with the fake output.
- A second real gap the fake-provider smoke test surfaced: `OrchestratorService` hard-requires
  three session-resolver callables (`rpg_session_sheet_resolver`, `branching_session_resolver`,
  `writing_session_resolver`) per mode — an unwired `writing_session_resolver` produced
  `PIPELINE_ERROR` for every WRITING turn, not a graceful degrade. These are plain typed reads of
  already-persisted session state via existing CRUD (not new pass logic, unlike the mode-specific
  pass SERVICES which remain out of scope) and are now wired in `pipeline_wiring.py`.
- Known, flagged gap (not silently worked around): the spec's E2E scenario "INTERACTION_REJECTED
  rendering in True CYOA" is not exercised by the current E2E spine. Verified empirically that
  True CYOA's rejection logic lives inside `BranchingWriterService`'s own pass
  (`BranchSelectionValidationService`), which is a mode-specific pass service Issue 19 deliberately
  left unwired — without it, every Branching turn falls back to the generic prose Writer path and
  returns `DELIVERED` regardless of `interaction_style`. The E2E spine's Branching test covers
  setup + a delivered turn instead; `INTERACTION_REJECTED` E2E coverage requires wiring
  `BranchingWriterService` first, which is Phase 3-adjacent mode-specific work Issue 19 scoped out
  (see the "Mode-specific pass services... out of scope" note above).

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
