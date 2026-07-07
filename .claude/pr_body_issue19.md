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
