# Afterworlds Construction Readiness Document (v9)

*Items 1–17 of the Construction Handoff Checklist — maintained from v8 and revised May 2026 to integrate Owner Decisions #1–#14. This revision replaces stale Issue 13–21 roadmap shorthand with resolved ownership boundaries, sets React + Vite + TypeScript as the v1 frontend stack, preserves Branching cadence/verbosity and Starter Access, adds the dedicated post-spine billing-platform/payment-integration issue, and clarifies public-launch blockers after the Issue 21 narrative spine demo.*

*The safety-envelope model remains binding: the core narrative pipeline is Planner → Writer → Extractor → Contradiction. Input Safety Preflight runs before Planner/Writer when orchestration policy requires it. Conditional Output Safety Audit runs after Writer and before Extractor/Contradiction when provider or risk policy requires it. Provider refusals are typed pass failures, not Safety verdicts.*

*Caching remains adapter-calibrated, not universal. Afterworlds owns stable/volatile separation and deterministic stable-context reuse discipline. Provider/platform-specific cache realization belongs to Issue 14 provider adapters.*

---

## Item 1 — Product Scope is Pinned Down

### What Afterworlds Is

Afterworlds is a platform for exploring stories in an interactive, participatory way. It lets a Sojourner enter the world of a story — whether created by them or encountered elsewhere — and continue within it through choices, prose, rules, and consequences.

The core impulse: when someone finishes a story they love, there is often a longing to continue it, enter it, or live through it differently. Afterworlds closes that gap.

### Who It’s For

Primary audiences:

- **Readers** who want to continue or inhabit stories differently.
- **Players** who want consequence-aware narrative play.
- **Budding writers** learning craft through collaborative storytelling with an AI partner.

### What Problem It Solves

Afterworlds solves the post-story longing problem with an interactive narrative engine that preserves canon, remembers consequences, and keeps continuity as a first-class product requirement.

### What Is Explicitly In v1

v1 is the first release-capable MVP, not merely an internal milestone.

- Text engine with full Sojourn orchestration path: Planner → Writer → Extractor → Contradiction with safety envelope.
- RPG, Branching, and Writing modes.
- Full story hierarchy: Story / Arc / Chapter / Node / Turn.
- Rolling Summary + Story Bible.
- Rules Package support with one curated, ingested, published, and queryable d20 Rules Package.
- Bounded d20 Rules System Adapter for RPG deterministic rails.
- Vector retrieval memory through ChromaDB.
- Extractor update classification policy.
- Contradiction Checker.
- SQLite persistence.
- BYOK API support with local-first credential storage.
- Hosted subscription credits / top-ups entitlement framework, including optional Starter Access as a paid entry package using the same full pipeline.
- BYOK perpetual license + first-year Cloud Services inclusion, with renewal-capable Cloud Services state.
- React + Vite + TypeScript frontend shell.
- Minimal FastAPI API surface needed by the frontend.
- User-facing billing/BYOK visibility and configuration.
- v1 operations/support/compliance minimums as defined in Issue 22.
- Payment integration before public launch if hosted paid access or top-ups are offered.

### What Is Explicitly Not In v1

Deferred beyond v1:

- Image generation from Node metadata.
- Visual story map.
- Non-destructive What If? branching.
- Voice input/output.
- Player-supplied Setting Canon Packs for licensed RPG settings.
- Marketplace or collaborative multi-user stories.
- Mobile clients.
- Full Writing-mode version history, draft branching, restore/rollback, and compare tooling unless separately scoped.
- A polished full admin console with advanced analytics, CRM workflow, or enterprise-grade operations tooling.
- Direct OpenAI or Google/Gemini provider surfaces.
- Supported local/open-weight or VPS-hosted open-weight model surfaces.
- Rich Branching/Writing UX beyond the minimal v1 shell and v1 Branching cadence/verbosity setting unless separately scoped.
- Persona expansion across RPG and Branching modes.

### Versioning Clarification

Version numbers refer to release-capable product scope.

Pre-v1 milestones describe build order only:

- foundation and persistence
- Story Bible and summary services
- Rules Package schema and ingestion
- context assembly
- minimal Writer path
- Extractor, Contradiction, Planner, Safety, and full orchestration
- entitlement routing
- provider routing and BYOK credential management
- mode integrations
- retrieval memory
- frontend/API shell
- billing/BYOK visibility
- final narrative spine demo
- public-launch blockers: billing-platform/payment integration and operations/support/compliance

v1 is the first release-capable MVP.

---

## Item 2 — Core Architecture Principles Are Frozen

These principles must not be casually reinvented during coding.

1. **Story Bible is structurally separate from prose history.**
2. **Six memory layers have distinct roles:** Immediate / Rolling Summary / Story Bible / Rules Package / Retrieval Memory / Contradiction Checker.
3. **Intent is classified before context is assembled.**
4. **The Sojourn orchestration path is staged:** Planner → Writer → Extractor → Contradiction, protected by a safety envelope: Input Safety Preflight before Planner/Writer when required; Conditional Output Safety Audit after Writer and before Extractor/Contradiction when required. Provider refusals are typed pass failures, not Safety verdicts.
5. **Extractor proposes canon updates; it does not write canon directly.**
6. **Stable context is assembled once per turn and shared across passes.** Provider/platform-specific cache realization belongs to provider adapters, not Context Builder or orchestration.
7. **Operational state transitions that affect money, access, or user data must be reconstructable by humans** through explicit event logging rather than inferred from opaque current-state fields.
8. **No access path removes the core continuity pipeline or safety envelope.**
9. **Scope creep and Known Unknowns must be surfaced, not silently resolved.**

---

## Item 3 — v1 Success Criteria Are Defined

A minimal v1 success statement:

- A Sojourner can create a story.
- Select RPG, Branching, or Writing mode.
- Complete mode setup.
- Submit turns and receive coherent output.
- Persist story state and turn history.
- Maintain Story Bible and Rolling Summary.
- Query vector retrieval memory during play.
- In RPG mode, adjudicate against one active, ingested, queryable d20 Rules Package with bounded deterministic rails.
- Run contradiction checking before delivery.
- Use BYOK model access.
- Use hosted access with runtime entitlement enforcement.
- View user-facing billing/BYOK status and configuration.
- Operate the commercial product responsibly through the Issue 22 support/compliance minimums.

