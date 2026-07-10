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

- BYOK readiness seam (`ByokCredentialReadinessProvider`, Issue 14a/#122) is consumed exactly as
  shipped, only inside `api/access_path.py::select_access_path` — no `ProviderResolver` policy
  duplicated, no raw credential inspection.
- Access-path selection remains one tested API-layer helper (DoR-E); route handlers never branch
  on raw entitlement status directly.
- Owner-approved turn-anchor chain resolves the v1 current-node gap: one real Arc→Chapter→Node
  "turn-anchor" chain per story, created at story-creation time via existing Issue-3 CRUD
  (`ensure_story_turn_anchor_node`, idempotent) — not a node-advancement policy, not a graph
  engine; many Turns share this one Node for all of v1.
- The RPG inline dice UI (shared dice-expression subsystem, pending-roll consume adapter,
  scorecard, dice animation, pending-roll rehydration) is intentionally deferred to Issue 19b,
  governed by AW_Dice_Subsystem_CRD.
- Chromadb pip-audit ignore (`CVE-2026-45829`) survives from Issue 18 onto this branch; not
  retired here (not Issue 19's job).
- Newly surfaced, unrelated CVEs (Mako, pydantic-settings, msgpack, idna, urllib3, pip —
  pre-existing transitive dependencies of alembic/chromadb, none tracing to `fastapi`/`uvicorn`)
  remain an owner decision / dependency follow-up, not silently resolved here.
- Real `OrchestratorService` wiring (`api/pipeline_wiring.py`) assembles existing typed seams only
  (Planner/Writer/Extractor/Contradiction/Safety/IntentClassifier/ProviderResolver/ContextBuilder/
  ChromaDB retrieval) — no new orchestration policy. Mode-specific pass services (RPG
  adjudication, Branching writer, Writing OOC extractors) intentionally remain unwired except
  where Issue 19 explicitly consumes an existing required seam (e.g. `WritingVisibleStateService`,
  the three mode session resolvers); `OrchestratorService` already falls back to the generic prose
  Writer path when a mode-specific pass service is absent (ADR-016 Decision 3).
- Visible-state dispatch is centralized in one function (`api/visible_state.py`), shared by the
  turn-submission envelope's `visible_state` field and the standalone `GET .../visible-state`
  route — not a reuse of `OrchestrationResult`'s embedded visible-state fields, which are forbidden
  by the disposition-invariant validator on every non-DELIVERED disposition.
- Setup route (`POST .../setup`) writes structured setup/config fields via existing typed CRUD and
  never writes turns. Promotion semantics are mode-specific:
  - Branching: once the effective persisted setup has both `interaction_style` and
    `branching_cadence`, the setup route promotes `play_status` to `IN_PLAY`; this is required for
    Branching rails such as CYOA rejection and branch-choice validation.
  - Writing: the setup route does not promote `play_status`; the next ordinary `POST .../turns`
    call remains the ADR-017 setup-confirmation turn (`SETUP_CONFIRMATION` / `NON_CANON_SUPPORT`)
    and the server promotes to `IN_PLAY` only after that turn lands.
  - RPG: the setup route records structured setup only; RPG progression to `IN_PLAY` remains tied
    to the later concrete character-sheet/adjudicability path, not Issue 19's minimal setup form.
- The DoR-B fake-provider path (`api/fake_pipeline.py`, env-gated by `AFTERWORLDS_FAKE_PROVIDER`,
  never true in the product/dev path) is E2E support only, not product behavior — each real pass
  service's own parsing/validation logic still runs end-to-end against deterministic canned data;
  only the model call underneath is faked.
- Mode-specific pass services intentionally remain unwired except where Issue 19 explicitly
  consumes existing required seams. Current Branching UI limitation: Hybrid/True CYOA interaction
  styles are disabled in the minimal frontend until `BranchingWriterService` is wired; the
  orchestrator's fail-closed guard against a direct-API-configured in-play HYBRID/TRUE_CYOA story
  is the correct backstop in the meantime, and `INTERACTION_REJECTED` coverage remains at the API
  level where the UI can no longer reach it.
- Current packaging boundary: a packaged (wheel) launch fails loudly at startup if the frontend
  dist path is neither explicitly configured nor present at its default repo-relative location,
  rather than silently booting an API-only server. Full wheel/pip packaging (bundling the frontend
  dist, `docs/prompts`, and the Alembic migration directory as package data) remains a follow-up —
  see below.

## Current follow-ups / owner decisions

- **Dependency CVEs / pip-audit:** owner decision needed on ignore-with-justification vs. upgrade
  for the pre-existing, unrelated transitive-dependency CVEs surfaced by `pip-audit` (Mako,
  pydantic-settings, msgpack, idna, urllib3, pip).
- **Full wheel/pip packaging follow-up:** bundle the frontend dist, `docs/prompts`, and the
  Alembic migration directory as package data (or resolve them via `importlib.resources`) so a
  site-packages install works without a repo checkout present.
- **Issue 19b:** RPG inline dice UI — shared dice-expression subsystem, pending-roll consume
  adapter, scorecard, dice animation, pending-roll rehydration (AW_Dice_Subsystem_CRD).
- **BranchingWriterService-rich UX** (Hybrid/True CYOA interaction styles) remains outside Issue
  19's scope; wiring it is a prerequisite for re-enabling those styles in the frontend.

## Remediation log

Detailed Codex/Claude remediation history, sibling audits, negative controls, and round-specific
gate results have been moved to:

- `.claude/pr_126_remediation_log.md`

This PR body keeps only the merge-relevant summary, acceptance coverage, durable Architecture
Notes, current known boundaries, and final gate status.

## Final gate status

Gates on the exact branch head (round 14, the latest landed round):

- Python: `black`, `ruff`, `mypy --strict` (173 source files, no issues), `pytest -q` (2324
  passed, 10 skipped, 91.98% coverage) — unchanged since round 13; round 14 touched frontend
  only.
- Frontend: `tsc --noEmit`, ESLint, Prettier, Vitest (45 passed, up from 39), `npm audit
  --audit-level=high` (0 vulnerabilities), production build.
- E2E: full Playwright spine (7/7 passing) via `npm run e2e` against a fresh build.
- OpenAPI/TS: generated and drift-checked; no schema changes in round 13 or round 14.
