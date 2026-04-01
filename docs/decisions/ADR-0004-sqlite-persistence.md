# ADR-0004 — SQLite Persistence Schema Decisions (Issue 3)

**Date:** 2026-03-31
**Status:** Accepted

---

## Context

Issue 3 introduces SQLite persistence (via SQLAlchemy 2.0 + Alembic) for all
core Pydantic models defined in Issues 2 and 2a.  Several schema decisions
required explicit choices.

---

## Decisions

### 1. FK cascade policy — CASCADE DELETE

**Decision:** CASCADE DELETE for all parent → child FK relationships
(Story → Arc → Chapter → Node; Story → WorldState; Story → CharacterState;
Story → session states; Story → RpgCharacterSheetBase → Dnd5eCharacterSheet;
Node → Turn uses SET NULL because Turn.node_id is nullable).

**Rationale:** Story data is session-scoped; a deleted story has no meaningful
orphan children.  CASCADE DELETE simplifies deletion semantics — callers only
need to delete the parent row.  RESTRICT was considered but would require every
deletion call site to explicitly delete child rows in dependency order —
unnecessary complexity for v1.

---

### 2. Static/dynamic partition storage — single table with column prefixes

**Decision:** Store WorldState and CharacterState partition columns on the same
table, using `static_` and `dynamic_` column name prefixes.

**Rationale:** Separate tables were considered but a single-table approach
avoids joins and keeps ORM mapping simpler.  The partition boundary is enforced
by the CRUD service's separate update paths (`update_world_state_static` /
`update_world_state_dynamic`) rather than schema-level table isolation.  This
matches the spec requirement for explicit typed columns (no JSON blobs) while
keeping the schema flat.

---

### 3. Node.mode_metadata — JSON column with Pydantic model_dump/model_validate

**Decision:** `mode_metadata` is stored as a JSON column.  Serialisation uses
`model.model_dump()` and deserialisation uses the concrete class's
`model_validate()` dispatched on the `mode` discriminator field.

**Rationale:** This is the one approved JSON-blob location per Issue 3 spec.
The discriminated union (rpg / branching / writing) maps naturally to a JSON
envelope with a `mode` key.  Using Pydantic's own serialisation/deserialisation
gives type-validated round-trips without a custom codec.

---

### 4. UUID storage — TEXT(36) strings

**Decision:** UUIDs are stored as `TEXT(36)` strings in SQLite (using
`sa.String(36)`).  The CRUD layer converts between `UUID` objects and strings
at the boundary.

**Rationale:** SQLite has no native UUID column type.  `sa.Uuid` with
`native_uuid=False` was considered but `sa.String(36)` with explicit
`str(uuid)` / `UUID(str)` conversions is simpler and avoids SQLAlchemy type
coercion surprises.

---

### 5. Session state one-active-row-per-story — UniqueConstraint

**Decision:** Each mode-specific session state table (`rpg_session_states`,
`branching_session_states`, `writing_session_states`) has a
`UniqueConstraint("story_id")`.

**Rationale:** v1 supports one active session per story per mode.  Enforcing
this at the database level prevents duplicate rows from application bugs and
makes the constraint explicit in the schema.

---

### 6. arc_ids / chapter_ids / node_ids — not stored, derived from relations

**Decision:** The `arc_ids`, `chapter_ids`, and `node_ids` list fields on
Story, Arc, and Chapter Pydantic models are **not** stored as JSON columns.
They are populated by the CRUD read functions via SQLAlchemy relationship
traversal (`row.arcs`, `row.chapters`, `row.nodes`).

**Rationale:** These lists are fully derivable from the relational structure.
Storing them as JSON columns would create a redundant source of truth that
could diverge from the actual FK relationships.  Deriving them at read time
keeps the schema normalised.
