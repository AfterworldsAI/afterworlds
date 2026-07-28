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

## Remediation round 7 — draft read-visibility + non-creating read paths

Codex round 7 (P1 + P2). The canonical `rules_corpus_<pkg>` collection is
populated in-place during a draft rebuild before SQL publication commits, and two
paths leaked that draft state / created external state on read.

**P1 — `diagnostic_query` publication-aware (`rules_corpus_service.py`).** It read
the canonical collection without checking SQL publication status, so a concurrent
diagnostic/admin query during a multi-batch draft rebuild could observe partial,
ungated vectors. `diagnostic_query` now requires a SQL `session` and returns no
results unless BOTH the `RulesPackageORM` row is `published` + enabled AND its
`CorpusReleaseORM` row is `published` (checked in `_is_published_and_enabled`
**before** any Chroma access). Missing / draft / disabled / inconsistent records
return nothing without touching Chroma. Draft visibility is controlled by
persisted SQL publication state, not Chroma — the canonical in-place reindex is
unchanged (ADR-018 D11: no staging/swap/rename; not a runtime-pass surface, D10).

**P2 — non-creating verify/diagnostic lookups (`vector_publication.py`,
`collections.py`).** `read_actual_vector_state` used the creating
`get_rules_corpus_collection`, so verify-only reuse of a published release whose
collection was missing *created* an empty canonical collection (new external
state after a failed verification). New `get_existing_rules_corpus_collection`
uses the non-creating `client.get_collection`; `read_actual_vector_state` and
`diagnostic_query` use it. Only `NotFoundError` is ordinary absence (→ empty /
no results); locked/corrupt/permission and other operational errors propagate; an
embedding-model mismatch remains an explicit verification failure that creates,
wipes, or rewrites nothing. `reindex_from_sql` (write/rebuild) keeps the creating
helper. Reuse is now fully non-mutating: a missing collection fails verification
while leaving Chroma exactly as it was.

Sibling-audit (recurrence-triggered, complete — settled implementation, not an
Owner Decision): write/rebuild paths legitimately create; verification and
diagnostic paths are existing-only; draft visibility is gated by persisted SQL
publication state. Dispositions: `patched` at the root in `diagnostic_query` /
`read_actual_vector_state` + the new `get_existing_rules_corpus_collection`. No
staging/swap architecture; both publication records checked; no `get_or_create`
on any read path; no operational-error swallowing; no reuse mutation. Issue 18
schema/ID/metadata/writer/batch unchanged; no scope beyond Issue 5c/18.

### Round 7 regression coverage

- `test_rules_corpus_service.py::TestDiagnosticQueryPublicationAware` — a committed
  draft package with real canonical vectors is invisible and Chroma is never
  opened (`get_existing_rules_corpus_collection` never called); each inconsistent
  publication state fails closed (package-draft / package-disabled / release-draft
  / release-missing, parametrized) + missing-records; published diagnostics
  succeed. The reindex round-trip tests now publish (`_publish_release`) and pass
  a session.
- `test_vector_publication.py` — `read_actual_vector_state` on a missing
  collection returns empty **and leaves the collection absent** (non-creating);
  a non-`NotFoundError` `get_collection` failure propagates. Existing
  reuse-missing-collection / mismatch fail-closed tests remain green.

## Remediation round 8 — release-scope the output chunk identity

Codex round 8 (P1). `build_corpus` derived `chunk_id = content_id("chunk",
leaf.leaf_id)` — package-independent. When a source / transform config /
transform-source manifest / embedding model changed while a leaf stayed
identical, the new immutable release received the predecessor's chunk ID; since
`rp_chunks.chunk_id` is a **global primary key**, full persistence of the second
release raised `IntegrityError`. The prior coexistence tests inserted only
`rp_packages`, so they never exercised the actual chunk rows.

**Root correction.** `build_corpus(ledger, package_uuid)` now derives
`chunk_id = content_id("chunk", package_uuid, leaf.leaf_id)`, scoping the output
chunk identity to the immutable release while leaving the source-side `leaf_id`
release-independent (it remains the provenance identity later work consumes).
`package_uuid` is computed before a2 (as today) and passed in explicitly — no
package-less default. Reconciliation regenerates projection IDs from the newly
scoped chunk IDs automatically (`projection_id = content_id("projection",
leaf_id, chunk_id, role)`). Byte-for-byte regeneration for identical inputs is
preserved (`package_uuid` is itself deterministic); `rp_chunks` schema and the
global-UUID PK are unchanged (no composite key); Issue 18's vector-ID format is
unchanged (`rules:{pkg}:chunk:{chunk_id}` was already package-scoped).

