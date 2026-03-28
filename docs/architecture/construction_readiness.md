# Afterworlds Construction Readiness Document (v4)

*Items 1–17 of the Construction Handoff Checklist — completed March 2026*

---

## Item 1 — Product Scope is Pinned Down

### What Afterworlds Is

Afterworlds is a platform for exploring stories in an interactive, participatory way. It lets you enter the world of a story — whether you've created it or encountered it elsewhere — and live within it as the protagonist, making choices that shape the narrative according to your instincts rather than the original author's path.

The core impulse: when you finish a story you love — a novel, film, game — there's often a longing to continue it, to enter its world, or to live through it as your character would have rather than as the original author wrote it. Afterworlds bridges that gap.

### Who It's For

Lovers of story in all its forms, primarily:

- **Readers** who want to continue a story or inhabit it differently after finishing
- **Players** who want to experience narrative as an interactive game where they solve mysteries and face consequences
- **Budding writers** learning the craft through collaborative storytelling with an AI partner

### What Problem It Solves That Nothing Else Solves As Well

The longing at the end of a beloved story — the sense that the narrative should continue, or that you'd tell it differently if you could. Afterworlds closes that gap.

### What Is Explicitly In v1

v1 is the first release-capable MVP, not merely an internal build milestone.

- Text engine with full five-pass Sojourn pipeline
- RPG, Branching, and Writing modes
- Full story hierarchy (Story / Arc / Chapter / Node / Turn)
- Rolling summary + Story Bible
- Rules Package support with one curated, ingested, and queryable d20 Rules Package
- Vector retrieval memory (ChromaDB)
- Extractor update classification policy
- Contradiction checker
- SQLite persistence
- BYOK API support

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
- tier routing and BYOK support

v1 is the first release-capable MVP.

---

## Item 2 — Core Architecture Principles Are Frozen

These principles must not be casually reinvented during coding. Any code that violates them should be caught in review. Codex has this document as a written reference to cite in review comments.

1. **Story Bible is structurally separate from prose history**
2. **Six memory layers have distinct roles** (Immediate / Rolling Summary / Story Bible / Rules Package / Retrieval Memory / Contradiction Checker)
3. **Intent is classified before context is assembled**
4. **The pipeline is staged:** Planner → Writer → Extractor → Contradiction → Safety
5. **Extractor proposes canon updates; it does not write canon directly**
6. **Stable prompt prefix is assembled once per turn and shared across all passes for caching efficiency**

---

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

**Terminology guardrail:** Story Bible = narrative canon; Rules Package = external mechanical canon for RPG mode; canon pack = optional external lore/canon corpus for Branching/Writing modes. Session state remains separate from all three.

---

## Item 4 — Technical Stack Is Decided Enough to Begin

| Component | Decision |
|-----------|----------|
| **Backend** | Python + FastAPI |
| **Storage** | SQLite first; ChromaDB included in v1 release scope |
| **Frontend** | React or Svelte (resolve before Issue 19) |
| **Deployment** | Local web server accessed via browser |
| **Model access** | BYOK / hybrid as recommended default |

**Known unknown:** React vs. Svelte is acceptable to resolve during early construction (before Issue 19). It does not block architecture decisions.

---

## Item 5 — Core Entities Are Defined

| Entity | Description |
|--------|-------------|
| **Story** | Top-level container for a complete narrative |
| **Arc** | Major narrative division within a Story |
| **Chapter** | Subdivision within an Arc |
| **Node** | A story beat / state transition. Unified entity across all three modes; includes mode-specific metadata (branching logic for Branching mode, mechanical modifiers for RPG mode, beat constraints and version pointers for Writing mode). Node means "story beat" in all modes, but what constitutes a complete beat and how it's tracked varies by mode. |
| **Turn** | One interaction unit: one user input + one AI response |
| **Story Bible** | Structured narrative canon — world rules, cast, locked facts, timeline, forbidden facts |
| **Rolling Summary** | Compressed narrative history, auto-updated every N turns |
| **Rules Package** | External mechanical canon package for RPG mode; future canon-pack pattern for large franchise/reference corpora in Branching/Writing |
| **World / Character State** | Current world conditions, character stats, inventory, relationship meters |
| **Mode-Specific Session State** | RPG: HP, dice modifiers, active quests; Branching: pacing stage, branch tree, plot thread tracker; Writing: beat constraints, version history pointers |

**Key principle:** Node is a unified entity across all three modes. Mode-specific metadata flags make the distinction clear without duplicating the schema.

---

## Item 6 — Mode Prompt Contracts Are Written

The mode prompt contracts are canonical versioned artifacts. Full content — system prompts, pre-play sequences, and player configuration tables — lives in the prompt files. This section records the key decisions and design rationale behind each contract. Do not duplicate prompt text here; update the prompt files directly when contracts change.

**Canonical prompt files:**
- `/docs/prompts/rpg_mode.md`
- `/docs/prompts/branching_mode.md`
- `/docs/prompts/writing_mode.md`

---

### RPG Mode — Key Decisions

