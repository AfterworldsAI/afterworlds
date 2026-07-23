# Quarantined Legacy SRD Artifact — CRD Issue 5c (#132), ADR-005c Owner Decision 1

This directory holds **inert historical evidence only**. Nothing in the running
system reads, ingests, selects, publishes, or regenerates from it. It is retained
solely to document the defect that CRD Issue 5c remediated.

## Artifact identity

- **File:** `srd_5_2_1_structured.legacy.json` (moved here from the former
  default ingestion location `data/srd/srd_5_2_1_structured.json`).
- **SHA-256:** `3d1e7de02a2d37f6a4aadec01d8854aec7fda6a7c7ec765ca1d3a942b9187e02`
- **Size:** 58,686 bytes
- **Former package identity (Issue 5b path):** name `D&D SRD 5.2.1`, version `5.2.1`.

## Why it is quarantined (not authoritative)

ADR-005c found CRD Issue 5b's full-corpus contract unmet: this artifact holds 54
sections / 50 entities against a 364-page authoritative PDF, and no code path or
test ever derived, checked, or reconciled it against the source. CRD Issue 5c's
concordance audit further confirmed content and locator defects consistent with
pre-5.2.1 (2014) material under a `5.2.1` tag — e.g. Cure Wounds `1d8` with an
undead/construct exclusion (SRD 5.2.1: `2d8`, no exclusion), and `page_ref`
values that match none of their actual PDF locations.

## Quarantine rule (Owner Decision 1)

This material is **never eligible** for publication, ingestion, package
selection, fallback, seed, migration input, or regeneration. It must remain
unreachable from every executable path — production code, scripts, CLI defaults,
seed operations, package manifests, test fixtures, and runtime lookups. The
zero-reachability rule is machine-checked by
`afterworlds.ingestion.corpus.quarantine.check_legacy_reachability` and covered
by the Issue 5c test suite (Acceptance #12).

Downstream consumers bind only to the new immutable corpus release produced by
the Issue 5c pipeline, which supersedes this artifact.
