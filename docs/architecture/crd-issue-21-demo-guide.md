# CRD Issue 21 — Narrative Spine Demo Guide and Evidence Matrix

Governing issue: [#203](https://github.com/AfterworldsAI/afterworlds/issues/203) (published 2026-10-17 with the three accepted prerequisite contracts as comments). Implementation publication: the Owner conditionally authorized commit, push and a PR after satisfactory Codex review and local verification, holding at merge; merge, deployment and shared-runtime or Rules Package activation remain unauthorized. Governing documents: [CRD Issue 21 — Final Narrative Spine Demo](crd-issue-21-final-narrative-spine.md) and its [Integration Prerequisite Contracts](crd-issue-21-integration-prerequisites.md) (both accepted 2026-10-16), [ADR-016b](../decisions/adr-016b-branching-story-start.md), [ADR-006b](../decisions/adr-006b-automatic-rolling-summary.md).

Everything here runs on disposable stores with synthetic credentials. No real provider is contacted: the provider HTTP transport is scripted.

## What is real and what is replaced

| Layer | In these proofs |
|---|---|
| Built frontend (`frontend/dist`), FastAPI routes, story lock, access-path selection, BYOK readiness, `ProviderResolver` binding, refusal-fallback router | Production code |
| Anthropic / OpenAI SDK clients, adapters' request building, response parsing, refusal detection | Production code |
| Intent classification, Context Builder, Planner, Writer / Branching writer, Safety, Extractor, Contradiction, RPG adjudication, dice, action sequences, Rolling Summary pass, Story Bible, Retrieval Memory (local ChromaDB, local ONNX embeddings), transactions, settlement | Production code |
| Provider HTTP transport | **Replaced**: `scripts/scripted_provider.py` answers in each provider's wire format; deterministic defaults plus per-test scripted replies |
| Credential storage | **Replaced**: production keychain store over the in-memory keyring (`scripts/e2e_memory_keyring.py`) |
| Hosted key | Synthetic (`sk-ant-SYNTHETIC-…`) |
| RPG character creation and binding | **Product path** (ADR-015c): world confirmation, Rules Package selection, GM-led or pasted-sheet candidate, Accept character (validated and bound by the character service under the exact binding), configuration saved and summarized by the GM, then Complete setup confirming that summary's revision. The scripted GM's character proposal is transport data from `GET /__e2e__/fixtures/character`; nothing seeds character state or forces play. The CRD 15b/15c suites keep their own seeded fixtures for mechanics |
| Rules authority | Published-release store built through the real lifecycle into a temp directory (`scripts/e2e_rpg_server.py::build_store`) |

Scripted replies establish integration behavior only. They say nothing about live-model narrative quality, cache performance or commercial consumption.

## Reproduce

Prerequisites: Python 3.12 virtualenv with `pip install -e ".[dev]"`; Node 22 (`frontend/.nvmrc`).

```bash
# API / service proofs (production resolver, scripted transport)
pytest -q tests/api/test_branching_begin.py \
          tests/api/test_rolling_summary_production.py \
          tests/api/test_spine_continuity_and_failures.py
# RPG product startup and RPG spine on the published-release store (builds it: minutes)
pytest -q tests/ingestion/mechanical/test_crd21_rpg_startup.py tests/ingestion/mechanical/test_crd21_rpg_spine.py

# Built-app browser proof
cd frontend && npm ci && npm run build
npm run e2e -- --project=crd21-spine     # starts scripts/e2e_spine_server.py
```

Playwright starts every configured web server, including the two that build a published-release store, so the browser run takes several minutes before tests begin.

### Manual walkthrough (built app)

1. `PYTHONPATH="src:." python scripts/e2e_spine_server.py --port 8003`, then open <http://127.0.0.1:8003>.
2. `curl -X POST http://127.0.0.1:8003/__e2e__/access/hosted` (hosted credits).
3. Create a Branching story. Choose **True CYOA** and **2–3**, then **Save setup**. No turn exists yet; reloading still shows **Begin story**.
4. Click **Begin story**. The opening and two cards appear. Type freeform text: it is rejected and nothing is billed. Click a card to continue. Reload: the cards come back.
5. Continue to ten delivered turns. `GET /__e2e__/stories/{id}/summaries` shows version 1 covering them. The next turn's Planner request (`GET /__e2e__/provider/calls`) carries the summary.
6. Create an RPG story and describe the world. **Confirm world**, then **Use this Rules Package**. Queue the GM's proposal with `POST /__e2e__/provider/rpg_setup_writer` (body: `{"tool_input": {"schema_version": 1, "gm_text": "...", "result": {"kind": "character_proposal", "path": "gm_led", "character": <GET /__e2e__/fixtures/character>}}}`) and chat or paste a sheet. Review, **Accept character**, change the configuration and **Save configuration**, ask the GM below to summarize it, and **Complete setup** (it confirms the GM's summary; any later edit requires a new one). Then queue a check with `POST /__e2e__/provider/rpg_adjudication` and act.
7. BYOK: `POST /__e2e__/access/byok`, then save any non-`invalid` key under **Account & BYOK**. The account view now selects BYOK, every call carries the BYOK key and `GET /__e2e__/deductions` stops growing.

