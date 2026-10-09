# CRD Issue 5c restart — release-order replacement: recorded follow-up

## Authority

- The [21 September restart Owner Decision](../../../docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md) and the settled official SRD 5.2.1 chapter order.
- Owner acceptance, verbatim: "I accept this exact release-order candidate." Receipt [`owner-acceptance.json`](owner-acceptance.json), SHA-256 `efe48d9b3f5c7f33591763ed823a2938519d276c2e5d6e3776ac22be6d4cd5e3`, created `2026-10-07T05:28:37Z`.
- Accepted candidate: SHA-256 `8a6a9a9c305f41207190c0deb55875a027019116ce3f825a6a0425a3a115b4bf`, 35,061,929 bytes, retained unchanged as [`accepted-candidate.json`](accepted-candidate.json). It was reviewed in the [candidate packet](../issue-5c-release-order-candidate.md) (SHA-256 `ec044533…`) and the [Codex review](../issue-5c-release-order-candidate-codex-review.md) (SHA-256 `51e826b7…`).

This recording grants no commit, push, merge, publication, activation or shared-store write authority.

## Recorded artifact

| | |
|---|---|
| File | `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b.json` |
| SHA-256 | `def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c` |
| Size | 35,572,079 bytes |
| Binding | `1299484e-c72d-509b-bd8d-d0169ee1f8d2` / `5.2.1-corpus.8781d4e0-a3b` (equals the receipt binding) |
| Projection UUID | `8d8cb42c-aefe-559c-9d85-6ba975c038af` (same as the candidate) |
| Recorded at | `2026-10-07T05:39:49Z` |
| Reviewer | `Ravenlok (Owner)` |
| Scope | 24 batches, 1,835 records, 1,486 reference resolutions, representation schema 17 |

### How it was recorded

[`RECORD.py`](RECORD.py) replays the captured 43-step chain `live-chain.pkl` (SHA-256 `b5d82c71…`; 24 `accept_proposal` and 19 `resolve_references` steps) through the native functions. It uses the existing `rel-old`/`rel-new` stores, the leaf-keyed rebind maps and the code fingerprint. It does not recapture, rebuild or regenerate the candidate, and `recompose.py` is unchanged.

Each step carries fresh evidence: reviewer `Ravenlok (Owner)` and the recording time. Each `rule` and `authorization_reference` cites:
- the Owner statement;
- the candidate SHA-256;
- the receipt path and SHA-256;
- the Codex review and packet SHA-256s;
- the release.

No prior approval provenance was copied or relabelled. The run's residue check asserts that no prior `accepted_at`, `resolved_at`, `rule` or `authorization_reference` value survives, that no `SIMULATION` text remains, and that no old binding coordinates remain.

### Candidate-to-recording difference

Everything outside `acceptance` is byte-exact, and `proposal_identity` is exact for all 24 batches. Only the six evidence fields changed:

| Collection | Field | Changed values |
|---|---|---|
| `batches` | `rule` | 24 |
| `records` | `accepted_at`, `reviewer` | 10,493 each |
| `reference_resolution_records` | `authorization_reference`, `authorized_by`, `resolved_at`, `reviewer` | 1,486 each |
| `review_unit_records` | `accepted_at`, `reviewer` | 1,476 each |

Unaccounted differences: 0. Order-only collections: 0.

## Evidence

All raw logs and exits are under [`run/`](run/); `run/run.py` refuses to overwrite. Wrapper exits are not raw gate exits: `focused` reports the runner's exit and pytest's own summary.

