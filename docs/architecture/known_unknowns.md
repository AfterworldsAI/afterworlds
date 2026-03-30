# Afterworlds — Known Unknowns

*Canonical reference for all open design and implementation decisions.*
*Maintained throughout construction. Update this file when an unknown is resolved or a new one surfaces.*
*Last updated: March 2026*

---

## How to Use This Document

**For Claude Code:** Before implementing anything that touches a listed unknown, stop and flag it. Do not resolve a Known Unknown unilaterally — raise it in the PR description and pause for explicit owner decision. Resolving a Known Unknown is a load-bearing product decision, not a local implementation choice.

**For Codex:** Flag any PR that appears to resolve or work around a Known Unknown without a corresponding ADR in `/docs/decisions/` and explicit owner confirmation.

**For the project owner:** When a decision is made, move the item from "Open" to "Resolved," record the decision and rationale here, and write an ADR in `/docs/decisions/`.

---

## Resolved — No Longer Unknowns

These were open questions during design. Decisions are recorded here for traceability.

| Item | Decision | Notes |
|---|---|---|
| Vector DB | ChromaDB, self-hosted from day one | Not a v2 deferral — core to v1 release scope |
| Contradiction checker approach | Sequential gate on Writer output, small/fast model | Checker evaluates generated prose, not input context; see Item 7 in CRD |
| Intent classifier approach | Lightweight model call | Classifies before context assembly; see Issue 7 |
| Business model and pricing | Metered hosted subscription with credits + BYOK perpetual license + first-year Cloud Services | See Item 8 in CRD and Design doc Section 8 |
| Story Bible schema | Committed | Static / dynamic / provisional partitions, Events Ledger, Locked/Forbidden Facts; see Issue 4 |
| Mode prompt contracts | Written | Versioned .md files in `/docs/prompts/`; see Item 6 in CRD |
| BYOK commercial structure | Perpetual license + first year of Cloud Services included; optional annual renewal thereafter | License and services must not be collapsed in code or UX language |
| Writing mode structure | Persona-based — Mentors (Chiron, Merlin, Vidura) and Peers (Odin, Athena, Thoth) | No explicit submode labels; category communicated through persona descriptions |
| RPG dice handling | Two modes: Player rolls / AI rolls | Hidden rolls are a narrative mechanic in both modes, not a player-facing setting |

---

## Open — Acceptable to Resolve During Construction

These are genuinely open. Each has a designated resolution window. Do not resolve early without explicit approval.

---

### React or Svelte for the initial frontend

**Resolve before:** Issue 19

**Why it's open:** Both are viable. The decision affects component architecture, build tooling, and long-term maintainability but does not affect any backend or pipeline decisions. Deferring keeps early issues unblocked.

**What resolution requires:** A brief ADR weighing bundle size, ecosystem maturity, team familiarity, and the eventual visual story map (v2, likely Canvas/Konva). Document the choice and rationale before Issue 19 begins.

**Constraint:** Must be resolved before any frontend skeleton work begins. All Issues 1–18 are backend/pipeline — this unknown does not block them.

---

### Exact ChromaDB collection schema for story/rules vectors

**Resolve before:** Issue 18

**Why it's open:** Collection design (one collection per story vs. shared collections with metadata filtering, embedding model choice, chunking strategy) has performance and retrieval quality implications that are best informed by having a working pipeline to test against. Premature lock-in here is more costly than deferral.

**What resolution requires:** Define collection naming convention, metadata fields per document type (scene, Story Bible entry, rules chunk), embedding model, and chunking policy. Document in an ADR before Issue 18 begins.

**Constraint:** Context Builder (Issue 8) should be designed to accept a retrieval interface rather than hard-coding ChromaDB assumptions, so this unknown doesn't block Issues 8–17.

---

### Exact FastAPI route shapes

**Resolve before:** Issue 18 (or whenever the first route is needed)

**Why it's open:** Route design is best decided once the service layer is stable. Premature route definitions create churn if underlying service contracts change during Issues 2–11.

**What resolution requires:** Define route naming conventions, versioning strategy (e.g., `/api/v1/`), request/response payload shapes for core operations (create story, submit turn, retrieve state). Document before implementation begins.

---

### Rolling summary compression trigger value (N turns)

**Resolve during:** Issue 6. Starting value: 10 turns.

