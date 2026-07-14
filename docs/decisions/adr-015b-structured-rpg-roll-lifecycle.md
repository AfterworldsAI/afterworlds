# ADR-015b: Structured RPG Roll Instructions, Action-Resolution Sequences, and Player-Roll Lifecycle Completion

**Issue:** CRD Issue 15b — corrective extension to CRD Issue 15 / ADR-015
**GitHub:** #127
**Date:** 2026-07-13
**Status:** Proposed — Phase 1 (this document) requires explicit owner acceptance and merge before Phase 2
(`feature/issue-15b-structured-roll-lifecycle`) may begin.

---

## Central Invariant

> **The model may propose that a roll or mechanical decision is required; it may never make a
> trust-relevant mechanical value authoritative.**
>
> The active Rules System Adapter and code-owned services create the authoritative roll instruction.
> The Sojourner supplies bounded roll results or selects permitted options. Code validates, resolves,
> audits, and applies mechanical effects.
>
> Mechanically linked rolls accumulate inside one action-resolution sequence and reach the Writer
> together at a meaningful narrative boundary — not once per die roll.
>
> Every accepted intermediate roll, adjustment, or mechanical decision commits durable, append-only
> provenance atomically with sequence advancement — without becoming sheet, canon, or delivered-result
> authority until final narrative delivery.

Audit honesty and hidden-state protection are governed by Decision Group 5 below (15b-16, 15b-17).
Durable intermediate provenance is governed by Decision Group 15 below (15b-34). Stored-snapshot authority
applies equally to pending rolls and pending mechanical decisions, per Decision Group 16 below (15b-35).

---

## Context

CRD Issue 15 / ADR-015 established the correct RPG authority boundaries — code-owned deterministic
rails, schema-first roll-authorship enforcement, `gm_cheating = off` as an immutable-record invariant,
and hidden-roll visibility filtering. Those boundaries are correct and are not reopened here.

What ADR-015 did not establish, and what the shipped implementation does not provide, is a player-roll
contract wide enough for ordinary bounded-d20 play: multi-die pools, keep-highest/keep-lowest selection,
mixed and repeated terms, typed adjustments (advantage/disadvantage as a player-facing choice rather
than model-inferred text), a persisted unit larger than one request for mechanically linked rolls
(e.g., an attack roll followed by a damage roll), and any product-API route through which a Sojourner
can actually submit a roll result. CRD Issue 19 shipped a frontend/API shell but left the RPG roll
lifecycle unreachable through it.

This ADR amends ADR-015. It does not reopen the RPG adjudication pass position (Fork A/A1), the
sheet-mutation application path (Fork B/B1), schema-first roll-authorship enforcement (ADR-015 Decision
3), `gm_cheating = off` enforcement (ADR-015 Decision 4), hidden-roll handling (ADR-015 Decision 5), or
the bounded-d20/no-ingestion-mechanics boundary (ADR-015 Decision 7). See **Inherited ADR-015 Decisions**
below for the complete non-reopened list.

---

## Delivery Phases

1. **Phase 1 (this PR, `feature/issue-15b-structured-roll-adr`):** this ADR, the Design/CRD clarification
   edits below, and the directly related `known_unknowns.md` edit. No implementation code. Implementation
   begins only after explicit owner acceptance and merge of this PR.
2. **Phase 2 (`feature/issue-15b-structured-roll-lifecycle`):** DTOs, persistence, migration, adapter
   expansion, sequence service, validation, projected state, audit integration, orchestrator resume,
   legacy consume-path retirement, and backend/orchestration tests — proven without HTTP routes.
3. **Phase 3 (`feature/issue-15b-rpg-product-wiring`):** service construction in `create_app()`, API DTOs
   and routes, story-lock participation, OpenAPI/TypeScript generation, fake-provider E2E coverage. Splits
   into a new CRD Issue 19c if it requires persistence/migration/orchestration/business-policy work beyond
   what Phase 2 delivers, or more than twelve hand-authored production files outside tests and generated
   artifacts.

---

## Superseded ADR-015 / Shipped-Implementation Assumptions (15b-2)

ADR-015b identifies exactly which narrow player-roll assumptions it supersedes. Each item below cites the
shipped source as it stands on `origin/main`, not a paraphrase of it.

| # | Narrow assumption (ADR-015 / shipped code) | Citation | Superseded by |
|---|---|---|---|
| 1 | `PendingRollRequest` is a single free-standing row with no unit above it linking mechanically related rolls. | ADR-015 Decision 1 ("`PendingRollRequest` rows... persist for 'pending' turns"); `models/rpg.py:184-221` has no sequence/step field; grep across `models/rpg.py` and `pipeline/rpg/` finds no multi-step linkage concept. | `ActionResolutionSequence` with `sequence_id`/`step_id` (15b-18, 15b-19). |
| 2 | The only roll expressions the system ever produces are three hardcoded strings, and consumption is total-only with the raw die *derived* by subtraction. | `pipeline/rpg/adapter.py:245-250` (hardcoded `if/elif` emitting `"1d20"`/`"2d20kh1"`/`"2d20kl1"` only); `adapter.py:413-467` `consume_player_roll(pending, reported_total, ...)`; `raw_die = reported_total - visible_mod - hidden_mod` at `adapter.py:430`; `dice.py:51-63` `chosen_die_range` gates validation to single-chosen-die expressions only. Note: `dice.py:17-20`'s `_EXPRESSION_RE` accepts general `NdS(kh\|kl)K([+-]N)` syntax, including `keep_n > 1`, but the executor (`dice.py:117-122`) does not correctly implement it: for `keep_n > 1` it returns `sorted(raw, ...)[:keep_n][0]` — the single highest/lowest die, not the sum of the kept dice — and neither the executor nor `chosen_die_range` rejects `keep_n > count`. The defect is the adapter's narrow *generator*, the total-only *consumption* path, AND the executor's unproven multi-keep selection logic — not a parser ceiling. | Structured `RollInstructionSnapshot`/`RollTerm` contract supporting summed pools, keep-highest, keep-lowest, mixed pools, repeated pools, and code-owned integer modifiers (15b-3, 15b-4, 15b-5); raw per-term submission (15b-14, 15b-15). |
| 3 | Advantage/disadvantage is inferred by regex over the model's free-text `subsystem_tag`; there is no player-facing adjustment mechanism at all. | `adapter.py:42-44` (`_ADV_RE`/`_DISADV_RE`); applied at `adapter.py:241-243`; no `AdjustmentOption`-shaped model exists anywhere in `src/` (only the unrelated billing `ManualCreditAdjustmentPayload`); `RollProposal` (`models/rpg.py:37-53`) has no dedicated field. | Typed `RollAdjustmentOption` with a stable `option_id`, backend-derived eligibility, and pre-roll timing (15b-9 through 15b-13). |
| 4 | Consuming a reported roll total re-enters the full provider-backed narrative pipeline (Planner, and later Writer, Contradiction, Extractor when preceding gates permit) rather than resolving deterministically. | `orchestrator/service.py:822-839` routes the `player_reported_total is not None` branch through `self._run_narrative(...)`; `_run_narrative` re-enters the narrative pipeline: Input Safety Preflight is conditional, gated behind `self._safety_policy.should_run_input_preflight(preflight_ctx)` (`:1145-1178`), the Planner call is unconditional (`:1181-1213`), and later Writer/Contradiction/Extractor run in the same function when preceding gates permit. | Deterministic intermediate operations with no provider call or settlement (15b-27, 15b-28); narration only at sequence completion via `orchestrate_rpg_resume` (15b-20, 15b-21). |
| 5 | `PendingRollRequest` carries precomputed display/derivation fields that duplicate authority instead of deriving from one structured snapshot. | `models/rpg.py:184-221`: `roll_expression`, `expected_value_shape`, `visible_modifier_total`, `visible_modifier_breakdown_json`, `check_label`, `player_facing_instruction`, `visible_modifier_note`, `hidden_modifier_present` all present as plain fields with no structured snapshot backing them. | Column Disposition table in **Revised PendingRollRequest** below — these fields retire after backfill in favor of `instruction_snapshot_json`. |
| 6 | The pending-roll intercept (`BLOCKED_PENDING_ROLL`) triggers on a single outstanding `PendingRollRequest` row and has no notion of a pending mechanical decision or a completed-but-not-narrated sequence. | `orchestrator/service.py:863-891`; `pipeline/rpg/pending.py:54-72` (`load_pending_for_story`, single-row `.one_or_none()` lookup); DB uniqueness index at `persistence/orm/rpg.py:65-72` structurally allows only one pending row per story. | Sequence-aware gate blocking ordinary in-character input for any unresolved sequence state — pending roll, pending mechanical decision, or `ready_for_narration` (**Gate and Resume Trigger**, 15b-31, 15b-32). |
| 7 | No product-API wiring exists for the RPG roll lifecycle, and the gap is deeper than a missing route: the RPG adjudication pass service itself is left unwired in the running application. | `api/dto.py:94-98` (`TurnSubmissionRequest` has `extra="forbid"` and only `user_input`); `api/routes/turns.py:164-171` (orchestrator call never threads a roll total); `Glob` of `api/routes/*.py` shows no roll-submission/adjustment/decision/resume route; `api/pipeline_wiring.py:406-435` (`build_orchestrator()`) never passes `rpg_adjudication_service`, `rpg_dice_service`, or `rpg_pending_roll_service` — all left at `None` defaults, confirmed by the module's own docstring at `pipeline_wiring.py:9-10, 66-68, 83-85`. | Phase 3 product-API wiring reusing CRD Issue 19 conventions (**Product API Wiring** below, 15b-29). Flagged here because Phase 2's orchestrator-integration work and Phase 3's route work both depend on closing this gap, and neither should assume the other already did. |
| 8 | No durable, append-only record of an intermediate mechanical operation survives independently of final delivery. `rpg_roll_audit` is delivery-gated and rolled back atomically with any blocked/errored turn; `PendingRollRequest` is a single row mutated in place on consumption. Nothing records that a specific intermediate roll/adjustment/decision was accepted, independent of whether the Turn that eventually narrates it is ever delivered. | `persistence/orm/rpg.py:32-36` (`RpgRollAuditORM.turn_id` is `nullable=False`, FK to `turns.turn_id`); `persistence/orm/rpg.py:16-27` docstring ("Rows are written inside the 12c outer transaction after the provisional turn_id exists... rolled back atomically with the Turn if any block disposition fires"); `pipeline/rpg/pending.py`'s `mark_consumed` performs an in-place `UPDATE` on the existing `pending_roll_requests` row; no append-only or event-sourced table for intermediate RPG operations exists anywhere in `persistence/orm/rpg.py`. | Append-only `action_resolution_events` ledger, committed atomically with sequence advancement, independent of final-delivery gating (Group 15, 15b-34). |

