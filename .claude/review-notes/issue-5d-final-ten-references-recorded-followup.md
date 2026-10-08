# CRD Issue 5d — Final ten references: recorded follow-up (#132, #137)

## Authorization

The Owner's statement, verbatim:

> I accept this exact candidate.

**Approval time.** Codex verified the statement before 2026-10-07T01:13:39Z ([acceptance note](issue-5d-final-ten-references-owner-acceptance.md)). No more precise approval time is claimed. `APPROVAL_BEFORE` in the script is documentary and is never recorded; the record path asserts the write time is later than it. The recorded action carries its real execution time in UTC.

**Pinned files.** The ACCEPT script asserts the constructor pin at import, and the PROPOSAL, DELTA, Owner packet, Codex review, acceptance note and reviewed-test history copy on every run. The live reader (`service.py`) and the live reader test are asserted before the write only (`_precheck`), because deferred work may later change either without touching the oracle.

| File | SHA-256 |
|---|---|
| `issue-5d-final-ten-references/candidate/CANDIDATE.py` (constructor) | `2f84d877037b865121bd502a9c92ae365f44cf82dc6d312d814759200433fd57` |
| `issue-5d-final-ten-references/candidate/issue-5d-final-ten-references-PROPOSAL.json` | `46808846b0ad6712393b0f058a71e03d6e664a2ffdf8734de7d046bf4b4d68e3` |
| `issue-5d-final-ten-references/candidate/issue-5d-final-ten-references-DELTA.txt` | `465a17f7d749c512aed45848874576a6c2a839e1eaf0ea595da6a6c11c827851` |
| `issue-5d-final-ten-references/candidate/reviewed-test_final_ten_references_candidate.py.txt` (reviewed test, history copy) | `fec853b8ed1d84146248aa19d5f92b1c60b14aea226cf281a31dba6a07ba3dbe` |
| `issue-5d-final-ten-references-candidate.md` (Owner packet) | `24a42c7321111b186dc090327ab0e43afc422720ed80cf83cc1d4d7c92d012b0` |
| `issue-5d-final-ten-references-codex-review.md` (Codex review) | `d5e1a9b2ea62a3d65c3a7acf0b3cab067acc0c617bb8754b1ca94ea5e25c80ab` |
| `issue-5d-final-ten-references-owner-acceptance.md` | `5166bb4092937c7679ca07ef74d8f3f44ff0dd8741af17391a2f9cf6efd6dc5e` |
| `src/afterworlds/services/rules_authority/service.py` (reader, pre-write) | `4a33bf3c5f07120623c943b06f22e327f53d47dafba820677d5780b008877e2d` |
| `tests/ingestion/mechanical/test_final_ten_references_candidate.py` (live reader test, pre-write) | `fec853b8ed1d84146248aa19d5f92b1c60b14aea226cf281a31dba6a07ba3dbe` |

**Relocated history.** The reviewed constructor, PROPOSAL, DELTA and test were under the uncommittable `.claude/_sp/final-ten/candidate/`. They were copied byte for byte into `.claude/review-notes/issue-5d-final-ten-references/candidate/` so that the ACCEPT script and the replay chain depend only on committable files. The originals are untouched. The relocated constructor's check mode passed before the write (`relocated-check.log`, EXIT 0, DELTA `465a17f7…`, 247 lines). After the write, the live test file was edited (fixtures only; see below). Its accepted bytes `fec853b8…` are kept as the history copy.

## Final oracle

`src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json`

| State | SHA-256 | Schema | Batches / records / spans / units / resolutions | Reference / uncovered-leaf / other findings |
|---|---|---|---|---|
| prior (equipment-spell-references recording) | `5909e5bdd8c73bf32525b17942924364871146d648b83681518561361a434c0d` | 17 | 24 / 1835 / 10493 / 1476 / 1476 | 10 / 0 / 0 |
| **recorded (final, on disk)** | **`e6f5f36aa3af13807bbff721797d971dcf0d8e588a97483c7d769cf88cbd1308`** | **17** (unchanged, no lift) | **24 / 1835 / 10493 / 1476 / 1486** | **0 / 0 / 0** |

There are 0 reference-resolution violations. Resolution approvals: 1486.

**Simulated state.** `6302adbe7b09fab0a26d60e5526d72fa5269214e3911b0362486ad9e705d85ff` is the reviewed constructor's composition under the simulated reviewer. It was reproduced by `--simulate`, and again on the record path before the write. It was never written.

## Recorded action (real UTC)

