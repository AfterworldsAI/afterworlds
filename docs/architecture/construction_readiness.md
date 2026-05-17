# Afterworlds Construction Readiness Document (v8)

*Items 1–17 of the Construction Handoff Checklist — completed March 2026*
*Revised April 2026 to incorporate structural cleanup after review and keep Issue 22 explicit, scoped, and maintainable.*
*Revised May 2026 to replace the five-pass pipeline framing with the safety envelope model. Safety is no longer a mandatory fifth narrative pass. The core narrative pipeline is Planner → Writer → Extractor → Contradiction. A safety envelope provides input preflight (before Planner/Writer, when required) and conditional output audit (after Writer, before Extractor/Contradiction, when required). Provider refusals are typed pass failures, not Safety verdicts. No retroactive amendment to Issues 9–12a is required; those specs were written under the prior framing and remain valid construction context.*
*Revised May 2026 to make the caching architecture explicit: Afterworlds owns provider-neutral cache intent, deterministic stable/volatile context separation, and stable-context reuse discipline. Provider/platform-specific cache realization — cache-key semantics, breakpoint or context-object strategy, TTL/retention controls, cache metrics, and verified cache-hit behavior — belongs to Issue 14 provider adapters. Stable internal context identity is required for efficient caching, but it is not itself a provider-agnostic guarantee of cache hits.*
*Revised May 2026 to formalize Issues 12a–12c after Issue 11 completion and to record the construction pause: once Issue 12c is complete, Issues 13–21 must be formally drafted before further implementation proceeds.*

-----

## Item 1 — Product Scope is Pinned Down

### What Afterworlds Is

Afterworlds is a platform for exploring stories in an interactive, participatory way. It lets you enter the world of a story — whether you’ve created it or encountered it elsewhere — and live within it as the protagonist, making choices that shape the narrative according to your instincts rather than the original author’s path.

The core impulse: when you finish a story you love — a novel, film, game — there’s often a longing to continue it, to enter its world, or to live through it as your character would have rather than as the original author wrote it. Afterworlds bridges that gap.

### Who It’s For

Lovers of story in all its forms, primarily:

- **Readers** who want to continue a story or inhabit it differently after finishing
- **Players** who want to experience narrative as an interactive game where they solve mysteries and face consequences
- **Budding writers** learning the craft through collaborative storytelling with an AI partner

### What Problem It Solves That Nothing Else Solves As Well

The longing at the end of a beloved story — the sense that the narrative should continue, or that you’d tell it differently if you could. Afterworlds closes that gap.

### What Is Explicitly In v1

v1 is the first release-capable MVP, not merely an internal build milestone.

- Text engine with full Sojourn orchestration path (core narrative pipeline + safety envelope)
- RPG, Branching, and Writing modes
- Full story hierarchy (Story / Arc / Chapter / Node / Turn)
- Rolling summary + Story Bible
- Rules Package support with one curated, ingested, and queryable d20 Rules Package
- Vector retrieval memory (ChromaDB)
- Extractor update classification policy
- Contradiction checker
- SQLite persistence
- BYOK API support
- Hosted subscription credits / top-ups entitlement framework
- BYOK perpetual license + first-year Cloud Services inclusion, with renewal-capable entitlement model
- **v1 operations/support minimums as defined in Issue 22**

### What Is Explicitly Not In v1

Pre-v1 internal milestones handle construction sequencing and dependency order, but they are not product versions.

The following are deferred beyond v1:

- Image generation from Node metadata
- Visual story map — deferred to v2
- Non-destructive What If? branching (parallel timelines) — deferred to v2
- Voice input / output — deferred to v2
- Player-supplied Setting Canon Packs for licensed RPG settings — deferred to v2/v3
- Marketplace or collaborative multi-user stories — deferred to v3
- Mobile clients — deferred to v3
- **A polished full admin console** with advanced analytics, CRM-style workflow, or enterprise-grade operations tooling. v1 requires the operational minimums above, not a large dashboard product.

### Versioning Clarification

Version numbers refer to release-capable product scope.

Pre-v1 internal milestones describe build order only:

- foundation and persistence
- Story Bible and summary services
- Rules Package schema and ingestion
- context assembly
- minimal Writer path
- Extractor and contradiction systems
- full pipeline orchestration
- entitlement routing, hosted credits/top-ups, and BYOK support
- operations/support minimums

v1 is the first release-capable MVP.

-----

## Item 2 — Core Architecture Principles Are Frozen

These principles must not be casually reinvented during coding. Any code that violates them should be caught in review. Codex has this document as a written reference to cite in review comments.

1. **Story Bible is structurally separate from prose history**
1. **Six memory layers have distinct roles** (Immediate / Rolling Summary / Story Bible / Rules Package / Retrieval Memory / Contradiction Checker)
1. **Intent is classified before context is assembled**
1. **The pipeline is staged:** core narrative pipeline — Planner → Writer → Extractor → Contradiction — protected by a safety envelope: input preflight before Planner/Writer when required; conditional output audit after Writer and before Extractor/Contradiction when required. Provider refusals are typed pass failures, not Safety verdicts.
1. **Extractor proposes canon updates; it does not write canon directly**
1. **Stable context is assembled once per turn and shared across all passes.** Stable/volatile separation is a core Afterworlds architecture rule. Provider/platform-specific cache realization — cache-key semantics, explicit breakpoint or context-object strategy, TTL/retention controls, cache metrics, and verified cache-hit behavior — belongs to provider adapters, not to Context Builder or orchestration.
1. **Operational state transitions that affect money, access, or user data must be reconstructable by humans** through explicit event logging rather than inferred from opaque current-state fields

-----

## Item 3 — v1 Success Criteria Are Defined

A minimal v1 success statement:

- A user can create a story
- Select RPG, Branching, or Writing mode
- Submit turns and receive coherent output
- Persist story state and turn history
- Maintain a Story Bible and rolling summary
- Query vector retrieval memory during play
- In RPG mode, adjudicate against one active, ingested, queryable d20 Rules Package
- Run contradiction checking
- Use BYOK model access
- Operate the commercial product responsibly via the operations/support minimums defined in Issue 22

**Terminology guardrail:** Story Bible = narrative canon; Rules Package = external mechanical canon for RPG mode; canon pack = optional external lore/canon corpus for Branching/Writing modes. Session state remains separate from all three.

-----

## Item 4 — Technical Stack Is Decided Enough to Begin

|Component       |Decision                                           |
|----------------|---------------------------------------------------|
|**Backend**     |Python + FastAPI                                   |
|**Storage**     |SQLite first; ChromaDB included in v1 release scope|
|**Frontend**    |React or Svelte (resolve before Issue 19)          |
|**Deployment**  |Local web server accessed via browser              |
|**Model access**|BYOK / hybrid as recommended default               |

**Known unknown:** React vs. Svelte is acceptable to resolve during early construction (before Issue 19). It does not block architecture decisions.

-----

## Item 5 — Core Entities Are Defined

