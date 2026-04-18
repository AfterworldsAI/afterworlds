# ADR-0010 — Context Builder Design Decisions (Issue 8)

**Status:** Accepted
**Date:** 2026-04-18
**Issue:** CRD Issue 8 — Context Builder (GitHub #TBD)
**Scope:** Rule slice placement; ROLLING_SUMMARY_N status; RuleSliceRequest scope

---

## Decision 1 — Rule Slice is Separate from StablePrefix

### Context

CRD Issue 8 requires the Context Builder to retrieve rule slices for RPG mode.
The question is whether the rule slice belongs inside `StablePrefix` (alongside
the system prompt, Story Bible, and rolling summary) or is stored separately.

The CRD stable-prefix cost model assumes a cache hit rate of ~88% with extended
TTL (1-hour).  This rate depends on the stable prefix being byte-for-byte
identical across turns within the same session.

`RuleSliceRequest.subsystem_tags` and `entity_refs` can change between turns:
a combat turn queries `COMBAT` subsystem; the next turn queries `SPELLS`.  A
different query produces a different slice, which changes the stable prefix
byte sequence and busts the cache hit for that turn.

### Decision

**Rule slice is stored as a separate field (`rule_slice`) on `AssembledContext`,
not inside `StablePrefix`.**

The assembled context structure is:

```
AssembledContext
  stable_prefix      — system prompt + Story Bible + rolling summary
  rule_slice         — ActiveRuleSlice | None (separate from stable prefix)
  volatile_suffix    — recent turns + current input + intent
  pass_forward_ledger — mutable per-pass additions
```

`AssembledContext.render_for_pass()` renders all components in the documented
canonical order (stable prefix → rule slice → pass-forward ledger → volatile
suffix), so the pipeline (Issue 12) always sees the correct prompt structure.

### Rationale

- Cache economics: keeping rule_slice separate preserves the stable prefix as
  a stable byte sequence across turns with different subsystem queries.
- Architectural clarity: the CRD explicitly lists "system prompt + mode contract
  + Story Bible active context + rolling summary" as stable prefix components.
  Rule slice is not in that list.
- The CRD says "retrieves rule slices on demand by mode" — "on demand" implies
  per-turn, not per-session.

### Consequences

- `StablePrefix` does not contain `rule_slice`.  Tests verify this structurally.
- `AssembledContext.render_for_pass()` inserts the rule slice text between
  stable prefix and volatile suffix (optimal position for context layering).
- The pipeline (Issue 12) must pass the `AssembledContext` (including its
  `rule_slice`) to each pass, not just the `stable_prefix`.

---

## Decision 2 — ROLLING_SUMMARY_N Status: Partial Measurement, Not Closed

### Context

ADR-0009 deferred empirical finalization of `ROLLING_SUMMARY_N` to Issue 8,
with the explicit mandate:

> "Issue 8 (Context Builder) must measure stable-prefix pressure with N = 10
> and produce an updated ADR entry or an amendment to this ADR if the value
> needs adjustment."

### What Was Measured in Issue 8

Stable prefix token budget was estimated analytically from the CRD cost model
using representative Story Bible content (minimal / moderate / complex):

| Scenario | System prompt | Story Bible | Rolling summary | Total stable prefix |
|---|---|---|---|---|
| Minimal   | ~500 tok | ~5,000 tok  | ~500 tok  | ~6,000 tok  |
| Moderate  | ~500 tok | ~12,000 tok | ~800 tok  | ~13,300 tok |
| Complex   | ~500 tok | ~22,000 tok | ~1,200 tok | ~23,700 tok |

With `ROLLING_SUMMARY_N = 10` and an estimated average turn length of ~500
tokens, the volatile suffix carries ~5,000 tokens of verbatim recent turns
plus ~150 tokens of current input.  Total context at moderate scenario:
~18,450 tokens per pass — well within model limits and consistent with the
CRD cost model estimates.

Analytically, N = 10 appears to produce rolling summaries in the ~500–1,200
token range and does not cause stable-prefix overflow.

### What Cannot Be Measured Without the Writer Path

1. **Actual turn length distribution** — CRD estimates 500 tokens/turn, but
   RPG, Branching, and Writing mode turns may differ significantly.  No real
   turns exist until Issue 9 (Writer) produces output.

2. **Summary quality vs. compression frequency tradeoff** — shorter windows
   (N = 5) compress more frequently but over less content per window; wider
   windows (N = 20) accumulate more per-turn content before compressing.
   Quality cannot be assessed without a real Writer producing real prose.

3. **Cache window interaction** — whether N = 10 produces summaries that stay
   within the stable prefix budget across long campaign sessions requires
   empirical measurement with real session data.

### Decision

**N = 10 is confirmed as the provisional value.  The Known Unknown is NOT
declared closed.**

The analytical evidence is consistent with N = 10 being a reasonable starting
value, but it is not empirically validated.  Full empirical finalization
requires the Writer path (Issue 9) to be operational.

The `ROLLING_SUMMARY_N = 10` constant in `services/rolling_summary.py` remains
unchanged.  Issue 9 or a follow-up issue should measure real stable-prefix
pressure once real turns are being produced and update this ADR if adjustment
is needed.

This ADR records the analytical measurement as required by ADR-0009.  The
known_unknowns.md entry for ROLLING_SUMMARY_N remains in the "Resolved"
section per the existing ADR-0009 entry, with this ADR providing the partial
Issue 8 measurement.

### Consequences

- `ROLLING_SUMMARY_N` stays at 10.
- This ADR documents the analytical stable-prefix budget measurement.
- Empirical validation is explicitly deferred to post-Issue-9 once real Writer
  output is available.
- PR Architecture Notes for Issue 8 surface this as a Known Unknown not yet
  fully resolved (no unilateral resolution).

---

## Decision 3 — RuleSliceRequest Defined in Issue 5a Domain

### Context

The Issue 8 implementation brief instructed: "Reuse `RuleSliceRequest` from
Issue 5a; do not define a parallel model."  However, `RuleSliceRequest` was
not defined during Issue 5a — only `ActiveRuleSlice` (the return type) exists
in `models/rules_package.py`.

### Decision

**`RuleSliceRequest` is added to `src/afterworlds/models/rules_package.py`
(Issue 5a's namespace) rather than creating a parallel model in the Context
Builder module.**

This satisfies the "do not define a parallel model" instruction and keeps the
request/response pair (`RuleSliceRequest` / `ActiveRuleSlice`) co-located in
the Rules Package domain.

### Rationale

- `RuleSliceRequest` bundles parameters that are inherently Rules Package
  domain concepts: `package_id`, `subsystem_tags`, `entity_refs`.
- Defining it in the Context Builder namespace would create cross-domain
  coupling (Context Builder importing from Rules Package for the return type,
  but owning the request type).
- The instruction "Reuse RuleSliceRequest from Issue 5a" implies it was
  intended to live in that domain; it was simply omitted during Issue 5a.

### Consequence

This PR adds a new model to `models/rules_package.py` that was in scope for
Issue 5a but not defined there.  This is a minor scope boundary extension; it
is surfaced here rather than silently omitted or defined as a duplicate in the
Context Builder namespace.
