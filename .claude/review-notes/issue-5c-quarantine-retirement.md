# CRD Issues 5c/5d — Step 5 retirement of the original products

Recorded Owner Decision of 21 September 2026, Step 5 ("Retire superseded work"),
implemented on branch `codex/quarantine-retirement` over main `fcc4e1f` (PR #178
merged 9 October 2026), for delivery as a separate retirement PR. That PR carries
the final review and the exact-head CI disposition; merge stays an Owner
boundary. No publication, activation, shared-database write or issue-state change.

**Historical links.** Older notes and the historical body of
`docs/architecture/issue-5c-5d-clean-restart.md` still name the retired
artifacts, tools and outputs listed below. They were left as written; every
named file is recoverable from Git history (for example
`git show fcc4e1f:<path>`).

## What was retired

**Original products.**
- `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-36b786d8-fa2.json`
  (original 5d authority, nine batches on the retired release).
- `src/afterworlds/ingestion/corpus/srd_table_inventory.json` (expected-table
  oracle of the geometric transform).

**Geometric construction and finalization code** (no current caller):
- deleted modules `corpus/tables.py`, `corpus/table_inventory.py` and
  `corpus/transform_identity.py`, plus `scripts/regen_table_inventory.py`;
- removed functions `pipeline.build_candidate`, `bundle.transform_config_payload`/
  `transform_config_hash`, `persistence.finalize_release` (its only extra guard
  was the table inventory), `concordance.check_table_concordance`/
  `TableConcordanceResult`, and the geometric `ledger.build_ledger` builder.

**Tests that only graded or skipped on the retired products.**
- Every `QUARANTINED_RECONSTRUCTION` skip, together with `full_candidate`,
  `full_release`, `compact_candidate` and `compact_release`.
- Corpus suites: `test_tables`, `test_table_inventory`, `test_transform_identity`,
  `test_operational_contract` and `test_baseline_reset_script`.
- The compact-fixture part of `test_persistence_quarantine` and the geometric
  part of `test_ledger_pipeline`.
- Mechanical suites: `test_production_release` and
  `test_runtime_production_release`.
- The four `*_frozen_prior` and four `*_acceptance_reproduction` suites
  (areas-of-effect, cover, speed and proficiency).
- `test_proficiency_1_proposal`, `test_proficiency_destinations_1_proposal`,
  `test_proficiency_references_resolve` and `test_retained_proposals`.
- The 36b-content cases in `test_committed_accepted_authority`,
  `test_accepted_inputs`, `test_policy_versioning`, `test_reference_resolution`,
  `test_schema_6_succession` and `test_schema_14_proficiency_inputs`.
- Test data: two frozen priors with no remaining consumer
  (`accepted_prior_…_actions_1.json` and `…_actions_1_attitudes_1.json`).

**Original-product tooling under `.claude/review-notes/` (34 files).**
- The 28 generator, ACCEPT, discovery and obligation scripts that imported
  `corpus.pipeline.build_candidate`.
- `issue-5d-batch-proficiency-destinations-1-and-proficiency-1-ACCEPT.py`, which
  bound and wrote the 36b artifact.
- `_rebaseline_accepted_oracle.py`, which named only the 36b JSON.
- `issue-5d-schema-2-crossbatch-matrix.py`,
  `issue-5d-schema-closure-threebatch-matrix.py` and
  `issue-5d-zero-path-corrected-matrix.py`. These were the only readers of the
  retired batch-actions and batch-hazards audits.
- `issue-5d-batch-conditions-1-generator.py`. It was not in either supplied
  inventory, but it is a sibling of the retired family:
  - it produced the retired `batch-conditions-1` proposal;
  - its inputs (`leaves.json`, `containers.json`, `edges.json`, `binding.json`)
    are not tracked, so it cannot run;
  - it hard-codes the protected checkout path;
  - nothing calls it.
- A fixed-string search for each name over `src/`, `tests/`, `scripts/`,
  `.github/` and `.claude/` found callers only among the retired files. The one
  exception was explanatory text in `test_schema_6_ready_source_provenance.py`,
  which now names its retained JSON input and the Git restore path instead of
  the removed tool.

**Original outputs under `.claude/review-notes/` (31 JSON files), with no current
caller.**
- Proposals and audits: actions-1 schema 6 and schema 7; batch actions-1,
  attitudes-1, conditions-1 (including its schema-2 version) and hazards-1;
  batch proficiency-destinations-1.
- Audits only: batch areas-of-effect-1, cover-1 and speed-1.
- `attitudes-1-final-independent-probe`.
- Proposal and audit pairs for the conditions-1 schema-2 and schema-3
  REGEN/REMEDIATION and the hazards-1 schema-3, 4 and 5 REGEN.