### Sibling-audit dispositions (release-identity family)

- **RuleChunk output `chunk_id`** — **patched** (now `content_id("chunk",
  package_uuid, leaf_id)`).
- **Rules-corpus vector ID + collection name** — **already package-scoped**:
  `build_rules_corpus_chunk_id` → `rules:{package_uuid}:chunk:{chunk_id}`,
  `rules_corpus_collection_name` → `rules_corpus_{package_uuid.hex}`
  (`models/retrieval.py`); no change.
- **RuleSource ID + Issue-5c ledger/container/projection persistence** —
  **already safely package-scoped**: `_persist_package_and_source` sets
  `source_id = pkg`; every `rp_*` corpus table is `package_uuid`-keyed
  (`persistence.py` / `orm/corpus.py`). The coexistence test proves this
  empirically — both releases persist fully with no `IntegrityError` on any table.
- **MechanicalEntity identity** — **out of scope** for Issue 5c; Issue 5d
  identity design is not pre-decided.

### Round 8 regression coverage

- `test_reconcile_policy.py` — same leaf + same package → same chunk ID; same leaf
  + different packages → different chunk IDs, with `leaf_id` (provenance)
  unchanged across releases.
- `test_persistence_quarantine.py::
  test_two_releases_coexist_fully_persisted_with_disjoint_chunks` — two releases
  differing only in the embedding model (identity-bearing) are **finalized
  fully** into one database; both `rp_chunks` sets are complete, equal-sized, and
  disjoint; projections reference their own release's chunk IDs and are disjoint;
  the predecessor stays published + enabled with its own version; both
  persisted-digests re-verify against their actual SQL + vector state. No
  `IntegrityError`.
- Determinism/reconstruction unchanged:
  `test_clean_regeneration_is_byte_for_byte_deterministic` and
  `test_reconstructed_payload_equals_in_memory` still pass (same inputs → same
  scoped chunk IDs → same bundle root / digest / reconstruction).
- The two package-only version-key tests were renamed + rescoped to state they
  prove only the `(name, version, system)` constraint, pointing at the
  full-persistence test for actual chunk coexistence (no coexistence claim from
  `rp_packages` alone).

## Remediation round 9 — compact canary-page fixtures (non-blocking test-perf)

Non-blocking improvement (test architecture; production contract unchanged).
`test_persistence_quarantine.py` was ~13m51s of a 24m25s CI pytest run: its 39
tests each re-persisted/re-reindexed the full 14,023-leaf / 13,658-chunk SRD into
fresh SQLite+Chroma even for policy/rollback/tamper/fault-injection cases whose
assertions do not depend on full-SRD cardinality.

**Fixture split.** New session-scoped `compact_candidate` / `compact_release`
(conftest) build a REAL, gate-passing release restricted to the six version-canary
pages (~250 chunks vs 13,658) via the production pipeline (`build_ledger` →
`build_corpus` → `reconcile` → `build_bundle`), binding the real
`PDF_SHA256`/extraction config so it passes the genuine finalize/gate/persist/
reindex path — **no mocks**. `test_persistence_quarantine.py` shadows
`candidate`/`release` with the compact fixtures for this module only; the fixture
chain is shadow-safe (`compact_candidate` → `full_candidate`, never the shadowed
`candidate` → no recursion). Fresh per-test SQLite/Chroma isolation is preserved;
the session-scoped fixtures are immutable candidate/release objects, not shared
databases (no state leakage; no test-order dependence). No production batching/
persistence/publication/digest behavior changed.

**Retained full-SRD integration guarantees.** Three tests request
`full_candidate`/`full_release` explicitly and prove the complete corpus can be
persisted, reconstructed, digest-verified, and vector-indexed
(`test_persist_round_trip_digest_matches`); gated, published, and reused
(`test_repeated_finalize_is_idempotent_and_does_not_mutate`); and retrieved
through `RulesPackageService` including a GENERAL-subsystem slice
(`test_published_package_retrievable_via_rules_package_service`). The neighboring
`test_ledger_pipeline::test_clean_regeneration_is_byte_for_byte_deterministic`
also finalizes the full corpus and confirms the conftest restructure preserved
byte-for-byte identity.

