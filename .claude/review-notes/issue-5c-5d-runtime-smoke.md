# CRD Issues 5c/5d — bounded local runtime smoke (10 October 2026)

**Status: the app booted and served, the native authority reads passed, and the app stopped.** This
note records an operational check. It is not a completion declaration, and no issue state was changed:
#132 and #137 were already closed before the smoke, and their state does not waive accepted
requirements. The final CRD Issue 5d cutover remains unfinished; see "Completion gaps" below. Current
status is in the [restart opening](../../docs/architecture/issue-5c-5d-clean-restart.md).

## Authority, code and targets

- **Owner authorization.** Verbatim: "start the **bounded local app launch and smoke check** against
  `D:\AI\Claude\afterworlds-runtime`, using merged main in an isolated checkout. Once that is complete,
  proceed to the review of whether to declare the restart complete and close #132/#137."
  - The operational interpretation: stop the app afterwards; no issue-state change, merge or
    completion declaration; no provider calls or gameplay turns.
- **Code.** Merged main `71c77b2c9be7c1c4ccdd06b84fc0148a52fec568`, which merged PR #181, in the
  isolated checkout `D:\AI\Claude\quarantine-retirement\afterworlds`. The frontend was built there
  with `npm ci` and `npm run build`; `package-lock.json` was unchanged.
- **Runtime targets.** These are the stores published and activated under the
  [execution record](issue-5c-5d-shared-publication-preparation.md):
  - SQLite `sqlite:///D:/AI/Claude/afterworlds-runtime/afterworlds.db`;
  - embedded Chroma `D:\AI\Claude\afterworlds-runtime\.chroma_data`.
- **App.** `afterworlds.main:app` ran under one uvicorn worker on `127.0.0.1:8000`.
  - Every HTTP request was a GET.
  - Variables that looked like keys or tokens were removed from the child's environment, and the fake
    provider was unset.

## Run 2 results (harness `ec1944fe…`)

| Phase | Result |
|---|---|
| Preflight and baseline | HEAD and a clean tree; the 123 immutable inputs; the protected original checkout equal to its intake snapshot; byte-copy classification `fully-published`, one collection with 11,076 embeddings |
| Launcher self-check | The exact launcher served a private stand-in app, ready in 1.0 s, and stopped gracefully |
| HTTP | Ready in 3.6 s (app loaded at 2.8 s). `GET /api/health` returned 200 `{"status":"ok","db_reachable":true,"schema_version":1}`. `GET /`, the built `/assets/index-CiI_luBF.js` (bytes equal to `dist`), `/api/personas` and `/api/stories` all returned 200. The route table has no rules or citation route |
| Shutdown | Graceful through the stop file, exit 0; port 8000 no longer listening |
| Native reads, on `app.state.session_factory` and rolled back; **not HTTP** | Active projection `1f0db408-ee07-5e8d-897d-29838d614c53`. The exact four-part binding by UUID and by slug, with the empty override set `521a6242-…`. Whole package: 1,835 records. `glossary.blinded` provenance equals the oracle, with official locator `p. 177`. The four citation families are `RESOLVED`. An ONNX query on the accepted collection returned 5 hits. 36b is quarantined, and 3fe and 574 are superseded. The app-wired path quarantines the retired package |
| After | No DB table deltas, including `rp_*` and `alembic_version`. Chroma payload tables and segment files are unchanged; the only non-payload delta is `acquire_write`, the per-process open marker. The 123 immutable inputs and the protected checkout are unchanged |

**Raw result and review supplement.**
- The raw `99-result.json` is **FAIL**. It is preserved unchanged.
- Its only stop is the harness's wiring check. That check compared the engine's rendered URL
  `sqlite:///D%3A/AI/…` with the input string `sqlite:///D:/AI/…` as strings.
- SQLAlchemy's renderer escapes the drive colon, so the difference is presentation only.
- **What verified the target.** Codex checked it independently, without opening a connection:
  - `create_engine(DB_URL).url.database` is `D:/AI/Claude/afterworlds-runtime/afterworlds.db`;
  - that path resolves to the intended file;
  - `make_url(rendered) == make_url(DB_URL)`.
  The settings URL equalled the input exactly.
- **Harness correction.** The private comparison now requires parsed-URL equality and the same
  resolved absolute SQLite file; it is not a prefix match. A focused check with no DB connection and
  no app:
  - accepts the input string, the run-2 rendered URL from the receipt, and a freshly rendered URL;
  - refuses another file in the same directory, the protected original store, the same file name in
    another directory, a relative default, in-memory, a differing query, and another backend.
- The app was not relaunched and the native checks were not repeated to change the badge.

**Cutover counterexample (observed, not pass/fail).**
- The same valid requests went through the typed `RulesAuthorityService` and through the app-wired
  forwarding shape at `src/afterworlds/services/context_builder.py:410-418`:

  | Request | `RulesAuthorityService` | App-wired forwarding |
  |---|---|---|
  | Record selector `glossary.blinded` | `resolved`, 1 record, with binding | 0 chunks, 0 entities |
  | `whole_package=True` | `resolved`, 1,835 records, with binding | 0 chunks, 0 entities |
  | Stale recorded binding | `stale` | 0 chunks, 0 entities |

- `ActiveRuleSlice` has only the fields `package_id`, `chunks` and `entities`: it carries no binding.

## Run 1 (harness `9ed0e182…`): launcher defect, preserved

Run 1 failed readiness at 121.6 s and then stopped gracefully (exit 0), with no listener. Its only
store change was the normal first-start `sojourner_identity` row (0 → 1); authority rows, the Chroma
payload, the immutable inputs and the protected checkout were unchanged.