**Pre-play sequence is mandatory.** Two phases before Turn 1: world setup first, then character creation within that world context. Play does not begin until the character sheet is complete enough to adjudicate against.

**Character creation is GM-led and conversational.** The player either works through creation with the GM or pastes a completed sheet. Incomplete or ambiguous sheets trigger clarification before play begins — not during.

**Character sheet is a first-class persistent object.** Not a conversation artifact. Persists across sessions, mutable during play, tracks current and maximum values where applicable. Schema requirements flagged for Issue 2.

**v1 supports original and custom settings only.** Playing in existing licensed settings (Forgotten Realms, Greyhawk, etc.) requires player-supplied Setting Canon Packs — deferred to v2/v3.

**Dice handling has two modes.** Player rolls = GM announces check and modifiers, waits for player to report result, never narrates outcome before the roll. AI rolls = GM rolls and always shows the result. Hidden rolls (checks the player has no in-world awareness of) are a narrative mechanic that applies in both modes — not a player-facing setting.

**GM cheating is a player-controlled toggle.** Default on, calibrated to tone. When disabled, all dice results are honored absolutely in both directions at all moments, including climactic ones. UI shows a plain-language warning when the player turns it off.

**Session type is a configuration parameter.** Shapes pacing expectations for the GM. Short adventure / Campaign / Open-ended. UI surfaces a gentle note that campaign play benefits from the paid tier given the free tier turn cap.

**Tone is a front-end dropdown, not free text.** Gritty / Balanced / Forgiving / Danger-free. Passed directly to the AI.

---

### Branching Mode — Key Decisions

**Tone is not a configuration parameter.** It lives in world summary alongside genre, setting, and narrative register. Free text lets players describe the story they actually want without imposing a vocabulary on them.

**Freeform input is a first-class option, equal to branch selection.** Branch cards and freeform text field are presented with equal prominence. Branch options exist to inspire and indicate what's possible — not to confine. Players who type freeform every turn are using the mode correctly.

**Branch frequency uses experiential language.** Three options: Interactive / Balanced / Immersive. No granular mechanical options (word counts, beat counts). UI note on the Interactive option explains that the narrator may hold branches briefly during climactic moments — this is intentional behavior, not a bug.

**Setup uses the hybrid model.** Structured form followed by a single lightweight confirmation pass from the story architect. Catches setup problems before they infect the story; establishes the architect's presence from the first moment.

**Length preference is a configuration parameter.** Short story / Novella / Novel. Shapes how quickly the story architect advances through pacing stages.

**Story seeds and supporting cast are configuration fields.** Players can contribute dramatic hooks, premises, allies, and antagonists at setup time. Both optional.

---

### Writing Mode — Key Decisions

**Persona selection determines relationship type.** No explicit Mentor / Writing Partner submode labels. The player selects a persona from a gallery divided into Guides and Peers. The category is communicated through persona descriptions, not submode taxonomy.

**Guides: Chiron, Merlin, Vidura.** Developmental mentors. Primary orientation is teaching through making — craft goals, generative exercises, targeted feedback. Manuscript repair is not their function. Bringing existing prose to a Guide is a diagnostic path only ("what should we work on?"), not a repair path.

**Peers: Odin, Athena, Thoth.** Creative collaborators. Primary orientation is making alongside the user. Teaching available but not default — a Peer speaks up only when something is genuinely holding the work back, or when asked. Preference for generative work over manuscript repair, but will work on an existing manuscript when the project calls for it.

**Roster is intentionally small.** Three Guides, three Peers. Enough meaningful choice without overwhelming players or creating excessive implementation burden. Roster can expand once the persona system is well-designed and functional.

**Future consideration — persona expansion across modes.** The persona layer is a strong candidate for RPG and Branching modes in a future version. Should not be architected against in v1.

**Setup uses the hybrid model.** Structured form followed by the persona opening with a brief confirmation and 1–2 clarifying questions specific to their orientation. Work does not begin until the working relationship and immediate goal are clear.

---

### OOC Communication — All Modes

Full protocol in each mode's prompt file. The UI provides an explicit OOC button that prepends the [OOC] marker automatically. Players may also type it manually.

---

## Item 7 — Contradiction Checker Architecture Is Decided

**v1 approach:** Lightweight model-assisted — a small, fast LLM call with a focused prompt. Single code path for both tiers; depth and scope vary by tier, not mechanism.

**What it checks:**

| Tier | Scope |
|------|-------|
| **Free** | Recent context (last ~10 turns) + Story Bible locked facts only |
| **Paid** | Full retrieval history + complete Story Bible |

Both tiers catch continuity violations including but not limited to: dead characters acting, items never acquired, location/name drift, POV/tense shift, violated locked facts. The checker prompt is designed to surface any narrative inconsistency against established Story Bible canon and recent context — the listed categories are common failure modes, not an exhaustive definition. Paid tier additionally catches contradictions against events further back than the immediate context window.

