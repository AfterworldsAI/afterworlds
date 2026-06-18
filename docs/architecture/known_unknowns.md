# Afterworlds — Known Unknowns

*Canonical reference for all open design and implementation decisions.*
*Maintained throughout construction. Update this file when an unknown is resolved or a new one surfaces.*
*Last updated: June 2026 — revised to align with Design v11 and CRD v9 after Owner Decisions #1–#14, Claude critique incorporation, Branching cadence/verbosity preservation, Starter Access retention, and True CYOA input-handling clarification.*

---

## How to Use This Document

**For Claude Code:** Before implementing anything that touches a listed unknown, stop and flag it. Do not resolve a Known Unknown unilaterally — raise it in the PR description and pause for explicit owner decision. Resolving a Known Unknown is a load-bearing product decision, not a local implementation choice.

**For Codex:** Flag any PR that appears to resolve or work around a Known Unknown without a corresponding ADR in `/docs/decisions/` and explicit owner confirmation when the item is resolved during construction.

**For the project owner:** When a decision is made during construction, move the item from **Open** to **Resolved**, record the decision and rationale here, and write an ADR in `/docs/decisions/` when the decision is made inside an implementation issue or materially constrains implementation. Pre-construction owner decisions captured in the Design doc and CRD are already auditable there; they do not require retroactive ADRs unless later implementation changes their shape.

---

## Resolved — No Longer Unknowns

These were open questions during design or early construction. Decisions are recorded here for traceability.

