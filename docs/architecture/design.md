# Afterworlds: Synthesized Design Document (v9)

*Revised May 2026 to replace the five-pass pipeline framing with the safety envelope model. Safety is no longer modeled as a mandatory fifth narrative pass after Contradiction. The core narrative pipeline is Planner → Writer → Extractor → Contradiction. A safety envelope wraps the generation core: input preflight before Planner/Writer when orchestration policy requires it, and conditional output audit after Writer and before Extractor/Contradiction when provider or risk policy requires it. See Section 4 and the Construction Readiness Document for full architecture detail.*

-–

## Core Philosophy

One shared narrative engine. Three UX contracts on top of it.

The platform is the **Sojourn Story State Machine** — not a chatbot wearing a cape.

-–

## 1. Terminology

Two concepts that must stay distinct:

- **Turn** — one interaction unit (one user input + one AI response)

- **Node** — one persisted story beat / state transition in the story graph

These often correspond 1:1, but not always. In branching scenarios, a node may encompass multiple turns, or represent an alternative path never actually traversed. Collapsing them is conceptual debt. Keep them separate throughout the codebase and data model.

-–

## 2. Data Architecture

### Story Object Hierarchy

```
Story

&#x20;└── Arc

&#x20;     └── Chapter

&#x20;          └── Node (story beat / state transition)

&#x20;               └── Turn (interaction unit)
```

### Node Schema

Every persisted story beat is a Node:

| Field | Description |

|—|—|

| Node ID | Unique identifier |

| Content | Generated prose or dialogue |

| State Delta | World mutations caused by this beat (e.g., `gold -50`, `king\_trust: hostile → neutral`) |

| Branching Logic | Pointers to next possible nodes |

| Intent Type | Action / Dialogue / Author instruction / Branch choice / Milestone |

| Metadata | POV, location, mood, tense, timestamp |

### The Story Bible

Structured canon — not prose. A *contract* the AI is bound to honor.

- Setting summary and world rules

- Cast list: traits, goals, secrets, relationship links

- Timeline of locked events

- Unresolved plot threads

- Forbidden facts (cannot happen)

- Locked facts (cannot be undone)

The Story Bible is read before every generation call and updated — carefully — after, via the Extractor. See Section 4 for update policy.

### The Rules Package *(RPG-first, reusable as Canon Package for Branched and Writing modes)*

Rules do **not** live inside the Story Bible. The Story Bible governs fictional canon; the Rules Package governs mechanical canon. They must remain separate.

A canon pack is an external, queryable lore corpus for non-RPG continuity needs (for example: franchise canon, adaptation references, or fan-fiction setting material). Unlike a Rules Package, it contains narrative reference material rather than mechanical adjudication rules.

A Rules Package is a versioned, modular, externally stored corpus containing:

- Core rule text and subsystem chunks

- Structured mechanical entities (conditions, actions, spells, items, stat blocks, etc.)

- Rule metadata (system, module, source, precedence, enabled/disabled status)

- House-rule and setting-specific overrides

- Retrieval indexes for play-time lookup

**Ingestion model:** rulebooks, licensed/open materials, or user-supplied documents are processed through an offline/admin ingestion pipeline into a dedicated Rules Corpus (SQL + vector index). The live GM model does **not** build this corpus during play and does **not** receive whole rulebooks in prompt context.

**Play-time model:** the Context Builder retrieves only the rules relevant to the current turn (for example: attack resolution, a spell entry, an active condition, a monster trait). Deterministic calculations should move to code/services where practical; the model narrates and adjudicates from the retrieved packet rather than “remembering” the system wholesale.

**v1 assumption:** d20 is the first curated Rules Package. Future systems (GURPS, Shadowrun, etc.) slot in as additional Rules Packages using the same ingestion and retrieval path.

The same ingestion pattern can later support lighter-weight canon packs for Branching and Writing modes (for example: franchise lore packs, fan-fiction canon packets, or setting bibles larger than the normal Story Bible should carry).

-–

## 3. Memory Architecture

Six layers, each with a distinct role:

| Layer | Contents | Inclusion |

|—|—|—|

| Immediate | Last ~10 turns verbatim | Always |

| Rolling Summary | Compressed narrative, auto-updated every N turns | Always |

| Story Bible | Structured canon | Always |

| Rules Package | Retrieved mechanical canon or external canon-pack context | On demand by mode |