## Acceptance evidence matrix

Legend: **B** built-app browser (`frontend/e2e/crd21-spine.spec.ts`), **A** API/service integration on the production resolver, **R** reused accepted proof, **D** test double in use, **L** limitation.

| AC | Evidence | Kind |
|---|---|---|
| 1. Branching and RPG on hosted and BYOK through the built app; Writing closed | **Branching: met.** B: Freeform-only, Hybrid and True CYOA each on hosted and BYOK, covering setup, separate Begin, opening, next interaction and reload. A: the same 3×2 matrix. **RPG: met through product startup (ADR-015c).** B: fresh stories on hosted (GM-led + player roll/resume; completed sheet + backend and hidden checks) and on BYOK (GM-led; completed sheet + player roll/resume), each with a world clarification, a character clarification (GM-led) or an unresolved candidate first (completed sheet), and a saved configuration confirmed through the GM's summary, with reloads at each phase. A: both creation paths × hosted/BYOK through world, package, clarification, acceptance, configuration, first interaction, pending roll and resume (`test_crd21_rpg_startup.py`). R: the ADR-017b Writing-unavailable proof (`tests/api/test_mode_availability.py`, `frontend/e2e/spine.spec.ts`, delivery `0077140a`, CI 38972806481), unchanged | B, A, R, D |
| 2. Branching styles and RPG lifecycle | **Branching: met.** A/B: saved and partial setup with hydration; distinct Begin; first cards; explicit and invalid selection; annotation; True CYOA freeform rejection; OOC style changes (refused when True CYOA would have no selectable committed cards, with a style/range-only note; independent cadence/length still applied); each beat replaces the cards; setup cannot race Begin; repeated Begin is a no-op; failed, refused or malformed openings. **RPG: met.** Product startup with code-owned confirmations and stale/out-of-order/repeated/concurrent handling; refused, malformed, phase-invalid and Safety-blocked setup exchanges expose nothing and charge nothing; acceptance commit failure and changed authority leave setup intact; then the mechanical lifecycle (backend check, hidden check, player roll → resume). R: CRD 15b/15c suites for the full mechanics | B, A, R |
| 3. Production access selection and binding | Every A/B proof runs `ProviderResolver` (no `FakeProviderResolver`); assertions read which key reached the transport | A, B, D |
| 4. Settlement, BYOK non-deduction, unavailable access, fallback | Hosted deductions per delivered and OOC turn, including the summary pass snapshot. BYOK: no deduction, including with Cloud Services lapsed; BYOK-first selection once a key is saved (B). 403 before any work. Same-path fallback on BYOK (Anthropic → OpenRouter, BYOK keys only) and on hosted via the factory-wired `OPENROUTER_API_KEY` + `OPENROUTER_FALLBACK_MODEL` (hosted keys only, settled as hosted). The key without the model fails closed | A, B |
| 5. Persistence, Story Bible, Rolling Summary, Retrieval Memory, Rules Package | Extractor event reaches later Story Bible context; delivered narration retrieved from ChromaDB on a later turn; story isolation; summary v1 at N=10 eligible turns and v2 from the prior summary; later context consumes it; RPG audit rows on the published authority | A, B |
| 6. Safety, contradiction, refusal, operational failure | Input/output Safety blocks (BYOK OpenRouter route, Safety required), contradiction block, refusal, malformed output, provider 500, summary refusal/blank/500/persistence failure: no Turn, canon, summary, ingestion or deduction; retry delivers | A, B |
| 7. Isolated stores, synthetic credentials, secrets and hidden RPG data protected | tmp SQLite/Chroma per test; in-memory keyring; synthetic keys; BYOK key absent from page; hidden check absent from responses and page; summary pass receives no adjudication views | A, B |
| 8. Findings classified | See *Findings* below | — |
| 9. Revision, commands, substitutions, reused proofs, limitations | This document, `../evidence/implementation/IMPLEMENTATION-STATUS.md`, `RPG-STARTUP-IMPLEMENTATION-STATUS.md` and `WHOLE-CANDIDATE-R1-REMEDIATION-STATUS.md` (logs with exit codes) | — |
| 10. Repository gates, final-head CI, Codex review | Codex reviews: the local A/B rounds completed; whole-candidate review R1 (2026-10-17) found six defects and its re-review two Save-configuration residues plus one post-save recovery regression, all remediated. **Codex source closure is recorded** (`../evidence/implementation/CODEX-WHOLE-CANDIDATE-SOURCE-CLOSURE.md`). Local final gates on the stabilized source are the evidence handoff in `WHOLE-CANDIDATE-R1-REMEDIATION-STATUS.md` (the earlier RPG-startup suite results are pre-remediation, not final). detect-secrets: the narrowly corrected baseline is staged and the actual hook passes in the checkout, with a negative control. **Still required after the PR: exact-head GitHub CI, including 8-shard collection equality and combined Python coverage ≥ 80%.** No frontend coverage threshold is configured; see the status artifact for the measured value | L, **pending CI** |
| 11. Spine verdict | **Not yet passed:** it awaits exact-head GitHub CI on the PR (AC10). Stated in the status artifact, separately from public-launch readiness | — |