| Item | Decision | Notes |
|---|---|---|
| Vector DB | ChromaDB, self-hosted from day one | Not a v2 deferral — core to v1 release scope. |
| Contradiction checker approach | Sequential gate on Writer output, small/fast model | Checker evaluates generated prose, not input context; see CRD Item 7 and Issue 11. |
| Intent classifier approach | Lightweight model call | Classifies before context assembly; see Issue 7. |
| Business model and pricing shape | Metered hosted subscription with credits + BYOK perpetual license + first-year Cloud Services + optional Starter Access | See CRD Item 8 and Design Section 8. Exact plan prices, credit quantities, and payment-provider implementation remain separate launch/business decisions. |
| Starter Access | Retained as an optional paid entry package / trial subscription using normal hosted credits and the full Sojourn pipeline | Starter Access is not a free tier, degraded tier, or reduced-continuity path. It may be abandoned later if a better trial model replaces it, but preserving it causes no architectural harm. |
| Story Bible schema | Committed | Static / dynamic / provisional partitions, Events Ledger, Locked/Forbidden Facts; see Issue 4. |
| Events Ledger tiered inclusion N value | 15 (configurable constant) | Resolved during Issue 4. Implemented as `EVENTS_LEDGER_N = 15` in `services/story_bible.py`. Tune with testing. See ADR-0005. |
| Rolling summary compression trigger value (N turns) | Provisional N = 10 (configurable constant); empirical finalization deferred to Issue 8 | Escape hatch invoked during Issue 6: Context Builder not yet wired; stable-prefix-pressure evidence unavailable. Implemented as `ROLLING_SUMMARY_N = 10` in `services/rolling_summary.py`. Must be finalized in Issue 8 — not deferred past Issue 8. See ADR-0009. |
| Significance flagging criteria for Events Ledger | Seven-value enum; six qualify for always-include | Resolved during Issue 4. Always-include: CHARACTER_DEATH, LOCKED_FACT_ESTABLISHED, MAJOR_PLOT_TURN, RELATIONSHIP_CHANGE, WORLD_STATE_CHANGE, FORBIDDEN_FACT_ESTABLISHED. ROUTINE is the only non-always-include value. See ADR-0005. |
| Mode prompt contracts | Written and revised to v2 | Versioned `.md` files live in `/docs/prompts/`. Mode-contract content changes belong to Issues 15–17 unless a later dedicated issue explicitly scopes them. |
| BYOK commercial structure | Perpetual license + first year of Cloud Services included; optional annual renewal thereafter | License and services must not be collapsed in code, UX language, entitlement logic, support views, or export/deletion handling. |
| Cloud Services scope | Hosted persistence, sync, backup, remote access, hosted ingestion, and any hosted runtime dependent on Afterworlds server resources | Issue 13 enforcement must cover all Cloud Services-dependent resources, not only hosted generation. |
| Issue 13 vs. Issue 14 routing boundary | Issue 13 routing = access-path and entitlement enforcement. Issue 14 routing = provider/platform selection and fallback. | Conflating entitlement routing with provider routing is an architectural error. |
| Hosted-credit semantics | Hosted credits are provider-neutral, usage-backed entitlement units computed from structured turn/pass usage metrics through a configurable conversion policy | No flat per-turn decrement; no provider-dollar accounting in entitlement core. Issue 14 supplies provider/platform calibration inputs. |
| Provider targets for v1 | Anthropic direct and OpenRouter | OpenAI direct and Gemini direct are deferred. |
| Provider refusal handling in the pipeline | Typed `ProviderRefusalError` per pass → `REFUSED_BY_PROVIDER`; no retries / fallback / routing in Issue 12c v1 | Resolved during Issue 12c; see ADR-0014. Issue 14 owns refusal-aware routing. |
| Provider refusal reason opacity | `ProviderRefusal.coarse_reason` is captured for audit but advisory only — orchestrator never routes on it | Resolved during Issue 12c; see ADR-0014. Issue 14 may use observed patterns to inform routing without depending on granular reasons. |
| BYOK fallback-pool boundary | BYOK fallback may only use provider credentials/configuration the user supplied. If only one BYOK provider is configured, no fallback exists. | Fallback must never silently cross hosted/BYOK boundaries. |
| RPG dice handling | Two modes: Player rolls / AI rolls | Hidden rolls are hidden from the Sojourner, not the backend. Code generates and records trust-relevant rolls. |
| RPG deterministic rails boundary | Code owns deterministic RPG rails and auditability; the model interprets rules from supplied slices and narrates resolved outcomes | Rules ingestion does not generate executable mechanics. Each supported adjudicated system needs a hand-authored Rules System Adapter. |
| Writing mode structure | Persona-based — Mentors (Chiron, Merlin, Vidura) and Peers (Odin, Athena, Thoth) | No explicit user-facing submode labels; category communicated through persona descriptions. |
| Writing-mode version-history scope | Minimal future-compatible version pointers only in v1 | Full draft branching, restore/rollback, compare views, and manuscript evolution tooling are deferred unless a later issue explicitly scopes them. |
| Branching interaction styles | Three persisted styles: Freeform only; Hybrid freeform + branch cards; True CYOA / choices-only | Interaction style controls the Sojourner input mechanism. |
| Branching cadence / verbosity | Preserved as a separate persisted setup dial: Interactive / Balanced / Immersive | Cadence/verbosity applies to all Branching interaction styles, including Freeform-only. It controls storyteller response density and decision-point pacing, not the Sojourner’s own input verbosity. |
| True CYOA input handling | Explicit branch selection is ordinary story input; branch selection with a small annotation is still a branch choice; explicit OOC remains OOC; attempted freeform story action is invalid and should offer a Hybrid-mode switch | Example: “2, but I do it cautiously” is a valid choice annotation. “I ignore the options and climb the wall” is not ordinary True CYOA input; ask whether to switch to Hybrid. |
| Frontend stack | React + Vite + TypeScript | Svelte is no longer an open option for v1. Issue 19 must not introduce Next.js, SSR, a separate Node application server, or Electron. |
| API ownership | Issue 19 owns the minimal FastAPI API surface needed by the frontend | Exact route shapes remain an Issue 19 implementation design item, but ownership is no longer open. |
| Billing-platform issue placement | Issue 23 — Billing Platform / Payment Integration | Created after Issue 21 and before public launch. It is a commercial launch blocker, not a spine-demo prerequisite. |
| Retrieval-memory ownership and gate | Issue 18 owns ChromaDB retrieval-memory design and implementation, beginning with a mandatory ADR / owner checkpoint before implementation code proceeds | Exact collection schema and retrieval parameters remain open until the Issue 18 ADR is accepted. |
| OOC narrative effect | OOC does not advance story or canon unless a later mode-specific contract defines a safe typed configuration update | The UI provides explicit OOC affordance; manual `[OOC]` remains valid. Branching interaction-style/cadence changes are examples of safe typed config updates. |
| Credit deduction timing | Hosted credits deducted only for `DELIVERED` and `OOC_HANDLED` turns. Safety blocks, contradiction blocks, provider refusals, and pipeline errors do not deduct. | Resolved during Issue 13; see ADR-013. Owner Decision #1. |
| Safety-policy provider whitelist | Anthropic direct: always WHITELISTED + capable via AFTERWORLDS_VERIFIED profile. OpenRouter: whitelist + capability evaluated per-model via `OpenRouterCapabilityRegistry`. Implemented in `CapabilityProfileAwareSafetyPolicy` via `EligibleModelRoute.whitelist_status` and `supports_required_capabilities`. | Resolved during Issue 14a/14b; see adr-014a, adr-014b. |
| Provider capability profiles and fallback eligibility | `AnthropicCapabilityProfile` owns pass→model mapping. `EligibleModelRoute` carries `whitelist_status` + `supports_required_capabilities`. `RefusalFallbackRouter` owns at-most-one-fallback semantics. BYOK pool bounded by configured credentials; no hosted/BYOK boundary crossing. | Resolved during Issue 14a/14b; see adr-014a, adr-014b. OpenRouter cache adapter verification deferred — still open (see Open section). |
| React or Svelte for the initial frontend | Deferred to before Issue 19 per CRD Item 4. All Issues 1–18 are backend/pipeline and are unblocked. | CRD Item 4 establishes this must be resolved before frontend skeleton work (Issue 19). No decision required before Issue 18. |