Terminology guardrail: Story Bible = narrative canon; Rules Package = external mechanical canon for RPG mode; canon pack = optional external lore/canon corpus for Branching/Writing modes. Session state remains separate from all three.

---

## Item 4 — Technical Stack Is Decided Enough to Begin

| Component | Decision |
|---|---|
| Backend | Python 3.12 + FastAPI. |
| Storage | SQLite first. |
| Retrieval memory | ChromaDB included in v1 release scope. |
| Frontend | React + Vite + TypeScript. |
| Deployment | Local web server accessed through browser. |
| Model access | Hosted provider routing + BYOK. |
| Package management | pip + virtualenv only. |

Issue 19 must not introduce Next.js, SSR, a separate Node application server, or Electron. Electron or another desktop wrapper remains optional later, not v1 frontend infrastructure.

Future model/deployment surfaces must not be architected against. v1 local-first browser deployment plus hosted/BYOK provider access remains the build target, but later issues may add local/open-weight models, VPS-hosted open-weight models, broader hybrid BYOK surfaces, or a desktop wrapper if product and quality constraints justify them.

---

## Item 5 — Core Entities Are Defined

| Entity | Description |
|---|---|
| Story | Top-level container for a complete narrative. |
| Arc | Major narrative division within a Story. |
| Chapter | Subdivision within an Arc. |
| Node | Story beat / state transition. Unified across all three modes; mode-specific metadata distinguishes behavior. |
| Turn | One interaction unit: one Sojourner input + one AI response. |
| Story Bible | Structured narrative canon: world rules, cast, locked facts, forbidden facts, timeline, relationship ledger, unresolved threads. |
| Rolling Summary | Compressed narrative history, auto-updated every N turns. |
| Rules Package | External mechanical canon package for RPG mode. |
| Rules System Adapter | Hand-authored deterministic helpers for a supported RPG rules system. |
| Character Sheet Model | Persistent ruleset-specific RPG character state. |
| World / Character State | Current world conditions and runtime character state not owned by the RPG character sheet. |
| Mode-Specific Session State | RPG transient combat/session context; Branching pacing/config/tree state including interaction style, Branching cadence/verbosity, branch presentation metadata, and selection metadata; Writing beat constraints and minimal version-history pointers. |
| Runtime Entitlement State | Authoritative product-access state used for routing/enforcement: hosted credits, top-up balances, BYOK license, Cloud Services active/lapsed status. |
| Entitlement / Support Event History | Append-safe operational record owned by Issue 22 for support, audit, remediation, deletion/export state, and anomaly visibility. |

Key principle: Node is a unified entity across modes. Mode-specific metadata flags make distinctions clear without duplicating base schema.

---

## Item 6 — Mode Prompt Contracts Are Written

The mode prompt contracts are canonical versioned artifacts. Full content — system prompts, pre-play sequences, and player/Sojourner configuration tables — lives in the prompt files. This section records the key decisions and design rationale behind each contract. Do not duplicate full prompt text here; update the prompt files directly when contracts change.

Canonical prompt files:

- `/docs/prompts/rpg_mode.md`
- `/docs/prompts/branching_mode.md`
- `/docs/prompts/writing_mode.md`

The prompt files are versioned artifacts. Construction issues may load and inject them, but mode-contract content changes belong to the mode integration issues that own them.

### RPG Mode — Key Decisions

- Pre-play sequence is mandatory: world setup first, then character creation.
- Character creation is GM-led and conversational or accepts a completed sheet. Incomplete or ambiguous sheets trigger clarification before play begins, not mid-adjudication.
- Character sheet is first-class persistent state, not a conversation artifact.
- v1 supports original/custom settings only. Player-supplied Setting Canon Packs for licensed settings remain deferred.
- Dice handling has Player rolls and AI rolls modes.
  - Player rolls: the GM announces the check and applicable modifiers, then waits for the Sojourner to report the result before narrating the outcome.
  - AI rolls: code generates the result and the GM shows the result for player-character actions.
- Hidden rolls are hidden from the Sojourner, not the backend.
- Code generates and records trust-relevant rolls.
- GM cheating is prompt/config behavior except `gm_cheating = off`, which code enforces as roll-result preservation. The UI should warn plainly that disabling GM cheating means all roll results are honored absolutely, including climactic failures.
- d20 is the v1 supported adapter target.
- Session type is a configuration parameter: Short Adventure / Campaign / Open-ended. It shapes pacing expectations and may drive gentle usage guidance for long-running campaigns.
- Tone is a frontend dropdown, not free text: Gritty / Balanced / Forgiving / Danger-free. It calibrates consequence severity and GM posture without overriding roll-result preservation when `gm_cheating = off`.
- RPG UI may expose a compact world-state sidebar for visible character/world state such as HP, inventory, relationship meters, and location, with hidden-state visibility controlled by mode rules.

### Branching Mode — Key Decisions

- Branching uses a typed mode-specific output contract.
- Prose remains literary; interaction affordances are structured.
- Branch options, freeform availability, branch-count range, branch presentation state, Branching cadence/verbosity, and selection metadata are validated/persisted for UI use.
- Interaction style is persisted configuration:
  - Freeform only.
  - Hybrid freeform + branch cards.
  - True CYOA / choices-only.
- Branching cadence/verbosity is also persisted configuration with Interactive / Balanced / Immersive values. It applies to all Branching interaction styles. In Freeform-only it controls storyteller response verbosity and pacing; in Hybrid and True CYOA it also shapes branch-card presentation cadence where cards are enabled.
- Interaction style and cadence can later change through OOC by updating persisted Branching configuration.
- Tone is not a separate rigid dropdown for Branching mode. It lives in the world/story summary alongside genre, setting, and narrative register so the Sojourner can describe the actual story they want.
- Setup uses the hybrid model: structured setup fields followed by a lightweight story-architect confirmation pass to catch setup problems before they infect the story.
- Length preference is a configuration parameter: Short Story / Novella / Novel. It shapes pacing-stage progression.
- Story seeds and supporting cast are optional setup fields. Sojourners may provide dramatic hooks, premises, allies, rivals, or antagonists without being forced to do so.
- The Interactive / Balanced / Immersive vocabulary is preserved as the Branching cadence/verbosity setup dial. It is not a replacement for interaction style: interaction style controls input mechanism, while cadence controls storyteller verbosity and decision-point pacing.
- In True CYOA, ordinary freeform narrative text is not valid story input. If such text reaches the backend without being classified as OOC, the system must reject it as invalid for that interaction style and ask the Sojourner to choose a branch or use OOC to change configuration.
- Future richer Branching UX — visual story map, non-destructive What If? branches, branch-timing controls beyond the v1 cadence/verbosity dial, and optional external canon/lore packs — must not be architected against, but remains deferred unless separately scoped.