|Entity                         |Description                                                                                                                                                                                                                                                                                                                                             |
|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|**Story**                      |Top-level container for a complete narrative                                                                                                                                                                                                                                                                                                            |
|**Arc**                        |Major narrative division within a Story                                                                                                                                                                                                                                                                                                                 |
|**Chapter**                    |Subdivision within an Arc                                                                                                                                                                                                                                                                                                                               |
|**Node**                       |A story beat / state transition. Unified entity across all three modes; includes mode-specific metadata (branching logic for Branching mode, mechanical modifiers for RPG mode, beat constraints and version pointers for Writing mode). Node means “story beat” in all modes, but what constitutes a complete beat and how it’s tracked varies by mode.|
|**Turn**                       |One interaction unit: one user input + one AI response                                                                                                                                                                                                                                                                                                  |
|**Story Bible**                |Structured narrative canon — world rules, cast, locked facts, timeline, forbidden facts                                                                                                                                                                                                                                                                 |
|**Rolling Summary**            |Compressed narrative history, auto-updated every N turns                                                                                                                                                                                                                                                                                                |
|**Rules Package**              |External mechanical canon package for RPG mode; future canon-pack pattern for large franchise/reference corpora in Branching/Writing                                                                                                                                                                                                                    |
|**World / Character State**    |Current world conditions, character stats, inventory, relationship meters                                                                                                                                                                                                                                                                               |
|**Mode-Specific Session State**|RPG: HP, dice modifiers, active quests; Branching: pacing stage, branch tree, plot thread tracker; Writing: beat constraints, version history pointers                                                                                                                                                                                                  |
|**Entitlement Event Log**      |Append-safe record of access-, billing-, credit-, and service-state changes relevant to support, audit, and user trust                                                                                                                                                                                                                                  |
|**Support Operations State**   |Controlled support/remediation records such as manual credit grants, trial/service extensions, deletion/export request status, and operator reason notes                                                                                                                                                                                                |

**Key principle:** Node is a unified entity across all three modes. Mode-specific metadata flags make the distinction clear without duplicating the schema.

-----

## Item 6 — Mode Prompt Contracts Are Written

The mode prompt contracts are canonical versioned artifacts. Full content — system prompts, pre-play sequences, and player configuration tables — lives in the prompt files. This section records the key decisions and design rationale behind each contract. Do not duplicate prompt text here; update the prompt files directly when contracts change.

**Canonical prompt files:**

- `/docs/prompts/rpg_mode.md`
- `/docs/prompts/branching_mode.md`
- `/docs/prompts/writing_mode.md`

-----

### RPG Mode — Key Decisions

**Pre-play sequence is mandatory.** Two phases before Turn 1: world setup first, then character creation within that world context. Play does not begin until the character sheet is complete enough to adjudicate against.

**Character creation is GM-guided and conversational.** The player either works through creation with the GM or pastes a completed sheet. Incomplete or ambiguous sheets trigger clarification before play begins — not during.

**Character sheet is a first-class persistent object.** Not a conversation artifact. Persists across sessions, mutable during play, tracks current and maximum values where applicable. Schema requirements flagged for Issue 2.

**v1 supports original and custom settings only.** Playing in existing licensed settings (Forgotten Realms, Greyhawk, etc.) requires player-supplied Setting Canon Packs — deferred to v2/v3.

**Dice handling has two modes.** Player rolls = GM announces check and modifiers, waits for player to report result, never narrates outcome before the roll. AI rolls = GM rolls and always shows the result. Hidden rolls (checks the player has no in-world awareness of) are a narrative mechanic that applies in both modes — not a player-facing setting.

**GM cheating is a player-controlled toggle.** Default on, calibrated to tone. When disabled, all dice results are honored absolutely in both directions at all moments, including climactic ones. UI shows a plain-language warning when the player turns it off.

**Session type is a configuration parameter.** Shapes pacing expectations for the GM. Short adventure / Campaign / Open-ended. UI surfaces a gentle note that longer campaign play is best served by hosted subscription credits or BYOK, since extended play consumes more usage and makes ongoing storage/state services more valuable.

**Tone is a front-end dropdown, not free text.** Gritty / Balanced / Forgiving / Danger-free. Passed directly to the AI.

-----

### Branching Mode — Key Decisions

**Tone is not a configuration parameter.** It lives in world summary alongside genre, setting, and narrative register. Free text lets players describe the story they actually want without imposing a vocabulary on them.

**Freeform input is a first-class option, equal to branch selection.** Branch cards and freeform text field are presented with equal prominence. Branch options exist to inspire and indicate what’s possible — not to confine. Players who type freeform every turn are using the mode correctly.

**Branch frequency uses experiential language.** Three options: Interactive / Balanced / Immersive. No granular mechanical options (word counts, beat counts). UI note on the Interactive option explains that the narrator may hold branches briefly during climactic moments — this is intentional behavior, not a bug.

**Setup uses the hybrid model.** Structured form followed by a single lightweight confirmation pass from the story architect. Catches setup problems before they infect the story; establishes the architect’s presence from the first moment.

**Length preference is a configuration parameter.** Short story / Novella / Novel. Shapes how quickly the story architect advances through pacing stages.

**Story seeds and supporting cast are configuration fields.** Players can contribute dramatic hooks, premises, allies, and antagonists at setup time. Both optional.

-----

### Writing Mode — Key Decisions

**Persona selection determines relationship type.** No explicit Mentor / Writing Partner submode labels. The player selects a persona from a gallery divided into Mentors and Peers. The category is communicated through persona descriptions, not submode taxonomy.

**Mentors: Chiron, Merlin, Vidura.** Developmental guides. Primary orientation is teaching through making — craft goals, generative exercises, targeted feedback. Manuscript repair is not their function. Bringing existing prose to a Mentor is a diagnostic path only (“what should we work on?”), not a repair path.

**Peers: Odin, Athena, Thoth.** Creative collaborators. Primary orientation is making alongside the user. Teaching available but not default — a Peer speaks up only when something is genuinely holding the work back, or when asked. Preference for generative work over manuscript repair, but will work on an existing manuscript when the project calls for it.

**Roster is intentionally small.** Three Mentors, three Peers. Enough meaningful choice without overwhelming players or creating excessive implementation burden. Roster can expand once the persona system is well-designed and functional.

**Future consideration — persona expansion across modes.** The persona layer is a strong candidate for RPG and Branching modes in a future version. Should not be architected against in v1.

**Setup uses the hybrid model.** Structured form followed by the persona opening with a brief confirmation and 1–2 clarifying questions specific to their orientation. Work does not begin until the working relationship and immediate goal are clear.

-----

### OOC Communication — All Modes

Full protocol in each mode’s prompt file. The UI provides an explicit OOC button that prepends the [OOC] marker automatically. Players may also type it manually.

-----

## Item 7 — Contradiction Checker Architecture Is Decided

**v1 approach:** Lightweight model-assisted — a small, fast LLM call with a focused prompt. One code path across all access paths. Core contradiction checking runs every turn; commercial entitlements may later influence retrieval depth or cost guardrails, but not whether the checker exists.

**What it checks:**

|Scope layer                    |Coverage                                                                                                                                                                |
|-------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|**Baseline v1 behavior**       |Recent context + active Story Bible context (including locked facts and current world/canon state)                                                                      |
|**Expanded retrieval behavior**|Retrieved relevant historical scenes/events once ChromaDB integration is wired; later plan or cost controls may expand depth further without removing the checker itself|

The checker is designed to catch continuity violations including but not limited to: dead characters acting, items never acquired, location/name drift, POV/tense shift, and violated locked facts. The listed categories are common failure modes, not an exhaustive definition.

**Pipeline position:** The checker runs immediately on the Writer’s candidate output — evaluating the generated prose against the Story Bible and assembled context before anything is delivered to the user. It does not run on input context alone; it must see what the Writer produced in order to catch contradictions introduced by generation (for example, a dead character acting in newly generated prose).

Output is gated on the checker clearing. Nothing is delivered to the user until it does. Because the checker uses a small, fast model, the latency added to the turn approaches zero in practice.

Nothing is delivered to the user until the checker clears. Contradictions are caught before they’re read, not flagged after the fact.

**Rationale for synchronous gate:** In a narrative product, continuity *is* the deliverable. A contradiction the user reads and then gets corrected on the next turn has already done its damage. Async flagging is acceptable in productivity tools; it is not acceptable here.

-----

## Item 8 — Cost Model and Pricing Architecture Are Estimated

