# CRD Issue 5d — Finite reference routes: recorded follow-up (#132, #137)

## Authorization

The Owner's statement, verbatim:

> I accept the exact ten-reference route batch and its combat-batch replacement, retaining 23 reference findings, zero uncovered leaves, and the partial-publication block.

**Approval time.** The statement came before 2026-10-02T09:16:10Z, which is when the parent verified it. No more precise approval time is claimed. `APPROVAL_BEFORE` in the script is documentary and is never recorded. The recorded action carries its real execution time in UTC. No renewed Owner approval was sought, and a Codex review follows.

**Manifest.** The Owner manifest `finite-reference-routes-owner-manifest.json` was verified by the parent outside the repository. It is named in the authorization reference, but not pinned by sha, because its sha is not available here.

**Owner files.** The ACCEPT script asserts the constructor pin at import. It asserts the PROPOSAL, DELTA, review and combat pins on every run.

| File | SHA-256 |
|---|---|
| `issue-5d-finite-reference-routes-REPLACEMENT.py` (constructor) | `afb1cf886296c59693aebd07fa97fb29a3bab85621e3d94fa57622b83e9fe3ec` |
| `issue-5d-finite-reference-routes-PROPOSAL.json` | `404bee285f9695bfdffe5ff5b21d2a2ef2b443cf370a1bdfb3df5332470482d8` |
| `issue-5d-combat-damage-breaking-finite-reference-routes-PROPOSAL.json` | `1cc561616526b271728f0d8b0b5f2c7490b76ee76cf684e33903512daecf48f5` (identity `cfd193513e8c769d45b42f4a6dfa420481b43f064b45fef564f1e5c5eaac8c23`, replaces `ce7a80ff95d8ae361d2a76612b85d7f5d546c57755588d3084a6a41a4f8a7de2`) |
| `issue-5d-finite-reference-routes-DELTA.txt` | `e90abfff64caae94ac4f0fe16f5bc8ef2099ccb702e874fc41a6b874a01d9bca` |
| `issue-5d-finite-reference-routes-review.md` (packet) | `17fc80f63e0f956229fb63733629802a2eb2e884c5d586c27ac8f80f28ea6b15` |

## Final oracle

`src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json`

| State | SHA-256 | Schema | Batches / records / spans / units / resolutions | Reference / uncovered-leaf / other findings |
|---|---|---|---|---|
| prior (reference-alternatives recording) | `cc994e1badee3baf733d2df5d5c88903ad96b4ddd0172f52111ecdf0b4c1f190` | 17 | 24 / 1835 / 10492 / 1476 / 1453 | 33 / 0 / 0 |
| **recorded (final, on disk)** | **`e9678ab30c27ba92deda5757de4be082aba8bfc44690b6bf94f7bc1f747a45ca`** | **17** (unchanged, no lift) | **24 / 1835 / 10493 / 1476 / 1463** | **23 / 0 / 0** |

There are 0 reference-resolution violations, and the partial-publication block stands.

**Simulated state.** `b6caeb91e7886d3e0747290751315e59a2852f6e904090b34c2f5a7d14f00f28` is the reviewed constructor's composition under the simulated reviewer. It was checked by `--simulate`, and again on the record path before the write. It was never written.

## Recorded action (real UTC)

**Script.** `.claude/review-notes/issue-5d-finite-reference-routes-ACCEPT.py`. Its final sha is `54e991c327a50838ba3b8687ebe75ce99162f560e1f6a0f1c8f95fd0597e403b`, taken after `RECORDED_AT` and `RECORDED_SHA256["recorded"]` were pinned from the values the run printed and read back.

**Logs.** All logs are in `.claude/_sp/frr/`. Each run went through `run.py`, which writes `NAME.log` (stdout and stderr) and `NAME.exit` (the exit code).

