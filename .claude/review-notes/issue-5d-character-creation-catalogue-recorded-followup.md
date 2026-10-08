# CRD Issue 5d — Character Creation catalogue: recorded follow-up (#132, #137)

## Authorization

The Owner's statement, verbatim:

> I accept the exact Character Creation catalogue proposal and its two reference resolutions, retaining 62 reference findings, zero uncovered leaves, and the partial-publication block.

**Approval time:** the statement preceded the parent's observation at 2026-09-29T18:35:28Z. No more precise message time is claimed. The recorded action carries its real execution UTC times.

**Owner files.** The parent verified all seven manifest files and the starting baseline. This task rechecked the manifest files and baseline `0df63f1d…` at 18:39:31Z, pinned the two Owner files in the ACCEPT script, and rechecked every pin after the write (`manifest-postwrite.txt`, 19:05:32Z; all match):

| File | SHA-256 |
|---|---|
| `character-creation-catalogue-owner-review.md` | `8897f37bd8a5d5f1d5c7f44bdb290faad3545a98bae05601f90d1b3c53a87ffd` |
| `character-creation-catalogue-owner-manifest.json` | `234eb06333f3b04d424639d9388a5757c92f36006ff44f6c93c7719d7b83db1b` |
| generator | `7ffb2a6f969c5d7d23592b2cfc5e1cbd6c1367bef1239a2274b4d381e99c3433` |
| PROPOSAL (identity `cee3b640f955a34ed627fb720b8f9ec121d605dda6f792ba469ebe7ac429a5be`) | `98864a96933a3c967d0728b5bc2252f12a2af5e43accadf89595325e363adc2c` |
| resolutions-DRAFTS | `47167c97d16436905aee4149be1c56d1ee7cc98ea8778696bdec46bdc1597ae5` |
| DELTA | `d48ce267966e85bb218f0bdfe4b25a0e89d0363e40a43148cf0d011a4c556dc8` |
| review.md | `2efbe02be979374f4c9e93c7e0552b151ac017cf18eb318a4284ee2ef2c925f0` |

The ACCEPT script asserts the generator, PROPOSAL (with `expected_identity`), DRAFTS, DELTA and review.md hashes on every run.

## Final oracle

`src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json`

| State | SHA-256 | Batches / records / spans / units / resolutions | Reference / uncovered-leaf findings |
|---|---|---|---|
| prior (framing-coverage recording) | `15478aa5ea712b9946999ff865283cd12b36dd4f917137a76c225543066b8922` | 23 / 1834 / 10491 / 1475 / 1438 | 64 / 0 |
| **recorded (final, on disk)** | **`ea0c219feec8571142c797ebd127713d55595db7309c64670a1436756b4413de`** | **24 / 1835 / 10492 / 1476 / 1440** | **62 / 0** |

Other findings: 0. Reference-resolution violations: 0. The partial-publication block stands.

**Simulated state.** `5dc89b9585450040d1227f98831ea5b288d1c03daee7bafbafec345f02a982a9` was pinned by this task, not by the review packet. It is tied to reviewed material because `_precheck` asserts it equals the generator's own `GEN.drafted(GEN.accepted(prior, candidate), drafts)`. It was never written; the recorded bytes differ from it.

## Recorded action (real UTC)

Script: `.claude/review-notes/issue-5d-character-creation-catalogue-ACCEPT.py`, final sha `e677fcbcd3917d2be3b144253d65228c3b15f96e3d9eb892775a01a0a8a71f6a`. Logs: `.claude/_sp/ccr/`.

| Action | Log | Result |
|---|---|---|
| earlier precheck runs (no log kept) | — | Failed before any write: first on `SIMULATED_SHA256`, which was unpinned by design; then on the DELTA comparison, fixed as below |
| `--simulate`, final | `simulate.txt` | EXIT 0; nothing written |
| `record-character-creation-catalogue` | `record.txt` (start 18:49:27Z, end 18:52:08Z) | EXIT 0; `accepted_at` **2026-09-29T18:51:30Z**, `resolved_at` **2026-09-29T18:51:34Z**; `ea0c219f…`; post-write `_state()` and `verify` pass |
| `--verify` against the pins, over the replayed prior | `verify.txt` | EXIT 0 |
| framing-coverage `--verify` | `framing-verify.txt` | EXIT 1: unrecognized batches (expected refusal) |

Nothing was re-recorded. `RECORDED_AT` and `RECORDED_SHA256` were pinned after the write, from the values the run printed and read back.

**Recording shape.**
- One write of two native steps, each reading the UTC clock when it runs:
  1. `accept_proposal` of the exact PROPOSAL as batch `character-creation-catalogue`, with `rule` set to the verbatim statement and `reviewer` set to the Owner;
  2. `resolve_references` with the two drafts loaded from the pinned DRAFTS file by the loader's own parser. `reviewer` and `authorized_by` are the Owner, and `authorization_reference` names the Owner files, the generator, the candidate, the drafts and the prior, and quotes the statement.
- This simplifies the Animals two-write pattern: no intermediate state ever reached disk. Both times are recorded and read back.
- **Base.** The append reads the committed file as loaded. No chain is rebuilt, and no batch or resolution is replaced.
- **Prior.** The oracle is untracked, so after the write `15478aa5…` exists only as a replay: `FRAMING.composed(FRAMING.prior(), OWNER, 12:47:38Z)`, sha-asserted. `--verify` and the tests use this replay. Before the write, `_precheck` proved that the composition over the replay equals the composition over the loaded file, byte for byte.
- **Real vs simulated evidence.**
  - `_precheck` runs every post-write check on the Owner's composition at a placeholder time.
  - `verify` refuses the placeholder time and the simulated bytes.
  - `_approvals` requires:
    - the batch rule to be exactly the statement;
    - every span and unit acceptance of the batch to name the Owner;
    - both new resolution records to carry `(Owner, Owner, AUTHORIZATION_REFERENCE)`.
  - It passed on the recorded file.

