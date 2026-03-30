# ADR-0001: Pricing model shift from freemium to metered hosted subscription plus BYOK

- **Status:** Accepted
- **Date:** 2026-03-29
- **Owners:** Project owner (Brian) / Afterworlds
- **Related docs:**
  - `docs/architecture/design.md` (Afterworlds Design v7)
  - `docs/architecture/construction_readiness.md` (CRD v5)

---

## Context

Afterworlds was originally modeled with a freemium structure:

- a **free tier** with a reduced pipeline
- a **paid tier** with the full five-pass Sojourn pipeline
- a **BYOK** path positioned as a one-time purchase covering infrastructure only

This design initially appeared attractive because it followed a familiar SaaS pattern: low-friction user acquisition through free access, with deeper functionality reserved for paying users.

During architecture review, a critical flaw was identified in the degraded free-tier design. The reduced free pipeline omitted the **Extractor** pass. Without the Extractor, the system had no reliable mechanism to:

- propose Story Bible updates
- apply or stage world-state changes
- keep dynamic canon current across turns
- maintain continuity quality at the level the product promises

This exposed a deeper issue than a single missing pass.

Afterworlds is not primarily selling generic AI text generation. It is selling **persistent, coherent, stateful narrative experience**: continuity, canon maintenance, memory integrity, and believable progression across turns and sessions. A free experience that removed core continuity machinery would not function as a true demonstration of the product. It would train users to believe the product was unreliable.

In short:

- a degraded free tier would weaken the product's core promise
- separate pipeline-quality tiers would increase implementation and testing complexity
- the old BYOK framing understated real ongoing platform costs for storage, sync, ingestion, and future marketplace/service layers

A business-model correction was therefore required.

---

## Decision

Afterworlds will no longer use a degraded freemium architecture.

The product will adopt the following commercial structure:

### 1. One canonical narrative engine

All paying access paths use the same full five-pass Sojourn pipeline:

**Planner -> Writer -> Extractor -> Contradiction -> Safety**

No commercial tier may remove core continuity functions in order to create an upgrade incentive.

### 2. Hosted subscription with credits

Hosted access is sold as a **metered subscription with included monthly credits**, rather than as a fake-unlimited subscription or a degraded free tier.

The hosted model includes:

- monthly subscription fee
- included credits
- transparent top-ups
- optional limited rollover, if later adopted
- explicit usage visibility in the UI

When credits are exhausted, the system must stop cleanly or prompt for top-up. It must not silently degrade output quality or remove pipeline passes.

### 3. BYOK remains first-class

BYOK remains a core product path, not a fallback or reduced mode.

BYOK users receive the same pipeline and continuity quality as hosted users, but supply their own provider/model credentials.

### 4. BYOK is split into license and services

The prior phrase "one-time purchase" is no longer sufficient on its own, because BYOK users still consume ongoing platform resources through Afterworlds.

BYOK is therefore split into two commercial components:

#### Perpetual BYOK License

A one-time purchase that grants:

- permanent product rights to use Afterworlds with the user's own keys
- full core feature parity with hosted users
- first year of Cloud Services included

#### Cloud Services Renewal

An optional annual renewal after the first included year, covering ongoing hosted-service costs such as:

- cloud storage
- sync / backup / remote access
- pack ingestion processing
- future marketplace participation infrastructure
- similar recurring platform services

This preserves honesty in pricing language: the software/product right is perpetual; the hosted service layer is renewable.

### 5. Graceful non-renewal for BYOK Cloud Services

If a BYOK user does not renew Cloud Services:

- read/export/download access to owned work should remain available where practical
- only genuine recurring-cost services should be suspended or reduced
- user-created work must not be held hostage as leverage for renewal
- reactivation later should remain straightforward

---

## Alternatives considered

### A. Keep the original freemium model

**Rejected.**

Reason:

- the degraded free tier undermined continuity
- it no longer represented the real product
- it created architectural and testing complexity
- it risked poor first impressions and weak conversion

### B. Replace freemium with a full-feature trial model

**Considered seriously, but not chosen as the primary architecture.**

