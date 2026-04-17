# ADR-0009 — Rolling Summary Compression Trigger Value N

**Status:** Accepted (provisional — empirical finalization deferred to Issue 8)
**Date:** 2026-04-17
**Issue:** CRD Issue 6 — Rolling Summary Service (GitHub #63)
**Resolves Known Unknown:** "Rolling summary compression trigger value (N turns)"

---

## Context

The Rolling Summary memory layer is compressed every N turns.  N is a
designated Known Unknown from `known_unknowns.md` with the following
resolution rule:

> **Default rule:** N should be resolved during Issue 6.
>
> **Escape hatch:** if Issue 6 cannot produce meaningful stable-prefix-pressure
> evidence because the Context Builder integration does not yet exist, the ADR
> must say so explicitly.  In that case, the ADR must record:
> - the configurable mechanism,
> - the provisional value of 10,
> - the specific reason empirical finalization could not be completed in Issue 6,
> - that empirical finalization is deferred to Issue 8 only.

This ADR invokes the escape hatch.

---

## Decision

**Provisional N = 10.**

Implemented as the module-level constant:

```python
ROLLING_SUMMARY_N: int = 10
```

in `src/afterworlds/services/rolling_summary.py`.

N is exposed as a configurable value, not a hardcoded literal.  The
`should_compress(story_turn_count, n=ROLLING_SUMMARY_N)` helper accepts an
explicit `n` argument, making the trigger configurable in tests and
adjustable without code changes once a config layer exists.

---

## Why Empirical Finalization Cannot Be Completed in Issue 6

The right trigger value for N depends on:

1. **Stable-prefix budget pressure:** how many tokens the Rolling Summary
   typically consumes relative to the Story Bible and system prompt.  This
   requires the Context Builder (Issue 8) to be wired so that a real
   stable-prefix assembly can be measured with representative content.

2. **Turn length distribution at steady state:** what a "normal" turn looks
   like in each mode (RPG action, Branching beat, Writing exchange).  This
   data only accumulates once the Writer path (Issue 9) is producing real
   output.

3. **Cache window economics:** a summary that fires too frequently wastes
   generation cost; one that fires too rarely causes the Immediate layer
   (recent turns verbatim) to overflow the available prefix budget.  The
   cost model in the CRD (Item 8) estimates the stable prefix at 5k–24k
   tokens and the rolling summary component at roughly 500–1,200 tokens —
   but these figures are estimates, not measured values.

At Issue 6, none of this evidence exists:

- The Context Builder does not exist; no stable prefix has ever been
  assembled end-to-end.
- No Writer path produces real turns; turn length distribution is unknown.
- ChromaDB integration (Issue 18) is not yet wired; retrieval overhead is
  not measurable.

Choosing N = 10 is consistent with the known_unknowns.md starting value.
It is *empirically unsettled*, and this ADR says so explicitly rather than
pretending the value is validated.

---

## Configurable Mechanism

`ROLLING_SUMMARY_N` is defined as a plain integer constant at module scope.
Callers and tests can:

1. Import and assert the current value: `from afterworlds.services.rolling_summary import ROLLING_SUMMARY_N`.
2. Pass a different `n` to `should_compress(count, n=custom_n)` to test
   trigger behavior at any threshold without patching global state.
3. Override the module constant in integration tests or configuration shims
   without any code change to the service internals.

The value is intentionally not buried in a constructor argument — it is a
single module-level constant that is the single source of truth for the
default trigger, matching the pattern of `EVENTS_LEDGER_N` in
`services/story_bible.py`.

---

## Deferred Finalization — Issue 8 Only

Empirical finalization of N is deferred to **Issue 8 (Context Builder)**,
where:

- The stable prefix is assembled end-to-end for the first time.
- Token budgets for each memory layer can be measured against real content.
- Cache hit rates under different N values can be estimated from the
  pipeline cost model.
- The tradeoff between compression frequency and stable-prefix token
  pressure can be observed directly.

**N must not be further deferred to Issue 12 or later.**  The known_unknowns.md
escape hatch explicitly prohibits deferral past Issue 8.

---

## Alternatives Considered

**N = 5 (more frequent compression):**
More frequent summaries keep the Immediate layer shorter, reducing volatile
suffix size.  But more frequent generation calls add cost and may produce
lower-quality summaries over short turn windows.  Insufficient evidence to
prefer this without stable-prefix measurement.

**N = 20 (less frequent compression):**
Allows longer verbatim turn histories before compression, which may improve
summary quality.  But risks stable-prefix bloat if the rolling summary
balloons to cover many turns' worth of content.  Again, insufficient evidence.

**Hardcoded constant (not configurable):**
Rejected per the issue spec requirement: "implement N as a configurable
value, not a hardcoded literal."

---

## Consequences

- `ROLLING_SUMMARY_N = 10` is the active trigger value from Issue 6 onward.
- Issue 8 (Context Builder) must measure stable-prefix pressure with N = 10
  and produce an updated ADR entry or an amendment to this ADR if the value
  needs adjustment.
- `known_unknowns.md` is updated to move the N-value item from Open to
  Resolved (with this escape-hatch deferral noted).