**No assertion loss / stronger isolation.** 39 tests preserved (verified via
`--co`); none skipped, optional, or excluded. Because the compact candidate passes
the gate with ZERO failures, failure-injection tests isolate *only* the injected
fault (legacy-block fails only on legacy; `test_final_gate_failure` fails only on
the tampered `transform_config_hash`) — tighter than the full corpus gave. The
compact positive control (`verify_persisted_digest` True on the clean release)
keeps every compact tamper/digest/policy test non-vacuous. Two-release coexistence
still persists complete, disjoint chunk/projection state for both releases (not
package rows), consolidated in one test. Multi-batch behavior elsewhere uses a
compact corpus + an artificially small advertised Chroma batch limit (round 5),
not thousands of documents.

**Consolidated/replaced tests:** none removed or merged — this is a pure
fixture swap (compact vs full), so every test and assertion is retained. Three
tests were explicitly pinned to the full corpus (listed above); all others route
through the compact shadow.

**Measured timing (module, local):** 39 passed **307.18s → 74.46s (~4.1×)**.
Slowest remaining: the one-time full-corpus fixture build (~38s setup, shared) and
the three retained full-SRD tests (~7–13s each); all 36 compact tests ≤0.5s.
`--durations=25` added to the CI pytest invocation (`.github/workflows/ci.yml`;
no existing `--durations` in `addopts` to duplicate); no wall-clock threshold.

---

## Round 14 — Four coordinated merge-blocking/regression findings (completeness, tables, source membership, Issue 18)

Four findings in the bounded authoritative-corpus attestation chain (authoritative
PDF → exhaustive ordered extraction → structurally faithful ledger → correctly
persisted source membership → verified immutable release), plus one Issue-18
ownership correction. No Owner Decision / ADR redesign required (settled Issue-5c
obligations).

**Round-9 correction (completeness defect, no Codex thread).** Round 9 rested on
"a six-canary-page candidate passes the genuine `finalize_release`/publication
gate." That was itself the completeness hole: the authoritative-source hash is a
bound constant, not a function of the pages actually extracted, so a partial
corpus carrying the real PDF hash could publish. It is **corrected here** — a
partial corpus is now rejected by production finalization; the six-page fixture is
a **negative control**, and finalizes only through the private `_finalize_core`
seam used by lower-layer compact tests (no test flag / caller boolean / public
bypass). The round-9 speedup is retained (compact fixtures still exercise
persist/reconstruct/digest/gate on the partial corpus via the seam).

**1. Exhaustive extraction (MERGE-BLOCKING).** `source_completeness`: an ordered
per-page extraction manifest hashed to a golden `AUTHORITATIVE_SOURCE_EXTRACTION_
HASH` + structural `1..364` sequence checks, detecting omitted/duplicated/
reordered/substituted pages. Enforced in `finalize_release` before any SQL/Chroma
mutation (rejected candidate leaves no state); reuse path adds a DB-grounded
persisted-page-coverage check. Proof is over pre-segmentation page text (stable
across Finding 2). Regressions: six-page negative control + each corruption mode
leaving no package/release/vector state.

**2. Structurally faithful tables (MERGE-BLOCKING).** `tables`: rect-anchored
column boundaries + text-line rows → `TABLE_CELL` leaves partitioning each row's
char span (tiling preserved: adjacent within a row, one `\n` between rows), wrapped
cells folded, page-spanning tables continued, `TABLE` containers nested. Ledger
leaves gain `table_id/table_row/table_col` (migration 0019); bound into the digest
via the ledger payload. Mis-detections discard the table (span-validity + page
concordance) and fall back to paragraphs — tiling never sacrificed. `check_table_
concordance` verifies every emitted cell's **structural consistency** (unique
row/col, in-range, non-empty) and on-page presence from the reconstructed tables
(independent of RuleChunks) — the structural checks catch failure modes the
detection filter does not itself guarantee, so it is non-tautological — and
surfaces the detection coverage tally. **Coverage (no silent cap):** 1,571 rect
anchors → 640 tables emitted; 931 candidate regions correctly fall back to
paragraphs (743 no clean contiguous row run, 2 inverted/overlapping spans, 186 a
reconstructed cell not on-page — verified to be shaded *prose* spanning both body
columns, e.g. "teristics, as shown Ability Descriptions", not real tables). Exact
oracles: page-9 Skills (3-col), page-10 Actions (wrapped multi-line cell), page-7
Attack Roll (2-col, canary page). Full-corpus: 364 pages → 28,750 leaves (was
14,023) = 28,385 represented + 365 excluded + 0 unresolved; 640 tables / 16,095
cells; 0 gaps/overlaps/orphans/duplications; concordance + table structural
consistency + canaries pass; byte-for-byte deterministic.

