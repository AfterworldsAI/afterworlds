# Afterworlds: Design Document (v11)

*Revised May 2026 to integrate Owner Decisions #1–#14 from the CRD issue-drafting sequence. This revision preserves the v10 safety-envelope model and cache architecture while updating entitlement ownership, hosted-credit semantics, BYOK/Cloud Services behavior, provider targets, RPG adjudication boundaries, Branching interaction styles and cadence controls, Writing-mode Mentor/Peer terminology, retrieval-memory ownership, frontend stack, Starter Access retention, and the v1 launch sequence.*

*Safety remains an envelope around the generation core, not a mandatory fifth narrative pass. The core narrative pipeline is Planner → Writer → Extractor → Contradiction. Input Safety Preflight runs before Planner/Writer when orchestration policy requires it. Conditional Output Safety Audit runs after Writer and before Extractor/Contradiction when provider or risk policy requires it. Provider refusals during provider-backed passes are typed pass failures, not Safety verdicts.*

*Afterworlds owns provider-neutral cache intent, deterministic stable/volatile context separation, and stable-context reuse discipline. Provider/platform-specific cache realization — cache-key semantics, breakpoint or context-object strategy, TTL/retention controls, cache metrics, and verified hit behavior — belongs to provider adapters defined during Issue 14. Stable internal context identity is necessary for cache efficiency; it is not, by itself, a provider-agnostic guarantee of cache hits.*

---

## Core Philosophy

One shared narrative engine. Three UX contracts on top of it.

The platform is the **Sojourn Story State Machine** — not a chatbot wearing a cape.

The product promise is excellent continuity-aware storytelling. Commercial access paths, provider choices, and interface modes may differ, but no supported access path removes the core continuity pipeline or the safety envelope.

---

## 1. Terminology

Two concepts must stay distinct:

- **Turn** — one interaction unit: one Sojourner input plus one AI response.
- **Node** — one persisted story beat or state transition in the story graph.

These often correspond 1:1, but not always. In branching scenarios, a Node may encompass multiple Turns or represent an alternative path never actually traversed. Collapsing them is conceptual debt. Keep them separate throughout the codebase and data model.

Additional core terms:

- **Sojourner** — the user inhabiting, playing, or authoring inside an Afterworlds story.
- **Story Bible** — structured narrative canon. It is not prose history.
- **Rules Package** — ingested mechanical canon and source authority for RPG adjudication.
- **Rules System Adapter** — hand-authored executable helpers for deterministic rails in a supported RPG rules system.
- **Character Sheet Model** — persistent, ruleset-specific character state.
- **RPG Adjudication Loop** — the orchestration layer that uses the Rules Package, Rules System Adapter, Character Sheet Model, dice services, and the narrative pipeline.
- **Canon pack** — future external narrative/lore reference corpus for Branching or Writing modes. Canon packs are not Rules Packages.
- **Cloud Services** — Afterworlds-hosted persistence, sync, backup, remote access, hosted ingestion, and any hosted runtime dependent on Afterworlds server resources.
- **BYOK** — Bring Your Own Key/provider credentials. BYOK is a first-class product path, not a fallback.
- **Hosted credit** — a provider-neutral, usage-backed entitlement unit computed from structured turn/pass usage metrics through a configurable conversion policy.

---

## 2. Data Architecture

### Story Object Hierarchy

```text
Story
└── Arc
    └── Chapter
        └── Node (story beat / state transition)
            └── Turn (interaction unit)
```

### Node Schema

Every persisted story beat is a Node.

| Field | Description |
|---|---|
| `node_id` | Unique identifier. |
| `content` | Generated prose or dialogue. |
| `state_delta` | World mutations caused by this beat, such as inventory changes or relationship-state transitions. |
| `branching_logic` | Base Node field containing canonical graph pointers to next possible nodes. Branching-mode metadata may add presentation/configuration/selection detail, but canonical branch pointers do not migrate out of the base schema. |
| `intent_type` | Node-level representation: Action / Dialogue / AuthorInstruction / BranchChoice / Milestone. This is narrower than the full Turn intent taxonomy; the full Turn intent value `beat_milestone` maps to the Node-level `Milestone` representation when a story-graph milestone is persisted. |
| `metadata` | POV, location, mood, tense, timestamp, and similar mode-neutral metadata. |
| `mode_metadata` | Typed mode-specific metadata for RPG, Branching, or Writing. |

### Turn Schema

A Turn records one interaction unit.

| Field | Description |
|---|---|
| `turn_id` | Unique identifier. |
| `user_input` | One Sojourner input. |
| `assistant_output` | One AI response. |
| `timestamp` | Time of the interaction. |
| `intent_classification` | Full `IntentClassificationResult` produced before context assembly. |
| `node_id` | Link to the associated Node when applicable. |

A Turn is not a Node. A Node is not a Turn. This distinction survives persistence, service contracts, tests, and UI assumptions.

### The Story Bible

The Story Bible is structured canon — not prose and not a chat transcript. It is the contract the AI must honor.

It contains, at minimum:

