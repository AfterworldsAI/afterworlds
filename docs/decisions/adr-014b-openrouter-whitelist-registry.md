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
when the catalog affirmatively reports the model is incapable:
`supports_text_output is False` (explicit `False`, not `None`).  A catalog miss,
`None` capability flags, or `context_length=None` all collapse to
`supports_required_capabilities=False` without rejecting the route — Safety runs,
the route is live.

**Rationale:** Over-rejecting a route on absent evidence is worse than running
Safety on it.  A model the catalog does not know about might be valid; a model
with no reported context length might still work.  Rejection is reserved for
positive evidence of incapability, not absence of positive evidence of
capability.

---

## Decision 4: Context-length floor is a capability gate, not a rejection gate

**Decision:** `_WRITER_CONTEXT_LENGTH_FLOOR = 8192` is used only in the
capability evaluation (step 6 of `resolve_route`): a model with
`context_length < floor` gets `supports_required_capabilities=False` and Safety
runs, but the route is not rejected with `ProviderConfigError`.  The constant
is marked provisional.

**Rationale:** The floor value is an owner decision, not a value derivable from
provider documentation.  At any specific floor, legitimate models with shorter
context windows would be silently rejected.  The safer approach is: confirmed
capable = both `supports_text_output is True` AND `context_length >= floor`.
Below floor: Safety runs.  A future owner decision can raise the floor or
introduce explicit route rejection at a spec-mandated threshold.

**Known Unknown carried forward:** The exact context-length floor and whether a
below-floor model should be rejected outright (vs. Safety always running) remain
owner decisions.  See `known_unknowns.md`.

---

## Decision 5: STALE vs. UNKNOWN semantics

**Decision:**
- `UNKNOWN` — model id is not in the whitelist and not in the catalog.
  Safety always runs.  Route not rejected.
- `STALE` — model id IS in the whitelist but is NOT found in the catalog.
  The model was previously approved but is no longer visible.  Safety always
  runs.  Route not rejected.

**Rationale:** The distinction matters for operational observability.  `STALE`
signals a whitelist entry that may need review (model delisted or renamed).
`UNKNOWN` signals a model the system has never assessed.  Both force Safety;
neither rejects the route, consistent with the fail-safe rule.

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
raises `ProviderConfigError` (positive incapability — `supports_text_output is
False`), the exception propagates through `_resolve_openrouter_route` and the
entire `resolve_for_turn` call fails.  The primary Anthropic pass does not
proceed.

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

## Decision 11: AC 11 (structured-pass incapability) is handled at call time, not at route resolution

**Decision:** `resolve_route` evaluates Writer pass capability only.  A model
that is confirmed Writer-capable (`supports_text_output=True`, adequate context)
but both `supports_tool_use=False` and `supports_structured_output=False` is
not rejected at route resolution time.  Structured passes (Planner, Extractor)
that require tool use or structured output will raise `ProviderCallError` at
call time through the existing 14a adapter behavior.

**Rationale:** `supports_required_capabilities` on `EligibleModelRoute` drives
the Safety-skip decision for the Writer pass.  Planner/Extractor fail-closed at
call time (14a behavior) is the correct gate for structured-pass capability.
Pre-catalog rejection of routes with confirmed structured-pass incapability was
considered; it would require a separate resolution axis in `resolve_route` and
is deferred as an owner decision.  See Architecture Notes.

---

## Architecture Notes

**Drift:** None from core design principles.  The safety envelope (conditional
Input Preflight and Output Audit) is preserved.  The stable-prefix is assembled
once per turn.  Entitlement routing is unaffected.

**Scope question — AC 11 (structured-pass incapability at route resolution):**
The current implementation does not pre-reject OpenRouter routes where both
`supports_tool_use` and `supports_structured_output` are explicitly `False`.
Such routes are live (Safety runs), but will fail at call time when the Planner
or Extractor pass attempts a structured call.  Whether this is acceptable or
whether the registry should pre-reject these routes is an owner decision.  It is
not resolved in 14b.

**Known Unknown carried forward — context-length floor:**
`_WRITER_CONTEXT_LENGTH_FLOOR = 8192` is provisional.  The value and rejection
semantics (floor below → `ProviderConfigError` vs. Safety runs) are owner
decisions documented in `known_unknowns.md`.

**14b does not carry forward the 14a cache-verification work:**
The cache adapter verification for OpenRouter routes (deferred in ADR-014a,
Decision 4) remains open.  14b is the whitelist/registry layer; OpenRouter
cache verification belongs to a follow-on task within Issue 14's scope.