The business model is no longer based on a degraded free tier versus a full paid tier. Afterworlds now assumes **one canonical Sojourn orchestration path** for all paying access paths. Commercial differentiation is handled through billing structure, credit allowance, and hosted-service entitlements — not through removal of core continuity functions or safety guardrails.

### Core Pricing Architecture

|Access Path                    |Revenue Shape                                      |Cost Driver                                                                        |
|-------------------------------|---------------------------------------------------|-----------------------------------------------------------------------------------|
|**Hosted Subscription**        |Monthly subscription with included credits         |Model usage + storage + hosted services                                            |
|**Hosted Top-Ups**             |One-off credit purchases                           |Incremental model usage                                                            |
|**BYOK Perpetual License**     |One-time purchase                                  |Initial platform access, onboarding, first-year cloud services bundle              |
|**BYOK Cloud Services Renewal**|Optional annual renewal after year one             |Ongoing storage, sync, ingestion processing, remote access, and service maintenance|
|**Institutional (future)**     |Per-seat / pooled credit / capped-usage contracts  |Aggregate hosted usage + admin/service overhead                                    |
|**Marketplace (future)**       |Transaction fee / seller tools / discovery services|Payment rails, moderation, hosting, payout ops                                     |

The key principle: **continuity quality is invariant across access paths.** A hosted subscriber and a BYOK user receive the same narrative engine. The difference is who pays model cost and which hosted platform services are active.

### Operational Reality Addendum

Earlier versions of the CRD correctly modeled credits, top-ups, BYOK, and Cloud Services as product/business concepts, but left implicit how a human operator would actually inspect and repair those states. That gap is now resolved explicitly.

v1 requires the **operations/support minimums defined in Issue 22**. This does **not** imply a large full-featured admin product in v1. It does require an explicit support/compliance layer with a defined implementation home, auditability, and deletion/export handling.

### Per-Turn Cost Basis

The underlying per-turn cost model assumes the full Sojourn orchestration path:

[Input Safety Preflight, conditional] → Planner → Writer → [Output Safety Audit, conditional] → Extractor → Contradiction

Safety costs are **conditional**, not guaranteed per turn:

- Input preflight runs before Planner/Writer when the selected provider is not on the safety whitelist or when explicit risk policy triggers it.
- Output audit runs after Writer when provider or risk policy requires it.
- Provider refusals halt the pipeline before downstream passes run.
- On ordinary turns using whitelisted providers with no elevated risk signal, neither Safety call may execute.

Context still splits into a **stable context region** and a **volatile suffix**. That separation remains economically important. Whether a provider discounts the stable region across passes, across turns, both, or neither is adapter-specific and must be verified in Issue 14 rather than assumed universally.

#### Story Bible Size at Steady State

The Story Bible is split into static (written at creation, requires Sojourner confirmation to change), dynamic (Extractor-maintained), and provisional (proposed but not yet ratified) partitions. The Events Ledger uses a tiered inclusion policy — full record stored in SQLite, active context loads only recent and high-significance events. Nothing is ever deleted.

|Scenario|Story Bible tokens (active context)|
|--------|-----------------------------------|
|Minimal |~5,000                             |
|Moderate|~12,000                            |
|Complex |~22,000                            |

The Events Ledger is the primary growth driver. Without the tiered inclusion policy it would dominate the Bible’s footprint within a few chapters. The policy bounds the active context while preserving the full record for retrieval and deep contradiction checking.

#### Stable Context Budget

|Component                     |Tokens             |
|------------------------------|-------------------|
|System prompt + mode contract |~500               |
|Story Bible (tiered inclusion)|5k / 12k / 22k     |
|Rolling summary               |~500 / 800 / 1,200 |
|**Total**                     |~6k / 13.3k / 23.7k|

#### Volatile Suffix

|Component                        |Tokens|
|---------------------------------|------|
|Recent turns verbatim (~10 turns)|~5,000|
|Current input + classified intent|~150  |
|**Total**                        |~5,150|

**Pass-forward additions:** ~2,000–2,500 tokens total across pipeline. Their cache treatment is provider/payload dependent; do not assume universal caching behavior for them.

#### Gross Input Tokens Per Turn — Full Pipeline, Before Caching

|Scenario                                        |Minimal|Moderate|Complex |
|------------------------------------------------|-------|--------|--------|
|**Core pipeline (4 passes, Safety conditional)**|~47,000|~76,000 |~118,000|

These numbers may be materially reduced by provider/platform caching where the active adapter supports and verifies such savings. They are not universally reduced merely because Afterworlds assembles stable context once per turn.

### Cache Economics — Adapter-Calibrated, Not Universal

**Within a single turn:** there is **no universal cross-pass cache-hit-rate assumption**. Shared stable context and deterministic rendering create the opportunity for reuse; the active provider/platform adapter determines whether that opportunity becomes an actual cache hit. Issue 14 must document verified assumptions for supported adapters, including whether cross-pass reuse exists and whether pass-specific system/tool differences affect it.

**Between turns within a session:** cache behavior is likewise adapter-specific. The table below is an **illustrative Anthropic-style TTL sensitivity scenario**, not a cross-provider pricing promise:

|User behavior          |Illustrative short retention (5 min)|Illustrative extended retention (1 hr)|
|-----------------------|------------------------------------|--------------------------------------|
|Focused (1–3 min gaps) |~90%                                |~99%                                  |
|Normal (5–10 min gaps) |~40%                                |~95%                                  |
|Casual (15–30 min gaps)|~5%                                 |~80%                                  |
|Long pause (1+ hr)     |0%                                  |~10%                                  |

**Illustrative blended hit rate, 20-turn session:**

|Retention setting        |Blended hit rate|Effective stable-context cost as % of gross|
|-------------------------|----------------|-------------------------------------------|
|Short retention          |~45%            |~55%                                       |
|Extended retention       |~88%            |~18%                                       |
|Cold start (session open)|0%              |100%                                       |

These figures are useful for understanding why retention controls matter, but Issue 14 must replace generalized assumptions with provider/platform-adapter calibration before these numbers drive production pricing decisions.

**Retention default:** Where a provider/platform adapter supports a validated longer-lived cache mode or equivalent retention control without unacceptable tradeoffs, the adapter should enable that default and document the rationale. The core architecture does not assume that “1 hour TTL” exists everywhere, means the same thing everywhere, or is always economically optimal.

**Session resumption:** Cold start on a new session or a cache miss is an expected baseline. The architecture must tolerate it cleanly. The UX question of whether to surface that warm-up to the Sojourner remains a Known Unknown resolved during Issue 14.

**Architectural requirement:** Afterworlds must preserve stable/volatile separation and deterministic stable-context rendering from day one. Provider-specific adapters then convert that cache intent into concrete payload behavior where supported.

### Representative Model Cost Assumptions

**Price assumptions (representative, verify before launch and whenever provider pricing changes):**

|Model tier   |Use                                                       |Input     |Cache read|Output  |
|-------------|----------------------------------------------------------|----------|----------|--------|
|Large/quality|Writer pass                                               |$3/MTok   |$0.30/MTok|$15/MTok|
|Small/fast   |Planner / Extractor / Contradiction / Safety (conditional)|$0.60/MTok|$0.06/MTok|$2/MTok |

**Hosted tier uses OpenRouter or direct-provider routing as configured.** If OpenRouter is used, pricing assumptions must include its credit-purchase fee overhead. Any cache-read estimate used in pricing must be tied to a verified provider/platform adapter, not borrowed across surfaces by analogy.

#### Illustrative Hosted Model Cost Per Turn

|Scenario                |Minimal|Moderate|Complex|
|------------------------|-------|--------|-------|
|**Hosted full pipeline**|~$0.05 |~$0.07  |~$0.09 |

These are illustrative model-cost estimates derived from cache-mitigated assumptions, not universal guarantees. Issue 14 adapter calibration may materially change them. Infra and service overhead are additional, though secondary relative to inference cost.