- A fixed-string search over `src/`, `tests/`, `scripts/`, `.github/` and
  `.claude/` found no reader outside the retired matrix scripts.
- Every dynamic name builder (`_replacement_chain.py` and the replacement and
  ACCEPT scripts) formats only the `REGEN-3fe24ff6`, `REGEN-574662e9`,
  current-tag or `remaining-references` names.
- Owner receipts, checkpoint and review prose were not touched.

## Tombstones kept

- `afterworlds.quarantine` still refuses package `4458fa10-…`, release
  `5.2.1-corpus.36b786d8-fa2`, projection `82c75aad-…` and transform recipe
  `6332f201…` at every authority seam.
  - Its artifact filenames and digests are kept to identify stray copies.
  - `test_quarantine_5c_5d.py` now asserts the files are absent and still
    refused.
  - The recipe refusal is proven on a synthetic transform config under two
    embedding labels.
- `scripts/ingest_srd.py` is refusal-only: the first statement raises
  `QuarantinedAuthorityError` before any migration or store.
- `oracle._resolve_committed_inputs` refuses the retired and superseded releases
  before reading the directory.

## Retained, with current purpose

| Item | Current caller / purpose |
|---|---|
| `corpus/ledger.py` (`ledger_payload`, `ledger_hash`) | Source ledger hash in `pipeline`, `bundle`, `gate`, `persistence`; payload shape unchanged so recorded hashes hold |
| `transform.build_corpus`/`section_label_for`, `pdf_source`, `policy`, `reconcile`, `source_completeness`, `concordance.verify_citations`/canaries | `build_source_candidate` and `finalize_source_release` |
| `concordance` `page_substring` dispatcher branch | Shared, live-tested dispatcher; stored geometric releases are refused upstream by recipe hash |
| Oracle `srd-5-2-1-corpus-3fe24ff6-4e3.json` | Current restart evidence. `_replacement_chain.py`, the Monsters-corrections ACCEPT/REPLACEMENT closure, `release-order-recording/RECORD.py`, `superseded_release.py` and the 3fe acceptance tests read it as the pre-official-order accepted chain |
| Oracle `srd-5-2-1-corpus-574662e9-0ef.json` | Its 17 regenerated proposals feed the stale/rejected identity check in `test_committed_accepted_authority`; the class-spell-tables, Monsters-corrections and generator replay scripts read it |
| Both intermediates' packaging | Excluded from wheel and sdist (`exclude-package-data`, `MANIFEST.in exclude`), because resolution refuses them by version before reading the directory |
| `data/accepted_prior_conditions_1_hazards_1.json` | `test_schema_6_succession` (lift regression input) |
| `data/…_areas_of_effect_1.json`, `…_cover_1.json`, `…_speed_1.json` | `test_schema_10_cover`, `test_schema_11_speed`, `test_schema_14_proficiency_inputs`, `test_policy_versioning` (schema/policy crossing inputs for current shared lift code) |
| `data/legacy_conditions_1_unanchored_schema3.json` | 14 schema-legality/succession suites (legal schema-3 shape) |
| `issue-5d-actions-1-obligation-coordinates.json` | `test_schema_6_ready_source_provenance`, `test_schema_7_casting_time_gate` |
| `issue-5d-areas-of-effect-1-source-manifest.json`, `issue-5d-batch-areas-of-effect-1-PROPOSAL.json` | `test_schema_9_areas_of_effect` |
| `issue-5d-cover-1-source-manifest.json`, `issue-5d-batch-cover-1-PROPOSAL.json` | `test_schema_10_cover` |
| `issue-5d-speed-1-source-manifest.json`, `issue-5d-batch-speed-1-PROPOSAL.json` | `test_schema_11_speed`; the proposal is also linked from existing ADR, known-unknown and comparison documents |
| `issue-5d-batch-proficiency-1-PROPOSAL.json` | `test_schema_13_proficiency`, `test_schema_14_proficiency_inputs` |

These eight are the only original-named JSON inputs kept. All current accepted
proposals, Owner receipts, pinned source and current oracle files, and the
3fe/574 regression and replay inputs are unchanged.

## Coverage carried over or restored

- **Corpus gate.** `test_gate.py` (18 cases) and the generic release invariants
  now run live on the session `source_release` instead of skipping. These are
  the canaries, accounting, five hashes, report proof hashes and the
  host-independent evidence report.
- **Persistence verifiers.** One representative failure each moved into
  `test_source_lifecycle.py` on the published store:
  - single-source invariant plus digest;
  - deleted policy row (`PolicyReconstructionError`);
  - orphan enabled chunk (runtime membership).
