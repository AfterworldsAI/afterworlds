# CRD Issue 5d — Equipment, cursed-item and spell references: recorded follow-up (#132, #137)

## Authorization

The Owner's statement, verbatim:

> I accept this exact thirteen-reference candidate and reader correction.

**Approval time.** Codex verified the statement before 2026-10-03T09:20:14Z ([acceptance note](issue-5d-equipment-spell-references-owner-acceptance.md)). No more precise approval time is claimed. `APPROVAL_BEFORE` in the script is documentary and is never recorded. The recorded action carries its real execution time in UTC.

**Pinned files.** The ACCEPT script asserts the constructor pin at import, and the PROPOSAL, DELTA, packet, independent review and acceptance-note pins on every run. The reader correction and its tests are asserted before the write only (`_precheck`), because deferred work may later change either without touching the oracle.

| File | SHA-256 |
|---|---|
| `issue-5d-equipment-spell-references-CANDIDATE.py` (constructor) | `623f0509812dc64872d09f8fa98d09b07b9b5a6f28b197cdb451933817bd6b7e` |
| `issue-5d-equipment-spell-references-PROPOSAL.json` | `b9bf5638902b2384da3875963f4846d794339e3656efd2c8321c4c6094d8056d` |
| `issue-5d-equipment-spell-references-DELTA.txt` | `0e00a0d6cd7576ba43651f0b06d69062ed9e3ab7e40783b6bfc4ea48e2a8c601` |
| `issue-5d-equipment-spell-references-review.md` (implementation packet) | `29caa23daee5eb78404d637ba8149bd4ebd2f4895f286a46646475b6bcfd646d` |
| `issue-5d-equipment-spell-references-owner-review.md` (independent review) | `bd829a6c937efd994362da5946f754b99cba5bf92a5b325780ed663d0aa27d39` |
| `issue-5d-equipment-spell-references-owner-acceptance.md` | `de2a917bec119217fd2026214a732a8b76935b44e930d83bcb4820be34ca3e61` |
| `src/afterworlds/services/rules_authority/service.py` (reader correction, pre-write) | `4a33bf3c5f07120623c943b06f22e327f53d47dafba820677d5780b008877e2d` |
| `tests/ingestion/mechanical/test_equipment_spell_references_candidate.py` (reader tests, pre-write) | `00111b870eb8f0c3e9fcc45da20ff2695fa6ac283c4b7a69abc876063fc7f8b5` |

The reader-test file was then edited after the write (fixtures only; see below). Its accepted bytes `00111b87…` are historical: they were in place at the write.

## Final oracle

`src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json`

| State | SHA-256 | Schema | Batches / records / spans / units / resolutions | Reference / uncovered-leaf / other findings |
|---|---|---|---|---|
| prior (finite-reference-routes recording) | `e9678ab30c27ba92deda5757de4be082aba8bfc44690b6bf94f7bc1f747a45ca` | 17 | 24 / 1835 / 10493 / 1476 / 1463 | 23 / 0 / 0 |
| **recorded (final, on disk)** | **`5909e5bdd8c73bf32525b17942924364871146d648b83681518561361a434c0d`** | **17** (unchanged, no lift) | **24 / 1835 / 10493 / 1476 / 1476** | **10 / 0 / 0** |

There are 0 reference-resolution violations, and the partial-publication block stands.

**Simulated state.** `faa46e9c5f4668bad2ed5ad764fccd9f1f8fb2f9471f5986186523961e418290` is the reviewed constructor's composition under the simulated reviewer. It was reproduced by `--simulate`, and again on the record path before the write. It was never written.

## Recorded action (real UTC)

**Script.** `.claude/review-notes/issue-5d-equipment-spell-references-ACCEPT.py`. Its final sha is `a6763ef89326ff85d6f782689e36f00573d32be9f0acf36ae5c4b60e239cfd28`, taken after `RECORDED_AT` and `RECORDED_SHA256["recorded"]` were pinned from the values the run printed and read back. Black, Ruff and `mypy --strict` (`MYPYPATH=src`) are 0 before and after pinning.

**Logs.** All are in `.claude/_sp/esr/recording/`. Each run went through `../run.py`, which writes `NAME.log` (stdout and stderr, UTF-8) and `NAME.exit`. No earlier log was overwritten.

| Action | Log | Result |
|---|---|---|
| `--simulate` (09:27:55Z–09:29:06Z; nothing written) | `accept-simulate.log` | EXIT 0. Simulated bytes `faa46e9c…`. Every post-write check passes on the Owner's evidence at the placeholder time. The Owner composition differs from the simulated one in 52 leaves. |
| pre-write checks | — | No python process; the live oracle was `e9678ab3…`; no record log existed. |
| `record-equipment-spell-references` (09:29:21Z–09:31:27Z) | `accept-record.log` | **EXIT 0.** One native write at **2026-10-03T09:30:23Z**, sha **`5909e5bd…`**. The post-write `_state` recomposition from the recorded time matched, every check was True, and the file reloaded to the same bytes. |
| `--verify .claude/_sp/esr/recording/prior-oracle.json` on the pinned script (09:31:50Z–09:32:46Z) | `accept-verify.log` | EXIT 0, every line True. |