---

## Open — Acceptable to Resolve During Construction

These are genuinely open. Each has a designated resolution window. Do not resolve early without explicit approval.

---

### OpenRouter Writer context-length floor value and rejection semantics

**Resolve during:** Issue 14 (any remaining 14x sub-issue) or before production whitelist population.

`_WRITER_CONTEXT_LENGTH_FLOOR = 8192` in `_registry.py` is a provisional constant. It gates whether an OpenRouter route is marked `supports_required_capabilities=True` (Safety can be skipped). Routes with `context_length < floor` currently get `supports_required_capabilities=False` and Safety always runs; the route is not rejected.

**Two open questions:**
1. Is 8192 the correct floor for the Writer pass? Too high rejects viable models; too low allows models that will fail mid-story.
2. Should a model with confirmed `context_length < floor` be rejected at route resolution time (`ProviderConfigError`) rather than allowed with Safety always running?

**What resolution requires:** Owner decision on floor value and rejection semantics. Update `_WRITER_CONTEXT_LENGTH_FLOOR` and `resolve_route` step 5 accordingly. Document in ADR-014b or a follow-on decision record.

---

### OpenRouter structured-pass capability pre-validation at route resolution

**Resolve during:** Issue 14 (any remaining 14x sub-issue) or Issue 21 if a defect surfaces.

`resolve_route` in `OpenRouterCapabilityRegistry` evaluates Writer capability only (`supports_text_output` + context length). It does not pre-reject routes where both `supports_tool_use` and `supports_structured_output` are explicitly `False`. Such routes are live but will fail at call time during the Planner or Extractor pass with `ProviderCallError`.

**What resolution requires:** Owner decision on whether pre-catalog rejection at route resolution time (vs. call-time fail-closed) is the correct behavior for structured-pass incapability. If pre-rejection is desired, `resolve_route` needs a separate step for structured-pass capability, a new return axis, or a separate method. Document in ADR-014b.

---

### OpenRouter cache adapter verification

**Resolve during:** Issue 14 (any remaining 14x sub-issue) or before OpenRouter routes enable extended-TTL caching.

ADR-014a Decision 4 and the `_openrouter.py` module docstring note that OpenRouter cache adapter behavior (cross-pass reuse, TTL, cache metric semantics) requires adapter verification before extended-TTL caching is enabled for OpenRouter routes. This verification was not completed in 14a or 14b.

**What resolution requires:** Verify OpenRouter cache behavior for stable-prefix reuse across passes within a turn. Document verified assumptions, update the adapter and ADR-014a/014b. Extended-TTL caching must not be enabled for OpenRouter routes without this verification.

---

### Mode-specific OOC handler selection and final protocol implementation

**Resolve during:** Issues 15 (RPG), 16 (Branching), 17 (Writing).

Issue 12c short-circuits OOC turns away from the ordinary narrative passes and routes them through `WriterService` with the thin v1 placeholder at `/docs/prompts/ooc_handler.md`. The v2 mode prompt contracts now contain OOC sections, but the implementation question remains: how the orchestrator selects or injects the final mode-specific OOC instruction, and whether the placeholder is replaced outright or retained as a generic fallback.

**What resolution requires:** Issues 15–17 must finalize the mode-specific OOC protocol sections and specify how they are selected at runtime. Document the swap in an ADR if the orchestrator’s OOC-handler selection logic changes shape.

---

### Rollover/cap policy for hosted credits

**Resolve before:** Pricing lock (before public launch).

**Why it's open:** Issue 13 preserves separate hosted and top-up credit balances. Whether hosted credits roll over between billing periods, and whether any cap applies to total accumulated credits, is an open product decision. No enforcement logic or schema fields exist for rollover/cap in v1.

**What resolution requires:** Owner decision on rollover period (monthly reset vs. carry-forward), top-up cap (if any), and whether rolled-over included credits are treated differently from top-up credits. Implement enforcement logic and any new schema fields in a follow-on issue after the pricing decision is locked. Document in an ADR.

---

### Exact ChromaDB collection schema and retrieval-memory ADR

**Resolve during:** Issue 18, before implementation code proceeds.

ChromaDB is committed for v1 and Issue 18 owns retrieval-memory design and implementation. The exact collection design remains open: one collection per story vs. shared collections with metadata filtering, embedding model choice, chunking strategy, metadata schema, write triggers, update/delete/reindex behavior, and query construction.

