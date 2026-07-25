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

## Remediation round 3 — bind first-party transform code into the release identity

Codex round 3 (P1, `bundle.py:40`): `transform_config_payload()` covered only the
extractor configuration and the frozen policy. A first-party transform-code
change with no PDF / extractor-version / policy change (e.g. a `ledger`
segmentation fix or a `transform` chunk-generation change) kept the same
`transform_config_hash` → same `package_uuid` / `release_version`, so
`finalize_release` could take the existing-release *reuse* path under an identity
minted by *different code*. The evidence report likewise labelled only
`ledger.extraction_config` as the transform identity.

**Root correction (honest-by-construction, no manual bump).** New module
`transform_identity.py` derives a deterministic first-party transform identity:
a stable tool label plus a canonical source manifest over the audited modules —
each entry a repo-relative path + SHA-256 of the file's newline-normalized
source, sorted by path — and an aggregate `transform_source_hash` that is a pure
function of those bytes. `transform_config_payload` now embeds this identity
alongside the extractor config and frozen policy, so the transform hash (hence
`package_uuid` and `release_version`) moves automatically on any covered-source
change. The Component B invocation (`build_candidate` entrypoint + a0–b steps,
deterministic) and the "no intermediate representation committed" flag are
recorded. The tool version label is descriptive only; change detection is the
source hash, so there is no manually-remembered constant that can silently
bypass it. Newlines are normalized before hashing (matching the pipeline's `\n`
canonical discipline; `.gitattributes` already pins `*.py` to `eol=lf`) so a
CRLF checkout cannot perturb the identity; a missing audited module fails closed
(`TransformSourceMissingError`).

**Gate (`gate.py` condition 2).** No longer reconstructs the *old partial*
identity from `ledger.extraction_config` + the current policy. It now validates
the **complete recorded** transform configuration: rejects a config with no
first-party source manifest (the pre-fix payload), checks the recorded
`transform_config_hash` equals `hash_obj(rel.transform_config)` (recorded-config
tamper), and ties the recorded extractor config / policy to the reconstructed
artifacts. The gate stays a pure function of the artifacts — it does not re-read
the live source tree; the "code change → new identity" protection lives entirely
at `build_candidate` (manifest → transform hash → `package_uuid` → reuse-lookup
miss → fresh draft), with the gate proving the recorded hash was honestly
derived from a complete recorded config.

**Evidence report (`report.py`).** `transform_identity` now records the complete
Component B identity — extractor config + source manifest/hash + deterministic
invocation + IR-committed flag — not just `ledger.extraction_config`.
`build_report` takes the transform-config payload to do so.

### Manifest audit dispositions

Included (can affect the candidate corpus or a canonical identity in steps a0–b):

| Module | Reason |
|---|---|
| `pdf_source` | extraction (a1) |
| `ledger` | leaf/container segmentation (a1) |
| `transform` | canonical corpus generation (a2) |
| `reconcile` | policy application / dispositions / projections (a3) |
| `policy` | frozen policy code + `normalize`/`exclusion_reason_for` (a0, affects a3) |
| `bundle` | canonical member/reconciliation payloads, bundle root, identity derivation (b) |
| `hashing` | canonical serialization + `content_id` underlying every identity |
| `models` | dataclasses/enums whose values enter canonical payloads |
| `pipeline` | a0–b orchestration / `build_candidate` ordering |
| `transform_identity` | defines the manifest itself (self-covering, tamper-resistant) |

