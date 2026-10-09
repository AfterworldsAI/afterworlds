# CRD Issue 5d — framing coverage: recorded follow-up (#132, #137)

## Authorization

The Owner's statement, verbatim:

> I accept the exact framing-coverage proposal, including its glossary conventions and reviewed framing exclusions.

**Approval time:** the parent received this statement before its observation at 2026-09-29T12:33:01Z. No more precise message timestamp is claimed. The recorded action below carries its real execution UTC time.

**Owner files.** Checked against the manifest before the first write (`manifest-prewrite.txt`, 12:45:37Z) and again after all writes (see "Final manifest recheck"):

| File | SHA-256 |
|---|---|
| `framing-coverage-owner-review.md` | `7ed0ef9cddd70c592076f1c769c089fc4313a3d7b44594d7c72dd6134b130511` |
| `framing-coverage-owner-manifest.json` | `461bf0e412221c3f95ad18df48766d89ab29f99fc0a7bf602bfbb99a781fd2cc` |

Before the first write, all 8 task pins matched: generator `e64617cb…`, PROPOSAL `5589a262…`, DELTA `67d6f798…`, review.md `f460a957…`, Owner review `7ed0ef9c…`, the oracle `96e90f71…` and `.secrets.baseline` `7a0327fa…`, plus the proposal identity `a7a98598…a70`, which the script checks on load.

## Final oracle

`src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json`

| State | SHA-256 | Batches / records / spans / review units / resolutions | Reference / uncovered-leaf findings |
|---|---|---|---|
| prior (Animals catalogue recording) | `96e90f71ddde22da6424eef9875b51eb36620876dfee635546e1d6872594a91b` | 22 / 1833 / 10485 / 1460 / 1438 | 64 / 28 |
| **recorded (final, on disk)** | **`15478aa5ea712b9946999ff865283cd12b36dd4f917137a76c225543066b8922`** | **23 / 1834 / 10491 / 1475 / 1438** | **64 / 0** |

- **Simulated state.** The simulated composition, `0c7e85079ca56a7b6f7c79cf880ca378ee0409a2d442b640a3f17568b59b0097`, is pinned only as the reviewed candidate; it was never written, and the recorded bytes differ from it. It was derived independently by the generator's own `accepted()` over the committed file as loaded (`simulate-crosscheck.txt`), not only by the ACCEPT script.
- **Violations.** Other findings: 0. Reference-resolution violations: 0. Dangling component claims: none.
- **Partial publication.** The partial-publication block stands.

## Recorded action (real UTC)

The script is `.claude/review-notes/issue-5d-framing-coverage-ACCEPT.py`, sha `4e1d032f…` final (after pinning and the multiset fix below). Logs are in `.claude/_sp/fcr/`. Times are log completion times.

| Action | Finished | Recorded time | Result |
|---|---|---|---|
| `--simulate`, run 1 (`simulate-1.txt`) | 12:41:05Z | — | EXIT 1: `SIMULATED_SHA256` not yet pinned (by design); printed `0c7e8507…`. Nothing written. |
| generator cross-check (`simulate-crosscheck.txt`) | 12:41:24Z | — | EXIT 0; `GEN.accepted(load_accepted_inputs(file), proposal)` = `0c7e8507…` |
| `--simulate`, run 2 (`simulate.txt`) | 12:43:28Z | — | EXIT 0. Nothing written. |
| manifest recheck (`manifest-prewrite.txt`) | 12:45:37Z | — | 8/8 match |
| `record-framing` (`record.txt`) | 12:48:19Z | `accepted_at` 2026-09-29T12:47:38Z | EXIT 0; `15478aa5…`; post-write `_state()` and `verify` pass |
| `--verify` against the pins (`verify.txt`) | 12:50:52Z | — | EXIT 0 |
| `--verify`, final script, `PYTHONHASHSEED=987` (`verify-final.txt`) | 14:24:41Z | — | EXIT 0 |

The two `--simulate` runs preceded a black reformat, a typed `_acceptances` helper (mypy) and the two post-write pin edits. `record-framing` runs the same `_precheck` on the script's then-final logic before writing, and `--verify` ran on the final pinned script. `RECORDED_AT` and `RECORDED_SHA256` were pinned after the write from the time the run printed and read back. Nothing was re-recorded.

**Recording shape.**
- One native `accept_proposal` of the exact proposal (`PROPOSAL` `5589a262…`, loaded with `expected_identity`) as batch `framing-coverage` over the prior, with `rule` = the verbatim Owner statement, `reviewer` = the Owner, and the real `accepted_at`. No chain is rebuilt, no batch replaced, no resolution added.
- **Prior.** The oracle is untracked, so after the write the `96e90f71…` state exists only as the Animals catalogue replay (`ANIMALS_CATALOGUE.recorded()`, sha-asserted). Before the write `_precheck` showed the composition over that replay equals the composition over the committed file as loaded, byte for byte.
- **Real vs simulated evidence.** `_precheck` (before the write) holds the simulated composition to `0c7e8507…`, then composes under the Owner at a placeholder time and runs every post-write check on it: `_check` and `_approvals` must pass, its bytes must differ from the simulated bytes. `verify` refuses the placeholder time and the simulated bytes in the file. `_approvals` checks that the batch rule is exactly the verbatim statement and every span and review-unit acceptance of the batch names the Owner.
- **Unit-only representation.** The 20 framing leaves outside Glossary Conventions are covered by review units alone, as authorized; no span lies on them.

