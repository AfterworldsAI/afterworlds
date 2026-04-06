# ADR-0006 — Story Bible Dynamic Field Versioning Mechanism

**Status:** Accepted
**Date:** 2026-04-06
**Issue:** 4 — Story Bible Schema and Service

---

## Context

The dynamic partition of the Story Bible contains fields that the Extractor updates
automatically during pipeline execution — for example, a character's current location,
current status, whether they are alive, and relationship states.

The architecture spec (Issue 4) requires:
> "Dynamic canon updates must preserve prior values in an append-only history table
> or an equally explicit version-history mechanism.  Replacing current values without
> retained history does not satisfy this requirement."

The chosen mechanism must be stated explicitly.

---

## Decision

**An append-only generic history table (`sb_dynamic_field_history`).**

Every call to `update_dynamic_field` on the service:
1. Records the prior value as a JSON-serialised string in `sb_dynamic_field_history`
   before writing the new value to the entity row.
2. Updates the field on the entity.

### Schema

```
sb_dynamic_field_history
  history_id      STRING(36) PK
  entity_type     STRING(64) NOT NULL   — "cast_entry" | "relationship_ledger"
  entity_id       STRING(36) NOT NULL   — PK of the affected entity
  field_name      STRING(64) NOT NULL   — the logical field name (e.g. "current_location")
  old_value       TEXT       NULLABLE   — JSON-serialised prior value
  changed_at      STRING(64) NOT NULL   — ISO-8601 timestamp
  source_turn_id  STRING(36) NULLABLE   — provenance (no FK constraint)
```

The table carries no FK to the entity tables it describes.  Entity IDs are stored as
plain strings.  This avoids cascading deletes and keeps the history table structurally
independent.

### Why generic rather than per-entity history tables

A per-entity approach (`cast_entry_history`, `relationship_history`, etc.) would
require a new table for each entity type and a migration every time a new dynamic
entity is introduced.  At Issue 4 scope, we have two dynamic entity types (cast
entries and relationship ledger).  Future issues may add more.

A single generic table:
- Requires one migration.
- Adds new entity types by updating the service layer, not the schema.
- Is queryable by `entity_type` + `entity_id` without schema coupling.

The cost is that the generic `old_value` column stores JSON-serialised strings rather
than typed columns.  This is acceptable because history records are read for
audit/review purposes, not for high-frequency canonical queries.

### Scope

Only the service's `update_dynamic_field` method writes history records.  Direct ORM
mutations outside the service bypass this mechanism.  All dynamic field updates in
the pipeline must go through the service.

History records are never soft-deleted or hard-deleted.  `soft_delete` on the service
does not mark history records as inactive.

---

## Consequences

- The Extractor (Issue 10) must use `update_dynamic_field` for all dynamic field
  updates rather than writing to the ORM directly.
- Prior values are recoverable for any dynamic field via
  `get_dynamic_field_history(entity_type, entity_id)`.
- The history table grows with every dynamic update.  This is expected and acceptable.
  Story Bible updates are low-frequency relative to prose generation.
- If a future issue requires per-field history tables for performance reasons (e.g.
  for bulk queries), that is a migration from this mechanism, not a contradiction of it.

---

## Alternatives Considered

**Per-entity history tables (e.g. `sb_cast_entry_history`).**
Considered.  More type-safe but requires a migration per entity type.  Rejected in
favour of the generic approach given Issue 4 scope and the low query frequency of
history reads.

**Version counter column on the entity row (optimistic locking).**
Considered.  Solves concurrency but does not preserve prior values.  Explicitly
rejected by the spec.

**Append-only entity rows (never update, only insert new rows with a `superseded_at`
column).**
Considered.  Requires every query to filter by `superseded_at IS NULL` and complicates
the `get_active_context_window` assembly.  The separate history table approach is
cleaner for the common case (read current state) while still preserving history.