**Recording shape.** The script made one `resolve_references` call over the prior with the thirteen resolutions the constructor's `drafts` builds. Each has `reviewer` and `authorized_by` set to `Ravenlok (Owner)`, `authorization_reference` set to the decision (acceptance note, packets, constructor, PROPOSAL, DELTA, simulated sha, reader correction, prior sha and the verbatim statement), and `resolved_at` set to the clock, read once. No batch was replaced, re-accepted, re-keyed or reordered.

**Actual vs simulated** (`accept-record.log`). The leaf walk compares the two payloads with object lists aligned by their non-evidence content. Only the thirteen new approval records differ, in exactly four evidence fields:

| Collection | Field | Count | Simulated | Recorded |
|---|---|---|---|---|
| `acceptance.reference_resolution_records` | `reviewer` | 13 | `SIMULATION - not an Owner approval` | `Ravenlok (Owner)` |
| | `authorized_by` | 13 | `SIMULATION - not an Owner approval` | `Ravenlok (Owner)` |
| | `authorization_reference` | 13 | `SIMULATION ONLY: in-memory composition check; records no acceptance` | this decision |
| | `resolved_at` | 13 | `2026-10-03T00:00:00Z` | `2026-10-03T09:30:23Z` |

Nothing else differs. The script asserts the total is 13 × 4.

## Preservation and replay evidence

This evidence is from `accept-record.log` and `accept-verify.log`.

- **Counts.** 24 / 1835 / 10493 / 1476 / 1476. Schema 17 is unchanged, with no lift.
- **Findings.** 23 / 0 / 0 → 10 / 0 / 0, compared as multisets. Exactly 13 were cleared, and none are new. The ten that remain are the deferred rows.
- **Additive only.** In every payload collection nothing was lost. The only additions are 13 `reference_resolutions` and 13 `acceptance.reference_resolution_records`.
- **Batches.** All 24 batches, their identities, approvals and evidence are verbatim, and so are the batch and review-unit acceptances. Binding, schema, representation, lifts and policy history are equal.
- **Resolutions.** The 1463 prior resolutions are verbatim, in canonical order. Their 1463 historical approvals are verbatim, in order. The 13 new resolutions are exactly the reviewed PROPOSAL's: 13 resolutions, 15 routes, 62 destinations.
- **Delta.** The delta is the reviewed DELTA with the 13 new resolutions' authorizer and reference set to the Owner's.
- **Reload.** The file reloads to the same bytes.

## Historical scripts now refuse

| Script | Log | Result |
|---|---|---|
| equipment-spell-references constructor, check mode | `refusal-constructor-check.log` | EXIT 1, `AssertionError: accepted changed`. Expected: its input pin is the prior file. |
| finite-reference-routes `--verify` (its own replayed prior; 09:32:48Z–09:36:05Z) | `refusal-frr-verify-replay.log` | EXIT 1, `AssertionError: drifted`. Expected. |
| finite-reference-routes `--verify .claude/_sp/esr/recording/prior-oracle.json` | `refusal-frr-verify.log` | EXIT 1 at `saved_prior`: **my misinvocation, not a refusal result.** That file is this recording's prior, not FRR's. Preserved, and superseded by the replay run above. |

## Moved pins (historical checks kept)