- setting summary and world rules
- cast entries with static/dynamic field separation
- locked facts that cannot be undone
- forbidden facts that cannot happen
- relationship ledger entries
- timeline and Events Ledger entries
- unresolved plot threads
- provisional Extractor proposals awaiting ratification

The Story Bible has three partitions:

| Partition | Contents | Mutation policy |
|---|---|---|
| Static | Setting summary, world rules, cast profiles, locked facts, forbidden facts | Written at setup or explicit confirmation. Requires Sojourner confirmation to change. |
| Dynamic | Current relationship states, active world conditions, ongoing plot threads, transient character/world state not owned by the character sheet | Extractor-maintained and append-safe. Prior values remain reconstructable. |
| Provisional | Extractor-proposed updates pending ratification | Staged separately. Not visible as canon until ratified. |

The Extractor proposes Story Bible updates. It does not write canon directly.

### The Rules Package

Rules do **not** live inside the Story Bible. The Story Bible governs fictional canon; the Rules Package governs mechanical canon. They must remain structurally separate.

A Rules Package is a versioned, modular, externally stored corpus containing:

- core rule text and subsystem chunks
- structured mechanical entities: conditions, actions, spells, items, stat blocks, and similar records
- rule metadata covering system, source, precedence, enabled/disabled status, and publication state
- source provenance and source authority ordering
- house-rule and package-patch overrides
- retrieval and indexing support for play-time lookup

**Ingestion model:** rulebooks, licensed/open materials, or approved user-supplied documents are processed through an offline/admin ingestion pipeline into SQL and vector indexes. The live GM model does not build the Rules Package during play and does not receive whole rulebooks in context.

**Play-time model:** the Context Builder and RPG integration retrieve only the rules relevant to the current turn. Deterministic calculations should move to code/services where practical. The model narrates and adjudicates from retrieved rule slices rather than “remembering” a system wholesale.

**v1 assumption:** d20 is the first curated Rules Package, based on the approved SRD ingestion path. A bounded d20 Rules System Adapter is the first supported deterministic rail.

A Rules Package may exist without a compatible Rules System Adapter. Such a package can be ingested and queried, but it cannot be offered as a fully supported adjudicated RPG system until a compatible adapter exists.

### Rules System Adapter

The Rules System Adapter is executable, hand-authored, system-specific code. It owns deterministic helpers that cannot safely be left to prose generation:

- dice generation and result preservation
- roll visibility rules
- simple modifier aggregation when code has the required data
- enforcement of `gm_cheating = off`
- audit records for trust-relevant rolls and adjudication inputs
- other bounded deterministic helpers approved for the system

Rules ingestion does not generate executable mechanics. Each supported RPG system with deterministic rails needs a hand-authored adapter.

### Character Sheet Model

The RPG character sheet is a first-class persistent object and is ruleset-specific. It is not a blob, not a freeform field, and not mode session state.

The concrete v1 sheet is d20/D&D-derived and includes typed mutable resources such as current and maximum HP, spell slots, inventory, class, stats, skills, and equipment. The character sheet binds to the active Rules Package by identifier. Rules meaning and legality are interpreted by the Rules Package plus adjudication layer; the base persistence layer must not encode universal RPG rule assumptions.

### Canon Packs

Canon packs are future external narrative/lore corpora for Branching and Writing modes. They reuse the ingestion/retrieval pattern where appropriate but do not carry mechanical adjudication authority. They are deferred beyond the current v1 construction plan unless a later issue explicitly scopes them.

---

## 3. Memory Architecture

Six memory layers remain distinct.

| Layer | Contents | Inclusion |
|---|---|---|
| Immediate | Last ~10 recent narrative turns verbatim | Always for ordinary narrative windows; OOC turns remain persisted for audit/history but are excluded from later narrative recent-turn windows by `RecentTurnReader` unless a later issue explicitly defines a different retrieval surface. |
| Rolling Summary | Compressed narrative history, auto-updated every N turns | Always when present. |
| Story Bible | Structured canon and active context window | Always. |
| Rules Package | Retrieved mechanical canon or future canon-pack slices | On demand by mode and intent. |
| Retrieval Memory | Vector DB of past scenes/events and other approved retrieval records | On demand. |
| Contradiction Checker | Synchronous check of Writer output against provided canon and context | Every ordinary narrative turn; retrieval depth may expand later, but the checker itself is core. |

### Retrieval Memory

ChromaDB remains in v1 scope.

Issue 18 owns ChromaDB retrieval-memory design and implementation. It begins with a mandatory ADR / owner checkpoint before implementation proceeds. The ADR must resolve, at minimum:

- collection schema for story retrieval memory and rules/corpus vector use without violating the Rules Package authority model
- metadata shape, including story/node/turn provenance, mode, timestamps, source type, chunk kind, and fields needed for filtering/debugging
- scene/document chunking policy
- embedding strategy and configuration surface
- retrieval defaults: top-k, score threshold behavior, filtering rules, and empty-result behavior
- write triggers and timing
- update/delete/reindex semantics
- retrieval query construction
- how results enter the existing `RetrievalMemoryProvider` / `StablePrefix.retrieval_memory` seam
- test obligations for retrieval relevance, metadata filtering, non-cross-story leakage, and Context Builder integration

