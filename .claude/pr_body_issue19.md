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
