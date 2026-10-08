# Remediation log — CRD Issue 5c/5d clean restart, increment 1

Local remediation of the two quarantine gaps Codex reported against increment 1
(`bdff735`), plus the comparison-instrument claim corrections the Owner's brief
required in the same pass. Reviewer files were not modified.

## R1 — the obsolete production path was closed by output identity, not by recipe

**Defect.** `_finalize_core` refused on `package_uuid` and `release_version`,
both of which are content-derived. Reconfiguring the embedding model label minted
a different package UUID (`f17712a9-251f-5c91-b38c-eae01be1f991`,
`5.2.1-corpus.811044cf-46e`) for the *same* obsolete extraction, and that release
was admitted. Separately, `scripts/ingest_srd.py` ran `upgrade_to_head` and built
the Chroma client before anything downstream refused, so a refused command still
migrated a database and created a store directory.

**Correction.** `QUARANTINED_TRANSFORM_SOURCE_HASHES` names the retired transform
recipe — `transform_identity.transform_source_hash`, the frozen digest of the v1
transform's own source manifest, which every build of the PDF-geometric corpus
records whatever identity its configuration produces. `_finalize_core` now passes
that value at step 0, above the idempotency select. One hash for one retired
recipe: no enumeration of alternate outputs, and no compatibility layer.
`scripts/ingest_srd.py` refuses as the first statement of `main()`,
**unconditionally** rather than on a computed key — the retired thing is the
command, and a key derived from the transform source would silently re-admit it
the moment someone edited that source.

**Sibling.** `scripts/reset_corpus_baseline.py` had the same shape and was worse:
it deletes *every* Chroma collection, `story_memory` included, and rebuilds rules
corpora only. Its rebuild seam refused the quarantined package — after the
deletion. The refusal moved into `preflight`, keyed per published release on
package UUID, release version and recorded transform recipe, so it lands before
`build_chroma_client`. Scoped, so the replacement corpus can still use the
command. Full dispositions for the `scripts/` tree are in §2.2 of
`docs/architecture/issue-5c-5d-clean-restart.md`.

## R2 — generic publication and default reads bypassed the quarantine

**Defect.** Codex reproduced publication of the quarantined package through
`IngestionService.publish`, and retrieval of its chunk through default
`get_package_by_id` / `get_chunks_by_subsystem`, in isolated SQLite.

**Correction.** Identity-scoped guards in `IngestionService.ingest` (configured
release version, upserted package UUID) and `publish` (before the first select,
and again on the stored row's version), and one guard in
`RulesPackageService._package_accessible` — the single accessibility helper all
six by-id readers route through, so entity and override readers are covered once
rather than six times. There is no enumeration method whose listing behaviour a
raise could change.

Boundaries held: `include_non_published=True` is a lifecycle filter, not reference
access, so the read guard ignores it; explicit reference access remains reading
committed bytes from a path, which the inverted tests pin. `RuleOverrideORM`
*writes* are `already safe` — the admission mechanism is that no production code
constructs one (`grep "RuleOverrideORM("` over `src/` and `scripts/` is empty), so
no production path attaches an override to a quarantined package. Unrelated custom
packages still ingest, publish and read end to end.

## R3 — the comparison instrument claimed more than it measured

Two claims were wrong and are withdrawn, not softened:

* **Content preservation.** `policy.compact` (`nfkc-ws-1`) folds the minus sign
  and then removes hyphens, so `modifier -2` and `modifier 2` compare equal. The
  normalization is not lossless; signs, footnote markers and adjacent qualifiers
  are not checked by this pass.
* **The universal reordering bound.** The `2 * WINDOW` floor bounds *one isolated*
  junction. Adjacent junctions merge into a single longer run — a 134-character
  identical-multiset counterexample is recorded — so the floor is a reporting
  threshold, not a clearance. The verdict `prose_within_noise_floor` was renamed
  `below_floor_unresolved` because the old name read as the clearance the prose
  denied, and the sub-floor runs are now counted in the record
  (`runs_below_floor` 112, `chars_below_floor` 10,000) instead of left implicit.
  The round 10,000 is a coincidence: `_run` computes `final - first + window` with
  no clamp, and the sum is over 112 runs each below 96.

No second comparison engine was built. Full source qualification remains pending,
including sign/number/qualifier differences, structural ownership, community
additions and official p.1 attribution.

The 364-page evidence record was regenerated because the verdict rename and the
new fields had to appear in it. Every measurement is identical to increment 1
(coverage identical, 54 runs / 37,305 characters over floor, same run lengths,
same additions, same pin commit); only the claims changed.

## R4 — skip accounting

109 skipped tests carry `QUARANTINED_RECONSTRUCTION`; the other 10 skips in the
full run predate this work. The retired-versus-still-live disposition of each, and
the six operational-coverage obligations the replacement stage owes, are recorded
in §2.5 of `docs/architecture/issue-5c-5d-clean-restart.md`. No skip was converted
back into a passing test by weakening a guard: passing tests went 6,264 → 6,279
entirely through new refusal coverage.

## Gates

`.claude/review-notes/issue-5c-5d-clean-restart-gates.md`, second section.