| Action | Log | Result |
|---|---|---|
| `--simulate` (in memory, nothing written; 09:38:25Z–09:43:06Z) | `accept-simulate.log` | EXIT 0. Simulated bytes `b6caeb91…`; every check passes at the placeholder time. The log of the two earlier failing runs (EXIT 1, verifier defects below) was overwritten by this run. Nothing was written by any of them. |
| actual-vs-simulated dry run (`rec/simdiff_dry.py`, 09:46:57Z–09:50:19Z) | `simdiff-dry.log` | EXIT 0. An earlier run exited 1 on list misalignment, fixed below. |
| `record-finite-reference-routes`, first attempt (from 09:50:29Z) | `accept-record-interrupted-0950.log` (preserved) | **Interrupted** by session teardown before any write. It left no exit file and no process, and the oracle was still `cc994e1b…`. |
| recovery checks | — | The oracle sha was `cc994e1b…`, no python process or competing writer existed, and the interrupted log was preserved. The saved ACCEPT script, prior bytes, simulate result and dry-run result were reused, not rebuilt. |
| `record-finite-reference-routes`, recovery run, detached (09:55:34Z–10:03:12Z) | `accept-record.log` | **EXIT 0.** The pre-write checks passed, and there was one native write at **2026-10-02T10:00:20Z** with sha **`e9678ab3…`**. The post-write `_state` recomposition matched, every check was True, and the file reloaded to the same bytes. |
| `--verify .claude/_sp/frr/rec/prior-oracle.json` on the pinned script (10:03:32Z–10:06:43Z) | `accept-verify.log` | EXIT 0, with every line True. |

**Verifier fixes before the write.** None of these touches the recording path, and nothing was re-recorded.

1. **Order check.** The batch order was first compared against `REPL._proposals()`. That does not match the recorded chain, because later steps re-accept batches. It now compares against `prior().batches`, which is the Equipment class-eligibility pattern.
2. **DELTA.** The simulated delta equals the reviewed DELTA byte for byte. The DELTA blanks the reviewer and `resolved_at`, but not `authorized_by` or `authorization_reference`. So the Owner delta is the reviewed DELTA with exactly 10 occurrences of the simulated pair replaced by the Owner pair. The check asserts that substitution: `raw.count(simulated) == 10`, and the Owner pair is absent from the reviewed bytes.
3. **`sim_diff` alignment.** Acceptance records are sorted with `accepted_at` in the key, so the simulated and actual lists are ordered differently. `_aligned` now sorts lists of dicts by their non-evidence JSON, and asserts those keys are unique. It does this before the leaf walk. The full-payload comparison is kept.

**Prior.** Before the write, the prior bytes were saved to `.claude/_sp/frr/rec/prior-oracle.json` (scratch, sha `cc994e1b…`, verified). The oracle is untracked, so the prior also exists as the sha-asserted replay `FINITE_REFERENCE_ROUTES.prior()`, which `reference_alternatives_recorded()` exposes for the tests.

**Recording shape.** The script made one native write, which did the following:

- It replaced only the combat-damage-breaking batch, at its existing position: `ce7a80ff…` → `cfd19351…`. The batch's rule is the verbatim statement, and its records and review-unit records name `Ravenlok (Owner)` at the recorded time.
- It added the 10 reviewed resolutions (94 routes, 121 destinations) through `resolve_references`. Each has `reviewer` and `authorized_by` set to `Ravenlok (Owner)`, `authorization_reference` set to the decision (files, shas and the verbatim statement), and `resolved_at` set to the clock, read once.
- It did not re-accept, re-key or drop any other batch, span, unit or resolution. The corpus was not reordered.

**Actual vs simulated** (`accept-record.log`, leaf walk over the two aligned payloads). Only the approval and time evidence differs:

