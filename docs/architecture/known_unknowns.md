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
| Contradiction checker approach | Sequential gate on Writer output, small/fast model | Checker evaluates generated prose, not input context; see CRD Item 7 and CRD Issue 11. |
| Intent classifier approach | Lightweight model call | Classifies before context assembly; see CRD Issue 7. |
| Business model and pricing shape | Metered hosted subscription with credits + BYOK perpetual license + first-year Cloud Services + optional Starter Access | See CRD Item 8 and Design Section 8. Exact plan prices, credit quantities, and payment-provider implementation remain separate launch/business decisions. |
| Starter Access | Retained as an optional paid entry package / trial subscription using normal hosted credits and the full Sojourn pipeline | Starter Access is not a free tier, degraded tier, or reduced-continuity path. It may be abandoned later if a better trial model replaces it, but preserving it causes no architectural harm. |
| Story Bible schema | Committed | Static / dynamic / provisional partitions, Events Ledger, Locked/Forbidden Facts; see CRD Issue 4. |
| Events Ledger tiered inclusion N value | 15 (configurable constant) | Resolved during CRD Issue 4. Implemented as `EVENTS_LEDGER_N = 15` in `services/story_bible.py`. Tune with testing. See ADR-0005. |
| Rolling summary compression trigger value (N turns) | Provisional N = 10 (configurable constant); empirical finalization deferred to CRD Issue 8 | Escape hatch invoked during CRD Issue 6: Context Builder not yet wired; stable-prefix-pressure evidence unavailable. Implemented as `ROLLING_SUMMARY_N = 10` in `services/rolling_summary.py`. Must be finalized in CRD Issue 8 — not deferred past CRD Issue 8. See ADR-0009. |
| Significance flagging criteria for Events Ledger | Seven-value enum; six qualify for always-include | Resolved during CRD Issue 4. Always-include: CHARACTER_DEATH, LOCKED_FACT_ESTABLISHED, MAJOR_PLOT_TURN, RELATIONSHIP_CHANGE, WORLD_STATE_CHANGE, FORBIDDEN_FACT_ESTABLISHED. ROUTINE is the only non-always-include value. See ADR-0005. |
| Mode prompt contracts | Written and revised to v2 | Versioned `.md` files live in `/docs/prompts/`. Mode-contract content changes belong to Issues 15–17 unless a later dedicated issue explicitly scopes them. |
| BYOK commercial structure | Perpetual license + first year of Cloud Services included; optional annual renewal thereafter | License and services must not be collapsed in code, UX language, entitlement logic, support views, or export/deletion handling. |
| Cloud Services scope | Hosted persistence, sync, backup, remote access, hosted ingestion, and any hosted runtime dependent on Afterworlds server resources | CRD Issue 13 enforcement must cover all Cloud Services-dependent resources, not only hosted generation. |
| CRD Issue 13 vs. CRD Issue 14 routing boundary | CRD Issue 13 routing = access-path and entitlement enforcement. CRD Issue 14 routing = provider/platform selection and fallback. | Conflating entitlement routing with provider routing is an architectural error. |
| Hosted-credit semantics | Hosted credits are provider-neutral, usage-backed entitlement units computed from structured turn/pass usage metrics through a configurable conversion policy | No flat per-turn decrement; no provider-dollar accounting in entitlement core. CRD Issue 14 supplies provider/platform calibration inputs. |
| Provider targets for v1 | Anthropic direct and OpenRouter | OpenAI direct and Gemini direct are deferred. |
| Provider refusal handling in the pipeline | Typed `ProviderRefusalError` per pass → `REFUSED_BY_PROVIDER`; no retries / fallback / routing in CRD Issue 12c v1 | Resolved during CRD Issue 12c; see ADR-0014. CRD Issue 14 owns refusal-aware routing. |
| Provider refusal reason opacity | `ProviderRefusal.coarse_reason` is captured for audit but advisory only — orchestrator never routes on it | Resolved during CRD Issue 12c; see ADR-0014. CRD Issue 14 may use observed patterns to inform routing without depending on granular reasons. |
| BYOK fallback-pool boundary | BYOK fallback may only use provider credentials/configuration the user supplied. If only one BYOK provider is configured, no fallback exists. | Fallback must never silently cross hosted/BYOK boundaries. |
| RPG dice handling | Two modes: Player rolls / AI rolls | Hidden rolls are hidden from the Sojourner, not the backend. Code generates and records trust-relevant rolls. |
| RPG deterministic rails boundary | Code owns deterministic RPG rails and auditability; the model interprets rules from supplied slices and narrates resolved outcomes | Rules ingestion does not generate executable mechanics. Each supported adjudicated system needs a hand-authored Rules System Adapter. |
| Writing mode structure | Persona-based — Mentors (Chiron, Merlin, Vidura) and Peers (Odin, Athena, Thoth) | No explicit user-facing submode labels; category communicated through persona descriptions. |
| Writing-mode version-history scope | Minimal future-compatible version pointers only in v1 | Full draft branching, restore/rollback, compare views, and manuscript evolution tooling are deferred unless a later issue explicitly scopes them. |
| Branching interaction styles | Three persisted styles: Freeform only; Hybrid freeform + branch cards; True CYOA / choices-only | Interaction style controls the Sojourner input mechanism. |
| Branching cadence / verbosity | Preserved as a separate persisted setup dial: Interactive / Balanced / Immersive | Cadence/verbosity applies to all Branching interaction styles, including Freeform-only. It controls storyteller response density and decision-point pacing, not the Sojourner’s own input verbosity. |
| True CYOA input handling | Explicit branch selection is ordinary story input; branch selection with a small annotation is still a branch choice; explicit OOC remains OOC; attempted freeform story action is invalid and should offer a Hybrid-mode switch | Example: “2, but I do it cautiously” is a valid choice annotation. “I ignore the options and climb the wall” is not ordinary True CYOA input; ask whether to switch to Hybrid. |
| Frontend stack | React + Vite + TypeScript | Svelte is no longer an open option for v1. CRD Issue 19 must not introduce Next.js, SSR, a separate Node application server, or Electron. |
| API ownership | CRD Issue 19 owns the minimal FastAPI API surface needed by the frontend | Exact route shapes remain a CRD Issue 19 implementation design item, but ownership is no longer open. |
| Billing-platform issue placement | CRD Issue 23 — Billing Platform / Payment Integration | Created after CRD Issue 21 and before public launch. It is a commercial launch blocker, not a spine-demo prerequisite. |
| Retrieval-memory ownership and gate | CRD Issue 18 owns ChromaDB retrieval-memory design and implementation, beginning with a mandatory ADR / owner checkpoint before implementation code proceeds | Exact collection schema and retrieval parameters remain open until the CRD Issue 18 ADR is accepted. |
| ChromaDB collection schema | Collection topology, metadata schema, chunking, embedding, retrieval defaults, eligibility/write-trigger rules, and update/delete/reindex semantics resolved by ADR-018. RPG setup-confirmation turn-time classification required a new narrow sidecar carrier (`rpg_turn_retrieval_markers`) per the Owner Decision recorded in ADR-018, since no existing signal qualified. | Resolved during CRD Issue 18 Phase 1; see `/docs/decisions/adr-018-retrieval-memory.md`. Implementation (Phase 2) proceeds only after explicit owner acceptance of ADR-018. |
| OOC narrative effect | OOC does not advance story or canon unless a later mode-specific contract defines a safe typed configuration update | The UI provides explicit OOC affordance; manual `[OOC]` remains valid. Branching interaction-style/cadence changes are examples of safe typed config updates. |
| Credit deduction timing | Hosted credits deducted only for `DELIVERED` and `OOC_HANDLED` turns. Safety blocks, contradiction blocks, provider refusals, and pipeline errors do not deduct. | Resolved during CRD Issue 13; see ADR-013. Owner Decision #1. |
| Safety-policy provider whitelist | Anthropic direct: always WHITELISTED + capable via AFTERWORLDS_VERIFIED profile. OpenRouter: whitelist + capability evaluated per-model via `OpenRouterCapabilityRegistry`. Implemented in `CapabilityProfileAwareSafetyPolicy` via `EligibleModelRoute.whitelist_status` and `supports_required_capabilities`. | Resolved during CRD Issue 14a/14b; see adr-014a, adr-014b. |
| Provider capability profiles and fallback eligibility | `AnthropicCapabilityProfile` owns pass→model mapping. `EligibleModelRoute` carries `whitelist_status` + `supports_required_capabilities`. `RefusalFallbackRouter` owns at-most-one-fallback semantics. BYOK pool bounded by configured credentials; no hosted/BYOK boundary crossing. | Resolved during CRD Issue 14a/14b; see adr-014a, adr-014b. OpenRouter cache adapter verification deferred — still open (see Open section). |
| OpenRouter context-length floor value and rejection semantics | `resolve_route` rejects routes with known `context_length < writer_context_length_floor` (ProviderConfigError). Floor is a constructor parameter on `OpenRouterCapabilityRegistry`; default `_WRITER_CONTEXT_LENGTH_FLOOR = 8192` is provisional. `context_length=None` does not reject. | Resolved during CRD Issue 14b; see adr-014b Decision 4. The correct production floor value remains an operator configuration decision. |
| OpenRouter structured-pass capability pre-validation at route resolution | `resolve_route` rejects routes where `supports_tool_use is False AND supports_structured_output is False` (ProviderConfigError). Only explicit False triggers rejection; None fields fail safe. | Resolved during CRD Issue 14b; see adr-014b Decision 11. |
| React for the initial frontend | Deferred to before CRD Issue 19 per CRD Item 4. All Issues 1–18 are backend/pipeline and are unblocked. | CRD Item 4 establishes this must be resolved before frontend skeleton work (CRD Issue 19). No decision required before CRD Issue 18. |

