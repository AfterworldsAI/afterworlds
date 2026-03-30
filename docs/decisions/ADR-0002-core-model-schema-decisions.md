# ADR-0002 — Core Model Schema Decisions (Issue 2)

**Status:** Accepted
**Date:** 2026-03-30
**Issue:** 2 (GitHub Issue #20)

---

## Context

Issue 2 defines the backbone data objects the entire system depends on.
Several schema decisions required choices not explicitly covered by the CRD
or design documents.  This ADR records them for traceability.

---

## Decision 1 — Static / Dynamic Partition as Nested Sub-Models

**Decision:** WorldState and CharacterState use nested Pydantic sub-models
(`static: WorldStateStaticPartition`, `dynamic: WorldStateDynamicPartition`)
to represent the static / dynamic partition structurally.

**Alternatives considered:**
- Field-level metadata annotations (e.g., a custom `is_static` marker)
- A flat model with comments distinguishing static from dynamic fields

**Rationale:** Nested sub-models make the partition a type-system constraint,
not just documentation.  The Extractor update policy (Issue 4+) can dispatch
on the type of the sub-model.  Flat models with comments drift silently;
nested models enforce the boundary at instantiation.

---

## Decision 2 — BranchTree Uses `dict[str, BranchNode]` with String Keys

**Decision:** `BranchTree.nodes` is typed as `dict[str, BranchNode]`, using
`str(UUID)` as the map key rather than `UUID` directly.

**Rationale:** JSON object keys are always strings.  When this model is
serialized to SQLite (Issue 3) or transmitted over the API (Issue 18),
`dict[UUID, BranchNode]` would require a custom serializer at every boundary.
String keys are idiomatic for JSON-backed storage.  The UUID identity of each
node is preserved in the `BranchNode.node_id` field.

---

## Decision 3 — D&D 5e Ability Score Range: 1–30

**Decision:** `AbilityScores` validates each score in the range `[1, 30]`.

**Rationale:** The D&D 5e player cap is 20, but class features (Epic Boons),
artifacts, and Wish can push scores above 20.  The absolute system maximum
(used for some legendary creatures) is 30.  Capping at 20 would break
legitimate high-level play scenarios.  Capping at 30 covers the full D&D 5e
rules space while still preventing obviously invalid values.

This decision is scoped to D&D 5e.  Broader cross-system ability score
abstractions are deferred to Issue 5a/5b.

---

## Decision 4 — `Dnd5eCharacterSheet.skills` as `dict[str, int]`

**Decision:** Skills are represented as `dict[str, int]` (skill name →
computed modifier), not as a structured enum or fixed-field model.

**Rationale:** At Issue 2 scope, the character sheet must be typed and
non-blob.  A full D&D 5e `Dnd5eSkills` model with typed fields for all 18
skills would be appropriate but creates coupling between the schema and the
specific skill list — which belongs in the Rules Package (Issue 5a).
`dict[str, int]` is fully typed (no `Any`, no blob), captures the relevant
data, and defers the skill taxonomy to Issue 5a where it belongs.

---

## Decision 5 — `level` Field Capped at 20

**Decision:** `Dnd5eCharacterSheet.level` is validated `ge=1, le=20`.

**Rationale:** D&D 5e caps character level at 20.  This is a mechanical
rule, not an arbitrary constraint.  Epic Boons and similar features exist at
level 20+ in some editions but are not part of standard 5e.  This can be
relaxed in a future schema version if needed.

---

## Known Unknowns Not Touched

No items from `known_unknowns.md` were resolved by this issue.  All open
items remain as documented.