### Hosted Subscription Pricing Logic

Hosted subscriptions are **metered subscriptions with included credits**.

The subscription price must cover:

- included monthly credit allowance
- expected cache-mitigated model cost
- storage and retrieval infrastructure
- ingestion jobs and background processing
- support, payment overhead, and a real margin buffer

Top-ups absorb variance from heavy users without forcing the base subscription high enough to subsidize pathological usage. This is preferable to fake-unlimited pricing for an AI-native narrative product.

**Economic principle:** hosted subscription pricing should be set so that a normal engaged user fits comfortably inside the included credits, while heavy use expands through explicit top-ups rather than invisible margin erosion.

### BYOK Pricing Logic

BYOK is split into two commercial components:

#### 1. Perpetual BYOK License

The one-time purchase covers:

- permanent right to use Afterworlds with the user’s own API/provider keys
- product access and core feature parity with hosted users
- first year of Cloud Services bundled
- continuing access to owned functionality under the license terms

#### 2. BYOK Cloud Services Renewal

After the included first year, optional annual renewal covers ongoing hosted-service costs such as:

- cloud story storage
- sync / backup / remote access
- pack ingestion processing
- marketplace participation infrastructure (when applicable)
- other continuing platform services that generate real recurring expense

This keeps the commercial model honest: the software/product right is perpetual; the hosted-service layer is renewable.

### BYOK Non-Renewal Assumption

If Cloud Services are not renewed, the system must preserve trust:

- read/export/download access to owned work remains available where practical
- only genuine recurring-cost services are suspended or reduced
- reactivation later remains straightforward

This is both a product-policy commitment and a business-model constraint.

### Future Revenue Layers

Planned later-stage monetization layers remain compatible with this structure:

- **Creator marketplace** (v3): transaction fees, seller services, discovery/promotion tools
- **Institutional licensing**: pooled budgets, per-seat pricing, or capped-usage agreements
- **Expansion packs / major feature categories** for BYOK users, provided these are clearly new capabilities rather than withheld essentials

### Pricing Commitments and Unknowns

**Committed:**

- one canonical Sojourn orchestration path (core narrative pipeline + safety envelope) across all paying access paths
- hosted subscription with credits
- top-ups rather than silent degradation
- BYOK perpetual license + first year of Cloud Services included
- optional annual Cloud Services renewal thereafter
- support/audit/deletion minimums sufficient to run the business responsibly at launch

**Still to finalize before public pricing lock:**

- exact monthly hosted credit allotments
- top-up package sizes and pricing
- rollover policy and cap
- exact BYOK license price
- exact annual Cloud Services renewal price
- institutional pricing structure
- marketplace fee structure
- provider/platform-specific cache adapter calibration used by production cost models

These can be tuned later. The commercial architecture itself should now be treated as stable.

-----

## Item 9 — Construction Order Is Defined

The following issues define the pre-v1 internal construction sequence.

**Issues 1–11 (foundation and core services) — fully defined before construction and now completed as the foundation for the pipeline tranche:**

1. Repo skeleton, config, linting, test harness, CI scaffold
1. Core models: Story / Arc / Chapter / Node / Turn — including World/Character State schema and mode-specific session state (RPG: HP, dice state, active quests; Branching: pacing stage, plot thread tracker; Writing: beat constraints, version history pointers)
1. SQLite persistence and CRUD services for all core models
1. Story Bible schema and service — static / dynamic / provisional partitions, Events Ledger with tiered inclusion policy, Locked/Forbidden Facts as first-class entries
   5a. Rules Package schema and data model — package metadata, rule chunk model, structured mechanical entities, source tracking, precedence/override model
   5b. Rules Package ingestion pipeline — ingestion tooling from approved source materials, package publication flow, d20 v1 ingestion path; delivers one ingested, published, and queryable curated d20 Rules Package in the development environment
1. Rolling summary service — compression trigger, update policy
1. Intent classification — lightweight model call; classifies input before context assembly
1. Context builder — assembles stable context once per turn; volatile suffix separately; pass-forward additions tracked; retrieves rule slices on demand by mode
1. Minimal Writer path — single-pass, no orchestration, no pipeline yet; proves the Writer call works end to end
1. Extractor classification policy — proposes canon updates, does not write directly; routes to locked / soft / transient / unresolved
1. Lightweight contradiction checker — parallel sync, small/fast model, release-minimum scope

**Issues 12a–12c (pipeline completion tranche) — formally specified after Issue 11 completion:**

12a. Planner pass — callable service, typed `PlannerResult` / `PlannerOutput`, focused prompt contract, structured-output parsing, tests; no orchestration policy  
12b. Safety Service: Input Preflight and Conditional Output Audit — callable `SafetyService` with `INPUT` / `OUTPUT` target, typed `SafetyResult`, prompt contract, safety taxonomy, typed `SafetyPassError`, tests; no orchestration policy  
12c. Full pipeline orchestration — safety envelope integration; OOC short-circuit; input preflight gating; output audit gating; provider-refusal handling; PassForwardLedger composition across passes; transaction boundaries; shared stable-context rendering consolidation across provider-backed passes; output gated on safety envelope and Contradiction clearing

**Issues 13–21 (entitlements, routing, modes, release integration) — directionally sequenced, but not yet formally specified. After Issue 12c is complete, construction pauses until Issues 13–21 are drafted with boundaries, deliverables, acceptance criteria, and test requirements before implementation proceeds:**

13. Entitlement routing logic — hosted subscription credits/top-ups, BYOK license state, Cloud Services active/lapsed status, and storage/ingestion entitlement enforcement; tested as architectural invariant  
14. BYOK API key management, provider/platform routing, OpenRouter integration, provider capability profiles, and cache-capability adapters that realize Afterworlds’ generalized cache intent through provider-specific payload strategy, retention defaults, and cache-metric interpretation  
15. RPG mode integration — prompt contract loaded as versioned artifact, d20 adjudication against ingested Rules Package, dice handling modes wired (Player rolls / AI rolls), GM cheating toggle, pre-play sequence enforced, character sheet as first-class persistent object  
16. Branching mode integration — prompt contract loaded, pacing stage tracking calibrated to length preference, branch generation call, freeform input as first-class option  
17. Writing mode integration — prompt contract loaded, persona-based model (three Mentor personas: Chiron, Merlin, Vidura; three Peer personas: Odin, Athena, Thoth), persona behavioral briefs and prompt injections wired, beat constraints  
18. ChromaDB integration — vector retrieval service, collection schema per story and rules corpus, semantic query wired into context builder  
19. Frontend skeleton — story creation, mode selection, turn submission, output display; React vs. Svelte resolved before this issue  
20. User-facing billing and BYOK configuration — API key entry, provider selection, hosted credit balance/top-up visibility, Cloud Services status, and burn-rate communication  
21. Full end-to-end integration test — all three modes, hosted and BYOK access paths, first release-capable MVP spine demo confirmed working

**Issue 22** remains the explicit pre-specified exception because the operational gap was resolved pre-construction and v1 release readiness depends on it:

22. Operations, support, and compliance minimums — support lookup, entitlement event log, controlled manual remediation path, delete/export workflow, and basic anomaly visibility sufficient for responsible v1 launch

This document now reflects the actual phase boundary: Issues 12a–12c have been formally pulled into the construction plan after Issue 11 completion; Issues 13–21 are not to be implemented from roadmap shorthand. Their formal issue definitions are the next specification task after Issue 12c closes.

-----

## Item 10 — Each Early Issue Has Boundaries and Acceptance Criteria

-----

**Issue 1 — Repo Skeleton**