---

## Open — Acceptable to Resolve During Construction

These are genuinely open. Each has a designated resolution window. Do not resolve early without explicit approval.

---

### OpenRouter cache adapter verification

**Resolve during:** CRD Issue 14 (any remaining 14x sub-issue) or before OpenRouter routes enable extended-TTL caching.

ADR-014a Decision 4 and the `_openrouter.py` module docstring note that OpenRouter cache adapter behavior (cross-pass reuse, TTL, cache metric semantics) requires adapter verification before extended-TTL caching is enabled for OpenRouter routes. This verification was not completed in 14a or 14b.

**What resolution requires:** Verify OpenRouter cache behavior for stable-prefix reuse across passes within a turn. Document verified assumptions, update the adapter and ADR-014a/014b. Extended-TTL caching must not be enabled for OpenRouter routes without this verification.

---

### Mode-specific OOC handler selection and final protocol implementation

**RESOLVED during CRD Issue 17.** All three modes now have dedicated OOC handlers.

**RPG resolution (CRD Issue 15):** Implemented as a distinct mode-specific handler for RPG mode via `docs/prompts/rpg_ooc_handler.md`. Replaces the 12c placeholder when `StoryMode.RPG` is active. Answers rules, configuration, setup, and clarification questions; advances no story; mutates no canon; routes configuration changes through typed paths. The orchestrator `_run_ooc()` now accepts `story_mode` and selects between `rpg_ooc_handler.md` (RPG mode) and `ooc_handler.md` (other modes). See ADR-015 Decision 11 and `/docs/prompts/rpg_ooc_handler.md`.

**Branching resolution (CRD Issue 16):** Implemented as a distinct mode-specific handler for Branching mode via `docs/prompts/branching_ooc_handler.md`. When `StoryMode.BRANCHING` is active, the orchestrator `_run_ooc()` now selects `branching_ooc_handler.md`. Handles interaction-style/cadence/length configuration updates (transaction-scoped to `OOC_HANDLED`), Branching Mode platform questions, and True CYOA rejection guidance. See ADR-016 Decisions 4 and the OOC handler Known Unknown section.

**Writing resolution (CRD Issue 17):** Implemented via `docs/prompts/writing_ooc_handler.md`. When `StoryMode.WRITING` is active, the orchestrator `_run_ooc()` selects `writing_ooc_handler.md`. Handles persona changes, authoring-control updates (critique intensity, style density, form, tense, POV, etc.), platform questions, and Writing Mode config extraction via `WritingOocConfigExtractorService` (transaction-scoped, best-effort). See ADR-017.

---

### Rollover/cap policy for hosted credits

**Resolve before:** Pricing lock (before public launch).

**Why it's open:** CRD Issue 13 preserves separate hosted and top-up credit balances. Whether hosted credits roll over between billing periods, and whether any cap applies to total accumulated credits, is an open product decision. No enforcement logic or schema fields exist for rollover/cap in v1.

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

**Resolve during:** CRD Issue 19, before route implementation.

CRD Issue 19 owns the minimal FastAPI API surface needed by the React + Vite + TypeScript frontend. Route design is best decided once the backend service layer and frontend shell requirements are stable.

**What resolution requires:** Define route naming conventions, versioning strategy such as `/api/v1/`, request/response payloads for core operations, error envelope shape, and route ownership boundaries. Document in an ADR or in CRD Issue 19 Architecture Notes before implementation begins.

---

### Session resumption UX on cache miss

**Resolve during:** CRD Issue 19 (frontend) or earlier if UX copy must be written before then.