| Collection | Field | Count | Simulated | Recorded |
|---|---|---|---|---|
| `acceptance.batches` | `rule` | 1 | `SIMULATION ONLY: …` | the verbatim statement |
| `acceptance.records` | `accepted_at` / `reviewer` | 163 / 163 | `2026-10-01T00:00:00Z` / `SIMULATION - not an Owner approval` | `2026-10-02T10:00:20Z` / `Ravenlok (Owner)` |
| `acceptance.review_unit_records` | `accepted_at` / `reviewer` | 5 / 5 | as above | as above |
| `acceptance.reference_resolution_records` | `resolved_at`, `reviewer`, `authorized_by`, `authorization_reference` | 10 each | simulated values | the Owner values and this decision |

Nothing else differs.

## Preservation and replay evidence

This evidence is from `accept-record.log` and `accept-verify.log`.

- **Counts.** The counts are 24 / 1835 / 10493 / 1476 / 1463. Schema 17 is unchanged, with no lift.
- **Findings.** Findings go from 33 / 0 / 0 to 23 / 0 / 0, compared as multisets. Exactly 10 were cleared, and none are new.
- **Batches.** The 23 other batches' identities are unchanged. Their approvals and evidence are verbatim.
- **Combat batch.** Outside combat, everything is kept, evidence included. The lost/added counts reflect only the one replaced combat batch: spans (0, 1); units, obligations, batches and schema anchors (1, 1); components, prose bindings and provenance (0, 1); records (162, 163); review-unit records (5, 5); resolutions and resolution records (0, 10).
- **Resolutions.** The 1453 prior resolutions are verbatim, in canonical order. Their 1453 historical approvals are verbatim, in order. The 10 new resolutions are exactly the reviewed PROPOSAL's: (10, 94, 121).
- **History.** Lifts and policy history are unchanged.
- **Delta.** The delta is the reviewed DELTA with the 10 new resolutions' authorizer and reference set to the Owner's.
- **Reload.** The file reloads to the same bytes.

## Historical scripts now refuse

| Script | Log | Result |
|---|---|---|
| finite-reference-routes constructor, check mode (10:03:32Z–10:03:35Z) | `refusal-constructor-check.log` | EXIT 1, `AssertionError: accepted changed`. This is the expected refusal: its input pin is the prior file. |
| Equipment class-eligibility `--verify` (10:03:32Z–10:05:54Z) | `refusal-ece-verify.log` | EXIT 1, `AssertionError: drifted`. This is the expected refusal. |
| reference-alternatives `--verify` (10:03:32Z–10:05:54Z) | `refusal-ra-verify.log` | EXIT 1, but with `ValueError: too many values to unpack (expected 1)` at its `_read_back` (line 215, `(at,) = {a.resolved_at for a in new}`), not `drifted`. Its "new" resolutions now span two resolved times. It fails closed, but with a different message. The historical script was not modified. |

## Moved pins (historical checks kept)

| File | Change |
|---|---|
| `tests/ingestion/mechanical/_replacement_chain.py` | Loads `FINITE_REFERENCE_ROUTES` (module `finite_reference_routes_accept`). `COMMITTED_SHA256` now points to its recorded sha. Adds `reference_alternatives_recorded()`, the replayed prior. Docstring updated. |
| `test_animals_proposal.py` | The live reference-alternatives test becomes the historical `test_the_reference_alternatives_recording_rebuilds`: replay = `cc994e1b…`, plus RA `_read_back`, `_approvals`, `_check`, and 33 / 0. New: `test_the_committed_oracle_records_finite_reference_routes`. It checks the sha, reproduces the committed inputs, and checks `_read_back == RECORDED_AT`. It also reproduces the bytes from `recorded(OWNER, RECORDED_AT)`, checks that every combat and new-resolution acceptance names the Owner and this decision (`_approvals` is empty), runs `_check` over the replayed prior, and checks 23 / 0. |
| `test_finite_reference_routes_candidate.py` | The `persisted` fixture reads the recorded oracle. Its docstring now calls it the Owner-accepted recording, still unpublished. |
| `test_committed_accepted_authority.py` | `test_no_refused_candidate_is_selectable` now names the combat batch's replacement. The regenerated combat identity is excluded from the current-release set, `FINITE_REFERENCE_ROUTES.COMBAT_IDENTITY` is added, and the clean-restart entry `COMBAT_DAMAGE_BREAKING_PROPOSAL` (the same regenerated proposal, `ce7a80ff…`) is replaced by a comment. This follows the pattern of the earlier replaced batches. The pin was missed before the focused pytest and found by it (below). |
| `test_source_release_readiness.py` | 10492 → 10493 spans and 1453 → 1463 resolutions. Docstring updated. |
| `src/.../oracles/README.md` | Current state updated (`e9678ab3…`, 1463, 23). The reference-alternatives history entry is completed, and a finite-reference-routes entry is added. Reference-alternatives and this constructor's check mode are added to the list of scripts that refuse. |