- *Goal:* Establish the project structure, tooling, and CI scaffold before any application code is written
- *In scope:* Directory structure, pyproject.toml, Black + Ruff + mypy configuration, pytest harness, GitHub Actions CI pipeline running format/lint/type/test checks, branch protection rules on main, PR template with Architecture Notes section, detect-secrets pre-commit hook
- *Out of scope:* Any application logic, models, routes, or services
- *Deliverables:* Passing CI on an empty test suite; PR template in place; branch protection active
- *Acceptance criteria:* CI passes on a trivial commit; direct commits to main are rejected; PR template appears on all new PRs
- *Test requirements:* Trivial smoke test confirming pytest runs; no application tests yet

-----

**Issue 2 — Core Models**

- *Goal:* Define the backbone data objects the entire system depends on
- *In scope:* Story, Arc, Chapter, Node, Turn as Pydantic models; World/Character State schema (static and dynamic partitions); mode-specific session state schemas (RPG, Branching, Writing); field definitions and type annotations for all. RPG character sheet must be modeled as a first-class persistent object with structured fields (class, stats, skills, equipment, current and maximum HP, spell slots, etc.) and support for mutable values — not as a blob or freeform field on session state.
- *Out of scope:* SQLite persistence — Issue 3; Story Bible schema — Issue 4; Rules Package schema — Issue 5a; any routes or services
- *Deliverables:* All models defined with full type annotations; unit tests confirming instantiation and field validation
- *Acceptance criteria:* Models instantiate correctly; invalid field types are rejected; mode-specific session state is cleanly separated from core Node schema; RPG character sheet is a distinct structured model, not a freeform field
- *Test requirements:* Unit tests for each model; edge cases for optional fields; character sheet field validation tests

-----

**Issue 3 — SQLite Persistence and CRUD**

- *Goal:* Persist and retrieve all core models reliably
- *In scope:* SQLite schema for all Issue 2 models; CRUD services for Story, Arc, Chapter, Node, Turn, World/Character State; migration tooling (Alembic); basic integrity constraints
- *Out of scope:* Story Bible persistence — Issue 4; Rules Package persistence — Issue 5; any API routes; any business logic
- *Deliverables:* Working CRUD for all core models; migration baseline; unit tests confirming round-trip persistence
- *Acceptance criteria:* All models persist and retrieve correctly; foreign key relationships enforced; no data loss on round-trip
- *Test requirements:* Round-trip tests for each model; referential integrity tests; concurrent write safety baseline

-----

**Issue 4 — Story Bible Schema and Service**

- *Goal:* Implement the Story Bible as a structured, partitioned, append-safe canon store
- *In scope:* Static / dynamic / provisional partition schema; Events Ledger with tiered inclusion policy (recent N + high-significance flag; start N at 15, tune with testing); Locked Facts and Forbidden Facts as first-class entries; Relationship Ledger; Character entries with role tagging and static/dynamic field separation; Story Bible CRUD service; Extractor proposal staging area (not Extractor logic — Issue 10); significance flagging criteria to be defined during this issue
- *Out of scope:* Rolling summary — Issue 6; Extractor classification logic — Issue 10; any prompt construction
- *Deliverables:* Story Bible schema in SQLite; service for reading active context window per tiered inclusion policy; unit tests
- *Acceptance criteria:* Static partition requires explicit confirmation to update; Events Ledger loads correct subset per tiered inclusion policy; Locked Facts are queryable as a distinct set; provisional entries are staged separately from ratified canon
- *Test requirements:* Tiered inclusion policy unit tests; partition isolation tests; locked fact enforcement tests; provisional staging tests

-----

**Issue 5a — Rules Package Schema and Data Model**

- *Goal:* Define the data model for the external mechanical-canon subsystem RPG mode depends on
- *In scope:* Rules Package schema; rule chunk model; structured mechanical entity model (conditions, actions, spells/items/stat blocks as available in source); source tracking; precedence/override model; unit tests
- *Out of scope:* Ingestion pipeline and corpus delivery — Issue 5b; live RPG adjudication wiring — Issue 15; full semantic retrieval service integration — Issue 18; branch/writing canon-pack extensions — deferred
- *Deliverables:* Rules Package schema and data model with full type annotations; unit tests confirming instantiation, field validation, and override precedence
- *Acceptance criteria:* Rules Package is cleanly separated from Story Bible and session state; override model layers without mutating source records; source provenance fields are present and enforced per chunk/entity
- *Test requirements:* Schema separation tests; provenance field tests; override precedence tests; instantiation and field validation tests

-----

**Issue 5b — Rules Package Ingestion Pipeline**

- *Goal:* Build the ingestion tooling and deliver a queryable d20 Rules Package in the development environment
- *In scope:* Ingestion pipeline from approved source materials into SQL + vector index; package publication flow; d20 v1 ingestion path; at least one ingested, published, and queryable curated d20 Rules Package in non-production seed/dev form; unit tests
- *Out of scope:* Live RPG adjudication wiring — Issue 15; full semantic retrieval service integration — Issue 18; branch/writing canon-pack extensions — deferred
- *Deliverables:* Working ingestion tool/service; published and queryable d20 Rules Package in the development environment; unit tests
- *Acceptance criteria:* Ingested d20 package can be queried by subsystem and semantic lookup; overrides can be layered without mutating source records; source provenance is preserved per chunk/entity; ingestion is repeatable from approved source materials
- *Test requirements:* Ingestion round-trip tests; provenance tests; representative query tests across at least combat, conditions, and one additional subsystem

-----

**Issue 6 — Rolling Summary Service**

- *Goal:* Maintain a compressed narrative history that fits within the stable prefix budget
- *In scope:* Rolling summary schema; compression trigger (every N turns — start at 10, tune with testing); summary generation call (lightweight model); summary persistence; service for retrieving current summary
- *Out of scope:* Context builder integration — Issue 8; N tuning is a known unknown, 10 is the starting value
- *Deliverables:* Rolling summary service; compression trigger logic; unit tests
- *Acceptance criteria:* Summary updates correctly at trigger threshold; previous summaries preserved in SQLite; summary retrieval returns current version
- *Test requirements:* Trigger threshold tests; compression output tests; version history tests

-----

**Issue 7 — Intent Classification**

- *Goal:* Classify player input before context is assembled — intent classification precedes context building by design
- *In scope:* Intent taxonomy (in-character action / dialogue / author instruction / branch choice / beat milestone / rewind / lore question / OOC); lightweight model call with focused classification prompt; classification result schema passed to context builder
- *Out of scope:* Context builder — Issue 8; any mode-specific handling of classified intent
- *Deliverables:* Intent classifier returning typed classification result; unit tests across intent types
- *Acceptance criteria:* All defined intent types are classifiable including ambiguous and creative inputs; OOC input reliably detected; classification result is a typed object, not a raw string; misclassification rate acceptable on edge case test set
- *Test requirements:* One test per intent type; ambiguous and creative input edge cases; OOC detection tests; edge case test set defined during this issue

-----

**Issue 8 — Context Builder**

- *Goal:* Assemble the full context payload for each pipeline pass, with stable prefix and volatile suffix cleanly separated
- *In scope:* Stable prefix assembly (system prompt + mode contract + Story Bible active context + rolling summary); volatile suffix assembly (recent turns + current input + classified intent); pass-forward addition tracking; assembly called once per turn, shared across passes
- *Out of scope:* Pipeline orchestration — Issue 11; actual pipeline calls — Issues 9–11
- *Deliverables:* Context builder service returning stable prefix and volatile suffix as distinct objects; unit tests confirming assembly order and content
- *Acceptance criteria:* Stable prefix always assembled in correct order; Story Bible and rolling summary never mixed with prose history in stable prefix; volatile suffix contains only recent turns and current input; assembly is called once per turn, never per pass
- *Test requirements:* Assembly order tests; partition separation tests; content correctness tests for each scenario (minimal / moderate / complex Story Bible)

