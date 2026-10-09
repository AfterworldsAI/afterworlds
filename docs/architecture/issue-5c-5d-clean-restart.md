# CRD Issues 5c and 5d — clean restart: implementation state

## Current state - verified 9 October 2026 UTC (release-order recording accepted and delivered as draft PR #178; bounded test and CI correction reviewed; exact-head backend coverage gate pending; publication blocked)

- **Authority and inputs.** The [21 September Owner Decision](../decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md) governs the restart; legacy 5c/5d products remain quarantined and do not confer inherited acceptance. The [official SRD 5.2.1 PDF](../sources/DnD5_5e_SRD_CC_v5_2_1.pdf) remains ultimate rules authority. The [qualified community source](../sources/community/dnd-5e-srd-markdown/PINNED-SOURCE.md), its [source manifest](../sources/community/dnd-5e-srd-markdown/source_pin.json), and the [correction evidence](issue-5c-5d-community-source-corrections.md) identify the corrected machine-readable inputs; source qualification is distinct from semantic acceptance. `CORPUS_FILES` is in official chapter order, with one focused order test; both are committed at draft PR #178 head `24a80b0`.
- **Current accepted recording.** The Owner accepted the exact [release-order replacement candidate](../../.claude/review-notes/issue-5c-release-order-candidate.md), SHA-256 `8a6a9a9c305f41207190c0deb55875a027019116ce3f825a6a0425a3a115b4bf` (["I accept this exact release-order candidate."](../../.claude/review-notes/issue-5c-release-order-recording/owner-acceptance.json), `2026-10-07T05:28:37Z`). The native recording at `2026-10-07T05:39:49Z` with fresh `Ravenlok (Owner)` approvals has on-disk oracle `srd-5-2-1-corpus-8781d4e0-a3b.json`, SHA-256 `def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c`. Release `1299484e-c72d-509b-bd8d-d0169ee1f8d2` / `5.2.1-corpus.8781d4e0-a3b` has **24 accepted batches, 1,835 records, 1,486 reference resolutions and real approvals, representation schema 17**. Against the candidate, everything outside `acceptance` and every `proposal_identity` is exact; only the six approval-evidence fields differ. See the [recorded follow-up](../../.claude/review-notes/issue-5c-release-order-recording/recorded-followup.md). The prior oracle `srd-5-2-1-corpus-3fe24ff6-4e3.json` (`e6f5f36a…`, release `67c81736-…` / `5.2.1-corpus.3fe24ff6-4e3`) remains unchanged on disk as historical evidence; committed-authority resolution now refuses its release (see the [readiness correction](../../.claude/review-notes/issue-5c-release-readiness/correction-followup.md)). It is committed in initial delivery `24a80b0` on draft PR #178; it is not merged or activated.
- **Remaining boundaries.** **Reference, uncovered-leaf and other native findings are all zero. The partial-publication block stands.** Semantic acceptance alone grants no Git or runtime publication authority. The Owner separately authorized Git commit and delivery; merge, runtime publication, activation and shared-database writes remain held. Details:
  - **Superseded release:** corrected 7 October. No further Owner Decision was needed: the 21 September Decision authorizes retiring superseded work and forbids invented approval gates. Resolution now refuses `5.2.1-corpus.3fe24ff6-4e3` and `5.2.1-corpus.574662e9-0ef`; the files stay on disk as historical evidence.
  - **Pinned tests:** corrected 7 October. Generator-rebuild tests now compare current with current and historical with historical; only obsolete cross-release byte, count and tool expectations were retired, and the useful reference replay is kept on the representation's own findings. The *Animals* current reader expectation now follows the current source order (*Monsters* first). The historical *Animals* generator cannot build over the current release; this is recorded, not patched. See the [readiness correction](../../.claude/review-notes/issue-5c-release-readiness/correction-followup.md).
  - **Reader-retention residue:** pre-existing and out of scope; remains deferred.
  - **Prior local gates (7 October, Windows source checkout):** The corrected full default `pytest`/coverage run `final-pytest-coverage-2` completed at 21:42:29 UTC with native exit **0**: **7,397 passed, 141 skipped, 252 warnings, no failures or errors; 92.48% coverage against 80%**. Root Black (552 files) and Ruff are native 0. Strict affected-test mypy is native 0 on the final 42-file union; production strict mypy (235 files) is reused on unchanged source inputs. All 616 immutable frozen inputs remain unchanged through the completed gate. The original failed root receipt remains historical. See the [final readiness result](../../.claude/review-notes/issue-5c-release-readiness/codex-final-readiness.md). Native span acceptance remains restored in all seven historical compositions with exact missing-approval multisets. Final scoped secrets content has zero unbaselined findings; private-copy normalization returned 3 then 0, while the real relative hook remains native 1 because the baseline is unstaged. Preservation is retained separately. No publication or restart-completion authority is inferred.
    - The 16 test typing errors are closed in initial delivery `24a80b0`. See the [typing follow-up](../../.claude/review-notes/issue-5c-release-readiness/typing-followup.md): strict mypy exits 0 on the three files; Black and Ruff exit 0; 305 + 174 focused diagnostics pass.
    - The 105 further pre-existing strict mypy errors in 7 consumer test files are closed in initial delivery `24a80b0`; strict mypy over the selected 16-file set (the original 15 plus Checks/Actions/Rest) exits 0 (see the [readiness correction](../../.claude/review-notes/issue-5c-release-readiness/correction-followup.md)).
    - **Correction (8 October).** This Windows full gate ran in the source checkout, where the private superseded-release store `.claude/_rc/msc/rel/afterworlds.db` existed. It is not clean-checkout or Linux proof; see the [assembly correction](../../.claude/review-notes/issue-5c-git-delivery-assembly-2026-10-08.md).
    - Those 7 October secrets checks were historical: the private-copy hook exited 0, while the real relative hook exited 1 against the unstaged source baseline. The current additive changed-input check passed the real relative hook with native exit 0 and an unchanged baseline; prior whole-delivery proof is reused. Dependency-vulnerability repairs remain deferred until the 5c Restart is complete.
