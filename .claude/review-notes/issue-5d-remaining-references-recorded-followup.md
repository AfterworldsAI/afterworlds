# CRD Issue 5d — remaining-references replacement: recorded follow-up (#132, #137)

## Authorization

The Owner's statement, verbatim:

> I accept the exact remaining-references replacement candidate and its 29 reference resolutions, retaining 68 reference findings, 29 uncovered leaves, and the partial-publication block.

**Approval time:** the parent received this statement before its observation at 2026-09-29 06:59:40 UTC. No more precise message timestamp is claimed. Every recorded action below carries its real execution UTC time.

**Owner files.** The following were rechecked against the manifest before any write and again after all the writes (`.claude/_sp/rrr/recheck-final.txt`):

| File | SHA-256 |
|---|---|
| `remaining-references-owner-review.md` | `64fe900c19300d9ffc6422f38f5f0859ebe29a6df2677bdd186373c9e489ab59` |
| `remaining-references-owner-manifest.json` | `d4bf66e92e12619dbab6f9e3d434f1040ee42bee50f410055a3a10a6243818c2` |

Before the writes, all 10 manifest entries matched. After the writes, the only mismatches are the three this record expects:
- the oracle, which the Owner-authorized recording changed;
- `.secrets.baseline`, which the scoped scanner changed;
- `test_declared_record_expectations.py`, which moved as a dependent test.

## Final oracle

`src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json`

| State | SHA-256 | Batches / records / spans / review units / resolutions | Reference / uncovered-leaf findings |
|---|---|---|---|
| prior (Equipment recording) | `76a16103a08d…` (`EQUIPMENT_CITED.RECORDED_SHA256["resolved"]`) | 22 / 1826 / 10484 / 1459 / 1408 | 91 / 29 |
| remaining-recorded | `b61493266453bd4107dc729fafdfa1891208bf269f018baf7b4a9802ee1bb009` | 22 / 1832 / 10484 / 1459 / 1405 | 97 / 29 |
| **resolved (final, on disk)** | **`e0fd7690f519ec34dabcbba320936c20faff402fd94b925a2d4453316a29b14c`** | **22 / 1832 / 10484 / 1459 / 1434** | **68 / 29** |

- **Simulated state:** the reviewed simulated composition `10cf83a6b4b97b1370fd46a15af267bcf0cd41ba2903652f0d099cfb00cc45f5` is pinned only as the reviewed candidate. It is not a recorded hash and was not written.
- **Violations:** the final file has no reference-resolution violations.
- **Partial publication:** the partial-publication block stands.

## Recorded actions (real UTC)

The script is `.claude/review-notes/issue-5d-remaining-references-ACCEPT.py`. Logs are in `.claude/_sp/rrr/`.

| Action | Ran | Recorded time | Result |
|---|---|---|---|
| `--simulate` | 07:23:02–07:28:46Z | — | EXIT 0; nothing written |
| `record-remaining` | 07:28:53–07:35:49Z | `accepted_at` 2026-09-29T07:34:50Z | EXIT 0; sha `b6149326…` |
| `resolve-remaining` | 07:35:54–07:37:39Z | `resolved_at` 2026-09-29T07:37:07Z | wrote `e0fd7690…`; EXIT 1 on the post-write DELTA check (see below) |
| `--verify` | from 07:39:12Z | — | EXIT 0 |
| independent `recorded()` replay | finished 07:41:52Z | — | EXIT 0; equals the disk bytes |

**Recording shape.** The replacement is a fresh 22-batch chain over no prior, in unchanged batch order:
- The prior is rebuilt through `EQUIPMENT_CITED.recorded()`, not read from the file.
- 14 unchanged batches keep their recorded evidence.
- 8 changed proposals are accepted under the Owner. Their rule is the verbatim approval and their time is the real `accepted_at`.
- The 1,405 kept resolutions are re-applied verbatim.
- 3 re-keyed resolutions are dropped and re-drafted.
- The 29 drafts are then resolved: Owner as authorizer and reviewer, real `resolved_at`, and an `authorization_reference` naming the Owner review, the manifest, the constructor sha, the 8 candidate identities, the drafts sha and the prior sha.

### Disclosed check correction (after the write)

`resolve-remaining` wrote the resolved bytes, then its post-write DELTA check failed. The check compared the written delta with the reviewed `issue-5d-remaining-references-DELTA.txt` (`6e4e307d…`).

- **What differed:** both sides have 830 lines. 29 lines differ, and they differ only in `authorized_by` and `authorization_reference` on the 29 new resolution records (`.claude/_sp/rrr/deltadiff.py`).
- **Why:** `REPL.Delta.blank` blanks only the evidence fields (reviewer, accepted_at, resolved_at, rule). The reviewed DELTA therefore carries the simulated authorizer, and the recording carries the Owner's.
- **Correction:** `_authorizer_blank` now blanks those two keys on both sides before the line-for-line comparison. The check was corrected; the recorded bytes were not changed.
- **After the correction:** `--verify` and the independent replay both pass, and the delta equals the reviewed DELTA line for line (830).