Only delivery-cleared material becomes ordinary retrieval memory. Prose blocked by Safety, Contradiction, provider refusal, or pipeline error must not be written as ordinary retrieval memory.

The ADR is accepted only through explicit owner approval in the issue thread or PR before implementation code proceeds. If the ADR surfaces a larger unresolved question, split the work into Issue 18a design and Issue 18b implementation. Otherwise keep it as one gated Issue 18.

### Contradiction Checker

The Contradiction Checker catches clear, attributable continuity violations before the Sojourner sees the output.

Representative categories include:

- dead characters speaking or acting
- items in inventory that were never acquired
- location or name drift
- POV or tense shift mid-scene
- violated locked facts

The checker runs on Writer output, not merely on input context. A contradiction the Sojourner reads and then gets corrected on the next turn has already damaged the experience. Continuity checking is part of the product, not a premium ornament.

---

## 4. Narrative Orchestration Pipeline

Every ordinary narrative turn passes through the Sojourn orchestration path. Mode, access path, and task complexity may influence model class, retrieval depth, and billing behavior. They do not determine whether the core narrative pipeline or safety envelope exists.

The core narrative pipeline is:

```text
Planner → Writer → Extractor → Contradiction
```

The safety envelope wraps that core:

- **Input Safety Preflight** — runs before Planner/Writer when orchestration policy requires it.
- **Provider Refusal Handling** — happens during any provider-backed pass; refusal is a typed pass failure, not a Safety verdict.
- **Conditional Output Safety Audit** — runs after Writer and before Extractor/Contradiction when provider or risk policy requires it.

Practical shape:

```text
[Input Safety Preflight, when required]
Planner
Writer
[Output Safety Audit, when required]
Extractor
Contradiction
Deliver / Persist
```

If input violates Afterworlds policy, the system stops before generation starts. If Writer output violates policy, the system stops before Extractor and Contradiction. The Extractor must not extract canon from prose that will never be delivered.

### Step 1 — Intent Classification

Intent is classified before context assembly.

The v1 intent taxonomy includes:

- in-character action
- dialogue
- author instruction
- branch choice
- beat milestone
- rewind / retry / regenerate
- lore question
- OOC

The classifier produces a typed result. No downstream component should infer intent from raw input after the classifier has run. `beat_milestone` is the full Turn-level intent name; `Milestone` is the narrower Node-level `intent_type` representation when that intent becomes a persisted story-graph milestone.

### Step 2 — Context Assembly

The Context Builder assembles a stable prefix once per turn and a volatile suffix once per turn. The stable prefix is shared across provider-backed passes for cache efficiency and context consistency.

Canonical order:

```text
[System prompt + mode contract]
[Story Bible active context]
[Rolling summary]
[Retrieved relevant Rules Package or canon-pack slices as needed by mode]
[Retrieved relevant memories]
[Recent turns verbatim]
[Current input + classified intent]
```

The structured internal envelope remains provider-neutral. Provider-specific rendering belongs downstream to pass renderers and provider adapters.

### Step 3 — Core Pass Responsibilities

| Pass | Function |
|---|---|
| `[Input Safety Preflight]` | Evaluates Sojourner request against Afterworlds policy before generation starts. Conditional. |
| Planner | Produces scene goal, next beat, facts needed, and optional structural notes. |
| Writer | Produces polished prose/dialogue or OOC handler text where applicable. |
| `[Output Safety Audit]` | Evaluates Writer output against Afterworlds policy before downstream state changes. Conditional. |
| Extractor | Pulls new facts, state deltas, continuity updates, unresolved threads, and events from Writer output; proposes Story Bible updates. |
| Contradiction | Checks Writer output against Story Bible and assembled context before delivery. |

### Step 4 — Extractor Update Policy

The Extractor emits typed proposals. It never bypasses the Story Bible service.

| Classification | Handling |
|---|---|
| Locked fact | Stage and require explicit Sojourner confirmation before canon commit. |
| Soft fact | Stage and auto-ratify with low-confidence semantics encoded by proposal type. |
| Transient state | Stage and auto-ratify as current dynamic canon. |
| Unresolved thread | Queue to unresolved-thread tracking; do not treat as locked canon. |
| Event | Append through the Events Ledger `add_event` path with event kind and retention significance. |

An Extractor that auto-canonizes everything will hallucinate trivia into permanent law within a few chapters. This policy prevents that.

### Step 5 — Persistence

A delivered ordinary narrative turn persists:

- the Turn
- the associated Node or Node update
- approved state deltas
- Extractor-routed Story Bible updates
- rolling summary updates when threshold conditions are met
- retrieval-memory writes for delivery-cleared material

Blocked, refused, or errored outputs do not survive as ordinary delivered narrative state.

### Step 6 — Optional Multimodal

Deferred beyond v1:

- scene image generation from Node metadata
- TTS narration
- ambient audio triggers

These are downstream presentation layers. They must not become a substitute for the text pipeline’s canon discipline.