**ADR-005d is not edited.** The ADR records recordings only when they accept amendments. This recording accepts no amendment and no schema change. The Equipment class-eligibility and Playing the Game recordings have no ADR entries either.

## Gates (raw)

The gate logs are in `.claude/_sp/frr/rec/`.

- **ACCEPT script.** Black 0, Ruff 0 and `mypy --strict` (`MYPYPATH=src`) 0, before and after pinning (`mypy-accept.log`).
- **Black `--check` and Ruff on the ACCEPT script and the four test files edited before the pytest** (`black.log`, `ruff.log`). Both EXIT 0.
- **`test_committed_accepted_authority.py`, after its fix** (`black2.log`, `ruff2.log`, `mypy2.log`). Black `--check` 0, Ruff 0 and `mypy --strict` 0.
- **`mypy --strict` over the same five files** (`mypy.log`). EXIT 1, 11 errors in 3 files. None are in lines this change added:
  - `conftest.py:763/764/1010`;
  - `test_character_origins_feats_proposal.py:890/1762/1766`;
  - the older Animals test, `test_animals_proposal.py:421–433`.

  This falls under the standing non-green expanded mypy. `mypy src/` was not rerun, because no `src/` code changed: only the untracked oracle JSON and the README did.
- **Focused pytest** (`pytest-rec.log`; 17 node ids in `rec/pytest.ids`; `-p no:cacheprovider --no-cov`; started 10:06:57Z, detached). Ran 10:06:57Z–10:35:33Z. **44 passed, 1 failed in 1711.09s**, EXIT 1.
  - The failure is `test_committed_accepted_authority.py::test_no_refused_candidate_is_selectable`. Its expected set still named the replaced combat identity `ce7a80ff…`, and the release now names `cfd19351…`. This was a missed dependent pin, not a recording defect.
  - First fix (`pytest-rec2.log`, 10:36:25Z–10:36:39Z): it excluded the regenerated combat identity and added the new one. **1 failed** (EXIT 1): `ce7a80ff…` was still expected, through the clean-restart entry `COMBAT_DAMAGE_BREAKING_PROPOSAL`.
  - Second fix, which removes that entry (`pytest-rec3.log`, ends 10:37:27Z): **1 passed in 12.89s**, EXIT 0.
  - The other 44 tests do not import or read this test file.
