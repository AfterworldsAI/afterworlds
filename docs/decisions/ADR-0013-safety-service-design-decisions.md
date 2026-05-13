# ADR-0013: Safety Service Design Decisions

**Issue:** CRD Issue 12b — Safety Service: Input Preflight and Conditional Output Audit
**Date:** 2026-05-13
**Status:** Accepted

---

## Context

CRD Issue 12b scopes the Safety pass to a single callable service (`SafetyService.check()`) and typed results. Orchestration (when to call INPUT vs OUTPUT, gating pipeline flow) belongs to Issue 12c. This document records design decisions made during implementation that are not fully specified by the issue spec.

---

## Decision 1: SafetyResult omits `latency_ms` and `model_identifier`

**Decision:** `SafetyResult` contains `report`, `target`, and `usage` only. It does not include `latency_ms` or `model_identifier`.

**Rationale:** The Issue 12b spec defines the SafetyResult fields. `latency_ms` and `model_identifier` are absent from the spec. Following CLAUDE.md scope discipline ("don't add features beyond what the task requires"), these fields were omitted. The `usage` field (TokenUsage) carries input/output/cache token counts, which are sufficient for billing and observability at this scope boundary.

If Issue 12c or a future issue requires latency tracking, it should be added as a separate change with an explicit spec.

---

## Decision 2: TokenUsage is a Safety-specific model, not a shared type

**Decision:** `TokenUsage` is defined in `pipeline/safety/models.py` rather than as a shared cross-pass type.

**Rationale:** The issue spec says "do not introduce shared provider-failure types." The spirit of this constraint is pass isolation — each pass owns its own data contracts. Defining a shared `TokenUsage` across Planner, Safety, and future passes would create coupling. When a future consolidation is warranted (e.g. Issue 14 provider routing), it can introduce a shared type explicitly.

---

## Decision 3: PassForwardLedger is not rendered into the Safety payload

**Decision:** The Safety pass does not call `built_context.pass_forward_ledger.render()` or append to the ledger.

**Rationale:** The spec states "No PassForwardLedger mutation." The corollary is that the Safety payload should not include ledger content. For INPUT target, the ledger is empty at Safety's call site (Safety runs before Planner). For OUTPUT target, the Writer's prose is explicitly placed in the volatile suffix with a `[WRITER OUTPUT FOR SAFETY EVALUATION]` label — rendering the ledger would duplicate that content with different framing. The spec's volatile suffix description is exhaustive and does not mention the ledger.

---

## Decision 4: SafetyPassError.cause vs Python `__cause__`

**Decision:** `SafetyPassError` carries an explicit `self.cause: Exception | None` attribute rather than relying on Python's implicit `__cause__` chaining via `raise ... from exc`.

**Rationale:** The spec requires `SafetyPassError` as the single public exception type. Code that catches `SafetyPassError` and needs to inspect the underlying provider or validation error must be able to do so without introspecting `__cause__`. The explicit `self.cause` attribute makes the contract visible in the type signature and accessible without relying on exception chaining conventions.

Note: the service still uses `raise ... from exc` in addition to setting `self.cause`, so both mechanisms are available to callers.

---

## Decision 5: Mode contract in system parameter (Planner pattern, not Contradiction pattern)

**Decision:** The active mode contract (`built_context.stable_prefix.system_prompt`) is placed as the second block in the Anthropic `system` parameter. It is NOT included in the user-message blocks.

**Rationale:** Two patterns exist in the codebase. The Contradiction pass places `system_prompt` as the first user block. The Planner pass places it as the second system block. For the Safety pass, the mode contract tells the evaluator what behavioural constraints are active for the current story mode — it is a configuration input to the evaluator, not narrative content. This aligns with the `system` parameter's intended role. Following the Planner pattern also means the mode contract is outside the user-message stable-prefix region, which avoids confusing it with story content.

---

## Decision 6: Verdict is a computed property, never model-supplied

**Decision:** `SafetyResult.verdict` is a `@computed_field` derived from `report.concerns`. The model is never asked to supply a verdict field.

**Rationale:** The spec requires this explicitly: "Computed verdict from concerns list — no model-supplied verdict field." This is an architectural safety property: a model that could supply `verdict=ALLOW` with non-empty concerns would create an exploitable ambiguity. Computing the verdict locally from the concerns list closes that gap.

---

## Architecture Notes

No drift from design principles. The Safety pass is implemented as a guardrail envelope per CRD v7 / Design doc v9. It does not participate in narrative generation, does not persist, does not mutate caller state, and fails closed on any error.
