# Afterworlds: Synthesized Design Document (v6)

---

## Core Philosophy

One shared narrative engine. Three UX contracts on top of it.
The platform is the **Sojourn Story State Machine** — not a chatbot wearing a cape.

---

## 1. Terminology

Two concepts that must stay distinct:

- **Turn** — one interaction unit (one user input + one AI response)
- **Node** — one persisted story beat / state transition in the story graph

These often correspond 1:1, but not always. In branching scenarios, a node may encompass multiple turns, or represent an alternative path never actually traversed. Collapsing them is conceptual debt. Keep them separate throughout the codebase and data model.

---

## 2. Data Architecture

### Story Object Hierarchy

```
Story
 └── Arc
      └── Chapter
           └── Node (story beat / state transition)
                └── Turn (interaction unit)
```

### Node Schema

Every persisted story beat is a Node:

| Field | Description |
|---|---|
| Node ID | Unique identifier |
| Content | Generated prose or dialogue |
| State Delta | World mutations caused by this beat (e.g., `gold -50`, `king_trust: hostile → neutral`) |
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

**Play-time model:** the Context Builder retrieves only the rules relevant to the current turn (for example: attack resolution, a spell entry, an active condition, a monster trait). Deterministic calculations should move to code/services where practical; the model narrates and adjudicates from the retrieved packet rather than "remembering" the system wholesale.

**v1 assumption:** d20 is the first curated Rules Package. Future systems (GURPS, Shadowrun, etc.) slot in as additional Rules Packages using the same ingestion and retrieval path.

The same ingestion pattern can later support lighter-weight canon packs for Branching and Writing modes (for example: franchise lore packs, fan-fiction canon packets, or setting bibles larger than the normal Story Bible should carry).

---

## 3. Memory Architecture

Six layers, each with a distinct role:

| Layer | Contents | Inclusion |
|---|---|---|
| Immediate | Last ~10 turns verbatim | Always |
| Rolling Summary | Compressed narrative, auto-updated every N turns | Always |
| Story Bible | Structured canon | Always |
| Rules Package | Retrieved mechanical canon or external canon-pack context | On demand by mode |
| Retrieval Memory | Vector DB of past scenes, pulled by semantic relevance | On demand |
| Contradiction Checker | Pre-output scan for continuity violations | Every turn (depth varies by tier) |

### Contradiction Checker — What It Catches

- Dead characters speaking or acting
- Items in inventory never acquired
- Location or name drift
- POV or tense shift mid-scene
- Violated locked facts

This is what separates "better memory" as a marketing claim from "better memory" as a product reality.

**Free tier:** lightweight Planner + Writer + lightweight contradiction check (recent context + locked facts only) + Safety
**Paid tier:** full five-pass pipeline with deep validation against complete Story Bible and vector history

A free tier that silently fails on continuity isn't a funnel — it's an anti-demo. Basic dignity must be preserved at every tier.

---

## 4. The Narrative Orchestration Pipeline