### Writing Mode — Key Decisions

- Persona selection determines relationship orientation.
- Personas are divided into Mentors and Peers.
- Mentors: Chiron, Merlin, Vidura.
- Peers: Odin, Athena, Thoth.
- The roster is intentionally small in v1: three Mentors and three Peers. It provides meaningful choice without exploding prompt, UI, and test surface area.
- Setup uses the hybrid model: structured setup fields followed by the selected persona opening with a brief confirmation and one or two clarifying questions specific to that orientation. Work does not begin until the working relationship and immediate goal are clear.
- Writing mode exposes authoring controls where useful: tense, POV, length, style density, dialogue/narration ratio, genre conventions, and explicit beat or milestone constraints.
- Issue 17 owns setup, persona behavior, prompt-contract injection, beat constraints, mode-specific orchestration behavior, and minimal future-compatible version-history pointers.
- Full version-history tooling is deferred unless a dedicated later issue scopes it. Deferred does not mean forbidden: draft branching, restore/rollback, compare views, manuscript evolution tooling, and richer authoring controls must not be architected against.
- Minimal future-compatible version-history pointers may store lightweight identifiers, provenance references, or links to prior draft artifacts/turns; they must not imply full snapshot trees, restore workflows, compare views, branch management, or manuscript-versioning UI in v1.
- Persona expansion across RPG and Branching is a future consideration. v1 should not couple persona behavior so tightly to Writing mode that future cross-mode personas become unnecessarily difficult.

### OOC Communication — All Modes

The UI provides an explicit OOC button that prepends `[OOC]`. Sojourners may also type it manually. OOC classification is handled before context assembly. OOC does not advance story or canon unless a later mode-specific contract explicitly defines a safe, typed configuration update, such as Branching interaction-style changes.

---

## Item 7 — Contradiction Checker Architecture Is Decided

v1 approach: lightweight model-assisted synchronous gate on Writer output.

Baseline scope:

- recent context
- active Story Bible context
- Rolling Summary
- Rules Package slice when present
- Retrieval Memory when Issue 18 supplies it

The checker catches clear, attributable continuity violations, including but not limited to dead characters acting, item acquisition drift, location/name drift, POV/tense shift, and locked-fact violations.

Output is gated on the checker clearing. Nothing is delivered to the Sojourner until it does.

The checker is not a rules adjudicator. It may flag a rules-related contradiction only when the provided Rules Package slice explicitly establishes a fact and Writer output explicitly contradicts it. Broader RPG rules logic belongs to Issue 15.

---

## Item 8 — Cost Model and Pricing Architecture Are Estimated

The business model assumes one canonical Sojourn orchestration path for all real product access paths. Commercial differentiation is handled through billing structure, credit allowance, provider billing path, and hosted-service entitlements — not by removing continuity functions or safety guardrails.

### Core Pricing Architecture

| Access Path | Revenue Shape | Cost Driver |
|---|---|---|
| Hosted Subscription | Monthly subscription with included hosted credits | Model usage + storage + hosted services. |
| Hosted Top-Ups | One-off credit purchases | Incremental model usage + payment overhead. |
| Starter Access (optional) | Small paid entry package / trial subscription using normal hosted credits | Model usage + storage + hosted services + support + payment overhead. |
| BYOK Perpetual License | One-time purchase | Product access, onboarding, first-year Cloud Services bundle. |
| BYOK Cloud Services Renewal | Optional annual renewal after year one | Storage, sync, hosted ingestion, remote access, service maintenance. |
| Institutional (future) | Per-seat / pooled credit / capped usage | Aggregate hosted usage + admin/service overhead. |
| Marketplace (future) | Transaction fee / seller services / discovery | Payment rails, moderation, hosting, payout operations. |

Continuity quality is invariant across access paths.

### Hosted Credits

Hosted credits are provider-neutral, usage-backed entitlement units. They are computed from structured turn/pass usage metrics through a configurable conversion policy.

Issue 13 owns the durable accounting architecture and enforcement path. Issue 14 supplies provider/platform-specific normalization and calibration inputs. Provider-specific dollar-equivalent accounting does not live inside the entitlement core.

A flat per-turn decrement is rejected because it hides burn-rate variation and breaks usage transparency.

### Per-Turn Cost Basis

The underlying per-turn cost model assumes the full Sojourn orchestration path:

```text
[Input Safety Preflight, conditional] → Planner → Writer → [Output Safety Audit, conditional] → Extractor → Contradiction
```

Safety costs are conditional:

- Input Preflight runs when provider/risk policy requires it.
- Output Audit runs when provider/risk policy requires it.
- Provider refusals halt the pipeline before downstream passes run.

Context remains split into a stable context region and a volatile suffix. Provider/platform adapters determine whether stable context reuse becomes an actual cache hit.

### Cache Economics — Adapter-Calibrated, Not Universal

Within a single turn and between turns, there is no universal cache-hit assumption. Stable/volatile separation creates the opportunity for reuse; the active provider/platform adapter determines whether that opportunity becomes a real discount.

Issue 14 must document verified assumptions for supported adapters, including cross-pass reuse, pass-specific system/tool effects, TTL behavior, cache metric semantics, and pricing implications.

### BYOK Pricing Logic

BYOK has two commercial components:

1. **Perpetual BYOK License** — permanent right to use Afterworlds with user-supplied provider credentials, local orchestration, local SQLite persistence, local ChromaDB retrieval memory, and full pipeline parity.
2. **Cloud Services Renewal** — optional annual renewal after the included first year, covering hosted storage, sync, backup, remote access, hosted ingestion, and other recurring server-side costs.

