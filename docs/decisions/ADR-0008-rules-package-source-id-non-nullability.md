# ADR-0008 — Rules Package: source_id Non-Nullability on RuleChunk and MechanicalEntity

**Status:** Accepted  
**Date:** 2026-04-09  
**Issue:** CRD Issue 5a (Rules Package Schema and Data Model)

## Context

`RuleChunk` and `MechanicalEntity` both carry a `source_id` field that
references the `RuleSource` (source document) they were ingested from.

The question was whether `source_id` should be nullable — permitting
"orphaned" chunks or entities that are not associated with any named
source document.

## Decision

`source_id` is **non-nullable** on both `rp_chunks` and `rp_mechanical_entities`.

- Every chunk and every mechanical entity must belong to a named `RuleSource`
  record within its package.
- There is no legitimate use case for orphaned records in a d20 rules package:
  every piece of rule text or structured entity comes from an identifiable
  source document.
- Traceability (knowing which book, supplement, or adventure a rule comes from)
  is a first-class requirement of the Rules Package subsystem.

## Consequences

- **Ingestion (CRD Issue 5b):** The ingestion pipeline must create or identify
  a `RuleSource` record before inserting any `RuleChunk` or `MechanicalEntity`.
  If a source document is unknown at ingestion time, a default or placeholder
  `RuleSource` record must be created rather than inserting with a null
  `source_id`.
- **Migration:** The `rp_chunks.source_id` and `rp_mechanical_entities.source_id`
  columns carry `NOT NULL` constraints enforced at the database level.  Any
  bulk-load path that omits `source_id` will fail at insert time, which is the
  intended behaviour.
- **Testing:** The schema separation invariant test (`test_schema_separation_invariant.py`)
  does not need to verify non-nullability separately; it is verified directly
  in `test_rules_package.py` (`TestSourceProvenance`).
- **No nullable relaxation permitted** without a superseding ADR explaining
  the edge case that cannot be handled by a placeholder source record.