Every input passes through the Sojourn orchestration pipeline, with depth, pass composition, and model selection determined by mode, tier, and task complexity.

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
[System prompt + mode contract]
[Story Bible (includes cast ledger, world state)]
[Rolling summary]
[Retrieved relevant Rules Package or canon-pack slices as needed by mode]
[Retrieved relevant memories]
[Recent turns verbatim]
[Current input + classified intent]
```

### Step 3 — Multi-Model Pipeline

| Pass | Function |
|---|---|
| **Planner** | Scene goal, next beat, facts needed |
| **Writer** | Polished prose and dialogue |
| **Extractor** | Pulls new facts, state deltas, continuity updates — proposes Story Bible updates |
| **Contradiction** | Checks output against Story Bible before it leaves the system |
| **Safety** | Policy and moderation check |

**Tier routing:**
Free tier runs lightweight Planner + Writer + lightweight Contradiction + Safety.
Paid tier runs the full five-pass stack.

### Step 4 — Extractor Update Policy

The Extractor proposes candidate Story Bible updates. It does not write directly to canon. Updates are classified before acceptance:

| Classification | Handling |
|---|---|
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

---

## 5. The Three Modes

All three modes run on the Sojourn pipeline. They differ in prompt contract, planning emphasis, and UI affordances.

### RPG Mode

- **System prompt:** AI is Game Master running a d20-based tabletop RPG. Consequence-first narration; preserve Sojourner agency. Never tell players what they feel. Dice rolls govern all conflict including NPCs. GM cheating is calibrated to tone (gritty through danger-free) and can be disabled entirely by player configuration. Rule set consistency is maintained throughout — rule sets are modular, with d20 as the first and only v1 exemplar.
- **Pre-play sequence:** World setup first (player describes setting in free text; GM confirms and asks clarifying questions); then character creation within that world context (GM-guided conversational creation or player-supplied sheet; play does not begin until sheet is complete enough to adjudicate against). *v1 supports original and custom settings only; player-supplied Setting Canon Packs for licensed settings deferred to v2/v3.*
- **Character sheet:** First-class persistent object. Persists across all sessions for that story. Mutable during play — HP damage, level-ups, temporary buffs, spell effects, permanent modifications. Not a conversation artifact or a blob on session state.
- **World State sidebar:** HP, inventory, relationship meters, location (visible or hidden per Sojourner preference)
- **Rules access:** RPG mode binds to one active Rules Package. The GM receives only turn-relevant rule slices and house-rule overrides, never the entire rule library in prompt context.
- **Mechanical adjudication:** Two dice modes configured by player — Player rolls (GM announces check type and all applicable modifiers, waits for player to report result, never narrates outcome before the roll; stops and requests the roll if player acts without reporting one) or AI rolls (GM rolls and always shows the result). Hidden rolls apply in both modes when the player has no in-world awareness that a check is occurring — resolved privately, outcome narrated. Modifiers from character sheet, situation, retrieved rule text, and house rules; tone calibrates consequence severity.
- **Primary intent types:** Action, dialogue, lore question

### Branching Mode

- **System prompt:** AI is story architect, maintaining dramatic shape.
- **Optional canon packs (future-lightweight extension):** Branching mode may attach an external canon/lore pack for franchise or fan-fiction continuity without inflating the Story Bible.
- **Invisible plot graph:** Tracks current node, pacing stage (setup / escalation / reversal / climax / aftermath), locked outcomes. Pacing stage progression calibrated to player's configured length preference (short story / novella / novel).
- **Branch generation:** After each narrative beat, a secondary generation call produces 3–5 contextually relevant branch options. Sojourner may select one or type freeform. Both are first-class options presented with equal prominence — branch cards exist to inspire and indicate what's possible, not to confine.
- **Freeform handling:** Freeform input is mapped against current dramatic validity bands — not forced onto a preset rail. If Sojourner input meaningfully exceeds the current branch set, a new branch spawns rather than coercing the input. The story visibly adapts; it does not pretend it always knew where you were going.
- **Non-destructive branching** *(v2):* "What If?" paths are explored without touching the canonical timeline. Both exist in parallel. Deferred to v2.
- **Visual story map** *(v2):* Branch tree rendered in real time so Sojourners can see the shape of their story, not just inhabit it linearly. Deferred to v2.

### Writing Mode

- **System prompt:** AI is collaborative writing partner — not GM, not architect. Role and orientation determined by persona selection. The user is the author of record in all cases.
- **Optional canon packs (future-lightweight extension):** Writing mode may attach an external canon/lore pack when the Sojourner is writing in an existing setting or franchise.
- **Persona-based relationship model:** No explicit submode labels. The player selects a persona from a gallery divided into two categories — Guides and Peers — which determines the AI's fundamental relationship orientation.
  - **Guides** (Chiron, Merlin, Vidura): developmental mentors. Primary orientation is teaching through making — craft goals, generative exercises, targeted feedback aimed at a specific craft objective. Manuscript repair is not their function; bringing existing prose to a Guide is a diagnostic path only ("what should we work on?").
  - **Peers** (Odin, Athena, Thoth): creative collaborators. Primary orientation is making alongside the user — generating prose, proposing directions, pushing the work forward. Teaching available but not default; a Peer speaks up about craft only when something is genuinely holding the work back, or when asked.
- **Beat Control:** Sojourner sets milestone constraints ("By end of this chapter, X must happen") the AI is bound to honor.
- **Exposed controls:** Tense, POV, length, style density, dialogue/narration ratio, genre conventions.
- **Version history and draft branching** — compare outputs, restore previous versions.
- All writing is rewriting.
- Strongest style conditioning of the three modes.
- Guide focus: craft development through making. Peer focus: project-forward collaboration with the user as author of record throughout.

---

## 6. Tech Stack

**Backend:** Python + FastAPI

**LLM options:**

| Option | Trade-off |
|---|---|
| Local (Ollama + Mistral / LLaMA 3) | Full privacy, no API cost, quality ceiling tied to hardware |
| Hybrid BYOK (recommended) | Local app, cloud brain, Sojourner's own API key — best quality/cost balance |
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

---

## 7. Prompt Caching Strategy

All three major API providers support prompt/context caching in some form. Afterworlds should be architected to exploit this from the start — not as an afterthought, but as a first-class design constraint. For a system with large persistent Story Bibles and a five-pass pipeline, the economics are material.

### Prompt Layout

Structure every prompt with stable material first, volatile material last:

```
[System instructions + mode contract]
[Story Bible + world rules]
[Rolling summary]
[Retrieved ephemeral facts]
[Recent turns verbatim]
[Current Sojourner input + classified intent]
```

The stable prefix — everything above the retrieved facts — is the cacheable block. The volatile suffix changes every turn and is never cached. This layout maximizes cache hits across all three providers, which all reward stable shared prefixes.

### The Five-Pass Implication

This is where Afterworlds gains a structural advantage over naive implementations. The Planner, Extractor, Contradiction, and Safety passes all share the same Story Bible prefix. If the pipeline is architected so all five passes reference the same cached prefix in a single session, the effective per-turn cost drops substantially — you pay to write the cache once and read it up to four additional times at a fraction of the input price.

This means prompt assembly should not be re-run independently per pass. The canonical context block should be assembled once per turn, cached, and referenced by each subsequent pass.

### Provider Notes

| Provider | Caching Style | Read Discount | TTL |
|---|---|---|---|
| Anthropic | Explicit, breakpoint-based | ~90% of base input price | 5 min default; 1 hr available |
| OpenAI | Automatic, prefix-based | Model-dependent, up to 90% | ~5–10 min, clears within 1 hr |
| Google | Both implicit and explicit | ~90% on supported Gemini models | 1 hr default for explicit; storage cost applies |

Exact pricing varies by model and changes frequently. Verify against current provider pricing pages before building cost models.

### TTL Consideration

Anthropic's default 5-minute cache window is short for a narrative app where a Sojourner may pause mid-session. Sessions with natural breaks will pay full input price on cache misses more often than a naive cost model assumes. Use extended TTL options where available, and account for miss rate in per-tier cost projections.

### Design Rules

- Keep Story Bible and canon state structurally separate from prose history — this is economically correct, not just architecturally clean
- Prefer compact summaries and structured ledgers over resending long raw transcripts
- Never treat caching as a substitute for prompt discipline — a bloated prompt is still expensive; caching just makes repeated bloat less painful
- Caching is a coupon with engineering requirements, not a cost elimination

---

## 8. Business Model

Afterworlds is designed around an ethical fee structure. Competitor models gate content behind Stars, ads, and subscription tiers. The complaints are predictable consequences of that design.

Afterworlds' structure:

| Tier | What You Get |
|---|---|
| **Free** | 50 turns/month, lightweight Planner + Writer + lightweight Contradiction + Safety |
| **Paid subscription** | Full five-pass Sojourn pipeline, longer chapters, (image generation, voice narration, What-If? branching in v2) |
| **BYOK one-time purchase** | Full functionality, Sojourner supplies API key, flat fee covers infrastructure only — no grind, no content gate |
| **Open-source core** | Community trust and adoption; monetize hosted version for non-technical Sojourners |

The gating in competitor platforms is primarily a monetization decision, not purely a principled safety architecture. Safety, legal risk, and platform compliance all contribute to content restrictions in the industry broadly — but the specific pattern of locking NSFW content behind premium currency while offering it freely to paying users is transparently incentive-driven. Afterworlds' BYOK model sidesteps that incentive structure by design.

---

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
- Full five-pass pipeline orchestration
- Tier routing and BYOK support

### v1 — First release-capable text product
- Full five-pass Sojourn pipeline
- RPG + Branching + Writing modes
- RPG mode includes: modular Rules Package support with d20 as the first curated and ingested exemplar; two dice handling modes (Player rolls / AI rolls); GM cheating toggle; mandatory pre-play sequence (world setup → character creation → play); character sheet as first-class persistent object
- Branching mode includes: plot graph, pacing stage tracking calibrated to length preference, 3–5 branch options per beat with freeform input as equal first-class option
- Branching mode excludes: visual story map, non-destructive What If? branching (both deferred to v2)
- Writing mode includes: persona-based relationship model — three Guide personas (Chiron, Merlin, Vidura) and three Peer personas (Odin, Athena, Thoth)
- Full story hierarchy (Story / Arc / Chapter / Node / Turn)
- Rolling summary + Story Bible
- Extractor with update classification policy
- Contradiction checker
- SQLite persistence
- Vector retrieval memory (ChromaDB)
- BYOK API support

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

---

## Summary Architecture

```
[Sojourner Input]
↓
[Intent Classifier]
↓
[Context Builder] → System + Story Bible + Summary + Retrieved Rules Package / canon-pack slices + Retrieved Memory + Recent Turns
↓
[Mode Handler] → RPG / Branching / Writing (prompt contract + planning logic)
↓
[Sojourn Pipeline] → Planner → Writer → Extractor → Contradiction → Safety
↓
[Extractor Update Policy] → Classify → Confirm high-impact changes → Commit
↓
[Output to UI] → Prose display + input field or branch cards
↓
[Persistence] → Node saved, State Delta applied, Story Bible updated, vector DB pushed
```
