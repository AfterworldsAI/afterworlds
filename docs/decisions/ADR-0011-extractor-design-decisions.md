# ADR-0011 — Extractor Pass Design Decisions (CRD Issue 10)

**Status:** Accepted
**Date:** 2026-04-25
**Issue:** CRD Issue 10 — Extractor Classification Policy
**Scope:** Tool-use output schema; EVENT proposal type; cast-name resolution;
  pass-forward content; cross-pass cache reuse

---

## Decision 1 — Anthropic Tool Use for Structured Extraction Output

### Context

The Extractor pass must produce structured, typed proposal output (locked facts,
soft facts, transient states, unresolved threads, events).  Options:

1. **Tool use (`tool_choice` forced)** — model always calls the extraction tool;
   response is a `ToolUseBlock` with a validated JSON input dict.
2. **Prose JSON** — model returns a JSON blob inside a text response; service
   parses it.
3. **Separate classification calls** — one LLM call per category.

### Decision

**Option 1: Anthropic tool use with `tool_choice={"type": "tool", "name":
"propose_story_bible_updates"}` to force a single tool call per Extractor pass.**

The `EXTRACT_TOOL_SPEC` in `pipeline/extractor/caller.py` defines five typed
array fields: `locked_facts`, `soft_facts`, `transient_states`,
`unresolved_threads`, `events`.  All are optional (`required: []`) so the model
can omit categories where nothing was found.

### Rationale

- Tool use eliminates fragile JSON-in-prose parsing.
- `tool_choice={"type": "tool", "name": ...}` forces the model to always call
  the tool, producing a deterministic response shape.  No "I found nothing"
  prose to parse.
- A single tool call covers all five categories in one pass, minimising latency
  and token cost.
- Fail-closed: if the response contains no matching `ToolUseBlock`, the service
  raises `ExtractorPassError` rather than silently emitting empty proposals.

### Consequences

- `parse_tool_input()` in `caller.py` scans content blocks for a `ToolUseBlock`
  whose `.name` matches `EXTRACT_TOOL_NAME` and returns `.input` as a dict.
- Responses that contain only `TextBlock` (model ignores tool_choice) raise
  `ExtractorPassError`.
- The `ExtractorModelCaller` protocol and `AnthropicExtractorCaller` class
  mirror the `WriterModelCaller` pattern for injection and testability.

---

## Decision 2 — EVENT Added to ProposalType

### Context

The Events Ledger (`sb_events`) is part of the Story Bible.  The Extractor must
be able to propose new events as part of its extraction pass.  The existing four
`ProposalType` values (`LOCKED_FACT`, `SOFT_FACT`, `TRANSIENT_STATE`,
`UNRESOLVED_THREAD`) do not cover append-only ledger entries.

Options:

1. **Add `ProposalType.EVENT`** — a dedicated routing value; `ratify_update()`
   extended to create the `SBEventORM` row on ratification.
2. **Reuse `TRANSIENT_STATE`** — events encoded as transient-state proposals with
   `target_entity_type="event"`.  Service detects and routes accordingly.

### Decision

**Option 1: `ProposalType.EVENT` added to `models/enums.py`.**

`StoryBibleService.ratify_update()` extended with an `EVENT` branch that creates
an `SBEventORM` row and marks the proposal RATIFIED.  Events auto-commit (no
`confirmed=True` required).

### Rationale

- Events are a first-class Story Bible entity type; treating them as a subtype
  of `TRANSIENT_STATE` creates a leaky abstraction and forces the service to
  inspect `proposed_value` internals to determine routing.
- An explicit `ProposalType.EVENT` keeps routing logic in the enum discriminant,
  not in `proposed_value` interpretation.
- Events are always auto-committed (the Events Ledger is append-only; even
  `character_death` events are recorded immediately).  A dedicated enum value
  makes this policy explicit in code rather than implicit in a convention.

### Consequences

- `ProposalType.EVENT` is a new wire value (`"event"`) in the SQLite
  `sb_provisional_staging.proposal_type` column.  Rows from Issues 1–9 will
  not have this value; the column has no CHECK constraint limiting values so
  existing rows are unaffected.
- `ratify_update()` handles the new branch before the `else` clause that covers
  `SOFT_FACT` / `TRANSIENT_STATE`.
- Tests verify that event ratification creates a row in `sb_events`.

---

## Decision 3 — Cast-Name Resolution via AssembledContext