- **Immediate next step.** Obtain exact committed-head CI for the reviewed additive correction, then conduct fresh full-PR review. The [Git delivery packet](../../.claude/review-notes/issue-5c-git-delivery/PACKET.md) was assembled and reviewed in an isolated checkout ([assembly status](../../.claude/review-notes/issue-5c-git-delivery-assembly-2026-10-08.md)) and delivered on 8 October 2026 UTC as **draft PR #178**: branch `codex/5c-restart-delivery`, initial committed head `24a80b0`, base `f5a78aa`.
  - **Initial CI on that head failed.**
    - Backend: Black, Ruff and strict mypy passed. The tests then had 11 *Animals* failures, and the job was cancelled at the six-hour limit after running about 29% of them.
    - Frontend: `npm audit` failed under the dependency deferral, so the OpenAPI drift check and the build were skipped.
    - E2E: passed.
  - **Root cause.** Pinned replay scripts read the superseded release `5.2.1-corpus.3fe24ff6-4e3` from the private `.claude/_rc/msc/rel/afterworlds.db`. That store exists in the source checkout but not on CI.
  - **Correction state.** The bounded additive correction included here passed Codex review in the isolated delivery checkout:
    - Tests rebuild that release from delivered inputs, refuse any other identity, and fail any test-time open of a private `.claude/_*` path.
    - CI runs the backend suite as 8 shards of the files pytest collects, measured with sysmon coverage. It rejects a failed or empty shard selection before pytest. It requires the shards' tests to equal the full collection exactly once, and enforces the unchanged 80% threshold on combined coverage. pip-audit is unchanged.
    - Two strict mypy `no-any-return` errors in `tests/ingestion/conftest.py` are fixed with proper types.
  - **Local Linux results (diagnostic only).** *Animals* 23 passed and ESR 51 passed (focused). The new sharder tests pass (3 tests), and strict mypy, Black and Ruff exit 0 on the changed files. Collection is accounted for: 7,541 tests in 279 files, none missing or duplicated. Selector failure and empty selection both stop before pytest.
  - **Not passed.** The complete aggregate gate has not run or passed.
  - **Outstanding.**
    - Exact committed-head CI, including the complete aggregate gate.
    - Disposition of the frontend audit under the deferral.
    - Fresh full-PR review and external synchronization.
  - **Owner boundaries.** Dependency-vulnerability repairs alone keep the after-restart deferral. Merge and runtime publication, activation and shared writes remain separate Owner boundaries. Restart completion is not declared, and the partial-publication block stands.

  Previously settled and still in force:
  - The final-ten recording evidence remains in force: the [recorded follow-up](../../.claude/review-notes/issue-5d-final-ten-references-recorded-followup.md) and the [Codex recording review](../../.claude/review-notes/issue-5d-final-ten-references-recording-codex-review.md).
  - The settled directions are:
    - [pricing and Gear (34, 36)](../../.claude/review-notes/issue-5d-references-34-36-source-clarification-2026-10-06.md);
    - [Wizard-owned Spellbook (39)](../decisions/owner-decision-2026-10-06-wizard-spellbook-reference.md);
    - [SRD-only familiars (48, 60)](../decisions/owner-decision-2026-10-06-srd-familiar-reference-scope.md);
    - [bestiary/local stat blocks (54)](../../.claude/review-notes/issue-5d-reference-54-source-clarification-2026-10-06.md);
    - [Awakened Plant supplement (57)](../decisions/owner-decision-2026-10-06-awakened-plant-supplement.md);
    - [ability-modifier glossary (76)](../../.claude/review-notes/issue-5d-reference-76-source-clarification-2026-10-06.md);
    - [Cantrip/Ritual casting guidance (87, 88)](../decisions/owner-decision-2026-10-06-cantrip-ritual-reference-scope.md).
  - Awakened Plant remains a separate Afterworlds house-rule template with 3 HP (1d6), tested only through an isolated prose addition. It is uninstalled and unactivated, and no supplemental SRD creature record was added.
  - Keep the [earlier packet's](../../.claude/review-notes/issue-5d-equipment-spell-references-review.md) reader-retention residue deferred.

  Include this opening and its evidence in the normal restart delivery when authorized; do not extract a standalone PR.

## Historical implementation record

The sections below preserve the earlier increments and their evidence. Statements
about unfinished construction or absent semantic acceptance describe those earlier
states; use the dated current-state summary and its linked recording for the
verified status above.

Authority for this document is the **Recorded Owner Decision of 21 September
2026** (`docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md`),
reconciled with CRD Issue 5c (#132), CRD Issue 5d (#137), ADR-005c and its
2026-08-03 operational-reliability amendment, and ADR-005d with its 2026-09-16
practical-reliability policy. Where those documents describe the superseded
products as live authority, this decision governs; each of them now carries a
supersession banner pointing here.

Sections 1-7 are the state after the **first implementation increment**, which
quarantined the superseded products and qualified the community source. Section
8 is the **second increment**: the replacement 5c corpus built from that source,
cited to the official PDF, and proven through the real publication lifecycle in
isolated stores. Neither increment publishes or activates anything for
production, and no semantic acceptance has been made.

## 1. What this increment delivers

| | |
|---|---|
| Decision recorded in-repo | `docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md` |
| Quarantine | `src/afterworlds/quarantine.py`, enforced at 18 seams in 10 modules |
| Pinned community source | `docs/sources/community/dnd-5e-srd-markdown/` at upstream `1b4b99dc` |
| Comparison instrument | `src/afterworlds/ingestion/source/community_compare.py` |
| Comparison evidence | `docs/architecture/issue-5c-5d-community-source-coverage.json` |
| Second pass and qualification (§7) | `src/afterworlds/ingestion/source/community_tokens.py` |
| Correction notes and sibling audit | `docs/architecture/issue-5c-5d-community-source-corrections.md` |

Steps 3–5 of the handoff — coherent source units with citations, fresh 5d
construction, and retirement of the superseded work — are **later increments**.
No file from the old products has been deleted; Git history is the retention
mechanism the decision calls for, and retirement is sequenced after the
replacement exists.

## 2. Quarantine

### 2.1 What is quarantined

Read from the artifact's own `release_binding` rather than from any description
of it:

| | |
|---|---|
| `package_uuid` | `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` |
| `release_version` | `5.2.1-corpus.36b786d8-fa2` |
| `projection_uuid` | `82c75aad-b294-5b2e-a188-128cdcbada09` |
| `transform_source_hash` | `6332f201eba9cba19d699a06c6c12580de5ef1c7f349fadacd2045c0e5312cc0` |

`quarantine.py` also names the two committed artifact paths and three content
digests (artifact, bundle root, persisted corpus) so a copy under a different
name is still recognisable.

**The retired transform is an identity too.** A published package UUID is
content-derived, so it moves when an *incidental* input moves.
`bundle.derive_package_uuid` is a function of the PDF hash and the transform
configuration — and the transform configuration includes the configurable
embedding model label. Changing that label alone mints a different
`package_uuid` and a different `release_version` for the very same obsolete
geometric extraction: with the default label the candidate is
`4458fa10-…` / `5.2.1-corpus.36b786d8-fa2` and is refused; with
`independent-review-alternate-embedding` it is
`f17712a9-251f-5c91-b38c-eae01be1f991` / `5.2.1-corpus.811044cf-46e`, which an
identity-only quarantine admits. Keying on published UUIDs therefore closes one
*build* of the retired product rather than the product.

`QUARANTINED_TRANSFORM_SOURCE_HASHES` closes that. It names the retired
PDF-geometric transform *recipe* itself — the frozen digest of the v1 transform's
own source manifest, recorded in every candidate's
`transform_config["transform_identity"]` — which no reconfiguration of an
incidental input moves. This is one hash for one retired recipe, not an
enumeration of the output hashes a reconfiguration could produce: the replacement
corpus is admitted by having a *different transform*, not by happening to land on
a different number.

Two consequences follow. Lifecycle tests that reconstruct a release in a fresh
store are skipped with a named reason rather than weakened (§2.5), and the
replacement corpus must be built by a transform whose recipe hash is not the
retired one — which is now the thing to assert when it is built, in place of the
weaker "must derive a different `package_uuid`". The compact six-page corpus is
refused for the same reason as the real release: it is built by the retired
transform, whatever identity it carries.

### 2.2 Seam map

Quarantine refuses by raising `QuarantinedAuthorityError`; it never returns an
empty result. An empty corpus, an absent projection, and a refused one are
different facts, and a caller that cannot distinguish them will eventually treat
retired authority as "nothing configured" and fall back.

| Module | Seam | Path it closes |
|---|---|---|
| `scripts/ingest_srd.py` | `main` (first statement) | the obsolete production ingestion command, before it migrates a database or opens a Chroma store |
| `scripts/reset_corpus_baseline.py` | `preflight` | the baseline reset, before it opens the Chroma client and deletes every collection |
| `services/rules_package.py` | `get_active_rule_slice` | the sole runtime rule-inclusion path (invariant 10) |
| `services/rules_package.py` | `_package_accessible` | every by-id read: packages, chunks, entities and both override readers (six call sites, one guard) |
| `ingestion/ingestion_service.py` | `ingest` (×2) | generic ingestion, on the configured release version and on the upserted package UUID |
| `ingestion/ingestion_service.py` | `publish` (×2) | generic publication, before the first select and again on the stored row's version |
| `services/rules_package.py` | `resolve_slice_package` (×2) | slice package selection, both resolution outcomes |
| `services/rules_authority/binding.py` | `resolve_package_reference` (×2) | both `AuthorityOutcome.RESOLVED` returns |
| `ingestion/mechanical/publication.py` | `resolve_active_projection` | active-projection selection |
| `ingestion/mechanical/publication.py` | `_activate_projection` | activation |
| `ingestion/mechanical/publication.py` | `publish_from_committed_oracle` (×2) | publication and reuse |
| `ingestion/mechanical/oracle.py` | `_resolve_committed_inputs` | committed accepted-authority resolution |
| `ingestion/mechanical/bound_corpus.py` | `load_bound_corpus` | 5d's bound view of the 5c corpus |
| `ingestion/corpus/persistence.py` | `_finalize_core` | corpus release finalization, keyed on package, release **and transform recipe** |
| `ingestion/corpus/gate.py` | `run_gate` | the publication gate |
| `ingestion/corpus/operational.py` | `load_verified_operational_corpus` | verified operational load |
| `ingestion/corpus/vector_publication.py` | `reindex_and_verify`, `verify_only` | vector publication and verification |
| `pipeline/retrieval/rules_corpus_service.py` | `reindex_from_sql`, `diagnostic_query` | retrieval reindex and retrieval fallback |

`_finalize_core`'s guard sits **above** the read-only idempotency select, so the
refusal precedes every store read and every store write on both the fresh and the
reuse path. Guarding only the downstream reindex would have refused after draft
rows were flushed, leaving the claim resting on the compensation boundary
undoing writes it should never have made.

The CLI guard is the same ordering argument one layer out. `scripts/ingest_srd.py`
previously ran `upgrade_to_head` and built the Chroma client before anything
downstream refused, so a refused command still migrated a database and created a
store directory. The refusal is now the first statement in `main()` — ahead of
argument parsing, the PDF check, `RetrievalMemoryConfig.from_env()`, the migration
and the client — and it is unconditional, because the whole command is the retired
transform. `tests/test_quarantine_5c_5d.py` runs the real command in a subprocess
and asserts a non-zero exit, the refusal in stderr, no database file and no Chroma
directory.

**Sibling audit — production commands with store effects.** Family: a retired path
that refuses *after* it has already changed a store. Trigger: Codex's finding that
`ingest_srd.py` migrates and opens Chroma before the downstream refusal. The
`scripts/` tree was read for the same shape; the dispositions are
`scripts/ingest_srd.py` `patched` (unconditional refusal as the first statement of
`main`); `scripts/reset_corpus_baseline.py` `patched` — it deletes *every*
collection, `story_memory` included, and rebuilds rules corpora only, and its
rebuild seam (`RulesCorpusService.reindex_from_sql`) refused the quarantined
package only after that deletion, so the refusal moved into `preflight`, keyed on
each published release's package UUID, release version and recorded
`transform_identity.transform_source_hash`, and it is scoped, so the replacement
corpus can still use this command; `scripts/retrieval_backfill.py` `out of scope`
(per-story retrieval memory, no rules-corpus release path);
`scripts/dump_openapi_schema.py`, `scripts/regen_table_inventory.py` and
`scripts/seed_e2e_entitlement.py` `already safe`, the admission mechanism being
that none of them reaches a corpus release, a rules-package publication or the
configured Chroma store: `seed_e2e_entitlement.py` writes entitlement rows only,
`regen_table_inventory.py` regenerates a committed JSON inventory, and
`dump_openapi_schema.py` points `AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY` at a
throwaway temporary directory before importing the app. Regression:
`test_the_baseline_reset_refuses_before_deleting_any_collection` runs the real
command against an isolated SQLite database holding a published quarantined release
and a sentinel file in the configured persist directory, and asserts the sentinel
survives.

`IngestionService.ingest`/`publish` and `_package_accessible` are the generic
`RulesPackageORM` lifecycle, which is shared with unrelated custom packages. The
guards there are identity-scoped, so a custom package publishes and reads
normally; only the quarantined UUID and the retired release version are refused.
`_package_accessible` is the single accessibility helper every by-id read routes
through, so the entity and override readers are covered by one guard rather than
six copies, and there is no enumeration method whose listing behaviour a raise
could change.

### 2.3 What is deliberately not guarded

`candidate_from_accepted_inputs` and `load_accepted_inputs(path)` read committed
bytes from a path. Reading a file claims nothing about authority, and the
quarantine is about authority, not about file access — reference material stays
readable, which is what the decision asks for ("temporary reference material, not
a second supported authority system"). Every seam that could turn those bytes
into something selected, published, activated, gated, or retrieved is guarded
above. The inverted tests in
`tests/ingestion/mechanical/test_accepted_inputs.py` and
`test_committed_accepted_authority.py` assert exactly this split, so it is a
tested boundary rather than an omission.

`persist_release` also carries no guard, and the admission mechanism is the
publication state it writes rather than a check on its argument: it writes
`publication_status="draft"` and nothing else (`persistence.py` lines 133 and
201). `"published"` is set at exactly two sites, lines 1453 and 1456, both inside
`_finalize_core`, which refuses a quarantined package at step 0 before any store
is read or written. The reuse path at line 1240 requires an already-`published`
row, which therefore cannot exist for a quarantined release. All six callers are
tests. So it is not a publication entry point: a draft row is not authority, and
the only transition out of draft is guarded.

`include_non_published=True` is **not** treated as reference access. It is a
lifecycle filter — it admits draft and retired rows — and this service has no
diagnostic or reference mode: every method behind it answers an authority question
about mechanical canon. Its only production references are
`services/context_builder.py` — line 189, the reader protocol's signature, and
line 417, which forwards `RuleSliceRequest.include_non_published` into slice
assembly — and the request model that defines the field (default `False`). No
production caller sets it, so there is no administrative consumer to preserve. Explicit reference access lives where §2.3 puts it: reading
committed bytes from a path, which the inverted tests pin. So the read guard
ignores the flag, and a draft read of the quarantined package is refused too.

`RuleOverrideORM` **writes** are `already safe`, and the admission mechanism is
that the row cannot be produced: no service method and no script constructs a
`RuleOverrideORM` anywhere in `src/` or `scripts/`, so there is no production path
that attaches an override to a quarantined package. Only the *reads* needed a
guard, and they route through `_package_accessible` with everything else.

Unrelated custom Rules Packages and story-memory functionality are untouched:
refusal is keyed to the quarantined identities, the retired transform recipe and
the named digests, never to a category of package. `IngestionService` still
ingests, publishes and reads an unrelated package end to end, which
`test_an_unrelated_package_still_publishes_and_reads` demonstrates on the exact
seams that now refuse.

### 2.4 Verification

`tests/test_quarantine_5c_5d.py` (43 tests) covers the refusal predicate, the
transform-recipe key under an alternative embedding configuration, the obsolete
ingestion command and the guarded baseline reset refusing before any migration,
store creation or collection deletion,
the generic
ingestion/publication/read guards against isolated SQLite, and the unrelated
custom package still publishing and reading.
`tests/ingestion/corpus/test_persistence_quarantine.py` proves the publication
path against **isolated** SQLite and Chroma stores: the refused call raises, and
afterwards there is no `RulesPackageORM` row, no `CorpusReleaseORM` row, and a
read-back vector count of zero. No shared database or Chroma collection was
reset or mutated at any point in this increment.

### 2.5 Skipped tests — retired versus still live

Retiring a successful-publication expectation for a product that may no longer be
published is legitimate; a shared behaviour that is still enabled is not covered
by skipping it. Both skip sites carry `QUARANTINED_RECONSTRUCTION`, and the
disposition differs per suite:

| Skipped behaviour | Disposition | Why |
|---|---|---|
| Corpus release finalization publishing successfully (`conftest.finalize_in_fresh_db`, `test_persistence_quarantine._finalize`) | **retired with the product** | The behaviour under test is publication of a release built by the retired transform. There is nothing left to cover: the expectation is that it is now refused, which `tests/test_quarantine_5c_5d.py` asserts positively. |
| Persist → reconstruct → digest → gate lifecycle *mechanics* on the compact corpus | **retired, obligation carried forward** | The machinery is generic and will be exercised again by the replacement transform. It is not covered while skipped, and the replacement stage owes it — see the obligations below. |
| Idempotent reuse of an already-published release | **retired, obligation carried forward** | Same machinery, same replacement-stage obligation. |
| Public completeness guard (`finalize_release` negative controls) | **still live, still running** | These never reach `_finalize_core`; they assert refusal-to-publish on an incomplete candidate and are unaffected. |
| Generic `RulesPackageORM` ingestion, publication and read behaviour | **still live, newly covered** | Shared with unrelated custom packages, so it was never a candidate for skipping. The new regression tests cover both sides: refused for the quarantined identity, unchanged for an unrelated one. |
| Mechanical publication gate and runtime binding over the *production* release (`tests/ingestion/mechanical/test_production_release.py`, `test_runtime_production_release.py`) | **retired, obligation carried forward** | These asserted the honest 5d state structurally: the gate refuses an incomplete projection per leaf, and the runtime path reports a *typed* `UNPUBLISHED` rather than an empty answer. Both behaviours are generic and stay enabled; only the release they ran against is retired. Obligation 5 below. |

Every skip is taken at the shared real-corpus fixture, not at an individual
assertion, so the map is per file. **The counts below are superseded by 8.6**:
the refusal has since moved from ``finalize_in_fresh_db`` to
``full_candidate``, which skips more tests, not fewer.

| Suite | Skips | Disposition |
|---|---|---|
| `tests/ingestion/corpus/test_persistence_quarantine.py` | 45 | retired with the product |
| `tests/ingestion/corpus/test_gate.py` | 18 | retired, obligation carried forward (1) |
| `tests/ingestion/corpus/test_ledger_pipeline.py` | 17 | retired, obligation carried forward (1) |
| `tests/ingestion/mechanical/test_production_release.py` | 8 | retired, obligation carried forward (5) |
| `tests/ingestion/corpus/test_baseline_reset_script.py` | 8 | retired, obligation carried forward (6) |
| `tests/ingestion/corpus/test_operational_contract.py` | 7 | retired, obligation carried forward (3) |
| `tests/ingestion/mechanical/test_runtime_production_release.py` | 6 | retired, obligation carried forward (5) |

The count: **109** skipped tests carry `QUARANTINED_RECONSTRUCTION` — every skip
in `tests/ingestion` and every quarantine-attributable skip in the suite. The
other 10 skips in the full run predate this work and are unrelated. No test count
was recovered by re-enabling retired authority, and no skip was converted back
into a passing test by weakening a guard; passing tests rose from 6,264 to 6,279
entirely through new refusal coverage.

**Operational coverage the replacement stage owes.** These are obligations, not
present coverage. When the replacement corpus is built:

1. The full persist → reconstruct → digest → gate → publish lifecycle must be
   exercised end to end against isolated SQLite and Chroma stores, as
   `finalize_in_fresh_db` did — including the rollback and compensation paths.
2. Idempotent reuse must be re-proven: a second finalization of the same release
   reuses rather than republishes.
3. The verified operational load (`load_verified_operational_corpus`) and the
   vector publication verification (`reindex_and_verify`, `verify_only`) must be
   run on fresh-corpus data; they are currently guarded, not exercised.
4. The replacement candidate must be asserted to carry a transform recipe hash
   that is **not** in `QUARANTINED_TRANSFORM_SOURCE_HASHES` — the successor to the
   weaker "different `package_uuid`" obligation (§2.1).
5. The 5d side owes publish → activate → runtime-resolve over the replacement
   corpus: the publication gate refusing an incomplete mechanical projection with
   per-leaf reporting, and the runtime binding path answering with a *typed*
   outcome (`UNPUBLISHED`, resolvable package reference, empty override state,
   typed-not-empty rule slice) rather than an absence. Nothing asserts this while
   the two `tests/ingestion/mechanical` production suites are skipped.
6. The baseline-reset preflight's digest-bound proof — expected vector logical
   state rebuilt from SQL, persisted-corpus digest recomputed and compared to the
   digest recorded at publication — must be re-exercised against a genuinely
   proof-bound replacement corpus. The command itself now refuses quarantined
   releases before opening the store (§2.2), but that guard is not a substitute
   for the proof it protects.

## 3. Pinned community source

| | |
|---|---|
| Upstream | `downfallx/dnd-5e-srd-markdown` |
| Commit | `1b4b99dcb786cdd1a2fb26f8acec1551191f1ca4` |
| Vendored | 16 files, 1,893,352 bytes; all 21 upstream tracked files recorded |
| Status | **qualified** — compared against the PDF and corrected where the passes found defects (§7); the final source boundary was reviewed independently at `b70d016` (`source-structure-final-review.md`). Qualification is of these bytes against the official document; it never makes them a rules authority and is not a semantic acceptance |
| Corrections | 20 across 4 files; 1 preserved official defect; 1 controlled addition |
| Licence | upstream `LICENSE` vendored verbatim; CC BY 4.0 attribution travels with any derived corpus |

Manifest digests are of the **upstream Git blobs**, and
`docs/sources/community/dnd-5e-srd-markdown/** -text` in `.gitattributes` stops
any checkout rewriting them. The first vendoring pass copied from a Windows
worktree with `core.autocrlf=true`, which produced CRLF files whose digests would
have verified on that machine and failed in CI; a pin that holds on one platform
is not a pin. `tests/test_pinned_community_source.py` (37 tests) re-hashes every
vendored file, asserts no vendored file contains CRLF, and asserts the manifest
states what its digests are of.

The official PDF remains the source authority:
`docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf`, sha256
`8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87`, 6,031,375
bytes, 364 pages. A differing checksum is a discrepancy to resolve, never a
number to update.

## 4. PDF comparison pass

### 4.1 The instrument

`community_compare.py` compares compacted **character windows** of 48 characters
in both directions. Normalization is the repository's frozen
`policy.compact` (`nfkc-ws-1`), which folds ligatures, the minus sign and
typographic punctuation, then removes whitespace and hyphens and case-folds.

**The normalization is not content-preserving, and this instrument cannot see what
it removes.** Folding the minus sign to a hyphen and then deleting hyphens erases
the sign: `modifier −2` and `modifier 2` compact to the same string and compare
equal. Bullet glyphs and footnote asterisks are dropped from both sides by design.
So a matched window proves the *remaining* characters are adjacent in both
sources; it does not prove a sign, a bullet or a footnote marker survived the
snapshot. An earlier version of this section, and of the module docstring, claimed
losslessness — that claim was wrong and is withdrawn; sign, number and qualifier
differences remain pending (§4.6), and
`test_the_normalization_erases_a_minus_sign` pins the counterexample.

Removing whitespace is what makes the comparison usable rather than a source of
false alarms: the PDF renders small-caps ability abbreviations as `S tr`,
hyphenates across line ends, and flows two columns. Reading order comes from the
existing `pdf_source.extract_pages` recipe (`extract_words(use_text_flow=True)`,
`pdfplumber 0.11.10`), which follows this document's authored content stream and
was confirmed by inspection to read pages 9, 10, 26, 92 and 344 in correct column
order, including full-width tables and monster stat blocks.

Two glyph classes are dropped from **both** sides: the PDF's bullet glyph and
table footnote asterisk are markup on the Markdown side. Dropping them from the
Markdown alone made every bulleted list and every footnoted table read as absent
while all of their words were present — a 0.4 percentage-point artefact that was
found and removed before any number here was recorded.

### 4.2 The noise floor is a reporting threshold, not a clearance

Where **one isolated** joint is the only difference — the PDF flows a table header
straight on from the sentence above it, the snapshot separates them with markup —
the only unmatched windows are those straddling that joint, so the run cannot
exceed `2 × WINDOW − 1` = 95 characters. `NOISE_FLOOR` = `2 × WINDOW` = 96 is
derived from that single-junction case.

**The bound is not universal, and an earlier version of this section overstated
it.** It said that at or above the floor at least one character is genuinely
absent. That is false in the other direction as well as this one: two nearby
junctions merge into one longer run, and pure reordering with no character absent
at all can exceed the floor.
`test_two_nearby_junctions_merge_into_a_run_over_the_floor` demonstrates a
134-character run between two strings with *identical* character multisets. The
floor is therefore a **reporting threshold**: at or above it a run is worth
reading, and below it the instrument cannot separate a real omission from its own
artefacts. A run below the floor is **unresolved, not harmless** — which is why
the sub-floor verdict is named `below_floor_unresolved` and the evidence record now
counts sub-floor runs and characters instead of implying they were cleared.

The Owner-supplied positive controls are still measured. Printed page 26
(Multiclass Spellcaster) matches **completely** — no unmatched window at all.
Pages 9–10 (Actions) produce runs of 93 and 60 characters, both exactly such
junctions. The tests re-measure this, so a degraded instrument fails a control
instead of the floor quietly rising.

### 4.3 Coverage — all 364 pages

| | |
|---|---|
| Pages compared | 364 of 364 |
| Window coverage, whole document | **96.435%** (1,068,470 / 1,107,973) |
| Window coverage, excluding front matter | **99.131%** (1,068,470 / 1,077,833) |
| Pages with no unmatched window at all | **269 of 364** |
| Runs at or above the floor | 54 (37,305 characters) |
| — of those, front matter | 4 (30,328 characters) |
| — of those, document body | **50 (6,977 characters)** |
| Runs below the floor (unresolved, not cleared) | 112 (10,000 characters) |

Front matter is printed pages 1–4: the licence notice and the three-page table of
contents with its dot leaders. No Markdown file claims to represent a page-number
index, so counting those 30,140 windows as missing rules content would understate
coverage — and dropping them silently would overstate it. Both figures are
reported, and the front-matter runs remain in the evidence file.

The running header/footer (`N System Reference Document 5.2.1`) is stripped
before comparison and counted: 364 lines, one per page. It is a systematic
non-discrepancy, not 364 findings.

### 4.4 Discrepancies — what the 50 body runs are

Every run is recorded with its page, length and a 240-character excerpt in
`issue-5c-5d-community-source-coverage.json`. Reading them:

These groupings are signals read off the excerpts, not a partition: they overlap,
and two of them are mechanical tests rather than structural findings.

* **35 runs (4,399 characters)** contain an internally repeated ≥10-character
  substring. That is *consistent with* the PDF repeating a table's header row
  where the table continues into the next column or page, which the snapshot
  writes once — but the test fires on repeated **vocabulary**, not on structure,
  so it is not a classification. Page 31's 110-character run repeats
  `proficienci`; the spell-list runs repeat `transmutation`. Each still needs
  reading before anything is concluded about it.
* **6 runs (652 characters)** carry a quoted `(see "…")` cross-reference the
  snapshot writes differently — pages 7 (twice), 31 (twice), 49 and 204. **Five
  of these six also sit inside the 35 above**, which is the clearest evidence
  that the repeated-substring test is a signal and not a bucket.
* **12 runs** sit at a table-header or random-table row boundary without a repeat
  inside the excerpt window: class progression headers (pages 31, 53, 65, 77),
  two-up cost and reference tables (pages 95, 101, 102, 202), `1d100` result
  tables (pages 27, 225), and weapon-property run-in headings (page 90).
* **2 runs** are the largest and were checked individually — the only two traced
  to their snapshot content rather than classified by signature. Page 176's
  abbreviation glossary (560 characters) and page 179's creature-type
  enumeration (178 characters) are both present in `rules-glossary.md` as HTML
  tables; the PDF's two-up column flow serialises them in a different order.

**No run evidences absent rules prose.** That is the finding that supports
continuation, and it survives the overlap above: it rests on every excerpt having
been read, not on the grouping. It is a reading of the recorded evidence, not a
proof — only the two largest were traced to their snapshot content, and the other
48 rest on signature and page inspection.

In the other direction, the snapshot carries **36 runs (5,788 characters)** of
text absent from the document, across 9 of the 13 content files — heading and
navigation scaffolding among it. Each still needs reading before the source can be
qualified. Reported per file in the evidence record.

### 4.5 Named checks

All 11 Owner-named regions were run. Ten report
`below_floor_unresolved`; **`sorcerer-lists` (pages 67–68) reports
`discrepancy`** at 112 characters, which reading identifies as a repeated
`Spell School Special` header where the spell table continues across the column.
The `rarity-value-and-command-word` family flagged at 107 characters until the
footnote-asterisk asymmetry was fixed; it now sits at 94, below the floor.

Every check carries `table_association_checked: false`. There are only two
verdicts, `discrepancy` and `below_floor_unresolved`, and neither is a pass: below
the floor the instrument cannot separate a real omission from its own artefacts,
so a region under it is **not cleared**. The verdict was previously named
`prose_within_noise_floor`, which read as the very clearance the paragraph denied;
renaming it was part of this correction.

### 4.6 What is explicitly pending

> Read as of the comparison increment. §7 is the source-qualification
> increment and answers each item below, but not all of them to the same
> depth, so §7 says for each what was scanned mechanically over the whole
> source and what was read in particular places. Record ownership is the item
> that took two attempts: the first pass at §7 reported heading *counts* and
> contents-entry *titles*, neither of which can see which entry a heading
> owns, and six mis-nested stat blocks survived it. That is corrected and has
> its own pass now. The list stands as written because it records what the
> comparison could and could not see, which is what makes §7 reviewable.

* **Table row and column association is not checked at all.** Compaction removes
  whitespace, which is what makes the comparison work and also fuses one cell's
  text to the next. A matched window proves character adjacency; it does not
  prove the snapshot puts 13 in Chain Shirt's AC column rather than its cost
  column. `colspan` cells, empty cells and repeated ability-grid headers are
  untouched by this pass. The 579 embedded tables are inventoried, not qualified.
* **Record ownership is not checked.** Which stat block or entry a table or
  paragraph belongs to is invisible to a character-window comparison: two
  adjacent creature entries read as one continuous stream, so nothing here
  distinguishes an Archelon trait from a Baboon trait on the same spread. This
  is the same missing dimension as row and column association and belongs to the
  same structural pass.
* **Sign, number and qualifier differences are not checked.** The normalization
  erases the minus sign (§4.1), so a bonus written `+2` where the PDF says `−2`
  would not register. Digits and words survive compaction and would show up as
  unmatched windows, but only if the difference is long enough to clear the
  reporting threshold — `1d4` for `1d6` is three characters inside a matched
  neighbourhood.
* **Runs below the floor are unresolved, not cleared.** There are 112 of them
  covering 10,000 characters, now counted in the evidence record
  (`runs_below_floor`, `chars_below_floor`) rather than left implicit. Counts
  only: the excerpts would balloon the record without being readable, and
  qualification re-derives them.
* **The 36 community-addition runs are recorded, not adjudicated.**
* **The official document's printed page 1 is attributed, not qualified.** The
  licence notice is front matter excluded from the body figure; it is a distinct
  question from the three-page table of contents and is not answered here.
* **No region is qualified.** Full-source qualification needs the structural pass;
  this increment supports continuation toward it and claims nothing more.

## 5. Gates

Every completed result is retained at
`.claude/review-notes/issue-5c-5d-clean-restart-gates.md`. This increment: Black
reformatted 2 of 499 files (committed), Ruff clean, mypy strict success on 229
files, and 6,279 tests passed with 119 skipped across two attached halves
(2,856 + 3,423 passed; 10 + 109 skipped), plus the detect-secrets hook and the
pip-audit findings. Local
`pip-audit` reports 24 pre-existing vulnerabilities in 10 packages unrelated to
this work and distinct from the clean CI audit; it is not introduced or altered
here. The detect-secrets hook exits 0 after registering one new public checksum
by additive splice. Total-suite coverage was **not** re-measured in this
remediation — the two halves emitted no coverage summary, so the
`--cov-fail-under=80` addopts gate did not run; the figure below is a targeted
measurement, and the last whole-suite number is the previous increment's 92.45%.

Coverage of the changed modules, measured over
`tests/test_quarantine_5c_5d.py`, `tests/ingestion/source/test_community_compare.py`,
`tests/ingestion/test_ingestion.py`, `tests/services/test_rules_package.py` and
`tests/ingestion/corpus`: `quarantine.py` 35/35 and `community_compare.py`
119/119 — **100%**; `ingestion_service.py` **99%** (2 pre-existing lines: a
package-not-found raise and an empty-rows early return); `rules_package.py`
**92%**. Two notes on what is *not* covered. `rules_package.py` lines 487–501 are
the slug branch of `resolve_slice_package`, whose guard is defence in depth: the
`resolve_package_reference` delegate it calls refuses a quarantined slug first,
and that refusal *is* covered
(`test_package_reference_resolution_refuses_the_slug_form`). `persistence.py`
reports 19% because the retired finalization suite is skipped (§2.5); its changed
lines — the step-0 `refuse_quarantined` block at 1123–1136 — are covered by the
`_finalize_core` refusal tests. All new code is above the 80% minimum.

## 6. Remaining boundaries

1. **The replacement corpus must be built by a transform whose recipe hash is not
   in `QUARANTINED_TRANSFORM_SOURCE_HASHES`.** Assert that when the transform is
   chosen (§2.1). A different `package_uuid` is necessary but not sufficient: an
   incidental reconfiguration produces one without replacing anything.
2. **Source qualification is done and is recorded in §7.** Sign, number and
   qualifier differences, table row and column association, record ownership,
   the community additions and printed page 1 are each answered there, each
   with the extent of the check stated. What is qualified is the source: these
   bytes against the official PDF. A corpus built from them is a separate
   question and is qualified on its own evidence — the ingestion reading this
   source is not what makes the source good, and qualification does not wait
   on it.
3. **Coherent replacement 5c ingestion and citations are the next increment**,
   and are gated on this source boundary being reviewed. `legal-information.md`
   is outside `CONTENT_FILES`, so that increment has to pick it up explicitly or
   the required attribution will not travel with the corpus.
4. **Retirement of the superseded work is a later increment.** Historical
   descriptions in `oracle.py`, `MANIFEST.in`, `oracles/README.md` and
   `known_unknowns.md` are annotated as quarantined, not rewritten, because they
   still record what is being replaced.
5. **External issue synchronization text is prepared locally and not posted**, per
   the operating boundary.

## 7. Source qualification

The comparison increment (§4) measured the snapshot with one instrument and
listed what that instrument could not see (§4.6). This increment answers each
of those items and corrects what they exposed. Two records carry it:

| | |
|---|---|
| Coverage and dispositions | `docs/architecture/issue-5c-5d-community-source-coverage.json` |
| Correction notes and sibling audit | `docs/architecture/issue-5c-5d-community-source-corrections.md` |
| Regenerated by | `venv/Scripts/python.exe scripts/regen_community_source_coverage.py` |

### 7.1 The second pass

`src/afterworlds/ingestion/source/community_tokens.py` compares the same 364
pages by **token**, keeping the minus sign the window pass folds away, and
partitions the snapshot so every page's text is read against the official page
it belongs to. It reports per page the multiset of tokens each side holds that
the other does not — which is order-immune, so a two-column page does not
register as a difference.

`number_order` is the seam between the two. It keeps this pass's tokens and
reads them in sequence, which is what separates a table header the document
repeats at a page break from a table row lost under it. That distinction found
the one omission the multiset pass let through (§7.3, correction E).

Structure is read directly from the Markdown rather than through either pass:
`tests/ingestion/source/test_community_source_structure.py` checks every
table's column count, every ability grid's cell order, and recomputes every
modifier from its score — a check that is blind to the glyph by construction,
so a swapped pair of cells fails it even when both sides hold the same
characters.

Record ownership needed a third reading, and needed it for a structural
reason. Both comparison passes are blind to heading marks by construction: a
`#` is not a token the official page prints and not a number, so a stat block
emitted at its owning entry's depth compares as identical content while, in
Markdown, it has ended that entry and taken every entry after it. Heading
counts cannot see this either — the count is the same whichever depth the
heading carries — and neither can the official contents, which lists sections
and says nothing about depth or ownership. The ownership pass reads the depth
stack directly and reports, for every heading and every line of prose, the
entry it resolves to. Review found family G (§7.3); this pass is what
bounds it, to exactly six blocks, each now nested below the entry that owns it.
The pass reports the depths; it does not certify that the resolved owner is the
right one. That was read from the official pages and the six blocks are named in
the corrections notes. An earlier version of the generator also reported a count
of blocks at or above their owner's depth, which could only ever be zero because
the owner is selected as the nearest *shallower* heading; the counter is removed
rather than reworded.

### 7.2 What was covered

| | |
|---|---|
| Official pages compared | 364 (360 body, 4 front matter) |
| Body pages quiet in the token pass | 290 |
| Body pages with residue, each read | 70, in five named families |
| Body pages with identical numeric-token order | 296 |
| Body pages read because their number order differs | 64 |
| Snapshot characters assigned to an official page | 1,094,337 of 1,094,337 — no gaps |
| Official contents entries whose title matches some heading | 477 of 481; the other four dispositioned individually. Title presence only — this says nothing about a heading's depth or what it owns |
| Headings in the source | 2,876 across 13 files, each resolved to the entry that owns it. Read as 2,875 until the replacement front end found that an anchored `^#` misses `spells.md`'s own title, which a byte-order mark precedes |
| Stat blocks, found by their own AC and HP | 336; 6 embedded in a non-creature entry, each block's depth and its resolved owner's depth reported per block |
| Tables / ragged tables | 579 / 0 |
| Ability grids / ability rows | 333 / 672 |
| Score-to-modifier triples / mismatches | 2,016 / 0 |

The span partition is what makes an unanchored window-pass run an alignment
limit of that pass rather than unexamined content: every character of the
snapshot belongs to exactly one official page and was compared there.

Every figure above except one is a full mechanical scan, so its count is a
count of everything of that kind in the source. The exception is the contents
row, which is a representative read: 481 titles checked for presence, out of
several thousand headings. The coverage record separates the two under
`qualification.scope`, and the corrections notes' sibling audit lists the
direct page renderings — the correction and residue pages, not all 364 — as
reads rather than scans.

### 7.3 What was corrected

Twenty edits across four files, in seven families: ragged feature-table rows,
mislabelled MOD/SAVE legends, merged or missing ability-grid cells, paragraphs
split at a printed column break, one table row lost under a header repeated at
a page break, one clause the official page does not print, and six stat blocks
emitted at the depth of the entry that summons them. Upstream digests are
preserved beside the corrected ones in the manifest, so each edit reads as a
transition rather than as a silently rewritten expectation.

Family G is the one that changes how the source must be read. A heading closes
every open section at its own depth or above, so `## Draconic Spirit` inside
the Summon Dragon spell took Sunbeam through Zone of Truth with it, and an
`### Actions` under a `####` magic item took Necklace of Adaptation and every
remaining item in the file into the Avatar of Death's action list. Each block
is now one level below its entry and its labels one level below the block,
which is the nesting the creature files already use. The Giant Fly also moved,
unchanged, to the end of the Figurine of Wondrous Power entry, because
official p.222 sets it beside the entry and the figurine variants printed past
it are the entry's own text. The point of the family is that a consumer
reading heading depth now gets the official document's answer without any
special knowledge of where the conversion went wrong.

Two places where the official document itself reads oddly are kept as anomaly
notes: the Telekinesis truncation on p.168 and the Young White Dragon's
unsigned INT save on p.340. Both pages were rendered from the pinned PDF and
read directly, and both were rendered and read again independently in review;
the PDF prints them as the snapshot holds them. Matching the PDF is what a
source-stage qualification requires, so both are settled at this stage on the
evidence. Neither is a judgement that the content is correct, and neither asks
anything of a later runtime, which reads the Rules Package. Both are in the
corrections notes.

One controlled addition, `legal-information.md`, reproduces official page 1 and
carries the required attribution. It compacts identically to that page and is
asserted to.

### 7.4 What is not claimed

This is source qualification. It is not ingestion, not citations, not fresh 5d
authoring, and not a semantic acceptance of anything. The token and number passes
compare bags and sequences of what each side prints, which is why neither can
certify that a value sits in the right cell, that a passage belongs to the record
beside it, or that two sources read a table in the same order. Those are answered
by the structure scan, the ownership pass and the pages that were rendered and
read — never by a coverage fraction or a token count on its own. The community snapshot
stays the single controlled source: no second canonical source was created, and
no expected upstream digest was overwritten in place.


## 8. Replacement 5c construction

The second increment. The corrected, independently reviewed community snapshot
is cut into a logical corpus, every unit is cited to an official PDF page, and
the release is proven through the real publication lifecycle in isolated stores.
The PDF is the citation target and the `authoritative_source_hash`; it is not
read for structure. 5c owns faithful source structure. Interpretation is 5d's,
and nothing here begins it.

### 8.1 The corpus and its identity

| | |
|---|---|
| Source | `docs/sources/community/dnd-5e-srd-markdown/`, the 14 corpus files (13 content files plus the controlled `legal-information.md`, so attribution travels with the corpus), each digest-pinned in `transform_config` against the pin manifest; the pin directory's other entries are the manifest, licence and changelog, which carry no units |
| Official PDF | `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87`, 364 pages |
| Units / leaves | 10,465 |
| Chunks | 10,465 (one chunk per unit, each carrying its own citation) |
| Package UUID | `9717e288-c099-5217-b2d2-f89aeabd7b73` |
| Release version | `5.2.1-corpus.883aabdf-462` |
| `transform_config_hash` | `08cbcb4f9b1bb86a272def982a6f3416e200d227f1e4beda0c116ad70f8d0155` |
| Frozen source ledger hash | `301a1d6a502789f3e905b050072be91cc77e86517991196fdc14c8b5024bdaf4` |
| Bundle root hash | `c3b3668bb7dc5220eee9e7191008cfe92103b7e5eb6e003e97eebc7708f50cf1` |
| Evidence report schema | `5c-evidence-4` |
| Embedding documents | 11,076 bounded windows derived from the 10,465 chunks; 499 chunks need more than one window, the rest are sent whole (§8.8) |
| Transform version | `SOURCE_TRANSFORM_VERSION = "3"` |

`SOURCE_TRANSFORM_VERSION` went to 2 deliberately. Two corpus changes in this
increment — `section_label` becoming the whole heading stack rather than the
nearest heading, and `occurrence_index` becoming the global emission order —
are not `transform_config` inputs, so without the bump the changed corpus would
have minted the *same* `package_uuid` and `release_version` as the output it
replaces. Same inputs still mean the same release; a changed recipe now means a
new one.

It went to 3 for the same reason, and the identity above is this increment's—
not the one recorded before it. Two more changes that are not `transform_config`
inputs landed together: a table's caption above it and its footnote below it now
merge into the table's own unit (§8.8.1), and the embedding input is derived as
bounded windows rather than sent whole (§8.8.2). The first changes the units;
the second changes the vector projection. Either alone would have minted the same
package UUID and release version as the output it replaces.

The identity above moved once more, and this time **without** a version bump,
which is the mechanism working rather than an omission. The family-H source
correction (§8.10) changed one byte of `rules-glossary.md`, and the pin
manifest's per-file digest is inside `SOURCE_PIN` in the transform config, so
`derive_package_uuid` and `derive_release_version` both minted a new identity
from the changed digest. `SOURCE_TRANSFORM_VERSION` stays at 3: the recipe did
not change, the input did. The bumps above exist for changes the config could
*not* see; a changed source byte is one it does see.

### 8.2 Citation mapping, honestly accounted

The partition is the citation mapper. Each snapshot file is cut into contiguous
per-official-page regions; a 48-character window that occurs on exactly one
official page anchors a position, the longest non-decreasing run of anchors is
kept, and an unanchored position inherits the page of its nearest anchor.
Citation is a lookup, not a search.

The pass's own accounting now rides the candidate into the evidence report as
`source_citation_mapping` rather than being computed to gate the build and then
discarded:

| | |
|---|---|
| Units | 10,465 |
| Anchored on wording unique to one official page | 10,036 |
| Placed by their file's document order (inherited) | 429 |
| Unresolved | 0 |
| Printed across a page break (multi-page) | 165 |
| Distinct official pages cited | 361 |
| Body pages nothing cites | 0 |

The 429 inherited units are correct citations resting on weaker evidence, and
the report says so rather than presenting one undifferentiated pass. An earlier
draft of this work claimed they were all `### Actions` headings; that claim was
tested and is false. Measured over the compacted unit text: 344 are shorter than
the 48-character uniqueness window, 72 more are repeated verbatim elsewhere in
the corpus, and 13 are neither. Short or repeated wording cannot identify one
page, which is the whole reason the anchor run exists. The breakdown is
re-measured here: an earlier draft of this section reported 314/92/23, which the
same probe no longer reproduces on the current corpus, and the three figures
still sum to 429.

A unit printed across a page break cites the range. `Leaf.printed_page` carries
the **primary** page only; the full range lives in the `UnitCitation.pages`
tuple and in the chunk's `source_locator_value` (`pp. 9-10`), which is what the
consumer is served and what the verification re-derives. Page geometry is never
reconstructed downstream.

### 8.3 What the source-partition verification proves, and what it does not

`verify_source_partition` re-derives the whole corpus from the digest-verified
pinned bytes plus fresh PDF pages and requires a bijection — multiset equality
on `(compact(content), section_label, locator_value)`. Missing source texts are
a failure, never a pass.

It does not prove chunk **order**. The comparison is order-blind by
construction, so a reordering that left the multiset unchanged would pass here.
Order is bound by `bundle_root_hash` and restored on reconstruction by sorting
on `Leaf.occurrence_index`, which is why that field is a total emission order
and why a regression test pins it: `persistence._load_members` sorts the rebuilt
chunks by their first leaf's index, so a per-file or per-duplicate counter reads
plausibly and silently moves the bundle root away from the one the release was
published under.

Token bags alone cannot certify association or order. Nothing here is a general
proof engine, and none was built.

### 8.4 The page claim a persisted leaf can satisfy

A defect the new lifecycle suite found and this increment fixes. The reuse-path
completeness check reads `LedgerLeafORM.printed_page` — one page per leaf — but
the release recorded every page any unit *cited*: 361, including the
continuation pages of the 165 multi-page units. Page 27 carries only the
continuation of a unit that starts on page 26, so no leaf is ever filed there.
A fresh publish succeeded and its own reuse then failed with `persisted ledger
omits authoritative printed pages [27]`, meaning the release could never
re-verify itself after a restart.

The recorded claim is now `leaf_primary_pages` (360 pages), read by
`expected_leaf_pages`, which is what that column can express. This is strictly
stronger than what it replaces: an unsatisfiable expectation is a wall, not a
check. It is also deliberately narrower than the full citation, and
`verify_persisted_page_coverage` now says so in its own docstring — the
continuation pages are proven by re-deriving the corpus, not by this coarse
backstop.

### 8.5 Lifecycle and integrity coverage restored

The §2.5 obligations 1–4 are discharged against the replacement corpus, not the
retired one. `tests/ingestion/corpus/test_source_lifecycle.py` (12 tests) drives
the real `finalize_source_release` into a fresh SQLite database and a private
on-disk Chroma store:

| §2.5 obligation | Restored as |
|---|---|
| (1) full persist → reconstruct → digest → gate → publish, incl. rollback and compensation | `test_the_source_corpus_publishes_through_the_real_gate`; `test_a_failure_inside_the_publication_window_leaves_neither_store_written` (a gate failure mid-window leaves no release, package or chunk row and an empty collection, and the retry then publishes) |
| (2) idempotent reuse | `test_publishing_the_same_inputs_again_is_a_verified_no_op`; `test_reuse_refuses_a_release_whose_persisted_chunk_was_tampered_with` — reuse re-runs the full gate against the reconstructed state, so it is *verified*, not merely recognized |
| (3) verified operational load on fresh-corpus data | `test_the_operational_read_path_identifies_this_release_and_no_other` |
| (4) recipe hash not in `QUARANTINED_TRANSFORM_SOURCE_HASHES` | `test_source_release.test_the_candidate_is_not_the_quarantined_transform` |
| (5) 5d publish → activate → runtime-resolve | **still pending**, explicitly deferred to that stage |
| (6) baseline-reset preflight digest proof | `tests/ingestion/corpus/test_source_baseline_reset.py` (8 tests) — the replacement corpus published through the real `finalize_source_release` into a file-backed SQLite database, then `scripts/reset_corpus_baseline.py::main` driven over it with the destructive steps recorded rather than performed (§8.8.3) |

Corruption, omission and wrong-input refusal are covered on both the direct and
the persisted path: a tampered persisted chunk fails the re-derivation twice
over (its text matches no source unit, and the unit it carried is now carried by
nothing), a reassigned locator moves the release digest, an omitted chunk is
reported as an uncarried source unit, a release declaring the wrong verification
never reaches a store, stale source bytes are refused, and a changed recipe
mints a new release rather than colliding.

The quarantine refusal moved. `finalize_in_fresh_db` is shared lifecycle
machinery; what the Recorded Owner Decision retires is the PDF-geometric
*transform*. The skip therefore lives on `full_candidate` — the single point
where that recipe enters a test — and the source-built corpus finalizes through
the helper for real.

### 8.6 Skip accounting after the move

`tests/ingestion` with the two retrieval suites this increment adds to (`tests/pipeline/retrieval`, `tests/models/test_retrieval.py`): **3,654 passed, 131 skipped** in 14:31. The skip total is unchanged — this increment neither added nor removed one, and every skip still carries
`QUARANTINED_RECONSTRUCTION`.

| Suite | Skips | Disposition |
|---|---|---|
| `test_persistence_quarantine.py` | 52 | retired with the product |
| `test_gate.py` | 18 | retired; obligations (1)(2) restored in `test_source_lifecycle.py` |
| `test_ledger_pipeline.py` | 17 | retired; the replacement pipeline is covered by `test_source_units.py` and `test_source_release.py` |
| `test_tables.py` | 9 | **newly skipped** — asserts PDF table *reconstruction*, which the new transform does not perform |
| `test_production_release.py` | 8 | retired, obligation (5), 5d stage |
| `test_baseline_reset_script.py` | 8 | retired fixture; obligation (6) restored against the replacement corpus in `test_source_baseline_reset.py` (§8.8.3) |
| `test_operational_contract.py` | 7 | retired; obligation (3) restored in `test_source_lifecycle.py` |
| `test_runtime_production_release.py` | 6 | retired, obligation (5), 5d stage |
| `test_table_inventory.py` | 6 | **newly skipped** — grades the live reconstruction against the frozen table inventory; `finalize_source_release` deliberately does not run that oracle |

The per-file table in §2.5 is superseded by this one, and the whole +22 is
this increment's, not a carried-over discrepancy. The refusal used to be
raised inside `finalize_in_fresh_db`, so it fired only for a test that
actually finalized; it is now raised in the `full_candidate` fixture, so it
fires for every test that so much as builds the PDF-geometric candidate. That
is why `tests/ingestion` went 109 → 131: `test_tables.py` 0 → 9,
`test_table_inventory.py` 0 → 6, and `test_persistence_quarantine.py` 45 → 52,
the last being seven tests that use the retired candidate without finalizing
it. The move is deliberate and the wider skip is the honest one: those tests
assert about the retired transform's output whether or not they publish it.
An earlier draft of this section blamed the 45 → 52 on `a8de466`; that does not
survive the commit order — `d817dd4`, which recorded 45, was written after
`a8de466`, and the test file is unchanged since. The arithmetic above is the
actual cause.

Two suites were checked and deliberately **kept live** rather than lost to the
fixture move. `test_source_completeness.py` (7 tests) asserts about the PDF
*extraction*, which `finalize_source_release` still runs on the pages its
citations point at, so it was repointed at the source-built candidate's pages.
`test_tables.py` and `test_table_inventory.py` were checked the same way and
genuinely do grade retired machinery: `detect_page_tables`,
`build_table_inventory` and `check_against_committed_inventory` are reached by
no live path in the source build, and the new `transform_config` deliberately
carries no `expected_table_inventory_hash`. No skip was converted into a pass by
weakening a guard, and no test count was recovered by re-enabling retired
authority.

Coverage of the new modules, measured on `tests/ingestion/corpus` with
`--cov=afterworlds.ingestion.corpus`: `source_units.py` 98%,
`source_citations.py` 95%, `source_ledger.py` 94%, `report.py` 94%,
`pipeline.py` 82%, `persistence.py` 81%. Each clears the 80% floor on its own.
Increment 5's changed modules, measured on the run above: `corpus_windows.py` 90%, `models/retrieval.py` 100%, `rules_corpus_service.py` 96%, `vector_publication.py` 98%, `source_units.py` 98%, `source_ledger.py` 94%, `persistence.py` 82%.
The package total is 76%, pulled down by the retired machinery whose suites are
now skipped (`tables.py` 27%, `ledger.py` 26%); that is the arithmetic
consequence of retiring the product those lines belong to, reported rather than
smoothed over. The whole suite was re-measured for increment 5, with
coverage and the configured floor: **6,395 passed, 141 skipped, 0 failed** in
21:30, total coverage **92.20%** against the 80% floor. That is the current
figure and it supersedes the 92.50% of increments 2 and 3 as the latest
measurement — it does not correct them. The 92.45% in §5 is increment 1's
figure and is correct where it stands, because §5 records the quarantine
remediation, which came before both.

### 8.7 Consumer behavior and unresolved boundaries

1. **Oversized units and the production embedder** — **resolved**, §8.8.2.
   The suspicion was correct: the installed embedding function truncates at
   256 tokens, 494 of the 10,465 units exceeded it, and the embedding input is
   now derived as bounded windows. The measurement, the fix and its named
   ceiling are recorded there.
2. **Obligation (5) stays open** — 5d publication/activation/runtime.
   Obligation (6) is discharged (§8.8.3).
3. **No production publication or activation happened.** Every publication in
   this increment is into a throwaway SQLite database and a private Chroma
   directory. The shared stores are untouched, and the corpus is not selectable.
4. **`pip-audit` is not green** and is not made green here. Re-measured for
   increment 5 in this repository's `venv` (pip-audit 2.10.0, exit 1):
   **31 known vulnerabilities in 11 packages**, `afterworlds` itself skipped as
   not on PyPI. That is the same 31-in-11 increment 2 recorded and Codex's
   review reported; increment 1's 24-in-10 was measured earlier against
   whatever advisories existed then, and the cause of the difference is not
   established here. Every finding is in a transitive dependency unrelated to
   this work — `pip` (8), `chromadb` (5), `urllib3` (4), `setuptools`,
   `msgpack`, `mako`, `idna`, `cryptography`, `anyio`, `click` and
   `pydantic-settings`. No suppression, no `--fix`, no unrelated environment
   maintenance.

### 8.8 Increment 5: retrieval reachability and the baseline reset

Three engineering families, settled against the authorities already in force
and taken one commit each. The corpus content is unchanged wording; what changed
is which unit a note belongs to, what text is sent to the embedder, and one
operational call site.

#### 8.8.1 A table's note belongs to the table (`d0c59dd`)

`build_structure` ended a table unit at `</table>` and merged only the caption
above it, so `Magic Item Rarities and Values` (unit 3103, p. 206) was served as
one unit and the rule that gives its starred values meaning — *Halve the value
for a consumable item* — as the next. Sharing a section label does not make a
retrieval carry them together: a consumer served the table alone reads a price
list whose footnote marker resolves to nothing.

A footnote below a table now merges into that table's unit, alongside the
caption above it. The family was closed by classifying every block that follows
a `</table>`: 5 footnotes, 374 other prose blocks, 183 headings, 15 further
tables, 2 end-of-file — so exactly five units in the corpus were affected, all
five patched by the one change. The four siblings the review named are among
them (languages p. 20, travel pace p. 192, crafting p. 207, Deck of Illusions
p. 218), with magic-item rarities the fifth. Markers are `*`, `†`, `‡`; `**`
and `††` are excluded, being emphasis rather than a footnote mark. Merging is
of *adjacent* blocks, so spans stay contiguous and the tiling assertion
(`"".join(pieces) == whole`) still holds — the completeness guarantee is not
weakened to buy the merge. Units 10,470 — 10,465.

#### 8.8.2 The embedding input is bounded (`864d65d`)

The installed default embedding function truncates its own input:
`chromadb/utils/embedding_functions/onnx_mini_lm_l6_v2.py` calls
`tokenizer.enable_truncation(max_length=256)` before encoding, and
`resolve_default_embedding_function` returns exactly that function in
production. `RulesCorpusService.reindex_from_sql` sent `row.content` whole, so
494 of the 10,465 units were embedded from their opening alone: Weapons is 2,865
tokens and stopped at character 644 of 7,154; the Bard progression table stopped
at character 671 of 6,478. Read-back verification could not see it — the stored
document and its hash are complete either way — and the deterministic fake used
by the lifecycle suite has no ceiling at all, which is why publishing passed.

`pipeline/retrieval/corpus_windows.py` now derives the embedding input:
markup becomes whitespace (a `<td>` boundary carries nothing an embedding can
use, and stripping the table tags alone takes the over-ceiling count from 494 to
24), and the visible text is packed into windows of at most 448 characters,
breaking on block boundaries so a table row stays whole, each prefixed with the
chunk's section label so a window from the middle of a long unit still says what
it is about. 11,076 documents for 10,465 chunks, 499 of which need more than
one. (Those two figures were 11,077 and 500 before the family-H source
correction: a window's budget is shared with its section-label prefix, and
dropping `Swim Speed` from 47 units' label stacks left one of them fitting in a
single window. Measured, not predicted — see §8.10.)

* **The stored unit is untouched.** Windows are the embedding input and the
  vector document; `content` in SQL is still the whole authoritative unit.
  `diagnostic_query` over-fetches, deduplicates by `source_chunk_id` in rank
  order and hydrates `content` from SQL, so a hit on window 9 of Weapons returns
  Weapons with its own citation and its own note. Hydration is why 8.8.1 and
  8.8.2 compose instead of competing.
* **One mapping, not two.** `derive_retrieval_documents` is called by both the
  reindex writer and `expected_vector_state_from_sql`, so published state and
  expected state agree because they are the same function — not because two
  loops were kept in step.
* **The budget is a measured constant, not a knob.** At 448 the densest of the
  11,076 windows encodes to 189 tokens, a 26% margin; 700 was measured (10,569
  windows, densest 246) and rejected. It is a module constant rather than
  configuration because it is a property of the model's ceiling, and an
  env-tunable ceiling invites the silent truncation this fixes.
  **Named ceiling:** a custom Rules Package denser than anything in the SRD
  could still exceed 256 tokens in one window. The upgrade path is a lower
  budget, or tokenizing at write time behind an optional embedder capability.
* **Proven against the real embedder, offline.**
  `tests/pipeline/retrieval/test_corpus_windows.py` (9 tests) publishes with the
  cached ONNX MiniLM model and queries for a fact that appears only late in a long unit, with a negative
  control that fails to find it when the content is embedded whole.
  `tests/ingestion/corpus/test_retrieval_windows.py` (6 tests) measures every
  window of the whole corpus through the model's own tokenizer: the defect
  reproduces at > 400 units, and after the fix the worst window is under 224
  tokens. Both disable the cached tokenizer's own 128-token padding and
  truncation first — a capped encoder reports 128 or 256 for an input of any
  length, which is the blindness being removed.
* **Embedding model and configuration are unchanged.** No fallback embedder, no
  new proof topology, no header or note dropped: the completeness of the derived
  text is asserted word-for-word against `visible_text` for every unit.

`RulesCorpusChunkMetadata` gains `schema_version`, `source_chunk_id`,
`window_index` and `window_count`, and the document ID gains a `:w{i}` suffix.
That is an **additive deviation from ADR-018 D2 and D11**, recorded as such: the
existing keys keep their meaning, nothing is removed, and D10 still holds —
this surface is internal/admin diagnostic in v1, and runtime rule inclusion
remains exclusively `get_active_rule_slice`. Generic (non-corpus) collections
are not migrated or touched; they take the new document shape on their next
reindex, which is the same rebuild-from-SQL path they already rely on.

#### 8.8.3 The baseline reset accepts the replacement corpus (`6d76759`)

Obligation (6) is discharged against the replacement corpus, in isolated stores:
the corpus is published by the real `finalize_source_release` into a file-backed
SQLite database (a copy per test) and a throwaway Chroma directory, and
`scripts/reset_corpus_baseline.py::main` is then driven over it with client
construction, the store reset and the rebuild recorded rather than performed. No
shared database and no shared Chroma store is opened. The digest proof itself is
never stubbed — it is what the tests exercise — and the eight restored
guarantees are the ones the retired module owned: the untampered corpus passes
and rebuilds; a chunk's content or locator swapped for another *syntactically
valid* value is caught by the canonical digest proof before any Chroma
mutation; the proof completes before the reset; the verdict agrees with
`verify_persisted_digest`; and a deleted payload, a dropped page or an orphaned
chunk each fail precisely and early. The retired module stays skipped: what was
retired is the corpus fixture, not the guarantee.

Restoring them found an operational defect. `validate_corpus_payload` called
`verify_persisted_page_coverage` without the `expected_pages` override that
`finalize_source_release` passes (§8.4), so it demanded all 364 printed pages
while the release declares the 360 it files a leaf under. The command would have
refused the replacement corpus with `persisted ledger omits authoritative
printed pages [2, 3, 4, 27]` — four TOC-only pages — the first time an
operator ran it. Patched at that sibling call site by reading the override from
the release's own `transform_config`, and verified by reverting the fix: the
positive control and the canonical-proof test both fail with exactly that
message. The rebuild line's wording was corrected in the same commit; it still
said "chunks" after the writer began returning bounded embedding documents.

### 8.9 Increment 6: shared 5d tooling proved against the replacement corpus

The delivery sequence requires shared-tool readiness to be complete and exposed
for review *before* any real pilot semantic authoring. This increment does that
and stops there. **No pilot semantic record exists.** Nothing was accepted,
published or activated, and `oracles/` is untouched.

#### 8.9.1 What was already ready, and is now demonstrated rather than rebuilt

Every behaviour the brief asks this increment to prove was already
implemented. They needed evidence against the *new* corpus, not new code
— the gap this increment closes is **authoring**, not proof, and is the
subject of §8.9.2. (Refusal of old authority and refusal of mismatched
authority are two rows below because they are two different mechanisms
firing at two different seams, not one behaviour listed twice.)

| Behaviour | Existing mechanism |
| --- | --- |
| Source/proposal binding | `load_bound_corpus` reads exactly the tables the replacement corpus's `persistence.py` writes (`rp_ledger_leaves`, `rp_chunks`, `rp_corpus_projections`); `ReleaseBinding` carries all six coordinates |
| Truthful unreviewed status | `committed_oracle_for` returns `None` — a typed absence the publication layer turns into `PublicationOutcome.ABSENT`, never an empty oracle and never an exception |
| Refusal of old authority | `afterworlds.quarantine` refuses the superseded identity at both the corpus-load and oracle seams |
| Refusal of mismatched authority | `GateFailureCategory.MISMATCHED_RELEASE`, decided from the *persisted* projection header so a caller cannot substitute a snapshot |
| Review/acceptance separation | proposal and accepted artifacts are different shapes at every level; `proposal.py` never reads `oracles/` and never writes |
| Stale-reuse invalidation | `proposal_identity` is content-derived over the whole payload, binding included |

No schema or policy transition is required. `5d-semantic-policy-2` already
carries the prose-retention catalog and the `section`/`entry`/`table` review-unit
kinds the 16 September Owner Decision requires, the policy enumerates no batch
names or scopes, and `schema_lift` demands succession evidence only when
extending a prior acceptance — a first acceptance over a fresh release has no
prior and crosses no succession. A `-3` was considered and rejected as
unjustified.

#### 8.9.2 The one real gap, and the smallest thing that closes it

`proposal.py` had no way to derive a proposal from bound source. The accepted
batches of the superseded line — seven at the 16 September decision, nine by
the restart (`known_unknowns.md`:284) — were each produced by a throwaway
per-batch generator script, which is the one input to acceptance nobody
reviews: a reviewer sees the artifact, not the code that emitted it. (The
commit message for this increment says “seven”; that is the pre-restart
count, and nine is the figure of record.)

`seed_proposal(snapshot, leaf_ids, *, binding, origin, rationale)` is now that
entry point, in committed source where its behaviour is a contract. It produces
the **weakest honest proposal**: one whole-leaf span per requested leaf at
`UNRESOLVED`, content-derived span ids, an empty representation, and **no review
units**. Naming a coherent unit and saying what it must contain is a human's
reading of the source; seeding placeholder units would put unauthored inventory
inside the identity an acceptance records, which is the fabricated-coverage
failure `5d-proposal-2` exists to prevent. It refuses a binding for a different
release and a leaf the release does not represent.

`leaves_under(session, package_uuid, release_version, labels)` resolves a
printed heading to represented leaf ids, so a reviewer can name a section the
way the source prints it. It is deliberately **not** a field of
`BoundCorpusSnapshot`: the snapshot is a coordinate system, and giving it
container paths would make every validator a consumer of 5c's heading structure
rather than of its offsets. It shares `_represented_leaves` with
`load_bound_corpus`, so selection cannot offer a leaf the binding seam refuses.

Labels match as a **suffix** of a container's label path rather than as a full
path. That is not convenience — it is what lets a reviewer name a section the
way the source prints it, and qualify it by the labels above it when a label is
ambiguous, without either of them having to know a depth. `Telepathy` occurs in
the glossary and again in `monsters.md`; `("Rules Definitions", "Telepathy")`
separates them, and neither caller nor selector counts levels to do it.

**What this paragraph used to say, and why it was wrong.** It justified the
suffix match by `### Swim Speed` — the glossary's sole `h3` — nesting thirteen
following entries a level deeper, and called that faithful 5c structure to be
recorded rather than corrected, on the grounds that changing it would be 5d
editing 5c. Official pp.189–191 print Swim Speed, Target and Unconscious as peer
glossary entries, so preserving the community conversion's rank there was not
fidelity to anything. The correction belongs at the source's own 5c layer, and
that is where it was made (family H of
`issue-5c-5d-community-source-corrections.md`); the prohibition on 5d editing 5c
is a prohibition on compensating here, not a reason to keep a defect. Suffix
matching stays for the reason stated above, which never depended on the defect.

#### 8.9.3 Evidence

`tests/ingestion/mechanical/test_source_release_readiness.py` (15 tests) runs
every proof against the actual replacement release
(`9717e288-c099-5217-b2d2-f89aeabd7b73` / `5.2.1-corpus.883aabdf-462`), read
back from the file `finalize_source_release` published into — not a re-persist
and not a synthetic fixture. Its module docstring states, and its contents
enforce, that it is **testing, not acceptance**: every disposition is
`UNRESOLVED`, the reviewer name is `fixture-not-a-reviewer`, and no SRD
semantics are asserted anywhere.

The `MISMATCHED_RELEASE` proof uses a *synthetic* oracle bound to a different
release, because the committed one is refused by quarantine before the gate sees
it. Both refusals are proved: the quarantine one by identity, the gate one by
category. Conflating them would have let a quarantine pass masquerade as
evidence that the gate's own release check works.

`source_candidate` moved from `tests/ingestion/corpus/conftest.py` up to
`tests/ingestion/conftest.py` — the documented home for what more than one
subdirectory needs — joined by `source_release_db`, which publishes it through
the real lifecycle into a temporary *file* so a fresh session can read back
committed state. `finalize_in_fresh_db` cannot serve this: it closes its session
and disposes its engine.

`test_production_release.py` is retained, not replaced. It still describes what
is in the tree, and retiring it is Step 5 of the Owner Decision.

#### 8.9.4 Maintenance obligation: the window recipe is not independently versioned

`WINDOW_CHAR_BUDGET = 448` (`pipeline/retrieval/corpus_windows.py:61`) is a
module constant and is **not** part of `transform_config`, so the published
release identity does not move when the windowing recipe changes. Today that is
correct — windows are the embedding input, not the stored unit, and `content`
in SQL is the authoritative text either way (§8.8.2) — but it means a
consequential change to the recipe would leave the corpus claiming an identity
derived under the old one.

Recorded as a standing obligation rather than a defect, and deliberately
**without a second proof system**: changing the budget, the block-breaking rule,
or the markup-to-whitespace mapping in a way that alters which text reaches the
embedder must move the recipe identity — by folding the recipe into
`transform_config` at that point, not by adding a parallel versioning mechanism
alongside the one 5c already has. A second identity system would be a larger
correctness surface than the drift it guards.

#### 8.9.5 Pilot scope, named and bounded

The ordinary pilot section is the **Conditions family** in `rules-glossary.md`:
15 conditions plus the `Condition` glossary entry that indexes them, **87 units
across 17 subtrees**, ~8,200 characters. Chosen because it is a *closed,
enumerable, named* set — the index entry lists exactly fifteen, so coverage is
checkable against the source rather than against a count 5d invented.

| Subtree | Units | Note |
| --- | ---: | --- |
| `Condition` | 4 | the index entry; carries the family's only table |
| Blinded, Charmed, Deafened, Frightened, Poisoned, Prone | 3—4 each | the ordinary case |
| Grappled | 5 | escape rule lives outside it, in `Grappling` |
| `Grappling` | 5 | adjacent sibling, not a condition |
| Incapacitated | 6 | referenced *by* Paralyzed, Petrified, Stunned, Unconscious |
| Exhaustion | 6 | one cumulative level with linear penalties; referenced from Long Rest |
| Invisible, Restrained, Stunned | 5 each | |
| Paralyzed | 7 | |
| Unconscious | 8 | |
| Petrified | 9 | largest |

The tricky siblings are **adjacent, not internal**, which is the point of the
choice: `Grappling` holds the escape rule for `Grappled [Condition]`;
`Incapacitated` is referenced by four other conditions rather than restating
them; and Exhaustion's level is cumulative, penalised linearly, and removed by
a rule that lives in another chapter. Each is a relationship 5d has to represent
without reconstructing 5c.

Unconscious was listed here as a fourth tricky sibling, "nests one level
deeper". It does not, and never should have: that was the family-H source defect
(§8.10), and with the source corrected Unconscious is an ordinary peer of the
other fourteen. Nothing in the pilot's shape depended on it.

It is a **learning increment toward full substantive scope**, not a reduced
final MVP: 87 of 10,465 units. What it is meant to establish is whether the
shared path can carry cross-entry references and a closed enumeration, which is
what the rest of the corpus will need at scale.

**Proposed representation choices, with the source and the consumer benefit
each one earns.** These are ordinary proposal-organisation choices, recorded so
they are reviewable rather than implicit. They are *not* an approval gate: no
decision below is required before records may be **proposed**, and none of them
is a policy conflict. What stays explicit and held is the other thing entirely
— **semantic acceptance**, the human act of attesting that a record states what
the SRD means. No proposal, default or reviewer nod here is that act, and
nothing in this section can perform it. Q1 is listed first because it decides
what an acceptance would attest and therefore constrains the other four.

1. **What review-unit kind covers a condition** — `entry` per condition, or
   `section` for the family? The policy admits both. *Proposed:* `entry` per
   condition, because the source's own index enumerates exactly fifteen, so
   per-entry review makes coverage checkable against the source rather than
   against a boundary 5d drew. *Consumer benefit:* an adjudicator citing one
   condition resolves to the unit that was reviewed, not to a fifteen-entry
   family a reviewer signed off as a whole.
2. **Is the `Condition` index entry one record naming fifteen, or fifteen
   relationships?** Its table is the only structured content in the family.
   *Proposed:* one record whose content *is* the enumeration, with the fifteen
   as references out of it — restating each condition inside the index would
   duplicate meaning that already has an owner. *Consumer benefit:* "is this a
   condition?" is one read of one record rather than fifteen, and the answer
   cannot disagree with itself.
3. **Does `Grappling` belong in the pilot's scope?** The escape rule is the
   `Grappled` condition's content by meaning and a separate subtree by
   structure. *Proposed:* in scope, authored as its own record that `Grappled`
   references. Pulling it into `Grappled` would be 5d rewriting 5c's structure;
   dropping it would author a condition whose escape rule has no owner.
   *Consumer benefit:* "how do I escape a grapple?" resolves to a record that
   owns the rule and cites the page that prints it, rather than to a gap.
4. **How is Exhaustion's level represented?** Read from the source rather than
   from the shape the question first assumed: official p.181 prints no
   enumeration of six levels at all. It prints one condition with four labelled
   effects — the level is cumulative and you die at 6; a D20 Test is reduced by
   2 times the level; Speed is reduced by 5 feet times the level; a Long Rest
   removes 1 level and the condition ends at 0. *Proposed:* one record with a
   numeric level and the two penalties expressed as coefficients (2 per level on
   D20 Tests, 5 feet per level on Speed), plus the death threshold and the
   Long Rest removal as its own relationship. The consumer benefit is the reason
   to prefer it: an adjudicator needs to evaluate the penalty at a level, and a
   coefficient answers that at any level, where six enumerated rows answer it
   only at the six the author happened to write out. An earlier draft of this
   section claimed the source "prints them as one list" of six enumerated
   levels and proposed a level-indexed component on that basis; the premise was
   false and the proposal built on it is withdrawn.
5. **Does a condition that only references `Incapacitated` carry that reference
   as a relationship, or is the transitive effect part of its own
   representation?** *Proposed:* a relationship, not a copy — flattening the
   transitive effect into four conditions would put the same meaning under four
   owners, which is the drift the two-layer split exists to prevent.
   *Consumer benefit:* resolving Paralyzed follows one edge to Incapacitated and
   gets the current text, and a later SRD change to Incapacitated is one edit
   rather than four that can fall out of step.

Recorded before authoring because each one changes the shape of the first
records, and a proposal is cheaper to redirect than a rewrite. What authoring is
actually waiting on is narrower and is stated in §8.10: the corrected
source/consumer boundary this increment establishes has not been reviewed yet,
and no pilot semantic record is authored until it has been.

### 8.10 Family H: the glossary ownership correction, and the identity it moved

Increment 7 in the gate record, and a source correction rather than a 5d one.
Codex's review of the shared-5d readiness evidence found that the readiness
record had asserted a community-conversion defect as faithful 5c structure. It is recorded
in full as family H of `issue-5c-5d-community-source-corrections.md`; what
follows is what it did to this document's subject matter.

#### 8.10.1 The defect, measured before and after

`### Swim Speed` was the sole `h3` in the glossary's flat run of 155 entries
under `## Rules Definitions`. A Markdown heading closes every open section at
its own depth or above, so an `h3` in an `h4` run owns the run: the thirteen
entries from Target to Weapon Attack, and the 47 units they hold, resolved to
`Rules Glossary > Rules Definitions > Swim Speed`.

| Measurement | Before | After |
| --- | ---: | ---: |
| Glossary heading-rank census | `{1: 1, 2: 2, 3: 1, 4: 154}` | `{1: 1, 2: 2, 4: 155}` |
| Units whose ancestors include `Swim Speed` | 47 | 0 |
| Glossary entries captured | 13 | 0 |
| Glossary units by container-path depth | `{1: 1, 2: 10, 3: 435, 4: 47}` | `{1: 1, 2: 10, 3: 482}` |
| Total corpus units | 10,465 | 10,465 |
| `rules-glossary.md` bytes | 72,860 | 72,861 |

Official pp.189–191 print the entries as peers, which the citation machinery
independently agrees with: Swim Speed and Swimming cite p.189, Target and
Telepathy p.190, Unconscious and Weapon Attack p.191, each 2—8 leaves of its own.
Those page numbers are read off the built ledger rather than transcribed from a
review comment.

**Bounded sibling evidence.** The census above is the proof: the glossary now
carries exactly one heading rank in its entry run, so a rank outlier anywhere in
the 155 would fail, not only this one. The check is bounded to this file on
purpose — `spells.md` and `magic-items.md` legitimately mix ranks (a stat block
sits one level under the entry that summons it), so a corpus-wide rank census
would report noise rather than residue. Family G's ownership pass could not have
found this: it is organised per stat block, and the glossary embeds none.

#### 8.10.2 The new release identity, and what carried it

The identity moved with no new mechanism and no version bump, because the pin
manifest's per-file digest is already inside the transform config:

| | Superseded | Current |
| --- | --- | --- |
| Package UUID | `4f1bf24f-b64e-5706-924d-b50c2753e67e` | `9717e288-c099-5217-b2d2-f89aeabd7b73` |
| Release version | `5.2.1-corpus.6a11f2c0-393` | `5.2.1-corpus.883aabdf-462` |
| `transform_config_hash` | `041d839a…` | `08cbcb4f9b1bb86a272def982a6f3416e200d227f1e4beda0c116ad70f8d0155` |
| Frozen source ledger hash | `72ddaf29…` | `301a1d6a502789f3e905b050072be91cc77e86517991196fdc14c8b5024bdaf4` |
| Bundle root hash | `758b7b63…` | `c3b3668bb7dc5220eee9e7191008cfe92103b7e5eb6e003e97eebc7708f50cf1` |
| `rules-glossary.md` digest | `9b25315e…` | `3fa8904be1e84bfafda24bf673c5e30ad899bd4135809a4c4dfd1d738f0d5ead` |
| Embedding windows | 11,077 | 11,076 |

`load_pinned_sources` is why the two halves cannot drift: it refuses a build
whose bytes do not hash to the manifest, so the source edit and the manifest
entry are one change or there is no build at all.

The window count is the one figure that moved for a non-obvious reason and is
therefore measured rather than asserted. A window's 448-character budget is
shared with its section-label prefix; dropping `Swim Speed > ` from 47 units'
label stacks gave those windows 13 more characters, and one unit that needed two
windows now needs one. 500 chunks needing more than one window became 499.

**The superseded identity is not quarantined, and that is deliberate.**
Quarantine refuses *persisted* authority by identity. `4f1bf24f` /
`5.2.1-corpus.6a11f2c0-393` was only ever built into `tmp_path_factory` stores
inside the test session; nothing accepted it, nothing published it outside an
isolated store, and `oracles/` holds no artifact bound to it. There is nothing
persisted for a quarantine entry to refuse, so adding one would be ceremony
rather than a guard. What it left behind was three places in this document and
one module docstring, all updated here. The increment-5 and increment-6 gate
records keep the figures they measured; those were true when written, and the
supersession is recorded here rather than by editing a closed entry.

#### 8.10.3 What this increment does not do

No pilot semantic record is authored. The brief holds authoring until the
corrected source/consumer boundary has been reviewed, and that review has not
happened. §8.9.5's proposals are proposals; semantic acceptance remains the
separate, explicit, human act it was before this increment.

### 8.11 The accepted-source correction, and the identity it moves

A source and citation correction under the Owner's 2026-09-24 direction; the
defects, evidence and page changes are in
`.claude/review-notes/issue-5d-accepted-source-correction.md`. Three things
changed together:

- **Source bytes.** Two reviewed patches: Travel Pace's two-row header in
  `playing-the-game.md` (corrections family K), and the *Food, Drink, and
  Lodging* group labels and printed-order list, the *Saddle* group row and the
  *Airborne and Waterborne Vehicles* caption in `equipment.md` (families I and
  J). The pin manifest, corrections record and coverage JSON moved with them.
- **Citation instrument.** `cite_units` now has one path: the unit's whole text
  in the official page stream, bounded by the partition's kept anchors, with the
  partition's pages as the fallback. The earlier window-only path is removed,
  not kept behind a flag. `CitationReport` counts all four mechanisms
  (`located`, `placed`, `anchored`, `inherited`) and states that a status names
  the mechanism, not a proof the page is right.
- **Versions.** `SOURCE_TRANSFORM_VERSION` 3 → 4 and the `citation_instrument`
  string, both inside the transform config; `EVIDENCE_REPORT_SCHEMA_VERSION`
  `5c-evidence-4` → `5c-evidence-5`, because the report payload gained the
  `located`/`placed` counts.

| | Superseded | Corrected build |
| --- | --- | --- |
| Package UUID | `9717e288-c099-5217-b2d2-f89aeabd7b73` | `0b1a965e-28bd-55e6-ac13-bc7786a1bace` |
| Release version | `5.2.1-corpus.883aabdf-462` | `5.2.1-corpus.626c83f8-209` |
| `transform_config_hash` | `08cbcb4f…` | `eaa19d762d1d530ae6691824d8d26b3f5b874aaa867786d976e0dc489997d3ec` |
| Frozen source ledger hash | `301a1d6a…` | `2385d8e67b7edab8ec229fc6193d2243fd0ac43e52f8d2686acbb06322430296` |
| Bundle root hash | `c3b3668b…` | `0f49f740341dd8f5ca14881f23c42dd66b934e7ead1963209c0daf1457329a02` |
| Persisted corpus digest | `3b6a4bd7…` | `81009ec855c66a5732fbd24be79201bf3661dd7fc66df67f3aad82d8a7daf39b` |
| `playing-the-game.md` digest | `fbef5175…` | `7110c6ed7dca81776a346cd03665011aabc7ff11db8d85d6c010e7b7d473de76` |
| `equipment.md` digest | `eef7cb05…` | `ba4d96bf7c08a44103b11be1ae5385e6e09f3f5478d56c3a2f38f97bd77d645b` |
| Units | 10,465 | 10,465 |
| Citations: located / placed / anchored / inherited | only anchored and inherited were counted | 9,016 / 22 / 83 / 1,344; 0 unresolved, 0 uncited body pages |

The authoritative PDF hash is unchanged (`8974902d…3d87`).

**The corrected build is not published.** It was built only into a private
scratch store to regenerate proposals. Nothing rewrote the old oracle as
accepted against the new binding: the Owner approved a fresh acceptance chain
against `626c83f8-209` on the reviewed replacement packet, and it was recorded
at 2026-09-24T10:02:36Z as `srd-5-2-1-corpus-626c83f8-209.json` (SHA-256
`7b1d6f43…abdd8`) by `issue-5d-source-correction-REPLACEMENT-ACCEPT.py`, which
replays it with `--verify`. That file replaced
`srd-5-2-1-corpus-883aabdf-462.json` and its twelve per-batch acceptance
scripts and proposals, which are retired and remain in history at `5ed0657`.
The earlier gate records keep the figures they measured; this supersession is
recorded here rather than by editing a closed entry.
The Owner then accepted the `equipment` batch over that chain, and
`issue-5d-equipment-ACCEPT.py` recorded it in the same file on 2026-09-25
(SHA-256 `08cca0b7…03fb`: thirteen batches, 216 records, 49 resolutions). That
script's `--verify` now replays the whole file over the pinned twelve-batch
rebuild; the replacement script's own `--verify` now checks only that rebuild
against its recorded twelve-batch bytes, the prefix Equipment extends.
The Owner then accepted the `spellcasting` batch over the Equipment result,
and `issue-5d-spellcasting-ACCEPT.py` recorded it in the same file on
2026-09-25 (SHA-256 `c5971b89…572f`: fourteen batches, 235 records, 50
resolutions). That script's `--verify` now replays the whole file over the
Equipment result rebuilt natively and pinned to `08cca0b7…03fb`; the Equipment
script's own `--verify` now checks only that the current file preserves that
thirteen-batch prefix, and the replacement script's still checks the twelve.

The Owner's correction of the Level 2 Bard, Druid, Sorcerer and Wizard spell
tables produced a further release, `ebdd9333-eeed-5df1-b3e1-8b97c2f65f80` /
`5.2.1-corpus.574662e9-0ef`, which the cross-release check does not let the
`626c83f8-209` file extend. On the exact owner-review packet the Owner approved
a fresh chain of the seventeen regenerated batches and 51 resolutions, and the
`spell-descriptions` batch and its 1046 resolutions over it;
`issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py` recorded it on 2026-09-27
UTC as `srd-5-2-1-corpus-574662e9-0ef.json` (SHA-256 `b1f8718f…`: eighteen
batches, 947 records, 1097 resolutions), replayed by its `--verify`. The
`626c83f8-209` file is superseded; this entry records the supersession rather
than editing the ones above. Under a later Owner authorization the superseded
file and its twenty-seven superseded construction inputs were retired on
2026-09-27 (`.claude/review-notes/issue-5d-spell-retirement-followup.md`).
The Owner then accepted the `gameplay-toolbox` batch and its one resolution
over that eighteen-batch result, and `issue-5d-gameplay-toolbox-ACCEPT.py`
recorded them in the same file on 2026-09-27 (09:46:01Z and 09:46:44Z UTC;
SHA-256 `671f47d7…`: nineteen batches, 980 records, 1098 resolutions). That
script's `--verify` now replays the whole file over the eighteen-batch result
rebuilt natively and pinned to `b1f8718f…`; the replacement script's own
`--verify` now refuses the current file's batch set as unrecognized. The
record is
`.claude/review-notes/issue-5d-gameplay-toolbox-recorded-followup.md`.
The Owner then accepted the `magic-items` batch and its one resolution over
that nineteen-batch result, and `issue-5d-magic-items-ACCEPT.py` recorded them
in the same file on 2026-09-27 (23:27:11Z and 23:28:26Z UTC; SHA-256
`fc62c47c…`: twenty batches, 1250 records, 1099 resolutions). The batch adds
270 records and one component to each of the accepted Potion of Healing and
Spell Scroll Equipment records, whose derived `prose_bound_components`
obligations name it; nothing else of the prior changed. That script's
`--verify` now replays the whole file over the nineteen-batch result rebuilt
natively and pinned to `671f47d7…`; the Gameplay Toolbox script's own
`--verify` now refuses the current file's batch set as unrecognized. The
record is
`.claude/review-notes/issue-5d-magic-items-recorded-followup.md`.