-----

**Issue 9 — Minimal Writer Path**

- *Goal:* Prove end-to-end that a player input goes in and coherent prose comes out — single pass, no orchestration
- *In scope:* Single Writer LLM call using assembled context; response parsing; Turn saved to SQLite; no Planner, no Extractor, no Contradiction, no Safety yet
- *Out of scope:* Full pipeline orchestration — Issue 12; mode-specific prompt contracts — Issues 15–17; this is a proof-of-life call, not a production path
- *Deliverables:* Working Writer call with context builder output as input; Turn persistence; integration test confirming round-trip
- *Acceptance criteria:* Input goes in, prose comes out, Turn is saved; context assembly confirmed correct before the call; response is parseable
- *Test requirements:* Integration test: full round-trip from input to saved Turn; context content verification before call

-----

**Issue 10 — Extractor Classification Policy**

- *Goal:* Implement the Extractor pass per Item 2, Principle #5 (proposes updates, never writes canon directly)
- *In scope:* Extractor LLM call on Writer output; classification of proposed updates (locked / soft / transient / unresolved); staging area for proposed updates pending ratification; service for surfacing locked-fact proposals to Sojourner for confirmation; auto-commit logic for soft and transient facts
- *Out of scope:* Pipeline orchestration wiring — Issue 12; UI for Sojourner confirmation — deferred
- *Deliverables:* Working Extractor pass; classification routing; staging area persistence; unit tests
- *Acceptance criteria:* Extractor never writes directly to canon; locked fact proposals are staged and require confirmation; soft and transient facts auto-commit with correct flags; unresolved threads queued, not committed
- *Test requirements:* Classification routing tests for each category; direct-write prevention test (architectural invariant); auto-commit behavior tests

-----

**Issue 11 — Lightweight Contradiction Checker**

- *Goal:* Implement the contradiction checker per the architecture defined in Item 7 (sequential gate on Writer output, small/fast model)
- *In scope:* Contradiction checker LLM call with focused prompt; checker evaluates Writer candidate output against Story Bible and assembled context; baseline scope against recent context + active Story Bible context; output gate logic; contradiction result schema
- *Out of scope:* Retrieval expansion beyond the currently wired context sources — deferred until ChromaDB is integrated (Issue 18); pipeline orchestration wiring — Issue 12
- *Deliverables:* Working contradiction checker; gate logic; unit tests
- *Acceptance criteria:* Checker evaluates Writer output before delivery, not input context alone; output is gated — nothing ships until checker clears; baseline scope correctly covers recent context + active Story Bible context; contradictions caught and reported before delivery
- *Test requirements:* Gate behavior tests; scope boundary tests (baseline context vs. expanded retrieval once available); known contradiction detection tests using representative examples (dead character acting, item never acquired, locked fact violated) — these are test anchors, not the complete set of detectable violations

-----

**Issue 12a — Planner Pass**

- *Goal:* Implement the standalone Planner pass that consumes `BuiltContext`, makes one focused small/fast-model call, and returns a typed `PlannerResult` containing a validated `PlannerOutput` (`scene_goal`, `next_beat`, `facts_needed`, optional `notes`) for later orchestration handoff to the Writer.
- *In scope:* `PlannerService.plan(built_context)`; typed Planner schema and typed `PlannerPassError`; versioned Planner prompt contract; structured-output/tool-use parsing; injectable model dependency; pass-level usage/cache metrics; validation that the Planner reads the provided `BuiltContext` without mutating it; default-CI and opt-in real-provider coverage.
- *Out of scope:* Pipeline orchestration; Writer invocation; PassForwardLedger composition at runtime; Safety behavior; OOC short-circuit routing; persistence or Story Bible writes; structured retrieval-query design beyond v1 natural-language `facts_needed` references.
- *Deliverables:* Planner service; `PlannerOutput`, `PlannerResult`, `PlannerPassError`; Planner prompt artifact; tests covering schema validation, parser failure modes, immutable input context, structured-output handling, and integration against a representative Branching-mode context.
- *Acceptance criteria:* Valid Planner calls return well-formed typed results; required text fields are non-empty after trimming; `facts_needed` remains list-typed and may be empty; malformed or missing structured output raises `PlannerPassError`; provider exceptions are wrapped cleanly; the caller’s `BuiltContext` remains unchanged; the service performs no orchestration or persistence.
- *Test requirements:* Unit tests for output validation, parser error paths, provider exception wrapping, dependency injection, and non-mutation of `BuiltContext`; default-CI integration test using a high-fidelity fake provider; opt-in real-provider integration test behind the explicit credential gate.

-----

**Issue 12b — Safety Service: Input Preflight and Conditional Output Audit**

- *Goal:* Implement the callable Safety service that evaluates either Sojourner input or Writer-generated output through one typed safety taxonomy and returns a typed `SafetyResult` for later orchestration by Issue 12c.
- *In scope:* `SafetyService.check(built_context, text, target)` with `SafetyTarget.INPUT` / `SafetyTarget.OUTPUT`; typed `SafetyResult`, `SafetyReport`, `SafetyConcern`, category and verdict model; Safety prompt contract; tool-use parsing; evidence-summary validation; typed `SafetyPassError`; usage metrics exposed through `SafetyResult.usage`; default-CI and opt-in real-provider coverage.
- *Out of scope:* Deciding when Safety runs; provider whitelist or capability policy; pipeline gating; UI/block messaging; provider-routing fallback; treating narrative-pass provider refusals as Safety verdicts; persistence or mutation of the caller’s `BuiltContext`.
- *Deliverables:* Safety service; versioned Safety prompt artifact; Safety schema/result types; typed `SafetyPassError`; tests for INPUT and OUTPUT target behavior, ALLOW/BLOCK derivation, concern validation, provider/parse failure handling, and integration against representative built contexts.
- *Acceptance criteria:* INPUT and OUTPUT checks both return the same typed result family; `verdict` derives from concerns (`ALLOW` when none, `BLOCK` when any concern exists); evidence summaries obey validation requirements; Safety operational failures, including provider failures from the Safety call, raise `SafetyPassError`; provider refusals from other narrative/state passes are not recast as Safety verdicts; the service performs no orchestration, persistence, delivery decision, or context mutation.
- *Test requirements:* Unit tests for target handling, verdict derivation, taxonomy/schema validation, evidence-summary constraints, malformed response handling, provider exception wrapping, and context immutability; default-CI fake-provider integration coverage; opt-in real-provider integration test behind the explicit credential gate.

-----

**Issue 12c — Full Pipeline Orchestration**

