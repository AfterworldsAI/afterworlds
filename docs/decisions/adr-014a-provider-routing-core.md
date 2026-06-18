# ADR-014a: Provider Routing, Adapters, BYOK Credentials, Refusal Fallback

**Issue:** CRD Issue 14a — Provider Routing Core
**Date:** 2026-06-10
**Status:** Accepted

---

## Context

CRD Issue 14a replaces the single-provider Anthropic-specific caller injection
pattern with a provider-neutral `ProviderAdapter` protocol, adds BYOK credential
management, introduces `RefusalFallbackRouter`, and adds provider-scoped SQLite
tables. This document records design decisions made during implementation that are
not fully specified by the issue spec or that resolve open architectural questions.

---

## Decision 1: `ProviderCallRequest` does not carry a model identifier

**Decision:** `ProviderCallRequest` has no `model` field. The adapter resolves
model selection from its own configuration (pass-to-model mapping in
`AnthropicCapabilityProfile`).

**Rationale:** The pipeline passes are provider-neutral. Embedding a model
identifier in `ProviderCallRequest` would couple pass construction to
provider-specific model naming schemes. Adapters own model selection; passes
own prompt construction.

**Consequence:** `AnthropicCapabilityProfile.model_for(pass_id)` is the
authoritative pass→model mapping. The `ProviderCallResult` reports
`model_identifier` as a fact, not a directive.

---

## Decision 2: All service constructors drop the `caller=` argument; `provider=` is keyword-only on service methods

**Decision:** Planner, Writer, Safety, Extractor, and Contradiction services no
longer accept `caller=` in their constructors. All service call-site methods
(`plan`, `write`, `check`, `extract`) accept `*, provider: ProviderAdapter` as
a keyword-only argument.

**Rationale:** Issue 12c's constructor injection pattern was convenient for
single-provider Issue 9 but locked the adapter to construction time. Issue 14a's
per-turn provider binding (`TurnProviderBinding`) requires the adapter to be
resolved at turn start, not at service construction. Method-level injection
enables per-turn provider resolution without rebuilding service objects.

---

## Decision 3: `ProviderCallResult` carries flat `*_token_count` fields, not a nested `TokenUsage` object

**Decision:** `cache_read_token_count`, `cache_creation_token_count`,
`input_token_count`, `output_token_count` are top-level `int | None` fields
on `ProviderCallResult`. The `TokenUsage` class from earlier iterations is gone.

**Rationale:** Flat fields are easier to propagate through `SafetyResult`,
`PlannerResult`, etc. without nested attribute traversal. The token count
fields are already optional; a nested object adds an extra nullability layer
with no benefit.

---

## Decision 4: `RenderedBlock` replaces `TextBlockParam` dicts in all stable-prefix and service-level rendering

**Decision:** `render_stable_prefix_blocks()` returns `list[RenderedBlock]`
instead of `list[TextBlockParam]`. `RenderedBlock` carries `text`,
`has_cache_breakpoint`, and `ttl`. Adapters convert `RenderedBlock` to
provider-specific wire types (`TextBlockParam`, OpenAI message dicts).

**Rationale:** Decouples cache marker semantics from the Anthropic SDK type.
OpenRouter and future adapters can read `has_cache_breakpoint`/`ttl` and map
to their own cache control representations without the pipeline passing around
Anthropic-specific dict shapes.

---

## Decision 5: `PromptRenderer` in `writer/renderer.py` and `AnthropicModelCaller` in `writer/caller.py` are removed as dead code

**Decision:** `writer/renderer.py` and `writer/caller.py` (Issue 9 legacy) are
deleted. `WriterService._render()` builds `ProviderCallRequest` directly.

**Rationale:** After the Issue 14a rewrite, `PromptRenderer` and
`AnthropicModelCaller` had no callers in src/ or tests/. Keeping them would
cause a `list[RenderedBlock]` vs `list[TextBlockParam]` type mismatch in mypy
strict mode with no path to resolution that doesn't break the abstraction. Dead
code that causes mypy failures is removed.

---

## Decision 6: Safety provider refusals are excluded from fallback by an explicit router guard

**Decision:** `RefusalFallbackRouter.call()` contains an explicit pass-id guard:
when the primary raises `ProviderRefusalError` on `INPUT_SAFETY` or
`OUTPUT_SAFETY`, fallback is bypassed, a `NO_FALLBACK_CONFIGURED` log row is
written for the audit record, and the original `ProviderRefusalError` is
re-raised immediately. Narrative and state passes (Planner, Writer, Extractor,
Contradiction) remain fallback-eligible on `ProviderRefusalError`.

**Rationale:** The CRD acceptance invariant is "no fallback after a Safety
provider refusal." The guard in the router provides defense-in-depth when a
Safety pass refusal fires inside an already-running orchestration (e.g., Output
Safety after Writer completes). The audit row is preserved regardless — the
`NO_FALLBACK_CONFIGURED` code is logged before re-raise so refusal analytics and
support reconstruction can distinguish "refused with no fallback available" from
"refused on a pass where fallback is structurally disabled by policy."

---

## Decision 7: Nested `RefusalFallbackRouter` is rejected at construction

**Decision:** `RefusalFallbackRouter.__init__` raises `ProviderConfigError` if
`fallback` is itself a `RefusalFallbackRouter`.

**Rationale:** CRD invariant: "at most one fallback attempt per pass call."
Constructor rejection makes the invariant impossible to violate through
misconfiguration; runtime detection would be too late.

---

## Decision 8: BYOK fallback pool is bounded by configured credentials

