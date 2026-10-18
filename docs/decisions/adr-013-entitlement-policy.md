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

> **CRD Issue 22 lifecycle amendment (Owner-accepted 2026-10-17).** Authority:
> [CRD Issue 22 #206](https://github.com/AfterworldsAI/afterworlds/issues/206), the
> [accepted lifecycle ADR amendment contract, revision 1](https://github.com/AfterworldsAI/afterworlds/issues/206#issuecomment-6246562569)
> and the [field/store retention matrix, revision 1](https://github.com/AfterworldsAI/afterworlds/issues/206#issuecomment-6246563742)
> (including its exact accounting and perpetual-rights allowlist); repository copies in
> `docs/architecture/crd-issue-22-governing/`.
>
> **Superseded portion:** none of the ordinary mutation rule above. The amendment adds the retained
> lifetime and governed-expiry boundary.
>
> **Inserted clause:** “CRD Issue 22 support actions still call only this mutation path. During
> active life plus 24 calendar months after account closure, minimized retained events must parse and
> replay at exact `global_sequence` order with stable `event_id`, subject, source/idempotency/turn
> references when material, and all typed fields necessary to reconstruct credit/access effects. The
> retained event representation is versioned and owned by entitlement service; it is not arbitrary
> JSON redaction or a second ledger. Expiry after the approved lifetime uses a governed path, subject
> to an individually justified financial-record duty. Minimum BYOK-rights evidence survives
> independently while enforceable, reviewed annually. Story deletion alone does not start
> account-closure expiry.”
>
> **Preserved:** existing credit precision, negative balances, BYOK independence, Cloud expiry and
> event mutation semantics.
>
> **Remote prerequisite #205 note:** in a remote deployment the entitlement subject
> (`sojourner_id`) of a hosted account is that account's stable `account_id`
> ([ADR-021](adr-021-remote-identity-and-storage.md)). No new event type, parallel ledger or
> mutation path is introduced; local installations keep the single local Sojourner subject.
>
> **Common amendment clause (verbatim):** Ordinary operation retains this ADR's append-only, immutable, transactional, replay and provenance requirements. A verified, explicitly confirmed Story or account-wide terminal deletion, or an approved record's retention expiry, is a separately authorized lifecycle operation. It may remove only inventoried in-scope content or expired minimized records through the owning service and a reviewed migration/maintenance contract. The operation records trusted actor, subject/scope, confirmation and source revision, policy version, exact affected classes/counts, per-store progress, timestamps and verification in minimized append-safe receipts. It fences new work, preserves unrelated subjects, shared Rules Packages, current money/access reconstructability and perpetual BYOK rights, and prevents restore, replay, delayed jobs and reindex from resurrecting erased data. Existing database UPDATE/DELETE triggers are not simply disabled by an ad hoc administrator action; the reviewed lifecycle path must preserve ordinary immutability and have tests for its exceptional behavior. An operational receipt is not a retained copy of narrative, provider, RPG or credential payload. This exception neither resolves gameplay cancellation/expiration/rewind nor creates a refund, credit repair, payment event or new entitlement path. Backups and legal exceptions follow the accepted CRD Issue 22 matrix; final deletion cannot be claimed before verified backup disposition.
>
> A service that cannot meet the approved 7-day live or overall 30-day backup deletion limit is an
> unmet prerequisite, not grounds for an implicit extension.

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
