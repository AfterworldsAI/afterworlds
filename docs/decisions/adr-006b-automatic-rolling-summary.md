# ADR-006b: Automatic Rolling Summary in Production — Eligibility, Atomic Compression, Provider Pass

**Issue:** CRD Issue 21 Integration Prerequisite B ([contracts](../architecture/crd-issue-21-integration-prerequisites.md#prerequisite-b--automatic-rolling-summary-in-production))
**Date:** 2026-10-16
**Status:** Accepted (Owner acceptance of the prerequisite contracts, 2026-10-16)
**Extends:** CRD Issue 6 (`RollingSummaryService`, GitHub #63), [ADR-0009](ADR-0009-rolling-summary-n-value.md), [ADR-0010](ADR-0010-context-builder-design-decisions.md) Decision 2, [ADR-0014](ADR-0014-pipeline-orchestrator-design-decisions.md), [ADR-014a](adr-014a-provider-routing-core.md).

---

## Context

`RollingSummaryService` (CRD Issue 6) owns append-safe summary persistence and Context Builder
reads its current row into the stable prefix. No production caller ever compressed: the only
product construction was the per-turn context reader with a generator returning `""`. The
Owner decided on 2026-10-16 that a due summary commits atomically with the narrative turn, and
that only delivered ordinary Branching/RPG narrative turns count toward provisional N = 10.

## Decision 1: Eligibility is a durable per-Turn fact

Every Branching or RPG Turn written by the narrative persistence path records
`rolling_summary_eligible` in its existing `Turn.mode_metadata` JSON carrier
(`BranchingNodeMetadata` / `RpgNodeMetadata`; a narrow optional typed field, no migration).
It is decided by code at delivery time, inside the turn's transaction:

| Turn | Eligible |
|---|---|
| Branching in-play narrative turn | yes |
| Branching Begin story opening ([ADR-016b](adr-016b-branching-story-start.md)) | yes |
| Branching setup-confirmation turn (`play_status = setup`) | no |
| RPG in-play turn with no new action-resolution sequence | yes |
| RPG turn announcing a pending roll/decision (sequence start) | no |
| RPG resume narration of a ready sequence | yes (once) |
| RPG setup turn | no |
| OOC turn (any mode) | no (no record; absence means ineligible) |
| Blocked, refused, rejected or errored attempt | no Turn survives |

The fact is never inferred later from session status, prose, Node snapshots or the Retrieval
Memory eligibility policy. Historical or shared data is not reclassified; Turns without the
field are ineligible. Writing-specific eligibility remains deferred (ADR-017b).

## Decision 2: Threshold, window and source material

The count is the story's eligible Turns in persisted chronological order (`timestamp`, then
`turn_id`), including the current provisional Turn inside its transaction. Compression is due
when `should_compress(count, ROLLING_SUMMARY_N)` holds (N = 10, provisional; ADR-0009/0010
unchanged).

The window is every eligible Turn after the current summary's `compressed_through_turn_id`, up to
and including the current Turn. `compressed_from_turn_id`/`compressed_through_turn_id` anchor its
first and last eligible Turns; ineligible Turns between them are skipped and are not claimed as
summarized. Each window entry supplies the delivered Sojourner input and the delivered
player-visible narration only (the Begin marker input is omitted). Hidden RPG adjudication,
roll state, setup-only/OOC material and failed candidates are never source material.

## Decision 3: A lightweight provider pass on the selected binding

`PipelinePassId.ROLLING_SUMMARY` / `PassIdentifier.ROLLING_SUMMARY` is a provider-backed pass
using the owning adapter's configurable lightweight (Haiku-tier) model on the turn's already
selected hosted or BYOK binding, through the same `ScopedProviderAdapter` and refusal-fallback
router as the other passes. No independent resolver, hardcoded model, cross-path fallback or
hidden free call.

The request reuses the turn's immutable stable prefix through `render_stable_prefix_blocks`
(no replacement prefix is assembled) followed by a volatile block holding the prior summary and
the window, and the minimal generic contract in
[`docs/prompts/rolling_summary.md`](../prompts/rolling_summary.md). It does not render the
pass-forward ledger, so hidden RPG adjudication views never reach it. Output arrives through a
forced tool; blank or malformed output fails closed. The summary preserves continuity, invents
nothing and ratifies no Story Bible canon.

## Decision 4: Placement and atomicity

A due compression runs inside `_narrative_persist`, after Output Safety and the Contradiction
gate pass and before the outer transaction commits, on the orchestrator's own session. The Turn,
its canon, its eligibility fact and the new current summary commit together. The stable prefix
of the current turn is unchanged; later turns read the new summary. Context Builder stays a
reader: its `RollingSummaryService` generator raises if ever called.

## Decision 5: Failure, usage and settlement

- Exhausted provider refusal → `REFUSED_BY_PROVIDER`; blank/malformed output, operational
  failure or persistence failure → `PIPELINE_ERROR`. Both roll back the Turn, canon and summary
  change, deliver nothing, skip Retrieval Memory ingestion and leave the count unchanged.
- `OrchestrationResult.rolling_summary_result` carries the pass usage. A successful hosted turn
  includes it in the existing `settle_hosted_turn_cost` snapshot list; BYOK never deducts.
  Usage from a failed compression is retained on the non-delivered result for audit and is not
  charged. Post-commit settlement-warning behavior is unchanged.
- A user retry re-runs an uncommitted turn and window; there is no background recovery.
  Coverage idempotency and the single current row stay with `RollingSummaryService` and its
  savepoint constraints. GitHub #65's accepted tolerance of duplicate concurrent generator work
  is retained; no single-flight reservation, lock service or migration is added.

## Not decided here

Empirical finalization of N, summary quality calibration, summary UI, token-budget redesign,
mode-prompt retuning and Writing eligibility.