Item 2's caveat needs restating precisely, because the original phrasing overclaimed the executor's
capability — a Codex review of this document (round 1) caught it. What's actually true: the parser
(`_EXPRESSION_RE`) accepts general `NdS(kh|kl)K([+-]N)` syntax, and the executor correctly handles the two
shapes the shipped adapter ever generates — a summed-all pool (`keep_op is None`) and a single kept die
(`keep_n == 1`). It does **not** correctly handle `keep_n > 1`: `sorted(raw, ...)[:keep_n][0]` takes the
first element of the kept slice, not its sum, so `4d6kh3` would return one die's value instead of the sum
of the top three, and neither the executor nor `chosen_die_range` rejects `keep_n > count`. This is a
correction to the ADR's own defect inventory, not a Phase 2 implementation note: **Phase 2 must fix or
replace the executor's selection logic under the new `RollTerm` contract** — reusing `dice.py`'s parser is
still reasonable; reusing its unproven multi-keep executor as-is is not. This document does not patch
`dice.py`; it is documents-only. Phase 2's tests must prove at least one `NdSkhK`/`NdSklK` case with
`K > 1` (e.g. `4d6kh3`, and a multi-die keep-lowest case) and must prove rejection of a zero or excessive
`keep_count` (i.e., outside `[1, count]`).

Item 4's citation needs the same kind of restatement — a Codex review of this document (round 2) caught it.
`_run_narrative` does not run Input Safety Preflight unconditionally: that block is gated behind
`self._safety_policy.should_run_input_preflight(preflight_ctx)` (`orchestrator/service.py:1145`). What is
unconditional is the Planner call immediately after it (`:1181-1213`), and, when preceding gates permit,
the later Writer/Contradiction/Extractor passes. The underlying defect is unchanged by this correction: the
legacy consume path re-enters the provider-backed narrative pipeline — including unconditional Planner
execution — to resolve what should be a deterministic intermediate operation, regardless of whether Safety
itself runs on any given call.

---

## Decisions of Record

### Group 1 — Scope and ADR relationship

**Decision (15b-1, 15b-2):** Deliver this corrective issue through three sequential PRs (ADR, backend
lifecycle, product wiring), using the Phase 3 split escape hatch above if product wiring exceeds its
approved boundary. This ADR identifies exactly which narrow player-roll assumptions it supersedes — see
the table above — rather than presenting itself as a silent rewrite.

**Rationale:** ADR-015's authority boundaries (adjudication pass position, sheet-mutation path,
schema-first roll authorship, `gm_cheating = off`, hidden-roll filtering, bounded-d20 boundary) are sound
and are not being revisited. Only the player-roll representation and consume path were too narrow. A
scoped amendment against a named defect inventory keeps the correction auditable instead of ambiguous.

### Group 2 — Roll Instruction Contract

**Decision (15b-3 through 15b-7):** A structured `RollInstructionSnapshot` is authoritative; human-readable
expressions are display/diagnostic text only. Every independently meaningful dice term receives a stable
backend-owned `term_id`. The common contract supports summed pools, keep-highest, keep-lowest, mixed
pools, repeated pools, and code-owned integer modifiers — it does not execute arbitrary expressions. Roll
purpose uses a bounded adapter-owned `RollPurpose` vocabulary, never a free-form string. The bounded d20
adapter must represent the ordinary mechanics required by the curated v1 Rules Package; unsupported
mechanics fail explicitly rather than inventing a result.

**Rationale:** A typed term/modifier contract lets the backend validate submissions structurally (exact
term IDs, legal value ranges, stored selection rules) instead of re-deriving intent from a total. Stable
`term_id`s make repeated same-size pools (e.g., two `2d6` damage terms) distinguishable, which a bare
expression string cannot do. Explicit failure on unsupported mechanics preserves the ADR-015 Decision 7
boundary: an unrepresentable mechanic is a merge blocker for the coverage inventory, not something the
adapter silently approximates.

**Consequence:** See **Roll Instruction Contract** shapes under Consequences below. `RollTerm` validation
(bounded positive `count`/`sides`, `keep_count` only for keep operations, `1 <= keep_count <= count`,
adapter approval for supported dice/operations) is a Phase 2 implementation obligation, not optional
polish.

### Group 3 — Pending status, adjustments, and revisioning

**Decision (15b-8 through 15b-13):** Keep dormant `PendingRollStatus.CANCELLED`/`EXPIRED` for schema
compatibility with no v1 behavior — confirmed already true of the shipped `status` literal
(`models/rpg.py:184-221`), so this is a "keep as-is" decision, not new code. Adjustments are optional
operations against a pending roll, not a separate interaction phase; backend-supplied options ride on
`PlayerRollInstructionView`. V1 adjustment options are parameterless selections by stable `option_id`
unless the bounded-d20 coverage inventory proves a supported mechanic needs typed parameters, in which
case 15b-10 requires an ADR-015b amendment before that shape ships. Only pre-roll adjustments are
implemented in v1; the post-roll-before-outcome timing category is preserved but inert until the curated
package requires it. Adjustment costs/effects stay provisional until final narrative delivery. Accepted
adjustments increment `instruction_revision`; stale submissions are rejected and rehydrated. Full revision
history is deferred.

**Rationale:** Treating an adjustment as a sub-operation on the pending roll (rather than its own
interaction phase) keeps `RpgInteractionPhase` a three-value enum instead of growing a fourth
"pending-adjustment" state that would need its own gate/resume handling. Deferring typed adjustment
parameters unless proven necessary avoids building a generalized parameter framework the curated v1
package may never need — the coverage inventory is the gate, not a guess.

### Group 4 — Submission channels and validation

**Decision (15b-14, 15b-15):** Inline rolling submits raw integer values grouped by `term_id`; the backend
derives selections, subtotals, totals, and outcomes. Physical self-report may provide raw values or an
aggregate-only result; audit provenance distinguishes the two and never fabricates raw dice for an
aggregate-only report.

**Rationale:** This is the direct replacement for the superseded total-only `consume_player_roll` path
(table item 2). Submitting raw values per term lets the backend own every derivation instead of trusting
a client-computed total, closing the "derive raw die by subtraction" gap.

### Group 5 — Audit and hidden-state protection