Excluded (cannot change the candidate corpus bytes or an a0–b canonical identity;
including them would spuriously churn the identity and is the "unrelated
runtime/publication code" the finding warns against):

| Module | Reason |
|---|---|
| `concordance` | verification only (E/J) — verifies, never generates |
| `report` | post-persistence evidence (e) |
| `gate` | publication verification (g) |
| `persistence` | persistence/reconstruction (c/d) |
| `vector_publication` | informational vector write/read-back (c) |
| `quarantine` | legacy zero-reachability check (L) |

### Round 3 regression coverage

- **Byte-sensitivity / no-silent-bypass** (`test_transform_identity.py`):
  aggregate order-independence + byte-change sensitivity; manifest covers exactly
  the audited module set; each recorded sha256 equals the real file digest (not a
  constant); flipping one byte in **each** covered module (parametrized) moves
  `transform_source_hash`; a transform-code change moves
  `transform_config_hash`, `package_uuid`, and `release_version`; identical
  sources deterministic; missing module fails closed; Component B invocation / IR
  flag recorded.
- **Gate** (`test_gate.py`): `test_gate_fails_on_incomplete_transform_config`
  (pre-fix payload with no manifest rejected),
  `test_gate_fails_on_tampered_transform_config` (recorded-config tamper vs.
  stored hash). The existing `transform_config_hash="0"*64` tamper
  (`test_final_gate_failure_does_not_publish_partial_content`) remains green.
- Byte-for-byte determinism preserved: the full-corpus
  `test_clean_regeneration_is_byte_for_byte_deterministic` still passes (the
  manifest is stable across a clean rebuild of the same sources).

### Sibling-audit disposition (release-identity seam, recurring)

Same seam family as DF3 (release-key identity). DF3 fixed the *version-vs-UUID*
derivation asymmetry; round 3 fixes the *completeness of the transform hash's
inputs* (first-party code was absent). Both `patched` at the root in
`bundle.derive_*` / `transform_config_payload`. Remaining release-identity inputs
audited: authoritative source (PDF hash, bound), extractor config (bound), frozen
policy (bound), first-party transform code (now bound). No Owner Decision, Known
Unknown, or later-issue (5d/2b/15c/15b/19b) scope was entered; no MechanicalEntity
generated.

## Remediation round 4 — cross-store compensation on all finalize exits

Codex round 4 (P2, `persistence.py:922`, AGENTS.md transaction/rollback): in the
fresh-publish path, `cleanup_vector_collection` ran only when `run_gate()`
*returned* a failed result. Any exception in the intervening read-back /
reconstruction / digest / report / gate setup, or during `session.commit()`,
bypassed cleanup — SQL rolled back with the session lifecycle, but the
unpublished `rules_corpus_{pkg}` collection stayed queryable through the
diagnostic/admin surface with no published SQL release (cross-store leak).

**Root correction.** The fresh-publish vector attempt through the successful SQL
commit is now **one exception-safe compensation boundary** in `finalize_release`.
An `cleanup_armed` flag is set **before** `reindex_and_verify` (which can write
the collection and then raise during read-back before returning) and cleared
**only after** `session.commit()` returns. Every unsuccessful exit compensates:

- *Failed gate* → `session.rollback()`, disarm, `cleanup_vector_collection`,
  return the ordinary `FinalizeResult(published=False, …, gate=gate)`. Disarming
  before this cleanup means a cleanup failure here re-raises via the `except`
  (no clean failed result is returned while a collection leaked).
- *Ordinary exception* (read-back / reconstruction / digest / report / gate) →
  `except`: `session.rollback()`, armed `cleanup_vector_collection`, `raise` — the
  original exception propagates; a cleanup failure is not swallowed (chains onto
  it).
- *Commit exception* → armed is still set (disarm is after commit) → same
  `except` compensation.
- *Success* → disarm only after `commit()` returns; no cleanup.

The mis-named `_finalize_vector_or_rollback` wrapper (it never owned rollback) was
removed; the boundary calls `reindex_and_verify` directly. The reuse path is
untouched: it verifies only (`verify_only`) and never deletes an existing
published collection.

### Round 4 regression coverage (`test_persistence_quarantine.py`, fault injection)

- `test_exception_during_reconstruction_rolls_back_and_removes_collection` —
  `build_report` patched to raise *after* the reindex wrote N>0 docs (so the
  collection provably existed); asserts SQL rows absent + read-back count 0 +
  exception propagated.
- `test_exception_from_run_gate_rolls_back_and_removes_collection` — `run_gate`
  patched to raise; same compensation.
- `test_commit_exception_rolls_back_and_removes_collection` — `session.commit`
  patched to raise (only the publish commits in this path; `reindex_from_sql` /
  legacy check do not); same compensation.
- `test_reuse_verification_exception_does_not_delete_published_collection` —
  after a successful fresh publish (collection retained, count > 0), `verify_only`
  patched to raise on the reuse attempt; asserts the exception propagates while
  the published collection and SQL row both survive.
- The normal *failed-gate* case (ordinary `FinalizeResult`, no exception; no SQL
  rows, no vectors) remains proven by the existing
  `test_final_gate_failure_does_not_publish_partial_content` — not duplicated.

Sibling-audit: cross-store compensation family (SQL transaction vs. non-
transactional Chroma write). The reuse path was inspected and correctly left
without fresh-attempt cleanup (verification only). `patched` at the root in
`finalize_release`; no scope beyond Issue 5c; Issue 18's collection
schema/ID/metadata/writer unchanged.

## Remediation round 5 — reindex self-cleans a partial destructive rebuild

Codex round 5 (P2, `rules_corpus_service.py`, ADR-018 D11): the bounded batched
upsert (added round 3) made `reindex_from_sql` destructive-but-not-atomic. After
the old collection is wiped, a later-batch `collection.upsert()` failure left the
earlier successful batches queryable — a partial `rules_corpus_{pkg}` collection
contradicting SQLite ground truth. `finalize_release` compensated only for its
own call path; **direct** reindex callers got the exception with partial content
retained.

**Service-level cleanup invariant.** `reindex_from_sql` is now exception-safe at
its own public boundary. The initial wipe stays **outside** the compensation
scope: an operational wipe failure propagates without touching the old
collection (preserves PR #119 round 7; the old collection is never deleted when
the wipe itself failed). Once the wipe succeeds the old collection is gone, so
`cleanup_armed` is set and every collection this attempt creates or partially
populates is its responsibility — a create / row-transform / embedding / any-
batch failure removes the attempt's collection (`delete_collection_ignoring_
absence`) and re-raises. Cleanup is disarmed **only** after every batch succeeds,
or after a legitimate zero-row rebuild completes with an empty collection. On a
**cleanup** failure the cleanup error surfaces as the propagating exception with
the originating failure preserved as `__context__` — nothing swallowed, never a
clean-failure claim while partial content may remain. ADR-018 D11 honored: still
in-place re-upsert, no temp/swap collection; no change to reuse path, vector
schema, deterministic IDs, metadata, or batch size. `finalize_release`'s outer
boundary is kept unchanged — now redundant for the reindex step but
absence-tolerant, so the double cleanup is a safe no-op (5c not weakened).

### Round 5 regression coverage (`test_rules_corpus_service.py`, fault injection)

- `test_later_batch_failure_removes_all_partial_documents` — `_MAX_UPSERT_BATCH`
  forced to 2 over 4 chunks (2 batches); a wrapper fails the 2nd upsert after the
  1st landed; asserts the exception propagates and the collection is **removed**
  (`get_collection` → `NotFoundError`, not merely `count == 0` — which could not
  distinguish removed from emptied).
- `test_first_batch_failure_removes_the_attempt_collection` — failure on the
  first upsert (after a successful wipe) still removes the newly created
  collection. Representative for **all** pre-first-batch failures (creation /
  transform / first upsert share the one `except`); variants not duplicated.
- `test_successful_multi_batch_rebuild_writes_exact_complete_set` — 5 chunks over
  3 batches writes exactly the complete SQL-backed id/document set.
- `test_cleanup_failure_is_surfaced_not_swallowed` — a later-batch upsert failure
  plus a failing compensating `delete_collection`; asserts the cleanup error
  propagates, the originating upsert error is chained (`__context__`), and the
  partial batch-1 content genuinely remains (`count == 2`) — i.e. a cleanup
  failure is surfaced, never reported as a clean failed rebuild.
- Existing `TestReindexPropagatesWipeFailure` (operational wipe failure leaves the
  prior collection untouched) preserved unchanged.

Sibling-audit: same destructive-rebuild compensation family as round 4's
finalize boundary, one layer down (the non-transactional Chroma writer itself).
`patched` at the root in `reindex_from_sql`; reuse path untouched; Issue 18
schema/ID/metadata/writer/batch-size unchanged; no scope beyond Issue 5c/18.

## Remediation round 6 — three settled families + one unrelated CI unblock

Codex round 6 (three P1s) plus the failed CI at head `4eaa8c9` (unrelated
frontend advisory). No schema migration.

**P1a — persisted reconciliation policy (`persistence._load_policy`).**
Reconstruction previously accepted `candidate.policy`/`FROZEN_POLICY` and never
read `ReconciliationPolicyORM`, so tampering the persisted policy row was
invisible to the digest/reuse gate. New `policy_from_payload` (in `policy.py`,
fails closed on malformed shape/unknown enum) + `_load_policy` reconstruct the
applied policy from the row and validate a closed cross-reference chain: payload
shape; payload-derived version/hash vs the row; row vs `rp_reconciliations`;
row vs `rp_corpus_releases`; reconstructed payload vs the policy embedded in the
stored transform config. Used in `recompute_persisted_digest` /
`verify_persisted_digest` / `reconstruct_payload` / `_reconstruct_artifacts` and
both finalize paths; the reuse path catches `PolicyReconstructionError` and
reports an ordinary failed result. Never substitutes a default/caller policy.
Tests: `test_load_policy_accepts_clean_release_positive_control` (round-trip +
digest verifies) and delete / version / hash / payload / rp_reconciliations /
rp_corpus_releases / transform-config cross-reference tamper each fail closed;
`test_reuse_fails_closed_on_deleted_policy_row`.

**P1b — vector configuration in the immutable identity
(`models.retrieval.rules_corpus_vector_identity`).** `embedding_model_id` changes
the required vector metadata + persisted digest but previously could not change
the package UUID/version, so a model-only reindex hit the verify-only reuse path
against a stale digest with no identity to mint a replacement. The vector
identity — the actual `embedding_model_id` plus the rules-corpus logical
schema/ID/metadata contract, *sampled from the real builders*
(`build_rules_corpus_chunk_id`/`rules_corpus_collection_name` with a placeholder
UUID + `RulesCorpusChunkMetadata` field set / schema_version) — is bound into
`transform_config_payload`, so it contributes to `transform_config_hash`, package
UUID, and release version. Resolved before `build_candidate`
(`retrieval_config`), recorded in the release + report, and the gate ties the
recorded `embedding_model_id` to the actual persisted vector state. Identity binds
contract **shape**; per-document values remain the digest's job. No sixth
top-level hash; no operational/runtime settings or embedding bytes bound; a
model change mints a new release (predecessor untouched). Bounded sibling: an
identity-bearing vector schema/ID/metadata change likewise moves the identity, so
it cannot fall into the "reuse identity, fail digest" dead end. Tests
(`test_vector_identity`): determinism; identity-inputs-only; model change moves
hash/UUID/version; coexisting release without collision.

**P1c — Chroma batch capability (`rules_corpus_service.reindex_from_sql`).**
Removed the hard-coded `_MAX_UPSERT_BATCH = 5000` (would fail on a backend whose
advertised max is lower). Batch size now derives from the actual client via
Chroma's supported `create_batches` helper (which slices by
`get_max_batch_size()`); an invalid/unusable capability (`<= 0`/non-int) fails
clearly rather than reverting to a fixed size. Deterministic in-order slices,
the round-5 partial-write cleanup boundary, zero-row behavior, and the outer 5c
compensation boundary are preserved; reuse path, schema, IDs, metadata unchanged.
Tests: fake client advertising max 2 produces valid multiple batches + the exact
complete set; a later dynamically-sized batch failure still receives the
partial-rebuild cleanup; invalid capability fails clearly.

**Unrelated CI unblock — brace-expansion advisory (GHSA-mh99-v99m-4gvg).** CI's
`npm audit --audit-level=high` failed on `brace-expansion <=5.0.7`; no frontend
source file is otherwise in the diff. npm flags every brace-expansion below
5.0.8, but 5.x is a CJS-named-export rewrite (`exports.expand`) that older
minimatch (3.1.5 under eslint 9, 5.1.9 under @redocly) call as
`require('brace-expansion')(...)`, so a blanket `5.0.8` override satisfies audit
but breaks lint (`expand is not a function`). Smallest verified correction: pin
`brace-expansion: 5.0.8` **and** consolidate the stale minimatch instances onto
`^10` (already present via the @typescript-eslint path, compatible with 5.x) —
keeping eslint 9 and openapi-typescript 7.13.0, avoiding the `npm audit fix
--force` ESLint-10 major / OpenAPI downgrade the task flagged. Verified: npm
audit (0), typecheck, lint, format:check, Vitest (45), api-types drift (none),
production build, Playwright e2e (7) all pass with zero application-code edits.
(The local package-lock prettier warning is a Windows CRLF artifact; committed
LF passes — CI already showed format:check green.)