---

## 5. The Three Modes

All three modes run on the same Sojourn orchestration path. They differ in prompt contract, setup flow, mode-specific state, UI affordances, and orchestration details.

### RPG Mode

RPG mode presents the AI as a Game Master running a d20-based tabletop RPG.

Core commitments:

- Consequence-first narration.
- Preserve Sojourner agency.
- Never tell the player what their character feels except under clear in-world influence such as magic, telepathy, or madness.
- Use dice for trust-relevant conflict.
- Maintain rule-set consistency.
- Keep hidden information hidden from the Sojourner while preserving backend auditability.

#### Setup

Pre-play is mandatory:

1. **World setup** — the Sojourner describes the original/custom setting. The GM confirms understanding and asks critical clarifying questions.
2. **Character creation** — the GM leads conversational creation or accepts a completed sheet. Play does not begin until the sheet is complete enough to adjudicate.

v1 supports original and custom settings only. Player-supplied Setting Canon Packs for licensed settings are deferred.

#### Configuration and UI Notes

RPG setup keeps the older player-configuration intent while respecting the newer deterministic-rails architecture.

- **Session type** is a configuration parameter: Short Adventure / Campaign / Open-ended. It shapes pacing expectations and may drive gentle usage guidance for long-running campaigns.
- **Tone** is a frontend dropdown, not free text: Gritty / Balanced / Forgiving / Danger-free. It calibrates consequence severity and GM posture without overriding roll-result preservation when `gm_cheating = off`.
- **GM cheating** remains player-configurable prompt behavior except for the code-enforced `gm_cheating = off` invariant. The UI should warn plainly that disabling GM cheating means all trust-relevant roll results are honored absolutely.
- **World-state presentation** may include a compact sidebar for visible state such as HP, inventory, relationship meters, and location. Hidden information remains hidden from the Sojourner while staying backend-visible for auditability.

#### Dice and Adjudication

Code owns deterministic RPG rails and auditability. The model performs rules interpretation and narrative adjudication from retrieved Rules Package slices.

The LLM may request or propose rolls. It may not author numeric results for trust-relevant rolls.

Dice handling has two player-visible modes:

- **Player rolls** — the GM announces the check and applicable modifiers, waits for the Sojourner to report the result, and does not narrate the outcome before the roll exists.
- **AI rolls** — code generates the result and the GM shows the result for player-character actions.

Hidden rolls are hidden from the Sojourner, not from the backend. Hidden rolls are generated by code, recorded internally, and passed to the model only as resolved adjudication facts with player-facing visibility constraints.

This section describes dice handling at the conceptual level only. The wire-level contract — the
structured `RollInstructionSnapshot`/`RollTerm` representation, multi-die and multi-term pools, typed
adjustments, mechanical decisions, and the persisted `ActionResolutionSequence` that batches mechanically
linked rolls to one narration boundary — is specified in ADR-015b, which amends ADR-015's narrower
player-roll contract. See `/docs/decisions/adr-015b-structured-rpg-roll-lifecycle.md`.

#### GM Cheating

GM cheating is prompt/configuration behavior in v1, not a code-side roll-alteration system, with one exception:

- `gm_cheating = off` is enforced by code as a strict roll-result preservation invariant.

When `gm_cheating = off`, all trust-relevant roll results are honored absolutely, including climactic moments. No narrative convenience gets to mug arithmetic in an alley.

#### Rules Architecture

RPG mode uses four separate parts:

| Component | Role |
|---|---|
| Rules Package | Ingested mechanical canon and source authority. |
| Rules System Adapter | Hand-authored executable helpers and deterministic rails for a supported rules system. |
| Character Sheet Model | Persistent ruleset-specific state. |
| RPG Adjudication Loop | Orchestration layer using all three plus dice services and the narrative pipeline. |

For v1, the supported adapter is a bounded d20 adapter.

### Branching Mode

Branching mode is a story architect contract. It preserves literary prose while making interaction affordances structured.

Generated narrative prose remains natural language. Branch options and interaction state are not left embedded loosely in Writer prose. They must be structured, validated, persisted, and available to the UI.

Structured Branching output includes:

- branch options
- freeform availability
- branch-count range
- branch presentation state
- branch-selection metadata

#### Interaction Styles

At setup, the Sojourner chooses one interaction style and one Branching cadence/verbosity setting. These are separate axes.

Interaction style controls the input mechanism.

| Style | Behavior | Allowed branch-count ranges |
|---|---|---|
| Freeform only | The Sojourner inputs their own text. No branch cards are generated or displayed during ordinary play. | None. |
| Hybrid freeform + branch cards | The Sojourner may type freeform input or choose from generated branch options. | 1–2, 2–3, or 3–4 branch options. |
| True CYOA / choices-only | The Sojourner chooses only from generated branch options during ordinary play. Freeform narrative input is not available during ordinary play. | 2–3, 2–4, or 2–5 branch options. |

Hybrid is the only mode where branch cards and freeform input are presented together with equal prominence. Freeform-only and True CYOA are distinct interaction contracts.