If Cloud Services lapse, hosted active-use services suspend. Existing hosted user content remains available for read/export/download and later reactivation. Ongoing turn generation continues through the local BYOK path rather than uncompensated hosted retrieval/storage.

“Self-hosted retrieval memory” means locally operable by the Sojourner’s Afterworlds installation, not necessarily hosted by AfterworldsAI.

### Payment Platform Ownership

Issue 20 is billing/BYOK visibility and configuration only. It does not implement actual hosted top-up purchase/redemption.

A dedicated billing-platform/payment-integration issue lands after Issue 21 and before public launch. It is a commercial launch blocker, not a spine-demo prerequisite.

That issue owns payment-provider integration, checkout, webhooks, idempotency, failed-payment/refund/chargeback representation, reconciliation, translation of successful payment events into Issue 13 entitlement mutations, and operational/support events for Issue 22.

### Pricing Commitments and Unknowns

Committed:

- one canonical Sojourn orchestration path across access paths
- provider-neutral hosted credits
- configurable credit conversion policy from structured usage metrics
- hosted subscriptions with explicit credits
- top-ups rather than silent degradation
- BYOK perpetual license + first-year Cloud Services
- optional annual Cloud Services renewal
- support/audit/deletion minimums for responsible launch

Still to finalize before public pricing lock:

- exact monthly hosted credit allotments
- top-up package sizes and pricing
- rollover policy and cap
- exact BYOK license price
- exact annual Cloud Services renewal price
- institutional pricing structure
- marketplace fee structure
- provider/platform-specific cache calibration used by production pricing

---

## Item 9 — Construction Order Is Defined

### Issues 1–12c — Foundation and Pipeline

1. Repo skeleton, config, linting, test harness, CI scaffold.
2. Core models.
2a. Character Sheet Architecture Correction.
3. SQLite persistence and CRUD.
4. Story Bible schema and service.
5a. Rules Package schema and data model.
5b. Rules Package ingestion pipeline.
6. Rolling Summary service.
7. Intent Classification.
8. Context Builder.
9. Minimal Writer Path.
10. Extractor Classification Policy.
11. Lightweight Contradiction Checker.
12a. Planner Pass.
12b. Safety Service: Input Preflight and Conditional Output Audit.
12c. Full Pipeline Orchestration.

### Issues 13–21 — Entitlements, Providers, Modes, UI, and Spine

13. Runtime Entitlement State and Enforcement.
14. Provider Routing, Capability Profiles, Cache Adapters, Refusal Fallback, and BYOK Credential Management.
15. RPG Mode Integration.
16. Branching Mode Integration.
17. Writing Mode Integration.
18. ChromaDB Retrieval Memory.
19. React/Vite Frontend and Minimal FastAPI API Surface.
20. Billing/BYOK Visibility and Configuration.
21. Final Narrative Spine Demo.

### Launch Blockers After Issue 21

22. Operations, Support, and Compliance Minimums.
23. Billing Platform / Payment Integration.

Issue 21 remains the narrative spine gate. It is necessary but not sufficient for public launch.

---

## Item 10 — Each Issue Has Boundaries and Acceptance Criteria

### Issue 1 — Repo Skeleton

- **Goal:** Establish project structure, tooling, and CI scaffold before application code.
- **In scope:** directory structure, `pyproject.toml`, Black, Ruff, mypy strict, pytest, GitHub Actions, PR template, detect-secrets.
- **Out of scope:** application logic, models, routes, services.
- **Acceptance:** CI passes; branch protection active; PR template appears; all placeholder docs exist.

### Issue 2 — Core Models

- **Goal:** Define backbone data objects.
- **In scope:** Story, Arc, Chapter, Node, Turn, WorldState, CharacterState, mode-specific session states, first-class RPG character sheet.
- **Out of scope:** persistence, Story Bible schema, Rules Package schema, routes/services.
- **Acceptance:** typed models preserve Turn/Node distinction, static/dynamic partitions, and character sheet as structured persistent object.

### Issue 2a — Character Sheet Architecture Correction

- **Goal:** Correct drift by making the concrete v1 sheet explicitly ruleset-specific.
- **In scope:** preserve first-class sheet, ruleset-specific concrete model, structural validation only at base layer.
- **Out of scope:** Rules Package, adjudication services, broad cross-system abstractions.
- **Acceptance:** base persistence model does not encode universal RPG rule semantics.

### Issue 3 — SQLite Persistence and CRUD

- **Goal:** Persist and retrieve Issue 2/2a models with full fidelity.
- **In scope:** SQLAlchemy/Alembic schema, CRUD, WAL mode, FK enforcement, explicit partitions.
- **Out of scope:** Story Bible, Rules Package, ChromaDB, API routes.
- **Acceptance:** round-trip fidelity, explicit relational partitioning, character sheet table chain, FK/WAL tests.

### Issue 4 — Story Bible Schema and Service

- **Goal:** Implement structured, partitioned, append-safe canon store.
- **In scope:** static/dynamic/provisional partitions, Events Ledger, Locked/Forbidden Facts, Relationship Ledger, CRUD, active context window, proposal staging.
- **Out of scope:** Extractor classification logic, Context Builder, Rolling Summary, Rules Package.
- **Acceptance:** no hard delete, confirmation enforcement for static changes, active context assembly, staging supports Extractor routes.

### Issue 5a — Rules Package Schema and Data Model

- **Goal:** Define Rules Package schema foundation.
- **In scope:** RulesPackage, RuleSource, RuleChunk, MechanicalEntity, provenance, RuleOverride, minimal deterministic read surface, `get_active_rule_slice`.
- **Out of scope:** ingestion pipeline, semantic retrieval, live adjudication.
- **Acceptance:** Rules Package separate from Story Bible; no FK to story/canon tables; stable typed active rule slice.

### Issue 5b — Rules Package Ingestion Pipeline

- **Goal:** Ingest and publish the full approved d20/SRD corpus into the development environment.
- **In scope:** parsing, chunking, normalization, manifest, publication flow, idempotency, minimal vector write path.
- **Out of scope:** schema changes to 5a models, live adjudication, full retrieval design.
- **Acceptance:** published package queryable; manifest distinct and unique; idempotent; vector index populated; interim Chroma choices flagged for Issue 18.

### Issue 6 — Rolling Summary Service