CRD Issue 14a completed the provider/cache technical work. Extended-TTL (1h) cache markers are emitted by default. The product question remains: whether to surface a cold-start resumption to the Sojourner with a visible cue, silently absorb it, or expose it only in usage/billing views.

**What resolution requires:** Decide the UX pattern and document it before CRD Issue 19 implements session-resume flows. This is a product decision, not a cache-correctness decision.

---

### Starter Access package parameters

**Resolve during:** CRD Issue 23, or earlier if pricing copy must be written before then.

Starter Access is retained as an optional paid entry package / trial subscription using normal hosted credits and the full Sojourn pipeline. The exact commercial parameters remain open.

**What resolution requires:** Decide package price, included hosted credits, expiration/renewal behavior, top-up eligibility, upgrade path, refund/support expectations, and whether Starter Access is presented as a trial subscription, one-time starter pack, or both. Ensure no copy or entitlement logic implies a free tier or degraded pipeline.

---

### Hosted-credit conversion policy defaults

**Resolve during:** CRD Issue 13, with calibration inputs revisitable during CRD Issue 14.

The architecture is resolved: hosted credits are provider-neutral, usage-backed units computed from structured pass/turn usage metrics through a configurable conversion policy. The exact default coefficients, rounding rules, reserve behavior, and top-up balance handling still need implementation-time defaults.

**What resolution requires:** CRD Issue 13 must define the credit-conversion policy schema, default coefficients, rounding/precision behavior, handling of missing provider metrics, event logging for credit mutations, and enforcement behavior when credits are exhausted. CRD Issue 14 may later supply provider/platform-specific normalization factors without changing CRD Issue 13 ownership.

---

### Mentor and Peer persona behavioral implementation details

**RESOLVED during CRD Issue 17.** All six personas have implementation-ready prompt fragments, behavioral briefs, and registry profiles in `src/afterworlds/modes/personas/profiles/writing_personas.v1.json`. Each profile includes `prompt_fragment`, `signature_move`, `opening_question_style`, `negative_constraints`, and `demeanor_tags`. The `WritingContextRenderer` injects the resolved persona fragment into the stable prefix once per turn. See ADR-017 Decision 2.

---

### Prose parity constraint for Writing mode

**DEFERRED — out of scope for CRD Issue 17.** ADR-017 Decision 13 explicitly defers prose parity tracking. The decision record: v1 does not enforce per-turn or running-total prose parity. The persona prompt fragments include guidance that naturally limits AI output scope (e.g., negative constraints, Peer vs. Mentor orientation), but no counter is stored in `WritingSessionState` and no enforcement gate exists in the pipeline. A future issue may revisit if user research indicates AI output volume consistently overwhelms Sojourner authorship.

**What resolution requires if revisited:** Decide parity model (per-turn vs. running-total), scope (Peers only vs. all), and measurement unit. Add counter fields to `WritingSessionState`, update migration, and add enforcement in the orchestrator or context renderer. Requires a new ADR or ADR-017 amendment.

---

### True CYOA intent-classifier precision (ClassificationHints not wired)

**Resolve during:** A future issue after CRD Issue 16 (target: CRD Issue 20 or whichever issue next touches the classifier).

**Surfaced during:** CRD Issue 16.

CRD Issue 16 ships the `INTERACTION_REJECTED` disposition for True CYOA invalid freeform input. The v1 rejection predicate is: reject if `intent_type not in {branch_choice, ooc}`. However, the classifier (CRD Issue 7) does not receive `ClassificationHints` about the current interaction style or presented branch options.

**V1 limitation:** A Sojourner in True CYOA mode who writes "Cross the bridge" — even when "cross the bridge" paraphrases a presented option — will be rejected because the classifier returns `in_character_action`, not `branch_choice`. `branch_choice` is only emitted for explicit selection language ("I choose option 2", "Take the second option", "Option 1"). This is a precision gap, not a correctness gap: the safest behavior in True CYOA is explicit rejection of ambiguous input.

**What resolution requires:** Wire `ClassificationHints` (containing the presented branch-option texts and `interaction_style=TRUE_CYOA`) into the classifier call when `story_mode is BRANCHING`. The classifier uses the hints to detect when freeform input clearly matches an offered option by paraphrase and emits `branch_choice` in that case. Requires owner decision on whether the classifier should do fuzzy matching or only exact/near-exact option-text matching. Document in an ADR or Architecture Notes for the owning issue.

---

### Pending-roll rewind/cancel policy

**Resolve during:** A future issue after CRD Issue 15b, when at minimum one supported rewind/cancel flow exists.

**Surfaced during:** CRD Issue 15. **Touched, not resolved, during CRD Issue 15b.**

CRD Issue 15 shipped a v1 block-and-redirect policy: if a new in-character action arrives while a
`PendingRollRequest` is outstanding, the orchestrator blocks and redirects the Sojourner to the pending
roll. It does not cancel, supersede, or expire the request. `PendingRollRequest.status` has `cancelled`
and `expired` as valid literals for schema compatibility, but no code path activates them in v1.

CRD Issue 15b (ADR-015b) generalizes the block-and-redirect gate from one pending-roll row to any unresolved
`ActionResolutionSequence` state — pending roll, pending mechanical decision, or `ready_for_narration` —
but explicitly does not resolve this unknown (15b-33): cancellation, expiration, rewind,
retry/regenerate, and supersession all remain deferred. `PendingRollStatus.CANCELLED`/`EXPIRED` stay
dormant in the revised schema for the same reason (15b-8). CRD Issue 15b also adds one directly related open
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

### Rules Package carries no structured numeric/mechanical data (DC, dice formulas)

