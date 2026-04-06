# ADR-0005 — Story Bible Events Ledger: Significance Taxonomy and Always-Include Policy

**Status:** Accepted
**Date:** 2026-04-06
**Issue:** 4 — Story Bible Schema and Service
**Resolves Known Unknown:** "Significance flagging criteria for Events Ledger" and "Events Ledger tiered inclusion N value"

---

## Context

The Events Ledger is an append-only record of narrative events in the Story Bible.
The full ledger lives in SQLite, but only a subset is loaded into the active context
window for each pipeline turn.  The tiered inclusion policy must balance two competing
pressures:

- **Context window pressure:** loading every event is expensive and bloats the stable
  prefix, increasing per-turn cost and cache miss risk.
- **Continuity coverage:** events that define irreversible narrative facts must always
  be visible to the pipeline regardless of how many routine events have accumulated
  since.

The architecture (design.md §2) specifies that the Events Ledger uses a tiered
inclusion policy.  The known_unknowns.md listed two open decisions that must be
resolved during Issue 4:

1. Which significance values qualify for always-include behaviour.
2. The starting value of N (most-recent events to load unconditionally).

---

## Decision

### Significance Taxonomy

Seven values are defined in `EventSignificance` (a `StrEnum`):

| Value | Description |
|---|---|
| `ROUTINE` | A normal narrative event — no special inclusion behaviour |
| `CHARACTER_DEATH` | A character has died — irreversible narrative fact |
| `LOCKED_FACT_ESTABLISHED` | A new locked fact has been committed to canon |
| `MAJOR_PLOT_TURN` | A major reversal, revelation, or turning point |
| `RELATIONSHIP_CHANGE` | A significant shift in a character-to-character relationship |
| `WORLD_STATE_CHANGE` | A permanent world-level shift (e.g. "the war began", "the city fell") |
| `FORBIDDEN_FACT_ESTABLISHED` | A new forbidden fact has been explicitly confirmed |

The minimum set required by the spec (`CHARACTER_DEATH`, `LOCKED_FACT_ESTABLISHED`,
`MAJOR_PLOT_TURN`, `RELATIONSHIP_CHANGE`) is covered.  Two additional values
(`WORLD_STATE_CHANGE`, `FORBIDDEN_FACT_ESTABLISHED`) are added because:

- **`WORLD_STATE_CHANGE`:** permanent world-level events (e.g. "the treaty was
  broken") are load-bearing for the Contradiction Checker but accumulate slowly;
  missing them in context would cause continuity errors.
- **`FORBIDDEN_FACT_ESTABLISHED`:** an explicit "must not happen" constraint added
  mid-story must remain visible to Safety and Contradiction passes for the rest of
  the story.

### Always-Include Set

Six of the seven values qualify for always-include:

```python
ALWAYS_INCLUDE_SIGNIFICANCE: frozenset[EventSignificance] = frozenset({
    EventSignificance.CHARACTER_DEATH,
    EventSignificance.LOCKED_FACT_ESTABLISHED,
    EventSignificance.MAJOR_PLOT_TURN,
    EventSignificance.RELATIONSHIP_CHANGE,
    EventSignificance.WORLD_STATE_CHANGE,
    EventSignificance.FORBIDDEN_FACT_ESTABLISHED,
})
```

`ROUTINE` is the only value that does NOT qualify for always-include.  Routine events
fall out of the context window once they age beyond N.

### N Value

**Starting value: 15.**

This matches the known_unknowns.md starting estimate.  Implemented as the module-level
constant `EVENTS_LEDGER_N: int = 15` in `services/story_bible.py`.  It must be tuned
with testing against representative story scenarios at minimal, moderate, and complex
Story Bible sizes.

### Single Source of Truth

`ALWAYS_INCLUDE_SIGNIFICANCE` is defined once in `services/story_bible.py`.
Callers (including tests) must import and use this constant; they must not
reimplement the policy logic.  The `EventSignificance` enum is defined in
`models/enums.py` alongside all other project enums.

---

## Consequences

- The Extractor (Issue 10) must assign a significance value from this enum when
  proposing event additions.  The significance field on Events Ledger entries is a
  typed enum — not a freeform string or secondary boolean flag.
- The Context Builder (Issue 8) calls `get_active_context_window`, which applies the
  tiered inclusion policy internally.  Callers do not reimplement it.
- `ROUTINE` events older than N are not loaded.  Stories with many routine events
  will shed old routine history naturally; high-significance events are permanent in
  the context window.
- The N value may be increased if testing reveals the recent-N window misses
  continuity-relevant events at typical story lengths.  Changes to `EVENTS_LEDGER_N`
  are local to the service module.

---

## Alternatives Considered

**Boolean `is_high_significance` flag instead of enum.**
Rejected.  A boolean collapses all significance gradations into one bit, preventing
fine-grained routing by the Extractor, and makes future taxonomy extension impossible
without schema changes.

**Freeform string significance field.**
Rejected.  Freeform strings cannot be validated statically or used as reliable enum
dispatch targets.  The spec explicitly requires a typed enum.

**Always-include all non-ROUTINE values (same as chosen approach).**
Accepted as the correct default.  The five mandatory criteria plus two added values
are all genuinely irreversible narrative facts.  The cost of including them permanently
is low (they accumulate slowly); the cost of missing them is high (continuity errors).
