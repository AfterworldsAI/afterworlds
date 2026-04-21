# ADR-0010 — Context Builder Design Decisions (Issue 8)

**Status:** Accepted
**Date:** 2026-04-18
**Issue:** CRD Issue 8 — Context Builder (GitHub #68)
**Scope:** Rule slice placement; ROLLING_SUMMARY_N status; RuleSliceRequest scope

---

## Decision 1 — Rule Slice is Inside StablePrefix (Revised)

**Note:** This decision reverses the initial implementation choice.  The
original implementation stored `rule_slice` as a separate field on
`AssembledContext`.  Issue #68 review established that the canonical Issue 8
contract requires `rules_package_slice` to be a named field inside
`StablePrefix`.  This revision supersedes the original decision.

### Context

CRD Issue 8 requires the Context Builder to retrieve rule slices for RPG mode.
The canonical Issue 8 field order for `StablePrefix` is:

1. `system_prompt` — mode contract
2. `story_bible_context` — ratified Story Bible canon
3. `rolling_summary_text` — compressed narrative history
4. `rules_package_slice` — RPG rule slice (mode × intent policy gate)
5. `retrieval_memory` — vector retrieval payload

This five-field shape is the stable-prefix contract between the Context Builder
(Issue 8) and the pipeline (Issue 12).  Every field must be a named attribute
on `StablePrefix`; no field may float on `AssembledContext` as a peer of
`stable_prefix`.

A secondary concern is cache economics: the CRD stable-prefix cost model
assumes ~88% cache hit rate with extended TTL (1-hour).  Including a
query-dependent rule slice inside `StablePrefix` can change the stable prefix
byte sequence between turns (combat turn → COMBAT subsystem; lore turn →
SPELLS subsystem), which busts the cache for those turns.

### Decision

**`rules_package_slice` is a named field (field #4) on `StablePrefix`, per the
canonical Issue 8 contract.**

The assembled context structure is:

```
AssembledContext
  stable_prefix         — system_prompt + story_bible_context +
                          rolling_summary_text + rules_package_slice +
                          retrieval_memory
  volatile_suffix       — recent turns + current input + intent
  pass_forward_ledger   — mutable per-pass additions
```

`StablePrefix.render()` renders all five fields in canonical order.
`AssembledContext.render_for_pass()` renders stable prefix → pass-forward
ledger → volatile suffix.

A mode × intent policy gate in `build_stable_prefix()` ensures rule slices are
only retrieved for RPG mode with qualifying intents (IN_CHARACTER_ACTION,
DIALOGUE, LORE_QUESTION).  Non-qualifying combinations produce
`rules_package_slice = None`, which is omitted from the rendered output.

### Cache Tradeoff

Including `rules_package_slice` inside `StablePrefix` means that turns with
different subsystem queries (combat vs. lore) will produce different stable
prefix byte sequences and not share cache entries.  This is accepted because:

- The mode × intent policy gate means most non-combat turns yield
  `rules_package_slice = None`, which is identical across those turns and
  therefore cache-friendly.
- RPG combat turns (where the slice changes) are expected to be sequential
  within the same encounter; cross-encounter cache busts are acceptable.
- Where to draw the cache breakpoint (stable vs. volatile) for the rule slice
  is an Issue 12 (pipeline) and Issue 14 (caching) concern.  Forcing the
  correct Issue 8 field shape now avoids a larger architectural correction later.

### Rationale

- Issue #68 contract: the Issue 8 review explicitly requires `rules_package_slice`
  as named field #4 on `StablePrefix`.  Issue #68 wins over the original
  implementation choice (CLAUDE.md non-negotiable rule).
- Architectural clarity: all stable memory layers (Story Bible, rolling summary,
  rules, retrieval) belong inside `StablePrefix`.  A rule slice floating on
  `AssembledContext` as a peer of `stable_prefix` confuses the partition
  semantics that the pipeline relies on.
- The pipeline (Issue 12) should receive a complete `StablePrefix` that it can
  pass unchanged across all five passes — not an `AssembledContext` with a
  floating field it must thread separately.

### Consequences

- `StablePrefix` has five named fields in canonical order.  Tests verify this
  structurally and verify the render order.
- `AssembledContext` does not have a `rule_slice` field.  Any consumer that
  depended on the old placement must read from
  `assembled_context.stable_prefix.rules_package_slice`.
- The cache tradeoff for rule-slice-containing stable prefixes is acknowledged
  and accepted.  Empirical cache measurement deferred to Issue 12/Issue 14.

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

---

## Decision 4 — Retrieval Memory Cache Boundary Reconciliation

**Status:** Accepted
**Date:** 2026-04-21
**Trigger:** Codex P2 review comment on PR #69 (round 3); owner decision posted
  in thread `PRRC_kwDORsj9Fs65ox7S`.

### Context

The round-2 implementation of Issue 8 called
`RetrievalMemoryProvider.retrieve(story_id, intent_classification.raw_input)`
from inside `build_stable_prefix()` and stored the returned payload in
`StablePrefix.retrieval_memory`.

This creates a cache-boundary violation: the stable prefix is the cacheable
block shared across all pipeline passes and across turns where Story Bible,
rolling summary, and mode contract are unchanged.  A retrieval query keyed off
`intent_classification.raw_input` (which varies every turn) makes the "stable"
prefix vary per turn, collapsing cross-turn cache reuse.  This conflicts with:

- `docs/architecture/design.md` — stable prefix is the block above retrieved facts
- CRD Item 12 / architectural invariant: stable prefix assembled once per turn
  and shared unchanged across all passes
- The ~88% cache hit rate the CRD cost model depends on

### Decision

**Issue 8 preserves the injectable retrieval seam and typed placeholder
contract.  Issue 8 does NOT materialize query-dependent retrieval results
inside the cacheable stable prefix.**

Specifically:

1. `RetrievalMemoryProvider` remains injectable via `ContextBuilderService.__init__`
   (seam preserved; Issue 18 replaces `NullRetrievalMemoryProvider` without
   changing the constructor signature).
2. `StablePrefix.retrieval_memory` remains as a named typed field
   (`RetrievalMemoryPayload`).  It is always empty (`passages=[]`) when
   assembled by Issue 8 code.
3. `build_stable_prefix()` does NOT call `self._retrieval_memory.retrieve()`.
   `StablePrefix` is constructed with `retrieval_memory=RetrievalMemoryPayload()`.
4. Real placement of query-dependent retrieval results is deferred to
   **Issue 18** (ChromaDB integration), informed by the provider/prompt-boundary
   work from Issues 9 (Writer), 12 (pipeline), and 14 (caching).  Issue 18
   will determine whether retrieval results belong in the volatile suffix, a
   separate retrieval block, or elsewhere.

### Rationale

- The cache-boundary violation in round-2 was a direct conflict with the
  stable-prefix architectural invariant (CLAUDE.md non-negotiable).
- Deferring placement to Issue 18 is the correct scope boundary: Issue 8 owns
  the seam and the typed contract; Issue 18 owns retrieval implementation and
  prompt-boundary placement.
- Removing the `retrieve()` call from `build_stable_prefix()` removes the
  violation without prematurely designing retrieval placement.

### Consequences

- `StablePrefix.retrieval_memory` is always `RetrievalMemoryPayload(passages=[])`
  when assembled by the Context Builder.  The field exists for schema continuity
  and renders nothing in the stable prefix output.
- Tests that previously asserted query-dependent retrieval was wired into the
  stable prefix are replaced with tests that assert non-materialization.
- Issue 18 must decide final placement; this ADR records the defer explicitly
  so that decision is not lost.