Branching cadence/verbosity controls the storyteller’s output density and decision-point pacing. It is preserved for all Branching interaction styles, including Freeform-only, because even a Sojourner who writes their own action every turn still needs a dial for how expansive the story architect’s response should be. The Sojourner controls their own input verbosity turn-by-turn by how much they write before submitting; the cadence setting controls the system’s response style.

| Cadence | Behavior |
|---|---|
| Interactive | Shorter storyteller beats, faster return to the Sojourner, and more frequent explicit decision points where branch cards are enabled. |
| Balanced | Moderate storyteller beats, ordinary scene development, and branch-card presentation at natural beat boundaries where branch cards are enabled. |
| Immersive | Longer, more literary storyteller beats, slower scene development, and less frequent explicit decision points where branch cards are enabled. |

In True CYOA, ordinary play remains choices-only. The cadence setting controls how much narration the story architect produces before presenting the next required choice; it does not make ordinary freeform action available. In Freeform-only, cadence controls storyteller verbosity and pacing only; it does not create branch cards.

The interaction style and cadence may later change through an OOC request. That change updates persisted Branching-mode configuration. It is not a vague prompt instruction.

If ordinary freeform narrative text reaches the backend while the story is configured as True CYOA, and it is not explicitly classified as OOC, the system treats it as an invalid interaction for that style and asks the Sojourner to choose an available branch or use OOC to change configuration. It must not silently convert the text into story action, ignore it, or treat it as OOC without classification support.

#### Setup and Story-Architecture Controls

Branching setup preserves the older story-architect intent while translating it into the typed interaction contract.

- **Tone** is not a rigid separate dropdown. It lives in the world/story summary alongside genre, setting, and narrative register.
- **Setup** uses the hybrid model: structured fields followed by a lightweight story-architect confirmation pass.
- **Length preference** is a configuration parameter: Short Story / Novella / Novel. It shapes pacing-stage progression through setup, escalation, reversal, climax, and aftermath.
- **Story seeds and supporting cast** are optional setup fields. Sojourners may provide dramatic hooks, premises, allies, rivals, and antagonists.
- **Branching cadence/verbosity** is a persisted configuration parameter with Interactive / Balanced / Immersive values. It applies to all Branching interaction styles; for branch-card styles it shapes both storyteller verbosity and branch presentation cadence, while for Freeform-only it shapes storyteller verbosity and pacing only.
- **Freeform handling** in Freeform-only and Hybrid should map Sojourner input against dramatic validity without forcing it onto a preset rail. If the Sojourner meaningfully exceeds the current branch set, the story should adapt rather than pretending the branch card was always the only legal road.

#### Future Branching Extensions

Optional canon/lore packs, visual story map, non-destructive What If? branches, richer branch-timing controls, and more elaborate branch-tree visualization remain deferred beyond v1 unless separately scoped. The v1 typed output contract should not make those features artificially hard later.

### Writing Mode

Writing mode is a collaborative writing contract. The user is the author of record.

Persona selection determines relationship orientation. The UI presents a gallery divided into **Mentors** and **Peers**.

#### Mentors

Mentors are developmental teachers. Their primary orientation is teaching through making: craft goals, generative exercises, targeted feedback, and structured practice.

- **Chiron** — patient, methodical, systematic.
- **Merlin** — wise, metaphorical, pattern-oriented.
- **Vidura** — direct, ethically grounded, no-nonsense.

Bringing existing prose to a Mentor is a diagnostic path: “what should we work on?” It is not a manuscript-repair service.

#### Peers

Peers are creative collaborators. Their primary orientation is making alongside the Sojourner: generating prose, proposing directions, maintaining continuity, challenging weak logic, and pushing the work forward.

- **Odin** — relentless, unsparing, drawn to the harder path.
- **Athena** — strategic, structural, precise.
- **Thoth** — meticulous, language-obsessed, sentence-level attentive.

Peers prefer generative work but can work on existing manuscript material when the project calls for it.

#### Setup and Authoring Controls

Writing setup preserves the older hybrid setup intent while keeping Issue 17’s scope boundary intact.

- The roster is intentionally small in v1: three Mentors and three Peers. It gives meaningful choice without creating excessive prompt, UI, and test burden.
- Setup uses structured fields followed by the selected persona opening with a brief confirmation and one or two clarifying questions specific to that orientation.
- Work does not begin until the relationship orientation and immediate writing goal are clear.
- Beat control allows the Sojourner to set milestone constraints such as “By the end of this chapter, X must happen.”
- Exposed controls may include tense, POV, length, style density, dialogue/narration ratio, genre conventions, and similar writing-surface controls.
- Writing mode has the strongest style-conditioning needs of the three modes.

#### Issue 17 Scope

Issue 17 owns:

- Writing-mode setup
- persona selection and behavior
- Mentor/Peer relationship orientation
- prompt-contract injection
- beat constraints
- mode-specific orchestration behavior
- minimal future-compatible version-history pointers

Issue 17 does not own full version history, draft branching, restore/rollback workflows, compare views, or broader manuscript evolution tooling in v1 unless a later dedicated issue explicitly scopes them. Deferred manuscript-evolution tooling remains a future design target, not a feature to accidentally block.

