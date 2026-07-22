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
| ChromaDB collection schema | Collection topology, metadata schema, chunking, embedding, retrieval defaults, eligibility/write-trigger rules, and update/delete/reindex semantics resolved by ADR-018. RPG setup-confirmation turn-time classification required a new narrow sidecar carrier (`rpg_turn_retrieval_markers`) per the Owner Decision recorded in ADR-018, since no existing signal qualified. | Resolved during CRD Issue 18 Phase 1; see `/docs/decisions/adr-018-retrieval-memory.md`. Implementation (Phase 2) proceeds only after explicit owner acceptance of ADR-018. |
| OOC narrative effect | OOC does not advance story or canon unless a later mode-specific contract defines a safe typed configuration update | The UI provides explicit OOC affordance; manual `[OOC]` remains valid. Branching interaction-style/cadence changes are examples of safe typed config updates. |
| Credit deduction timing | Hosted credits deducted only for `DELIVERED` and `OOC_HANDLED` turns. Safety blocks, contradiction blocks, provider refusals, and pipeline errors do not deduct. | Resolved during Issue 13; see ADR-013. Owner Decision #1. |
| Safety-policy provider whitelist | Anthropic direct: always WHITELISTED + capable via AFTERWORLDS_VERIFIED profile. OpenRouter: whitelist + capability evaluated per-model via `OpenRouterCapabilityRegistry`. Implemented in `CapabilityProfileAwareSafetyPolicy` via `EligibleModelRoute.whitelist_status` and `supports_required_capabilities`. | Resolved during Issue 14a/14b; see adr-014a, adr-014b. |
| Provider capability profiles and fallback eligibility | `AnthropicCapabilityProfile` owns pass→model mapping. `EligibleModelRoute` carries `whitelist_status` + `supports_required_capabilities`. `RefusalFallbackRouter` owns at-most-one-fallback semantics. BYOK pool bounded by configured credentials; no hosted/BYOK boundary crossing. | Resolved during Issue 14a/14b; see adr-014a, adr-014b. OpenRouter cache adapter verification deferred — still open (see Open section). |
| OpenRouter context-length floor value and rejection semantics | `resolve_route` rejects routes with known `context_length < writer_context_length_floor` (ProviderConfigError). Floor is a constructor parameter on `OpenRouterCapabilityRegistry`; default `_WRITER_CONTEXT_LENGTH_FLOOR = 8192` is provisional. `context_length=None` does not reject. | Resolved during Issue 14b; see adr-014b Decision 4. The correct production floor value remains an operator configuration decision. |
| OpenRouter structured-pass capability pre-validation at route resolution | `resolve_route` rejects routes where `supports_tool_use is False AND supports_structured_output is False` (ProviderConfigError). Only explicit False triggers rejection; None fields fail safe. | Resolved during Issue 14b; see adr-014b Decision 11. |
| React for the initial frontend | Deferred to before Issue 19 per CRD Item 4. All Issues 1–18 are backend/pipeline and are unblocked. | CRD Item 4 establishes this must be resolved before frontend skeleton work (Issue 19). No decision required before Issue 18. |

---

## Open — Acceptable to Resolve During Construction

These are genuinely open. Each has a designated resolution window. Do not resolve early without explicit approval.

---

### OpenRouter cache adapter verification

**Resolve during:** Issue 14 (any remaining 14x sub-issue) or before OpenRouter routes enable extended-TTL caching.

ADR-014a Decision 4 and the `_openrouter.py` module docstring note that OpenRouter cache adapter behavior (cross-pass reuse, TTL, cache metric semantics) requires adapter verification before extended-TTL caching is enabled for OpenRouter routes. This verification was not completed in 14a or 14b.

**What resolution requires:** Verify OpenRouter cache behavior for stable-prefix reuse across passes within a turn. Document verified assumptions, update the adapter and ADR-014a/014b. Extended-TTL caching must not be enabled for OpenRouter routes without this verification.

---

### Mode-specific OOC handler selection and final protocol implementation

**RESOLVED during Issue 17.** All three modes now have dedicated OOC handlers.