## Preservation and replay evidence

These checks are from `record.txt` and `verify.txt`:

- **Prior content.** `MC._preserved(prior payload, final payload)` returns `[]`. The comparison is recursive, treats lists as multisets and includes evidence. So all 23 prior batches, 1834 records and 1438 resolutions keep their recorded approvals.
- **Batches.** The sorted (batch, identity) pairs are the prior's plus `(character-creation-catalogue, cee3b640…)`.
- **Resolutions.** The only new resolutions are the two draft ids:
  - `resolve-glossary-character-sheet-record-character-creation-character-creation-catalogue-1`
  - `resolve-glossary-player-character-record-character-creation-character-creation-catalogue-1`
- **Members and framing unit.** The records, components and prose bindings of the six members, together with `framing-coverage/character_creation`, are identical in the prior and the final state (195 items).
- **Findings.** Compared as multisets, the change is exactly `{"reference srd-5.2.1/character-creation:'Character Creation': unresolved reference": 2}` cleared, with nothing new. The result is 62 / 0, other 0.
- **Delta.** `EQ.Delta(prior, final).report()` plus `GEN.membership_report` equals the reviewed DELTA line for line (70 lines), with 0 removals in any collection.
  - The DELTA blanks reviewer, times and rule, but it carries the simulated `authorized_by` and `authorization_reference` on the two resolution records.
  - So both sides go through `REMAINING._authorizer_blank`, the same helper the Animals catalogue recording used. The first comparison, without it, failed on exactly those two lines, and the diff showed nothing else.
- **Reload.** The recorded file reloads to the same bytes.

The candidate, source and consumer evidence was reused as reviewed and not rerun: membership order, reading of 125 spans, DISABLE of a member and of the section. REPLACE is not claimed.

## Moved pins (historical checks kept)

| File | Change |
|---|---|
| `tests/ingestion/mechanical/_replacement_chain.py` | Loads `CHARACTER_CREATION`. `COMMITTED_SHA256` now points to its recorded sha. Adds `framing_recorded()` (the replayed prior). Docstring updated. |
| `test_animals_proposal.py` | The live framing test becomes the historical `test_the_framing_coverage_recording_rebuilds`: the replay must equal `15478aa5…` and pass `FRAMING._check`. New test: `test_the_committed_oracle_records_character_creation_catalogue`. |
| `test_committed_accepted_authority.py` | The new identity is added to the named set. |
| `test_source_release_readiness.py` | Batch set gains `character-creation-catalogue`; 10491 → 10492 spans; 1438 → 1440 resolutions. |
| `test_gameplay_toolbox_proposal.py` | Batch set gains `character-creation-catalogue`. |
| `src/.../oracles/README.md` | Current state and history entry updated. |

## Gates (raw)

- **ACCEPT script.** Black 0, Ruff 0, `mypy --strict` (`MYPYPATH=src`) 0.
- **Black and Ruff, rerun between 19:31:25Z and 19:33:27Z.**
  - Files: the ACCEPT script and the five edited test files.
  - `black --check` exits 0, with 6 files unchanged.
  - `ruff check` exits 0.
- **Gates ran on the final bytes.**
  - All code files were last written by 18:53:08Z.
  - That is before `--verify` (18:54:16Z) and before the pytest start (about 18:54:47Z).
- **Focused pytest** (`pytest.txt`, 9 node ids, `-p no:cacheprovider`): **9 passed in 1624.06s**, EXIT 1.
  - The exit 1 is only the repo-wide `--cov-fail-under=80` applied to a 9-test run (42.70%). No test failed.
  - The ids were:
    - the two `test_animals_proposal` tests above;
    - `test_committed_accepted_authority::test_no_refused_candidate_is_selectable`;
    - `test_source_release_readiness::test_the_replacement_release_has_only_the_two_pilot_authorities`;
    - `test_gameplay_toolbox_proposal::test_the_committed_oracle_records_the_owner_acceptance`;
    - `test_character_origins_feats_acceptance::test_the_recorded_bytes_are_what_the_two_seams_record`;
    - `test_magic_items_proposal::test_accepted_then_resolved_in_memory_preserves_everything` and `::test_the_committed_oracle_records_the_owner_acceptance`;
    - `test_monsters_proposal::test_the_committed_oracle_records_the_owner_acceptance`.
- **Not run: broad suite.** Not green is claimed.
- **Deferred, not green:** pip-audit and expanded mypy.
- **detect-secrets.**
  - A scoped scan with `PYTHONUTF8=1` found 12 new public hashes and no obsolete entries.
    - The ACCEPT script's ten are the pins above, plus the recorded sha.
    - The oracle adds two: the new `proposal_identity` and `semantic_diff_hash`.
  - The baseline went from `0df63f1d…` to `d7e9b2f79dac6b34901301a049d3697c85bdeab53f15c87fc01043cc2e5c5235`.
    - 1010 oracle entries only had their line numbers refreshed.
    - Settings, filters, `generated_at` and the other 144 files are identical.
  - The baseline is staged by name. Evidence is in `.claude/_sp/ccr/bl/`, including the logs of both hook runs.

## Limits

- Nothing is committed, pushed, merged, published or activated.
- The release order is scheduled for one bounded pass after the packets, before publication.
- Five whole-chapter references stay behind the nested-catalogue reach boundary.
- The compound, dynamic, Origin Feats and Spellbook residue is separate.
- #4 (`glossary.hit_point_dice`) stays held.
- No source errata were encountered.