Minimal future-compatible version-history pointers may include lightweight identifiers, provenance references, or links to prior draft artifacts/turns sufficient for later tooling to understand where generated or revised material came from. They must not imply full snapshot trees, restore workflows, compare views, branch management, or a manuscript-versioning UI in v1.

Persona expansion across RPG and Branching is a future consideration. v1 should not couple persona behavior so tightly to Writing mode that future cross-mode personas become unnecessarily difficult.

---

## 6. Tech Stack

| Component | Decision |
|---|---|
| Backend | Python 3.12 + FastAPI. |
| Persistence | SQLite first. |
| Retrieval memory | ChromaDB included in v1. |
| Frontend | React + Vite + TypeScript. |
| Deployment | Local web server accessed through a browser. |
| Model access | Hosted provider routing and BYOK provider credentials. |
| Package management | pip + virtualenv. |
| Testing / quality | pytest, mypy strict, Ruff, Black, pip-audit, detect-secrets. |

Issue 19 implements the frontend shell and the minimal FastAPI API surface required by that shell. It must not introduce Next.js, SSR, a separate Node application server, or Electron. Electron or another desktop wrapper remains optional later, but not in Issue 19.

Route handlers stay thin. They expose existing service contracts rather than smuggling orchestration, entitlement, provider, or business policy into HTTP code.

### Future Model and Deployment Surfaces

The v1 build target is local-first browser deployment with hosted provider routing and BYOK provider credentials. That does not eliminate the older extensibility intent around local/open-weight models, VPS-hosted open-weight models, or broader hybrid BYOK surfaces.

Future issues may add those surfaces if quality, cost, privacy, hardware, and policy constraints justify them. The v1 adapter interfaces should therefore avoid assumptions that only direct hosted APIs can ever satisfy a provider-backed pass.

---

## 7. Provider Architecture and Prompt Caching

### v1 Provider Surfaces

Issue 14 implements two provider/platform surfaces in v1:

1. **Anthropic direct** — canonical quality-first direct-provider path and immediate continuation of the pipeline already built in Issues 9–12c.
2. **OpenRouter** — v1 aggregator/routing surface used to exercise provider selection, fallback policy, capability profiling, and surface-specific cache normalization.

OpenAI direct and Google/Gemini direct are explicitly deferred beyond v1. Issue 14’s adapter interfaces must not architect against adding them later.

Local/open-weight and VPS-hosted open-weight model surfaces are also deferred beyond v1 as supported provider paths. They remain part of the long-term extensibility posture, especially for privacy, cost-control, and content-policy flexibility, but they are not Issue 14 launch requirements.

### Provider Adapter Responsibilities

Issue 14 owns:

- provider routing
- provider/platform capability profiles
- pass-to-provider/model selection
- cache-capability adapters
- cache-key and breakpoint/context-object strategy
- TTL/retention behavior where applicable
- cache metric interpretation
- provider refusal taxonomy and typed refusal events
- constrained provider-refusal fallback
- BYOK credential storage and validation
- provider-specific usage normalization and calibration inputs for Issue 13 credit accounting

Context Builder does not own provider-specific cache realization. Orchestration does not own provider-specific cache realization. They preserve the stable/volatile boundary and deterministic rendering preconditions; adapters convert that intent into concrete API behavior.

Caching design rules:

- Afterworlds owns provider-neutral cache intent: stable context is assembled once per turn and volatile/pass-forward material stays outside the stable-cache region.
- Provider adapters own concrete cache realization: cache-key semantics, breakpoint or context-object strategy, TTL/retention behavior, cache metrics, and verified hit behavior.
- Correctness must never depend on cache hits. A missed cache may be expensive; it must not change narrative, canon, entitlement, or safety behavior.
- Cache-hit behavior must be adapter-verified. No provider-independent assumption about cache reuse, TTL, billing semantics, or metric names is binding until an adapter proves it.
- Context Builder and orchestration may preserve stable identity and rendering determinism, but they must not smuggle provider-specific cache semantics into the architecture core.

### Provider Refusal Fallback

When Afterworlds policy allows the content but the selected narrative/state provider refuses, the router may attempt one fallback to an explicitly configured eligible provider/platform surface within the same access path and fallback pool.

In v1, eligible surfaces are Anthropic direct and OpenRouter as permitted by the active access path. For BYOK users, the eligible fallback pool is bounded by the provider credentials and surfaces the Sojourner has configured. If a BYOK user has configured only one provider/surface, no fallback exists unless the Sojourner explicitly configures another eligible BYOK surface.

Fallback must never:

- run after an Afterworlds Safety `BLOCK`
- silently cross hosted/BYOK boundaries
- depend on granular refusal reasons being available

Every provider refusal is recorded as a typed refusal event with pass, provider, model/surface, coarse metadata when available, fallback attempted/not attempted, fallback target, and final outcome.

If no eligible fallback exists or fallback also refuses/fails, the system stops and surfaces a typed provider refusal for UI handling.