| Run | Raw exit | Result |
|---|---|---|
| `gates-{black,ruff,mypy}-prerecord` | 0 / 0 / 0 | `RECORD.py` before recording |
| `simulate` | 1 | Codex review pin was stale (review updated before acceptance); re-pinned |
| `simulate-2` | 0 | Control reproduces the live oracle and simulation reproduces the candidate, byte for byte; 1,510 bindings and 32,800 chunk ids rebound |
| `record` | 0 | Wrote, reloaded byte-equal, selected; 0 native findings against a disposable copy of `rel-new`; source stores unchanged |
| `gates-{black,ruff,mypy}-pinned` | 0 / 0 / 0 | `RECORD.py` with recorded values pinned |
| `verify` | 0 | Same checks against the file on disk |
| `recorded-reconstruction` | 0 | [`recorded_canonical_reconstruction.py`](recorded_canonical_reconstruction.py): `persist_draft`, `verify_reconstruction` and `reconstruct_candidate` on a disposable store; all 7 checks true; payload hash `69299de5…`; source store `f2067b83…` unchanged ([report](reports/recorded-canonical-reconstruction.json)) |
| `focused` | 0 | 18 passed: the whole readiness file (15, including the two former pending-recording failures) and the three directory listings |
| `gates-ruff-tests` / `gates-mypy-tests` | 1 / 1 | **Invocation error, not gate results**: the interpreter was passed twice |
| `gates-ruff-tests-2` | 0 | Four first-round pin files |
| `gates-mypy-tests-2` | 1 | 16 errors in 3 files, all pre-existing. Pre-edit copies give the identical error multiset (`gates-mypy-tests-preedit-copies`, raw exit 1) |
| `codex-packaging-pin-before` | 1 | Codex's diagnostic before the packaging fix (it also inherited coverage flags) |
| `focused-2` | 0 | 3 passed: packaging inventory, `test_no_refused_candidate_is_selectable`, sole-artifact listing |
| `gates-ruff-tests-3` / `gates-mypy-tests-3` | 0 / 0 | `test_packaging.py`, `test_committed_accepted_authority.py` |
| `gates-{black,ruff}-secrets` / `-secrets-2` | 0 / 0, 0 / 0 | [`recorded_scoped_secrets.py`](recorded_scoped_secrets.py) before and after its scope fix |
| `secrets-apply` | 1 | Failed closed on the first 16-hex hit, before writing the baseline (still `e492abda…`) |
| `secrets-apply-2` | 0 | Baseline `e492abda…` → `1f84998b…`; 3,130 entries added; settings and out-of-scope entries exact |
| `secrets-private-copy` | 0 | Hook against a private copy of the new baseline: content check passes, copy unchanged |
| `secrets-real-hook` | 1 | **Not green**: "Your baseline file (.secrets.baseline) is unstaged." Nothing was staged |

Codex independently confirmed the recorded bytes ([live-pin findings](codex-live-pin-findings.md), `codex-native-persistence.json`, `codex-recorded-payload-review.json`).

### Reused proofs

The projection UUID and payload hash equal the accepted candidate's, so the candidate phase's reader proofs still apply: the 13 reader pairs and the negative controls. The 1,835-record reader sweep was not repeated.

## Live selection

- The new binding resolves only to the recorded file.
- The prior oracle `srd-5-2-1-corpus-3fe24ff6-4e3.json` (`e6f5f36a…`) stays in `oracles/` unchanged, labelled **Superseded** in the README, following the `574662e9-0ef` precedent. The old binding still resolves to it alone; a copy is retained as [`prior-live-oracle.json`](prior-live-oracle.json).
- Stale-binding lookup stays fail-closed: `record`/`verify` assert the old binding selects only the prior file and never the recorded one, and the resolver's existing refusal of two files claiming one release is unchanged.

## Affected pins

**Defect family:** exact current-inventory pins over the committed oracle directory or its committed batches. **Trigger:** the new release file and its 24 rebound proposal identities. All 7 sites that iterate the directory were inspected.

| Site | Disposition |
|---|---|
| `test_accepted_inputs.py::test_exactly_one_accepted_artifact_is_committed_for_the_release` (directory listing) | patched: added the new filename |
| `test_committed_accepted_authority.py::test_the_release_resolves_to_this_sole_committed_artifact` (directory listing) | patched: added the new filename |
| `test_oracle.py::test_the_committed_oracle_directory_holds_one_artifact_per_release` (directory listing) | patched: added the new filename |
| `test_packaging.py::test_the_production_oracle_directory_ships_only_reviewed_content` (directory listing) | patched after Codex P2: added the new filename; sentinel assertion kept |
| `test_committed_accepted_authority.py::test_no_refused_candidate_is_selectable` (identity union) | patched after Codex P2: added the 24 literal identities from the accepted candidate (`8a6a9a9c…`), not derived from the oracle under test. They are disjoint from the old release's identities. The historical set, exact equality and refused-identity assertions are kept. |
| `test_source_release_readiness.py` (docstrings) | patched: module identity and pilot-authorities wording; assertions unchanged |
| `oracles/README.md` | patched: new **Current** entry; old entry relabelled Superseded |
| `test_committed_accepted_authority.py` per-release filter (`same_release`, about line 1288) | already safe: filters by `release_version`, so the new release cannot enter it |
| `test_classes_proposal.py` / `test_spell_descriptions_proposal.py` snapshot-compare globs | already safe: the directory is compared before and after with itself |
| Acceptance tests that resolve `committed_inputs_for` with old-chain bindings (equipment, spellcasting, character-origins-feats, and the `REPLACEMENT.RELEASE`/`RECORDING.RELEASE` users) | already safe: the old binding resolves the unchanged prior file |
| Generator-rebuild tests over `source_release_db` that assert the old `ORACLE` bytes (for example `test_classes_proposal.py:166,825`, `test_rules_glossary_completion_proposal.py:182,1032`; about 25 files) | out of scope: these are pinned-binding history, failing both before and after this recording; not patched |
| Quarantine tests | already safe: identity-scoped; no release-order quarantine was added |

