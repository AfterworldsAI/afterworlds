# ADR-0014: Pipeline Orchestrator Design Decisions

**Issue:** CRD Issue 12c — Full Pipeline Orchestration
**Date:** 2026-05-16
**Status:** Accepted

---

## Context

CRD Issue 12c wires Issues 7–12b into one end-to-end Sojourn Turn. It also
resolves the two open Known Unknowns about provider-refusal handling in
the pipeline and provider-refusal reason opacity. This document records
the design decisions made during implementation that are not fully
specified by the issue spec or that resolve open architectural questions.

---

## Decision 1: One shared stable-prefix renderer in `pipeline/_stable_prefix_renderer.py`

**Decision:** A single pure utility (`render_stable_prefix_blocks`,
`collect_stable_prefix_texts`) lives in `pipeline/_stable_prefix_renderer.py`
and is consumed by every provider-backed pass — Planner, Writer,
Input/Output Safety, Extractor, Contradiction. Each pass's private helper
(`_collect_stable_texts`, `_collect_stable_prefix_texts`,
`_render_stable_prefix_blocks`) is removed.

**Rationale:** Issue 12c's "Stable-Prefix Rendering Consolidation" section
explicitly required factoring this logic into one shared callable. The
spec's canonical block list (Story Bible → Rolling Summary → Rules Package
slice → Retrieval Memory; breakpoint on the final emitted block) lives
authoritatively in one place so future drift is impossible by structure
rather than by convention. The utility is a pure callable with no Context
Builder calls, no session, and no orchestration decisions — pass-specific
system blocks, tools, ledger/volatile handling, evaluated-text framing,
and parsing remain pass-owned.

---

## Decision 2: Mode contract moves to `system` parameter for Extractor and Contradiction

**Decision:** The active mode contract (`stable_prefix.system_prompt`) is
no longer included as a user-message stable-prefix block in the Extractor
or Contradiction payloads. Both passes now place it as the second `system`
block, matching the Planner / Safety convention already in the codebase.

**Rationale:** The Issue 12c canonical stable block list explicitly omits
the mode contract; the shared renderer therefore omits it. Two passes
previously included it as a stable-prefix user block, which (a) made the
stable region differ across passes — breaking the cache-shared-region
invariant — and (b) duplicated `_collect_stable_texts` divergently. Moving
the mode contract into `system[1]` for both passes preserves the model's
visibility of the mode rules without diverging the cacheable region. This
matches the rationale recorded in ADR-0013 Decision 5 for the Safety pass.

The structural-identity integration test asserts byte-identical stable
regions across all six provider-backed passes, ensuring this consolidation
holds going forward.

---

## Decision 3: Conservative v1 `SafetyPolicy` defaults to empty whitelist

**Decision:** `SafetyPolicy()` constructed without arguments produces an
empty `whitelisted_providers` frozenset, so both Input Preflight and
Output Audit run on every Turn. `request_risk_signal=True` forces Input
Preflight even for whitelisted providers (whitelist is empty in v1 so the
predicate is trivially True regardless).

**Rationale:** Issue 12c "Safety Gating Policy" specifies the v1
whitelist is empty until Issue 14 defines provider capability profiles.
The conservative default matches the safety-first posture established in
Issue 12b's fail-closed behavior: the absence of a positive whitelist
decision must not silently skip the Safety call. `SafetyPolicy` is the
sole policy seam — provider/risk policy is never inlined elsewhere in the
orchestrator, so adding routing later (Issue 14) requires only swapping
the policy object.

---

## Decision 4: ProviderRefusalError as a shared exception type

**Decision:** `ProviderRefusalError` and `ProviderRefusal` live in
`pipeline/_refusal.py` and are caught by exception class at the
orchestrator. Pass services do not wrap a `ProviderRefusalError` raised by
their caller into their pass-specific `*PassError`; they re-raise it
unchanged from their `except` branches. v1 pass services do not
automatically synthesize `ProviderRefusalError` from coarse provider
exceptions — refusal-classification heuristics belong to Issue 14.

