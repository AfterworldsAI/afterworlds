# Afterworlds — Known Unknowns

*Canonical reference for all open design and implementation decisions.*
*Maintained throughout construction. Update this file when an unknown is resolved or a new one surfaces.*
*Last updated: May 2026 — Issue 12c resolved provider-refusal handling and opacity; added OOC protocol authoring and safety-whitelist resolution as new Open items.*

---

## How to Use This Document

**For Claude Code:** Before implementing anything that touches a listed unknown, stop and flag it. Do not resolve a Known Unknown unilaterally — raise it in the PR description and pause for explicit owner decision. Resolving a Known Unknown is a load-bearing product decision, not a local implementation choice.

**For Codex:** Flag any PR that appears to resolve or work around a Known Unknown without a corresponding ADR in `/docs/decisions/` and explicit owner confirmation.

**For the project owner:** When a decision is made during construction, move the item from "Open" to "Resolved," record the decision and rationale here, and write an ADR in `/docs/decisions/`. Pre-construction design decisions are documented in the Design doc and CRD, which serve as their auditable record — no separate ADR is required for items resolved before construction began.

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
| Events Ledger tiered inclusion N value | 15 (configurable constant) | Resolved during Issue 4. Implemented as `EVENTS_LEDGER_N = 15` in `services/story_bible.py`. Tune with testing. See ADR-0005. |
| Rolling summary compression trigger value (N turns) | Provisional N = 10 (configurable constant); empirical finalization deferred to Issue 8 | Escape hatch invoked during Issue 6: Context Builder not yet wired; stable-prefix-pressure evidence unavailable. Implemented as `ROLLING_SUMMARY_N = 10` in `services/rolling_summary.py`. Must be finalized in Issue 8 — not deferred past Issue 8. See ADR-0009. |
| Significance flagging criteria for Events Ledger | Seven-value enum; six qualify for always-include | Resolved during Issue 4. Always-include: CHARACTER_DEATH, LOCKED_FACT_ESTABLISHED, MAJOR_PLOT_TURN, RELATIONSHIP_CHANGE, WORLD_STATE_CHANGE, FORBIDDEN_FACT_ESTABLISHED. ROUTINE is the only non-always-include value. See ADR-0005. |
| Mode prompt contracts | Written | Versioned .md files in `/docs/prompts/`; see Item 6 in CRD |
| BYOK commercial structure | Perpetual license + first year of Cloud Services included; optional annual renewal thereafter | License and services must not be collapsed in code or UX language |
| Writing mode structure | Persona-based — Mentors (Chiron, Merlin, Vidura) and Peers (Odin, Athena, Thoth) | No explicit submode labels; category communicated through persona descriptions |
| RPG dice handling | Two modes: Player rolls / AI rolls | Hidden rolls are a narrative mechanic in both modes, not a player-facing setting |
| Provider refusal handling in the pipeline | Typed `ProviderRefusalError` per pass → `REFUSED_BY_PROVIDER`; no retries / fallback / routing in v1 | Resolved during Issue 12c; see ADR-0014. Issue 14 owns refusal-aware routing. |
| Provider refusal reason opacity | `ProviderRefusal.coarse_reason` is captured for audit but advisory only — orchestrator never routes on it | Resolved during Issue 12c; see ADR-0014. Issue 14 may use observed patterns to inform routing without depending on granular reasons. |

---

## Open — Acceptable to Resolve During Construction

These are genuinely open. Each has a designated resolution window. Do not resolve early without explicit approval.

---

### Mode-contract OOC protocol authoring (Issue 12c surface)

**Resolve during:** Issues 15 (RPG), 16 (Branching), 17 (Writing).

Issue 12c short-circuits OOC turns away from the narrative passes and routes them through `WriterService` with the thin v1 placeholder at `/docs/prompts/ooc_handler.md`. The placeholder is mode-agnostic, brief, and explicitly marked as v1 only. The final mode-aware OOC protocols — what the GM, Story Architect, and Writing personas should say when the Sojourner steps out of character — belong to each mode's prompt contract.

**What resolution requires:** Issues 15–17 must extend `/docs/prompts/{mode}_mode.md` with an explicit OOC protocol section per mode, then either replace the placeholder or have the orchestrator select the mode-specific OOC instruction. Document the swap in an ADR if the orchestrator's OOC-handler selection logic changes shape.

---

### Safety-policy provider whitelist resolution (Issue 12c surface)

**Resolve during:** Issue 14 (BYOK API key management and provider routing).

Issue 12c ships with `SafetyPolicy()` defaulting to an empty `whitelisted_providers` frozenset, so Input Preflight and Output Audit run on every Turn. Issue 14 defines provider capability profiles and chooses which providers (if any) are trusted enough to skip the conservative default. Until that decision is made, neither Safety call may silently skip.

**What resolution requires:** Issue 14 must specify which provider identifiers qualify for the whitelist, the criteria (e.g. provider-side safety attestations, observed refusal patterns), and the operator-visible audit trail for whitelist changes. Document the criteria in an ADR before flipping the default.

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

*This document is a canonical architecture artifact. Updates require a PR with an Architecture Notes section. Resolving a Known Unknown during construction requires a corresponding ADR in `/docs/decisions/`. Items in the Resolved table that were decided before construction began are documented in the Design doc and CRD.*