**Pipeline position:** Parallel sync. The checker fires the moment context is assembled — concurrent with the Writer pass, not after it. Output is gated on both completing before anything ships to the user. In the common case, the checker (small/fast model) finishes before or near the Writer, and the latency hit approaches zero.

Nothing is delivered to the user until the checker clears. Contradictions are caught before they're read, not flagged after the fact.

**Rationale for synchronous gate:** In a narrative product, continuity *is* the deliverable. A contradiction the user reads and then gets corrected on the next turn has already done its damage. Async flagging is acceptable in productivity tools; it is not acceptable here.

---

## Item 8 — Per-Turn Cost Model Is Estimated

### Story Bible Size at Steady State

The Story Bible is split into static (written at creation, requires Sojourner confirmation to change), dynamic (Extractor-maintained), and provisional (proposed but not yet ratified) partitions. The Events Ledger uses a tiered inclusion policy — full record stored in SQLite, active context loads only recent and high-significance events. Nothing is ever deleted.

| Scenario | Story Bible tokens (active context) |
|---|---|
| Minimal | ~5,000 |
| Moderate | ~12,000 |
| Complex | ~22,000 |

The Events Ledger is the primary growth driver. Without the tiered inclusion policy it would dominate the Bible's footprint within a few chapters. The policy bounds the active context while preserving the full record for retrieval and deep contradiction checking.

**Known dependency:** The contradiction checker sees the active context window, not the full SQLite ledger. Deep historical contradictions not flagged high-significance can slip past the free tier checker. Mitigation is disciplined significance flagging and the paid tier's full retrieval scope.

---

### Five-Pass Context Size Per Turn

Context splits into a **stable prefix** (cacheable, paid once per session) and a **volatile suffix** (paid every pass, every turn).

**Stable prefix:**

| Component | Tokens |
|---|---|
| System prompt + mode contract | ~500 |
| Story Bible (tiered inclusion) | 5k / 12k / 22k |
| Rolling summary | ~500 / 800 / 1,200 |
| **Total** | ~6k / 13.3k / 23.7k |

**Volatile suffix (consistent across scenarios):**

| Component | Tokens |
|---|---|
| Recent turns verbatim (~10 turns) | ~5,000 |
| Current input + classified intent | ~150 |
| **Total** | ~5,150 |

**Pass-forward additions (not cached):** ~2,000–2,500 tokens total across pipeline.

**Gross input tokens per turn — all passes, before caching:**
Note: The per-turn cost estimates and pricing margins in the section below were calculated against the original (understated) token totals and should be re-examined against these corrected numbers before being used as a reliable cost model.
| Scenario | Minimal | Moderate | Complex |
|---|---|---|---|
| Free tier (4 passes) | ~47,000 | ~76,000 | ~118,000 |
| Paid tier (5 passes) | ~58,000 | ~95,000 | ~147,000 |

These numbers are materially reduced by caching. The stable prefix — which dominates gross input — is paid at full price once per session and at ~10% for each subsequent pass within a turn.

---

### Cache Hit Rates

**Within a single turn:** ~100% guaranteed. All five passes share the same warm cache. This is the structural advantage of the parallel sync architecture — correct for latency and correct for cost simultaneously.

**Between turns within a session:**

| User behavior | Anthropic default (5 min TTL) | Extended TTL (1 hr) |
|---|---|---|
| Focused (1–3 min gaps) | ~90% | ~99% |
| Normal (5–10 min gaps) | ~40% | ~95% |
| Casual (15–30 min gaps) | ~5% | ~80% |
| Long pause (1+ hr) | 0% | ~10% |

**Blended hit rate, 20-turn session:**

| TTL setting | Blended hit rate | Effective stable prefix cost as % of gross |
|---|---|---|
| Default (5 min) | ~45% | ~55% |
| Extended (1 hr) | ~88% | ~18% |
| Cold start (session open) | 0% | 100% |

**Extended TTL must be a default architectural choice wherever the provider supports it.** On a moderate story, default TTL roughly doubles per-turn cost compared to extended TTL. The difference is not marginal.

**Session resumption:** Cold start on every new session is unavoidable regardless of provider. First turn always pays full input price on the stable prefix. Design this as the expected baseline, not an exception.

---

### Effective Per-Turn Cost — BYOK and Hosted Tiers

**Price assumptions (representative mid-2025 rates, verify before building cost models):**

| Model tier | Use | Input | Cache read | Output |
|---|---|---|---|---|
| Large/quality | Writer pass | $3/MTok | $0.30/MTok | $15/MTok |
| Small/fast | All other passes | $0.60/MTok | $0.06/MTok | $2/MTok |

**Hosted tier uses OpenRouter.** OR passes provider costs through without markup; a 5.5% fee applies to credit purchases. All hosted model costs are therefore 5.5% above raw provider rates.

**Total per-turn cost (extended TTL, moderate scenario):**

| Tier | Minimal | Moderate | Complex |
|---|---|---|---|
| Free | ~$0.025 | ~$0.035 | ~$0.05 |
| Paid | ~$0.05 | ~$0.07 | ~$0.09 |