**Rationale:** Issue 12c's failure taxonomy explicitly distinguishes
narrative/state pass refusals (`ProviderRefusalError` →
`REFUSED_BY_PROVIDER`) from Safety failures (`SafetyPassError` →
`PIPELINE_ERROR`). A shared exception class lets the orchestrator route
by exception type without per-pass dispatch logic. The "do not wrap"
contract is enforced by each pass's `try / except ProviderRefusalError:
raise` block, so a future Issue 14 caller that raises refusals reaches
the orchestrator with full metadata intact. Tests construct refusals
explicitly because there is no v1 provider-side heuristic.

This resolves Known Unknown "Provider refusal handling in the pipeline":
the orchestration contract is now uniform across the four narrative-or-
state passes — `REFUSED_BY_PROVIDER` with no retries / fallback / routing
in v1; Issue 14 owns refusal-aware routing.

---

## Decision 5: `ProviderRefusal.coarse_reason` is advisory, never authoritative

**Decision:** The `coarse_reason` field on `ProviderRefusal` is optional
and explicitly documented as advisory. The orchestrator never routes on
it; the v1 disposition is `REFUSED_BY_PROVIDER` regardless of any reason
the provider surfaces.

**Rationale:** Issue 12c's Known Unknown "Provider refusal reason
opacity" requires that the orchestrator never treat provider refusal
metadata as authoritative policy signal. Capturing the reason for audit
is useful; routing on it would couple Afterworlds to per-provider
refusal-string conventions that providers may change without notice.
Issue 14 may use observed refusal patterns to inform routing heuristics
later, but routing must not depend on granular refusal reasons being
available.

---

## Decision 6: Outer transaction managed explicitly, commit decided by disposition; commit failure routed to PIPELINE_ERROR

**Decision:** The orchestrator opens the outer transaction with
`session.begin()` and centralizes the post-pipeline commit/rollback
policy in one helper, `_finalize_transaction`, used by both the
narrative and OOC wrappers. `session.commit()` is called if and only if
the inner pipeline returned `DELIVERED` (narrative) or `OOC_HANDLED`
(OOC); all other dispositions cause a best-effort `session.rollback()`.
Explicit `session.rollback()` calls inside `_narrative_persist` /
`_ooc_persist` are removed — the helper is the single source of
commit/rollback truth, guarded by `session.in_transaction()` so it stays
idempotent if a downstream call already rolled the transaction back.

If `session.commit()` itself raises (flush / constraint / IO / transient
deadlock / disk-full), the helper catches the exception, runs a
best-effort `session.rollback()` (wrapped in `suppress(Exception)` so a
broken rollback cannot escape past the typed result contract), and
returns a typed `PIPELINE_ERROR` `OrchestrationResult`. The cause text
is preserved in `pipeline_error_summary` (formatted as `"transaction
commit failed after <success_disposition>: <exc>"`). The already-
completed pass results (Planner, Writer, Extractor, Contradiction,
both Safety results) are preserved for observability, but
`delivered_output` and `turn_id` are explicitly dropped — the Turn
write and Extractor SAVEPOINT writes did not survive, so the
candidate's surviving-row claim is no longer true.

**Rationale:** The result-based commit decision is data-dependent: only
two of seven dispositions commit. Hiding this inside individual error
branches risks an unbalanced commit on some path that would survive
testing because it happens only for one rare combination of failures.
Centralizing it in one helper makes the spec invariant — "Only
`DELIVERED` and `OOC_HANDLED` leave a surviving Turn row; all other
dispositions leave the database byte-equal to its pre-orchestration
snapshot" — visible at the orchestration layer rather than scattered
through pass-specific failure handlers, AND ensures the narrative and
OOC paths cannot drift on commit-failure handling.

The commit-failure → `PIPELINE_ERROR` fallback satisfies Issue 12c's
exhaustive typed-terminal-state contract: a raw SQLAlchemy exception
escaping `orchestrate_turn` would bypass `PipelineDisposition` entirely
and crash request handling. This was a Codex P1 finding on PR #87
(round 2); regression coverage in
`TestCommitFailureRoutesToPipelineError` proves both narrative and
OOC paths, asserts the cause-text propagation, asserts rollback is
attempted, and asserts `delivered_output` / `turn_id` do not falsely
survive as if commit succeeded.

