# PR #134 Remediation Log — CRD Issue 5c

Archive of detailed Codex/Claude review-remediation history for PR #134. This material was moved out of the PR body to keep that body focused on the implemented result, acceptance coverage, durable Architecture Notes, current boundaries, and final verification status.

---

## Remediation round 1 — persist-then-prove publication lifecycle

Codex round 1 found the lifecycle proved the *intended in-memory* corpus, not
the *actual persisted, runtime-visible* state. Split at the true persistence
boundary per Component K (persist → digest from actual persisted state →
evidence report → record hashes → final gate → publish):

- **`pipeline.build_candidate()`** (a0–b): returns `CandidateRelease` with no
  report/digest/release fields — structurally cannot claim persistence.
- **`persistence.finalize_release()`** (c–g): persists a non-visible `draft`,
  reconstructs strictly from the persisted rows, computes the digest from that
  reconstruction, runs a **live** legacy check against the session, generates +
  hashes the post-persistence report, runs the final gate against DB-grounded
  artifacts, and only on a pass flips **both** `RulesPackageORM` and
  `CorpusReleaseORM` to `published` and commits — else rolls back entirely.
- **`verify_chunk_runtime_membership()`**: fails closed on an orphan enabled
  `rp_chunks` row or a disabled projected chunk/source (cases the digest alone,
  scoped to the declared-projection set, would miss but runtime reads expose).
- CLI applies real Alembic migrations (not `create_all()`); migration
  0017/`CorpusReleaseORM` post-persistence hash fields made nullable; the
  five-hash publication requirement is unweakened.
- Idempotent reuse re-runs the **full** gate + `rp_packages` state check before
  accepting a no-op.

## Remediation round 2 — cross-store proof, provenance attestation, release key

Codex round 2 found three further gaps; all fixed at the root:

**DF1 — actual vector persistence + read-back (was `vector_write_ok=True`).**
Component K step c requires persisting into SQL **and required vector storage**.
`finalize_release` now, after the SQL draft persist, drives the existing Issue 18
`RulesCorpusService.reindex_from_sql` (canonical `rules_corpus_{pkg}` collection,
`build_rules_corpus_chunk_id`, `RulesCorpusChunkMetadata` — **no** second Chroma
schema/writer), then reads the collection back and verifies exact document IDs,
content, required metadata, count, and embedding-model consistency against SQL
ground truth (`vector_publication.py`). The persisted-corpus digest is now
computed over the reconstructed SQL state **plus the actual verified vector
logical state** — never a SQL-synthesized vector payload. The gate takes a
`PublicationEvidence` with **no defaults** (no caller can hardcode SQL/vector
success); a write failure, empty/missing/extra/stale document, or metadata/model
mismatch blocks publication and is reachable from the production path. A failed
gate rolls back SQL **and** drops the vector collection this attempt wrote, so no
partial content is runtime-visible in either store. Reuse re-verifies existing
vectors without rewriting and fails closed against a missing/stale collection.
A latent batch-size defect in the Issue 18 writer (single `upsert` of ~13.6k
chunks > Chroma's max batch) was fixed in place by batching the write — schema,
IDs, and metadata unchanged.

**DF2 — RuleChunk provenance attestation.** `_load_members` now binds the actual
persisted `source_document` / `source_locator_type` / `source_locator_value`
from `rp_chunks` (previously it synthesized the page from the ledger and ignored
these runtime-served fields), and they are bound into the persisted-corpus
digest. Tampering any cited locator field now fails `verify_persisted_digest`
and both the final and reuse gates. No change to the Issue 5a `RuleChunk` schema.

**DF3 — release-version identity.** `derive_release_version` now derives from
**both** the authoritative-source hash and the transform hash (consistent with
`derive_package_uuid`). A changed source with unchanged transform config now
yields both a new `package_uuid` and a new `release_version`, so it no longer
collides with the prior release on the `rp_packages (name, version, system)`
uniqueness constraint; identical inputs stay byte-identical.

## Sibling-audit note (defect family across both remediation rounds)

Defect family: proof computed from in-memory / caller-supplied /
partially-verified state instead of the actual persisted, runtime-visible
cross-store state. Inspected and corrected within Issue 5c, reusing Issue 18's
owned schema/service seams: SQL reconstruction (round 1), RuleChunk runtime
provenance (DF2), vector persistence/read-back (DF1, via the Issue 18 reindex
seam), and release-key identity (DF3). Dispositions: all `patched` at the root.
No work crossed into Issue 5d/2b/15c; no MechanicalEntity generated; the new
package UUID/version seam consumed by 5d/2b is stable.

## Round-specific regression coverage

Remediation-specific coverage retained here (removed from the PR-body
acceptance matrix as separate pseudo-criteria; folded into the numbered rows
there):

- **DF1 — vector persistence + read-back:** `test_vector_publication.py::*`,
  `test_reuse_rejects_missing_vector_collection`,
  `test_gate_fails_on_vector_verification_failure`,
  `test_final_gate_failure_does_not_publish_partial_content` (negative control:
  a failed final gate publishes no partial content in either store).
- **DF2 — RuleChunk provenance attestation:**
  `test_tamper_chunk_source_document_breaks_digest`,
  `test_tamper_chunk_locator_type_breaks_digest`,
  `test_tamper_chunk_locator_value_breaks_digest`.
- **DF3 — release-version identity:** `test_release_identity.py::*`.
- **Round 1 lifecycle:** `test_persist_round_trip_digest_matches`,
  `test_release_binds_five_top_level_hashes`,
  `test_repeated_finalize_is_idempotent_and_does_not_mutate`,
  `test_candidate_release_carries_no_persistence_claim`,
  `test_legacy_active_row_blocks_publication`.