*Component C sibling audit (defect family: source content flattened / mis-typed).*
Searched: table containers, list containers, multi-paragraph list items, stat-block
fields + action lines, captions/titles/labels.
- table containers/cells — **patched** (this finding).
- list containers — **out of scope**: list *items* are already atomic `LIST_ITEM`
  leaves (inventoried, no content loss); a grouping `LIST` container is not required
  by #132 and would not change the accounting equation.
- multi-paragraph list items — **already safe**: each paragraph is an atomic leaf;
  nothing is dropped or double-counted.
- stat-block fields / action lines — **already safe**: `STAT_FIELD` leaves (2,102)
  plus paragraph leaves inventory them exhaustively; #132 requires no cell grid here.
- captions / titles / labels — **already safe**: inventoried as heading/paragraph
  leaves (no loss); a dedicated `CAPTION` type is out of scope for #132.
No MechanicalEntity / executable interpretation / 5d work entered.

**3. Persisted source membership (MERGE-BLOCKING).** Digest binds every chunk's
persisted `source_id` and the complete ordered logical `RuleSource` set
(id/package/name/category/precedence/enabled; `created_at` excluded);
`verify_single_source` enforces the single-source invariant. Reconstructed from
persisted state; gates publication + reuse. No Issue-5a schema change (`source_id`
already on `rp_chunks`). Regressions: extra/missing/altered/disabled/reassigned
source all fail; clean positive control.

**4. Package-generic Issue 18 diagnostics (P2 regression).** `_is_published_and_
enabled` no longer unconditionally requires a `CorpusReleaseORM`: the package must
be published+enabled, and a corpus release is required to be published only *when
one exists*. A generic package published through the pre-existing
`IngestionService.publish` path (no corpus release) is diagnostically queryable
again; a draft/inconsistent 5c release still stays hidden with no Chroma access.
No completeness/table checks in this generic surface. Non-creating Chroma lookup
preserved.

---

## Round 15 — Table-attestation defect family (four P1s)

One defect family across the table dependency chain (pdf_source → source_completeness
→ tables → ledger → models → transform_identity → concordance → persistence/digest),
not four isolated edits. Boundary/sibling-audit gate active (second consecutive
round on the table hotspot); settled Issue-5c obligations, no Owner Decision.

**F1 — table code in transform identity.** `tables.py` (segmentation, cell
contents/ids, row/col metadata) was absent from `TRANSFORM_SOURCE_MODULES`, so its
output could change without re-minting identity. Bounded transitive a0–b audit and
dispositions: *included* — pdf_source, ledger, **tables**, transform, reconcile,
policy, bundle, hashing, models, pipeline, transform_identity; *already-covered* —
`models.retrieval.rules_corpus_vector_identity` (its output, the vector identity, is
bound into transform_config directly); *verification-only* — concordance, report,
gate, persistence, vector_publication, quarantine, source_completeness. Plus one
*data* input (F4 below). Regression: mutating tables.py moves transform hash, package
UUID, release version.

**F2 — geometry in completeness.** `source_extraction_manifest` bound only page
ordinals/dimensions/canonical text, so a geometry-only change could alter headings/
tables while passing completeness. It now binds the full normalized extraction
geometry every heading/table/ledger step consumes (line top/x0/x1/size + span + text,
word text/x0/x1 + span, rect geometry; rect *type* not read → not bound). Golden
re-derived. Geometry-only negatives (coord/font/word-span/rect, text unchanged) fail
completeness before any SQL/Chroma mutation.

**F3 — cross-page logical tables.** Table ids were page-local and `_build_cells`
restarted row numbering, so the Actions table (printed pages 9→10) persisted as two
unrelated grids. `assemble_tables` links the geometrically lowest table on page N to
the highest on page N+1 iff they share column count + normalized header (never column
x-positions — a table shifts body column between pages; page-9 Actions is the right
column, page-10 the left). Logical tables have a stable id (first segment), continuous
logical rows that do not restart at the page boundary, and a retained+flagged repeated
continuation header (shares logical row 0, `is_continuation_header`, not double-counted).
Leaves stay per-page (tiling invariant intact); logical identity is metadata
(`table_id`=logical id, `table_row`=logical row, new `table_segment`; migration 0020),
bound into the digest and surviving persistence/reconstruction/publication/reuse. Exact
page-spanning Actions oracle: seg0 p9 lr0 Action/lr1 Attack/lr2 Dash; seg1 p10 lr0 Action
(continuation header) + lr3 Disengage… .