---

## Decision 7: Extractor SAVEPOINT via explicit session threading

**Decision:** `StoryBibleService.route_extractor_proposals(..., session=
caller_session)` opens `session.begin_nested()` on the caller's session
and threads the caller-supplied `Session` explicitly through every read,
write, and helper-method call in `_execute_routing_body`. The
service-internal helpers used during routing
(`update_dynamic_field`, `add_event`, `find_character_by_name`,
`_find_relationship_row`, `_update_relationship_field`) each gained a
backward-compatible optional `*, session: Session | None = None` keyword
parameter; each resolves the working session locally as `target = session
if session is not None else self._session` and uses `target` for all DB
I/O. The standalone path (`session=None`) preserves the historical
commit-at-end behavior using `self._session`; the orchestrator-driven
path lets the caller's outer transaction own the commit boundary.

`self._session` is NEVER overwritten during routing.

**Rationale:** The first round of this PR implemented the SAVEPOINT
extension with a temporary `self._session` swap inside
`route_extractor_proposals`. Codex review of PR #87 flagged that pattern
as a thread-safety race: a single `StoryBibleService` instance handles
concurrent turns under any normal multi-request deployment (and an
explicit future state once FastAPI is wired), and storing the
caller-supplied session on the instance lets one turn's session become
visible to another mid-routing, corrupting Story Bible writes across
transaction boundaries.

Threading the session explicitly through every helper eliminates the
shared mutable state. Concurrent calls into one service instance each
carry their own session through the routing body; `self._session`
remains the immutable per-instance default for the standalone path. A
multi-threaded stress regression
(`TestStoryBibleSessionThreading.test_concurrent_calls_do_not_corrupt_self_session`)
proves the property under contention; the SAVEPOINT rollback proof
(`TestContradictionBlockSAVEPOINTProof`) continues to pass against real
SQLite. ADR-0014 Decision 7 (original) is superseded by this revision.

---

## Decision 8: OOC short-circuit derives a context that only swaps the system prompt

**Decision:** The OOC short-circuit builds a derived `AssembledContext`
that swaps `stable_prefix.system_prompt` to the v1 OOC handler
instruction loaded from `docs/prompts/ooc_handler.md`. All other stable
prefix fields (Story Bible, rolling summary, rules slice, retrieval
memory) and the volatile suffix remain unchanged. The derived context
uses a fresh empty `PassForwardLedger`.

**Rationale:** The v1 OOC instruction is mode-agnostic and tells the
model to stay out of character and not advance story state. Zeroing the
Story Bible would be a behavior change unrelated to the OOC short-
circuit; the instruction itself is sufficient to keep the response out
of character. Issues 15–17 may revisit the derived context shape as part
of mode-specific OOC protocol authoring; the short-circuit shape itself
is stable.

OOC turns persist on `OOC_HANDLED` and are excluded from later narrative
recent-turn windows by the `exclude_ooc=True` default added to
`RecentTurnsProvider.get_recent_turns`. No schema migration is required
because the filter uses the existing `intent_classification` column.

---

## Decision 9: ThreadPoolExecutor lifecycle — bounded orchestrator-owned executor

**Decision (round 8, supersedes the original per-call design):** When the
constructor receives `executor=None`, the orchestrator owns one bounded
`ThreadPoolExecutor` created in `__init__` with
`max_workers=parallel_pass_max_workers` (default
`DEFAULT_PARALLEL_PASS_MAX_WORKERS = 4`, named
`"orchestrator-contradiction"`). It is reused across every `orchestrate_turn`
call and lives until `close()` (the service is also a context manager).
Per-turn `submit()` queues a fresh future; on timeout the orchestrator
calls `future.cancel()` (cancels queued-but-not-started work, cannot
interrupt a running provider call). When `executor` is injected the
caller owns its lifecycle and the orchestrator never calls `shutdown`
on it (`close()` is a no-op for an injected executor).