## Preservation

- **`MC._preserved(prior payload, final payload)` is empty.** It walks the whole prior payload recursively (every top-level key, lists as multisets, evidence included): all 22 batches, 1833 records and 1438 resolutions with their recorded approvals are kept.
- **Batches.** The sorted (batch, identity) pairs are the prior's plus `(framing-coverage, a7a98598…)`.
- **Delta.** `EQ.Delta(prior, final).report()` plus `GEN.unit_report` equals the reviewed DELTA (`67d6f798…`) line for line, 326 lines, evidence blanked; 0 removals in every collection.
- **Findings.** (64, 0), other 0; the 64 reference findings equal the prior's string for string.
- **`_read_back(final) == RECORDED_AT`** (`2026-09-29T12:47:38Z`), one `accepted_at` across the batch.
- **Glossary conventions and the abbreviation table** are kept exactly as reviewed (the DELTA prints them in full). The reviewed exclusions do not waive licensing obligations and do not bar future catalogue targets over the covered headings.

## Dependent gates moved

Only the pins the new committed bytes invalidate were moved. Historical checks are kept.

- **`tests/ingestion/mechanical/_replacement_chain.py`**: loads `FRAMING` (the ACCEPT script); `COMMITTED_SHA256` is now `FRAMING.RECORDED_SHA256["recorded"]`; adds `animals_catalogue_recorded()` = `FRAMING.prior()`; docstring updated.
- **`test_animals_proposal.py`**:
  - The Animals catalogue test is now historical (`test_the_animals_catalogue_recording_is_kept`): it checks `animals_catalogue_recorded()` at `96e90f71…` with the same kept, approvals, read-back, identity, `_reowned`, `_expectations`, counts and (64, 28) assertions. Its file read and production-resolver check moved to the new test.
  - The new `test_the_committed_oracle_records_framing_coverage` checks the file sha and the production resolver's bytes; that `FRAMING.composed(prior, OWNER, RECORDED_AT)` equals the file; `_approvals`; the batch (identity, rule); `FRAMING._check("recorded", …)`; and (64, 0) findings.
- **`test_committed_accepted_authority.py`**: `FRAMING.IDENTITY` added to the named identity set (hub import extended).
- **`test_source_release_readiness.py`**: `framing-coverage` added to the batch set; 10485 → 10491 spans; resolutions stay 1438; docstring updated.
- **`test_gameplay_toolbox_proposal.py`**: its committed batch-set pin gains `framing-coverage`. This livepin was missed in the first pass and surfaced by the focused run below.
- **`oracles/README.md`**: the current-file paragraph was updated before any test ran.

### Test evidence

All runs used `RTK_DISABLED=1` and the venv python, `-q -p no:cacheprovider`, with no edits to the oracles directory during the runs.

| Log | Files | Result | Ran | Exit |
|---|---|---|---|---|
| `pytest-focused.txt` | `test_committed_accepted_authority`, `test_source_release_readiness`, `test_declared_record_expectations`, `test_animals_proposal`, `test_monsters_proposal`, `test_character_origins_feats_acceptance`, `test_gameplay_toolbox_proposal`, `test_magic_items_proposal` (serial, coverage on) | 134 passed, 2 failed; coverage fail-under (47% < 80%, expected for a focused subset) | 12:52:13–14:20:13Z | 1 |
| `pytest-rerun.txt` | the two failures plus `test_the_animals_catalogue_recording_is_kept`, `--no-cov` | 3 passed | 14:22:59–14:27:26Z | 0 |

**The two failures, and what changed.**
- `test_the_committed_oracle_records_framing_coverage`: the ACCEPT script's `_check` compared the 64 reference findings as ordered lists. Their order follows set iteration, so it varies with the hash seed (`refs-order-diagnosis.txt`: ordered False, multiset True, 64/64). The recording-time checks passed on a matching order. `_check` now compares them as multisets, as the reviewed generator did. The recorded bytes, evidence and every other check are unchanged; `verify-final.txt` reran the full check under a different hash seed.
- `test_gameplay_toolbox_proposal::test_the_committed_oracle_records_the_owner_acceptance`: a current batch-set livepin missing `framing-coverage` (moved above).

The other 134 tests were not rerun after these two edits; neither edit touches code they exercise.

Lint (final): ACCEPT script black, ruff and mypy `--strict` (`MYPYPATH=src`) exit 0; hub and the four moved tests black and ruff exit 0. No broad suite was run.