**Decision (15b-16, 15b-17):** Audit records the structured instruction and result used; anti-cheat,
browser attestation, and cryptographic fairness are out of scope. Player DTOs expose only player-visible
facts — hidden values, hidden-modifier existence, and internal references remain backend-only. Durable
audit for intermediate, pre-delivery operations is the append-only event ledger (Group 15, 15b-34); this
decision's audit-recording obligation for delivered results continues to mean `rpg_roll_audit`.

**Rationale:** This is a direct continuation of ADR-015 Decision 5 (hidden-roll handling), extended to the
richer instruction/adjustment surface: `ability_id` on `RollAdjustmentOption` is backend-only precisely
because ADR-015 already established that hidden-modifier existence must never leak into a player-facing
view.

### Group 6 — Action-Resolution Sequence identity and concurrency

**Decision (15b-18, 15b-19):** At most one unresolved `ActionResolutionSequence` exists per story,
enforced by a SQLite partial unique index over `active`/`ready_for_narration` statuses — the same pattern
already used for the single-pending-roll index (`persistence/orm/rpg.py:65-72`). A sequence exposes at
most one pending interaction: either a roll or a mechanical decision, never both.

**Rationale:** Reusing the existing partial-unique-index pattern (rather than inventing new concurrency
primitives) keeps the new persistence shape consistent with CRD Issue 3's established patterns and gives
Phase 2 a proven enforcement mechanism instead of an application-level race.

### Group 7 — Narration batching

**Decision (15b-20):** Narrate at mechanically coherent action boundaries, not after every roll.
Intermediate operations invoke no Writer, Extractor, Contradiction, Safety, or settlement pass.

**Rationale:** This is the architectural core of the fix for table item 4 — the current implementation's
"a provider-backed turn per reported roll" defect. A pool such as `10d6` is one instruction with ten dice,
not ten requests; a multiattack sequence resolves every linked roll before the Writer runs once.

### Group 8 — Orchestrator-owned resume

**Decision (15b-21 through 15b-24):** Pipeline resumption is orchestrator-owned through a new
`orchestrate_rpg_resume(...)` entry point. `ActionResolutionService` supplies a typed
`ReadyActionResolutionBundle` and never returns `OrchestrationResult` or invokes the pipeline itself. RPG
resume uses a code-owned synthetic intent and typed continuation context — it does not classify an empty
string or call `IntentClassifierService`. The resume route resolves and passes the current canonical
`node_id`, matching ordinary turn submission; the orchestrator requires it to match the unresolved
sequence's stored `node_id`, and a mismatch is a typed sequence conflict. Resume context uses the
originating action's user input plus a code-owned continuation frame — resolved mechanics enter through
the ready-bundle/pass-forward seam, not fabricated user prose.

**Rationale:** Keeping orchestration authority inside `OrchestratorService` (never inside
`ActionResolutionService`) preserves the CRD Issue 12c invariant that the orchestrator is the sole
pipeline owner. `orchestrate_turn(...)` and `orchestrate_rpg_resume(...)` must delegate to shared internal
pipeline machinery rather than duplicate Writer/Safety/Extractor/Contradiction/transaction code — the
exact shape of that shared machinery is a mandatory Phase 2 advisor checkpoint, not decided here, because
it requires inspecting `orchestrate_turn`'s full body (including `_synthesize_intent` and the delivery
transaction) before committing an extraction shape that must not alter CRD 12c's disposition semantics,
transaction boundary, or pass ordering.

### Group 9 — Legacy retirement and duplicate protection

**Decision (15b-25, 15b-26):** Phase 2 retires the shipped total-only consume path in full: the
orchestration intercept inside `orchestrate_turn` (`orchestrator/service.py:822-839, 1288-1304`), the
`player_reported_total` parameter, `consume_player_roll(...)` (`adapter.py:413-467`), and
`chosen_die_range` (`dice.py:51-63`). Their tests migrate; nothing survives as a second parallel path.
Atomic duplicate-consumption protection is preserved with no persistent client replay ledger added.

**Rationale:** A surviving parallel consume path is explicitly prohibited (15b-25) — this is a merge
blocker for Phase 2, not a cleanup nice-to-have, precisely because table item 2 and item 4 both trace back
to this one code path.

### Group 10 — Transaction and disposition shape

**Decision (15b-27, 15b-28):** Intermediate roll, adjustment, and decision operations are not narrative
Turns and add no `PipelineDisposition` value. They make no provider call and incur no settlement. Initial
announcement and final narration use the ordinary access-path/settlement flow unchanged.

**Rationale:** This keeps CRD Issue 13's entitlement/settlement boundary intact — only provider-backed
Turns participate in settlement, and intermediate deterministic operations are, by construction, never
provider-backed.

### Group 11 — Product wiring reuse

**Decision (15b-29):** Product routes stay thin and reuse CRD Issue 19's app factory, error envelope,
access-path helper, story lock, and generated contracts. Reusing `409 TURN_IN_FLIGHT` for deterministic
RPG mutations is deliberate despite the name.

**Rationale:** This is a Phase 3 concern but recorded here because it bounds Phase 2: nothing in Phase 2's
service design may require a second lock, a second error envelope, or a second route-construction
mechanism.

### Group 12 — Migration

**Decision (15b-30):** Convert existing pending expressions (`1d20`, `2d20kh1`, `2d20kl1`) deterministically
into the new structured shape. Unknown pending expressions fail visibly and are never coerced to a default
roll. Backfilled rows carry `schema_version = 2` (the versioning rule under **Revised PendingRollRequest**
above); untouched legacy consumed rows keep `schema_version = 1`, their nullable sequence/instruction
linkage, and their existing `consumed_turn_id`/`source_proposal_ref` provenance exactly as shipped. The
action-resolution event ledger (15b-34) requires no backfill: no historical intermediate-operation data
exists to populate it from, since the shipped implementation never persisted per-step provenance
(supersession table item 8). The migration creates the table empty; only sequences created after Phase 2
ships generate events.

`pending_roll_requests` stays one physical SQLite table with one fixed column set across both row versions
(Round 5, correcting a specification defect — Codex, PR #128, "Specify a table-level v1/v2 migration
shape"): the migration widens the five currently-`NOT NULL` legacy columns to nullable and adds the six
nullable structured columns via a standard SQLite rebuild-copy pass, then backfills the structured columns
for unconsumed rows only. No column is dropped and no row is lost. See **Revised PendingRollRequest** →
Column Disposition / physical migration shape below for the full correction.

**Rationale:** Table item 2 confirms the shipped generator only ever produces these three expressions, so
the migration's deterministic-conversion set is exhaustive against real data — but "fail visibly" is the
correct behavior for any row this ADR's inspection did not anticipate, consistent with CLAUDE.md invariant
11 (auditability from explicit event logs, not inferred state). Versioning backfilled rows as `2` rather
than leaving them at `1` keeps `schema_version` a truthful description of a row's actual column shape. A
single physical table with nullable field families, rather than an implied per-row column set, is the only
shape SQLite can actually express (Round 5) — proposing otherwise would have forced Phase 2 to choose
between dropping historical data or inventing an unspecified destructive migration.

### Group 13 — Client gate and resume UX

**Decision (15b-31, 15b-32):** The client immediately invokes resume when advancement returns
`ready_for_narration`; reloading a ready sequence produces the same resume affordance. Ordinary
in-character input remains blocked while any unresolved sequence exists; OOC remains available and does
not alter the sequence. A resume attempt against an already-completed sequence returns typed
`ACTION_SEQUENCE_ALREADY_COMPLETED`, which the client treats as success-equivalent (refetch transcript and
pending state) rather than an error toast.

**Rationale:** This directly generalizes ADR-015 Decision 10's `BLOCKED_PENDING_ROLL` gate (table item 6)
from "one pending roll row" to "any unresolved sequence state," while preserving the same block-and-redirect
philosophy Decision 10 established rather than inventing a new gate semantics.

### Group 14 — Deferred scope

**Decision (15b-33):** Cancellation, expiration, rewind, retry/regenerate, and supersession remain
deferred. Failed final narration preserves validated results and does not authorize rerolling.

**Rationale:** This is a continuation, not a resolution, of the open `known_unknowns.md` entry
"Pending-roll rewind/cancel policy" — see the `known_unknowns.md` edit accompanying this PR. The append-only
event ledger (Group 15, 15b-34) is the durable mechanism that makes "failed final narration preserves
validated results" a transactional guarantee rather than a stated intention only.

### Group 15 — Durable intermediate audit

**Decision (15b-34):** Every accepted intermediate roll, adjustment, or mechanical decision commits an
append-only action-resolution event atomically with sequence advancement. These events preserve durable
mechanical provenance without becoming sheet, canon, or delivered-result authority. `rpg_roll_audit`
remains delivery-gated and tied to a non-null final `turn_id`.

The Phase 2 contract:

- A dedicated append-only event table, or an equivalent normalized immutable persistence shape, owned by
  the action-resolution subsystem. Exact repository-native naming/schema is a mandatory Phase 2 advisor
  checkpoint — not decided here, in the same way Group 8 leaves the shared-machinery extraction shape to
  an advisor checkpoint rather than guessing at it.
- Events are keyed by `sequence_id`, `step_id`, an ordered event identity, and event kind, and carry stable
  `story_id`/`session_id`/`character_id` identity directly on the common envelope (Round 5) — so final audit
  construction never needs to join `ActionResolutionSequence` or `RpgSessionState` for these values.
- Every accepted `ResolvedStepKind` is covered: player roll, AI roll, hidden roll, adjustment, and
  mechanical decision.
- Each event preserves provisional effects, timestamps, and mechanical provenance in its common envelope,
  plus a kind-discriminated payload: roll-kind events preserve the applicable instruction snapshot,
  submission source, raw or aggregate input, and derived selections/subtotal/total/outcome; adjustment
  events preserve the resulting instruction snapshot and a string accepted option ID; mechanical-decision
  events preserve the complete decision snapshot (including decision ID and revision) and a string accepted
  option ID. No event carries fields outside its own kind's payload (see **Action-Resolution Event Ledger**
  below for the exact shape).