| Retrieval Memory | Vector DB of past scenes, pulled by semantic relevance | On demand |

| Contradiction Checker | Pre-output scan for continuity violations | Every turn; core checker always on, retrieval depth may expand with entitlement or user-configured cost guardrails |

### Contradiction Checker — What It Catches

- Dead characters speaking or acting

- Items in inventory never acquired

- Location or name drift

- POV or tense shift mid-scene

- Violated locked facts

This is what separates “better memory” as a marketing claim from “better memory” as a product reality.

Continuity checking is part of the product, not a premium ornament. Afterworlds does not ship a degraded access path that removes canon maintenance or contradiction prevention in order to manufacture an upsell. All real product access paths — hosted subscription, starter access if offered, and BYOK — run the same Sojourn orchestration path, including the core narrative pipeline and the safety envelope.

Commercial differences may later affect usage entitlements, retrieval budgets, or service allowances, but not whether the core continuity machinery or responsible guardrails exist.

-–

## 4. The Narrative Orchestration Pipeline

Every input passes through the Sojourn orchestration path. Mode, access path, and task complexity may influence model class, retrieval depth, and billing behavior, but not whether the core narrative pipeline and safety envelope are present.

The core narrative pipeline is: **Planner → Writer → Extractor → Contradiction**

The safety envelope wraps the generation core:

- **Input Safety Preflight** — runs before Planner/Writer when orchestration policy requires it (e.g., provider not on the safety whitelist, or explicit risk signal)
- **Provider Refusal Handling** — during any provider-backed pass; treated as a typed pass failure, not a Safety verdict
- **Conditional Output Safety Audit** — runs after Writer and before Extractor/Contradiction when provider or risk policy requires it

The practical orchestration shape is:

```
[Input Safety Preflight, when required]
Planner
Writer
[Output Safety Audit, when required]
Extractor
Contradiction
Deliver / Persist
```

Safety is a guardrail envelope, not a mandatory terminal narrative pass. If a Sojourner request violates policy, the system stops before generation starts. If Writer output violates policy, the system stops before Extractor and Contradiction — the Extractor must not extract canon from prose that will never be delivered.

### Step 1 — Intent Classification

Classify *before* building context:

- In-character action

- Dialogue

- Author instruction

- Branch choice

- Beat milestone set

- Rewind / retry / regenerate

- Lore question

### Step 2 — Context Assembly

Stack in priority order:

```
\[System prompt + mode contract]

\[Story Bible (includes cast ledger, world state)]

\[Rolling summary]

\[Retrieved relevant Rules Package or canon-pack slices as needed by mode]

\[Retrieved relevant memories]

\[Recent turns verbatim]

\[Current input + classified intent]
```

### Step 3 — Core Narrative Pipeline and Safety Envelope

| Pass | Function |

|—|—|

| **[Input Safety Preflight]** | Evaluates Sojourner request against Afterworlds policy before generation starts. Conditional: runs when orchestration policy requires it. |

| **Planner** | Scene goal, next beat, facts needed |

| **Writer** | Polished prose and dialogue |

| **[Output Safety Audit]** | Evaluates Writer-generated prose against Afterworlds policy before downstream passes run. Conditional: runs when provider or risk policy requires it. |

| **Extractor** | Pulls new facts, state deltas, continuity updates — proposes Story Bible updates |

| **Contradiction** | Checks output against Story Bible before it leaves the system |

**Access routing:**

Hosted subscription, starter access if offered, and BYOK all run the full Sojourn orchestration path, including both the core narrative pipeline and the safety envelope.

Commercial routing governs credit consumption, top-up prompts, Cloud Services entitlements, and provider billing path — not whether core continuity passes or responsible guardrails are present.

### Step 4 — Extractor Update Policy

The Extractor proposes candidate Story Bible updates. It does not write directly to canon. Updates are classified before acceptance:

| Classification | Handling |

|—|—|

| **Locked fact** | Requires explicit Sojourner confirmation before commit |

| **Soft fact** | Auto-committed with low confidence flag, Sojourner can review |

| **Transient state** | Auto-committed (e.g., current location, active quest) |

| **Unresolved thread** | Queued to plot thread tracker, not committed to canon |

An Extractor that auto-canonizes everything will hallucinate trivia into permanent law within a few chapters. This policy prevents that.

