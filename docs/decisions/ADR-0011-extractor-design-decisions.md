# ADR-0011 — Extractor Pass Design Decisions (CRD Issue 10)

**Status:** Accepted
**Date:** 2026-04-25
**Issue:** CRD Issue 10 — Extractor Classification Policy
**Scope:** Tool-use output schema; proposal model; transaction ownership;
  natural-key resolution; EventKind taxonomy; writable-field allowlists;
  events bypass staging; cross-pass cache reuse

---

## Decision 1 — Anthropic Tool Use with Discriminated Union Schema

### Context

The Extractor pass must produce structured, typed proposal output.  Options:

1. **Tool use with discriminated union** — model calls `propose_canon_updates`
   once with a `proposals` array; each element is tagged by `kind`.
2. **Tool use with flat parallel arrays** — separate arrays per category
   (`locked_facts`, `soft_facts`, etc.).
3. **Prose JSON** — model returns a JSON blob in text; service parses it.

### Decision

**Option 1: `propose_canon_updates` with a `proposals: [{oneOf discriminated-union}]`
array, forced via `tool_choice={"type": "tool", "name": "propose_canon_updates"}`.**

The `EXTRACT_TOOL_SPEC` in `pipeline/extractor/caller.py` defines a single
`proposals` array whose items are a `oneOf` discriminated union keyed on `kind`:
`locked_fact`, `soft_fact`, `transient_state`, `unresolved_thread`, `event`.

### Rationale

- A single array is easier to extend (add a new `kind` variant without touching
  the schema shape).
- The discriminated union makes kind membership explicit at the schema level —
  no implicit inference from which array a proposal appears in.
- Tool use eliminates fragile JSON-in-prose parsing.
- Fail-closed: if the response contains no matching `ToolUseBlock`, the service
  raises `ExtractorPassError`.

### Consequences

- `parse_tool_input()` in `caller.py` extracts the tool-use block.
- `ExtractorProposalSet.model_validate(tool_input)` validates the full proposal
  list using the Pydantic discriminated union in `models/extractor.py`.
- The flat-array design (from prior Issue 10 iteration) is retired; any existing
  data was never committed to production.

---

## Decision 2 — EventProposal Bypasses Staging; ProposalType.EVENT Removed

### Context

Events are append-only ledger entries.  The prior design staged events as
`ProposalType.EVENT` rows in `sb_provisional_staging`, then ratified them.
Issue 10 as posted requires events to go directly to `add_event` without a
staging row.

### Decision

**Events bypass the provisional staging table entirely.**

`route_extractor_proposals()` calls `add_event()` directly for `EventProposal`
instances.  No `SBProvisionalStagingORM` row is created.  `ProposalType.EVENT`
is removed from the `ProposalType` enum.

### Rationale

- Events are always auto-committed (the Events Ledger is append-only).
- A staging row adds latency and a join without providing a rollback path that
  matters for append-only data.
- Removing `ProposalType.EVENT` keeps the enum truthful: the four remaining
  values all have provisional staging rows; events do not.

### Consequences

- `ExtractorRoutingSummary.event_ids` carries the `event_id` UUIDs of the
  `sb_events` rows, not proposal IDs.
- Tests verify that no staging row exists after an event proposal (bypass test).
- `ratify_update()` no longer handles `ProposalType.EVENT`.

---

## Decision 3 — Fail-Loud Natural-Key Resolution

### Context

The Extractor LLM returns character names and relationship keys, not UUIDs.
The prior design silently skipped field updates when a name was unresolvable.
Issue 10 as posted requires the entire routing transaction to fail on any
unresolvable natural key.

### Decision

**Resolution failure raises `EntityNotFoundError` and aborts the transaction.**

`StoryBibleService.find_character_by_name()` raises `EntityNotFoundError` if no
active cast entry matches the name (case-insensitive).  `_parse_relationship_natural_key()`
raises `ValueError` on bad delimiter format.  Both propagate through
`route_extractor_proposals()` and are caught in `ExtractorService.extract()` as
`ExtractorPassError`, leaving no DB state committed.

### Rationale

- Strict fail-loud matches the posted spec acceptance criteria.
- Silent skip could leave partial state (some proposals applied, others not)
  within the same turn — harder to reason about and audit.
- If strictness proves operationally undesirable, it can be relaxed in a later
  issue.  Starting strict is safer than starting permissive.

### Consequences

- The operator-facing error message includes the unresolvable name.
- `EntityNotFoundError` and `ValueError` are caught in `ExtractorService.extract()`
  and re-raised as `ExtractorPassError`.
- No partial DB state is committed when routing fails.

---