- The event and its corresponding sequence advancement commit atomically — one write, one commit; no
  partially-advanced sequence with a missing event, and no orphaned event without a matching advancement.
- Invalid, stale, rejected, or duplicate submissions change neither the sequence nor the event ledger.
- Append-only behavior is enforced at the database layer — the same trigger-based pattern `rpg_roll_audit`
  already uses (`persistence/orm/rpg.py:23`, migration 0011). Phase 2's migration and tests must cover it.
- `rpg_roll_audit` stays semantically unchanged as the final delivered-result audit: non-null `turn_id`,
  written only inside the final delivery transaction, per ADR-015 Decision 1.
- On successful narration: final `rpg_roll_audit` rows are derived from the immutable action-resolution
  events, sheet effects apply, the sequence completes, and all of it commits together with the delivered
  Turn. This derivation is field-complete (Round 5): every `rpg_roll_audit` column other than DB-generated
  identity and the final `turn_id` has a named source on the roll event's envelope, payload, or embedded
  `RollInstructionSnapshot` — see **Final Audit Projection** below.
- On blocked, refused, or failed final narration: the Turn, `rpg_roll_audit` rows, sheet effects, and
  sequence completion roll back exactly as ADR-015 Decision 1 already requires — but the previously
  committed `ready_for_narration` sequence and its event ledger survive that rollback undisturbed. A later
  resume attempt reuses exactly those recorded mechanics; it does not authorize rerolling, re-deciding, or
  regenerating a different outcome (continuation of 15b-33).

**Rationale:** This is audit completeness and transaction correctness, not anti-cheat or fairness
enforcement — Group 5's disclaimer (15b-17) still governs cryptographic/attestation scope. Supersession
table item 8 identified a real gap: nothing durable survives between "a mechanical operation was accepted"
and "the Turn that narrates it is delivered," which forces Phase 2 to choose between losing a validated
result on rollback or persisting trust-relevant mechanics outside any audit boundary. An append-only event
ledger closes that gap without touching ADR-015's delivery-transaction rollback discipline: sequence state
remains provisional operational state with no independent audit weight, the event ledger is immutable
pre-delivery provenance, and `rpg_roll_audit` remains the sole final delivered-result audit. Committing the
event atomically with sequence advancement — rather than as an afterthought write — is what makes "no lost
validated result" a transactional guarantee instead of a best-effort one.

### Group 16 — Persisted decision request snapshot

**Decision (15b-35):** A pending mechanical decision is backed by the same stored-snapshot authority
pattern as a pending roll. `MechanicalDecisionSnapshot` is the backend-authoritative record — analogous to
`RollInstructionSnapshot` — persisted for the lifetime of the pending decision and referenced by the
sequence's `current_decision_request_id`. `PendingMechanicalDecisionView` gains a `decision_revision`
field; a decision submission requires `expected_decision_revision`, validated and rejected/rehydrated on
mismatch exactly as `expected_instruction_revision` already governs roll submissions (15b-13).
`ResolvedSequenceStep` gains `decision_snapshot: MechanicalDecisionSnapshot | None` and
`accepted_option_id: str | None` alongside its existing roll-shaped fields, so a `MECHANICAL_DECISION`
step's stored authority — and the audit/event row later reconstructed from it (15b-34) — never depends on
re-reading live adapter or Character Sheet state at validation or reconstruction time.

**Rationale:** ADR-015b already requires this level of authority for rolls — a structured snapshot, stable
identity (`term_id`/`instruction_id`), and revision-gated staleness rejection. Mechanical decisions are a
first-class pending-interaction kind (15b-19), not a lesser one, and the inherited ADR-015 principle of
"stored-snapshot authority over later live-state drift" (see **Inherited ADR-015 Decisions** below)
already applies to both interaction kinds — this decision makes that application explicit instead of
leaving decisions as the one interaction kind without a defined stored contract. Removing mechanical
decisions from scope was the offered alternative, but it would silently cut acceptance criterion 11, the
`submit_decision` service method, `MECHANICAL_DECISION_INVALID`, and `SequenceInteractionKind.DECISION` —
a materially smaller lifecycle than the one already accepted across 15b-19 through 15b-24 — so the
additive fix is the correct, smaller change.

---

## Inherited ADR-015 Decisions (not reopened)

Per the governing spec, Issue 15b does not reopen:

- the dedicated RPG adjudication pass (ADR-015 Fork A / Decision 2);
- code-owned trust-relevant mechanics (ADR-015 Decision 3);
- code-applied sheet effects outside Extractor proposals (ADR-015 Fork B);
- the existing delivery transaction and rollback discipline (ADR-015 Decision 1);
- stored-snapshot authority over later live-state drift;
- Writer visibility filtering (ADR-015 Decision 5);
- the core pipeline and disposition taxonomy (ADR-015 Decision 10, generalized per Group 13 above, not
  replaced);
- deferred cancellation and rewind semantics (Group 14 above).

---

## Roll Instruction Contract (shapes)

Architectural sketches; equivalent repository-native shapes are acceptable if they preserve these fields
and invariants.

```python
class RollPurpose(str, Enum):
    ATTACK = "attack"
    SAVING_THROW = "saving_throw"
    ABILITY_CHECK = "ability_check"
    SKILL_CHECK = "skill_check"
    DAMAGE = "damage"
    HEALING = "healing"
    DURATION = "duration"
    CONTESTED = "contested"


class DiceSelectionRule(str, Enum):
    SUM_ALL = "sum_all"
    KEEP_HIGHEST = "keep_highest"
    KEEP_LOWEST = "keep_lowest"


class RollContribution(str, Enum):
    ADD = "add"
    SUBTRACT = "subtract"


class RollTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    term_id: UUID
    count: int
    sides: int
    selection_rule: DiceSelectionRule
    keep_count: int | None = None
    contribution: RollContribution = RollContribution.ADD
    label: str | None = None
```

Required validation: bounded positive `count`/`sides`; `keep_count` only for keep operations;
`1 <= keep_count <= count`; adapter approval for supported dice/operations; no arbitrary formula
execution.

```python
class RollInstructionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    instruction_id: UUID
    instruction_revision: int
    purpose: RollPurpose
    terms: tuple[RollTerm, ...]
    modifier_components: tuple[RollModifierComponent, ...]
    display_expression: str
    display_label: str
    dc: int | None = None
    source_rule_refs: tuple[str, ...]
    adjustment_options: tuple["RollAdjustmentOption", ...]
    sequence_id: UUID
    step_id: UUID
```

`dc` (Round 5) is the code-verified difficulty/target value for checks that compare `total` against one —
attack vs. AC, save vs. DC, skill check vs. DC — verified at the Proposal-to-Instruction Boundary the same
way purpose, modifier, and target are; it is `None` for rolls with no compare-outcome, such as damage or
duration. `dc` is backend-only and never appears in `PlayerRollInstructionView`, the same non-leak rule
`ability_id` follows on `PlayerAdjustmentOptionView` (Group 5). This closes a completeness gap in the final
`rpg_roll_audit` projection (Group 15, 15b-34) — see **Final Audit Projection** below — not a new roll
mechanic; it is required propagation of 15b-34, not a Group 2 reopening.

