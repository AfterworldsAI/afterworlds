## Summary

CRD Issue 19 (#124) — React/Vite frontend shell + minimal FastAPI API surface. Phases 1-3
implement the API side: `create_app()` factory, DoR-A Sojourner identity, story CRUD exposure,
turn submission wired through entitlement + the DoR-E access-path selection helper + the
Binding Decision 8 per-story lock, and the three mode surfaces (visible-state dispatch,
structured setup, personas gallery). Phase 4 (frontend shell, generated TS types, Playwright
E2E, packaging) in progress.

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