| File | Change |
|---|---|
| `tests/ingestion/mechanical/_replacement_chain.py` | Loads `EQUIPMENT_SPELL_REFERENCES` (module `equipment_spell_references_accept`). `COMMITTED_SHA256` now points to its recorded sha. Adds `finite_reference_routes_recorded()`, the replayed prior. Docstring updated. |
| `test_animals_proposal.py` | The live finite-reference-routes test becomes the historical `test_the_finite_reference_routes_recording_rebuilds`: replay = `e9678ab3…`, plus FRR `_read_back`, `_approvals`, `_check`, and 23 / 0. New: `test_the_committed_oracle_records_equipment_spell_references`. It checks the sha, reproduces the committed inputs, and checks `_read_back == RECORDED_AT`. It also reproduces the bytes from `recorded(prior, OWNER, RECORDED_AT)`, checks `_approvals` is empty, runs `_check` over the replayed prior, and checks 10 / 0. |
| `test_equipment_spell_references_candidate.py` | Fixtures only. `accepted` (the control's source) is the replayed prior. `candidate` loads the recorded oracle instead of composing the simulation, which would now fail on already-resolved citations. Docstring updated. No test body changed. |
| `test_source_release_readiness.py` | 1463 → 1476 resolutions. Docstring updated. |
| `src/.../oracles/README.md` | Current state updated (`5909e5bd…`, 1476, 10). The finite-reference-routes history entry is completed, and an equipment-spell-references entry is added. Finite-reference-routes `--verify` and this constructor's check mode are added to the scripts that refuse. |

**No batch changed**, so `test_committed_accepted_authority.py` needs no edit. Its live test ran and passed (below). **ADR-005d is not edited**: this recording accepts no amendment and no schema change. The reader correction conforms to the accepted Decision 7.

## Checks (raw)

Recording invalidates three things: the live-file identity (sha and counts), the ESR test fixtures that composed the simulation over the live file, and the persisted reader over the recorded bytes. Only those were rerun. Both runs used `scripts/run_focused_tests.py`, which checks Black on the five changed Python files first. Both were launched detached at 09:36:36Z, after the last test and script write (09:32:42Z). The README (09:36:48Z) is read by no test.

| Run | Ids | Result |
|---|---|---|
| `pytest-reader.log` (`reader.ids`) | ESR persisted reader: control refuses ×13, every route reads as drafted ×13, the Equipment chapter ×3, the 8 source-gone retention cases, the 2 unrelated-override cases | **39 passed in 985.92s**, EXIT 0 |
| `pytest-live.log` (`live.ids`) | Live identity: the two Animals tests above, the 8 `committed_oracle…`/recorded-bytes tests (classes, gameplay toolbox, magic items ×2, monsters, rules glossary, spell descriptions, character-origins-feats), `test_no_refused_candidate_is_selectable`, the two readiness tests, checks-actions-rests native seam, reference-resolution untouched corpus, and Equipment and Spellcasting `…preserves_both_steps…` | **17 passed in 1186.27s**, EXIT 0 |

Both are FOCUSED DIAGNOSTICS ONLY, not acceptance or full-gate evidence.

**Reused, not rerun.** The rest of the ESR file (cursed items, spellcasting, spell characteristics, destination disable, deferred gear) passed in `focused2` over the same thirteen resolutions; the recorded bytes differ from that composition only in approval evidence, which the reader does not read. The finite-reference-routes and reference-alternatives candidate files are also reused: additive resolutions do not change their routes or retention. Their source-gone, edit-keeps and destination-disable cases passed in `focused4`.

**Format, lint, type** (`gates/`). Black 0 and Ruff 0 on the four changed test files. `mypy --strict` over them: EXIT 1, 11 errors in 3 files, none in changed lines: `conftest.py:763/764/1010`, `test_character_origins_feats_proposal.py:890/1762/1766`, and `test_animals_proposal.py:423–435`. The last is the pre-existing 421–433 block, shifted by the two added import lines. This is the standing non-green expanded mypy. `mypy src/` was not rerun, because no `src/` Python changed.

**LF only.** All new or edited files have 0 CR.

**detect-secrets.** A scoped scan under the baseline's own plugins and filters, run with `PYTHONUTF8=1`, over the eight files in `.claude/_sp/esr/recording/bl/files.txt`: the ACCEPT script, this note, the oracle, the README and the four test files. Logs: `blscan.log`, `blapply.log`, `scope.log`, `blscan2.log`. The oracle's 1014 findings were scanned, so it was not skipped.

- **10 new public hashes, every value recovered and named.** All are the ACCEPT script's pins: constructor, PROPOSAL, DELTA, packet, independent review, acceptance note, reader, reader tests, simulated and recorded. Nothing in the oracle is new, because no batch changed.
- **0 obsolete, 0 pruned.** 966 line numbers were refreshed, in the oracle and in `test_animals_proposal.py`.
- **Scope.** Only the `results` entries of scanned files changed. Settings and `generated_at` are identical.
- **Baseline.** `5796c5acea85b60e5be2d84ddaa00d2e850db9d50535d1ba32c41fa69144b44d` → `ae2268b60aa6ed124fb22c0753f6b91f0f3537e8a754baa0cad4aa82326d2c61`, in the working tree only. It is **not staged**: the index blob is still `4884b897`. The rescan found 0 new and 0 obsolete. No `pragma: allowlist secret` was added, and `scan --baseline` was not run.
- **Final hooks.** In `.claude/_sp/esr/recording/final-hook.log`. The real hook uses the working-tree baseline. That is not what a commit would see, because the baseline is unstaged. The private-copy hook checks content coverage only.

**Not run.** The broad suite. No green is claimed. Deferred and not green: pip-audit, expanded mypy and coverage.

## Limits

- Nothing is staged, committed, pushed, merged, published or activated. No shared DB was written.
- The release order is scheduled for one bounded Owner pass before publication.
- 10 reference findings remain (the ten deferred citations), and the partial-publication block stands.
- The pre-existing out-of-scope reader-retention residue in the implementation packet stays deferred.
- The restart summary in `docs/architecture/issue-5c-5d-clean-restart.md` is Codex's and was not edited.