**BYOK user burn rate:** At $0.07/turn on a moderate story, a user doing 20–30 turns per session spends $1.40–$2.10 per session in API costs. Heavy users running long complex stories spend $3–5 per session. Users routing through OR pay an additional 5% on usage beyond the free monthly request allowance. Users connecting directly to their provider pay raw provider rates.

---

### Break-Even Usage — Paid Subscription Tier

**Infrastructure cost per user per month (hosted):**

| Scale | Compute | ChromaDB | Other | Total |
|---|---|---|---|---|
| 100 users | ~$0.50 | ~$0.13 | ~$0.07 | ~$0.70 |
| 1,000 users | ~$0.12 | ~$0.03 | ~$0.07 | ~$0.22 |
| 5,000 users | ~$0.06 | ~$0.02 | ~$0.05 | ~$0.13 |

Model cost is the primary variable. Infrastructure is not the problem.

**Committed pricing structure:**

| Tier | Price | Turn cap | Model cost | Infra | Margin |
|---|---|---|---|---|---|
| Free | $0 | 50 turns/month | ~$1.75 | ~$0.20 | Platform absorbs |
| Hosted paid | $19.99 | 200 turns/month | ~$14.77 | ~$0.23 | ~$5.00/user |
| BYOK | $49 one-time | Unlimited | User pays | ~$0.20/month | Infrastructure covered ~2 years |

**Free tier rationale:** 50 turns is enough to experience the product across 2–3 short sessions. Not enough to use it as a permanent free ride.

**Hosted paid rationale:** 200-turn hard cap at $19.99 yields ~$5.00/user/month margin at 1,000 users. Thin but real, scaling favorably with volume. The hosted tier is a visibility and accessibility play, not the primary margin center.

**BYOK rationale:** $49 covers ~2 years of infrastructure overhead. At $0.07/turn in API costs, a user doing 200 turns/month pays ~$14/month to their provider regardless. The $49 flat fee covers only infrastructure — that framing makes the value obvious.

**BYOK expansion model:** Base purchase includes all bug fixes, UI improvements, and pipeline enhancements, forever. Major new feature categories are sold as optional expansions at reduced cost ($15–25). Expansions must be unambiguously new capability — bug fixes are always free.

**Note on deep memory:** Vector retrieval (ChromaDB) is core to v1, not an expansion. Although it lands later in the pre-v1 construction sequence, it is part of the first release-capable product scope.

---

## Item 9 — Construction Order Is Defined

The following issues define the pre-v1 internal construction sequence.

**Issues 1–11 (foundation and core services) — fully defined, construction-ready:**

1. Repo skeleton, config, linting, test harness, CI scaffold
2. Core models: Story / Arc / Chapter / Node / Turn — including World/Character State schema and mode-specific session state (RPG: HP, dice state, active quests; Branching: pacing stage, plot thread tracker; Writing: beat constraints, version history pointers)
3. SQLite persistence and CRUD services for all core models
4. Story Bible schema and service — static / dynamic / provisional partitions, Events Ledger with tiered inclusion policy, Locked/Forbidden Facts as first-class entries
5a. Rules Package schema and data model — package metadata, rule chunk model, structured mechanical entities, source tracking, precedence/override model
5b. Rules Package ingestion pipeline — ingestion tooling from approved source materials, package publication flow, d20 v1 ingestion path; delivers one ingested, published, and queryable curated d20 Rules Package in the development environment
6. Rolling summary service — compression trigger, update policy
7. Intent classification — lightweight model call; classifies input before context assembly
8. Context builder — assembles stable prefix once per turn; volatile suffix separately; pass-forward additions tracked; retrieves rule slices on demand by mode
9. Minimal Writer path — single-pass, no orchestration, no pipeline yet; proves the Writer call works end to end
10. Extractor classification policy — proposes canon updates, does not write directly; routes to locked / soft / transient / unresolved
11. Lightweight contradiction checker — parallel sync, small/fast model, release-minimum scope

**Issues 12–21 (pipeline, modes, release integration) — directionally correct, provisional until Issues 1–11 near completion:**

12. Full five-pass pipeline orchestration — Planner → Writer → Extractor → Contradiction → Safety; parallel sync for Contradiction; output gated on both Writer and Contradiction completing
13. Tier routing logic — free vs. paid vs. BYOK; pipeline depth, turn cap enforcement; tested as architectural invariant
14. BYOK API key management — key storage, provider routing, OR integration
15. RPG mode integration — prompt contract loaded as versioned artifact, d20 adjudication against ingested Rules Package, dice handling modes wired (Player rolls / AI rolls), GM cheating toggle, pre-play sequence enforced, character sheet as first-class persistent object
16. Branching mode integration — prompt contract loaded, pacing stage tracking calibrated to length preference, branch generation call, freeform input as first-class option
17. Writing mode integration — prompt contract loaded, persona-based model (three Guide personas: Chiron, Merlin, Vidura; three Peer personas: Odin, Athena, Thoth), persona behavioral briefs and prompt injections wired, beat constraints
18. ChromaDB integration — vector retrieval service, collection schema per story and rules corpus, semantic query wired into context builder
19. Frontend skeleton — story creation, mode selection, turn submission, output display; React vs. Svelte resolved before this issue
20. BYOK user-facing configuration — API key entry, provider selection, burn rate communication
21. Full end-to-end integration test — all three modes, all three tiers, first release-capable MVP spine demo confirmed working