**Consumers that now fail closed (intended for superseded recordings):** `issue-5d-animals-part-catalogue-ACCEPT.py --verify` exited 1 with `unrecognized batches [... 'framing-coverage' ...]` (`animals-catalogue-verify.txt`, 12:52:05Z). Its recording stays reachable through the hub's `animals_catalogue_recorded()`.

## Not claimed

- **Consumer probes.** DISABLE was demonstrated in the reviewed packet. No new REPLACE coverage is claimed.
- **Deferred gates.** pip-audit and expanded mypy remain non-green and deferred. No all-green claim is made.

## Secrets baseline (scoped)

Tooling is in `.claude/_sp/fcr/bl/`: `bl_scan.py` does a scoped scan of the 9 files in `files.txt` with the baseline's own plugins and filters, and `apply.py` merges the scan into the baseline.

- **Result.** The baseline went from `7a0327fa…cbdd` to `127eba6c…e58d`. `apply.txt` reports added 11, pruned 0, moved 984 (line-number moves only: 981 in the oracle, 3 in `test_animals_proposal.py`), 5759 entries over 142 files.
- **New entries (`preservation.txt`).** All 11 are public hashes:
  - 9 in the ACCEPT script: its sha pins for the generator, PROPOSAL, IDENTITY, DELTA, review.md, the simulated and recorded oracle bytes, and the two Owner files.
  - 2 in the oracle: the proposal identity `a7a98598…` and the batch's `semantic_diff_hash`, both printed in the reviewed DELTA.
- **Preservation against the index copy.** Top-level key order, `version`, `plugins_used`, `filters_used` and `generated_at` are unchanged. All 139 other files' entries are identical, and the file order is kept. Nothing was removed from a scanned file (the oracle went from 1009 to 1011; `test_animals_proposal.py` stays at 3), and no entry is `is_verified`. The baseline was staged by name, and the staged blob equals the file on disk (`127eba6c…`, LF only).
- **cp1252 gap (for the Owner).** detect-secrets reads files with the locale codec. The new oracle contains `”` (UTF-8 `E2 80 9D`; `0x9D` is undefined in cp1252), so on this Windows machine both the scan and the hook skip the oracle silently. They report nothing, and a hook run passes vacuously. The first scan (`scan.json`, oracle 0 scanned against 1009 baselined) was discarded as invalid. The applied scan (`scan-utf8.json`) and the final hooks ran with `PYTHONUTF8=1`, which changes only the interpreter's I/O mode, not the plugins, filters or settings. No config was changed. `hook.log` records one default-mode run beside the two UTF-8 runs.
- **Final hooks (`hook.log`).** `detect-secrets-hook --baseline .secrets.baseline` ran over the 9 files plus the baseline:
  - UTF-8 mode, twice (starting 14:32:35Z and 14:34:19Z): EXIT 0 both times, baseline stable at `127eba6c…`;
  - default mode (14:36:01Z): EXIT 0, vacuous for the oracle, as described above.
  
  This doc changed during those runs, so its text was hooked again, twice in UTF-8 mode. The `doc-final-utf8` pairs in `hook.log` each record the doc sha they checked; earlier pairs cover intermediate text, and the last pair covers the final text.

## Final manifest recheck

The final recheck (`recheck-final.txt`, 14:35:10Z) compared every file against the pre-write pins:

- **Unchanged.** Both Owner files, the generator, the PROPOSAL, the DELTA and review.md match.
- **Changed as expected.**
  - the oracle, now `15478aa5…`;
  - `.secrets.baseline`, now `127eba6c…`;
  - the ACCEPT script, now `4e1d032f…`, after the two post-write pin edits and the multiset fix.
- **Repository state.** There are still 4 stashes and 36 staged deletions. The only other staged change is `.secrets.baseline`.

## Blockers and retention

- **Partial publication.** The block stands: 64 reference findings remain; uncovered leaves are now 0.
- **Release order.** Unchanged; the Owner's order decision holds.
- **Nothing released or committed.** Nothing was published or activated, and nothing was written to a shared DB. No commits, pushes or merges.
- **Untouched:** the framing-coverage generator, PROPOSAL, DELTA and review.md; earlier recorded ACCEPT scripts and packets; the 36 staged deletions and 4 stashes; the quarantine corpus; `issue-5d-source-correction-REPLACEMENT-PACKET.md`; the root `afterworlds.db`; the `574662e9` oracle; the pre-existing modification of `issue-5d-core-play-completion-generator.py` and other unrelated modifications.
- **Source-error policy.** No source error was found; none was corrected.
- **Process disclosure.** Several Bash calls in this session used a leading `cd` into the repository or a scratch directory, contrary to standing instructions. They only read files, ran the inline edit scripts described above, or computed hashes. Several PowerShell gate and baseline calls likewise used `Set-Location` into the repository root.