### Step 5 — State Persistence

- Save Turn; create or update Node

- Apply State Delta to World State

- Trigger rolling summary update if threshold hit

- Commit Extractor-approved updates to Story Bible

- Push scene to vector DB

### Step 6 — Optional Multimodal

- Scene image generated from Node metadata (character appearance pulled from Story Bible for visual consistency across chapters)

- TTS narration

- Ambient audio trigger

-–

## 5. The Three Modes

All three modes run on the Sojourn pipeline. They differ in prompt contract, planning emphasis, and UI affordances.

### RPG Mode

- **System prompt:** AI is Game Master running a d20-based tabletop RPG. Consequence-first narration; preserve Sojourner agency. Never tell players what they feel. Dice rolls govern all conflict including NPCs. GM cheating is calibrated to tone (gritty through danger-free) and can be disabled entirely by player configuration. Rule set consistency is maintained throughout — rule sets are modular, with d20 as the first and only v1 exemplar.

- **Pre-play sequence:** World setup first (player describes setting in free text; GM confirms and asks clarifying questions); then character creation within that world context (GM-led conversational creation or player-supplied sheet; play does not begin until sheet is complete enough to adjudicate against). *v1 supports original and custom settings only; player-supplied Setting Canon Packs for licensed settings deferred to v2/v3.*

- **Character sheet:** First-class persistent object. Persists across all sessions for that story. Mutable during play — HP damage, level-ups, temporary buffs, spell effects, permanent modifications. Not a conversation artifact or a blob on session state.

- **World State sidebar:** HP, inventory, relationship meters, location (visible or hidden per Sojourner preference)

- **Rules access:** RPG mode binds to one active Rules Package. The GM receives only turn-relevant rule slices and house-rule overrides, never the entire rule library in prompt context.

- **Mechanical adjudication:** Two dice modes configured by player — Player rolls (GM announces check type and all applicable modifiers, waits for player to report result, never narrates outcome before the roll; stops and requests the roll if player acts without reporting one) or AI rolls (GM rolls and always shows the result for player character actions. Exception: hidden rolls for checks the player has no in-world awareness of are resolved privately in both modes — the outcome is narrated without showing the roll). Modifiers from character sheet, situation, retrieved rule text, and house rules; tone calibrates consequence severity.

- **Primary intent types:** Action, dialogue, lore question

### Branching Mode

- **System prompt:** AI is story architect, maintaining dramatic shape.

- **Optional canon packs (future-lightweight extension):** Branching mode may attach an external canon/lore pack for franchise or fan-fiction continuity without inflating the Story Bible.

- **Invisible plot graph:** Tracks current node, pacing stage (setup / escalation / reversal / climax / aftermath), locked outcomes. Pacing stage progression calibrated to player’s configured length preference (short story / novella / novel).

- **Branch generation:** After each narrative beat, a secondary generation call produces 3–5 contextually relevant branch options. Sojourner may select one or type freeform. Both are first-class options presented with equal prominence — branch cards exist to inspire and indicate what’s possible, not to confine.

- **Freeform handling:** Freeform input is mapped against current dramatic validity bands — not forced onto a preset rail. If Sojourner input meaningfully exceeds the current branch set, a new branch spawns rather than coercing the input. The story visibly adapts; it does not pretend it always knew where you were going.

- **Non-destructive branching** *(v2):* “What If?” paths are explored without touching the canonical timeline. Both exist in parallel. Deferred to v2.

- **Visual story map** *(v2):* Branch tree rendered in real time so Sojourners can see the shape of their story, not just inhabit it linearly. Deferred to v2.

### Writing Mode

- **System prompt:** AI is collaborative writing partner — not GM, not architect. Role and orientation determined by persona selection. The user is the author of record in all cases.

- **Optional canon packs (future-lightweight extension):** Writing mode may attach an external canon/lore pack when the Sojourner is writing in an existing setting or franchise.

- **Persona-based relationship model:** No explicit submode labels. The player selects a persona from a gallery divided into two categories — Mentors and Peers — which determines the AI’s fundamental relationship orientation.

- **Mentors** (Chiron, Merlin, Vidura): developmental guides. Primary orientation is teaching through making — craft goals, generative exercises, targeted feedback aimed at a specific craft objective. Manuscript repair is not their function; bringing existing prose to a Mentor is a diagnostic path only (“what should we work on?”).