Reason:

- a trial is ethically cleaner than a crippled free tier
- however, it still centers the business model around temporary access rather than ongoing value alignment
- for an AI-native product with real ongoing inference costs, metered subscription with credits is a more sustainable default

Starter or trial-like paid entry may still be used later as an onboarding tactic, but not as the defining pricing model.

### C. Pure perpetual BYOK with no ongoing service fee ever

**Rejected as the default long-term model.**

Reason:

- it understates continuing platform costs
- it becomes less honest as storage, ingestion, sync, and marketplace features expand
- it risks creating a permanent-service obligation funded by a one-time payment

### D. Hosted unlimited flat-fee subscription

**Rejected.**

Reason:

- hides usage reality
- creates subsidy problems from heavy users
- pressures the product toward hidden throttles, quality degradation, or pricing increases
- conflicts with the goal of transparent, ethical pricing

---

## Rationale

This decision was made for three primary reasons.

### 1. Product integrity

Continuity is the core deliverable.

If the product degrades continuity quality by tier, it is not withholding a premium enhancement; it is withholding the product itself.

### 2. Architectural simplicity

One canonical narrative engine is simpler to:

- build
- test
- reason about
- document
- review

A single real engine is better than multiple quality classes pretending to be one product.

### 3. Ethical and economic clarity

Afterworlds should charge users in a way that maps to real cost and real value.

- hosted users pay for hosted usage
- BYOK users pay their own model costs and contribute to the ongoing platform services they continue to use
- no one is lured in through a deliberately broken or misleading experience

This better matches the project's explicit anti-gatekeeping and anti-dark-pattern stance.

---

## Consequences

### Positive consequences

- continuity quality becomes invariant across access paths
- pricing becomes more honest and more legible
- tier routing becomes entitlement logic, not pipeline mutilation
- BYOK remains strong without pretending hosted services are free forever
- the model scales more cleanly into future marketplace and institutional offerings

### Negative / tradeoff consequences

- there is no frictionless free tier for acquisition
- hosted subscription pricing must be tuned carefully around credits and top-ups
- BYOK pricing language becomes slightly more complex because license rights and cloud services are separated
- product and UI work must clearly explain the difference between perpetual rights and renewable services

### Implementation consequences

The following documentation and system assumptions must align with this decision:

- Design doc business-model section
- CRD cost-model and business-model-sensitive constraints
- tier-routing logic
- contradiction-checker assumptions tied to old free/paid pipeline splits
- UI copy for hosted credits, top-ups, BYOK license, and Cloud Services renewal
- entitlement tests covering hosted and BYOK paths

---

## Naming / language rules

The repo and product should use the following language consistently:

- **Hosted Subscription** = metered subscription with included credits
- **Top-Ups** = additional hosted credits purchased explicitly
- **Perpetual BYOK License** = one-time product/license purchase
- **Cloud Services** = recurring hosted-service layer
- **Cloud Services Renewal** = optional annual renewal after the first included year

Avoid these misleading patterns:

- calling BYOK a pure "one-time purchase" without mentioning renewable services
- describing hosted access as "unlimited" if actual usage is credit-bounded
- using vague terms like "maintenance fee" when the real issue is hosted-service cost

---

## Follow-up actions

1. Keep Design v7 and CRD v5 aligned with this ADR
2. Implement entitlement-aware tier routing around:
   - hosted credit balance
   - top-up flow
   - BYOK license status
   - Cloud Services active vs lapsed state
3. Add tests for full-pipeline parity across hosted and BYOK paths
4. Define initial hosted credit packs and top-up pricing before public launch pricing is finalized
5. Define initial BYOK license price and annual Cloud Services renewal price before public pricing lock
6. Ensure future marketplace and institutional features layer onto this model rather than replacing it

---

## Supersedes

This ADR supersedes the earlier implicit freemium assumption in which:

- free users received a degraded pipeline
- paid users received the real product
- BYOK was described too simply as a one-time purchase covering infrastructure

Those assumptions should be treated as obsolete wherever they still appear in old drafts, discussion, or implementation notes.