## Decision 4 — TargetDomain + Writable-Field Allowlists

### Context

The Extractor may target three domains: CHARACTER, RELATIONSHIP, WORLD.  Each
domain has a distinct natural-key convention and a distinct set of fields that
may be updated.

### Decision

**`TargetDomain` enum (CHARACTER, WORLD, RELATIONSHIP) and
`StoryBibleService.get_writable_fields(target_domain)` are the single sources of truth.**

- CHARACTER: `_CAST_DYNAMIC_FIELDS` = `{current_location, current_status, is_alive, notes}`
- RELATIONSHIP: `{current_status_description}`
- WORLD: `frozenset()` — not supported in v1; always fails field validation.

### Rationale

- A method on `StoryBibleService` owns the allowlist so the routing logic
  (`route_extractor_proposals`) does not duplicate policy knowledge.
- WORLD is a `frozenset()` (always-fail) rather than a separate code branch,
  so adding v1 world-state fields later only requires updating the method.

### Consequences

- Any proposal targeting `WORLD` domain raises `ValueError` (no writable fields)
  and aborts the transaction.
- The relationship allowlist is narrow (one field) to match what the schema and
  ORM currently support.

---

## Decision 5 — Relationship Natural-Key Format

### Context

Relationships are directional (subject → object).  The Extractor must identify
which relationship to update using character names.

### Decision

**Natural key format: `"<Subject> -> <Object>"` — exactly one ` -> ` delimiter
(space, dash, greater-than, space).**

`_parse_relationship_natural_key()` splits on `" -> "` and requires exactly two
parts.  Zero or more than one delimiter raises `ValueError`, which aborts the
transaction via the fail-loud resolution contract.

### Rationale

- A four-character fixed delimiter is unambiguous for any character name that
  does not itself contain ` -> `.
- Splitting on a fixed string (not a regex) is simple and readable.
- The format is documented in `extractor.md` so the LLM prompt mirrors it.

### Consequences

- Character names containing ` -> ` would produce a parse error; this is
  acceptable since no canon character names include that sequence.

---

## Decision 6 — EventKind Taxonomy Added

### Context

Events in the Events Ledger lacked a functional classification beyond
`significance`.  Downstream passes (summarisation, retrieval filtering) need a
machine-readable classification of what *kind* of event occurred.

### Decision

**`EventKind` enum added to `models/enums.py` with eleven values:**
LOCATION_CHANGE, INVENTORY_GAIN, INVENTORY_LOSS, NPC_INTRODUCTION,
STATUS_CHANGE, RELATIONSHIP_CHANGE, SCENE_TRANSITION, PLOT_REVEAL,
OATH_OR_PROMISE, DEATH, ROUTINE.

`event_kind` is a required field on the `Event` Pydantic model and a non-nullable
column (`server_default="routine"`) on `sb_events` (migration 0008).

### Rationale

- `significance` is a policy-tier field (for the tiered inclusion policy).
  `event_kind` is a functional-type field (for filtering, summarisation, display).
  The two are orthogonal; collapsing them into one field would create a
  mixed-semantics column.
- Making `event_kind` required on the model ensures new events are always
  classified; `server_default="routine"` backfills pre-Issue-10 rows safely.

### Consequences

- All callers that construct `Event` must supply `event_kind`.
- Test fixtures (`make_event`, context-builder tests) updated to include `event_kind`.
- Migration 0008 must run before the application processes any turn.

---

## Decision 7 — Transaction Ownership: route_extractor_proposals Commits

### Context

The Writer service calls `session.commit()` after persisting the Turn.  The
Extractor makes multiple staging and direct canon writes per turn.

### Decision

**`StoryBibleService.route_extractor_proposals()` calls `self._session.commit()`
once at the end of the pass.  `ExtractorService.extract()` does NOT touch the
session.**

### Rationale

- A single commit at the end is atomic: all proposals stage-and-apply together
  or none do.
- Removes session management from `ExtractorService`, which is a pipeline-layer
  concern, not a service-layer concern.
- Mirrors the Writer's single-commit pattern for consistency.

### Consequences

- If `route_extractor_proposals()` raises before commit, the session is dirty.
  The caller (`ExtractorService.extract()`) is responsible for rollback.
- Issue 12 (pipeline orchestration) must handle session lifecycle across all
  five passes and decide whether to use a single session or per-pass sessions.

---

## Decision 8 — Cross-Pass Cache Reuse: Deferred to Issue 12

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
  whether all five passes can share a single system-prompt tier.
- The Issue 10 Extractor produces stable within-pass caching.

### Consequences

- Issue 12 must revisit system-prompt sharing.  This is a Known Unknown that
  Issue 12 must address.
