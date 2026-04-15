# ADR-0007 — Rules Package: Entity-Targeting Override Patch Shape Deferral

**Status:** Accepted  
**Date:** 2026-04-09  
**Issue:** CRD Issue 5a (Rules Package Schema and Data Model)

## Context

The `RuleOverride` model supports two target types:

- **Chunk-targeting overrides** operate on `RuleChunk.content` (a plain text
  field).  The payload shape is `ChunkOverridePayload` — a typed Pydantic
  model with a single `content: str | None` field.  This shape is fully
  defined and enforced in this issue.

- **Entity-targeting overrides** operate on `MechanicalEntity.structured_data`,
  which varies by entity type (`SpellEntity`, `ConditionEntity`, `StatBlockEntity`,
  `ActionEntity`, `ItemEntity`).  A fully typed patch shape would require one
  patch schema per entity type, with field-level merge semantics.

In CRD Issue 5a, no downstream consumer (Context Builder, Adjudicator) yet
requires entity override patch application.  Defining the patch shapes now
would be speculative design with no validation feedback.

## Decision

Entity-targeting override structured patch shapes are **deferred** to the
issue that first requires them.

In this issue:

- Entity-targeting `RuleOverride` records are valid and persist correctly.
- The `override_payload` column stores `{"content": "<text>"}` as a plain
  string for entity targets — the same `ChunkOverridePayload` JSON shape.
- `AppliedEntity.override_ids_applied` records which overrides are active,
  but the service does **not** apply them to `structured_data`.
- `_apply_chunk_overrides` is a service-private method and is only called
  for chunk targets.

## Consequences

- Entity override storage and retrieval work today.  Only application is
  deferred.
- The issue that first needs entity override application must define concrete
  patch schemas (`SpellPatch`, `StatBlockPatch`, etc.) and update the service.
- The `ADR-0007` marker appears in the `RuleOverride` and `ChunkOverridePayload`
  docstrings as a breadcrumb to this decision.
- No breaking schema changes are required when the patch shapes are defined:
  `override_payload` is already `sa.Text` (free-form JSON string).