*Detection boundary (Component C sibling audit, table hotspot):* run growth is clipped
to the rect y-band + on-page row trimming, so page-9 Actions is detected without
swallowing the right-column prose above it. A page-9 vs page-7 geometry study showed a
table's own colored *title bar* (page-7 "Attack Roll Abilities", 27pt above the first
shaded rect) and adjacent prose are geometrically indistinguishable, so the title bar
falls to a **caption/paragraph leaf** (inventoried, not lost) while the table
reconstructs faithfully from its column-header row down — `already safe` (captions were
dispositioned as paragraph leaves in R14). Page-7 oracle updated accordingly.

**F4 — independent expected-table oracle.** The prior `check_table_concordance` re-ran
the detector at check time (self-comparison), so a suppressed/flattened table could
never fail. `table_inventory` adds a committed, frozen inventory
(`srd_table_inventory.json`, 683 logical tables incl. 9 multi-page) at logical-table
granularity (page span, header, col count, logical row count, segment count, cell-detail
hash), generated by a documented offline procedure (`scripts/regen_table_inventory.py`)
and compared against the live reconstruction — **never** regenerated by `_detect`/
`assemble_tables` at check time. Prose is excluded by construction (dropped to
paragraphs), distinguishing tables from prose. Its hash is bound into
`transform_config_payload` (candidate-affecting config → new release on change), and
`finalize_release` rejects a full-corpus candidate whose live tables diverge before any
store mutation (compact tests bypass via the private `_finalize_core` seam).
Discriminators (red-first) prove independence: suppress / invent / flatten / fragment /
merge each fails; live==committed positive control.

*False-merge guard (post-advisor audit):* the linker keyed continuation on column count + header, so tables sharing a header across a section break (every spell list is `spell/school/special`; the class/level is a heading above the table) could merge. All 16 candidate multi-page links were audited; a guard now links only when no section heading sits physically above the continuation segment — false merges drop 16 → 9, all 9 survivors verified genuine (Actions, d100 trinkets 34→35, per-class spell lists, 1d8-ray 4→5). Inventory regenerated (676 → 683 logical tables) and identity rebaselined; the wrong merges are no longer frozen into the oracle or the package identity.

**Full-corpus (clean build):** 364 pages → 28,474 leaves = 28,109 represented + 365
excluded + 0 unresolved; 0 gaps/overlaps/orphans/duplications; 15,715 table cells across
683 logical tables (9 page-spanning); whole-corpus concordance + table structural
consistency + independent inventory (683/683) + 6 canaries all pass; byte-for-byte
deterministic (same UUID/version/hashes on rebuild). package_uuid re-minted (tables.py +
inventory hash now in identity).

---

## Round 16 — three review threads (host-independent identity, packaging, stale-thread closure)

**F1 (closure) — stale Magma/Steam false-merge.** The comment predated `e25f877`
(the cross-page section-heading continuation guard). At head the page-307 Magma
Mephit and page-308 Steam Mephit stat blocks are distinct single-page logical
tables; the committed inventory records distinct IDs. No linker/inventory change.
Independent negative regression `test_magma_and_steam_mephit_statblocks_are_distinct_tables`
asserts (against the committed inventory, not `_has_heading_above`) that no logical
table spans `(307, 308)` and that the page-307/308 table IDs are disjoint.

**F2 (merge-blocking) — host-dependent release identity.** `build_report` placed
`platform.system()`/`platform.machine()` (and a runtime `sys.version_info`) into
the hashed `EvidenceReport` payload, so `report_hash` — one of the five top-level
release identities — could differ across supported hosts for identical committed
inputs. Fix: the payload records only the declared, host-independent reproduction
target (`{"python_target": "3.12"}`) plus the pinned extractor/parser versions +
deterministic invocation already carried by `transform_identity`; the actual host
is emitted as an operational log line only, never in any canonical artifact/hash/
digest/gate. *Audit of the five identity payloads:* `evidence_report_hash` carried
host data → **patched**; authoritative-source hash, transform-config hash,
bundle-root hash, persisted-corpus digest are all deterministic (repo-relative
source manifest, pinned-dep versions, no host/path/time) → **already safe**.
Regression `test_evidence_report_identity_is_host_independent` proves byte-identical
payload + `report_hash` under monkeypatched OS/arch/python. No package-UUID/version
move (the report is not in the transform config); no golden rebaseline (the hash is
runtime-computed and DB-stored, not a literal).