`RollModifierComponent` carries `modifier_id`, `label`, `value`, `visibility` (`PLAYER_VISIBLE`/`HIDDEN`),
`source_kind`, `source_reference`. Player-visible projections (`PlayerRollTermView`,
`PlayerModifierView`, `PlayerAdjustmentOptionView`, `SequenceProgressView`,
`PlayerRollInstructionView`) omit every backend-only field, per Group 5 above — `ability_id` in
particular never appears in `PlayerAdjustmentOptionView`.

---

## Mechanical Decision Contract

Per 15b-35. Architectural sketch; an equivalent repository-native shape is acceptable if it preserves
these fields and invariants — the same disclaimer that governs the Roll Instruction Contract above.

```python
class MechanicalDecisionOptionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    option_id: str
    player_visible_label: str
    source_rule_ref: str | None = None
    provisional_effects_json: str


class MechanicalDecisionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    decision_id: UUID
    decision_revision: int
    prompt: str
    options: tuple[MechanicalDecisionOptionSnapshot, ...]
    source_rule_refs: tuple[str, ...]
    sequence_id: UUID
    step_id: UUID
```

Required validation: at least one option; every `option_id` unique within a snapshot; adapter approval for
supported decision kinds — no arbitrary option execution, mirroring `RollTerm`'s "no arbitrary formula
execution" constraint.

`option_id`, `player_visible_label`, and `prompt` are the only fields that ever reach a player-facing view.
`source_rule_ref` and `provisional_effects_json` are backend-only, per Group 5 — parity with `ability_id`
never appearing in `PlayerAdjustmentOptionView`.

`PendingMechanicalDecisionView` (player-visible) gains `decision_revision: int`, mirroring
`PlayerRollInstructionView.instruction_revision`:

```python
class PendingMechanicalDecisionView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    decision_request_id: UUID
    sequence_id: UUID
    decision_revision: int
    interaction_phase: Literal[RpgInteractionPhase.PENDING_MECHANICAL_DECISION]
    prompt: str
    options: tuple[MechanicalDecisionOption, ...]
```

Submission mirrors the roll submission shapes' stale-revision guard:

```python
class MechanicalDecisionSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    decision_request_id: UUID
    expected_decision_revision: int
    option_id: str
```

`ResolvedSequenceStep` gains two fields alongside its existing roll-shaped ones, so a `MECHANICAL_DECISION`
step carries the same stored authority a roll step does:

```python
decision_snapshot: MechanicalDecisionSnapshot | None
accepted_option_id: str | None
```

For `MECHANICAL_DECISION` steps, `decision_snapshot`/`accepted_option_id` are populated and the
roll-shaped fields (`instruction_snapshot`, `submitted_term_results`, `derived_term_results`, etc.) are
`None`/empty; for roll-kind steps the reverse holds. Validating a decision submission (option membership,
`decision_revision` staleness) and reconstructing its later audit/event row (15b-34) both read only from
the stored `MechanicalDecisionSnapshot` — never from live adapter or Character Sheet state.

---

## Action-Resolution Sequence

```python
class ActionResolutionStatus(str, Enum):
    ACTIVE = "active"
    READY_FOR_NARRATION = "ready_for_narration"
    COMPLETED = "completed"


class SequenceInteractionKind(str, Enum):
    ROLL = "roll"
    DECISION = "decision"
    NONE = "none"
```

`ActionResolutionSequence` persists `sequence_id`, `story_id`, `session_id`, `node_id`, `character_id`,
`originating_turn_id`, `status`, `current_interaction_kind`, current pending roll/decision request IDs,
`resolved_steps`, `projected_state_json`, `provisional_effects_json`, timestamps. Repository-native
normalization is permitted, but identity, status, and uniqueness constraints must not be hidden inside one
opaque JSON blob.

`session_id` (Round 5) is required so RPG session identity survives on the durable sequence itself: without
it, deriving final audit rows after a blocked/failed narration and resume would have to re-read mutable
`RpgSessionState` rather than reconstruct from durable mechanical records, and `AI_ROLL`/`HIDDEN_ROLL`
events have no `PendingRollRequest` row to recover it from. `ReadyActionResolutionBundle` gains the same
field for the same reason — see Issue #127's **Ready Bundle** section.

```sql
CREATE UNIQUE INDEX uq_unresolved_action_resolution_per_story
ON action_resolution_sequences(story_id)
WHERE status IN ('active', 'ready_for_narration');
```

This follows the existing partial-unique-index pattern used by active pending rolls
(`persistence/orm/rpg.py:65-72`).

`resolved_steps` is the sequence's own provisional working view of accepted steps — it supports gating,
projection, and resume without a second read. It is not the durable audit record: append-only mechanical
provenance for every accepted step lives in the action-resolution event ledger below (15b-34), independent
of whatever normalized or JSON-backed shape `resolved_steps` itself takes.

---

## Action-Resolution Event Ledger

Per 15b-34. Architectural sketch; an equivalent repository-native shape is acceptable if it preserves
append-only enforcement, atomic commit with sequence advancement, and the fields below.

The event is a common envelope carrying only genuinely common fields — event/sequence/step identity, event
order, kind, provenance, provisional effects, and timestamp — plus a kind-discriminated `payload`. This is
required propagation of 15b-34 and 15b-35, not a new decision: rolls, adjustments, and mechanical decisions
are different authority shapes (a bounded dice result, a revised instruction, a chosen decision option) and
a single roll-shaped record cannot carry decision identity without either fabricating a roll `instruction_id`
for a decision or losing `decision_id`/`decision_revision` entirely.

```python
class RollEventPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    kind: Literal[
        ResolvedStepKind.PLAYER_ROLL, ResolvedStepKind.AI_ROLL, ResolvedStepKind.HIDDEN_ROLL
    ]
    instruction_snapshot: RollInstructionSnapshot
    submission_source: RollSubmissionSource | None
    pending_roll_request_id: UUID | None
    raw_input_json: str | None
    aggregate_input_json: str | None
    derived_selections_json: str
    subtotal: int | None
    total: int
    outcome: Literal[
        "success", "failure", "critical_success", "critical_failure", "undetermined"
    ]
    gm_cheating_at_roll: bool


class AdjustmentEventPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    kind: Literal[ResolvedStepKind.ADJUSTMENT] = ResolvedStepKind.ADJUSTMENT
    resulting_instruction_snapshot: RollInstructionSnapshot
    accepted_adjustment_option_id: str


class MechanicalDecisionEventPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    kind: Literal[ResolvedStepKind.MECHANICAL_DECISION] = ResolvedStepKind.MECHANICAL_DECISION
    decision_snapshot: MechanicalDecisionSnapshot
    accepted_decision_option_id: str


class ActionResolutionEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    event_id: UUID
    sequence_id: UUID
    step_id: UUID
    story_id: UUID
    session_id: UUID
    character_id: UUID
    event_order: int
    kind: ResolvedStepKind
    mechanical_provenance: str
    provisional_effects_json: str
    created_at: datetime
    payload: RollEventPayload | AdjustmentEventPayload | MechanicalDecisionEventPayload
```

`story_id`, `session_id`, and `character_id` (Round 5) are stable identity carried directly on every event,
regardless of kind — genuinely common fields, not roll-specific ones, since every event belongs to exactly
one story/session/character. This is what lets a `RollEventPayload`-carrying event supply
`rpg_roll_audit.story_id`/`session_id`/`character_id` on its own: final audit construction never needs to
join `ActionResolutionSequence` or `RpgSessionState` for these values (see **Final Audit Projection**
below).

Required cross-field invariants: `kind` and `payload.kind` agree — `PLAYER_ROLL`/`AI_ROLL`/`HIDDEN_ROLL`
require `RollEventPayload`; `ADJUSTMENT` requires `AdjustmentEventPayload`; `MECHANICAL_DECISION` requires
`MechanicalDecisionEventPayload`; no other kind/payload combination is constructible. A
`MechanicalDecisionEventPayload` carries no `instruction_id`, `instruction_revision`, or other roll-instruction
field — a decision event never fabricates a roll identity. A `RollEventPayload` carries no `decision_snapshot`
or `accepted_decision_option_id` — a roll event never carries decision fields. `accepted_adjustment_option_id`
and `accepted_decision_option_id` are `str`, matching `option_id`'s type on `RollAdjustmentOption` and
`MechanicalDecisionOptionSnapshot`; neither is ever `UUID`. `MechanicalDecisionEventPayload.decision_snapshot`
carries the complete immutable `MechanicalDecisionSnapshot`, including `decision_id` and `decision_revision`,
so a `MECHANICAL_DECISION` event never depends on `ActionResolutionSequence.resolved_steps` or other mutable
sequence state to reconstruct its accepted authority.