**Cause, a private harness defect.** The launcher held a blocking `sys.stdin.read()` on a pipe during
startup, which stalls numpy's native import (`numpy/_core/multiarray.py:11`, reached through
chromadb) inside uvicorn's loop.
- A no-app probe reproduced the stall 2 of 2 times, with the stack captured.
- The same probe with stdin set to DEVNULL was ready in 2.6 s.
- A negative control using the preserved run-1 launcher text, with a stand-in app, stalled in the same
  frame.

The corrected launcher uses DEVNULL stdin, a stop file with a harness-liveness check, and a
tree-kill fallback. No product dependency or code changed.

## Completion gaps

Both are settled, issue-scoped CRD Issue 5d obligations. Neither needs a new Owner Decision. They
describe merged main `71c77b2` at the time of the smoke; the
[final-cutover note](issue-5d-final-cutover.md) records the code change that addresses them.

1. **Existing production consumer cutover.** Contract 6 governs this
   (`docs/architecture/issue-5d-practical-reliability-draft.md:443-454`): it requires extending the
   existing `RuleSliceRequest` / `get_active_rule_slice` path so that every slice carries the exact
   four-part binding and keeps the deterministic selectors or `whole_package`.
   - Today the Context Builder drops `recorded_binding`, `record_selectors`, `component_selectors` and
     `whole_package`.
   - `get_active_rule_slice` still reads legacy chunks and entities.
   - Its result carries no binding.
2. **Final legacy retirement.** AC22 and the removal requirements (draft lines 510, 546 and 645)
   require removing `MechanicalEntity` and its siblings, `MechanicalEntityORM` / `rp_mechanical_entities`,
   their constructors and callers, and the legacy chunk/entity override path
   (`RuleOverrideORM` / `rp_overrides`).
   - These remain, including the entity construction in `ingestion/ingestion_service.py`.
   - This is distinct from PR #179's completed retirement of the original corpus products
     ([retirement disposition](issue-5c-quarantine-retirement.md)).

**Not required for either gap:** a new HTTP endpoint, an RPG gameplay selector policy, Character
Sheet storage (2b), or adapter behavior (15c).

**Discharged, for contrast** (see the [completion disposition](issue-5c-5d-restart-completion.md)
and the [execution record](issue-5c-5d-shared-publication-preparation.md)):
- source qualification;
- the 5c release outcomes (#132);
- the six isolated §2.5 obligations;
- the Owner's semantic acceptance of the 8781 recording;
- the accepted projection and its typed services;
- local publication and activation.

## Stopped state and protection

- The app is stopped, with no Python process remaining.
- No runtime migration or deletion took place, and no production code changed.
- The protected original checkout `D:\AI\Claude\afterworlds`, the global settings and the 123
  immutable inputs are unchanged.

## Private evidence (not in Git)

Paths are relative to the Codex evidence root
`C:\Users\raven\.codex\visualizations\2026\10\09\01a121f3-798d-7fd2-88a4-b8c172155dba\`.

| Item | SHA-256 |
|---|---|
| `runtime-smoke-review/runtime_smoke.ec1944fe.py` (run-2 harness, read-only copy) | `ec1944fe96398dd4357d27ee8aedb161fc8499fba192697ffc128c75f8624237` |
| `runtime-smoke-review/runtime_smoke.9ed0e182.py` (run-1 harness) | `9ed0e1829da1b7a6df7ff10442d403e4a5df7a4e6beb9ca1d2e1fc788b16652e` |
| `runtime-smoke-review/runtime_smoke.py` (URL comparison corrected; not run against the app) | `db8dc686593c3f26df01a1b73a2a8021e6bc14faf709c88af7a3860490c22b0f` |
| `runtime-smoke-review/smoke-run-2/04-inprocess.json` | `864d8cc6269436788a5744aa7929e2c2f4a95a86ec8605fac6a0ef54c3860383` |
| `runtime-smoke-review/smoke-run-2/99-result.json` (raw FAIL, unchanged) | `9deb628b96c8e1674c8168c0d58a4b5b82fd5546dfcd09f49e21d9801cd71fba` |
| `runtime-smoke-review/smoke-run-2/02-http.json` | `41bd26c15ac37866f84136be80613be035f04510532a61eba0ba48e406434411` |
| `runtime-smoke-review/smoke-run-2/05-after.json` | `e5dcbfd230a55e5c10beffb6aa4041101d0412a342607c57cacf590fcdf8fbd7` |
| `runtime-smoke-review/url-check-2.json` (focused URL check) | `102f8b6178182c82a8e7fbdc6d6d9271675bc5d9fa8a4165f22e293669b44a4c` |
| `runtime-smoke-review/smoke-run-1/99-result.json` | `d9fd1e8df77371b8697f72c3b6b6d19ab80e384620f129bfc22c3d4fe05d4299` |
| `runtime-smoke-review/launch-probe-5.jsonl` (run-1 reproduction) | `a665393b348fa1d8899fff81e1c0b51327d071dc0a522af029803a6ad0496c14` |
| `runtime-smoke-review/negative-control-1.json` | `c369225643acc80bbfa4232477dc37d4972db51528b2f06ebe758e7ce663511f` |

The other receipts live in the same directory: `smoke-run-2/`, `smoke-run-1/`, the probes, and the
Codex reviews `CODEX-PRELAUNCH-REVIEW.json` and `CODEX-RETRY-REVIEW.json`. Codex's integrated
`COMPLETION-ASSESSMENT.md` is being finalized by Codex and is not reproduced here.
