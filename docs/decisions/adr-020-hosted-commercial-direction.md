# ADR-020 — Hosted Commercial Direction and Billing/BYOK Visibility Boundary

**Date:** 2026-10-15
**Issue:** CRD Issue 20 / GitHub #199 — Billing/BYOK Visibility and Configuration
**Status:** Accepted (Owner decisions recorded in the accepted CRD Issue 20 body)

## Context

Design §8, CRD Item 8 and the Known Unknowns described an optional paid
**Starter Access** entry package alongside the hosted subscription. CRD Issue
20 builds the user-facing billing/BYOK surface and needed the commercial
direction it may present. The Owner confirmed that direction while accepting
CRD Issue 20. This ADR records it and the boundaries it sets; it activates
nothing.

## Owner Decisions

1. Hosted access will offer a **15-day free trial and one paid subscription**.
2. Trial and paid access provide the same features and normal performance.
   There are no feature or performance upgrade tiers.
3. Heavy users may purchase additional usage. Pass-through billing versus
   credit packs remains undecided.
4. BYOK remains separate. Perpetual BYOK rights and renewable Cloud Services
   remain distinct.
5. Trial/subscription allowances, prices, credit-conversion parameters and
   numeric burn estimates await representative consumption measurements across
   RPG, Branching and Writing. *(Narrowed by ADR-017b, 2026-10-16: the v1
   release modes are RPG and Branching; Writing is deferred and does not block
   v1 measurement.)*

The free-trial direction **replaces the optional paid Starter Access offer**
as commercial direction.

## Consequences

- **Ownership.** Trial lifecycle, commercial eligibility, payment, checkout,
  purchase/redemption, webhooks and commercial entitlement migrations belong to
  CRD Issue 23, which mutates runtime entitlements only through CRD Issue 13's
  approved event path. CRD Issue 13 keeps entitlement state, accounting,
  enforcement and settlement.
- **Existing data is not reinterpreted.** `HostedAccessPlan.STARTER_ACCESS`
  and any recorded Starter Access state keep their current meaning (a paid
  hosted plan using the full pipeline and normal hosted credits). Nothing
  relabels it as a free trial, and no trial is activated by this decision or
  by CRD Issue 20. Any migration of that state belongs to CRD Issue 23.
- **Numeric burn estimates are deferred.** CRD Issue 20 communicates that
  usage estimates are unavailable pending calibration; that message does not
  fulfil the roadmap's numeric-estimate deliverable. Before an estimator,
  prices or allowances are accepted, separately owned measurement must
  distinguish provider costs (including unsuccessful attempts) from customer
  credit deductions. No average burn, dollar equivalents, remaining-turn
  forecasts or priced allowances may be derived from the provisional
  `TurnCostPolicyConfig` defaults.
- **CRD Issue 20 boundary.** The surface displays authoritative balances,
  hosted availability, Cloud Services and BYOK state, and configures BYOK
  through the credential owner. It adds no entitlement enforcement, access-path
  preference, hosted-provider configuration or provider/fallback/Safety
  policy. Purchasing and trial enrollment are shown as unavailable pending
  CRD Issue 23.

## Supersession

This ADR supersedes the "optional Starter Access" commercial-direction
passages in Design §8, CRD Item 8 / Issue 13 scope and the Known Unknowns
(Business model, Starter Access rows and the Starter Access package parameters
entry), which are annotated accordingly. ADR-0001's rejection of a crippled
free tier stands: the trial is full-feature, not a degraded tier.