Issues 12–21 will be formally written with acceptance criteria as Issues 1–11 near completion. Construction order beyond Issue 11 is directionally correct but detail-level definitions should wait until the foundation is stable.

---

## Item 10 — Each Early Issue Has Boundaries and Acceptance Criteria

---

**Issue 1 — Repo Skeleton**
- *Goal:* Establish the project structure, tooling, and CI scaffold before any application code is written
- *In scope:* Directory structure, pyproject.toml, Black + Ruff + mypy configuration, pytest harness, GitHub Actions CI pipeline running format/lint/type/test checks, branch protection rules on main, PR template with Architecture Notes section, detect-secrets pre-commit hook
- *Out of scope:* Any application logic, models, routes, or services
- *Deliverables:* Passing CI on an empty test suite; PR template in place; branch protection active
- *Acceptance criteria:* CI passes on a trivial commit; direct commits to main are rejected; PR template appears on all new PRs
- *Test requirements:* Trivial smoke test confirming pytest runs; no application tests yet

---

**Issue 2 — Core Models**
- *Goal:* Define the backbone data objects the entire system depends on
- *In scope:* Story, Arc, Chapter, Node, Turn as Pydantic models; World/Character State schema (static and dynamic partitions); mode-specific session state schemas (RPG, Branching, Writing); field definitions and type annotations for all. RPG character sheet must be modeled as a first-class persistent object with structured fields (class, stats, skills, equipment, current and maximum HP, spell slots, etc.) and support for mutable values — not as a blob or freeform field on session state.
- *Out of scope:* SQLite persistence — Issue 3; Story Bible schema — Issue 4; Rules Package schema — Issue 5a; any routes or services
- *Deliverables:* All models defined with full type annotations; unit tests confirming instantiation and field validation
- *Acceptance criteria:* Models instantiate correctly; invalid field types are rejected; mode-specific session state is cleanly separated from core Node schema; RPG character sheet is a distinct structured model, not a freeform field
- *Test requirements:* Unit tests for each model; edge cases for optional fields; character sheet field validation tests

---

**Issue 3 — SQLite Persistence and CRUD**
- *Goal:* Persist and retrieve all core models reliably
- *In scope:* SQLite schema for all Issue 2 models; CRUD services for Story, Arc, Chapter, Node, Turn, World/Character State; migration tooling (Alembic); basic integrity constraints
- *Out of scope:* Story Bible persistence — Issue 4; Rules Package persistence — Issue 5; any API routes; any business logic
- *Deliverables:* Working CRUD for all core models; migration baseline; unit tests confirming round-trip persistence
- *Acceptance criteria:* All models persist and retrieve correctly; foreign key relationships enforced; no data loss on round-trip
- *Test requirements:* Round-trip tests for each model; referential integrity tests; concurrent write safety baseline

---

**Issue 4 — Story Bible Schema and Service**
- *Goal:* Implement the Story Bible as a structured, partitioned, append-safe canon store
- *In scope:* Static / dynamic / provisional partition schema; Events Ledger with tiered inclusion policy (recent N + high-significance flag; start N at 15, tune with testing); Locked Facts and Forbidden Facts as first-class entries; Relationship Ledger; Character entries with role tagging and static/dynamic field separation; Story Bible CRUD service; Extractor proposal staging area (not Extractor logic — Issue 9); significance flagging criteria to be defined during this issue
- *Out of scope:* Rolling summary — Issue 6; Extractor classification logic — Issue 10; any prompt construction
- *Deliverables:* Story Bible schema in SQLite; service for reading active context window per tiered inclusion policy; unit tests
- *Acceptance criteria:* Static partition requires explicit confirmation to update; Events Ledger loads correct subset per tiered inclusion policy; Locked Facts are queryable as a distinct set; provisional entries are staged separately from ratified canon
- *Test requirements:* Tiered inclusion policy unit tests; partition isolation tests; locked fact enforcement tests; provisional staging tests

---

**Issue 5a — Rules Package Schema and Data Model**
- *Goal:* Define the data model for the external mechanical-canon subsystem RPG mode depends on
- *In scope:* Rules Package schema; rule chunk model; structured mechanical entity model (conditions, actions, spells/items/stat blocks as available in source); source tracking; precedence/override model; unit tests
- *Out of scope:* Ingestion pipeline and corpus delivery — Issue 5b; live RPG adjudication wiring — Issue 15; full semantic retrieval service integration — Issue 18; branch/writing canon-pack extensions — deferred
- *Deliverables:* Rules Package schema and data model with full type annotations; unit tests confirming instantiation, field validation, and override precedence
- *Acceptance criteria:* Rules Package is cleanly separated from Story Bible and session state; override model layers without mutating source records; source provenance fields are present and enforced per chunk/entity
- *Test requirements:* Schema separation tests; provenance field tests; override precedence tests; instantiation and field validation tests