**Rationale (round 8):** The prior per-call local executor +
`shutdown(wait=False, cancel_futures=True)` design bounded request wall
time correctly but did not cap worker accumulation — every timed-out
turn could leave a fresh contradiction worker running until natural
completion, accumulating without bound under repeated provider timeouts.
A single long-lived orchestrator-owned executor with
`max_workers=N` caps total live contradiction worker threads at N
regardless of how many turns time out. The wall-time bound is preserved
because the per-turn timeout fires on the new turn's own future, not on
a hung worker, and queued-but-not-started futures are cancelled on
timeout so a queue full of stuck workers does not block subsequent
turns indefinitely.

Contradiction performs no DB I/O, so a hung worker is side-effect-free
for canon and only consumes one queue slot until natural completion.
Provider-level cooperative cancellation (the only way to interrupt a
running provider call) is deferred to Issue 14 provider-adapter work.

**Why a long-lived owned executor and not just process-pooled workers
per FastAPI request?** The orchestrator is the seam between the request
boundary and the model-call boundary. Pushing executor lifecycle to the
process owner would still require either bounded resource ownership in
the orchestrator (this decision) or trust that callers always inject;
the orchestrator-owned bound is the safe default. Callers that want
their own pool can still inject one and the orchestrator will use it
without modification.

---

## Decision 10: `pass_latency_breakdown` is latency-only

**Decision:** `OrchestrationResult.pass_latency_breakdown` carries
millisecond integers per canonical pass key (`intent`, `context`,
`input_safety`, `planner`, `writer`, `output_safety`, `extractor`,
`contradiction`). Skipped passes are omitted. Token metrics remain
embedded inside each pass's native typed result; the orchestrator does
not flatten or aggregate them.

**Rationale:** Issue 12c invariant #13 forbids flattening token metrics
into the orchestrator-owned latency breakdown. Keeping the two concerns
separate means Issue 13 (entitlement routing) can consume token metrics
through whichever pass result is relevant without depending on the
orchestrator's structural choices. The latency map is the only
orchestrator-owned scalar; everything else is observable through the
embedded pass results.

---

## Decision 11: `OrchestrationResult` invariants enforced by Pydantic model_validator

**Decision:** The disposition-population invariant table from Issue 12c
is enforced at construction time via a Pydantic `model_validator(mode=
"after")` on `OrchestrationResult`. Any violation raises
`OrchestratorError` with a message identifying which required/forbidden
predicate failed. The orchestrator never silently coerces a refused or
blocked turn into `DELIVERED` / `OOC_HANDLED` by manipulating field
absence.

**Rationale:** Issue 12c invariant #7 ("`PipelineDisposition` is
exhaustive; new terminal states require explicit new disposition values,
invariants, and tests") is enforced by structure. The validator covers
all seven dispositions including the OOC-vs-narrative split for
`BLOCKED_OUTPUT_SAFETY` (narrative requires `planner_result`; OOC
forbids it).

For the pre-classification PIPELINE_ERROR path (Intent Classification
fails before we know the intent), the orchestrator synthesizes a
sentinel `IntentClassificationResult` so the required-field invariant
remains satisfied. The synthesized intent uses zero confidence and the
neutral `AUTHOR_INSTRUCTION` type — the caller learns the classification
was synthesized from the `PIPELINE_ERROR` disposition and the
`pipeline_error_summary`.

---

## Consequences

- One renderer-ownership gap closed; future pass services consume the
  shared utility by construction.
- Provider-refusal handling resolved for v1; Issue 14 layers
  refusal-aware routing on top without reopening the orchestrator
  contract.
- The Issue 12c open items recorded in `known_unknowns.md` are:
  (a) mode-contract OOC protocol authoring — Issues 15–17;
  (b) safety-policy whitelist resolution — Issue 14.
- The previously-open items "Provider refusal handling in the pipeline"
  and "Provider refusal reason opacity" are now resolved with this ADR.