**RESOLVED (architecture) by ADR-005c.** See `/docs/decisions/adr-005c-rules-authority-repair.md`. The
architectural question — how DC and dice-term authority should be modeled and bound so an adapter can
execute against real Rules Package content, and why that authority must never silently fall back to
prose, retrieval, or model inference — is resolved by ADR-005c (Decisions 1, 2, 4, 5, 6).
**Source-corpus layer implemented by CRD Issue 5c (#132).** The authoritative full-corpus ingestion,
frozen source ledger, frozen reconciliation policy, deterministic reconciliation, source-to-corpus
concordance, byte-for-byte reproducible acyclic build, and corpus-publication gate are delivered under
ADR-005c Completion Contract A. (R18 / CRD Issue 5c Rev7 / CRD Issue 18 Rev6: the former *strict legacy
quarantine* — a repo/runtime zero-reachability scan + publication-time legacy check — was superseded by a
breaking pre-release clean baseline: the incomplete legacy SQL package is deleted by migration 0018, the
obsolete structured JSON and its loaders are deleted, and the development Chroma store is reset in full
once before the corrected corpus is rebuilt.)
**Amended 2026-08-03 — operational reliability.** CRD Issue 5c is now judged by operational reliability
rather than adversarial or forensic proof. Full-corpus ingestion, faithful and citable source records,
concordance, stable immutable releases, meaningful-change versioning, accidental-corruption and
stale-reuse detection, fail-closed publication, and rebuildability all remain binding. The "byte-for-byte
reproducible acyclic build" phrasing above describes the originally specified proof architecture and is
no longer a governing requirement; downstream CRD Issue 5d verifies a narrow 5c-owned operational seam
instead of reconstructing 5c's publication history. See
`/docs/decisions/adr-005c-operational-reliability-amendment.md`.

**Scope of the baseline reset (owner decision, 2026-07-29).** That reset is implemented
**only** as a one-time, pre-release, **offline-exclusive** operation
(`scripts/reset_corpus_baseline.py`): the API, workers, and every other process that writes to the
SQLite database or the Chroma store must remain **stopped** from preflight through completion of the
rebuild. The command verifies each published corpus against its canonical digest proof before deleting
anything, but it does not hold that SQLite snapshot across the rebuild, detect other processes, or take
a cross-process lock — concurrent writes are out of contract, not defended against. Rebuilding a **live
/ production** store is therefore **deferred**: no such maintenance functionality exists today, and if
it is ever required it needs a separately designed maintenance mode, or an online
build-and-swap / catch-up workflow with its own data-preservation guarantees. This is a bounded
*operational* deferral only; it leaves nothing about the source-corpus **architecture** unresolved
(that is settled by ADR-005c, above, and delivered by CRD Issue 5c). See ADR-018's 2026-07-29 owner
decision and `srd-corpus-reproducibility.md`.

The Issue-5c delivery establishes the source-corpus layer
and the new package UUID/release-version seam only; it does **not** provide executable mechanical
authority (no MechanicalEntity, no DC/dice typing — Owner Decision 2). **Implementation remains pending**
CRD Issue 5d (structured mechanical authority and deterministic rule binding), CRD Issue 2b (D&D 5e
character-state completeness for deterministic adjudication), and CRD Issue 15c (bounded d20 adapter
production reachability).

**Owner Decision 2026-09-16 — practical reliability policy adopted; implementation pending.**
The [amended ADR-005d](../decisions/adr-005d-complete-typed-mechanical-authority.md) and amended
#137 govern section/entry/table review, use-driven field selection, exact governing prose, shared
batch tooling, and a regular-section pilot. Full actual-rule coverage and downstream ownership remain.
The seven accepted batches are preserved. The landed implementation and historical schema work below
are not evidence that the new policy is already implemented. No new corpus acceptance, publication,
activation, or merge is implied by this decision.

**In progress — typed Rules Package authority (CRD Issue 5d, #137).** CRD Issue 5d is under
construction and is **not complete**. Landed so far: span-exact semantic accounting, the closed typed
representation, the persistence → reconstruction → digest → gate → publication lifecycle and its exact
completeness gate; the runtime four-component `RulesPackageBinding`, typed override application,
retained provenance-exact override-set versions, and the authored-authority prose overlay; and the
production-authoring workflow with the evidence-backed expansion of the closed typed-fact union — dice,
attacks, damage, healing, creature defence/speed/challenge and saving-throw modifiers, spell
descriptors, action economy, conditions, spell-slot progression, class spell-list membership, resource
and recharge cadence, equipment descriptors, advantage/disadvantage, and stated scaling.

**Extended by the conditions batch (schema closure).** Accounting the first production-content batch —
the 15 SRD conditions and the `Condition` glossary rule — forced authority the union could not carry
faithfully, and in four cases could not carry *at all*: roll actor polarity (Blinded and Invisible
reduced to identical typed facts for opposite rules), ability-qualified rolls (a Dexterity-save claim
could only be stated as a claim about every saving throw), the all-damage response, and Prone's three
attack-roll rules (two collapsed into one rejected duplicate). Added: a shared `RollSpec` value object
(actor, roll context, optional ability), `AutomaticOutcomeFact`, `SpeedModificationFact`,
`ActionRestrictionFact`, `CriticalHitRuleFact`, `StateEffectFact`, a damage-response scope with stated
exceptions, and a scaling direction with a condition-level basis.

Contract 3 family groups after that batch:

* **discharged** — *critical changes* (`CriticalHitRuleFact`) and *typed state effects*
  (`StateEffectFact`, over a closed vocabulary whose members each required siblings in more than one
  section);
* **narrowed, still deferred** — *targeting restrictions*. Three instances were forced (Charmed,
  Frightened, Invisible), and a corpus sweep of the restriction mechanics found their referents range
  over distances, creature relationships, spell schools, spatial areas, and effect properties. A closed
  referent vocabulary spanning those would be a predicate language, so these are classified as
  affirmatively prose-bound under `contextual_applicability` rather than typed. Revisit when a batch
  forces a referent set that closes;
* **untouched** — contests, explicit probability, random-table selection, eligibility, choices, and
  sequencing, added by batch-driven accounting as the corpus surfaces them, due no later than
  full-corpus closure.

Known residue from that batch, recorded rather than typed on single instances: an imposed sensory state
(Blinded's *"You can't see"* and Deafened's parallel — every other blinding effect in the corpus instead
says *"has the Blinded condition"*), Exhaustion's cumulative level accrual, death threshold, and
level removal on a Long Rest, movement options and per-foot movement cost, size-comparative eligibility,
Petrified's transformation, and one sequencing clause.

**Narrowed by representation schema 3 (conditions-1 semantic review).** Semantic review rejected the
conditions-1 schema-2 proposal because the union could not carry Grappled > Movable faithfully, and in
three respects could not carry it *at all*: creature-to-creature transport had no family, so *"The
grappler can drag or carry you when it moves"* was recorded as supporting authority and produced no
typed fact; a movement cost named no payer, so Grappled's grappler-paid surcharge and a subject-paid one
were the same typed authority; and a size comparison kept neither operand, so *"you are two or more
sizes smaller than it"* and its reverse were indistinguishable. A fourth gap surfaced in the same
review: Prone's *"half your Speed (round down)"* stated a rounding the union could not record at all.

Schema 3 discharges those four. Added: `MovementTransportFact` over a closed `ParticipantRole`
(`SUBJECT`/`COUNTERPART`) and `TransportKind`; `MovementCostFact.payer`; `MovementCostFact.rounding`
over a `RoundingRule` whose `DOWN` default is derived from the Rules Glossary *Round Down* entry rather
than from a runtime arithmetic convention; and `SizeComparison.measured`/`reference`/`at_most`.
`COUNTERPART` is admissible only where a closed structure in the same component establishes the binary
relation — in schema 3, `MovementTransportFact` alone — so the role can never become "some other entity
the prose mentions".

**Retained successors, none of them forced by conditions-1.** Each was surfaced by the schema-3 sibling
audit and is deliberately not decided here:

* **Source-authored cross-record suppression of a surcharge.** Shambling Mound's Engulf states *"costing
  it no extra movement"*, waiving a surcharge defined in the Grappled condition — a different record.
  Swimming and Climbing state their own waivers *beside* their own surcharge, which is an applicability
  negation the union already has, so the Mound is the only instance of the cross-record form. This is
  **base-projection semantics and is not a `RuleOverride`**: an override is authored suppression, while
  this is what the source itself says. Owner-confirmed as deferred; unresolved.
* **Counterpart establishment outside transport.** Unarmed Strike's Grapple/Shove size restriction
  establishes its counterpart through an attack/target relation, so it cannot use `COUNTERPART` until
  the admitted set of counterpart-establishing structures is widened. That widening is a validation
  change, not necessarily a schema mint.
* **Third-party size comparisons.** Black Pudding and Ochre Jelly Split compare a created creature to
  the originating one; neither operand is the record's subject, so the two-member role vocabulary does
  not reach them. Likely a creature-creation structure rather than an applicability condition.
* **Ratio-form movement costs.** Gust of Wind, Plant Growth, and Wall of Thorns state *"spend 4 feet of
  movement for every 1 foot"*. `MovementCostKind` has no ratio member, and converting the ratio to an
  equivalent surcharge would record a claim the source never makes.
* **Rounding supplied by the governing rule rather than stated locally.** Where a future fractional
  quantity does not restate its rounding, the value comes from the *Round Down* glossary entry, which is
  itself corpus content awaiting a batch. A fact must not claim provenance over a span it did not
  account for.
* **Applicability over a capability predicate.** Swimming's and Climbing's *"if you have a Swim Speed and
  use it to swim"* ranges over possessing and using a movement mode, outside `ApplicabilityKind`'s four
  closed vocabularies. Related to the targeting-restriction disposition above: revisit when a batch
  forces a referent set that closes.

**Narrowed by representation schema 6 (the `actions-1` schema stop).** Discovery over the thirteen
`actions-1` records stopped at the schema before generating a proposal: 21 blocking families across 35
`UNRESOLVED` obligations. Schema 6 is the batch-driven accounting the *untouched* list above anticipated,
and it moves three of those groups:

* **narrowed, still deferred — *eligibility*.** `ActivationCostEligibilityFact` carries *"a spell must
  have a casting time of an action"* over the printed, enumerable casting-time field, with three
  instances in three records (`Ready` L8, `Magic` K1, `Utilize` O2). Reclassifying L8 from supporting
  authority to substantive is a correction recorded with the schema, not a silent move. Not
  discharged: `EligibilitySubject.SPELL` has siblings in more than one section, but `.OBJECT` has a
  single instance in a single one, and no corpus sweep has shown what else a mechanic can be made
  eligible by. Revisit when a batch forces a subject the two members do not reach;
* **narrowed, still deferred — *sequencing*.** Split rather than unified: `MovementInterleaveFact`
  locates a point inside a repeated action, `TriggeredResolutionFact` locates one relative to a
  trigger. One enum spanning both would be the cross-domain vocabulary the module refuses — but each
  vocabulary currently holds **one member with one instance**, which is the weakest closure evidence
  this document admits, and no sequencing sweep has been run. Two typed families are what these two
  clauses forced, not a demonstration that sequencing closes;
* **narrowed, still deferred — *choices*.** `ProseBindingDraft.option_key` lets prose govern one arm of
  an exhaustive choice, which is what `Help` and `Ready` L4 both need: one clause governs one arm and says
  nothing about its sibling. Both are authorable under the union as it stands — L4's arms each state
  `ActionEconomyFact(REACTION)`, the consumption the source names, with the own-Speed allowance on the
  second and *which* action left to option-grain prose. Three earlier readings held L4 unauthorable; each
  looked only at the allowance families, where typing arm 1 would have published a grant the source never
  makes, and each is recorded as refuted in the batch checkpoint.

  It does **not** make every printed "or" an option set: `Attack` B2 is one entitlement with an instrument
  qualification, refused by `option_set_violations` rather than by choice. The group stays open because
  deciding whether a printed alternation is a choice is still case-by-case work — not because of any span
  budget. An earlier note here said L4's encoding needs five primary provenance claims over one printed
  sentence; it does not, and the reading behind it was wrong. Every authoritative element needs *evidence*
  of any role, and only a substantive *span* needs one *primary owner*. L4's real coordinates satisfy both
  with four spans: L2, L4 split once at its printed `or`, and L6, with the shared Reaction evidenced
  contextually on L2. Those edges are contextual because of what L2 *scopes*, not because of what L4
  omits: L2 states the slot once for the whole readied response, so it supports each arm's copy without
  stating that *this alternative* is what spends it. Verified on the real leaf ids, extents and printed
  text in `test_schema_6_ready_source_provenance`, which checks its literals against the committed
  coordinates artifact and its pinned source digest. **No new family is proposed here**, and the span
  partition was a proposal's decision, not this note's — the Owner accepted that proposal on
  2026-09-09, which settled the partition without discharging this group.

**Narrowed by representation schema 7 (the `actions-1` residue S-1).** Independent review of the
schema-6 batch confirmed one remaining stop, and it is the reason `Magic` K2, K3 and K4 were unresolved
together. *"If you cast a spell that has a casting time of 1 minute or longer"* (`Magic`, p185) is a
threshold over a spell's **printed casting-time descriptor**. `ActivationCostEligibilityFact` ranges
over `ActionCost`, which prints no amount and no unit; `ApplicabilityKind.ELAPSED_DURATION` would have
meant time *already spent* casting, which is false at the moment the clause first applies. Schema 7 adds
one applicability kind, `SPELL_CASTING_TIME`, over one closed value object, `CastingTimeThreshold`.

* **narrowed, still deferred — *eligibility*.** The group above is unchanged in its closure standard,
  and this is a second, adjacent axis rather than a widening of the first. The threshold gate and the
  activation-cost eligibility fact range over the two different arms of one printed descriptor: which
  spells a mechanic *reaches* by the cost they print, and which spells a further requirement *applies
  to* by the duration they print. A one-minute spell falls outside `Magic` K1, **not** outside the Magic
  action. Not discharged: `SPELL_CASTING_TIME` has one instance in one record, which is the weakest
  closure evidence this document admits, and the comparable-clause check that established the bounded
  vocabulary was scoped to casting-time eligibility rather than run as a corpus sweep. Revisit when a
  batch forces a second threshold instance or a subject the two eligibility members do not reach.

New residue recorded with the mint, and open:

* **A round and a turn have no length this layer may read.** `casting_time_meets` compares two stated
  durations by magnitude across the calendar units whose length is fixed — second, minute, hour, day —
  so cross-unit comparisons are ordinary arithmetic and are *not* an open question. `ROUND` and `TURN`
  are slices of the initiative cycle, and no printed casting-time descriptor states how long one lasts.
  Rather than assign a guessed length or answer `False` — which would report the substantive
  *"this rule does not reach that spell"* for a comparison never made — the comparison **raises**
  `UncomparableCastingTimeError`. The corpus prints no casting time in rounds or turns, so nothing is
  currently reached by the refusal. Revisit when a batch forces one — at which point the question is
  where a round's length is *stated*, not how to compute with it.
* **A component carries exactly one `applies_when`.** Where two components of one record sit inside the
  same printed condition, the second restates it, and its evidence edge on the shared span is
  `CONTEXTUAL` because there is no position for a condition two components share. This is a structural
  limit of the union, recorded rather than worked around: `Magic` K2's gate is the only instance the
  batch forces, and a shared-scope structure is not proposed on one.

Nothing in this group is **discharged**. This document's standard for that is a closed vocabulary whose
members each required siblings in more than one section, and neither group above meets it yet.

*Contests*, *explicit probability* and *random-table selection* remain **untouched**, due no later than
full-corpus closure, and this batch contributes no evidence to any of them. The suggested skill tables in
`Influence`, `Search` and `Study` were briefly recorded as three surfaced instances of random-table
selection; **that was an error, and the Owner has clarified what they are: exemplars and DM guidance.**
The GM chooses, nothing is rolled, and no row is selected — so they neither instantiate that group nor
stand as an obstacle to it. Their advisory content is preserved as the governing prose it always was,
under `gamemaster_latitude` and `subjective_judgment`. The earlier note that a printed table's row keys
range over no closed vocabulary is withdrawn with the claim it supported: the full-corpus random-table
work remains deferred on its own evidence and borrows none from these tables.

Known residue from this batch, prose-bound at the scope where it applies rather than typed: *which*
action a subject readies (`Ready` L4 — both arms are typed; the identity of the chosen action is open),
`Attack` B2's instrument qualification, and the option-scoped clauses on `Help`. In each case `option_key`
records the arm a clause governs without typing its content. Each is contract 3's second branch used as
intended rather than a deferral: a catalog reason is affirmatively true of every one of them.

**Representation schema 8 (the `attitudes-1` stop S-2) narrows nothing here, and that is recorded
rather than left silent.** *"Indifferent is the default attitude of a monster."* had no shape under
schema 7, so schema 8 adds one family, `DefaultAttitudeFact`, over one closed vocabulary, `Attitude`,
under #137 contract 3 and ADR-005d Decision 4 — see the schema-8 amendment in
`docs/decisions/adr-005d-complete-typed-mechanical-authority.md`. It belongs to none of the groups
above, discharges none of them, and changes no closure standard stated in this document. **The
discharge standard stated above is a standard for discharging these groups; it is not an admission gate
on new families under contract 3.** An `attitudes-1` draft read it as the latter, which reinstated a
sibling-count precondition that `issue-5d-actions-1-SCHEMA-STOP-CHECKPOINT.md` §6 had explicitly
withdrawn; the misreading is corrected in that batch's artifacts and is noted here so the standard is
not read that way again. `attitudes-1` has since been accepted, which resolved the three `attitude.*`
reference targets it also defines.

**Representation schema 9 (the `areas-of-effect-1` class) narrows nothing here either, and the same
is recorded rather than left silent.** `[Area of Effect]` — seven Rules Glossary entries, 43 clauses,
24 of them substantive — had **no** shape under schema 8, and no reason code in
`policy.IRREDUCIBILITY_REASONS` is affirmatively true of any of its clauses, so schema 9 adds seven
families over eleven closed vocabularies under #137 contract 3 and ADR-005d Decision 4; see the
schema-9 amendment in `docs/decisions/adr-005d-complete-typed-mechanical-authority.md`. It belongs to
none of the groups above, discharges none of them, and changes no closure standard stated in this
document — the discharge-standard clarification in the paragraph above applies here unchanged. **No
spatial-geometry Known Unknown is created, narrowed or leaned on.** The class prints no grid vocabulary
at all, and schema 9 represents no parameter value, unit, coordinate or grid semantic; runtime geometry
stays outside, where #137's Out of scope and ADR-005d Decision 11 leave it. What the batch does add is
residue: the class cites `Cover`, an untagged Rules Glossary entry no accepted batch represents, so
composing it produces a third unresolved reference target, `glossary.cover`, beside the two below.
Sequencing a batch that states `Cover` is ordinary engineering under #137, not an Owner Decision, and
nothing in this document anticipates that entry's content. `areas-of-effect-1` has since been accepted,
which added `glossary.cover` for real rather than in prospect and resolved nothing.

**Representation schema 10 (the `Cover` entry) narrows nothing here either, and the same is recorded
rather than left silent.** `Cover` — printed twice in the bound release, 16 leaves, 28 clauses, 16 of
them substantive — had **no** shape under schema 9, and no reason code in
`policy.IRREDUCIBILITY_REASONS` is affirmatively true of any of its clauses, so schema 10 adds five
families over eight closed vocabularies, plus the third member of `CoverDegree`, under #137 contract 3
and ADR-005d Decision 4; see the schema-10 amendment in
`docs/decisions/adr-005d-complete-typed-mechanical-authority.md`. It belongs to none of the groups
above, discharges none of them, and changes no closure standard stated in this document. **No
spatial-geometry, visibility or line-of-sight Known Unknown is created, narrowed or leaned on.** This
document holds no entry for cover, visibility, occlusion or line of sight; schema 10 computes no
geometry and carries no parameter value, unit, coordinate or grid semantic — the boundary being
runtime computation rather than geometric subject matter — and measuring coverage, deciding which
side an effect originated on, choosing a degree for a scene and executing an attack all stay
outside, where #137's Out of scope and ADR-005d Decision 11 leave them. The disposition recorded above — *"Sequencing
a batch that states `Cover` is ordinary engineering under #137, not an Owner Decision, and nothing in
this document anticipates that entry's content"* — was followed as written: the entry was measured from
the bound release rather than anticipated from that sentence, and no Owner Decision was required.
**`glossary.cover` is not resolved by this change.** A schema can now state the entry; only an accepted
`cover-1` proposal would define the target, and none exists. The count of unresolved cross-batch
reference targets below is therefore still three. *(That last sentence has since expired: the Owner
accepted `cover-1` on 2026-09-11, which defined the target and took the count to two. The rest of
this paragraph stands as written — it records what the schema change alone did.)*

**Representation schema 11 (the `Speed` entry) discharges nothing here, and the movement residue
this document already carries is the reason it has to say so explicitly.** `Speed` is printed twice in
the bound release — a Rules Glossary definition and `Playing the Game > Combat > Movement and
Position`, joined by the source's own reciprocal citation — 16 leaves, 36 clauses, 16 of them
substantive. No reason code in `policy.IRREDUCIBILITY_REASONS` is affirmatively true of any of them, so
schema 11 adds seven families over eleven new closed vocabularies and widens a twelfth,
`MovementMode`, by one member (`jump`), under #137 contract 3 and ADR-005d Decision 4; see the
schema-11 amendment in
`docs/decisions/adr-005d-complete-typed-mechanical-authority.md`. **Four movement items above are
neither narrowed nor leaned on.** *"Movement options and per-foot movement cost"* remains
`conditions-1` residue; *"Ratio-form movement costs"* is untouched, because no clause in this
population states a ratio and `MovementCostKind` gains no member; *"Applicability over a capability
predicate"* concerns the `Swimming` and `Climbing` entries, which are outside this batch's population
and whose *"if you have a Swim Speed and use it to swim"* is still unreachable by
`ApplicabilityKind` — schema 11 names `special_speed` as a category and does not make possession of one
an applicability condition; and the *sequencing* deferral is untouched, because `SpeedSelectionFact`
and `SpeedSwitchLimitFact` state a choice among a creature's own speeds and its printed cost, not a
position in a sequence, so neither `MovementInterleaveFact` nor `TriggeredResolutionFact` gains an
instance or a member. **No new Known Unknown is created.** **Nothing evaluates and nothing about a
grid is represented.** Schema 11 **invents** no parameter value, unit, coordinate or grid semantic,
which is not the same as carrying no unit: `SpeedDefinitionFact.unit` is `DistanceUnit.FOOT`, the
member schema 5 registered, and it names the foot *"the distance in feet"* prints. Reproducing a
unit the sentence states is the opposite of inventing geometry — no schema-11 vocabulary mentions a
square, a segment or a corner, and no fact in this batch carries a number.
Subtracting a move from the allowance, applying the propagation rule to a creature's actual speed
list, and every square, segment and corner rule stay outside, where #137's Out of scope and ADR-005d
Decision 11 leave them. The grid rules printed at `Playing the Game > Exploration > Vehicles` are
outside **this batch** by its membership rule and not outside declarative 5d; their printed
representation remains later 5d work, neither prejudged nor scheduled. **`glossary.speed` is not
resolved by this change.** A schema can now state the entry; only an accepted `speed-1` proposal would
define the target, and none exists. The count of unresolved cross-batch reference targets below is
therefore still two. When such a proposal is accepted it would close `glossary.speed` and open nine —
`glossary.climbing`, `.crawling`, `.flying`, `.jumping`, `.swimming`, `.burrow_speed`, `.climb_speed`,
`.fly_speed`, `.swim_speed` — taking the count to ten. ~~That is arithmetic over two sets and not a
measured seam result: no operation merges an accepted prior with an unaccepted draft.~~ It is recorded
here for the same reason the earlier residue movements were — as a consequence of accepting a complete
source class, not a reason to choose one.

**Corrected at the `speed-1` proposal (2026-09-12), struck above rather than deleted.** The struck
sentence was wrong. `acceptance._merge_representation` merges a lifted accepted prior with a draft and
`oracle.candidate_from_accepted_inputs` builds a candidate over the result, so ten is **measured**, not
arithmetic: the proposal generator runs `validate_representation` twice — nine unresolved-reference
findings against the draft alone, ten against the merge with the schema-11-lifted six-batch prior — and
asserts both target lists exactly. Separately, a `speed-1` proposal artifact now exists
(`.claude/review-notes/issue-5d-batch-speed-1-PROPOSAL.json`, identity `bd9d4942…`) and is unaccepted;
the merge above is performed in memory, so **the count of unresolved targets in accepted authority is
still two** and the rest of this paragraph stands. *(That last clause has since expired: the Owner
accepted `speed-1` on 2026-09-12, which resolved `glossary.speed`, emitted nine citations of its own
and took the count to ten. The rest of this paragraph stands as written — it records what the
proposal alone did.)*

Still outstanding inside CRD Issue 5d: **the accepted corpus is incomplete**. Seven batches are
accepted. `conditions-1` was reviewed and accepted by the Owner on 2026-08-23, `hazards-1` on
2026-09-03, `actions-1` on 2026-09-09, `attitudes-1` on 2026-09-10, `areas-of-effect-1` on
2026-09-11, `cover-1` later the same day and `speed-1` on 2026-09-12; all seven are committed as
accepted authority for the production SRD 5.2.1 release, so that release resolves to a committed
oracle — but that oracle covers **48 records and 594 spans** (15 conditions, 5 hazards, 12 actions,
3 attitudes and 6 areas of effect, plus the glossary entry defining each list, and the `Cover` and
`Speed` glossary rules, neither of which defines a list of its own), not the corpus. Ten cross-batch
reference targets named by accepted content are still unresolved and no target was invented for any
of them: `glossary.concentration`, inherited since `conditions-1`, plus the nine movement and
special-speed entries `speed-1` cites without defining — `glossary.burrow_speed`,
`glossary.climb_speed`, `glossary.climbing`, `glossary.crawling`, `glossary.fly_speed`,
`glossary.flying`, `glossary.jumping`, `glossary.swim_speed` and `glossary.swimming`.
`attitudes-1` closed three targets by accepting the complete source-defined Attitude class,
`areas-of-effect-1` closed none while adding `glossary.cover`, `cover-1` closed that one by defining
the entry `areas-of-effect-1` cites, and `speed-1` closed `glossary.speed` while opening nine. All
four are consequences of accepting complete source classes rather than reasons for accepting them,
and the residue moves in both directions rather than only down — `speed-1` moved it both ways at
once. The publication path therefore returns `INCOMPLETE` for the production projection rather than
`ABSENT`, the runtime binding still reports `UNPUBLISHED` because no mechanical projection has been
published or activated, and later batches extend the same release artifact through
`accept_proposal`'s `prior=` merge rather than committing a second one — as `hazards-1`,
`actions-1`, `attitudes-1`, `areas-of-effect-1`, `cover-1` and `speed-1` each did. The obsolete
`MechanicalEntity` path and the legacy chunk-targeting prose override path both remain in place
pending the final activation/legacy-retirement PR.

**Two kinds of outstanding reference, and they close by different means.** The ten above are
*named-but-unminted*: accepted content states a destination key and no accepted batch has minted a record
for it yet, so each closes the moment some batch does — the citation's own key never changes, nothing is
decided, and `attitudes-1`, `cover-1` and `speed-1` each closed targets exactly that way. The second kind
is an *empty target*: review read a citation the source plainly makes and could state no destination key at
all. **None is accepted today.** Four arrive with the Proficiency destinations batch — *Stat Block*,
*Combat Encounters*, *Combat* and *Opportunity Attack* — and they will not close the way the ten do,
because a reference's key includes its target: a later batch authoring the destination states a *different*
key, and the accepted empty edge survives beside it, reported both unresolved and ambiguous. An accepted
empty target closes only through an explicit reviewed reference resolution under Owner Decision 2026-09-19
(ADR-005d Decision 7), which records who authorized the destination and leaves the accepted history intact.
That capability exists and is demonstrated on isolated evidence; **no accepted citation has been resolved
by it, and those four stay open obligations until genuinely reviewed destinations exist.** Neither kind is
a Known Unknown of its own: both are the 5d corpus incompleteness this entry already records, distinguished
here so the two are not read as one thing that closes one way.

**Corrected at the Proficiency acceptance (2026-09-20 UTC), appended rather than rewritten.** Two counts
above have moved and one prediction has come true. "Seven batches are accepted" is now **nine**: the Owner
accepted `proficiency-destinations-1` and then `proficiency-1` in one action on 2026-09-20 UTC, and the
committed oracle now covers **53 records and 761 spans** rather than 48 and 594 — the five added records are
`play.actions`, `play.skills`, `glossary.challenge_rating`, `glossary.expertise` and the `play.proficiency`
rule the last of those cites. The ten named-but-unminted targets listed above are **unchanged**: the
Proficiency batches closed none of them and opened none. What did arrive is the second kind this entry
predicted — the four empty-target citations *Stat Block*, *Combat Encounters*, *Combat* and *Opportunity
Attack* are now accepted, so "**None is accepted today**" above has expired while everything it says about
how they close still stands. No destination was ingested for them, no target was invented, and
`reference_resolutions` is empty in the committed artifact, so no reviewed reference resolution was invoked
for any of the fourteen; those four remain open obligations. The publication path still returns `INCOMPLETE`
and the runtime binding still reports `UNPUBLISHED`; the acceptance published, activated and retired
**nothing**, and the corpus incompleteness this entry records is unchanged in kind.

**This does not move CRD Issue 15c's boundary.** Publishing a mechanical projection proves complete
*representation*, never adapter capability. The bounded-d20 adapter's capability manifest, certified
executable coverage, adjudication failure behaviour, and any typed application path for a
GameMaster-selected effect remain owned by CRD Issue 15c (ADR-005d Decisions 1 and 11). No 5d fact
family is admitted or withheld on the basis of what the adapter can execute, and neither authority view
carries an executability claim.

**Surfaced during:** CRD Issue 15b Phase 2 implementation on frozen PR #129 (`D20RulesSystemAdapter.
_verify_dc` unconditionally returns `None`; Rules Package entities carry no `dc`/`difficulty_class` field
and store dice/damage data as unstructured prose). The ADR-005c investigation also found the committed
SRD artifact (`data/srd/srd_5_2_1_structured.json`, 50 entities / 54 sections) falls short of CRD Issue
5b's full-corpus contract (ADR-005c Context item 1) — a distinct but related defect this entry's
resolution now covers under the same repair order.

**Resolve implementation during:** CRD Issues 5c, 5d, 2b, 15c, in the order recorded in ADR-005c's
Repair-Order Consequence.

---

### Parameterized adjustments (spell-slot-level upcasting, variable-amount resource recovery)

**Open. Not resolved by ADR-005c** — see ADR-005c's Verification Note and Scope Boundaries, which
explicitly exclude "implementing parameterized upcasting." ADR-005c does not approve a final parameter
schema for this item.

Some mechanics require validated typed parameters rather than selection through a fixed `option_id`.
Examples include casting-level selection and variable resource amounts. ADR-015b currently supports
fixed option selection only. The exact typed parameter contract and the set of mechanics admitted into
deterministic v1 support remain unresolved and require an explicit owner decision before implementation.

**Do not infer production coverage from this entry.** The current SRD artifact is an incomplete curated
subset (see the Rules Package entry above and ADR-005c Context item 1), and production package-to-adapter
reachability for any mechanic — base-level or parameterized — has not been established. This entry does
not claim that a specific number of spells, or base-level casting generally, is currently supported in
production; it only names the parameter-shape question that remains open regardless of corpus state.

**Unchanged by CRD Issue 5d's schema work, including the conditions batch.** 5d *records* stated
scaling declaratively and evaluates none of it. The conditions batch extended `ScalingFact` with a
direction and a condition-level basis so Exhaustion's *"the roll is reduced by 2 times your Exhaustion
level"* could be represented as what the source says; no adjustment parameter was defined, nothing
selects a value at play time, and the `chosen_slot_level`-shaped contract this entry names remains open
and owned by an ADR-015b amendment.

**Surfaced during:** CRD Issue 15b Phase 2 bounded-d20 coverage inventory (frozen PR #129), against the
curated SRD 5.2.1 package. Any adjustment option requiring parameters beyond a stable `option_id`
requires an ADR-015b amendment before it ships.

**What resolution requires:** Owner decision on whether to pull upcasting/variable-resource-recovery
mechanics into scope, and which mechanics are admitted into deterministic v1 support; an ADR-015b
amendment defining a typed `RollAdjustmentOption` extension before any implementation — *non-binding
illustrative example, not an approved schema:* a field shaped like `chosen_slot_level: int`,
server-validated against the sheet's available slots, is one possible form this could take. This is
independent of, and not resolved by, the Rules Authority repair order above.

---

## How to Add a New Unknown

When construction surfaces a decision that is not covered by existing docs and should not be resolved unilaterally:

1. Add it to the Open section above with: what it is, why it is open, what resolution requires, and when it must be resolved.
2. Note it in the PR description as a Known Unknown surfaced during implementation.
3. Do not proceed with a local resolution — pause for owner decision.

---

*This document is a canonical architecture artifact. Updates require a PR with an Architecture Notes section. Resolving a Known Unknown during construction requires a corresponding ADR in `/docs/decisions/` unless the owner explicitly classifies the decision as already covered by the Design doc / CRD record.*
