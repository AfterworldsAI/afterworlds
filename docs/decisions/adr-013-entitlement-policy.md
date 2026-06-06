# ADR-013 — Entitlement Policy Owner Decisions

**Date:** 2026-06-05
**Issue:** CRD Issue 13 / GitHub #93 — Runtime Entitlement State and Enforcement
**Status:** Accepted

## Context

Issue 13 implements the authoritative runtime entitlement service. Five owner decisions govern
credit deduction, pool consumption, balance overrun, BYOK independence, and Cloud Services
expiration semantics. These decisions are recorded here verbatim from the Issue 13 spec before
implementation begins.

## Owner Decisions

1. Hosted credit deduction occurs only for `DELIVERED` and `OOC_HANDLED` turns. Safety blocks,
   contradiction blocks, provider refusals, and pipeline errors do not deduct credits.

2. Hosted included credits are consumed before top-up credits.

3. If a hosted turn begins with positive total credits but actual delivered/OOC cost exceeds the
   remaining balance, v1 permits the balance to go negative. Further hosted turns are blocked until
   credits are replenished.

4. BYOK turns never deduct hosted credits. `byok_turn_available = byok_license_active`, independent
   of Cloud Services status.

5. Cloud Services effective access requires `cloud_services_active=True`, non-`None`
   `cloud_services_expires_at`, and `cloud_services_expires_at > now`.

## Architecture Notes — `MANUAL_CREDIT_ADJUSTMENT` and the Issue 13 / Issue 22 Boundary

**Issue 13 owns the event-sourced entitlement mutation primitive.**
`receive_entitlement_event` is the only approved path for mutating `RuntimeEntitlementState`.
All mutations — including support-initiated credit adjustments — must go through this
append-only path. Without `MANUAL_CREDIT_ADJUSTMENT`, Issue 22 would have no legal way to
adjust credit balances; removing it from Issue 13 would leave Issue 22 with no callable
mutation primitive.

**`MANUAL_CREDIT_ADJUSTMENT` exists solely so Issue 22 support/remediation code can mutate
runtime entitlement state through the approved append-only path.** It is a seam primitive,
not a support-workflow implementation. Issue 13 intentionally defines and enforces it here
because the Issue 13 spec explicitly defines the boundary: Issue 22 appends via
`receive_entitlement_event`; it does not get a back-door write path.

**`reason` and `adjusted_by` are minimal provenance fields, not support-workflow fields.**
A credit mutation with no record of who authorized it or why would be unauditable and
unrecoverable. These two fields are the minimum required to keep any money/access mutation
reconstructable from the append-only event log — the same bar applied to every other event
type's traceability fields (`external_source`, `external_reference_id`, etc.).

**Issue 22 owns:** the support/remediation workflow, support-facing entitlement history,
reason taxonomy expansion, admin surfaces, anomaly visibility, and all human operational
tooling. None of those surfaces are implemented in this PR.