**F3 (merge-blocking) — package the committed inventory.** `srd_table_inventory.json`
is read at runtime and finalization fails without it, but it was in neither
`package-data` nor `MANIFEST.in`. Fix: added to both (wheel + sdist);
`load_committed_inventory()` reads via `importlib.resources` (resolves from an
installed distribution, not a checkout/CWD), fail-closed on missing/corrupt; the
runtime read is decoupled from the regen write (`source_inventory_path()` used
only by the regen script). *Resource audit (Issue-5c corpus subsystem):* inventory
JSON = **included**; authoritative PDF = **out of scope** (separate source-path/
deployment contract, caller-supplied path); `transform_identity` reading sibling
`.py` modules = **already safe** (code always ships); `quarantine.check_source_references`
= **out of scope** (repo-scan verification taking an explicit `repo_root`, not a
packaged resource). Smoke test `test_packaging.py` builds wheel+sdist, asserts both
contain the JSON, installs into an isolated target, and imports from there (not the
editable checkout, via `-S` + explicit `PYTHONPATH`) to reload all 683 entries and
reproduce the committed inventory hash. `build` added to dev dependencies.

---

## Round 17 — evidence-report schema identity + clean-runner packaging

**P2 — evidence-report schema changes did not mint/invalidate release identity.**
`report.py` was verification-only, so R16's canonical report shape change
(`reproduction_environment` → `reproduction_target`) left the package UUID/version
unchanged. A pre-R16 published release keeps the same UUID → `finalize_release`
enters reuse, validates the stored obsolete-shape report against its stored hash
(both old → passes), and returns `reused=True` with the obsolete evidence identity.
Fix: an explicit canonical `EVIDENCE_REPORT_SCHEMA_VERSION = "5c-evidence-2"`
(bumped for the R16 shape), recorded in the report payload and bound into
`transform_config_payload` → transform hash → package UUID → release version, so
the R16 schema change mints a new immutable release. *Bounded analysis:* explicit
schema identity (not adding all of `report.py` to the byte-level transform-source
manifest) — only an intentional canonical-shape change should remint; a comment or
operational-logging edit must not. Reuse backstop `_report_schema_ok` fails closed
unless the persisted report **and** transform config both record the supported
version (missing/obsolete/contradictory/malformed → reject). *Sibling
post-persistence schemas:* persisted-corpus digest and bundle root are `already
safe` (reuse recomputes them from persisted state and compares to the stored value,
so a shape change fails closed); only the evidence report — validated against its
own stored hash on reuse — needed explicit versioning (`patched`). The identity
test helper now builds the complete production transform payload (all identity
fields incl. inventory hash + schema version), so its inequality assertions are
non-vacuous. Regressions: schema-version change moves transform hash/UUID/version;
obsolete pre-R16 report not reused; current-schema identical inputs reuse
byte-identically (full idempotency test); tampered/contradictory/missing/malformed
schema fails closed (`_report_schema_ok` unit + reuse integration).

**CI — clean-runner packaging build.** GitHub Actions run 30216668887's only Python
failure was `test_packaging.py::test_wheel_and_sdist_include_inventory_and_load_from_install`;
`_build_dists()` captured and suppressed the build's stdout/stderr, hiding the
cause. Root cause (reproduced in a clean venv): `python -m build --no-isolation`
requires the declared build backend (`[build-system].requires`: `setuptools>=68`,
`wheel`) to be importable in the current environment, but the dev extra added only
`build>=1.0` — a clean runner raised `Cannot import 'setuptools.build_meta'`. Fix:
add `setuptools>=68` + `wheel` to `[project.optional-dependencies].dev` (making the
no-isolation contract explicit) and surface build stdout+stderr on failure. The
wheel/sdist installed-artifact assertions are unchanged (not skipped/xfailed/mocked/
weakened); confirmed in a clean env that both archives build and contain the oracle.

---

## Round 18 — pre-release clean baseline (owner-approved specification correction)

Owner decision (Issue 5c Rev7 / Issue 18 Rev6): Afterworlds is pre-release, so
persistence created before Issue 5c receives no upgrade-compatibility or
preservation guarantee. The strict cross-store quarantine contract (the Round-18
P1 was valid *under that contract*) is explicitly **replaced** by a breaking clean
baseline. The superseded UUID-handoff / selective-quarantine / retryable
cross-store workflow design was **not** implemented. Deleted complexity, not added.

**Retired.** `ingestion/corpus/quarantine.py` (repo/runtime zero-reachability scan
+ active-store check); the publication-time legacy-reachability check in
`finalize_release` (both paths), the evidence report, and the publication gate
(condition 22); the now-dead `repo_root` parameter on `finalize_release`/
`_finalize_core` and its callers; the obsolete quarantined structured JSON
(`docs/legacy/quarantine/srd_5_2_1_structured.legacy.json` — kept only in Git
history); and the superseded interim direct reader `VectorWriter.query()` +
`QueryResult` (no production caller; the supported diagnostic reader remains
`RulesCorpusService.diagnostic_query()`).