### BYOK Credential Storage

Issue 14 implements local-first BYOK credential management.

User-supplied provider API keys are stored via the local platform credential store / OS keychain where available. Environment/config credentials remain only for development, CI, and opt-in integration testing.

SQLite stores only non-secret credential metadata and credential references.

Raw API keys must never be persisted in:

- SQLite
- logs
- telemetry
- exports
- backups
- support/admin views
- Story/Turn data

Cloud Services may sync non-secret provider preferences/metadata in v1. Cloud-hosted storage or sync of BYOK API keys is deferred unless a later issue defines a dedicated security model, threat model, audit trail, and deletion/export semantics.

### Canonical Prompt/Context Shape

Stable prefix:

```text
System prompt + mode/pass contract
Story Bible active context
Rolling Summary
Rules Package / canon-pack slice when present
Retrieval Memory when present
```

Volatile suffix:

```text
Recent turns
Current Sojourner input
IntentClassificationResult
Pass-forward additions outside stable prefix
```

Provider adapters and pass renderers may differ in API payload shape, but they must preserve the architectural boundary. PassForwardLedger and VolatileSuffix are outside the stable-cache region.

---

## 8. Business Model

### Commercial Structure

Afterworlds uses one canonical Sojourn orchestration path across real product access paths. Commercial differentiation is handled through entitlements, usage allowances, provider billing path, and hosted services — not by removing continuity machinery.

| Access path | Revenue shape | Cost driver |
|---|---|---|
| Hosted Subscription | Monthly subscription with included hosted credits | Model usage, storage, hosted services, support, payment overhead. |
| Hosted Top-Ups | One-off credit purchases | Incremental model usage and payment overhead. |
| Starter Access (optional) | Small paid entry package / trial subscription using normal hosted credits | Model usage, storage, hosted services, support, payment overhead. |
| BYOK Perpetual License | One-time purchase | Product access, onboarding, first-year Cloud Services bundle. |
| BYOK Cloud Services Renewal | Optional annual renewal after year one | Hosted storage, sync, backup, remote access, ingestion processing, service maintenance. |
| Institutional (future) | Per-seat / pooled credits / capped usage | Aggregate hosted usage and admin/service overhead. |
| Marketplace (future) | Transaction fee / seller services / discovery | Payment rails, moderation, hosting, payout operations. |

### Hosted Credits

Hosted credits are provider-neutral, usage-backed entitlement units. They are computed from structured turn/pass usage metrics through a configurable conversion policy.

A flat/coarse per-turn decrement is not a legitimate product direction because it divorces credits from hosted usage and undermines burn-rate transparency.

Provider-specific dollar-equivalent accounting inside the entitlement core is rejected as brittle. Provider pricing, cache semantics, billing units, aggregator fees, and fee structures change. Issue 13 owns the durable accounting architecture and enforcement path. Issue 14 supplies provider/platform-specific normalization and calibration inputs without reopening the credit model.

### Entitlement Ownership

Issue 13 owns authoritative runtime entitlement state and enforcement:

- hosted credit availability
- top-up balances/state as relevant to runtime enforcement
- BYOK license state
- Cloud Services active/lapsed state, including hosted storage, sync, backup, remote access, hosted ingestion, and hosted runtime dependent on Afterworlds server resources
- access-path and entitlement routing/enforcement decisions based on those states
- configurable credit conversion policy

Issue 22 owns the operational/support/compliance layer:

- append-safe entitlement/support event history
- support-facing reconstructability
- manual remediation actions with reason capture
- export/deletion request state
- admin investigation hooks and anomaly visibility

Runtime enforcement and human-operable reconstructability are related but not the same owner. Keep the boundary clean. Issue 13 routing means access-path and entitlement enforcement; Issue 14 routing means provider/platform selection, fallback, capability profiles, and adapter behavior.

### BYOK and Cloud Services

BYOK perpetual rights guarantee continued full-fidelity Afterworlds use through a local/self-hosted product path:

- local orchestration
- local SQLite persistence
- local ChromaDB retrieval memory
- user-supplied provider credentials

“Self-hosted” retrieval memory means locally operable by the Sojourner’s Afterworlds installation, not necessarily hosted by AfterworldsAI.

Cloud Services fund ongoing hosted convenience and service costs:

- cloud storage
- sync
- backups
- remote access
- hosted ingestion
- any hosted runtime dependent on Afterworlds server resources

If Cloud Services lapse, hosted active-use services suspend. Existing hosted user content remains available for read/export/download and later reactivation, but ongoing turn generation continues through the local BYOK path rather than through uncompensated server-hosted storage/retrieval.

### Billing Platform Ownership

Hosted top-ups, Starter Access, and paid hosted access are product concepts in v1 architecture. The full payment platform is Issue 23, a dedicated launch-blocker issue after Issue 21 and before public launch.

That billing-platform/payment-integration issue owns:

- payment-provider integration
- subscription/top-up checkout flows
- webhook ingestion
- payment-event idempotency
- failed-payment, refund, and chargeback representation
- reconciliation hooks
- translation of successful commercial events into Issue 13 entitlement mutations
- operational/support events consumable by Issue 22
- user-facing state that Issue 20 can display