- **Goal:** Implement compressed persistent narrative history.
- **In scope:** versioned schema, coverage metadata, N-turn trigger, generation service, current/history retrieval.
- **Out of scope:** Context Builder integration, pipeline calls, token budgeting.
- **Acceptance:** summaries versioned and append-safe; coverage uniqueness and current-row uniqueness enforced.

### Issue 7 — Intent Classification

- **Goal:** Classify Sojourner input before context assembly.
- **In scope:** v1 taxonomy including OOC, typed result schema, classification hints stub, model-call seam, malformed output handling.
- **Out of scope:** context assembly, mode-specific routing, downstream rewind behavior.
- **Acceptance:** typed result; no silent fallback; edge-case set documented; OOC detected.

### Issue 8 — Context Builder

- **Goal:** Assemble stable prefix and volatile suffix once per turn.
- **In scope:** typed `StablePrefix`, `VolatileSuffix`, `BuiltContext`, PassForwardLedger, Rules Package slice seam, RetrievalMemoryProvider seam.
- **Out of scope:** provider calls, prompt rendering, full ChromaDB retrieval, token budget enforcement.
- **Acceptance:** fixed assembly order; rule-slice conditional invocation; stable/volatile separation; no provider-specific cache behavior.

### Issue 9 — Minimal Writer Path

- **Goal:** Prove Sojourner input can produce parseable prose through a real provider path.
- **In scope:** Writer service, Anthropic rendering path, response parsing, Turn persistence, metrics.
- **Out of scope:** Planner, Extractor, Contradiction, Safety, orchestration.
- **Acceptance:** non-empty prose persisted as Turn; cache boundary honored; errors typed.

### Issue 10 — Extractor Classification Policy

- **Goal:** Implement Extractor pass and route typed proposals through Story Bible service.
- **In scope:** Extractor service, proposal discriminated union, tool-use parsing, `route_extractor_proposals`, EventKind column, transactional routing.
- **Out of scope:** orchestration, review UI for ratified proposals, contradiction checking.
- **Acceptance:** Extractor never writes canon directly; proposals routed atomically; natural keys resolved server-side.

### Issue 11 — Lightweight Contradiction Checker

- **Goal:** Implement synchronous contradiction pass on Writer output.
- **In scope:** Contradiction service, typed report/result, tool-use parsing, focused prompt contract.
- **Out of scope:** scheduling policy, side-effect coordination, regeneration policy, persistence.
- **Acceptance:** clear verdict derived from violations; checker writes nothing; output can be gated by 12c.

### Issue 12a — Planner Pass

- **Goal:** Implement standalone Planner pass.
- **In scope:** `PlannerService.plan`, typed `PlannerOutput`/`PlannerResult`, prompt contract, tool-use parsing, usage metrics.
- **Out of scope:** orchestration, Writer invocation, persistence, retrieval-query design.
- **Acceptance:** non-empty scene goal/next beat, valid facts list, optional notes, typed errors, no context mutation.

### Issue 12b — Safety Service: Input Preflight and Conditional Output Audit

- **Goal:** Implement callable Safety service for input/output evaluation.
- **In scope:** `SafetyService.check`, `SafetyTarget`, typed concerns/report/result, prompt contract, evidence validation, typed errors.
- **Out of scope:** deciding when Safety runs, provider whitelist, provider-routing fallback, UI messaging.
- **Acceptance:** verdict derives from concerns; failures do not silently allow; provider refusals from other passes are not Safety verdicts.

### Issue 12c — Full Pipeline Orchestration

- **Goal:** Wire Issues 7–12b into one end-to-end Sojourn Turn.
- **In scope:** OrchestratorService, SafetyPolicy, OOC short-circuit, PassForwardLedger composition, provider-refusal handling, transaction boundaries, delivery gating, rollback-safe Extractor/Contradiction coordination, shared stable-context rendering utility.
- **Out of scope:** entitlements, provider routing/cache adapters, mode-specific overrides, full OOC protocols, ChromaDB retrieval implementation, streaming, retry/regenerate semantics.
- **Acceptance:** only delivered/OOC-handled Turns survive persistence; blocked/refused/errored outputs leave no surviving ordinary Turn or canon writes; dispositions are typed and exhaustive.

### Issue 13 — Runtime Entitlement State and Enforcement

- **Goal:** Implement authoritative runtime entitlement state and enforcement.
- **In scope:** hosted credit availability, configurable credit conversion policy, top-up balance/state as relevant to enforcement, BYOK license state, Cloud Services active/lapsed state, access-path and entitlement routing/enforcement decisions, and Cloud Services enforcement for hosted storage, sync, backup, remote access, hosted ingestion, and hosted runtime dependent on Afterworlds server resources.
- **Out of scope:** provider-specific calibration details and provider/platform routing owned by Issue 14, human support/reconstruction history owned by Issue 22, payment platform owned by Issue 23.
- **Deliverables:** entitlement models/services, enforcement decision API, tests for hosted/BYOK/Cloud Services states, storage/ingestion/service enforcement hooks, credit conversion policy hooks.
- **Acceptance:** runtime can determine whether hosted/BYOK/Cloud Services paths are available; Cloud Services lapse prevents uncompensated hosted storage/sync/backup/remote-access/ingestion/runtime use while preserving read/export/download/reactivation access as specified; hosted credits mutate only through approved entitlement events; support history is not collapsed into runtime state. Issue 13 routing means access-path and entitlement enforcement, not provider/platform selection.

### Issue 14 — Provider Routing, Cache Adapters, Refusal Fallback, and BYOK Credential Management

- **Goal:** Implement v1 provider/platform routing surfaces and local-first BYOK credential management.
- **In scope:** Anthropic direct, OpenRouter, provider/platform routing, capability profiles, constrained provider-refusal fallback, typed refusal events, cache-capability adapters, provider/platform usage normalization/calibration, backend `CredentialStore`, OS/local keychain storage where available, metadata-only SQLite storage, validation/test-call behavior, redaction rules.
- **Out of scope:** access-path/entitlement enforcement owned by Issue 13, OpenAI direct, Google/Gemini direct, cloud sync/storage of raw BYOK keys, payment platform, frontend settings UI beyond backend contract.
- **Deliverables:** provider adapter interfaces, Anthropic/OpenRouter implementations, refusal/fallback routing, cache behavior documentation/tests, CredentialStore implementation, redaction tests.
- **Acceptance:** eligible fallback attempts at most once within same access path/fallback pool; no fallback after Safety BLOCK; no silent hosted/BYOK boundary crossing; BYOK fallback pools are limited to provider credentials/surfaces the Sojourner has configured; raw API keys never persist in SQLite/logs/telemetry/exports/backups/support/admin/Story/Turn data; cache assumptions are adapter-verified rather than universal. Issue 14 routing means provider/platform selection and fallback, not access-path entitlement enforcement.