\ - **Peers** (Odin, Athena, Thoth): creative collaborators. Primary orientation is making alongside the user — generating prose, proposing directions, pushing the work forward. Teaching available but not default; a Peer speaks up about craft only when something is genuinely holding the work back, or when asked.

- **Beat Control:** Sojourner sets milestone constraints (“By end of this chapter, X must happen”) the AI is bound to honor.

- **Exposed controls:** Tense, POV, length, style density, dialogue/narration ratio, genre conventions.

- **Version history and draft branching** — compare outputs, restore previous versions.

- All writing is rewriting.

- Strongest style conditioning of the three modes.

- Mentor focus: craft development through making. Peer focus: project-forward collaboration with the user as author of record throughout.

-–

## 6. Tech Stack

**Backend:** Python + FastAPI

**LLM options:**

| Option | Trade-off |

|—|—|

| Local (Ollama + Mistral / LLaMA 3) | Full privacy, no API cost, quality ceiling tied to hardware |

| Hybrid BYOK (recommended) | Local app, cloud brain, Sojourner’s own API key — best quality/cost balance |

| OpenRouter | Single integration point, model-agnostic routing, supports open-weight NSFW-capable models |

| VPS-hosted open-weight model | No per-token cost, full content control, fixed GPU compute overhead |

BYOK substantially reduces platform-level content gatekeeping and subscription friction. It does not eliminate all content constraints — upstream providers, app stores, and hosted service APIs retain their own policies — but it removes the ones competitors use as monetization levers.

**Storage:**

- SQLite — story state, sessions, nodes, character sheets, world state

- ChromaDB — vector/semantic retrieval memory (self-hosted from day one)

**Frontend:**

- React or Svelte web app

- Canvas/Konva for the visual branching story map *(v2)*

- Electron wrapper for desktop deployment (optional)

- Simplest path: local web server, accessed via browser

-–

## 7. Prompt Caching Strategy

All three major API providers support prompt/context caching in some form. Afterworlds should be architected to exploit this from the start — not as an afterthought, but as a first-class design constraint. For a system with large persistent Story Bibles and a multi-pass pipeline, the economics are material.

### Prompt Layout

Structure every prompt with stable material first, volatile material last:

```
\[System instructions + mode contract]

\[Story Bible + world rules]

\[Rolling summary]

\[Retrieved ephemeral facts]

\[Recent turns verbatim]

\[Current Sojourner input + classified intent]
```

The stable prefix — everything above the retrieved facts — is the cacheable block. The volatile suffix changes every turn and is never cached. This layout maximizes cache hits across all three providers, which all reward stable shared prefixes.

### Caching and the Multi-Pass Pipeline

This is where Afterworlds gains a structural advantage over naive implementations. The Planner, Extractor, Contradiction, and any conditional Safety passes all share the same Story Bible prefix. If the pipeline is architected so all passes reference the same cached prefix in a single session, the effective per-turn cost drops substantially — you pay to write the cache once and read it at a steep discount across subsequent passes within the turn.

The number of Safety calls per turn is conditional — input preflight may not run on ordinary turns from whitelisted providers, and output audit runs only when provider or risk policy requires it. Cost models should treat Safety as a conditional rather than guaranteed per-turn call.

This means prompt assembly should not be re-run independently per pass. The canonical context block should be assembled once per turn, cached, and referenced by each subsequent pass.

### Provider Notes

| Provider | Caching Style | Read Discount | TTL |

|—|—|—|—|

| Anthropic | Explicit, breakpoint-based | ~90% of base input price | 5 min default; 1 hr available |

| OpenAI | Automatic, prefix-based | Model-dependent, up to 90% | ~5–10 min, clears within 1 hr |

| Google | Both implicit and explicit | ~90% on supported Gemini models | 1 hr default for explicit; storage cost applies |

Exact pricing varies by model and changes frequently. Verify against current provider pricing pages before building cost models.

### TTL Consideration

Anthropic’s default 5-minute cache window is short for a narrative app where a Sojourner may pause mid-session. Sessions with natural breaks will pay full input price on cache misses more often than a naive cost model assumes. Use extended TTL options where available, and account for miss rate in per-tier cost projections.

### Design Rules

- Keep Story Bible and canon state structurally separate from prose history — this is economically correct, not just architecturally clean