---

**Issue 5b — Rules Package Ingestion Pipeline**
- *Goal:* Build the ingestion tooling and deliver a queryable d20 Rules Package in the development environment
- *In scope:* Ingestion pipeline from approved source materials into SQL + vector index; package publication flow; d20 v1 ingestion path; at least one ingested, published, and queryable curated d20 Rules Package in non-production seed/dev form; unit tests
- *Out of scope:* Live RPG adjudication wiring — Issue 15; full semantic retrieval service integration — Issue 18; branch/writing canon-pack extensions — deferred
- *Deliverables:* Working ingestion tool/service; published and queryable d20 Rules Package in the development environment; unit tests
- *Acceptance criteria:* Ingested d20 package can be queried by subsystem and semantic lookup; overrides can be layered without mutating source records; source provenance is preserved per chunk/entity; ingestion is repeatable from approved source materials
- *Test requirements:* Ingestion round-trip tests; provenance tests; representative query tests across at least combat, conditions, and one additional subsystem

---

**Issue 6 — Rolling Summary Service**
- *Goal:* Maintain a compressed narrative history that fits within the stable prefix budget
- *In scope:* Rolling summary schema; compression trigger (every N turns — start at 10, tune with testing); summary generation call (lightweight model); summary persistence; service for retrieving current summary
- *Out of scope:* Context builder integration — Issue 8; N tuning is a known unknown, 10 is the starting value
- *Deliverables:* Rolling summary service; compression trigger logic; unit tests
- *Acceptance criteria:* Summary updates correctly at trigger threshold; previous summaries preserved in SQLite; summary retrieval returns current version
- *Test requirements:* Trigger threshold tests; compression output tests; version history tests

---

**Issue 7 — Intent Classification**
- *Goal:* Classify player input before context is assembled — intent classification precedes context building by design
- *In scope:* Intent taxonomy (in-character action / dialogue / author instruction / branch choice / beat milestone / rewind / lore question / OOC); lightweight model call with focused classification prompt; classification result schema passed to context builder
- *Out of scope:* Context builder — Issue 8; any mode-specific handling of classified intent
- *Deliverables:* Intent classifier returning typed classification result; unit tests across intent types
- *Acceptance criteria:* All defined intent types are classifiable including ambiguous and creative inputs; OOC input reliably detected; classification result is a typed object, not a raw string; misclassification rate acceptable on edge case test set
- *Test requirements:* One test per intent type; ambiguous and creative input edge cases; OOC detection tests; edge case test set defined during this issue

---

**Issue 8 — Context Builder**
- *Goal:* Assemble the full context payload for each pipeline pass, with stable prefix and volatile suffix cleanly separated
- *In scope:* Stable prefix assembly (system prompt + mode contract + Story Bible active context + rolling summary); volatile suffix assembly (recent turns + current input + classified intent); pass-forward addition tracking; assembly called once per turn, shared across passes
- *Out of scope:* Pipeline orchestration — Issue 11; actual pipeline calls — Issues 9–11
- *Deliverables:* Context builder service returning stable prefix and volatile suffix as distinct objects; unit tests confirming assembly order and content
- *Acceptance criteria:* Stable prefix always assembled in correct order; Story Bible and rolling summary never mixed with prose history in stable prefix; volatile suffix contains only recent turns and current input; assembly is called once per turn, never per pass
- *Test requirements:* Assembly order tests; partition separation tests; content correctness tests for each scenario (minimal / moderate / complex Story Bible)

---

**Issue 9 — Minimal Writer Path**
- *Goal:* Prove end-to-end that a player input goes in and coherent prose comes out — single pass, no orchestration
- *In scope:* Single Writer LLM call using assembled context; response parsing; Turn saved to SQLite; no Planner, no Extractor, no Contradiction, no Safety yet
- *Out of scope:* Full pipeline orchestration — Issue 11; mode-specific prompt contracts — Issues 15–17; this is a proof-of-life call, not a production path
- *Deliverables:* Working Writer call with context builder output as input; Turn persistence; integration test confirming round-trip
- *Acceptance criteria:* Input goes in, prose comes out, Turn is saved; context assembly confirmed correct before the call; response is parseable
- *Test requirements:* Integration test: full round-trip from input to saved Turn; context content verification before call

---

**Issue 10 — Extractor Classification Policy**
- *Goal:* Implement the Extractor pass per Item 2, Principle #5 (proposes updates, never writes canon directly)
- *In scope:* Extractor LLM call on Writer output; classification of proposed updates (locked / soft / transient / unresolved); staging area for proposed updates pending ratification; service for surfacing locked-fact proposals to Sojourner for confirmation; auto-commit logic for soft and transient facts
- *Out of scope:* Pipeline orchestration wiring — Issue 12; UI for Sojourner confirmation — deferred
- *Deliverables:* Working Extractor pass; classification routing; staging area persistence; unit tests
- *Acceptance criteria:* Extractor never writes directly to canon; locked fact proposals are staged and require confirmation; soft and transient facts auto-commit with correct flags; unresolved threads queued, not committed
- *Test requirements:* Classification routing tests for each category; direct-write prevention test (architectural invariant); auto-commit behavior tests

