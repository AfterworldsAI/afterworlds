# ADR-014b: OpenRouter Model-Route Capability Registry and Safety Whitelist

**Issue:** CRD Issue 14b — OpenRouter Whitelist Registry
**Date:** 2026-06-18
**Status:** Accepted

---

## Context

CRD Issue 14a shipped the `CapabilityProfileAwareSafetyPolicy` with a single
`trusted_for_safety_skip` bool on `EligibleWriterRoute`.  All OpenRouter routes
were `trusted_for_safety_skip=False` (Safety always runs).  Issue 14b upgrades
the route type to `EligibleModelRoute` and adds:

- An exact-model-route Safety whitelist (`WhitelistConfig` / `WhitelistEntry`).
- A capability registry backed by the OpenRouter `/models` catalog
  (`OpenRouterCapabilityRegistry`).
- The `SafetyWhitelistStatus` five-value enum and
  `ModelRouteCapabilityProfile` capability fact type.
- Two catalog providers: `FixtureOpenRouterCatalogProvider` (CI default, no
  network) and `LiveOpenRouterCatalogProvider` (stdlib `urllib.request`, opt-in
  for live integration tests).

---

## Decision 1: `EligibleWriterRoute` fully replaced by `EligibleModelRoute`

**Decision:** The 14a type `EligibleWriterRoute` is removed (no compat alias).
`EligibleModelRoute` carries `whitelist_status: SafetyWhitelistStatus` and
`supports_required_capabilities: bool` instead of the 14a
`trusted_for_safety_skip: bool`.

**Rationale:** The 14a boolean was a placeholder.  Providing a compat alias
would leave the old semantics reachable after 14b ships, making the upgrade
auditable only at the compat boundary.  A clean full replacement is consistent
with the single-PR scope of 14b and the project's zero-tolerance for
silent-degradation paths.

---

## Decision 2: Safety-skip requires WHITELISTED AND capable on every route

**Decision:** `CapabilityProfileAwareSafetyPolicy._can_skip` is True only when
every eligible Writer route satisfies `whitelist_status is WHITELISTED AND
supports_required_capabilities`.

**Rationale:** Both axes must be positive to skip Safety.  A model may be
capable (confirmed by catalog) but not whitelisted — in that case the operator
has not explicitly approved it for Safety skip and Safety must run.  A model may
be whitelisted but the catalog entry confirms it is not capable (e.g., short
context window) — Safety must also run.  `DISABLED` status (whitelist
administratively off) is not `WHITELISTED`; capable + DISABLED still requires
Safety, since the whitelist gate is the operational approval mechanism.

---

## Decision 3: Fail-safe rule — reject only on positive evidence of incapability

**Decision:** The registry (`resolve_route`) raises `ProviderConfigError` only
when the catalog affirmatively reports a capability deficiency:

- `supports_text_output is False` (explicit `False`, not `None`) — Writer pass.
- `supports_tool_use is False AND supports_structured_output is False` (both
  explicit `False`, not `None`) — structured passes (Planner, Extractor).
- `context_length is not None AND context_length < writer_context_length_floor`
  — known inadequate context for Writer.

A catalog miss, `None` capability flags, or `context_length=None` all collapse
to `supports_required_capabilities=False` without rejecting the route — Safety
runs, the route is live.

**Rationale:** Over-rejecting a route on absent evidence is worse than running
Safety on it.  A model the catalog does not know about might be valid; a model
with no reported capability flags might still work.  Rejection is reserved for
positive evidence of incapability, not absence of positive evidence of
capability.  The context-length floor is an exception: a known below-floor
window is positive evidence the Writer pass will fail at call time.

---

## Decision 4: Context-length floor rejects; floor value is operator-configured

**Decision:** `resolve_route` raises `ProviderConfigError` when
`entry.context_length is not None AND entry.context_length <
writer_context_length_floor`.  The floor is a constructor parameter on
`OpenRouterCapabilityRegistry` (default `_WRITER_CONTEXT_LENGTH_FLOOR = 8192`).
`context_length=None` does not reject — it collapses to
`supports_required_capabilities=False` (Safety runs, route live).

**Rationale:** A known below-floor context length is positive evidence of
incapability for the Writer pass (14b spec, Design section).  The floor value
is an operator configuration decision, not a hardcoded constant — operators can
lower or raise it at construction.  The default of 8192 is provisional;
production deployments should configure an appropriate floor.

**Known Unknown carried forward:** The correct production floor value and
whether multiple per-pass floors are needed remain owner decisions.  See
`known_unknowns.md`.

---

## Decision 5: STALE vs. UNKNOWN semantics and time-based staleness

**Decision:**
- `UNKNOWN` — model id is not in the whitelist and not in the catalog.
  Safety always runs.  Route not rejected.
- `STALE` — model id IS in the whitelist but:
  - not found in the catalog (delisted/renamed), OR
  - found in the catalog but `WhitelistEntry.verified_at` is older than
    `max_evidence_age` (whitelist evidence expired).
  Safety always runs.  Route not rejected.

`max_evidence_age` is a constructor parameter on `OpenRouterCapabilityRegistry`
(`timedelta | None`; `None` means entries never expire by age).

**Rationale:** The distinction matters for operational observability.  `STALE`
signals a whitelist entry that may need review.  `UNKNOWN` signals a model the
system has never assessed.  Both force Safety; neither rejects the route,
consistent with the fail-safe rule.  Time-based staleness allows operators to
require periodic re-verification of whitelist entries.