- **Sibling audit for dependent pins naming the replaced combat identity.**
  - `grep` finds no literal `ce7a80ff` in `tests/` or `src/` Python.
  - The only other enumeration of the release's batches through the chain modules is `test_animals_proposal.py::test_the_playing_the_game_atoms_recording_rebuilds`. It is a historical replay of an earlier recording, so it is already safe. It was not in this run.
  - The advisor-prompted bounded check looked for siblings that name the combat batch through `BATCHES`, `proposal_path` or `identity` rather than by sha. Two filters were applied: every file mentioning `combat-damage-breaking` that also reads the live oracle, and every caller of `committed_inputs_for` or `ACCEPTED_PATH`. Dispositions:
    - **Already safe, reads another release.** In `test_committed_accepted_authority.py`, the other tests read `srd-5-2-1-corpus-36b786d8-fa2.json`, not the live file. `test_the_release_resolves_to_this_sole_committed_artifact` and `test_a_later_batch_extended_this_artifact_rather_than_adding_one` list file names or read that release. `test_accepted_inputs.py` asserts file names and quarantine, and reads the 36b786d8 file.
    - **Already safe, no live read.** `test_combat_damage_breaking_{acceptance,proposal}.py` and the checks/core-play/character-creation acceptance and proposal files mention `3fe24ff6` only in comments. They read replays, not the live file.
    - **Already safe, ran in the focused pytest.** The `committed_oracle_records…` tests in classes, gameplay toolbox, magic items, monsters, rules glossary and spell descriptions, plus character-origins-feats and checks-actions-rests, are in the 17 ids and passed.
    - **Ran, passed.** `test_equipment_acceptance.py::test_the_committed_file_preserves_both_steps_replayed_over_the_prior` and `test_spellcasting_acceptance.py::` (same name) read the live file through the resolver. They were run as `pytest-rec4.log`. The first launch (10:43:23Z) was interrupted by session teardown with no result; its log is preserved as `pytest-rec4-interrupted-1043.log`. The relaunch ran 10:45:21Z–10:46:36Z: **2 passed in 72.29s**, EXIT 0.
- **Last writes.** The test files were last written 09:50:46Z–09:56:47Z, the ACCEPT script at 10:03:24Z and the README at 10:03:44Z. All of these come before the pytest start. `test_committed_accepted_authority.py` was edited after that run, and only its one failing test was rerun.
- **LF only.** All new or edited files have 0 CR.
- **Not run:** the broad suite. No green is claimed.
- **Deferred, not green:** pip-audit, expanded mypy and coverage.
- **detect-secrets.** A scoped scan, run with `PYTHONUTF8=1` under the baseline's own plugins and filters, over the nine files of `.claude/_sp/frr/rec/bl/files.txt`: the ACCEPT script, this note, the oracle, the README and the five edited test files. Logs: `rec-blscan.log`, `rec-blscan2.log`. The oracle's 1014 findings were scanned, so it was not skipped.
  - **11 new public hashes; every value was recovered and named.**
    - 9 are the ACCEPT script's pins: constructor, combat sha, combat identity, combat replaces, PROPOSAL, DELTA, review, simulated and recorded.
    - 2 are in the oracle: the new combat batch's `proposal_identity` `cfd19351…`, and its `semantic_diff_hash` `fd078809…`, which is in the reviewed DELTA.
  - **2 obsolete, pruned.** Both are in the oracle: the replaced combat identity `ce7a80ff…` and its old `semantic_diff_hash`.
  - **999 line numbers refreshed:** 996 in the oracle and 3 in `test_animals_proposal.py`.
  - **Scope.** Only the `results` entries of scanned files changed; the other keys are identical (`rec/bl/scope.py`).
  - **Baseline.** It went from `ba8ea340c50595feb99c65dbfce4a12c4b3285414c98e174923a94409bb88f74` to `6b3b3fbffa6e91037b57235f5790e071bdd46b9d03d37d853d55533c620a15b0`, in the working tree only. It is **not staged**: the index blob is still `4884b897`.
  - **Rescan.** After the test fix and this note's edits, the rescan found 0 new, 0 obsolete and 0 moved, and the bytes were unchanged (`rec-blapply2.log`). The final hook runs are in `.claude/_sp/frr/rec/final-hook.log` and the final report.

## Limits

- Nothing is committed, pushed, merged, published or activated.
- No shared DB was written.
- The protected packet, quarantine and index are untouched.
- The release order is scheduled for one bounded Owner pass after the packets, before publication. It is not a prerequisite for this recording.
- 23 reference findings remain, and the partial-publication block stands.
- No other target-contract proposal is accepted.