---

**Issue 11 — Lightweight Contradiction Checker**
- *Goal:* Implement the contradiction checker per the architecture defined in Item 7 (parallel sync gate, small/fast model)
- *In scope:* Contradiction checker LLM call with focused prompt; parallel execution alongside Writer pass; free tier scope (recent context + locked facts); output gate logic; contradiction result schema
- *Out of scope:* Paid tier full retrieval scope — deferred until ChromaDB is integrated (Issue 18); pipeline orchestration wiring — Issue 12
- *Deliverables:* Working contradiction checker; parallel execution proof; gate logic; unit tests
- *Acceptance criteria:* Checker fires on context assembly, not after Writer output; output is gated — nothing ships until checker clears; free tier scope correctly limited to recent context + locked facts; contradictions caught and reported before delivery
- *Test requirements:* Parallel execution tests; gate behavior tests; scope boundary tests (free tier vs. paid tier); known contradiction detection tests using representative examples (dead character acting, item never acquired, locked fact violated) — these are test anchors, not the complete set of detectable violations

---

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
- Claude Code opens all PRs with a structured description including: what was built, how it satisfies each acceptance criterion, test coverage summary, and an Architecture Notes section (either "No drift from design principles" or explicit description of any deviation and rationale)
- No PR merges without Codex review passing
- No PR merges with failing CI
- PR scope must match issue scope — scope creep is a review failure

**Commit message format — conventional commits:**
`type(scope): description`
Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
Example: `feat(story-bible): implement tiered inclusion policy for events ledger`

**Architecture drift flag:**
Every PR description includes an Architecture Notes section. If Claude Code's implementation deviates from any principle in the Construction Readiness Document, it must describe the deviation, explain why it was necessary, and propose resolution. Silent resolution of architecture questions is a review failure regardless of whether the code works.

---

## Item 12 — CI Gates as Quality Handoff Contract

**Standard gates (active from Issue 1):**

| Gate | Tool | Notes |
|---|---|---|
| Formatting | Black | pyproject.toml; zero tolerance |
| Linting | Ruff | pyproject.toml; zero tolerance |
| Type checking | mypy | Strict mode; zero tolerance |
| Unit tests | pytest | Minimum 80% coverage on new code |
| Dependency scanning | pip-audit | Block on known vulnerabilities |
| Secret scanning | detect-secrets | Pre-commit hook; block on any secret pattern |

**Architectural invariant tests (added progressively as each component lands):**

| Invariant | Added at issue |
|---|---|
| Story Bible and prose history stored in separate tables, never commingled | Issue 4 |
| Prompt assembly follows stable-prefix-first order; assembled once per turn, never per pass | Issue 8 |
| App starts without error — uvicorn startup smoke test | Issue 9 |
| Extractor cannot write directly to canon without classification step | Issue 10 |
| Output never delivered until contradiction checker clears | Issue 11 |
| Free tier never receives full five-pass pipeline | Issue 12 |
| Tier routing correctly enforces turn caps | Issue 13 |

Codex receives only PRs that have already passed all active CI gates. Review effort is spent on design, logic, and security — not formatting failures or type errors.

---

## Item 13 — Documentation Standards as Architectural Drift Detection

**Where docs live:**

| Doc type | Location |
|---|---|
| Architecture docs | `/docs/architecture/` |
| Mode prompt contracts | `/docs/prompts/` (versioned .md files) |
| Decision logs | `/docs/decisions/` (ADR format) |
| Construction readiness doc | `/docs/architecture/construction_readiness.md` |
| Design doc | `/docs/architecture/design.md` |
| Known unknowns | `/docs/architecture/known_unknowns.md` |
| Spine demo definition | `/docs/architecture/spine_demo.md` |

**Canonical vs. provisional:**
Canonical docs are the Construction Readiness Document, the Design Document, and the mode prompt contracts. Any file marked `DRAFT` in both its filename and document header is provisional. Provisional docs may be referenced but not relied upon as behavioral spec.

**Update rule:**
Any PR that changes behavior described in a canonical doc requires a corresponding doc update in the same PR. This is a Codex review criterion, not a suggestion. If the code has changed and the doc has not, the PR is not complete.

**Decision log format (ADR):**
When a significant implementation decision is made during construction — anything that resolves a Known Unknown, deviates from design intent, or makes a load-bearing choice not covered by existing docs — Claude Code writes a short ADR in `/docs/decisions/` in the same PR. Format: decision title / context / decision made / rationale / consequences.

---

## Item 14 — Business-Model-Sensitive Constraints for Builders

The following are architectural invariants, not conventions. Codex reviews against them explicitly.

1. **Free tier turn cap is 50/month** — enforced at the API layer, not the UI. The UI communicates it gracefully; the API enforces it unconditionally.