**Kept / added.** Migration `0018`'s targeted deletion of the incomplete legacy SQL
package + dependent rows (docstring reframed; no random-UUID handoff for later
Chroma cleanup). `EVIDENCE_REPORT_SCHEMA_VERSION` bumped `5c-evidence-2` →
`5c-evidence-3` (R17 mechanism): dropping the legacy-reachability status changes
the canonical report schema, so transform hash / package UUID / release version
remint and a former-schema report cannot be reused. New guarded one-time reset:
`pipeline/retrieval/baseline_reset` (`resolve_reset_target` validates the exact
configured `persist_directory`, refusing empty/root/home/cwd/ancestor;
`reset_chroma_store` deletes **every** collection through the client — never
filesystem/rmtree/prefix) driven by the explicit CLI
`scripts/reset_corpus_baseline.py` (validate → full reset → rebuild the rules
corpus from the published SQL package via Issue 18's reindex path; never startup).

**Docs reconciled** with the owner decision (quoted, not fabricated from the
external Rev7/Rev6 text): dated correction notes in ADR-005c, ADR-018, the
reproducibility doc, `known_unknowns.md`, migration 0018's docstring, and the
legacy README (retained as concise documentation minus the deleted bytes).

**Regressions.** (1) obsolete JSON + every production reference absent (a repo-tree
scan replacing the deleted reachability checker); (2) migration 0018 deletes the
incomplete package + dependent rows; (3) an arbitrary-collection store is reset in
full then rebuilt from current SQLite records; (4) no legacy UUID/collection-name
knowledge required (reset takes none); (5) idempotent reset; (6) generic packages
+ story-memory reindex remain valid; (7) removed reader is absent and the diagnostic
reader neither retrieves nor recreates a deleted package UUID's collection; (8) new
report schema remints identity and former-schema reports cannot be reused. Guard
negative test: `resolve_reset_target` refuses root/home/cwd/ancestor/empty.

---

## Round 19 — fresh-publish rollback boundary + reset configuration contract

**P2 (a) — every fresh-publication SQL write is now inside the compensation
boundary.** `_finalize_core` opened its `try` *after* `_persist_package_and_source`,
`_persist_release_record`, and `_persist_bundle_rows`, so an exception during draft
persistence propagated with no `session.rollback()` — pending ORM state survived on
a session the caller may keep using. The boundary now opens before the first
fresh-release SQL mutation and closes only after a successful publication commit or
completed failed-gate compensation. Audited for the "first mutation" claim: between
the function signature and the boundary the only SQL is the read-only idempotency
`select`; every other statement above it belongs to the reuse branch, which returns.
Vector cleanup is initialised **disarmed** and armed immediately before
`reindex_and_verify` (which can write the collection and then raise during
read-back), disarmed only after commit — so a pre-vector SQL failure rolls back SQL
and never creates, inspects, or deletes a Chroma collection. Failed-gate, post-vector,
and commit compensation are behaviourally unchanged; reuse still verifies only.

**P2 (b) — the destructive reset documented a variable nothing reads.**
`scripts/reset_corpus_baseline.py` documented `AFTERWORLDS_RETRIEVAL_PERSIST_DIR`
while `RetrievalMemoryConfig.from_env()` reads
`AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY`; an operator following the documented
command would have exported an ignored variable and reset the **default** store.
Corrected to the canonical name — deliberately **not** aliased. Repo-wide audit of
both spellings (all file types, excluding `venv/`/`.git/`): the docstring was the
sole occurrence of the short name anywhere in the repo; all 12 other files (script,
config, frontend e2e harness, API/backfill tests) already used the canonical name.
Resolution, validation, client construction, reset, and rebuild all remain on the
same `config.persist_directory`.

**Regressions.** Parametrized fault injection at each pre-vector persistence step
(package/source, release record, bundle rows), each failing *after* its real writes
so genuine pending state must be rolled back, proving: the exception propagates; the
session is immediately reusable; no draft rows survive in `rp_packages`,
`rp_corpus_releases`, `rp_sources`, `rp_ledger_leaves`, or `rp_chunks`;
`session.new/dirty/deleted` are empty; `cleanup_vector_collection` was never called
and the collection count is 0; and a clean retry on the same session publishes. The
post-vector (`build_report`), gate (`run_gate`), and `commit` checkpoints are
parametrized alongside them (same coverage as the three Round-18 cases they replace).
Script-level: the canonical variable's target is what the **real** guard validates
and what the reset client is built from; the mistaken spelling alone does not
redirect the reset; `--help` shows only the canonical name.

**Sibling audit (gate: repeated rounds on `_finalize_core` cross-store
compensation).** Defect family: *SQL mutation reachable outside the
rollback/compensation boundary, or compensation armed outside the window where the
compensated resource can exist*. Triggering rounds: R18 P2 (vector attempt →
commit boundary) and R19 P2(a) (draft persistence outside it). Searched:
`_finalize_core` (both branches), `finalize_release`, `persist_release`,
`_persist_package_and_source`, `_persist_release_record`, `_persist_bundle_rows`,
`reindex_and_verify` / `verify_only` / `cleanup_vector_collection`, and every
`session.add`/`add_all`/`flush`/`execute(delete)`/`commit`/`rollback` in
`ingestion/corpus/persistence.py` (enumerated and attributed to its owning
function: all 14 draft-write statements belong to the three persist helpers, the
rest are `delete_release`'s two deletes + flush and `_finalize_core`'s own
flush/commit/rollback — no fourth writer exists).
Dispositions: fresh path draft persistence — **patched**; fresh path arming window —
**patched**; fresh path post-vector/gate/commit — **already safe** (R18, re-proven
by the parametrized checkpoints); idempotency `select` before the boundary —
**already safe** (read-only, no mutation to roll back); reuse branch — **already
safe** (verifies and reconstructs only, performs no SQL mutation and no vector
write, so it has nothing to compensate and must never delete the published
collection — pinned by the reuse-exception regression); `persist_release` (the
non-publication re-persist helper: it calls the same three helpers but commits
nothing and owns no boundary — the caller's transaction is the boundary) —
**already safe** by construction, and out of scope for this finding since it is
not a publication path; `delete_release` (deletes + flush, caller-owned
transaction, no vector side) — **already safe**; broader
cross-store/two-phase publication semantics — **out of scope** (Issue 5d /
retrieval redesign, explicitly excluded this round).

---

## Round 20 — reset-command disclosure (ownership already settled)

**Boundary, not a redesign.** Codex correctly observed that the full-store reset
deletes the shared `story_memory` collection while the command rebuilds only the
Issue-5c rules corpus. The suggested remedy — reindex all persisted stories inside
this command — is **not** the accepted contract: GitHub #132 Owner Decision 1 states
"any desired story-memory backfill uses Issue 18's existing reindex path and is not
redesigned here", and pre-5c development persistence carries no preservation
guarantee. Enumerating and reindexing every story here would turn the Issue-5c
baseline into Issue-18 restoration orchestration. Ownership is unchanged; what was
genuinely missing was **operator disclosure**.

**Corrected.** `scripts/reset_corpus_baseline.py` now states, in both `--help` and a
runtime warning, that the reset is full-store and deletes every collection
**including `story_memory`**; that the command rebuilds published rules-corpus
projections **only**; that it does **not** restore story memory and deliberately does
not enumerate or reindex stories; and that restoration is the existing per-story
`scripts/retrieval_backfill.py --story-id <uuid> --mode reindex`. The warning is
printed **before** `reset_chroma_store()` — a notice printed after deletion is a
report, not a warning — and a closing line repeats it. `--help` uses
`RawDescriptionHelpFormatter` so the section reaches the operator as written. ADR-018's
2026-07-27 correction gained a dated clarification: "story-memory restoration uses the
same Issue 18 reindex path" names the *optional recovery mechanism*, not a step of the
Issue-5c command. Nothing about corpus publication, evidence-report identity, or the
clean-baseline Owner Decision changed.

**Regressions.** `test_warns_that_story_memory_is_deleted_before_deleting_anything`
records an ordered trace of the script's prints against the reset call and asserts the
`story_memory` warning precedes `RESET` (and names the restoration command);
`test_usage_states_story_memory_is_deleted_and_not_rebuilt` pins the same disclosure in
`--help`; `test_reset_rebuilds_only_published_rules_corpora_and_never_story_memory`
seeds a published release, a draft release, and a real story, then asserts exactly the
published package is reindexed and that no story-memory machinery (`reindex_story`,
`backfill_story`, `StoryORM`, `RetrievalMemoryWriteService`) is reachable from the
script at all. The Round-18/19 reset-safety, idempotency, env-var, and rules-corpus
rebuild tests are unchanged and green.