**RPG resolution (Issue 15):** Implemented as a distinct mode-specific handler for RPG mode via `docs/prompts/rpg_ooc_handler.md`. Replaces the 12c placeholder when `StoryMode.RPG` is active. Answers rules, configuration, setup, and clarification questions; advances no story; mutates no canon; routes configuration changes through typed paths. The orchestrator `_run_ooc()` now accepts `story_mode` and selects between `rpg_ooc_handler.md` (RPG mode) and `ooc_handler.md` (other modes). See ADR-015 Decision 11 and `/docs/prompts/rpg_ooc_handler.md`.

**Branching resolution (Issue 16):** Implemented as a distinct mode-specific handler for Branching mode via `docs/prompts/branching_ooc_handler.md`. When `StoryMode.BRANCHING` is active, the orchestrator `_run_ooc()` now selects `branching_ooc_handler.md`. Handles interaction-style/cadence/length configuration updates (transaction-scoped to `OOC_HANDLED`), Branching Mode platform questions, and True CYOA rejection guidance. See ADR-016 Decisions 4 and the OOC handler Known Unknown section.

**Writing resolution (Issue 17):** Implemented via `docs/prompts/writing_ooc_handler.md`. When `StoryMode.WRITING` is active, the orchestrator `_run_ooc()` selects `writing_ooc_handler.md`. Handles persona changes, authoring-control updates (critique intensity, style density, form, tense, POV, etc.), platform questions, and Writing Mode config extraction via `WritingOocConfigExtractorService` (transaction-scoped, best-effort). See ADR-017.

---

### Rollover/cap policy for hosted credits

**Resolve before:** Pricing lock (before public launch).

**Why it's open:** Issue 13 preserves separate hosted and top-up credit balances. Whether hosted credits roll over between billing periods, and whether any cap applies to total accumulated credits, is an open product decision. No enforcement logic or schema fields exist for rollover/cap in v1.

**What resolution requires:** Owner decision on rollover period (monthly reset vs. carry-forward), top-up cap (if any), and whether rolled-over included credits are treated differently from top-up credits. Implement enforcement logic and any new schema fields in a follow-on issue after the pricing decision is locked. Document in an ADR.

---

### Exact ChromaDB collection schema and retrieval-memory ADR

**RESOLVED (Phase 1) during CRD Issue 18.** ADR-018 defines collection topology, metadata schema,
chunking policy, embedding strategy, retrieval defaults, write-trigger/eligibility rules (including
the RPG turn-category marker Owner Decision), mutation/reindex semantics, and the D9 cache-boundary
resolution of ADR-0010 Decision 4. See `/docs/decisions/adr-018-retrieval-memory.md`. Implementation
(Phase 2) proceeds only after explicit owner acceptance of ADR-018 on the Phase 1 PR.

**Constraint (still binding):** Context Builder already exposes the retrieval-memory seam. Do not
hard-code ChromaDB assumptions into earlier issues.

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

**RESOLVED during Issue 17.** All six personas have implementation-ready prompt fragments, behavioral briefs, and registry profiles in `src/afterworlds/modes/personas/profiles/writing_personas.v1.json`. Each profile includes `prompt_fragment`, `signature_move`, `opening_question_style`, `negative_constraints`, and `demeanor_tags`. The `WritingContextRenderer` injects the resolved persona fragment into the stable prefix once per turn. See ADR-017 Decision 2.

---

### Prose parity constraint for Writing mode

**DEFERRED — out of scope for Issue 17.** ADR-017 Decision 13 explicitly defers prose parity tracking. The decision record: v1 does not enforce per-turn or running-total prose parity. The persona prompt fragments include guidance that naturally limits AI output scope (e.g., negative constraints, Peer vs. Mentor orientation), but no counter is stored in `WritingSessionState` and no enforcement gate exists in the pipeline. A future issue may revisit if user research indicates AI output volume consistently overwhelms Sojourner authorship.

**What resolution requires if revisited:** Decide parity model (per-turn vs. running-total), scope (Peers only vs. all), and measurement unit. Add counter fields to `WritingSessionState`, update migration, and add enforcement in the orchestrator or context renderer. Requires a new ADR or ADR-017 amendment.

---

### True CYOA intent-classifier precision (ClassificationHints not wired)

**Resolve during:** A future issue after Issue 16 (target: Issue 20 or whichever issue next touches the classifier).

