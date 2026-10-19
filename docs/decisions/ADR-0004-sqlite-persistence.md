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

> **CRD Issue 22 lifecycle amendment (Owner-accepted 2026-10-17).** Authority:
> [CRD Issue 22 #206](https://github.com/AfterworldsAI/afterworlds/issues/206), the
> [accepted lifecycle ADR amendment contract, revision 1](https://github.com/AfterworldsAI/afterworlds/issues/206#issuecomment-6246562569)
> and the [field/store retention matrix, revision 1](https://github.com/AfterworldsAI/afterworlds/issues/206#issuecomment-6246563742);
> repository copies in `docs/architecture/crd-issue-22-governing/`.
>
> **Superseded portion:** none of Decision 1's ordinary FK choices. The amendment narrows only
> what FK cascade may prove for terminal erasure; the text above is the historical decision.
>
> **Inserted clause:** “For terminal Story/account erasure, FK cascade alone is insufficient.
> Inventory Story, Arc, Chapter, Node and Turn identities before detachment. Delete in-scope Turns
> including orphaned `node_id IS NULL` rows; verify no prose remains. Inspect other plain-string
> references and restrictive FKs. The deletion receipt is based on that durable inventory, not
> parent joins after removal.”
>
> **Preserved:** the normal FK choices remain; no blanket schema rewrite.
>
> **Common amendment clause:** see [Common CRD Issue 22 lifecycle amendment clause](#common-crd-issue-22-lifecycle-amendment-clause) below.

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

---

### 7. Remote deployment addendum (prerequisite #205, 2026-10-17)

Local SQLite remains the accepted **local** persistence decision; nothing above changes for a local
installation. Per the accepted lifecycle amendment contract (“Reconciliation beyond the lifecycle
ADRs”) and [Remote Identity and Storage Prerequisite #205](https://github.com/AfterworldsAI/afterworlds/issues/205),
a remote deployment must declare its authoritative stores, account isolation, durable lease/sidecar
behavior and worker topology, and prove its store/restore hooks. No database replacement or
multiworker architecture is mandated. The selected remote topology — one uvicorn worker process
holding an exclusive store lock, a remote content SQLite store, a separate control SQLite store for
identity, sessions, closure, deletion suppression and backup inventory, and embedded Chroma — is
recorded in [ADR-021](adr-021-remote-identity-and-storage.md). Remote use does not inherit
authority to upload device keys or migrate historical proof data.

---

### Common CRD Issue 22 lifecycle amendment clause

Recorded verbatim from the accepted lifecycle ADR amendment contract, revision 1:

> Ordinary operation retains this ADR's append-only, immutable, transactional, replay and provenance requirements. A verified, explicitly confirmed Story or account-wide terminal deletion, or an approved record's retention expiry, is a separately authorized lifecycle operation. It may remove only inventoried in-scope content or expired minimized records through the owning service and a reviewed migration/maintenance contract. The operation records trusted actor, subject/scope, confirmation and source revision, policy version, exact affected classes/counts, per-store progress, timestamps and verification in minimized append-safe receipts. It fences new work, preserves unrelated subjects, shared Rules Packages, current money/access reconstructability and perpetual BYOK rights, and prevents restore, replay, delayed jobs and reindex from resurrecting erased data. Existing database UPDATE/DELETE triggers are not simply disabled by an ad hoc administrator action; the reviewed lifecycle path must preserve ordinary immutability and have tests for its exceptional behavior. An operational receipt is not a retained copy of narrative, provider, RPG or credential payload. This exception neither resolves gameplay cancellation/expiration/rewind nor creates a refund, credit repair, payment event or new entitlement path. Backups and legal exceptions follow the accepted CRD Issue 22 matrix; final deletion cannot be claimed before verified backup disposition.

A service implementation that cannot meet an approved 7-day live or overall 30-day backup deletion
limit is an unmet prerequisite, not grounds for an implicit extension. This amendment records
authority only: CRD Issue 22 (#206) owns deletion fulfillment, and prerequisite #205 supplies the
ownership, fence and restore hooks.