### Issue 15 — RPG Mode Integration

- **Goal:** Integrate RPG mode over the shared Sojourn pipeline.
- **In scope:** prompt contract loading, mandatory pre-play sequence, character sheet use, bounded d20 Rules System Adapter, deterministic dice rails, hidden-roll handling, `gm_cheating = off` invariant, rule-slice request construction, RPG Adjudication Loop wiring, and a visible-state payload/DTO for RPG information the frontend may render such as HP, inventory, relationship meters, and location.
- **Out of scope:** new Rules Package schema, broad cross-system adapter framework beyond bounded d20, frontend UI rendering/polish beyond necessary integration, executable mechanics generated from ingestion.
- **Deliverables:** RPG mode orchestration layer, d20 adapter, dice/audit services, hidden-roll visibility controls, visible-state DTO/service contract, tests for rules/roll invariants.
- **Acceptance:** LLM may request/propose rolls but not author trust-relevant numeric results; hidden rolls are backend-visible and code-generated; `gm_cheating = off` preserves results; Rules Package / Rules System Adapter / Character Sheet Model / RPG Adjudication Loop remain separate; Issue 15 defines visible-state payload shape while Issue 19 renders it through the frontend/API shell.

### Issue 16 — Branching Mode Integration

- **Goal:** Implement Branching mode with typed output and typed interaction configuration.
- **In scope:** Branching prompt contract loading, typed output contract, branch options, freeform availability, branch-count range, branch presentation state, branch-selection metadata, persisted interaction style, persisted Branching cadence/verbosity, True CYOA invalid-freeform handling, OOC configuration update path, and clear separation between base `Node.branching_logic` pointers and `mode_metadata.branching` presentation/configuration/selection metadata.
- **Out of scope:** visual story map, non-destructive What If? branching, new orchestration architecture, untyped branch prose parsing, migrating canonical branch pointers out of the base Node field.
- **Deliverables:** Branching mode service/contracts, config persistence for interaction style and cadence, UI-facing DTOs, invalid-input handling for True CYOA, tests for all interaction styles and cadence settings.
- **Acceptance:** branch options are not loose prose; Freeform-only, Hybrid, and True CYOA behave distinctly; branch-count ranges enforced; Branching cadence/verbosity affects storyteller response density for all styles and branch presentation cadence where branch cards exist; OOC style/cadence change updates persisted configuration; ordinary non-OOC freeform text in True CYOA is rejected as invalid for that style; canonical graph pointers remain in `Node.branching_logic` while `mode_metadata.branching` stores presentation/configuration/selection metadata.

### Issue 17 — Writing Mode Integration

- **Goal:** Implement Writing mode over the shared pipeline.
- **In scope:** setup flow, persona selection and behavior, Mentor/Peer relationship orientation, prompt-contract injection, beat constraints, mode-specific orchestration behavior, minimal future-compatible version-history pointers.
- **Out of scope:** full version history, draft branching, restore/rollback workflows, compare views, broad manuscript evolution tooling.
- **Deliverables:** Writing mode service/contracts, persona injection, beat constraint handling, minimal pointer schema/usage, tests for Mentor/Peer behavior routing.
- **Acceptance:** Chiron/Merlin/Vidura operate as Mentors; Odin/Athena/Thoth operate as Peers; setup and prompt injection preserve user authorship; minimal pointers may store lightweight identifiers/provenance references/links to prior draft artifacts or turns; v1 does not implement snapshot trees, restore workflows, compare views, branch management, or manuscript-versioning UI; deferred manuscript-evolution tooling is not smuggled into v1 or architected against.

### Issue 18 — ChromaDB Retrieval Memory

- **Goal:** Design and implement ChromaDB-backed retrieval memory.
- **In scope:** mandatory ADR/owner checkpoint before implementation; vector retrieval service; collection schema; metadata; chunking; embeddings; retrieval defaults; write triggers; update/delete/reindex semantics; query construction; Context Builder seam integration.
- **Out of scope:** resolving retrieval design silently in implementation, violating Rules Package authority model, writing blocked/undelivered material into ordinary retrieval memory.
- **Deliverables:** owner-accepted ADR, ChromaDB service, retrieval provider implementation, tests for relevance/filtering/leakage/context integration.
- **Acceptance:** ADR receives explicit owner approval in the issue thread or PR before code proceeds; only delivery-cleared material becomes ordinary retrieval memory; no cross-story leakage; empty-result behavior defined; split into 18a/18b only if ADR surfaces larger unresolved issue.

### Issue 19 — React/Vite Frontend and Minimal FastAPI API Surface

- **Goal:** Implement the thin local-first browser UI and minimal API surface needed to exercise v1.
- **In scope:** React + Vite + TypeScript frontend skeleton; minimal FastAPI endpoints/DTOs for story creation, story listing/retrieval if needed, mode selection/setup handoff, turn submission, output display, status/error payloads; smoke/integration tests through existing services.
- **Out of scope:** Next.js, SSR, separate Node app server, Electron, new orchestration behavior, mode logic, entitlement logic, persistence architecture, provider routing, business policy.
- **Deliverables:** frontend shell, API routes, DTOs, service integration, tests.
- **Acceptance:** route handlers are thin; frontend can create/select story/mode, submit turn, and display output/status through existing services; no business logic leaks into HTTP code.

### Issue 20 — Billing/BYOK Visibility and Configuration

- **Goal:** Expose user-facing billing and BYOK state/configuration.
- **In scope:** hosted credit balance, estimated burn-rate communication, Cloud Services active/lapsed status, BYOK provider/key configuration UI over Issue 14 backend contract, provider selection, top-up visibility/eligibility messaging.
- **Out of scope:** actual payment/top-up transaction flow, checkout, webhooks, entitlement enforcement, support remediation workflows.
- **Deliverables:** UI/API for billing/BYOK state and settings, provider selection, key-entry flow using CredentialStore backend, tests for redaction and display state.
- **Acceptance:** Sojourner can see relevant credit/service/BYOK state and configure provider credentials without exposing raw keys; payment actions are visibility/eligibility only until the billing-platform issue.