**Decision:** `ProviderResolver._resolve_byok()` builds the fallback pool from
credentials present in `CredentialStore` at turn resolution time. If only one
provider is configured, there is no fallback. Fallback never crosses the
hosted/BYOK boundary.

**Rationale:** CRD invariant: "BYOK fallback may only use provider
credentials/configuration the user supplied." Dynamic pool expansion (e.g.,
using hosted keys as BYOK fallback) would violate this invariant silently.
The resolver's structure makes boundary crossing structurally impossible.

---

## Decision 9: `provider_refusal_log` is append-only with SQLite triggers

**Decision:** Migration 0010 installs `BEFORE UPDATE` and `BEFORE DELETE` triggers
on `provider_refusal_log`, matching the `entitlement_event` pattern from
migration 0009.

**Rationale:** Refusal logs are audit evidence. Mutability would allow
after-the-fact erasure of refusal patterns. Append-only at the DB layer (not
just the ORM layer) provides durable audit integrity.

---

## Decision 10: `keyring` and `openai` are declared runtime dependencies; lazy imports are hygiene only

**Decision:** `keyring` and `openai` are declared runtime dependencies in
`pyproject.toml` and are present in normal installs. Lazy imports (inside method
bodies rather than at module top level) are retained as implementation hygiene but
are no longer required for absence. Stubs for `keyring.errors` are absent from the
installed `keyring` stubs, so `import keyring.errors` still carries
`# type: ignore[import-not-found]`.

**Rationale:** Both packages are required at runtime for the BYOK credential path
(`keyring` for `OSKeychainCredentialStore`, `openai` for the OpenRouter adapter's
HTTP client). Lazy imports prevent `ImportError` at module load time on
environments that load provider modules without exercising the BYOK path (e.g.,
lightweight tooling environments), but the packages must not be treated as absent
in production or CI.

---

## Decision 11: Fallback operational failure re-raises the primary `ProviderRefusalError`

**Decision:** When the primary raises `ProviderRefusalError` and the fallback
raises `ProviderCallError` (operational failure — network, timeout, server error),
`RefusalFallbackRouter` logs `FALLBACK_ERROR` and re-raises the **primary**
`ProviderRefusalError` — not the fallback `ProviderCallError`.

**Rationale:** A fallback operational failure did not change the nature of the turn
outcome: the primary legitimately refused. The orchestrator's terminal disposition
remains `REFUSED_BY_PROVIDER`, not `PIPELINE_ERROR`. UI and support tooling can
resolve "why did this turn end?" from the typed `ProviderRefusal` field without
needing to reason about what the fallback did. The `FALLBACK_ERROR` code in
`provider_refusal_log` records the fallback failure for operational investigation
without promoting it to the terminal cause.

---

## Decision 12: BYOK credential eligibility requires active metadata, non-error status, and retrievable key

**Decision:** In 14a, a BYOK provider is eligible for turn routing if and only if:
1. A `ProviderCredentialMetadata` row exists for `(sojourner_id, provider_name)`
   with `is_active=True`.
2. The row's `validation_status` is not `"invalid"` or `"error"`.
3. A raw key is retrievable from `CredentialStore`.

`"valid"` and `"untested"` status values are eligible. A credential that has
never been validated (`"untested"`) is treated as potentially available rather
than failing closed, consistent with new-install ergonomics where a Sojourner
may add a key before running validation. Stricter validate-before-use behavior
(requiring `"valid"` status) is deferred as a later owner decision.

**Rationale:** Failing hard on `"untested"` would block first-use for any
Sojourner who adds a credential without immediately running a validation check.
`is_active=False` is the definitive opt-out controlled by the user; `"invalid"`
and `"error"` represent states where the system determined the key is known-bad
and should not be presented to a provider API, regardless of whether the user
has explicitly deactivated it.

---

## Architecture Notes

No drift from the core design principles. The safety envelope (conditional
Input Preflight and Output Audit) is preserved structurally. The stable-prefix
is assembled once per turn and shared across all passes via `TurnProviderBinding`.
Extended-TTL caching (`"1h"`) is applied by default wherever `has_cache_breakpoint`
is True. Entitlement routing governs billing path and access path; it does not
affect whether the core narrative pipeline or safety envelope exists.

Known Unknowns touched: none. Cache behavior for OpenRouter routes is noted as
requiring adapter verification before enabling (documented in Decision 4 and
in `_openrouter.py` module docstring); this defers to CRD Issue 14b.

**`refusal_log_fn` serialization invariant:** `RefusalFallbackRouter._log`
passes the full `ProviderCallRequest` object to `refusal_log_fn`. The concrete
DB-write implementation (`_build_refusal_log_fn` in `_resolver.py`) MUST NOT
serialize prompt text from `system_blocks`/`rendered_blocks` or any key-containing
field into `coarse_metadata_json` or any other column. Enforcement is by policy in
the calling code, not by the router itself. This constraint is verified by
`tests/pipeline/provider/test_refusal_log_writer.py::test_log_row_excludes_prompt_text_and_raw_excerpt`.

**Decision 10: `session_factory` is required for `ProviderResolver.resolve_for_turn`.**
`_resolve_hosted` and `_resolve_byok` raise `ProviderConfigError` when
`session_factory is None`. All resolver-produced routes are wrapped in
`RefusalFallbackRouter` with a `refusal_log_fn` backed by the session factory.
Single-provider routes use `fallback=None` so that `NO_FALLBACK_CONFIGURED` is
logged before re-raising the original `ProviderRefusalError`.