- Prefer compact summaries and structured ledgers over resending long raw transcripts

- Never treat caching as a substitute for prompt discipline — a bloated prompt is still expensive; caching just makes repeated bloat less painful

- Caching is a coupon with engineering requirements, not a cost elimination

-–

## 8. Business Model

Afterworlds is designed around an ethical, AI-native fee structure that aligns user value with real platform cost **without degrading the core narrative engine by tier**.

The core product promise is continuity: persistent state, canon maintenance, and coherent story progression across turns and sessions. Those are not premium embellishments. They are the product. For that reason, Afterworlds does **not** operate on a crippled free-tier model that removes core pipeline functions. All paying access paths use the same Sojourn orchestration path. Access classes differ in billing path, credit allowance, and hosted-service entitlements — not in continuity quality or the presence of responsible guardrails.

### Commercial Structure

| Access Path | What You Get |

|—|—|

| **Hosted Subscription** | Full Sojourn orchestration path (core narrative pipeline + safety envelope), monthly included credits, transparent top-ups, optional limited rollover, hosted storage, sync, pack ingestion, and ongoing platform access |

| **BYOK Perpetual License** | Permanent right to use Afterworlds with the Sojourner’s own API keys; full pipeline parity with hosted users; first year of Cloud Services included |

| **BYOK Cloud Services Renewal** | Optional annual renewal for continued hosted storage, sync, ingestion processing, remote access, and other ongoing platform services after the first included year |

| **Starter Access (optional launch/on-ramp)** | Small paid entry package that uses the same full pipeline and consumes normal hosted credits; exists to reduce first-purchase friction without introducing a degraded free tier |

| **Open-source core** | Community trust and adoption; hosted services, convenience layers, and non-technical onboarding remain monetized |

### Hosted Subscription Model

The hosted subscription is a **metered subscription with credits**, not an “all you can eat” promise detached from model cost.

- A monthly subscription includes a defined credit allotment

- Credits are consumed by actual use of the hosted system

- Transparent top-ups are always available

- Limited rollover may be offered, but must be capped and legible

- When credits are exhausted, the system stops or prompts for top-up — it does not silently degrade story quality

This structure matches the economics of AI-native products while remaining understandable to users. Afterworlds should never hide usage reality behind fake abundance and then recover margin through degraded output, surprise caps, or manipulative gating.

### Operational Reality Addendum

A real product that charges real people also needs a human-operable support surface. Earlier versions of the design left that layer implicit, as though entitlement logic plus a payment-processor dashboard would somehow add up to an operational plan. That gap is now resolved explicitly.

For v1, Afterworlds requires the **operations/support minimums defined in Construction Readiness Issue 22**. This is not a separate commercial product and not an excuse to bloat v1 into a full back-office platform. It is a modest internal/operator layer sufficient to run the business responsibly at launch.

These capabilities are **parallel administrative infrastructure**, not part of the per-turn Sojourn pipeline. They exist to inspect, reconstruct, and repair commercial/user-data state when necessary.

### BYOK Structure

BYOK is a first-class path, not a fallback.

The BYOK offer is intentionally split into two distinct components:

1. **Perpetual BYOK License**

   - one-time purchase

   - grants permanent rights to use Afterworlds with the Sojourner’s own model/provider credentials

   - includes all core product functionality and future bug fixes / core improvements covered by the license terms

2. **Cloud Services**

   - first year included with the BYOK purchase

   - optional annual renewal thereafter

   - covers ongoing hosted services such as cloud storage, sync, backups, remote access, pack ingestion processing, and similar platform costs

This distinction is critical. The perpetual license is the software/product right. Cloud Services are the ongoing hosted-service layer. Afterworlds should never describe BYOK as a pure one-time purchase if continued hosted service depends on recurring platform expense.

### Non-Renewal Behavior for BYOK Cloud Services

If a BYOK user does not renew Cloud Services, the product should fail gracefully and ethically:

- retain read/export/download access to owned stories and content where practical

- suspend or reduce only the genuinely ongoing-cost hosted services

- allow later reactivation without penalty

- never hold user-created story data hostage as leverage for renewal

The user loses hosted convenience and ongoing platform services — not ownership of their work.

### Future Revenue Layers

These are not required for v1, but the business model should remain compatible with them from the start:

- **Creator marketplace / shareable story templates (v3)** with user-trust-oriented payout logic