### Issue 21 — Final Narrative Spine Demo

- **Goal:** Verify the first release-capable MVP narrative spine.
- **In scope:** end-to-end verification for Branching, RPG, and Writing; hosted and BYOK access paths; major v1 systems cooperating coherently; narrow integration fixes when contracts are already clear.
- **Allowed fixes:** DTO name mismatch, route wiring gap, dependency injection issue, fixture/setup issue, frontend/backend field mismatch, small orchestration seam where ownership is already clear.
- **Out of scope:** architecture, ownership, schema, prompt-contract, entitlement policy, provider behavior, retrieval design, mode semantics, user-facing feature-scope changes.
- **Deliverables:** final spine demo tests, documented findings, narrow integration fixes where allowed.
- **Acceptance:** all three modes work end-to-end; hosted and BYOK paths function; if a contract is wrong/incomplete, Issue 21 records and opens/splits follow-up rather than smuggling design work.

### Issue 22 — Operations, Support, and Compliance Minimums

- **Goal:** Provide minimum human-operable workflows for responsible v1 launch.
- **In scope:** support lookup, append-safe entitlement/support event history, controlled manual remediation with operator reason capture, deletion/export request workflow and status, basic anomaly visibility.
- **Out of scope:** full admin dashboard, BI analytics, CRM/ticketing system, fraud suite, enterprise reporting, payment integration.
- **Deliverables:** support-facing lookup path, event history, remediation service/UI path, delete/export workflow, anomaly surfacing, documentation.
- **Acceptance:** support can inspect access/credit/service state; transitions reconstruct in order; manual actions require reasons and logs; delete/export requests have defined status; no support action silently mutates state.

### Issue 23 — Billing Platform / Payment Integration

- **Goal:** Implement the full commercial payment platform after Issue 21 and before public launch.
- **In scope:** payment-provider integration, subscription/top-up checkout flows, webhook ingestion, payment-event idempotency, failed-payment/refund/chargeback representation, reconciliation hooks, translation of successful commercial events into Issue 13 entitlement mutations, operational/support events for Issue 22, user-facing state for Issue 20 to display.
- **Out of scope:** runtime entitlement enforcement, settings UI, support remediation workflows, narrative spine verification.
- **Deliverables:** payment integration, checkout/webhook services, idempotency/reconciliation tests, entitlement mutation bridge, support event emission.
- **Acceptance:** successful payments mutate Issue 13 runtime entitlements through the approved path; failed/refunded/charged-back payments are represented; webhooks are idempotent; operational events are available to Issue 22; commercial launch is blocked until this is done if hosted paid access/top-ups are offered.

---

## Item 11 — Repo Governance as Agent Coordination Protocol

Development uses issue-scoped branches and PR review.

Rules:

- Feature branches per issue: `feature/issue-N-short-description`.
- No direct commits to `main`.
- Open a PR for every issue.
- PRs are not merged without Codex review passing.
- No PR merges with failing CI.
- Every PR description includes Architecture Notes: either “No drift from design principles” or an explicit deviation/rationale.
- Scope creep is a review failure.
- Known Unknowns are not resolved silently.

Review-loop boundary rule:

If repeated review rounds focus on the same file/function/query/schema/service hotspot, or the feedback shifts from concrete defects to ownership/semantics/placement, stop treating the next comment as merely the next patch. Classify the remaining feedback as merge-blocking defect, scope/boundary problem, Known Unknown, or non-blocking improvement. Pause for owner decision when needed.

---

## Item 12 — CI Gates as Quality Handoff Contract

CI gates remain mandatory:

1. Black formatting.
2. Ruff linting.
3. mypy strict type checking.
4. pytest unit/integration tests.
5. pip-audit dependency scan.

Additional standing expectations:

- detect-secrets pre-commit scanning.
- no real provider calls in default CI.
- opt-in real-provider integration tests must be gated behind explicit credentials and flags.
- new code must meet the coverage threshold set by repo governance.
- any failing gate blocks merge.

### Architectural Invariant Tests by Issue

The following table is a construction checklist for explicit invariant tests. Individual issue specs may add more tests; this table records the cross-cutting tests that must not disappear during implementation.