**Script.** `.claude/review-notes/issue-5d-final-ten-references-ACCEPT.py`. The executed bytes were `98216aa1890d9f1f61d016f02eab657ff08275b41b6d8e3b0e63f1f8eeee1c6a` (saved as `run/executed-ACCEPT.py.txt`). The final sha is `d3142fdf6d0d8d9cf9af893a531317bee78f09c2e43abb150708fae22eaec22e`, taken after `RECORDED_AT` and `RECORDED_SHA256["recorded"]` were pinned from the values the run printed and read back. Black, Ruff and `mypy --strict` (`MYPYPATH=src`) are 0 before and after pinning.

**Logs.** All are in `.claude/_sp/final-ten/recording/run/`. Each run went through `run.py`, which writes `NAME.log` (stdout and stderr, UTF-8, with input sha256 lines) and `NAME.exit`, and refuses to overwrite. No earlier log was overwritten.

| Action | Log | Result |
|---|---|---|
| gates on the unpinned script | `accept-gates-prewrite.log`, `accept-gates-prewrite-2.log` | EXIT 0 (Black, Ruff, mypy strict) |
| `--simulate` (nothing written) | `simulate.log`, then `simulate-2.log` after hardening | EXIT 0. Simulated bytes `6302adbe…`. Every post-write check passes on the Owner's evidence at the placeholder time: 1486 approvals, reload to the same bytes, persisted round trip on a scratch release copy. 40 differing leaves. |
| pre-write inputs | `record-inputs.sha256` | live oracle `5909e5bd…`, script `98216aa1…` |
| `record-final-ten-references` (01:28:44Z–01:31:23Z) | `record.log` | **EXIT 0.** One native write at **2026-10-07T01:30:07Z**, sha **`e6f5f36a…`**. The post-write recomposition from the recorded time matched, every check was True, and the file reloaded to the same bytes. |
| gates on the pinned script | `accept-gates-pinned.log` | EXIT 0 |
| `--verify .claude/_sp/final-ten/recording/pre-edit/accepted-oracle.json` (saved prior) | `verify-saved-prior.log` | EXIT 0, every line True |
| `--verify` (replayed prior through the chain) | `verify-replay.log` | EXIT 0, every line True. It prints the pre-existing "re-keyed recorded resolutions dropped" notice from the replay of earlier steps. |

**Recording shape.** The script made one `resolve_references` call over the prior with the ten resolutions the constructor's `drafts` builds. Each has `reviewer` and `authorized_by` set to `Ravenlok (Owner)`, `authorization_reference` set to this decision (acceptance note, packet, Codex review, constructor, PROPOSAL, DELTA, simulated sha, prior sha and the verbatim statement), and `resolved_at` set to the clock, read once. No batch was replaced, re-accepted, re-keyed or reordered.

**Actual vs simulated** (`record.log`). Only the ten new approval records differ, in exactly four evidence fields:

| Collection | Field | Count | Simulated | Recorded |
|---|---|---|---|---|
| `acceptance.reference_resolution_records` | `reviewer` | 10 | `SIMULATION - not an Owner approval` | `Ravenlok (Owner)` |
| | `authorized_by` | 10 | `SIMULATION - not an Owner approval` | `Ravenlok (Owner)` |
| | `authorization_reference` | 10 | `SIMULATION ONLY: in-memory composition check; …` | this decision |
| | `resolved_at` | 10 | `2026-10-06T00:00:00Z` | `2026-10-07T01:30:07Z` |

Nothing else differs. The script asserts the total is 10 × 4.

## Preservation and replay evidence

This evidence is from `record.log` and both `--verify` logs.

- **Counts.** 24 / 1835 / 10493 / 1476 / 1486. Schema 17 and the release binding are unchanged, with no lift.
- **Findings.** 10 / 0 / 0 → 0 / 0 / 0. Exactly 10 were cleared, and none are new.
- **Additive only.** Nothing was lost in any payload collection. The only additions are 10 `reference_resolutions` and 10 `acceptance.reference_resolution_records`.
- **Batches.** All 24 batches, their identities, approvals and evidence are verbatim. Lifts and policy history are unchanged.
- **Resolutions.** The 1476 prior resolutions are verbatim, in canonical order, and so are their 1476 approvals. The 10 new resolutions are exactly the reviewed PROPOSAL's (10 resolutions, 144 routes, 201 destinations), and the PROPOSAL rebuilds byte for byte.
- **Delta.** The delta is the reviewed DELTA without its simulation header, with the ten new resolutions' authorizer and reference set to the Owner's.
- **Reload.** The file reloads to the same bytes, and the persisted round trip on a scratch release copy holds.

