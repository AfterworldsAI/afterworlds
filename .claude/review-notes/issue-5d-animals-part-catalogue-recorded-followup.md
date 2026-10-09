# CRD Issue 5d — Animals part-catalogue replacement: recorded follow-up (#132, #137)

## Authorization

The Owner's statement, verbatim:

> I accept the exact Animals catalogue replacement proposal and its four reference resolutions, retaining 64 reference findings, 28 uncovered leaves, and the partial-publication block.

**Approval time:** the parent received this statement before its observation at 2026-09-29T10:22:16Z. No more precise message timestamp is claimed. Every recorded action below carries its real execution UTC time.

**Owner files.** The following were checked against the manifest before dispatch, again immediately before the first write, and once more after all writes (see "Final manifest recheck"):

| File | SHA-256 |
|---|---|
| `animals-part-catalogue-owner-review.md` | `01aeb9796dd71b7e721169c68dbacc5f26b38416c0a16f9a92837e977485a053` |
| `animals-part-catalogue-owner-manifest.json` | `f779c986f3a351bbabec70fe2bf9a5a44c2261b076b349868b7dc15b4670d223` |

Before the first write, all 7 manifest entries matched: REPLACEMENT.py, PROPOSAL, DRAFTS, DELTA, review.md, the oracle `e0fd7690…` and `.secrets.baseline` `eeea9c0f…`.

## Final oracle

`src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json`

| State | SHA-256 | Batches / records / spans / review units / resolutions | Reference / uncovered-leaf findings |
|---|---|---|---|
| prior (remaining-references recording) | `e0fd7690f519ec34dabcbba320936c20faff402fd94b925a2d4453316a29b14c` | 22 / 1832 / 10484 / 1459 / 1434 | 68 / 29 |
| animals-recorded | `8af13cb727ec941dc5c36229fd6d731d43fbb66fa0661e2b4c6336065237b4f4` | 22 / 1833 / 10485 / 1460 / 1434 | 68 / 28 |
| **resolved (final, on disk)** | **`96e90f71ddde22da6424eef9875b51eb36620876dfee635546e1d6872594a91b`** | **22 / 1833 / 10485 / 1460 / 1438** | **64 / 28** |

- **Simulated state.** The reviewed simulated composition, `e702cbc427716695bf54dc7ef2b0dc6d76f8e03d57104b166aed06e0fd6080f4`, is pinned only as the reviewed candidate. It was never written, and the recorded bytes differ from it.
- **Violations.** Other findings: 0. Reference-resolution violations: 0.
- **Partial publication.** The partial-publication block stands.

## Recorded actions (real UTC)

The script is `.claude/review-notes/issue-5d-animals-part-catalogue-ACCEPT.py`, sha `70fc38f1…` after pinning. Logs are in `.claude/_sp/apc/`.

| Action | Ran | Recorded time | Result |
|---|---|---|---|
| `--simulate`, run 1 | 10:29:09–10:30:47Z | — | EXIT 1: script defect, "not a partition". `composed` used the e0fd7690 file as the evidence base instead of `REMAINING.prior()`. Nothing written. |
| `--simulate`, run 2 | 10:31:12–10:33:09Z | — | EXIT 1: script defect. `drafts()` compared the rows in review order, but the payload is in canonical order; it now compares them sorted. Nothing written. |
| `--simulate`, run 3 (`simulate.txt`) | 10:34:55–10:37:39Z | — | EXIT 0. Nothing written. |
| manifest recheck | before 10:38:55Z | — | 7/7 match |
| `record-animals` (`record.txt`) | 10:38:55–10:42:33Z | `accepted_at` 2026-09-29T10:41:28Z | EXIT 0; `8af13cb7…`; post-write `_state()` and `verify` pass |
| `resolve-animals` (`resolve.txt`) | 10:42:38–10:45:21Z | `resolved_at` 2026-09-29T10:44:29Z | EXIT 0; `96e90f71…`; post-write `_state()` and `verify` pass |
| `--verify` against the pins (`verify.txt`) | 10:45:49–10:48:25Z | — | EXIT 0 |
| independent `recorded()` replay (`replay.txt`) | 10:45:49–10:47:33Z | — | EXIT 0; equals the disk bytes (`96e90f71…`) |

`RECORDED_AT` and `RECORDED_SHA256` were pinned after the writes, from the times read back out of the file. Nothing was re-recorded.

**Recording shape.** The recording follows the remaining-references pattern.
- The chain is rebuilt natively over `REMAINING.prior()`, which is the Equipment state: the 22 batches in unchanged order, with 21 batches reusing their recorded proposals, rules, reviewers and times.
- Only the Animals batch takes the exact proposal `228726d29769fcdb88e874c79b1a0685c8e1b18c59ce538011d8978d57645e38` (file `7f067f74…`, constructor `3fd3da99…`). Its rule is the verbatim Owner statement, its reviewer is the Owner, and its time is the real `accepted_at`.
- The 29 remaining-references resolutions are re-applied at their recorded time through `REMAINING.resolved`, so the 1434 prior resolutions carry their original evidence.
- The four drafts (`371dadb9…`) are parsed by the strict loader parser and checked against the constructor rows as a set. One `resolve_references` action then records them, with:
  - the Owner as authorizer and reviewer;
  - the real `resolved_at`;
  - an `authorization_reference` naming the Owner review, the manifest, the constructor sha, the proposal sha and identity, the drafts sha and the prior sha.