### Context

The Extractor LLM returns character names (e.g. `"Aldric"`) not UUIDs.  To
apply soft-fact and transient-state updates to live dynamic fields, the service
must resolve names to `cast_id` UUIDs.

Options:

1. **Use `AssembledContext.stable_prefix.story_bible_context.cast`** — the cast
   tuple is already in memory from the Context Builder pass; no extra DB query.
2. **Query the DB by name** — add a `find_cast_by_name()` method to
   `StoryBibleService` and query at extraction time.

### Decision

**Option 1: resolve character names from `AssembledContext` at extraction time.**

`_build_cast_name_map()` in `service.py` builds a `dict[str, UUID]` keyed on
lowercase character name from `built_context.stable_prefix.story_bible_context.cast`.

### Rationale

- The `AssembledContext` is already in memory; the cast is the authoritative
  snapshot used by the Writer.  No extra DB query for what is already available.
- Case-insensitive matching (`name.lower()`) tolerates LLM capitalisation drift.
- If the name does not resolve, the proposal is still staged and ratified; only
  the dynamic-field application is skipped (not raised).  The RATIFIED proposal
  remains in the staging table for future review.

### Consequences

- `proposed_value` for cast-update proposals stores both `character_name` (for
  human traceability) and `entity_id` (resolved UUID, or `None` if not found).
- If a character is added to the Story Bible after context assembly (by a
  previous Extractor pass in the same session), the name map will not contain
  the new entry.  This is acceptable in Issue 10 standalone; pipeline
  orchestration (Issue 12) will manage pass ordering.
- `target_entity_id` on the proposal is `None` for unresolvable names; the
  dynamic-field update is skipped without error.

---

## Decision 4 — Cross-Pass Cache Reuse: Deferred to Issue 12

### Context

The CRD requires that the five pipeline passes share the same stable-prefix
cache entry.  The Extractor uses a different system prompt than the Writer
(extractor.md vs. mode prompt), which means the two passes produce different
Anthropic cache keys.

### Decision

**Defer full cross-pass cache sharing to Issue 12 (pipeline orchestration).**

The Issue 10 Extractor renders the stable-prefix user-message blocks in
byte-for-byte identical order to the Writer's `PromptRenderer`, placing the
cache breakpoint on the same (last) stable-prefix block.  The system-prompt
block differs, which busts cross-pass sharing under the Anthropic caching model
(cache key includes system).

### Rationale

- Issue 12 owns pipeline orchestration and is the correct place to evaluate
  whether all five passes can share a single system-prompt tier or whether the
  stable-prefix is cached only within a single pass's lifetime.
- The Issue 10 Extractor produces stable within-pass caching (second call with
  the same Story Bible hits the same cache).  The tradeoff is accepted and
  documented.
- Full cross-pass system-prompt unification would require either (a) a shared
  system prompt across all passes (changing the Writer's behaviour) or (b) a
  provider feature that caches only the user-message tier independently of the
  system tier.  Neither is decided here.

### Consequences

- Pass-forward text from the Extractor adds ~2,000–2,500 uncached tokens per
  turn to subsequent passes, consistent with the CRD cost-model estimate.
- Issue 12 must revisit system-prompt sharing and decide whether a unified
  pass-agnostic system prompt is feasible.  This is noted as a Known Unknown
  that Issue 12 must address.

---

## Decision 5 — Extractor Does Not Commit to DB; Session Managed by Service

### Context

The Writer service calls `session.commit()` after persisting the Turn.  The
Extractor makes multiple staging and ratification writes.

### Decision

**`ExtractorService.extract()` calls `session.commit()` once at the end of the
pass, after all staging and ratification writes are complete.**

### Rationale

- A single commit at the end is atomic: either all proposals stage-and-ratify
  together or none do.  This prevents partial state (ratified proposals without
  corresponding staging rows) from reaching the DB on error.
- Mirrors the Writer's single-commit pattern for consistency.
- The pipeline (Issue 12) may choose to manage session lifecycle across all
  five passes; Issue 10 commits its own pass following the Issue 9 precedent.

### Consequences

- If `extract()` raises `ExtractorPassError` after some staging writes but
  before commit, the session is left dirty.  The caller is responsible for
  rollback.  Issue 12 must handle this in pipeline error recovery.
- All staging and ratification writes are flushed (but not committed) during the
  pass; ORM object state is consistent within the session before commit.