- **Institutional licensing** for schools, libraries, workshops, and studios using per-seat, pooled-credit, or capped-usage models

- **Optional expansion packs / major feature expansions** for BYOK users, provided these are genuinely new capabilities rather than backfilled bug fixes or withheld essentials

### Ethical Principles

- Do not degrade continuity by tier

- Do not hide usage economics behind misleading “unlimited” language

- Do not trap users with dark-pattern upgrade or renewal flows

- Do not conflate perpetual software rights with recurring hosted-service costs

- Do not gate core dignity behind premium currency mechanics

Afterworlds’ commercial model should feel like a clear exchange, not a carnival game: the Sojourner either pays for hosted usage directly, or brings their own model costs and pays only for the continuing platform services they actually consume.

-–

## 9. MVP Sequence

### Pre-v1 internal milestones

These are construction milestones, not product versions. They describe build order and dependency sequencing before the first release-capable MVP.

- Core data model and SQLite persistence

- Story Bible and rolling summary

- Rules Package schema and ingestion pipeline

- Intent classification and context builder

- Minimal Writer path

- Extractor classification policy

- Lightweight contradiction checker

- Full pipeline orchestration (Planner, Writer, Extractor, Contradiction, and Safety envelope wired)

- Entitlement routing, hosted credits/top-ups, and BYOK support

- Operations/support minimums as defined in Construction Readiness Issue 22

### v1 — First release-capable text product

- Full Sojourn orchestration path: core narrative pipeline (Planner → Writer → Extractor → Contradiction) with safety envelope (input preflight and conditional output audit)

- RPG + Branching + Writing modes

- RPG mode includes: modular Rules Package support with d20 as the first curated and ingested exemplar; two dice handling modes (Player rolls / AI rolls); GM cheating toggle; mandatory pre-play sequence (world setup → character creation → play); character sheet as first-class persistent object

- Branching mode includes: plot graph, pacing stage tracking calibrated to length preference, 3–5 branch options per beat with freeform input as equal first-class option

- Branching mode excludes: visual story map, non-destructive What If? branching (both deferred to v2)

- Writing mode includes: persona-based relationship model — three Mentor personas (Chiron, Merlin, Vidura) and three Peer personas (Odin, Athena, Thoth)

- Full story hierarchy (Story / Arc / Chapter / Node / Turn)

- Rolling summary + Story Bible

- Extractor with update classification policy

- Contradiction checker

- SQLite persistence

- Vector retrieval memory (ChromaDB)

- Hosted subscription credit/top-up entitlement framework

- BYOK API support with perpetual-license and Cloud Services entitlements

- Operations/support minimums as defined in Construction Readiness Issue 22

- Issue 22 completed as the explicit home for the human-operable support/compliance layer

- All CI gates passing; no failing checks at release

### v2 — Advanced branching + multimodal

- Image generation from Node metadata

- Visual story map (branch tree rendered in real time)

- Non-destructive What If? branching (parallel timelines, no canonical timeline impact)

- Voice input/output

- Player-supplied Setting Canon Packs for licensed RPG settings (Forgotten Realms, Greyhawk, etc.)

- Player-supplied Setting Canon Packs for copywritten settings (Potterverse, Middle-Earth, Dune, The Seven Kingdoms, etc.)

### v3 — Polish and ecosystem

- Creator marketplace / shareable story templates

- Collaborative multi-Sojourner stories

- Export: PDF, ebook formatting

- Mobile clients

-–

## Summary Architecture

```
\[Sojourner Input]

↓

\[Intent Classifier]

↓

\[Context Builder] → System + Story Bible + Summary + Retrieved Rules Package / canon-pack slices + Retrieved Memory + Recent Turns

↓

\[Mode Handler] → RPG / Branching / Writing (prompt contract + planning logic)

↓

\[Sojourn Pipeline] → [Safety Preflight?] → Planner → Writer → [Safety Output Audit?] → Extractor → Contradiction

↓

\[Extractor Update Policy] → Classify → Confirm high-impact changes → Commit

↓

\[Output to UI] → Prose display + input field or branch cards

↓

\[Persistence] → Node saved, State Delta applied, Story Bible updated, vector DB pushed
```

**Operational note:** The operations/support minimums defined in Construction Readiness Issue 22 are parallel administrative capabilities, not a sequential stage in the turn pipeline.