**Surfaced during:** Issue 16.

Issue 16 ships the `INTERACTION_REJECTED` disposition for True CYOA invalid freeform input. The v1 rejection predicate is: reject if `intent_type not in {branch_choice, ooc}`. However, the classifier (CRD Issue 7) does not receive `ClassificationHints` about the current interaction style or presented branch options.

**V1 limitation:** A Sojourner in True CYOA mode who writes "Cross the bridge" — even when "cross the bridge" paraphrases a presented option — will be rejected because the classifier returns `in_character_action`, not `branch_choice`. `branch_choice` is only emitted for explicit selection language ("I choose option 2", "Take the second option", "Option 1"). This is a precision gap, not a correctness gap: the safest behavior in True CYOA is explicit rejection of ambiguous input.

**What resolution requires:** Wire `ClassificationHints` (containing the presented branch-option texts and `interaction_style=TRUE_CYOA`) into the classifier call when `story_mode is BRANCHING`. The classifier uses the hints to detect when freeform input clearly matches an offered option by paraphrase and emits `branch_choice` in that case. Requires owner decision on whether the classifier should do fuzzy matching or only exact/near-exact option-text matching. Document in an ADR or Architecture Notes for the owning issue.

---

### Pending-roll rewind/cancel policy

**Resolve during:** A future issue after Issue 15b, when at minimum one supported rewind/cancel flow exists.

**Surfaced during:** Issue 15. **Touched, not resolved, during Issue 15b.**

Issue 15 shipped a v1 block-and-redirect policy: if a new in-character action arrives while a
`PendingRollRequest` is outstanding, the orchestrator blocks and redirects the Sojourner to the pending
roll. It does not cancel, supersede, or expire the request. `PendingRollRequest.status` has `cancelled`
and `expired` as valid literals for schema compatibility, but no code path activates them in v1.

Issue 15b (ADR-015b) generalizes the block-and-redirect gate from one pending-roll row to any unresolved
`ActionResolutionSequence` state — pending roll, pending mechanical decision, or `ready_for_narration` —
but explicitly does not resolve this unknown (15b-33): cancellation, expiration, rewind,
retry/regenerate, and supersession all remain deferred. `PendingRollStatus.CANCELLED`/`EXPIRED` stay
dormant in the revised schema for the same reason (15b-8). Issue 15b also adds one directly related open
question this item now covers: cleanup policy for an **abandoned `ready_for_narration` sequence** (one
that reached readiness but was never resumed) is unresolved and falls under the same future-issue
resolution window as rewind/cancel, since both are lifecycle-termination policy for the same persisted
unit.

**What resolution requires:** Decide at minimum one of: (a) whether the Sojourner can explicitly cancel a
pending roll or an active/ready sequence and what the mechanical/narrative consequence is; (b) whether a
pending roll or an abandoned ready sequence expires after N turns or N minutes and what cleanup applies;
(c) whether a GM-initiated scene transition supersedes a pending roll or sequence. Implement the chosen
policy, add or remove `cancelled`/`expired` lifecycle transitions accordingly, and test rollback for each
non-consumed termination path.

---

### Parameterized adjustments (spell-slot-level upcasting, variable-amount resource recovery)

**Resolve during:** A future issue, only if the owner pulls upcasting or similar variable-amount mechanics into v1 scope.

**Surfaced during:** Issue 15b Phase 2 bounded-d20 coverage inventory, against the curated SRD 5.2.1 package (`data/srd/srd_5_2_1_structured.json`).

The coverage inventory found two mechanic classes in the curated v1 package that need a genuinely typed parameter, not a fixed `option_id` selection: spell-slot-level selection for upcasting (8+ of the 16 curated spells scale dice count/targets by the chosen casting slot level, e.g. Magic Missile: +1 dart per slot level above 1st) and Arcane Recovery (variable-amount slot recovery, player-chosen). Per 15b-10, any adjustment option requiring parameters beyond a stable `option_id` requires an ADR-015b amendment before it ships. Phase 2 does not build this: base-level casting of all 16 curated spells is fully supported; upcasting and Arcane Recovery are declared explicitly unsupported and the adapter fails loud (not a silent `undetermined`, not a silent base-level fallback) if either is invoked. A per-slot-level enumerated `option_id` set was considered and rejected as parameter-laundering — the value flows into `RollTerm.count` arithmetic, which is exactly what 15b-10 gates.

