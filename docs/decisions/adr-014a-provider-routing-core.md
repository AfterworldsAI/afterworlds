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

## Decision 6: No fallback after a Safety BLOCK — enforced structurally

**Decision:** `RefusalFallbackRouter` is only attached to narrative pipeline
adapters (Planner, Writer, Extractor, Contradiction). Safety passes use the same
adapter but the orchestrator halts on a BLOCK verdict before any narrative pass
`call()` occurs. No code path in the router inspects `pass_id` to gate fallback.

**Rationale:** The CRD acceptance invariant is "no fallback after a Safety BLOCK."
Structural enforcement (BLOCK halts the pipeline before narrative passes run) is
more robust than a conditional in `RefusalFallbackRouter`. A conditional there
would need to be tested for every pass and could silently regress.

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

## Decision 10: Lazy imports for `keyring` and `openai` in provider code

**Decision:** `keyring` and `openai` are imported inside method bodies where
they are used (not at module top level). `type: ignore[import-not-found]` is
not needed when packages are installed; stubs for `keyring.errors` are absent
from the installed `keyring` stubs, so `import keyring.errors` carries
`# type: ignore[import-not-found]`.

**Rationale:** These are optional runtime dependencies — `keyring` is absent
on CI runners using `FallbackEnvCredentialStore`; `openai` is absent when no
OpenRouter BYOK key is configured. Lazy imports prevent `ImportError` at module
load time on environments where the package is not installed.

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
passes the full `ProviderCallRequest` object to `refusal_log_fn`. Any future
implementation of `refusal_log_fn` (the DB-write path for `provider_refusal_log`)
MUST NOT serialize prompt text from `system_blocks`/`rendered_blocks` or any
key-containing field into `coarse_metadata_json` or any other column. The column
header and migration docstring both enforce this constraint; enforcement is by
policy in the calling code, not by the router itself. Issue 14b or the first
concrete DB-write implementation must add a test that the serializer only emits
coarse metadata (pass_id, provider, model, outcome) — no prompt fragments.