## New proposal files

The 8 files are `.claude/review-notes/issue-5d-<batch>-remaining-references-PROPOSAL.json`. They were rendered from the constructor (`issue-5d-remaining-references-REPLACEMENT.py`, `7377fa56…`) and written between 07:18Z and 07:22Z. `_precheck` re-renders each one to its pinned bytes.

| Batch | File SHA-256 | Identity |
|---|---|---|
| checks-actions-rests | `389dd8ef…` | `fa646951…` |
| core-play-completion | `4d9fe61d…` | `cc0e3dd1…` |
| core-play-dependencies | `20387d70…` | `8fce546d…` |
| character-creation-foundations | `10d06eac…` | `fcee4afb…` |
| spellcasting | `7b0370d1…` | `5cc2bd87…` |
| gameplay-toolbox | `52c8a194…` | `fc81400f…` |
| magic-items | `626f80d9…` | `20e68a02…` |
| monsters | `5bdd535e…` | `791b52c3…` |

## Preservation

`_kept(prior, final)` returns nothing. It compares these, evidence included, as multisets:
- acceptance batches;
- span and review-unit records;
- reference-resolution records and resolutions.

It excludes only the 8 replaced batches, the 3 re-keyed ids and the 29 new ids. The other results:
- `_expectations` is `(10432, 10432, 38, 10, 0, 0)`.
- The 3 re-keys are unchanged in content.
- `_approvals(final)` is empty, so every new acceptance names the Owner and the approval.
- `_read_back(final) == RECORDED_AT`.

## Native replay

- `--verify` classifies the on-disk file as `resolved`. It rebuilds the file from the rebuilt prior and the recorded times, byte for byte.
- `recorded()` independently reproduces the disk bytes (`replay.txt`).

## Dependent gates moved

Only the tests invalidated by the new committed bytes were moved. Historical assertions and helper evidence are kept. Each earlier recording is still checked at its own recorded bytes through the hub's rebuilt states.

**Hub: `tests/ingestion/mechanical/_replacement_chain.py`**
- Added `REMAINING`.
- `COMMITTED_SHA256` is now `REMAINING.RECORDED_SHA256["resolved"]`.
- Added `equipment_recorded()`, which is `REMAINING.prior()`.

**`test_animals_proposal.py`**
- The Animals recording is kept in `equipment_recorded()`; before, it was checked against the file on disk.
- The Equipment test is now historical. It checks `equipment_recorded()` at its recorded sha, with the same counts, findings, approvals and read-back.
- New test: `test_the_committed_oracle_records_the_remaining_references`. It checks:
  - the file sha and the production resolver's bytes;
  - `REMAINING.recorded()` equals the file;
  - `_kept`, `_approvals`, `_read_back` and the batch (identity, rule) pairs;
  - `_expectations`, the counts, 0 violations and the (68, 29) findings.

**Other moved tests**
- `test_monsters_proposal.py`: the Animals recording is kept outside Equipment in `equipment_recorded()`.
- `test_character_origins_feats_acceptance.py`: the twelve-batch state is kept whole in `equipment_recorded()`. The committed bytes and sha checks are unchanged.
- `test_committed_accepted_authority.py`, the named set:
  - adds the 8 recorded identities;
  - drops the replaced regenerated identities: the 7 in `BATCHES`, the superseded Monsters identity, and the 5 clean-restart constants that resolve to the same replaced proposals.
- `test_source_release_readiness.py`: 1408 → 1434 resolutions.
- `test_declared_record_expectations.py`: the re-derived identities are compared with the replacement chain's approved identities (hub `identity()`), instead of whatever the committed file currently names. This file is in the Owner manifest, so its mismatch there is expected.

### Test evidence

All runs used `--no-cov -q -p no:cacheprovider`, `RTK_DISABLED=1` and the venv python.

**Before the test moves (after the hub change)**
- `test_accepted_inputs`, `test_oracle`, `test_packaging`, `tests/test_quarantine_5c_5d.py`, `test_subclass_refusal_at_authority_seams` and `test_checks_actions_rests_proposal`: 377 passed.
- `test_spell_descriptions_proposal` and `test_spellcasting_proposal`: 60 passed.
- `test_magic_items_proposal`: 34 passed.
- `test_rules_glossary_completion_proposal`: 34 passed.
- `test_classes_proposal`: 27 passed.
- `test_gameplay_toolbox_proposal`: 16 passed.
- The other runs had 7 failures, all stale committed-file pins. They are the tests moved above.

**After the test moves**

`t11.txt` ran the six moved files: 82 passed and 2 failed (942 s). Neither failure is a defect:
- `test_monsters_proposal::test_accepted_then_resolved_in_memory_preserves_everything` failed because I edited `oracles/README.md` mid-run. The test snapshots the oracles directory before and after the run.
- `test_committed_accepted_authority::test_no_refused_candidate_is_selectable` failed because the named set still carried five clean-restart constants. They resolve to the replaced `REGEN-3fe24ff6` proposals: checks-actions-rests, core-play-completion, core-play-dependencies, character-creation-foundations and spellcasting. Those five were dropped from the named set with a comment, and the constants remain.