## Historical scripts now refuse (by pin; not rerun)

Equipment-spell-references `--verify` asserts the live file is its recorded `5909e5bd…` (`_state`, "drifted"). The final-ten constructor's check mode asserts the live file is `ACCEPTED_SHA256` = `5909e5bd…`. Both now refuse by construction. They were confirmed from code and not rerun, to keep the run set small.

## Moved pins (historical checks kept)

| File | Change |
|---|---|
| `tests/ingestion/mechanical/_replacement_chain.py` | Loads `FINAL_TEN_REFERENCES` (module `final_ten_references_accept`). `COMMITTED_SHA256` now points to its recorded sha. Adds `equipment_spell_references_recorded()`, the replayed prior. Docstring updated. |
| `test_animals_proposal.py` | The live equipment-spell-references test becomes the historical `test_the_equipment_spell_references_recording_rebuilds`: replay = `5909e5bd…`, plus ESR `_read_back`, `_approvals`, `_check`, and 10 / 0. New: `test_the_committed_oracle_records_final_ten_references`. It checks the sha, reproduces the committed inputs, checks `_read_back == RECORDED_AT`, reproduces the bytes from `recorded(prior, OWNER, RECORDED_AT)`, checks no wrong approvals, runs `_check`, and checks 0 / 0. |
| `test_final_ten_references_candidate.py` | Fixtures and docstrings only. `HARNESS` loads the relocated constructor. `accepted` (the control's source) is the replayed prior. `candidate` loads the recorded oracle. No test body changed. |
| `test_equipment_spell_references_candidate.py` | Fixtures only. `candidate` is the replayed ESR recording instead of the live file, because the live file now resolves the deferred gear citation that `test_the_deferred_gear_citation_stays_unresolved` checks against the ESR state. Unused import removed; docstring updated. No test body changed. |
| `test_source_release_readiness.py` | 1476 → 1486 resolutions. Docstring updated. |
| `src/.../oracles/README.md` | Current state updated (`e6f5f36a…`, 1486, no findings). The ESR result is completed and a final-ten history entry is added. ESR `--verify` and the final-ten constructor check mode are added to the scripts that refuse. |

**No batch changed**, so `test_committed_accepted_authority.py` needs no edit. **ADR-005d is not edited**: this recording accepts no amendment and no schema change.

## Checks (raw)

The recording changes three things: the live-file identity (sha and counts), the candidate-test fixtures that read the live file, and the persisted reader over the recorded bytes. Only those were rerun, in one `scripts/run_focused_tests.py` run. It first checks Black on the ACCEPT script and the five changed test files. Its input hashes are logged and match the final files. No test or script was edited during the run.

| Run | Ids (`focused.ids`, 23) | Result |
|---|---|---|
| `focused-2.log` (01:40:23Z–02:11:05Z) | Live identity: the two Animals tests above plus the historical `test_the_finite_reference_routes_recording_rebuilds`; the 8 `committed_oracle…`/recorded-bytes tests (classes, gameplay toolbox, magic items ×2, monsters, rules glossary, spell descriptions, character-origins-feats); `test_no_refused_candidate_is_selectable`; the two readiness tests; the checks-actions-rests native seam; the reference-resolution untouched corpus; and Equipment and Spellcasting `…preserves_both_steps…`. Final-ten reader over the recorded bytes: the control refuses every drafted citation, every route reads as drafted, and disabled vs unrelated destination. ESR reader over its replayed recording: the deferred gear citation stays unresolved, and every route reads as drafted. | **53 passed in 1837.64s**, EXIT 0 |

It is FOCUSED DIAGNOSTICS ONLY, not acceptance or full-gate evidence. `focused.log` is a false start, kept: an unsupported `-p` flag gave EXIT 2 before any test ran.

**Reused, not rerun.** The rest of the final-ten reader file passed in the reviewed candidate's `reader-focused.log` (33 passed) over the same ten resolutions. The recorded bytes differ from that composition only in approval evidence, which the reader does not read.

**Format, lint, type** (`consumer-gates.log`). Black 0 and Ruff 0 on the five changed test files. `mypy --strict` over them: EXIT 1, 11 errors in 3 files, none in changed lines: `conftest.py:763/764/1010`, `test_character_origins_feats_proposal.py:890/1762/1766`, and `test_animals_proposal.py:425–437`. The last is the pre-existing 423–435 block from the ESR follow-up, shifted by two added import lines (`consumer-mypy-preexisting.txt`). This is the standing non-green expanded mypy. `mypy src/` was not rerun, because no `src/` Python changed.

**LF only and preservation.** All new or edited files have 0 CR. Index, stashes, tracked diff, the pre-edit file snapshot, external settings and the focused-run input pins are checked in `run/preservation.log`.

**detect-secrets.** A scoped scan under the baseline's own plugins and filters, run with `PYTHONUTF8=1`, over the thirteen files in `.claude/_sp/final-ten/recording/bl/files.txt`: the oracle, the README, the ACCEPT script, the four relocated candidate files, the acceptance note and the five test files. Logs: `blscan.log`, `bl-identify.log`, `bl-apply.log`, `bl-apply-2.log`, `bl-scope.log`, `bl-scope-2.log`. The oracle's 1014 findings were scanned (1014 in the baseline, 0 new, 0 obsolete), so it was not skipped.

- **22 new public hashes, every value recovered and named.** ACCEPT: 10 (constructor, PROPOSAL, DELTA, packet, Codex review, acceptance note, reviewed test, reader, simulated, recorded). CANDIDATE.py: 2 (`ACCEPTED_SHA256` = the prior oracle, and `FAMILIAR_INVENTORY_SHA256` = the sha of `issue-5d-srd-familiar-cr0-inventory-2026-10-06.json`). PROPOSAL: 6 and DELTA: 4, all values already present in the prior oracle.
- **Additive only.** 22 entries under 4 new file keys. 0 removed, 0 pruned, 0 obsolete. Settings and `generated_at` are identical. `bl-apply.log` is EXIT 1: it failed closed on a sort assertion before writing anything. `bl-apply-2.log` applied the same delta, appending.
- **Rescan.** The thirteen files plus this note (`bl/files2.txt`, `blscan-2.log`): 0 new and 0 obsolete in every file. The note itself has no findings.
- **Line numbers.** The additive apply did not refresh line numbers. The first final hook (`final-hook.log`) shows this: real hook EXIT 1 (baseline unstaged), private copy **EXIT 3**. The private hook rewrote line numbers only, with the same hash sets in every key. 966 of those rewrites were stale baseline line numbers in the two in-scope keys this work moved, because the additive apply does not renumber: the oracle (963) and `test_animals_proposal.py` (3). Once the hook was updating anyway, it also renumbered four out-of-scope keys whose entries match the pre-edit baseline: `issue-5d-finite-reference-atoms-DELTA.txt`, `issue-5d-finite-reference-routes-PROPOSAL.json`, `issue-5d-remaining-references-DELTA.txt` and `tests/ingestion/mechanical/data/bounded_oracle.json`. `bl/relines.py` (`bl-relines.log`) refreshed line numbers only, for the two in-scope keys, from `scan2.json`. It requires the same (hash, type) multiset and adds, removes and reorders nothing. A trial on a scratch copy got hook EXIT 0, with the copy unchanged. The four out-of-scope keys were left as they were.
- **Baseline.** `ae2268b60aa6ed124fb22c0753f6b91f0f3537e8a754baa0cad4aa82326d2c61` → `112fc518bc3f5de9e2821359e01f878b0b22fa3ecc24de021d03d5affcd42784` (22 added, 6861 entries) → `901663b0f2663c6d42620005470fe3183a1eb55e4f3d45791ebe25927427cba5` (966 line numbers refreshed). This is in the working tree only. It is **not staged**: the index blob is still `4884b897`. No configuration changed, no `pragma: allowlist secret` was added, and `scan --baseline` was not run.
- **Final hooks.** In `.claude/_sp/final-ten/recording/final-hook-2.log`. The real hook uses the working-tree baseline. That is not what a commit would see, because the baseline is unstaged. The private-copy hook checks content coverage only.

**Not run.** The broad suite. No green is claimed. Deferred and not green: pip-audit, expanded mypy and coverage.

## Limits

- Nothing is staged, committed, pushed, merged, published or activated. No shared DB was written.
- The partial-publication block and its lifting are outside this recording. The release order stays scheduled for one bounded Owner pass before publication.
- The pre-existing out-of-scope reader-retention residue stays deferred.
- Awakened Plant stays uninstalled and outside the SRD oracle.
- The restart summary in `docs/architecture/issue-5c-5d-clean-restart.md` is Codex's and was not edited.