| Invariant test | First issue that must enforce it |
|---|---|
| Story Bible schema is structurally separate from prose history and ordinary Turn/Node text. | Issue 4 |
| Story Bible records are soft-deleted / append-safe where specified; application behavior does not hard-delete canon records. | Issue 4 |
| Static Story Bible partition updates require explicit Sojourner confirmation. | Issue 4 |
| Rules Package tables carry no FK to Story, Arc, Chapter, Node, Turn, Story Bible, or session-state tables. | Issue 5a |
| Play-time Rules Package queries surface only published/enabled package content. | Issue 5a |
| Rolling Summary versions are append-safe, coverage-anchored, and unique by `(story_id, compressed_through_turn_id)`. | Issue 6 |
| Intent classification runs before Context Builder and produces a typed `IntentClassificationResult`. | Issue 7 |
| Context Builder assembles the stable prefix once per turn and does not reassemble it per pass. | Issue 8 |
| Stable prefix and volatile suffix are structured typed payloads, not concatenated strings. | Issue 8 |
| Rules Package slice retrieval is honored only when mode/intent/request policy allows it. | Issue 8 |
| Writer persists a Turn through the Issue 3 CRUD service and does not bypass persistence boundaries. | Issue 9 |
| Extractor writes only through Story Bible service routing; it never writes canon directly. | Issue 10 |
| Extractor event/state two-output behavior preserves both event ledger entries and current dynamic state when both apply. | Issue 10 |
| Contradiction verdict is derived from typed violations and blocks delivery when violations exist. | Issue 11 |
| Planner, Safety, Extractor, and Contradiction structured outputs fail closed on parse/validation errors. | Issues 10–12b |
| Orchestrator commits delivered Turn and Extractor writes together, and rolls both back on Safety block, provider refusal, pipeline error, or Contradiction block. | Issue 12c |
| OOC turns do not advance story/canon and are excluded from later ordinary narrative recent-turn windows. | Issue 12c |
| Provider/platform cache adapters realize generalized cache intent without moving provider-specific cache semantics into Context Builder or orchestration. | Issue 14 |
| Provider fallback never runs after Safety BLOCK and never silently crosses hosted/BYOK boundaries. | Issue 14 |
| Raw BYOK keys never persist in SQLite, logs, telemetry, exports, backups, support/admin views, or Story/Turn data. | Issue 14 |
| RPG trust-relevant roll results are generated/reported through code or Sojourner input; the LLM does not author numeric roll results. | Issue 15 |
| `gm_cheating = off` preserves trust-relevant roll results absolutely. | Issue 15 |
| Branching output separates canonical `Node.branching_logic` graph pointers from `mode_metadata.branching` presentation/configuration/selection metadata. | Issue 16 |
| Branching interaction style and Branching cadence/verbosity are persisted and tested independently. | Issue 16 |
| True CYOA rejects ordinary non-OOC freeform narrative input rather than silently treating it as story action. | Issue 16 |
| Writing minimal version-history pointers do not imply or implement full version history, restore/compare, or branch-management tooling. | Issue 17 |
| Retrieval Memory writes only delivery-cleared material and prevents cross-story leakage. | Issue 18 |
| Frontend/API route handlers remain thin and do not absorb orchestration, provider, entitlement, or business policy. | Issue 19 |
| Issue 20 displays billing/BYOK state and configuration without implementing payment flows. | Issue 20 |
| Issue 21 records/splits contract defects rather than smuggling architecture, schema, mode semantics, retrieval design, or entitlement changes into the spine demo. | Issue 21 |
| Issue 22 support/remediation actions are append-safe, reason-captured, and reconstructable. | Issue 22 |
| Issue 23 payment webhooks are idempotent and mutate runtime entitlements only through the approved Issue 13 path. | Issue 23 |

---

## Item 13 — Documentation Standards as Architectural Drift Detection

The architecture docs are binding references, not decorative wallpaper.

Required documentation behavior:

- Update `/docs/architecture/design.md` when a load-bearing architecture decision changes.
- Update `/docs/architecture/construction_readiness.md` when issue sequence, scope, or readiness changes.
- Update `/docs/architecture/known_unknowns.md` when an unknown is resolved, narrowed, or newly discovered.
- Add ADRs for material decisions made during implementation.
- PR Architecture Notes must explicitly call out deviations, deferrals, and boundary questions.

If implementation finds a materially better architecture, revise the spec/ADR first or in the same PR. Do not merge a quiet contradiction and call it clever.

---

## Item 14 — Business-Model-Sensitive Constraints for Builders

There is one canonical Sojourn orchestration path across real product access paths.

Builders must not:

- remove Planner, Writer, Extractor, Contradiction, or safety-envelope behavior from a paid access path to create tier differentiation
- silently degrade output quality when credits are exhausted
- conflate BYOK license rights with Cloud Services renewal state
- persist raw BYOK keys in SQLite, logs, telemetry, exports, backups, support/admin views, or Story/Turn data
- implement support remediation as opaque mutation without audit trail
- treat provider-specific cost metrics as universal accounting truth
- cross hosted/BYOK boundaries during provider fallback without explicit permission

Hosted credits are provider-neutral runtime entitlements. Starter Access, if offered, is a paid entry package using the same full orchestration path and normal hosted credits, not a degraded free tier. Cloud Services are hosted-service entitlements covering hosted storage, sync, backup, remote access, hosted ingestion, and hosted runtime dependent on Afterworlds server resources. Issue 13 owns access-path/entitlement enforcement; Issue 14 owns provider/platform routing and fallback; Issue 22 owns human reconstructability and support/compliance history.

---

## Item 15 — Known Unknowns Are Listed Explicitly

Known Unknowns must live in `/docs/architecture/known_unknowns.md` and be consulted before resolving unclear implementation questions.

Current or newly preserved unknowns include:

- Issue 18 ADR topics for ChromaDB retrieval memory.
- Production provider/cache calibration in Issue 14.
- Exact hosted pricing, credit allotments, top-up packages, rollover/cap policy, BYOK price, and Cloud Services renewal price.
- Future full Writing-mode version-history tooling, including draft branching, restore/rollback, compare views, and broader manuscript evolution tooling.
- Future direct OpenAI / Google / Gemini provider surfaces.
- Future local/open-weight or VPS-hosted open-weight provider surfaces, including quality, privacy, cost, hardware, and policy tradeoffs.
- Future canon-pack architecture for Branching/Writing external lore corpora.
- Future richer Branching/Writing UX, including visual story map, non-destructive What If? branches, branch-timing controls beyond the v1 cadence/verbosity dial, richer authoring controls, and possible persona expansion across RPG/Branching.

A Known Unknown is not an invitation to improvise. It is a tripwire with a name tag.

---

## Item 16 — Minimal End-to-End Slice Is Defined

The minimal release-capable spine is validated by Issue 21:

- Branching mode end-to-end.
- RPG mode end-to-end.
- Writing mode end-to-end.
- Hosted access path functioning.
- BYOK access path functioning.
- Core persistence, Story Bible, Rolling Summary, Retrieval Memory, and Rules Package interactions cooperating.
- Safety envelope, provider refusal handling, Extractor, and Contradiction behaving coherently.
- Frontend/API shell able to exercise the spine.

Issue 21 is verification-first. It can make narrow integration fixes only when ownership and contracts are already clear. It cannot absorb architecture or scope changes.

---

## Item 17 — The Handoff Trigger Is Chosen

The handoff trigger remains issue-based:

- After Issue 12c, formalize Issues 13–21 before implementation.
- After Issue 21 passes, do not treat the product as publicly launch-ready by default.
- Public launch additionally requires:
  - billing-platform/payment integration if hosted paid access or top-ups are offered
  - Issue 22 operations/support/compliance minimums
  - remaining security/compliance gates required by repo governance
  - owner approval that pricing, support, and data-handling policies are ready

Issue 21 passing means the narrative spine works. It does not mean the commercial machine has grown a conscience, a ledger, and a receipt printer. That is what Issues 22 and 23 are for.