2. **Free tier pipeline is lightweight Planner + Writer + lightweight Contradiction + Safety** — free tier never receives the full five-pass pipeline (no Extractor) regardless of story complexity.

3. **Paid tier runs the full five-pass pipeline** — Planner → Writer → Extractor → Contradiction → Safety. Paid tier contradiction checker scope includes full Story Bible, not just recent context.

4. **BYOK is a first-class path** — not a fallback, not an edge case. All pipeline features must work identically under BYOK. Users may route through OpenRouter or connect directly to their provider; both paths must be tested.

5. **Extended TTL caching must be enabled by default** wherever the provider supports it. Default TTL is not acceptable. This is an economic requirement, not a preference.

6. **Stable prompt prefix assembly rule** — see Item 2, Principle #6. Any implementation that rebuilds the stable prefix per pass is an architectural violation.

7. **Free tier must preserve basic continuity dignity** — see Item 7 for checker scope and architecture. Silent failure on continuity is not acceptable at any tier.

8. **Tier routing logic is tested as an architectural invariant** — dedicated unit tests must confirm that each tier receives the correct pipeline depth, turn cap, and contradiction checker scope.

---

## Item 15 — Known Unknowns Are Listed Explicitly

**Resolved before construction — no longer unknowns:**

| Item | Decision |
|---|---|
| Vector DB | ChromaDB, self-hosted from day one |
| Contradiction checker approach | Lightweight model-assisted, parallel sync |
| Intent classifier approach | Lightweight model call |
| Business model and pricing | Committed — see Item 8 |
| Story Bible schema | Committed — see Items 4–5 |
| Mode prompt contracts | Written — see Item 6 and `/docs/prompts/` |
| BYOK expansion model | Committed — see Item 8 |
| Writing mode structure | Persona-based — Guides (Chiron, Merlin, Vidura) and Peers (Odin, Athena, Thoth); no explicit submode labels |
| RPG dice handling | Two modes: Player rolls / AI rolls; hidden rolls are a narrative mechanic, not a player setting |

**Acceptable to resolve during construction:**

| Unknown | When to resolve |
|---|---|
| React or Svelte for the initial frontend | Before Issue 19 |
| Exact ChromaDB collection schema for story/rules vectors | Before Issue 18 |
| Exact FastAPI route shapes | Before Issue 18 |
| Rolling summary compression trigger value (N turns) | During Issue 6; start at 10, tune with testing |
| Events Ledger tiered inclusion N value (recent events to load) | During Issue 4; start at 15, tune with testing |
| Significance flagging criteria for Events Ledger | During Issue 4 |
| Session resumption UX on cache miss | During Issue 14 |
| Guide and Peer persona behavioral implementation details (six personas: Chiron, Merlin, Vidura, Odin, Athena, Thoth) | During Issue 17 |

---

## Item 16 — Minimal End-to-End Slice Is Defined

**Primary spine demo — Branching mode (proves the machine lives):**

1. User creates a new Story with a minimal Story Bible (setting, one protagonist, one dramatic hook)
2. Selects Branching mode with default configuration
3. Backend classifies intent (branch choice)
4. Context is assembled from new/empty state — stable prefix confirmed correct, pacing stage initialized to Setup
5. Writer generates a narrative beat; contradiction checker runs in parallel
6. Output is gated until checker clears; prose is delivered
7. Branch generation call produces 3–5 action options alongside a freeform text field as equal options
8. Turn is saved to SQLite; Node is created with pacing stage metadata
9. Story Bible and rolling summary update path runs — Extractor proposes; no locked facts to confirm on first turn
10. User selects a branch or types freeform input; second turn submitted; correct prior state and pacing stage load; response is coherent with first turn and advances pacing naturally

This is the proof of life. All three modes extend from this spine.

**RPG mode follow-on slice:** Same flow, but gated on the first d20 Rules Package already existing. Pre-play sequence runs first: world setup confirmed, character sheet complete. Step 3 retrieves the relevant d20 Rules Package slices. If `dice_mode = AI rolls`, step 6 narrates the consequence of the roll result with the roll value shown to the player. If `dice_mode = Player rolls`, the GM announces the required check and modifiers and waits for the player to report their roll before narrating the outcome. Hidden rolls for NPC/enemy checks the player has no in-world awareness of are resolved privately in both modes.

**Rules-enabled MVP dependency:** RPG mode is not MVP-ready until one curated d20 Rules Package has been ingested, published, and made queryable through the Context Builder. Branching and Writing modes may ignore this dependency in v1 unless a canon-pack use case is explicitly being tested.

**Writing mode follow-on slice:** Same flow, but the player has selected a Guide persona (e.g., Chiron). The Guide reads the completed setup form, opens with a brief confirmation and a craft-focused clarifying question, and then invites the user to write toward a specific craft goal. Step 6 returns targeted feedback aimed at that goal — not a manuscript repair response. The Guide never begins by receiving existing prose for correction.

---

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

---

*Construction Handoff Checklist — all 17 items complete. March 2026.*