---

## Decision 6: Static deny-set retained as pre-catalog fast-path

**Decision:** `_is_dynamic_alias` from `adapters/_openrouter.py` is imported
by the registry and applied at step 1, before the catalog fetch.  Catalog
entries with `is_dynamic_router=True` are additionally rejected at step 4 as
defense-in-depth.

**Rationale:** The static deny-set is O(1) and does not require a network
fetch.  It catches known dynamic aliases (e.g. `openrouter/auto`,
`openrouter/free`) before any catalog I/O.  The catalog-driven check is
defense-in-depth for aliases that appear in the API but were not in the static
set at code time.

---

## Decision 7: Anthropic-direct routes always WHITELISTED + capable

**Decision:** `ProviderResolver` builds Anthropic-direct routes with
`whitelist_status=WHITELISTED`, `supports_required_capabilities=True`, and an
`AFTERWORLDS_VERIFIED` `ModelRouteCapabilityProfile`.  This is computed by
`make_anthropic_capability_profile()` in `_registry.py` and applied in the
resolver — not by the `OpenRouterCapabilityRegistry`.

**Rationale:** Anthropic-direct routes are trusted by Afterworlds design
(CRD AC 15/18 regression from 14a).  They do not go through the OpenRouter
catalog.  Encoding this as a named function ensures the 14a guarantee is
preserved when the resolver is refactored.

---

## Decision 8: No registry → fail-safe (14a parity preserved)

**Decision:** When `capability_registry=None` is passed to `ProviderResolver`,
OpenRouter routes are constructed with `whitelist_status=UNKNOWN` and
`supports_required_capabilities=False`.  This is identical to the 14a behavior
(Safety always runs for OpenRouter).

**Rationale:** The registry is injected; absence must not introduce a silent
behavioral change.  UNKNOWN/False is the strictly more conservative fallback.

---

## Decision 9: Incapable fallback fails the whole turn

**Decision:** When the registry is configured and an OpenRouter fallback model
raises `ProviderConfigError` (positive incapability), the exception propagates
through `_resolve_openrouter_route` and the entire `resolve_for_turn` call
fails.  The primary Anthropic pass does not proceed.

**Rationale:** Consistent with 14a fail-closed behavior for blank-model routes.
The condition fires only on positive incapability evidence, not a catalog miss.
This is worth documenting because it can surprise: a healthy Anthropic primary
is lost if the configured OpenRouter fallback is positively incapable.
The correct fix is to update the fallback model identifier, not to suppress
route validation for fallbacks.

---

## Decision 10: 14b ships the registry machinery, not the catalog classification

**Decision:** 14b does not classify specific OpenRouter models as whitelisted
or not-whitelisted.  The `FixtureOpenRouterCatalogProvider` defaults to an empty
catalog (all misses; Safety always runs for OpenRouter routes).  Populating the
whitelist and catalog in production is an operator concern beyond 14b scope.

**Rationale:** Classifying individual models requires ongoing maintenance and
owner decisions.  14b delivers the infrastructure that enforces the policy;
policy population belongs to a configuration management workflow, not an
implementation issue.

---

## Decision 11: AC 11 — structured-pass incapability rejected at route resolution

**Decision:** `resolve_route` rejects any route where both
`supports_tool_use is False AND supports_structured_output is False` with
`ProviderConfigError`.  This is step 5 of the resolution ladder, symmetric to
the AC 12 text-output rejection.

Only explicit `False` triggers rejection — `None` (unverified) fails safe:
Safety runs, route is live.  If only one of the two structured-pass fields is
`False`, the other may still permit structured calls via that mechanism.

**Rationale:** AC 11 explicitly requires rejection "for structured passes at
resolution" — this is the 14b upgrade over 14a's call-time failure.  Planner
and Extractor require structured output; a route confirmed incapable for both
`tool_use` and `structured_output` cannot serve those passes and must be
rejected before the turn begins.  The fail-safe rule (reject only on positive
evidence) applies: `None` fields are not positive evidence of incapability.

---

## Architecture Notes

**Drift:** None from core design principles.  The safety envelope (conditional
Input Preflight and Output Audit) is preserved.  The stable-prefix is assembled
once per turn.  Entitlement routing is unaffected.

**EligibleWriterRoute → EligibleModelRoute:** Clean replacement, no compat
alias.  Callers updated in the same PR.

**Fail-safe defaults:** Catalog miss → UNKNOWN → Safety.  None fields → Safety.
Rejection only on explicit `False`.

**Capability evaluation (Step 6):** `supports_required_capabilities=True` requires
text output confirmed (`True`), context_length known and ≥ floor, **and** at least
one structured mechanism confirmed (`supports_tool_use is True OR
supports_structured_output is True`).  A route with both structured fields `None`
is not capable — Safety runs, route is live.  A single confirmed mechanism is
sufficient (OR, not AND).

**Dynamic-alias rule:** Static deny-set (O(1)) + catalog defense-in-depth.

**14b ships machinery:** The registry and whitelist infrastructure are complete.
Populating the production catalog/whitelist is a configuration-management concern
outside 14b scope.

**Context-length floor:** Default 8192 is provisional.  Operators configure via
`writer_context_length_floor` constructor parameter.

**OpenRouter cache adapter verification:** The cache adapter verification for
OpenRouter routes (deferred in ADR-014a, Decision 4) remains open.  14b is the
whitelist/registry layer; cache verification belongs to a follow-on task within
Issue 14's scope.