**What resolution requires:** Owner decision to pull upcasting/variable-resource-recovery mechanics into scope; an ADR-015b amendment defining a typed `RollAdjustmentOption` extension (e.g. `chosen_slot_level: int`, server-validated against the sheet's available slots) before any implementation.

---

### Rules Package carries no structured numeric/mechanical data (DC, dice formulas)

**Resolve during:** Whichever future issue next revises Rules Package ingestion/schema (Issue 5a/5b territory).

**Surfaced during:** Issue 15b Phase 2 implementation, while wiring `D20RulesSystemAdapter._verify_dc` and evaluating multi-die damage-pool generation against the curated SRD 5.2.1 package.

This is one defect family with two confirmed instances, found via sibling audit after the first instance surfaced:

1. **No DC field anywhere.** `SpellEntity`, `ConditionEntity`, `StatBlockEntity`, and `ActionEntity` (`models/rules_package.py`) carry no `dc`/`difficulty_class`/`save_dc` field of any kind. `RuleOverride` is a non-mutating layered content-patch channel for chunks/entities, not a per-call numeric-DC channel. Consequently `_verify_dc` returns `None` for every call in v1 — not a temporary implementation gap, but structurally unavoidable until Rules Package schema carries a DC field. Every DC-gated roll purpose (attack, saving throw, ability check, skill check, contested) resolves to `outcome="undetermined"` by construction; this is ADR-015 Decision 7's documented fallback behavior operating correctly, not a bug, but it means Issue 15b's Critical Acceptance Matrix item 1 ("prove a representative `1d20` attack") is satisfied at the mechanics/unit level (dice roll, modifier assembly, total, and the `_compute_outcome` success/failure/crit branches are all provably correct given an explicit `dc`), not at the "produces a non-undetermined verdict against real curated content" level.
2. **No structured dice/damage data.** The curated package's mechanical entities store dice formulas as unstructured prose within `structured_data.effect_description`/`actions` string fields (e.g. literally `"8d6 fire damage"` as text), not as a parseable `RollTerm`-shaped field. This means the bounded d20 adapter cannot auto-generate a real multi-die damage/healing `RollInstructionSnapshot` (e.g. Fireball's `8d6`, the Young Red Dragon's `2d10+6` bite) from `RollProposal` + sheet + rule slice alone — there is no source field for the adapter to read the dice shape from. Issue 15b's structured `RollTerm`/`RollInstructionSnapshot` contract itself fully **represents** these pools (summed/mixed/repeated pools were built and are unit-tested against hand-constructed instructions, proving the coverage-inventory's representability claim); what's blocked is adapter-side **generation** of such an instruction from today's Rules Package content for anything beyond the existing 1d20-family check/save/attack generation, which stays sheet-derived and unaffected by this gap.

**What resolution requires:** A Rules Package schema change (owned by whichever issue next revises ingestion — Issue 5a/5b territory, out of scope for Issue 15b, which owns roll instruction structure, not Rules Package data modeling) adding structured numeric fields — at minimum a DC-bearing field on entities that need one, and a structured dice-term representation (or a parseable canonical dice-string field) on entities with damage/healing effects — so ingestion can populate machine-readable mechanical data instead of only prose. Until then, DC-gated outcomes remain `undetermined` by construction and damage/healing/duration `RollInstructionSnapshot`s for curated-package content must be hand-supplied rather than adapter-generated.

---

## How to Add a New Unknown

When construction surfaces a decision that is not covered by existing docs and should not be resolved unilaterally:

1. Add it to the Open section above with: what it is, why it is open, what resolution requires, and when it must be resolved.
2. Note it in the PR description as a Known Unknown surfaced during implementation.
3. Do not proceed with a local resolution — pause for owner decision.

---

*This document is a canonical architecture artifact. Updates require a PR with an Architecture Notes section. Resolving a Known Unknown during construction requires a corresponding ADR in `/docs/decisions/` unless the owner explicitly classifies the decision as already covered by the Design doc / CRD record.*