- **Proposal loader.** `test_proposal_loading.py` reruns the loader refusals on
  the Owner-approved `conditions-pilot` proposal, including the `5d-proposal-1`
  shape carrying review units.
- **Vector identity.** It is now asserted on `source_transform_config_payload`.
- **Subclass walker.** It now runs against the current 8781 authority.
- **Retired with their product, not re-covered.** Policy-row field-level
  tampers, rollback fault-injection variants, reuse-rejection variants and
  two-release coexistence ran only on the six-page geometric compact fixture
  and had been skipped since 21 September.
  - Publication-window rollback and verified reuse remain covered in
    `test_source_lifecycle.py`.
  - No other coverage was lost.

## Lessons kept (shared account)

- Identity-keyed refusal has to outlive the artifacts. The recipe hash, not the
  output UUID, names a retired transform.
- A compact partial-corpus fixture made lifecycle tests cheap but tied them to
  one transform. When that transform was retired, the shared verifiers lost
  every negative test at once.
- Test-only historical data should not ship in runtime packages; exclusion is
  cheaper than relocation when replay scripts pin paths.

## Validation

All focused runs carried the focused-runner label (coverage off); they are
diagnostics, not gate evidence. Native exits are shown.

| Check | Result |
|---|---|
| Source candidate identity before/after (`build_source_candidate`) | Byte-identical. Package `1299484e-…`, release `5.2.1-corpus.8781d4e0-a3b`, transform-config hash `753e7608…` and bundle root `0941dc96…` all match the 8781 `release_binding` |
| Oracle bytes | 8781 `def7caa1…`, 3fe `e6f5f36a…` and 574 `fc62c47c…` unchanged |
| Collection, `pytest --collect-only --no-cov` | 7,546 → 7,318, exit 0. All 245 removed node IDs are in the retired files above; 17 added. Rerun after the data retirement: the same 7,318 node IDs |
| Focused A: quarantine plus the 12 changed mechanical files | 742 passed |
| Focused B1: corpus gate, invariants, persistence guards, vector/release identity, findings, reconcile | 55 passed |
| Focused B2: source lifecycle, release, completeness | 42 passed |
| Restored cases (host-independent report, v1 inventory refusal) | 2 passed |
| Packaging (corpus + mechanical) | 3 passed. Wheel and sdist ship only the 8781 oracle with its pinned digest, omit 36b, the inventory and both intermediates, and the installed copy resolves 8781 (24 batches) and refuses 36b as quarantined |
| `mypy src/` (strict) | Exit 0, 232 files |
| Strict mypy on the new or rewritten test files | Exit 0. Other touched legacy test files keep their pre-existing errors; CI gates `mypy src/` |
| Black, Ruff (`src tests scripts`) | Exit 0 |
| CI pip-audit command (four ChromaDB ignores) | Exit 0, "5 ignored" |
| `.secrets.baseline` | Line-number metadata only, for `quarantine.py` (92/94/96 → 94/96/98), `test_committed_accepted_authority.py` (1062–1085 → 164–187) and `test_oracle.py` (282 → 281). 12,851 entries, plugins/filters/config, file set and every hashed secret unchanged; no other entry changed; no regeneration or waiver |
| Native `detect-secrets-hook --baseline .secrets.baseline` (changed files), historical pre-staging run | Exit 1, solely "Your baseline file (.secrets.baseline) is unstaged" (staging is Codex's) |
| Native hook, byte-identical baseline copy (changed files) | Exit 0, no finding, and the copy is unmodified, so the line numbers are current |
| Final: native `detect-secrets-hook` against the real staged `.secrets.baseline` over all 47 changed or added surviving files (run by Codex after staging the reviewed change) | Exit 0, no output and no findings; the real baseline was not modified by the hook. Receipt: Codex's `native-secrets-final.txt` (empty output) |
| `compileall .claude/review-notes` | Exit 0; no remaining script names a retired tool or output |

**Not run locally, by instruction.** These are the full suite with coverage,
`test_source_baseline_reset`, `test_vector_publication`, the readiness/replay
batch, E2E and frontend. The B3 batch was cancelled by Codex, not failed.
Required exact-head CI on the separate PR covers them.

## Open for delivery

- The separate retirement PR's exact-head CI runs the full backend aggregate
  with coverage, the baseline-reset, vector-publication and readiness suites,
  frontend, E2E and pip-audit. Its outcome is not claimed here.
- The ChromaDB pip-audit residue (four CVEs, five rows) is unchanged under
  ADR-018.
- Obligation (5) of §2.5 (5d publish → activate → runtime-resolve over the
  replacement corpus) remains open.
- The partial-publication block stands.