`t12.txt` reran both, 08:58–09:02:59Z: 2 passed.

## Secrets baseline (scoped)

| | |
|---|---|
| Before | `6977694506a440f2de18ce19028ad70da5220db44fe09e527f413125b6a11c7e` (the manifest value; `apply.py` asserted it before writing) |
| After | `83348db4f892877b21f922a71fb69e35856d480ca8367d0160e14125b6e58f92` (staged by name; index blob equals the worktree) |
| Added / pruned / line-moved | 113 / 8 / 969 |
| Entries | 5612 → 5717 |
| Files | 127 → 136: the ACCEPT script and the 8 PROPOSALs, each added at the end |

**Delta by file**

| File | Added | Pruned | Line moves |
|---|---|---|---|
| ACCEPT script | 24 | 0 | 0 |
| 8 PROPOSALs (total) | 81 (23 / 11 / 17 / 6 / 6 / 6 / 6 / 6) | 0 | 0 |
| oracle | 8 | 8 | 963 |
| `test_animals_proposal.py` | 0 | 0 | 3 |
| `test_monsters_proposal.py` | 0 | 0 | 3 |

**Preserved:** top-level settings, plugins, filters, `version` and `generated_at`; every other file's entries; the existing key order, including the 17 empty-list keys; `is_verified` is false on the added entries.

**Scope.** Every touched file was rescanned under the baseline's own plugins and filters (`.claude/_sp/rrr/bl/bl_scan.py`, which uses a private settings copy):
- the ACCEPT script and the 8 PROPOSALs;
- the oracle and the oracle README;
- the hub and the 6 moved tests;
- this note.

The README, the hub, 4 of the moved tests and this note have no findings.

**Evidence that every added value is public**
- **ACCEPT, 24 values.** Each is one of the following (`verify.json`):
  - a proposal file SHA-256 or proposal identity;
  - the constructor, DRAFTS, DELTA or oracle SHA-256;
  - the Owner review or manifest SHA-256, rechecked against those files;
  - the intermediate or simulated state SHA printed by the run logs.
- **PROPOSALs, 81 values.** Every hash is already baselined under another file, meaning the same public values in earlier proposals. The 33 not recoverable as hex strings are also already baselined elsewhere.
- **Oracle, 8 added.** These are the 8 new proposal identities, already baselined elsewhere.
- **Oracle, 8 pruned.** These are the 8 replaced identities, which the rescan no longer finds in the oracle.

**Correction during the run.** The first `apply.py` pass dropped the pre-existing empty key for `test_character_origins_feats_acceptance.py`. `restore_empty.py` restored it in place before the hook ran, and `apply.py` now keeps existing empty keys.

**Hook.** `detect-secrets-hook --baseline .secrets.baseline` ran on all 19 files plus the baseline, twice (`hook.log`):
- run 1: exit 0 at 09:16:09Z;
- run 2: exit 0 at 09:18:36Z;
- the SHA was stable.

An earlier pair of runs exited 1 only because the baseline was unstaged.

**Not done:** no `scan --baseline` was run, and no allowlist pragma was added.

The deltas are in `.claude/_sp/rrr/bl/baseline-delta.json` and `baseline-delta-2.json` (the latter empty).

## Scope-report corrections

These are factual corrections to the earlier scope report, not a new fix loop:
- The scope was 21 historical identity comparisons, not all generator bytes.
- The baseline prior moves were +14 / −1 / 32 moves.
- The accepted generators already used declared records.

## Disclosures (nonblocking)

- Two ambiguous owner guards lack dedicated tests.
- pip-audit and the expanded mypy run remain non-green. No full-green claim is made.
- These consumers now fail closed on the new file, as intended for superseded recordings:
  - `RR.main()` / `RR.accepted()` assert the prior `76a16103…`.
  - `issue-5d-equipment-cited-targets-ACCEPT.py --verify` refuses the file. It was run 08:56:36–08:57:30Z and exited 1 with `resolved artifact drifted` (`eqc-verify.txt`).
  - `GEN.main()`.

  The per-recording tests reach those recordings through the hub's rebuilt states instead.

## Blockers and retention

- The partial-publication block stands: 68 reference findings and 29 uncovered leaves remain.
- The release's cross-file part order is unchanged. Animals still precedes its governing Monsters rules, and that remains a separate bounded correction.
- Nothing was published, activated, written to a shared DB or written to Chroma. There were no commits, pushes or merges.

Untouched:
- the 36 staged deletions and the 4 stashes;
- the quarantine corpus;
- `issue-5d-source-correction-REPLACEMENT-PACKET.md`;
- the root `afterworlds.db`;
- the `574662e9` oracle;
- the pre-existing modification of `issue-5d-core-play-completion-generator.py` and other unrelated modifications.

`.secrets.baseline` is staged by name only.