- **Before the first write (`record-animals`), `_precheck` ran (it did not run again before the resolve write):**
  - The simulated composition must reproduce `e702cbc4…`.
  - The same composition under the Owner at a placeholder time must pass every `_check`. That includes the DELTA, compared line for line (328 lines) after blanking evidence and authorizer.
  - Under the Owner, `_approvals` must be empty and its bytes must differ from the simulated bytes.
  - `verify` also refuses a placeholder time in the file. So actual approval evidence is distinguished from simulated evidence before the first write and after the writes, and `_approvals` independently validates the exact approval.

New resolutions:

- `resolve-classes-druid-wild-shape-known-forms-animals-animals-part-1`
- `resolve-spells-polymorph-effect-animals-animals-part-1`
- `resolve-classes-druid-wild-shape-known-forms-monsters-animals-part-1`
- `resolve-spells-polymorph-effect-monsters-animals-part-1`

All four target `animals.animals`.

## Preservation

- **`_kept(prior, final)` is empty.** It compares, evidence included, as multisets:
  - the 21 other batches' acceptance batches, span and review-unit records;
  - the 1434 prior reference-resolution records and resolutions.
- **Nothing is carried forward in general.** The 95 stat blocks are not re-read: each direct read is unchanged, as the reviewed consumer evidence shows.
- **`_expectations` is `(10432, 10433, 0, 1)`.** The one expectation added is the heading span's, under `animals.animals`.
- **`_approvals(final)` is empty.**
- **`_read_back(final) == RECORDED_AT`.**
- **Findings are exactly (64, 28), with no other findings.** Dangling component claims: none.
- **Disclosed boundary: Animals acceptances re-recorded.** The replaced Animals batch cannot keep its evidence, because its proposal identity changed. Its 836 span and 96 review-unit acceptances (835 + 1 heading span, 95 + 1 unit) are therefore recorded again under this decision. `_reowned` counts them.
- **The replaced Animals recording is not lost.** It was proposal `19685bc2…53cd`, under its own Owner approval, and it remains reproducible at its recorded bytes through the hub's `remaining_recorded()` (the rebuilt e0fd7690 state). It is not mutated in the committed file; it is superseded there.

## Dependent gates moved

Only the tests and pins the new committed bytes invalidate were moved. Historical checks are kept.

- **`tests/ingestion/mechanical/_replacement_chain.py`**:
  - loads `ANIMALS_CATALOGUE`;
  - `COMMITTED_SHA256` is now `ANIMALS_CATALOGUE.RECORDED_SHA256["resolved"]`;
  - adds `remaining_recorded()`, which is `ANIMALS_CATALOGUE.prior()`;
  - updates the docstring.
- **`test_animals_proposal.py`**:
  - The remaining-references test is now historical (`test_the_remaining_references_recording_is_kept`). It checks `remaining_recorded()` at `e0fd7690…` and `REMAINING.recorded()`, with the same kept, approvals, read-back, identities, expectations, counts and (68, 29) assertions.
  - The new `test_the_committed_oracle_records_the_animals_catalogue` checks:
    - the file sha and the production resolver's bytes;
    - that `ANIMALS_CATALOGUE.recorded()` equals the file;
    - `_kept`, `_approvals` and `_read_back`;
    - the Animals (identity, rule);
    - `_reowned == (836, 96)` and `_expectations`;
    - the counts, 0 violations and the (64, 28) findings.
- **`test_committed_accepted_authority.py`**: the named identity set drops the replaced Animals identity `19685bc2…` and adds `ANIMALS_CATALOGUE.IDENTITY` (`228726d2…`). The now-unused `ANIMALS_PROPOSAL` constant was removed.
- **`test_source_release_readiness.py`**: 10484 → 10485 spans and 1434 → 1438 resolutions, with the docstring updated.
- **`oracles/README.md`**: the current-file paragraph was updated. It was edited before any test ran.

### Test evidence

All runs used `pytest --no-cov -q -p no:cacheprovider`, `RTK_DISABLED=1` and the venv python. They ran in parallel from 10:49:56Z, with no edits to the oracles directory during the runs.

| Log | Files | Result | Ran | Exit |
|---|---|---|---|---|
| `t_authority.txt` | `test_committed_accepted_authority`, `test_source_release_readiness`, `test_declared_record_expectations` | 45 passed | 10:49:57–10:54:08Z | 0 |
| `t_animals.txt` | `test_animals_proposal` | 15 passed | 10:49:56–11:01:13Z | 0 |
| `t_monsters.txt` | `test_monsters_proposal` | 14 passed | 10:49:57–11:03:08Z | 0 |
| `t_others.txt` | `test_character_origins_feats_acceptance`, `test_gameplay_toolbox_proposal`, `test_magic_items_proposal` | 61 passed | 10:49:58–11:13:37Z | 0 |