**Why it's open:** The right trigger depends on average turn length, Story Bible growth rate, and acceptable context window pressure — all of which are empirically determined. 10 is a reasonable starting point based on cost model assumptions but must be validated with testing.

**What resolution requires:** During Issue 6, implement the trigger as a configurable value (not a hardcoded constant). Run representative test scenarios. Document the final chosen value and the test evidence in an ADR.

---

### Events Ledger tiered inclusion N value (recent events to load)

**Resolve during:** Issue 4. Starting value: 15 events.

**Why it's open:** The right N balances context window pressure against continuity coverage. Too low and the checker misses recent history; too high and the stable prefix bloats. 15 is a starting estimate.

**What resolution requires:** During Issue 4, implement N as a configurable constant. Test against representative story scenarios at minimal, moderate, and complex Story Bible sizes. Document the final value and rationale in an ADR.

---

### Significance flagging criteria for Events Ledger

**Resolve during:** Issue 4.

**Why it's open:** "High-significance" events are the ones that survive tiered inclusion even when they fall outside the N most recent. The criteria for what counts as high-significance — character death, locked fact establishment, major plot turning point, etc. — need to be defined and implemented as part of the Events Ledger service.

**What resolution requires:** Define a significance taxonomy during Issue 4. Implement as a structured enum or classification, not a freeform flag. Document criteria in an ADR. The Extractor will eventually propose significance levels; the Issue 4 implementation sets the schema it must conform to.

---

### Session resumption UX on cache miss

**Resolve during:** Issue 14 (BYOK API key management / provider routing).

**Why it's open:** When a user resumes a session after a long pause, the cache is cold and the first turn pays full stable prefix cost. The UX question is whether to surface this transparently (e.g., a brief "resuming your story" indicator), silently absorb it, or give the user a visual cue that the session is warming up.

**What resolution requires:** Decide on the UX pattern and document it before Issue 14. This is a product decision, not a technical one — the architecture handles cold starts correctly regardless. The decision is about what the user sees.

---

### Mentor and Peer persona behavioral implementation details

**Resolve during:** Issue 17.

**Personas:** Mentors — Chiron, Merlin, Vidura. Peers — Odin, Athena, Thoth.

**Why it's open:** The persona gallery, behavioral briefs, and prompt injections for each of the six personas need to be designed and written as part of Writing mode integration. The high-level orientation for each category is defined in the prompt contract (`/docs/prompts/writing_mode.md`), but the specific voice, behavioral emphases, and distinguishing characteristics of each individual persona are not yet specified.

**What resolution requires:** During Issue 17, write behavioral briefs for all six personas. Each brief should define: distinctive voice and register, default opening approach, how they handle ambiguity or unclear user goals, how they differ from other personas in their category, and any persona-specific constraints or tendencies. Document in an ADR or as companion files to the prompt contract.

---

### Prose parity constraint for Writing mode (Mentor and Peer output balance)

**Resolve during:** Issue 17.

**Why it's open:** The question is whether Mentors and Peers should be constrained to match or approximate the user's prose output volume per turn, to prevent the AI from taking over the writing. Two sub-questions remain open:

1. **Per-turn vs. running-total parity:** Per-turn parity is simpler but can feel mechanical (a two-sentence user input caps the AI at two sentences even when that's unhelpful). Running-total parity is more forgiving — the AI can write more in one turn if the user wrote more in a previous one, as long as cumulative balance stays roughly even.

2. **Scope — Peers only or all personas:** Parity makes clean sense for Peers, who are co-writers. It's murkier for Mentors, whose output is often feedback and craft instruction rather than prose. Counting Mentor feedback words against a prose parity cap may not be the right frame.

**What resolution requires:** Decide on the parity model (per-turn vs. running-total), the scope (Peers only vs. all personas), and how Mentor feedback output is measured differently from prose. Implement as a session state field (running word counts for user and AI prose, updated each turn by the Extractor). Document the decision in an ADR during Issue 17.

---

## How to Add a New Unknown

When construction surfaces a decision that isn't covered by existing docs and shouldn't be resolved unilaterally:

1. Add it to the Open section above with: what it is, why it's open, what resolution requires, and when it must be resolved
2. Note it in the PR description as a Known Unknown surfaced during implementation
3. Do not proceed with a local resolution — pause for owner decision

---

*This document is a canonical architecture artifact. Updates require a PR with an Architecture Notes section. Resolving a Known Unknown requires a corresponding ADR in `/docs/decisions/`.*