- *Goal:* Implement the `OrchestratorService` that turns the standalone callable services from Issues 7–12b into a working end-to-end Turn: intent classification, context assembly, safety envelope, Planner → Writer → Extractor || Contradiction orchestration, delivery gating, rollback-safe side-effect coordination, and typed terminal outcomes.
- *In scope:* `OrchestratorService.orchestrate_turn(...)`; exhaustive `PipelineDisposition` and `OrchestrationResult`; conditional Input Safety Preflight and Output Safety Audit through an injected `SafetyPolicy`; OOC short-circuit and placeholder OOC handler routing; PassForwardLedger composition; typed provider-refusal handling for narrative/state passes; `SafetyPassError → PIPELINE_ERROR` handling; outer transaction bracketing provisional Writer Turn persistence and Extractor writes; thread-safe parallel sync with Contradiction on a worker and Extractor on the orchestrator thread; SAVEPOINT-based nested extractor routing; OOC recent-turn exclusion; stable-context rendering consolidation across provider-backed passes so they share one rendering path for the stable context region; required known-unknowns and architecture-note updates.
- *Out of scope:* Entitlement gating; provider/platform routing or cache-capability adapters; refusal-aware fallback; mode-specific orchestration overrides; full OOC protocol authoring for RPG/Branching/Writing modes; ChromaDB retrieval integration; UI-facing block/refusal messaging; streaming; retry/regenerate/rewind semantics beyond the documented v1 posture.
- *Deliverables:* Orchestrator service and typed result/disposition/error models; `SafetyPolicy`; OOC handler prompt artifact; backward-compatible session participation extensions needed for rollback-safe Turn and Extractor writes; `RecentTurnReader` OOC filtering extension; shared stable-context rendering utility replacing pass-local drift-prone stable-region helpers; unit, integration, SAVEPOINT-proof, and opt-in real-provider tests; PR Architecture Notes and known-unknowns updates.
- *Acceptance criteria:* Non-OOC turns follow the canonical safety-envelope + core-pipeline ordering; OOC turns short-circuit Planner/Extractor/Contradiction while still obeying SafetyPolicy; only delivered/OOC-handled Turns survive persistence; blocked, refused, or errored prose leaves no surviving Turn or canon writes; Contradiction BLOCK rolls back provisional Turn + Extractor side effects atomically; dispositions obey explicit population invariants; provider refusals and Safety operational failures map to their correct terminal states; the shared stable-context renderer eliminates pass-local duplicate collection/order/omission/breakpoint-placement logic without becoming a provider cache adapter.
- *Test requirements:* Disposition-matrix and taxonomy tests; OOC routing tests; safety-policy gating tests; transaction rollback tests for Output Safety BLOCK, Contradiction BLOCK, refusal, and operational error paths; SAVEPOINT-proof integration against real SQLite; thread-safe parallel-sync tests; OOC recent-turn exclusion tests; stable-context rendering identity and TTL-plumbing tests; default-CI end-to-end orchestration tests with high-fidelity fakes; opt-in real-provider integration test behind the explicit credential gate.

-----

**Issue 22 — Operations, Support, and Compliance Minimums**

- *Goal:* Provide the minimum human-operable tooling and workflows needed to run Afterworlds responsibly at v1 launch
- *In scope:* support account lookup; entitlement event log for credits/top-ups/subscription and Cloud Services transitions/manual overrides; controlled manual remediation actions with operator reason capture; deletion/export workflow and request status handling; basic anomaly visibility sufficient to identify unusual hosted-credit burn or broken entitlement state; tests and documentation for all of the above
- *Implementation note:* Issue 22 defines and persists its own support/entitlement models, tables, and services using the persistence patterns established in Issues 2–3. It must not assume those artifacts already exist as a byproduct of the narrative-model work.
- *Out of scope:* full-featured admin dashboard; advanced BI analytics; CRM/ticketing system; fraud suite; enterprise reporting; generalized back-office platform
- *Deliverables:* support-facing lookup path; append-safe entitlement/support event history; controlled remediation service/UI path; delete/export operational workflow; basic usage anomaly surfacing; documentation of what actions exist and how they are logged
- *Acceptance criteria:* support can identify a customer and inspect their relevant access/credit/service state; entitlement transitions are reconstructable in order; manual remediation actions require explicit reason capture and are logged; delete/export requests have a defined code path and status model; anomaly visibility is sufficient to flag obviously abnormal usage or broken state; no support action silently mutates state without an audit trail
- *Test requirements:* event-order reconstruction tests; manual-override logging tests; deletion/export workflow tests; access-control tests for support actions; anomaly-threshold or anomaly-flag behavior tests where applicable

-----

## Item 11 — Repo Governance as Agent Coordination Protocol

**Branch strategy:**

- Feature branches per issue: `feature/issue-N-short-description`
- No direct commits to main under any circumstances — including by the project owner
- Main is always in a deployable state
- Hotfix branches permitted for critical post-merge fixes: `hotfix/issue-N-description`

**Claude Code authorization:**

- Authorized to implement fully within stated issue scope without checking in
- Authorized to make locally reasonable design decisions within issue scope — but must document them in the PR Architecture Notes section
- Not authorized to merge to main under any circumstances
- Not authorized to modify CI gate configuration without explicit approval
- Not authorized to make decisions that touch Known Unknowns — must flag and pause
- Must flag architecture drift explicitly in PR description rather than silently resolving it

**PR requirements:**

- Claude Code opens all PRs with a structured description including: what was built, how it satisfies each acceptance criterion, test coverage summary, and an Architecture Notes section (either “No drift from design principles” or explicit description of any deviation and rationale)
- No PR merges without Codex review passing
- No PR merges with failing CI
- PR scope must match issue scope — scope creep is a review failure

**Commit message format — conventional commits:**
`type(scope): description`
Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
Example: `feat(story-bible): implement tiered inclusion policy for events ledger`

**Architecture drift flag:**
Every PR description includes an Architecture Notes section. If Claude Code’s implementation deviates from any principle in the Construction Readiness Document, it must describe the deviation, explain why it was necessary, and propose resolution. Silent resolution of architecture questions is a review failure regardless of whether the code works.

**Operational-sensitivity addendum:**
Any PR touching entitlements, credits, Cloud Services state, support remediation, deletion/export behavior, or support-facing logs must explicitly describe:

- state transitions affected
- user-visible consequences
- audit/logging changes
- rollback or repair implications

-----

## Item 12 — CI Gates as Quality Handoff Contract

**Standard gates (active from Issue 1):**

|Gate               |Tool          |Notes                                                                           |
|-------------------|--------------|--------------------------------------------------------------------------------|
|Formatting         |Black         |pyproject.toml; zero tolerance                                                  |
|Linting            |Ruff          |pyproject.toml; zero tolerance                                                  |
|Type checking      |mypy          |Strict mode; zero tolerance                                                     |
|Unit tests         |pytest        |Coverage measurement active; –cov-fail-under=80 enforcement activates at Issue 2|
|Dependency scanning|pip-audit     |Block on known vulnerabilities                                                  |
|Secret scanning    |detect-secrets|Pre-commit hook; block on any secret pattern                                    |

**Architectural invariant tests (added progressively as each component lands):**

|Invariant                                                                                                                     |Added at issue|
|------------------------------------------------------------------------------------------------------------------------------|--------------|
|Minimum 80% coverage on new code — pytest –cov-fail-under=80                                                                  |Issue 2       |
|Story Bible and prose history stored in separate tables, never commingled                                                     |Issue 4       |
|Prompt assembly follows stable-prefix-first order; assembled once per turn, never per pass                                    |Issue 8       |
|App starts without error — uvicorn startup smoke test                                                                         |Issue 9       |
|Extractor cannot write directly to canon without classification step                                                          |Issue 10      |
|Output never delivered until contradiction checker clears                                                                     |Issue 11      |
|Entitlement routing never removes the core narrative pipeline or safety envelope                                              |Issue 12c     |
|Hosted credit/top-up enforcement and BYOK Cloud Services entitlements behave correctly                                        |Issue 13      |
|Provider/platform cache adapters realize generalized cache intent without moving provider-specific cache semantics into orchestration or Context Builder |Issue 14|
|Operational event history reconstructs entitlement/support state transitions and delete/export actions                        |Issue 22      |

Codex receives only PRs that have already passed all active CI gates. Review effort is spent on design, logic, and security — not formatting failures or type errors.

-----

## Item 13 — Documentation Standards as Architectural Drift Detection

**Where docs live:**

|Doc type                  |Location                                      |
|--------------------------|----------------------------------------------|
|Architecture docs         |`/docs/architecture/`                         |
|Mode prompt contracts     |`/docs/prompts/` (versioned .md files)        |
|Decision logs             |`/docs/decisions/` (ADR format)               |
|Construction readiness doc|`/docs/architecture/construction_readiness.md`|
|Design doc                |`/docs/architecture/design.md`                |
|Known unknowns            |`/docs/architecture/known_unknowns.md`        |
|Spine demo definition     |`/docs/architecture/spine_demo.md`            |