Lint results:
- ACCEPT script: black, ruff and mypy `--strict` (`MYPYPATH=src`) exit 0.
- Hub and moved tests: black and ruff exit 0.

No broad suite was run.

**Consumers that now fail closed (intended for superseded recordings):**
- `issue-5d-remaining-references-ACCEPT.py --verify` ran 11:10:54–11:12:26Z and exited 1 with `resolved artifact drifted` (`rr-verify.txt`).
- `issue-5d-animals-part-catalogue-REPLACEMENT.py` (verify-only) ran 11:12:26–11:12:29Z and exited 1 with `accepted changed` (`apc-constructor.txt`). The constructor asserts the committed bytes it was built over; it is pinned and was not edited.
- The per-recording tests reach those recordings through the hub's rebuilt states instead.

## Not claimed

- **Consumer probes.** The DISABLE consumer path was checked in the reviewed packet. REPLACE and combined selection were not newly probed; no production defect was identified, and no test for them is claimed.
- **Deferred gates.** pip-audit and expanded mypy remain non-green and deferred. No full-green claim is made.

## Secrets baseline (scoped)

| | |
|---|---|
| Before | `eeea9c0f3feb860e3ca475619a1704625e75b99e95d50590e9348d9d36243884` (the manifest value; `apply.py` asserted it before writing) |
| After | `7a0327fa2f2227cce229f5301cbb8b367280453a15d9941294a52d23f7e3cbdd` (staged by name) |
| Added / pruned / line-moved | 13 / 2 / 1008 |
| Entries / files | 5748 / 141 (the ACCEPT script appended as the one new file key) |

**Scope.** `.claude/_sp/apc/bl2/bl_scan.py` rescanned only this record's files, using the baseline's own plugins and filters from a private settings copy:
- the ACCEPT script, the oracle and its README;
- the hub and the three moved tests;
- this note.

The README, the hub, the authority and readiness tests and this note have no findings.

**Delta by file.**
- **ACCEPT, +11.** Each value is public:
  - the constructor, proposal, drafts and DELTA file SHAs;
  - the new and replaced proposal identities;
  - the simulated SHA;
  - the Owner review and manifest SHAs;
  - the two recorded oracle SHAs printed by the run logs.
- **Oracle, +2.** These are the new Animals proposal identity and the Animals `semantic_diff_hash`, which is in the reviewed DELTA.
- **Oracle, −2.** These are the replaced identity `19685bc2…` (SHA-1 `8704a0d4…` matches) and the replaced Animals `semantic_diff_hash`, which the rescan no longer finds.
- **Line moves: 1008 = 1005 oracle line refreshes + 3 `test_animals_proposal.py` line refreshes.**

**Preserved** (checked against the index copy): the top-level settings, plugins, filters, `version` and `generated_at`; every other file's entries; the existing key order. Every added entry has `is_verified` false.

**Not done.** No `scan --baseline` was run, and no allowlist pragma was added.

**Hook.** `detect-secrets-hook --baseline .secrets.baseline` ran on the 8 scoped files plus the baseline. Every run is in `.claude/_sp/apc/bl2/hook.log` with its exit code and SHA: the earlier runs preceded final edits to this note, and the last two runs cover its final text. All exited 0 with the SHA stable at `7a0327fa…`. The deltas are in `.claude/_sp/apc/bl2/baseline-delta.json`.

## Final manifest recheck

At 2026-09-29T11:22:17Z (`.claude/_sp/apc/recheck-final.txt`):
- The Owner review and manifest SHAs match.
- The REPLACEMENT constructor, PROPOSAL, DRAFTS, DELTA and review packet match.
- The only mismatches are the two this record expects: the oracle, which the recording changed, and `.secrets.baseline`, which the scoped update changed.

## Blockers and retention

- **Partial publication.** The partial-publication block stands: 64 reference findings and 28 uncovered leaves remain.
- **Release order.** It is unchanged. Animals is still released before its governing Monsters rules. The Owner's order decision holds: finish the packets, then one bounded order pass before publication or activation.
- **Sources and pins.** No source, pin or release-order change was made beyond the recording-dependent inputs.
- **Nothing released or committed.** Nothing was published or activated, and nothing was written to a shared DB. There were no commits, pushes or merges.
- **Untouched:**
  - the REPLACEMENT constructor, PROPOSAL, DRAFTS, DELTA and review packet;
  - the 36 staged deletions and 4 stashes;
  - the quarantine corpus;
  - `issue-5d-source-correction-REPLACEMENT-PACKET.md`;
  - the root `afterworlds.db`;
  - the `574662e9` oracle;
  - the pre-existing modification of `issue-5d-core-play-completion-generator.py` and other unrelated modifications.
- **Process disclosure.** One Bash call in this session used a leading `cd` into the repository root, contrary to standing instructions. It only performed the intended `drafts()` edit.