`RollEventPayload.pending_roll_request_id` (Round 5) is required (non-null) for `kind == PLAYER_ROLL` — the
Sojourner always submits against a real `PendingRollRequest` row — and null for `AI_ROLL`/`HIDDEN_ROLL`,
which have no player-facing pending-roll row to link. It is never reconstructed later from
`PendingRollRequest`; the event is the sole source once written, so it survives the pending row's own
mutation-in-place lifecycle. `RollEventPayload.gm_cheating_at_roll` (Round 5) is a snapshot of the session's
`gm_cheating` config taken at roll-acceptance time — the same "immutable once set" snapshot the shipped
`ResolvedAdjudicationRecord.gm_cheating_at_roll` already takes, moved onto the durable event so final audit
construction never re-reads live `RpgSessionState`.

Only `RollEventPayload`-carrying events (`PLAYER_ROLL`, `AI_ROLL`, `HIDDEN_ROLL`) ever produce a final
`rpg_roll_audit` row. `ADJUSTMENT` and `MECHANICAL_DECISION` events remain append-only mechanical
provenance and are never forced into `rpg_roll_audit`'s roll-shaped columns.

`RollEventPayload.total` and `RollEventPayload.outcome` are non-null for every accepted `PLAYER_ROLL`,
`AI_ROLL`, or `HIDDEN_ROLL` event (Round 6, correcting a P1: Codex, PR #128, "Require non-null roll totals
in audit projection") — matching the shipped `ResolvedAdjudicationRecord.total: int` and its non-null
bounded `outcome` (`models/rpg.py:137-149`), which the Final Audit Projection below writes directly into
the existing non-null `rpg_roll_audit.total`/`outcome` columns. `outcome` uses the same repository-native
bounded set `ResolvedAdjudicationRecord` and `WriterAdjudicationView` already use —
`"success"`/`"failure"`/`"critical_success"`/`"critical_failure"`/`"undetermined"` — not a new vocabulary.
Only `RollInstructionSnapshot.dc` remains nullable: when a roll has no compare-outcome target (damage,
healing, duration), `dc` is `None` and the event's `outcome` is the already-shipped `"undetermined"` value,
never a null outcome or an invented sixth value. Hidden-roll events retain complete internal `total`, `dc`
(via `instruction_snapshot`), and `outcome` authority — identical in shape to a player or AI roll event;
`ResolvedAdjudicationRecord`'s docstring already establishes that redaction happens only in the
Writer-facing view, not the internal record (`models/rpg.py:14-15, 160-161`), and this ADR does not reopen
that boundary. `WriterAdjudicationView.total`/`dc`/`outcome` stay `None` for `HIDDEN` visibility exactly as
shipped — this is existing, unchanged Group 5 (15b-16, 15b-17) behavior, restated here only to make explicit
that it is unaffected by the event payload becoming non-null.

### Audit Contract

Three layers now exist, and none of them stand in for another:

- **`ActionResolutionSequence` state** (`resolved_steps`, `projected_state_json`,
  `provisional_effects_json`) is provisional operational state. It advances as the sequence advances and
  carries no independent audit weight.
- **The action-resolution event ledger** is immutable pre-delivery mechanical provenance. Once written, an
  event is never updated or deleted; it durably records that a specific mechanical outcome was accepted,
  but it is not sheet, canon, or delivered-result authority on its own.
- **`rpg_roll_audit`** remains the sole final delivered-result audit, semantically unchanged from ADR-015:
  non-null `turn_id`, written only inside the final delivery transaction. At successful narration, final
  `rpg_roll_audit` rows are derived from the corresponding `RollEventPayload`-carrying event-ledger rows —
  this promotes already-durable provenance into the delivered-result record, it does not duplicate
  authority. `ADJUSTMENT` and `MECHANICAL_DECISION` events are never derived into `rpg_roll_audit`; they
  remain append-only mechanical provenance only.

### Final Audit Projection

Per 15b-34 (Round 5, required propagation — not a new decision): the immutable-event-to-final-audit
contract is field-complete. Every `rpg_roll_audit` column other than the two DB/transaction-supplied
identities below is sourced from a single `RollEventPayload`-carrying event's envelope, payload, or
embedded `RollInstructionSnapshot` — never from `ActionResolutionSequence`, `RpgSessionState`,
`PendingRollRequest`, adapter, or Character Sheet state.

| `rpg_roll_audit` column | Source |
|---|---|
| `global_sequence` | DB-generated (SQLite rowid); not sourced from the event. |
| `turn_id` | The final delivery transaction's provisional `turn_id` (ADR-015 Decision 1); not sourced from the event. |
| `story_id` | `event.story_id` (envelope). |
| `session_id` | `event.session_id` (envelope). |
| `character_id` | `event.character_id` (envelope). |
| `check_label` | `payload.instruction_snapshot.display_label`. |
| `visibility` | Derived from `event.kind`: `PLAYER_ROLL` → `RollVisibility.PLAYER`; `AI_ROLL` → `RollVisibility.SHOWN`; `HIDDEN_ROLL` → `RollVisibility.HIDDEN` — the same three-way distinction `ResolvedStepKind`'s roll values already encode, so no separate field is needed. |
| `expression` | `payload.instruction_snapshot.display_expression` (display text only, per 15b-3 — never audit authority in its own right). |
| `raw_rolls_json` | The flat per-die values reconstructed from `payload.derived_selections_json` when `raw_input_json` is complete; `"[]"` (never fabricated) for aggregate-only physical reports — see below. |
| `modifiers_json` | Serialized `payload.instruction_snapshot.modifier_components`. |
| `total` | `payload.total` (non-null — Round 6). |
| `dc` | `payload.instruction_snapshot.dc` (new field; `None` when the check has no compare-outcome target — the only nullable field in this row group). |
| `outcome` | `payload.outcome` (non-null — Round 6; `"undetermined"` when `dc` is `None`). |
| `source` | Derived from `event.kind`: `PLAYER_ROLL` → `"player"`; `AI_ROLL` → `"ai"`; `HIDDEN_ROLL` → `"hidden"`. |
| `gm_cheating_at_roll` | `payload.gm_cheating_at_roll` (new field). |
| `sheet_effects_json` | `event.provisional_effects_json` (envelope). |
| `created_at` | `event.created_at` (envelope) — the roll's own acceptance timestamp, not the final-delivery commit timestamp. |
| `sequence_id` | `event.sequence_id` (envelope). |
| `step_id` | `event.step_id` (envelope). |
| `pending_roll_request_id` | `payload.pending_roll_request_id` (new field; non-null for `PLAYER_ROLL`, null for `AI_ROLL`/`HIDDEN_ROLL`). |
| `instruction_id` | `payload.instruction_snapshot.instruction_id`. |
| `instruction_revision` | `payload.instruction_snapshot.instruction_revision`. |
| `instruction_schema_version` | `payload.instruction_snapshot.schema_version`. |
| `instruction_snapshot_json` | Serialized `payload.instruction_snapshot` in full. |
| `submission_source` | `payload.submission_source`. |
| `raw_values_complete` | `true` when `payload.raw_input_json` carries complete per-term raw values (inline UI, physical raw report, or `BACKEND_DICE_SERVICE` — the backend dice service always knows every die); `false` for aggregate-only physical reports. |

**Aggregate-only physical-report projection:** when `RollEventPayload.raw_input_json` is null and
`aggregate_input_json` carries the reported aggregate (15b-15), the payload records no per-die values —
`derived_selections_json` reflects that no raw selection was derived (an empty/no-op structure, never
invented die values), `total` is the reported aggregate as validated by code (still non-null — an
aggregate-only report supplies a total by definition), and `outcome` is derived from `total` vs `dc` exactly
as for a raw submission, or `"undetermined"` when `dc` is `None`; `outcome` is never null here either. At
final-audit projection, `raw_rolls_json` becomes `"[]"` — an honest "no raw dice recorded" value, not a
fabricated one — and `raw_values_complete = false` is the authoritative flag a consumer must check before
treating `raw_rolls_json` as complete per-die provenance.

**Sibling check (Round 6):** every other column in the table above was compared, destination nullability
against source nullability. `total` and `outcome` were the only `NOT NULL` `rpg_roll_audit` columns fed by a
then-nullable source; no other column has that direction of mismatch. `dc` is the sole intentionally
nullable destination, fed by the equally nullable `RollInstructionSnapshot.dc` — consistent by design, not a
contradiction. Every other `NOT NULL` destination (`story_id`, `session_id`, `character_id`, `check_label`,
`visibility`, `expression`, `raw_rolls_json`, `modifiers_json`, `source`, `gm_cheating_at_roll`,
`sheet_effects_json`, `created_at`) is already fed by a non-null envelope/payload/snapshot field or a
derivation that always produces a value. The nine nullable `rpg_roll_audit` columns added for legacy-row
compatibility are fed by sources of equal or narrower nullability, which is always safe. This check found no
further contradiction and does not broaden the contract beyond the `total`/`outcome` correction above.
`total`, `outcome`, `modifiers_json`, and every other projected column remain fully authoritative regardless
of `raw_values_complete`; only per-die granularity is missing, consistent with 15b-15's "never fabricates
raw dice for an aggregate-only report."

### Transaction Lifecycle

Two transaction boundaries apply, and Phase 2 must not conflate them:

1. **Intermediate transaction** (new, per 15b-34): committing an accepted roll, adjustment, or mechanical
   decision writes one action-resolution event and advances the sequence (status,
   `current_interaction_kind`, pending request IDs, `resolved_steps`) atomically. Invalid, stale, rejected,
   or duplicate submissions commit neither. This transaction has no provider call, no settlement, and adds
   no `PipelineDisposition` value (Group 10, 15b-27/15b-28) — extended by this decision, not contradicted.
2. **Final delivery transaction** (ADR-015 Decision 1, unchanged): on successful `orchestrate_rpg_resume`,
   the outer 12c transaction derives `rpg_roll_audit` rows from the event ledger's `RollEventPayload`-carrying
   rows only, applies sheet effects,
   marks the sequence `completed`, and commits all of it together with the delivered Turn. On block
   (Output Safety, Contradiction, provider refusal, pipeline error), the existing 12c rollback removes the
   Turn, the derived `rpg_roll_audit` rows, and the sheet mutations — exactly as ADR-015 Decision 1 already
   specifies. It does **not** remove the previously committed `ready_for_narration` sequence or its event
   ledger; those were committed by the intermediate transaction, not the final one, and survive.

### Narration Readiness and Recovery

- **Success:** `orchestrate_rpg_resume` derives final audit rows from the immutable events, applies
  effects, completes the sequence, and commits with the delivered Turn (final delivery transaction above).
- **Blocked, refused, or failed narration:** the final Turn, `rpg_roll_audit` rows, sheet effects, and
  sequence completion roll back per ADR-015 Decision 1. The previously committed `ready_for_narration`
  sequence and its event ledger are preserved untouched. A later resume attempt against that sequence
  reuses exactly the recorded mechanics — it does not authorize rerolling, re-deciding, or regenerating a
  different outcome (continuation of 15b-33). An identical-facts retry of the same resume attempt is
  idempotent against the same event ledger, not a second independent roll.

This is audit completeness and transaction correctness, not anti-cheat or fairness enforcement (Group 5,
15b-17 still governs that boundary).

---

## Revised PendingRollRequest

The shipped row's actual primary-key/column names differ from an earlier draft of this section, which a
Codex review of this document (round 1) caught: the persisted row's identity column is `request_id`, not
`pending_roll_request_id`; there is no `consumed_at` column (only `consumed_turn_id`); `source_proposal_ref`
and `schema_version` are shipped columns this table previously omitted; and `session_id` carries no
foreign key today. The corrections below apply to both this ADR and the governing Issue #127 spec, which
carried the same error in its own "Revised Row" sketch and column table — this was a specification defect,
not solely an ADR transcription error.

### Column Disposition

`pending_roll_requests` remains one physical SQLite table with one fixed column set for every row — SQLite
has no mechanism for a table to carry different columns per row, and no wording below may be read as
implying otherwise (Round 5, correcting a specification defect: Codex, PR #128, "Specify a table-level
v1/v2 migration shape"). "Retire after backfill" in the table means retired from `schema_version = 2`
reads, writes, and authority — it does not mean the column is physically dropped. Every retired column
stays present and nullable so historical `schema_version = 1` rows keep their populated, authoritative
legacy data undisturbed; physical column removal is a future cleanup only after v1 compatibility ends, and
is out of scope for Issue 15b. See the physical migration shape below the versioning rule for how the
existing `NOT NULL` legacy text columns become nullable without data loss.

| Shipped field (`models/rpg.py:184-221`) | Disposition |
|---|---|
| `request_id` | Retain as the persisted row's identity (primary key). Public submission DTOs and the new `rpg_roll_audit` linkage column may still name this `pending_roll_request_id` — that name remains legitimate at the DTO/audit layer; this table is not a mandate to rename it there. |
| `story_id` | Retain. |
| `session_id` | Retain **as shipped** — this column carries no foreign key today, and this ADR does not add one. |
| `character_id` | Retain with existing FK behavior. |
| `originating_turn_id` | Retain. |
| `visibility` | Retain; player-visible reads continue to depend on it. |
| `status` | Retain and preserve all four enum values (`pending`, `consumed`, `cancelled`, `expired`) — `cancelled`/`expired` stay dormant per Group 3. |
| `created_at` | Retain. |
| `consumed_turn_id` | Retain, nullable, for historical consumed rows. New deterministic consumption (15b-25) creates no narrative Turn, so new rows normally leave this null — it is not backfilled with a synthetic value. |
| `source_proposal_ref` | Retain as internal provenance. This is the smallest safe disposition absent a specified lossless migration destination for this field. |
| `schema_version` | Retain the column; **bump the value for the materially revised row contract** rather than silently calling both the legacy and new row shapes version 1 — see the versioning rule below. |
| `adapter_context_hash` | Retain as an internal drift diagnostic; non-authoritative, non-public. |
| `roll_expression` | Retire after backfill; derive display text from the structured snapshot. |
| `expected_value_shape` | Retire after backfill; derive from structured terms. |
| `visible_modifier_total` | Retire after backfill; derive from visible modifier components. |
| `visible_modifier_breakdown_json` | Retire after backfill; derive from structured modifier components. |
| `check_label` | Retire after backfill; replace with `purpose` and `display_label`. |
| `player_facing_instruction` | Retire after backfill; replace with the public instruction projection. |
| `visible_modifier_note` | Retire after backfill; replace with player-visible modifier labels. |
| `hidden_modifier_present` | Retire after backfill; internal code derives hidden-modifier existence from `ModifierVisibility.HIDDEN`, never exposed publicly. |

New fields required on new rows: `sequence_id`, `step_id`, `instruction_id`, `instruction_revision`,
`instruction_schema_version`, `instruction_snapshot_json`. Legacy consumed rows may retain nullable
sequence/instruction linkage, provenance (`source_proposal_ref`), and row-version information exactly as
shipped.

**`schema_version` versioning rule (Round 5 — corrects a specification defect, not a new decision):**
`schema_version` identifies which *field family is authoritative* for a row, not which columns physically
exist on it — every row has the same physical column set. The eight legacy display/derivation columns
(`roll_expression`, `expected_value_shape`, `visible_modifier_total`, `visible_modifier_breakdown_json`,
`check_label`, `player_facing_instruction`, `visible_modifier_note`, `hidden_modifier_present`) and the six
structured v2 columns (`sequence_id`, `step_id`, `instruction_id`, `instruction_revision`,
`instruction_schema_version`, `instruction_snapshot_json`) are both physically present, nullable, on every
row; each family is populated only for the rows that need it:

- `schema_version = 1` (legacy row shape): the eight legacy columns are populated and authoritative; the
  six structured columns are null.
- `schema_version = 2` (revised row shape): the six structured columns are populated and authoritative; the
  eight legacy columns may be null — they are not backfilled with synthetic legacy values — and are never
  read as authoritative for that row regardless of whatever value, if any, physically remains in them.

A row's `schema_version` reflects which family is authoritative, not merely its creation order: rows
created by `ActionResolutionService.start_sequence` are `schema_version = 2` with legacy columns left null;
legacy pending rows the migration backfills into a real `ActionResolutionSequence` (Migration item 6) become
`schema_version = 2` once backfilled — their original legacy column values may remain physically present
from the original insert, but code must not read them as authoritative once `schema_version = 2`; legacy
*consumed* rows that are not backfilled with real structured data (Migration item 7) remain
`schema_version = 1`, with their legacy columns populated and authoritative and their structured columns
null. No row is ever silently relabeled version 1 after gaining a structured instruction, and no row is
labeled version 2 without one.

**Physical migration shape (Round 5):** five shipped legacy columns are currently `NOT NULL`
(`check_label`, `player_facing_instruction`, `expected_value_shape`, `roll_expression`,
`persistence/orm/rpg.py:96-109`; and `hidden_modifier_present`, `persistence/orm/rpg.py:116-118` — it
carries `server_default="0"`, but must still widen to nullable rather than silently default to `False`,
which would read as an authoritative "no hidden modifier" claim on a `schema_version = 2` row that actually
has one) and must become nullable so `schema_version = 2` rows can leave them null rather than fabricating
legacy content. SQLite cannot alter a column's `NOT NULL` constraint in place, so Phase 2's migration uses
the standard SQLite rebuild-copy shape for this table: wrap the rebuild in `PRAGMA foreign_keys=OFF` /
`PRAGMA foreign_keys=ON`; create a new table with the full target column set (the five legacy columns above
widened to nullable, plus the six new nullable structured columns) and the same outgoing foreign keys —
`character_id` (`RESTRICT`), `originating_turn_id` (`CASCADE`), `consumed_turn_id` (`SET NULL`),
`story_id` (`CASCADE`) — reproduced verbatim, not merely implied; copy every existing row across unchanged;
drop the old table; rename the new table into place; recreate the `uq_pending_roll_requests_story_active`
partial unique index verbatim; and run `PRAGMA foreign_key_check` before commit. No row is dropped or
truncated by this step; it only widens nullability and adds columns. The deterministic-expression backfill
(Migration items 3, 6, 7) runs after the rebuild, against the now-nullable structured columns. Physical
removal of the five legacy columns is out of scope for Issue 15b — see the Column Disposition note above.

If Phase 2 source inspection identifies a compatibility consumer of a retired field that cannot be
migrated cleanly, that is a stop-and-flag event against 15b-25, not a reason to retain a second authority.

---

## Errors (typed, additive)

```text
PENDING_ROLL_NOT_FOUND
PENDING_ROLL_NOT_PLAYER_VISIBLE
PENDING_ROLL_ALREADY_CONSUMED
PENDING_ROLL_REVISION_MISMATCH
PENDING_ROLL_TERM_MISMATCH
PENDING_ROLL_INVALID_VALUE
PENDING_ROLL_INVALID_AGGREGATE
ACTION_SEQUENCE_NOT_FOUND
ACTION_SEQUENCE_ALREADY_COMPLETED
ACTION_SEQUENCE_STATE_CONFLICT
ACTION_ADJUSTMENT_NOT_ALLOWED
ACTION_ADJUSTMENT_INELIGIBLE
MECHANICAL_DECISION_INVALID
MECHANICAL_DECISION_REVISION_MISMATCH
SEQUENCE_NOT_READY_FOR_NARRATION
```

Exact names follow repository conventions; validation precedes atomic consumption in every case.

---

## Consequences

- `RollPurpose`, `DiceSelectionRule`, `RollContribution`, `RollTerm`, `ModifierVisibility`,
  `RollModifierComponent`, `RollInstructionSnapshot`, `RpgInteractionPhase`, `PlayerRollTermView`,
  `PlayerModifierView`, `PlayerAdjustmentOptionView`, `SequenceProgressView`,
  `PlayerRollInstructionView`, `MechanicalDecisionOption`, `PendingMechanicalDecisionView`,
  `ActionResolutionAdvanceResult`, `RollAdjustmentTiming`, `RollAdjustmentOption`,
  `ActionResolutionStatus`, `SequenceInteractionKind`, `ActionResolutionSequence`,
  `DerivedRollTermResult`, `ResolvedStepKind`, `RollSubmissionSource`, `ResolvedSequenceStep`,
  `ReadyActionResolutionBundle`, `PlayerRollTermResult`, `RawPlayerRollSubmission`,
  `PhysicalAggregateRollSubmission`, `ActionResolutionEvent`, `RollEventPayload`, `AdjustmentEventPayload`,
  `MechanicalDecisionEventPayload`, `MechanicalDecisionOptionSnapshot`, `MechanicalDecisionSnapshot`,
  `MechanicalDecisionSubmission` are added (Phase 2).
- `PendingMechanicalDecisionView` gains `decision_revision`; `ResolvedSequenceStep` gains
  `decision_snapshot` and `accepted_option_id` (Phase 2; 15b-35).
- `ActionResolutionSequence` and `ReadyActionResolutionBundle` gain `session_id`; `RollInstructionSnapshot`
  gains `dc`; `ActionResolutionEvent`'s common envelope gains `story_id`/`session_id`/`character_id`;
  `RollEventPayload` gains `pending_roll_request_id` and `gm_cheating_at_roll` (Phase 2; Round 5, required
  propagation of 15b-34 — see **Final Audit Projection** above). `RollEventPayload.total` and `.outcome`
  become non-null, `outcome` typed to the shipped bounded set (Phase 2; Round 6, required propagation of
  15b-34, correcting a P1 insert-failure risk against the existing non-null `rpg_roll_audit` columns).
- `PendingRollRequest` is revised per the Column Disposition table above (Phase 2, migration). The five
  currently-`NOT NULL` legacy columns (`check_label`, `player_facing_instruction`, `expected_value_shape`,
  `roll_expression`, `hidden_modifier_present`) widen to nullable via a SQLite rebuild-copy migration,
  alongside the six new nullable structured columns — one physical table, two nullable field families, no dropped
  columns or rows (Phase 2, migration; Round 5, required propagation of 15b-30).
- `action_resolution_sequences` table added with the partial unique index above (Phase 2, migration).
- `action_resolution_events` table added as an append-only ledger (DB-layer UPDATE/DELETE triggers, same
  pattern as `rpg_roll_audit`), keyed by `sequence_id`/`step_id`/event order, committed atomically with
  sequence advancement, requiring no backfill (Phase 2, migration; 15b-34).
- `rpg_roll_audit` gains nullable columns: `sequence_id`, `step_id`, `pending_roll_request_id`,
  `instruction_id`, `instruction_revision`, `instruction_schema_version`, `instruction_snapshot_json`,
  `submission_source`, `raw_values_complete` (Phase 2, migration). Every column's source is now named in
  **Final Audit Projection** above (Round 5). Existing append-only UPDATE/DELETE triggers must be preserved
  or recreated verbatim if SQLite forces table reconstruction.
- `ActionResolutionService` added (`start_sequence`, `apply_adjustment`, `consume_roll`,
  `submit_decision`, `get_ready_bundle`) — never returns `OrchestrationResult`, never invokes the
  pipeline (Phase 2).
- `OrchestratorService.orchestrate_rpg_resume(...)` added (Phase 2).
- `orchestrate_turn`'s pending-roll intercept, `player_reported_total`, `consume_player_roll(...)`, and
  `chosen_die_range` are removed, along with their tests (Phase 2, per 15b-25).
- Product API routes for pending-interaction read, roll submission, adjustment, mechanical decision, and
  resume are added under CRD Issue 19 conventions; OpenAPI/TypeScript contracts regenerate (Phase 3).
- `known_unknowns.md`'s "Pending-roll rewind/cancel policy" entry is updated to note 15b's explicit
  non-resolution (this PR).

---

## Seams

| CRD Issue | Relationship |
|---|---|
| 2 / 2a | Character Sheet remains authoritative persistent mechanical state. |
| 3 | Reuse repository, migration, transaction, and partial-unique-index patterns. |
| 5a / 5b | Rules Package remains mechanical canon; ingestion is unchanged. |
| 8 | Context Builder remains stable-prefix owner; intermediate operations build no model context. Resume uses a code-owned continuation frame and the ready bundle. |
| 9 | Writer receives ordered existing `WriterAdjudicationView` records at the narration boundary. |
| 10 / 11 | Extractor and Contradiction run only for final narrative output. |
| 12c | Orchestrator remains sole pipeline owner; core ordering, Safety, dispositions, and delivery transaction remain authoritative. |
| 13 | Only provider-backed Turns participate in entitlement settlement. |
| 14a / 14b | Provider routing and Safety capability policy are reused unchanged. |
| 15 | ADR-015 authority boundaries remain; this ADR supersedes the narrow player-roll representation and consume path only — see the supersession table above. |
| 18 | Intermediate mechanical interactions are not retrieval-memory content. |
| 19 | Owns app construction, route conventions, current-node resolution, story lock, access-path helper, settlement wiring, error envelope, and generated contracts. |
| 19b | Downstream consumer of the completed public API contract; its implementation remains outside this issue. |

---

## Known Unknowns Touched

- **Pending-roll rewind/cancel policy** (open, surfaced during CRD Issue 15): explicitly preserved as
  deferred by 15b-33; not resolved here. See the accompanying `known_unknowns.md` edit.
- **Exact FastAPI route shapes** (open, CRD Issue 19): Phase 3 adds concrete RPG roll-lifecycle routes
  under existing Issue 19 conventions; this ADR does not resolve the broader route-shape unknown, only
  commits Phase 3 to following whatever conventions Issue 19 already established.

No other listed Known Unknown is touched or resolved by this document.