## Findings

Round-1 Codex review also fixed: setup racing Begin (config-conditional promotion; `/setup` shares the story lock); due-summary errors now keep the Extractor/Contradiction results; malformed-tool and actual outer-commit-failure summary proofs; partial-setup hydration and recovery in the app. See `../evidence` chronology.

| Finding | Classification | Disposition |
|---|---|---|
| Hybrid/True CYOA could not start: setup promoted to play with no opening or cards; the Branching services were unwired | Prerequisite A (accepted) | Implemented (ADR-016b) |
| No production Rolling Summary producer | Prerequisite B (accepted) | Implemented (ADR-006b) |
| `create_app` never supplied `openrouter_fallback_model`, so setting `OPENROUTER_API_KEY` broke hosted resolution | Settled-contract wiring (ADR-014a/014b `HostedRoutingConfig`) | **Fixed**: explicit `OPENROUTER_FALLBACK_MODEL` binding with no default, proven through the factory |
| No production path created or bound the typed RPG character, or advanced RPG setup into play | Bounded RPG prerequisite (accepted 2026-10-16) | **Implemented** (ADR-015c), proven from fresh built-app stories |
| A Freeform-only → True CYOA change (OOC or in-play setup) could leave True CYOA with no selectable card set | Invalid-state correction under ADR-016b's next-selectable-cards rule | **Fixed**: refused with a truthful style/range-only note (OOC) or 422 (setup), and the story stays playable. No OOC narrative or card generation was added |
| Cards from an earlier beat survived an intervening Freeform-only beat and could be shown or selected again | ADR-016: each beat replaces the choices | **Fixed**: a Freeform-only beat commits an empty card set. An immediate switch back with no beat in between keeps the cards |
| Codex whole-candidate review R1: Complete setup did not require a GM configuration summary; the candidate view truncated or omitted proposed values; a failed pasted sheet was cleared; the setup view stopped refreshing at the 50-turn transcript cap; the browser proof skipped clarification and configuration confirmation; detect-secrets exited 3 | Implementation and proof corrections under the accepted RPG prerequisite | **Fixed; Codex source closure recorded** (ADR-015c configuration target and revision) |
| Codex R1 re-review: a stale full-form Save could overwrite a newer configuration; explicit clearing was indistinguishable from omission; a committed Save whose follow-up read failed hid the form | Same settled stale-write and truthful-recovery contract (boundary check: issue-scoped, no Owner Decision) | **Fixed; source closure recorded**: Save names the draft's base revision (`409` when stale, `422` when missing during setup); `null` clears optional settings while omission keeps them; a saved-but-unrefreshed form stays usable with Complete hidden until a reload |
| True CYOA paraphrase classification, BranchTree traversal, pending-roll cancellation/rewind, threshold calibration, Writing | Existing deferrals | Unchanged |

## Remaining before acceptance

- **Exact-head GitHub CI** on the PR: the full suite, 8-shard collection equality and combined coverage ≥ 80%. Not run locally to completion (estimated 7–12 h); CI performs it.
- **Merge** is held for the Owner.