It does not own runtime entitlement enforcement, settings UI, or support remediation workflows.

### Ethical Principles

- Do not degrade continuity by tier.
- Do not hide usage economics behind misleading “unlimited” language.
- Do not trap users with dark-pattern upgrade or renewal flows.
- Do not conflate perpetual software rights with recurring hosted-service costs.
- Do not gate core dignity behind premium currency mechanics.

Afterworlds’ commercial model should feel like a clear exchange, not a carnival game: the Sojourner either pays for hosted usage directly, or brings their own model costs and pays only for the continuing platform services they actually consume.

---

## 9. MVP Sequence

Pre-v1 internal milestones are construction milestones, not product versions.

### Foundation and Pipeline

1. Repo skeleton, tooling, and CI scaffold.
2. Core models.
2a. Character sheet architecture correction.
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

### Entitlements, Providers, Modes, UI, and Spine

13. Runtime entitlement state and enforcement.
14. Provider routing, capability profiles, cache adapters, refusal fallback, and BYOK credential management.
15. RPG mode integration with bounded d20 Rules System Adapter.
16. Branching mode integration with typed output contract, typed interaction configuration, and Branching cadence/verbosity setup.
17. Writing mode integration with persona behavior, Mentor/Peer orientation, prompt injection, beat constraints, and minimal version-history pointers.
18. ChromaDB retrieval-memory design and implementation, gated by ADR / owner checkpoint.
19. React + Vite + TypeScript frontend shell and minimal FastAPI API surface.
20. User-facing billing/BYOK visibility and configuration.
21. Final release-capable narrative spine demo.

Issue 21 is the narrative spine gate, not the commercial launch gate. It verifies all three modes end-to-end, hosted and BYOK access paths, and coherent cooperation among major v1 systems. It is verification-first and may include only narrow integration fixes where contracts are already clear.

### Launch Blockers After the Spine Demo

- Issue 23 — Billing Platform / Payment Integration after Issue 21 and before public launch.
- Issue 22 operations/support/compliance minimums.
- Any remaining security/compliance gates required by repository governance.

### v1 — First Release-Capable Text Product

v1 includes:

- full Sojourn orchestration path: Planner → Writer → Extractor → Contradiction with safety envelope
- RPG, Branching, and Writing modes
- full Story / Arc / Chapter / Node / Turn hierarchy
- Rolling Summary + Story Bible
- Extractor update classification policy
- Contradiction Checker
- SQLite persistence
- ChromaDB retrieval memory
- one ingested, published, queryable d20 Rules Package
- bounded d20 Rules System Adapter
- BYOK API support through local credential storage
- hosted subscription credit/top-up entitlement framework, including optional Starter Access as a paid entry package using the same full pipeline
- user-facing billing/BYOK visibility/configuration
- React + Vite + TypeScript frontend shell
- minimal FastAPI API surface
- operations/support/compliance minimums
- payment integration if hosted paid access or top-ups are offered publicly
- all CI and governance gates passing

### Deferred Beyond v1

- image generation from Node metadata
- visual story map
- non-destructive What If? branching
- voice input/output
- player-supplied Setting Canon Packs for licensed settings
- marketplace or collaborative multi-Sojourner stories
- mobile clients
- advanced admin console / BI / CRM-style support platform
- full Writing-mode version history, draft branching, restore/rollback, compare tooling, and broader manuscript evolution tooling unless separately scoped
- richer Writing-mode authoring UX beyond the v1 controls needed for setup, beat constraints, and prompt injection
- richer Branching UX including branch-tree visualization, visual story map, non-destructive What If? paths, and branch-timing controls beyond the v1 Branching cadence/verbosity setting
- persona expansion across RPG and Branching modes
- direct OpenAI and Google/Gemini provider surfaces unless a later issue adds them
- supported local/open-weight or VPS-hosted open-weight provider surfaces unless a later issue adds them

---

## Summary Architecture

```text
[Sojourner Input]
        ↓
[Intent Classifier]
        ↓
[Context Builder]
        ├─ Stable Prefix: System/Contract + Story Bible + Summary + Rules Slice + Retrieval Memory
        └─ Volatile Suffix: Recent Turns + Current Input + Intent
        ↓
[Safety Preflight?]
        ↓
[Planner]
        ↓
[Writer]
        ↓
[Safety Output Audit?]
        ↓
[Extractor] ─────┐
        ↓         │
[Contradiction] ←─┘
        ↓
[Delivery Gate]
        ↓
[Persistence]
        ├─ Turn / Node
        ├─ Story Bible updates through Extractor policy
        ├─ Rolling Summary as triggered
        └─ Retrieval Memory write only for delivery-cleared material
```

Provider adapters are orthogonal service infrastructure used by provider-backed passes for routing, payload realization, cache-capability handling, refusal fallback, BYOK credential access, and provider-specific metrics. They are not an additional sequential turn-pipeline stage.

Operations/support minimums are parallel administrative capabilities, not a turn-pipeline stage.
