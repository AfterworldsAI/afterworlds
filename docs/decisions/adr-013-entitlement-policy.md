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