## Remaining boundaries

- **Owner decision needed:** retiring or quarantining the superseded `3fe24ff6-4e3` file. It stays resolvable under its own binding; nothing here retires it.
- **Out of scope:** the generator-rebuild pinned-binding tests above.
- **Correction, 2026-10-07:** both entries above were wrong. The 21 September 2026 Owner Decision already authorizes retiring superseded artifacts, paths and tests and forbids inventing approval gates, so no further Owner Decision was needed. The `3fe24ff6-4e3` file stays on disk as historical evidence, but resolution now refuses its release. The generator-rebuild tests are not out-of-scope history: the current-release expectations were corrected, and only assertions that enshrined superseded bytes were retired. See the [readiness correction](../issue-5c-release-readiness/correction-followup.md). The entries above are kept as the record of what this follow-up said at recording time.
- **Verification outstanding at recording time:** broad-suite, coverage and expanded mypy results were not cleared. Holding these runs during the bounded recording pass did not authorize deferring correction of discovered non-dependency errors. The 16 test typing errors were open correction work before restart completion. Dependency-vulnerability repairs alone retained the after-completion deferral described here.
- **Readiness update, 2026-10-07:** the original 16 test typing errors and 105 additional affected-consumer errors are corrected. The selected 16-file strict check and the production strict check (235 files) exit 0, and their applicable inputs remain unchanged. Formatting and lint checks also exit 0. The full configured pytest/coverage gate is still running and has failure/error markers; its final report and correction of concrete in-scope non-dependency failures remain outstanding. Dependency-vulnerability repair alone retains the Owner's deferral. See the [bounded readiness review](../issue-5c-release-readiness/codex-bounded-review.md). This update does not grant publication authority.
- **Secrets:** see [`recorded-secrets-validation.json`](recorded-secrets-validation.json).
  - **Hook exits:** the real relative-path hook exits 1 because `.secrets.baseline` is unstaged, so that gate is not green. The private-copy content check exits 0. Nothing was staged to cure the gate.
  - **Scope:** 70 files: this folder except Codex's own `codex*` files and folders (left to Codex; one holds a tool-use id, not a hash), the new oracle, the affected pins and the restart doc.
  - **What was added:** the 3,130 additions are public content hashes. 1,014 each went to the new oracle, `accepted-candidate.json` and `prior-live-oracle.json`; the remaining 88 went to the small JSON/log/script files and the 24 new identity literals.
  - **Receipt naming:** the receipt's `*_public_sha256` key names over-claim. In each oracle-sized file, 958 of the 1,014 additions are 16-hex `fact_key` values, `sha256_hex(canonical_bytes(fact_payload))[:16]` (`representation.py:10460`); the other 56 are 64-hex. In the JSON, those 16-hex values occur 2,778 times in `provenance/target_key` and 12 times in `fact_qualifiers/fact_key`. The same form is already covered by the prior oracle's existing entries (958 of its 1,161 distinct 16-hex values; the rest are not detector hits).
  - **Unchanged by the run:** no line numbers needed refreshing, and no baseline key exists in both slash forms. Markdown hashes in backticks are not detector hits.
- **Unchanged:**
  - Awakened Plant stays uninstalled and unactivated, and no creature record was added.
  - Reader-retention residue stays deferred.
  - The partial-publication block stands.
  - Nothing was staged, committed, published or activated.