**What resolution requires:** The Issue 18 ADR must define collection naming, metadata fields, chunking policy, embedding strategy/configuration, retrieval defaults, filtering rules, empty-result behavior, write triggers, update/delete/reindex semantics, non-cross-story leakage prevention, and how results enter `RetrievalMemoryProvider` / `StablePrefix.retrieval_memory`. The ADR requires explicit owner approval before implementation code proceeds.

**Constraint:** Context Builder already exposes the retrieval-memory seam. Do not hard-code ChromaDB assumptions into earlier issues.

---

### Exact FastAPI route shapes

**Resolve during:** Issue 19, before route implementation.

Issue 19 owns the minimal FastAPI API surface needed by the React + Vite + TypeScript frontend. Route design is best decided once the backend service layer and frontend shell requirements are stable.

**What resolution requires:** Define route naming conventions, versioning strategy such as `/api/v1/`, request/response payloads for core operations, error envelope shape, and route ownership boundaries. Document in an ADR or in Issue 19 Architecture Notes before implementation begins.

---

### Session resumption UX on cache miss

**Resolve during:** Issue 19 (frontend) or earlier if UX copy must be written before then.

Issue 14a completed the provider/cache technical work. Extended-TTL (1h) cache markers are emitted by default. The product question remains: whether to surface a cold-start resumption to the Sojourner with a visible cue, silently absorb it, or expose it only in usage/billing views.

**What resolution requires:** Decide the UX pattern and document it before Issue 19 implements session-resume flows. This is a product decision, not a cache-correctness decision.

---

### Starter Access package parameters

**Resolve during:** Issue 23, or earlier if pricing copy must be written before then.

Starter Access is retained as an optional paid entry package / trial subscription using normal hosted credits and the full Sojourn pipeline. The exact commercial parameters remain open.

**What resolution requires:** Decide package price, included hosted credits, expiration/renewal behavior, top-up eligibility, upgrade path, refund/support expectations, and whether Starter Access is presented as a trial subscription, one-time starter pack, or both. Ensure no copy or entitlement logic implies a free tier or degraded pipeline.

---

### Hosted-credit conversion policy defaults

**Resolve during:** Issue 13, with calibration inputs revisitable during Issue 14.

The architecture is resolved: hosted credits are provider-neutral, usage-backed units computed from structured pass/turn usage metrics through a configurable conversion policy. The exact default coefficients, rounding rules, reserve behavior, and top-up balance handling still need implementation-time defaults.

**What resolution requires:** Issue 13 must define the credit-conversion policy schema, default coefficients, rounding/precision behavior, handling of missing provider metrics, event logging for credit mutations, and enforcement behavior when credits are exhausted. Issue 14 may later supply provider/platform-specific normalization factors without changing Issue 13 ownership.

---

### Mentor and Peer persona behavioral implementation details

**Resolve during:** Issue 17.

The high-level Writing-mode structure is resolved: personas are divided into Mentors and Peers, with Chiron, Merlin, Vidura, Odin, Athena, and Thoth as the v1 roster. The v2 prompt contract contains concise persona characteristics, but Issue 17 still owns final prompt-injection behavior, tests, and any companion behavioral briefs needed for implementation.

**What resolution requires:** During Issue 17, write implementation-ready behavioral briefs or prompt fragments for all six personas if the prompt contract alone is insufficient. Each brief should define distinctive voice/register, default opening approach, ambiguity handling, category-specific behavior, and tests/fixtures that distinguish personas without exploding the surface area.

---

### Prose parity constraint for Writing mode

**Resolve during:** Issue 17.

The question is whether Mentors and Peers should be constrained to match or approximate the user’s prose output volume per turn, to prevent the AI from taking over the writing. Two sub-questions remain open:

1. **Per-turn vs. running-total parity:** Per-turn parity is simpler but can feel mechanical. Running-total parity is more forgiving but requires session-level tracking.
2. **Scope — Peers only or all personas:** Parity makes clean sense for Peers, who are co-writers. It is murkier for Mentors, whose output is often feedback and craft instruction rather than prose.

**What resolution requires:** Decide on the parity model, the scope, and how Mentor feedback is measured differently from generated prose. If implemented, store the required counters in Writing session state and document how they are updated.

---

## How to Add a New Unknown

When construction surfaces a decision that is not covered by existing docs and should not be resolved unilaterally:

1. Add it to the Open section above with: what it is, why it is open, what resolution requires, and when it must be resolved.
2. Note it in the PR description as a Known Unknown surfaced during implementation.
3. Do not proceed with a local resolution — pause for owner decision.

---

*This document is a canonical architecture artifact. Updates require a PR with an Architecture Notes section. Resolving a Known Unknown during construction requires a corresponding ADR in `/docs/decisions/` unless the owner explicitly classifies the decision as already covered by the Design doc / CRD record.*