**Canonical vs. provisional:**
Canonical docs are the Construction Readiness Document, the Design Document, and the mode prompt contracts. Any file marked `DRAFT` in both its filename and document header is provisional. Provisional docs may be referenced but not relied upon as behavioral spec.

**Update rule:**
Any PR that changes behavior described in a canonical doc requires a corresponding doc update in the same PR. This is a Codex review criterion, not a suggestion. If the code has changed and the doc has not, the PR is not complete.

**Decision log format (ADR):**
When a significant implementation decision is made during construction — anything that resolves a Known Unknown, deviates from design intent, or makes a load-bearing choice not covered by existing docs — Claude Code writes a short ADR in `/docs/decisions/` in the same PR. Format: decision title / context / decision made / rationale / consequences.

**Operational documentation rule:**
Any PR that changes entitlement behavior, support remediation capabilities, or deletion/export handling must update the relevant operator-facing documentation in the same PR. Support-critical behavior must not live only in code.

-----

## Item 14 — Business-Model-Sensitive Constraints for Builders

The following are architectural invariants, not conventions. Codex reviews against them explicitly.

1. **There is one canonical narrative engine.**
   All paying access paths use the full Sojourn orchestration path: core narrative pipeline (Planner → Writer → Extractor → Contradiction) protected by a safety envelope (input preflight when required; conditional output audit when required). No commercial tier may remove core continuity functions or responsible guardrails in order to create an artificial upgrade path.
1. **Commercial differentiation is handled through entitlements, not degraded continuity.**
   Tier routing governs billing path, subscription status, credit balance, Cloud Services status, storage/ingestion entitlements, and related access controls — not whether the user receives the real product.
1. **Hosted subscriptions use credits.**
   Hosted access is a metered subscription with included credits and transparent top-ups. When credits are exhausted, the system must stop cleanly or prompt for top-up. It must never silently lower continuity quality, drop passes, or otherwise degrade the engine without explicit user knowledge.
1. **Top-up flows must be transparent and non-manipulative.**
   No dark-pattern upgrade prompts, fake urgency, or concealed overage behavior. Usage, remaining credits, and top-up consequences must be legible in the UI.
1. **BYOK is a first-class path.**
   BYOK users receive full pipeline parity with hosted users. All core product functionality must work under BYOK routing. BYOK is not a fallback or reduced-function mode.
1. **BYOK commercial structure is split into license and services.**
   The perpetual BYOK license grants permanent product rights and includes the first year of Cloud Services. Ongoing hosted capabilities after that period depend on optional annual Cloud Services renewal. Builders must not collapse these concepts in code, entitlement logic, or user-facing language.
1. **Cloud Services are concrete, not vague.**
   Renewal-sensitive entitlements must map to actual ongoing platform costs such as storage, sync, backup, remote access, ingestion processing, marketplace participation infrastructure, and similar hosted services. “Maintenance fee” is not a sufficient internal product concept.
1. **BYOK non-renewal must fail gracefully.**
   If a BYOK user does not renew Cloud Services, the system must preserve read/export/download access to owned work where practical and suspend only the genuinely recurring-cost hosted services. User-created content must never be held hostage as leverage.
1. **Cache intent is provider-neutral; cache realization is adapter-specific.**
   Afterworlds’ core architecture preserves deterministic stable/volatile context separation and stable-context reuse discipline. Provider/platform adapters own cache-key semantics, explicit breakpoint or cached-context-object strategy, tool/system/payload effects on reuse, TTL/retention controls, cache metrics, and verified cache-hit behavior. Orchestration, Context Builder, and pass-service business logic must not assume one provider’s caching model as universal.
1. **Stable context assembly remains invariant.**
   Stable context is assembled once per turn and shared across all passes. Any implementation that rebuilds the typed stable context independently per pass is an architectural violation.
1. **Cache-lifetime defaults are adapter-calibrated.**
   Where a provider/platform adapter supports a materially beneficial longer-lived cache mode or equivalent retention control without unacceptable tradeoffs, the adapter should make that the default and document the rationale. Cost-model claims must cite adapter calibration rather than universal TTL assumptions.
1. **Entitlement routing logic must be tested as an architectural invariant.**
   Dedicated tests must confirm correct enforcement of:
   - hosted subscription credit balances
   - top-up behavior
   - BYOK license entitlements
   - Cloud Services active vs. lapsed status
   - storage / ingestion / sync entitlement boundaries
   - full-pipeline parity across hosted and BYOK paths
1. **Marketplace and institutional features must layer onto this model, not rewrite it.**
   Future marketplace fees, seller tools, institutional budget controls, or pooled-credit models must remain compatible with the core architecture above: one engine, transparent usage, clear ownership boundaries, and no degraded-continuity tier tricks.
1. **Operational support actions must be explicit, bounded, and logged.**
   Manual credit grants, trial/service extensions, entitlement repairs, deletion/export processing, or similar support actions must happen through defined code paths or procedures with operator attribution and reason capture — not through silent ad hoc mutation.
1. **A user-facing billing model implies a support-facing reconstruction model.**
   If the product can charge, grant, revoke, renew, lapse, or top up access, the system must preserve enough event history for support to reconstruct what happened in order.
1. **Deletion/export is part of launch dignity, not deferred polish.**
   If Afterworlds stores paid user data or runs hosted services, delete/export handling requires a deliberate code path before launch, even if the first implementation is modest and operator-assisted.

-----

## Item 15 — Known Unknowns Are Listed Explicitly

All known unknowns — both resolved and open — are maintained in the canonical reference document:

**`/docs/architecture/known_unknowns.md`**

That document includes: the full list of decisions resolved before construction, the full list of open unknowns with resolution windows and context, and instructions for Claude Code and Codex on how to handle unknowns encountered during implementation.

**Operational note:** The existence of Issue 22 resolves the earlier ambiguity about whether the support/compliance layer had an explicit home in the construction plan. The remaining unknowns should concern implementation details, not whether the layer exists.

-----

## Item 16 — Minimal End-to-End Slice Is Defined

The full spine demo definition — including all three mode slices, prerequisites, step-by-step pass criteria, and failure modes to watch for — is maintained in the canonical reference document:

**`/docs/architecture/spine_demo.md`**

The primary spine is Branching mode. RPG and Writing mode slices extend from it. All three must pass before v1 is declared release-capable (Issue 21).

**Operational addendum for release readiness:** Passing the narrative spine demo is necessary but not sufficient for v1 release. Issue 22’s operations/support minimums must also be in place before launch.

-----

## Item 17 — The Handoff Trigger Is Chosen

Construction begins when:

- All items on this checklist are complete and committed to the repo
- First 11 GitHub issues are written with goals, scope boundaries, deliverables, and acceptance criteria
- Mode prompt contracts exist as versioned .md files in `/docs/prompts/`
- Repo structure, CI gates, and branch protection rules are active in GitHub
- PR template with Architecture Notes section is in place
- Known Unknowns are documented in `/docs/architecture/known_unknowns.md`
- Minimal end-to-end slice is described in `/docs/architecture/spine_demo.md`

> *The exact sentence: construction begins when the repo is ready to receive Issue 1 and Issue 1 is written well enough that Claude Code could start it without a conversation.*

**Release readiness reminder:** Construction can begin before Issue 22 is implemented. v1 cannot ship without Issue 22 being completed.

-----

*Construction Handoff Checklist — all 17 items complete. March 2026. Revised to v7 in May 2026 to replace five-pass pipeline framing with the safety-envelope model. Revised to v8 in May 2026 to make provider-neutral cache intent and provider/platform-specific cache adapter ownership explicit, formalize Issues 12a–12c after Issue 11 completion, and record the specification pause before Issues 13–21 implementation.*
