# CRD Issue 5c release-order replacement candidate — exact acceptance packet

Prepared 6 October 2026 for independent Codex review and exact Owner
acceptance. **This is a candidate, not an acceptance or a recording.** Nothing
here was written to the live oracle, staged, committed, pushed, published,
activated or written to a shared store. Every approval inside the candidate is
a clearly labelled **simulation**; recording requires the Owner's exact
acceptance of the candidate pinned below and then real approvals.

Authority: the [21 September restart decision](../../docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md)
and the release-order Owner direction recorded in the
[release-order review](issue-5c-release-order-review.md) ("correct the release
order in one bounded pass before publication or activation"). Retained evidence
is in [`issue-5c-release-order-candidate/`](issue-5c-release-order-candidate/).

## What is asked of the Owner

Accept, or decline, exactly this replacement candidate:

| Pin | Value |
| --- | --- |
| Candidate file | `issue-5c-release-order-candidate/candidate/srd-5-2-1-corpus-8781d4e0-a3b.json` (35,061,929 bytes) |
| Candidate SHA-256 | `8a6a9a9c305f41207190c0deb55875a027019116ce3f825a6a0425a3a115b4bf` |
| Replaces live oracle | `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json`, SHA-256 `e6f5f36aa3af13807bbff721797d971dcf0d8e588a97483c7d769cf88cbd1308` (unchanged) |
| Code change | `CORPUS_FILES` in `src/afterworlds/ingestion/corpus/source_units.py` (SHA-256 `4240742c…6df3be7`) and one focused order test in `tests/ingestion/corpus/test_source_units.py` (SHA-256 `bb404f22…2a72395`); deltas against the pre-edit working tree in `source_units.diff-vs-pre-edit.patch` and `test_source_units.diff-vs-pre-edit.patch` |

Acceptance would authorize recording the candidate content with real Owner
approvals in place of the simulated ones. It would not by itself authorize
commit, push, merge, publication, activation or a shared-store write.

**How the accepted SHA relates to the recorded bytes.** This candidate carries
simulated approvals, so recording with real approvals will produce different
bytes and a different SHA.
- The recorded oracle may differ from this candidate only in the acceptance
  evidence fields: `reviewer`, `accepted_at`, `rule`, `authorized_by`,
  `authorization_reference` and `resolved_at`.
- `proposal_identity` is not in that set. It is `hash_obj(proposal_payload(...))`
  (`proposal.py`), derived from proposal content under the same binding, not
  from approvals, so it must stay fixed between this candidate and the
  recording.
- The proof will be a `compare_oracles`-style run of the recorded oracle
  against this candidate (not against the live oracle). It must report zero
  unaccounted patterns and differences only in those six fields.
- Exact acceptance of this complete candidate covers all 24 batches and all
  1,486 reference resolutions under the new binding. The new approval receipt
  will preserve the Owner's actual acceptance wording; native recording will
  derive its real reviewer, timestamp and receipt references from that fresh
  acceptance. Old approvals will not be copied or relabelled. No separate
  batch-by-batch approval or manually supplied timestamps are needed.

## The correction

`CORPUS_FILES` now follows the official PDF's printed chapter order:

legal-information, playing-the-game, character-creation, classes,
character-origins, feats, equipment, spells, rules-glossary, gameplay-toolbox,
magic-items, monsters, monsters-A-Z, animals.

The previous tuple was based on alphabetical `CONTENT_FILES`, with the
previously accepted Monsters-before-Monsters-A-Z correction already applied.
It still put Animals immediately after attribution and Playing the Game late.
The consolidated correction now follows the full official chapter sequence. Each leaf's global `occurrence_index` follows this
tuple, and readers order governing passages by it.

## Release identities

| Coordinate | Old (live) | New (candidate) |
| --- | --- | --- |
| package_uuid | `67c81736-15fd-5e82-8523-e84922f0a7c6` | `1299484e-c72d-509b-bd8d-d0169ee1f8d2` |
| release_version | `5.2.1-corpus.3fe24ff6-4e3` | `5.2.1-corpus.8781d4e0-a3b` |
| authoritative_source_hash | `8974902d…3d87` | `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87` (unchanged) |
| transform_config_hash | `648ac3dd3b68b160d573338ad3bf50fba6c4726d5141da2f7b0c86224928d947` | `753e76087885ee99fb3fa97932c6a0e5b5075bbed1b0acd466d90a029ff0bc01` |
| ledger_hash | `67bd4a59f3012718903671ebb824551cea63ef3134a4e850d4115366edc77932` | `8e29a85dd10682e5a42b5a66a432d182c61a5de63c2803d901bfa02d8f0650b2` |
| bundle_root_hash | `87d95278c3349a5162ae7475a788c3d047bfdef30f56a73db9d7c22e3fe7f760` | `0941dc966337f190f5a6ed3b5dfc0370dc29efd15483889bf2a0d9fb7c564787` |
| persisted_corpus_digest | `8b7227d3792566a46651b675b89448d85a2c5cefee2f3c61bbcf57486e302d42` | `3717fa115a5abb68c4be179d0d643992ab7392a0f9cd5ca5dc4a73da9258e3c3` |

Both releases: 10,464 units, 2,877 containers, 10,464 chunks. Full identities:
`releases/old/identity.json`, `releases/new/identity.json`. The old build
reproduces the live binding exactly. The new release was derived natively from
the corrected tuple; the current oracle and its approvals were not relabelled.

## Evidence

Raw logs and exit files are in `issue-5c-release-order-candidate/run/`. Each log
records its command line and the SHA-256 of every file argument.

1. **Release order** (`compare-release`, exit 0). The leaf and container ID sets are
   identical. Only `occurrence_index` (10,459 units), `page_index` (10,292) and
   `chunk_id` (all 10,464) differ. `page_index` equals file position in each
   order. Within-file order is preserved for all 14 files. The new global runs
   equal the official sequence, with no file omitted or duplicated. Locators and
   the citation report are identical.
2. **Native chain capture** (`capture`, exit 0). The 43-step native chain (24
   `accept_proposal` and 19 `resolve_references` calls) was captured from the
   live recording; its replay equals the live oracle bytes. Retained as
   `chain/live-chain.pkl` (SHA-256 `b5d82c71…a0e`) with summary
   `chain/live-chain.json`.
3. **Recomposition** (`recompose`, exit 0).
   - Control: verbatim re-execution of the chain equals the live oracle byte for
     byte.
   - Candidate: the same chain with every input mechanically rebound: 1,510
     `ReleaseBinding` values old to new, and 32,800 `chunk_id` values through
     the leaf-keyed maps. Reviewer, rule, authorization and timestamp values are
     replaced by `SIMULATION ONLY … not an Owner acceptance/authorization`
     values. No semantic input is edited.
   - The `load_accepted_inputs` round trip is byte-equal and the binding equals
     the new release.
   - Residual old uuid, version, transform, bundle and digest values, Owner
     names and old chunk IDs: 0 each.
   - Native findings against the new store: **reference 0, uncovered-leaf 0,
     other 0**.
4. **Old/new payload accounting** (`compare-oracles-3`, exit 0;
   `reports/oracle-delta-final.json`). The candidate was normalized back
   through the binding and chunk maps (7,435 binding values, 32,800 chunks).
   - Every remaining difference is accounted evidence:
     - proposal identities: 24;
     - rules: 24;
     - `accepted_at`/`reviewer`: 10,493 records and 1,476 review units;
     - the four resolution evidence fields: 1,486 each.
   - Four collections changed only in order: acceptance records 10,493;
     review_unit_records 1,476; prose_bindings 16,400; provenance 30,236. Each
     is held in canonical-payload order in both artifacts, so its order follows
     from the accounted chunk IDs and simulated timestamps.
   - **Unaccounted difference patterns: 0.** Schema 17, 24 batches, 1,835
     records, 1,486 resolutions and every route, destination, condition and
     exception are preserved. The earlier attempts `compare-oracles` and
     `compare-oracles-2` (exit 0, positional and partially keyed) are
     superseded history.
5. **Native persistence and reconstruction** (`reader-proof2`, the first block).
   - Each oracle was persisted with `persist_draft` into a temp copy of its own
     release store.
   - `verify_reconstruction` returned `()` for both.
   - The reconstructed binding equals the persisted binding and the oracle
     binding.
   - The reconstructed candidate re-identifies to the same projection UUID:
     `498a9a0a-c693-53e5-8bcd-32143034fbe0` old, `8d8cb42c-aefe-559c-9d85-6ba975c038af` new.
   - Sessions were closed and engines disposed before temp cleanup. Nothing was
     activated or published.
6. **Reader proof** (`reader-proof2`; `reports/reader-proof2.json`).
   - Thirteen explicit records were read through the unmodified production
     GameMaster view. Only binding resolution was stood in. The old oracle was
     read over the old store and the candidate over the new store:
     - Animals: Wolf, Giant Owl, Swarm of Insects;
     - Monsters: the Monsters introduction (`parts_of_a_stat_block`) and Aboleth;
     - origin, creation and class controls: Acolyte, Level Advancement (route
       bearing) and Barbarian multiclass;
     - other controls: Casting Spells, Blinded, Acid, Activating a Magic Item,
       and Boon of Spell Recall (route bearing).
   - Comparison:
     - `__occurrence__` is removed, chunk IDs are mapped to leaf IDs, and
       package/version/projection values become placeholders.
     - Everything else is compared exactly and positionally.
     - Only `governing_prose` sequences may differ. Old must be in old file
       order and new in new file order, and new must equal the old stably
       re-sorted by new file position.
     - Routes, alternatives, destinations, component order and other arrays are
       not sorted.
   - All 13 records had 0 differences and non-empty prose.
   - For each Animal (3 of 3), the check required at least one component that
     reads both its own Animals text and the governing Monsters rules. Each had
     one: the old release read Animals first, and the new release reads the
     Monsters rules first and Animals last.
   - The Monsters introduction, Aboleth and all eight controls had no
     reordered component.
7. **Fail-closed controls** (`reader-proof2`, final block). Each case's actual
   outcome was asserted and recorded, not just the exit code.

   | Case | Result |
   | --- | --- |
   | Live oracle on the old store (real control) | ok, 0 findings |
   | Candidate on the new store (real control) | ok, 0 findings |
   | Candidate (new binding) on the old store | refused, 69,862 findings |
   | Live oracle (old binding) on the new store | refused, 69,862 findings |
   | Persist the candidate into the old store | refused, FOREIGN KEY constraint |
   | Persist the live oracle into the new store | refused, FOREIGN KEY constraint |
   | Mixed: new binding with old chunk IDs, new store | refused, 59,398 findings ("chunk … is not authoritative prose of release 1299484e…") |
   | Mixed: old binding with new chunk IDs, old store | refused, 59,398 findings |

   Admission mechanisms:
   - **Validation refusals** come from the bound-corpus gate: `load_bound_corpus`
     plus `validate_candidate` against the store's own release.
   - **Persist refusals** come from SQLite foreign-key enforcement. The
     projection header's `package_uuid` is a foreign key to
     `rp_corpus_releases.package_uuid` (`persistence/orm/mechanical.py`), and
     the wrong store does not hold that release. Production `create_engine`
     (`src/afterworlds/persistence/database.py`, `_set_sqlite_pragmas`) enables
     `PRAGMA foreign_keys = ON` on every connection. The proof helper's own
     identical pragma listener is redundant with it, not the source of the
     refusal.

8. **Focused order test** (`focused-order`, exit 0). 34 passed, with the label
   "FOCUSED DIAGNOSTICS ONLY". These are 34 distinct collected cases. The
   command repeated the test path, so this is not 17 cases run twice.
9. **Preservation** (`preservation`, exit 0; `reports/claude-preservation.json`).
   - Against the pre-edit snapshot, these are unchanged: HEAD `1388939`, the
     branch, the index, the four stashes, the live oracle, `source_pin.json`,
     the community source bytes, the official PDF, and the external guidance and
     settings.
   - The only changed pre-existing files are the two authorized code and test
     files.
   - The final rerun, `preservation-final` (exit 0;
     `reports/claude-preservation-final.json`), was taken after the restart
     opening and baseline edits. The same checks hold, and the only changed
     pre-existing files are the two code and test files, the restart opening,
     and `.secrets.baseline` (unstaged).

## Raw outcomes, including non-green runs

| Run | Raw exit | Meaning |
| --- | --- | --- |
| build-old, build-new, compare-release, capture, recompose, compare-oracles(-2,-3), focused-order, gate-black, gate-ruff, gate-mypy-src, preservation, preservation-final, reconstruct-diag, reconstruct-diag2 | 0 | as above |
| reader-proof-attempt1-missing-tables | 1 | Scratch stores lacked the 5d tables; superseded. Later runs add them to temp copies with `create_all`. |
| reader-proof-attempt2-aborted | 4294967295 | Intentional coordinator interruption. Its "semantic difference" lines came from a helper gap (Pydantic `RulesPackageBinding` not normalized), not from the candidate. |
| reader-diag1 | 1 | JSON `TypeError` on the same un-normalized Pydantic value (helper bug). |
| reader-diag2 | 4294967295 | Intentional checkpoint interruption. Its three sampled records differed in prose order only. |
| **reader-proof2** | **1** | **Not all green.** Every reader, Animal/Monsters, control, native verification and fail-closed check passed (59 of 61 recorded checks). The two failures are a strict helper check, `reconstructed candidate == identified candidate`, which failed on both stores, **including the old live-oracle control**. `reconstruct-diag` located the cause, and the asserting `reconstruct-diag2` (exit 0; it fails on any other pattern) confirms it on both stores. Native reconstruction returns two components' `fact_qualifiers` (`glossary.exhaustion/removing_exhaustion_levels` and `glossary.magic/long_casting`, neither in the 13-record reader set), and on the old store `review_unit_acceptances`, in a different tuple order with identical content. The native contract compares identity: `verify_reconstruction` is `()` and the projection UUID re-identifies. This is pre-existing persistence behaviour, independent of release order. It was not patched; it is surfaced below. |
| boundary-readiness | 1 | `test_source_release_readiness.py`: 2 failed, 13 passed. The pending-recording boundary for the new binding; see below. |
| gate-mypy (both files, strict) | 1 | 32 errors, all in the test file. The pre-edit test file alone has 31 (`gate-mypy-test-preedit`, exit 1) and the HEAD copy has 19 (`gate-mypy-test-head`, exit 1). The new test adds one `no-untyped-def` for its `structure` fixture argument, matching the file's convention. The source file is strict-clean. |

## Secrets baseline

The retained JSON, log and script files carry public SHA-256s, release hashes
and proposal identities: 128 Hex High Entropy hits in 20 files, of which 112 hits in 18 files were found first and 16 hits in the two final preservation receipts later. Every flagged
line was inspected after masking and contains only such values.

Coverage was appended additively to the working `.secrets.baseline`, which
remains **unstaged**:
- the existing results were preserved byte for byte;
- `detect-secrets scan FILES` was used without `--baseline`;
- no `pragma` was added.

| Hook run | Exit | Meaning |
| --- | --- | --- |
| Private copy | 0 | Content-clean. The final run covers all retained files, this packet and the restart document. |
| Real hook | 1 | Only "Your baseline file (.secrets.baseline) is unstaged". Staging is not authorized. |

The `.secrets.baseline` index entry predates this task; the index hash is
unchanged. At Claude handoff, the working baseline SHA-256 had gone from
`901663b0f2663c6d42620005470fe3183a1eb55e4f3d45791ebe25927427cba5` (pre-edit) to
`9ee16d356655e2fb79867bf29d33f3013be8841c18de4e7c1418418bde79fe35`, an
additive append only. The final preservation receipt records an intermediate
value, `d8441c1a…`, taken before the last 16 hits were appended.

Codex subsequently added scoped public-hash coverage for its independent review evidence. The [final secrets receipt](issue-5c-release-order-codex-evidence/secrets-validation.json) distinguishes content-clean private checks from the real unstaged-baseline refusal. All prior entries and scanner settings remain exact.

## Boundaries and limits

- **Pinned-binding tests.** About 25 test files pin the old release identity,
  and 89 use `source_release_db`. With the working-tree release now new, those
  that require committed authority for the build fail. The readiness file shows
  two such failures: "only the two pilot authorities" (`assert None is not
  None`), and the unreviewed-publication refusal (outcome ABSENT, not
  UNRESOLVED). This is expected until the replacement is recorded and the pins
  move with it. It is a visible boundary, not patched here.
- **Proof scope.**
  - The reader proof covers the 13 explicit records above. It is not a sweep
    of all 1,835 records.
  - Payload-level equivalence of all records is item 4.
  - Candidate reproducibility rests on the deterministic chain: the control
    re-execution equals the live oracle byte for byte.
  - Per the review instruction, the candidate was not re-derived a second
    time.
- **Deferred gates.** Not run or not green:
  - broad suites;
  - expanded mypy (the 11 pre-existing consumer errors remain);
  - coverage;
  - pip-audit.
- **Verification-helper limit: unordered reconstruction tuples.** Raw tuple
  equality was too strict for native canonical collections. The independent
  [Codex canonical reconstruction report](issue-5c-release-order-codex-evidence/codex-canonical-reconstruction.json)
  proves exact complete projection payload and acceptance-evidence equality
  for both stores, with zero native verification findings (exit 0). This
  closes the helper gap without a persistence patch, semantic change or new
  ownership decision. The combined helper's raw exit 1 remains retained.
- **Awakened Plant** remains uninstalled and unactivated.
- The pre-existing out-of-scope reader-retention residue remains deferred.

## Replay

Reuse unaffected verified stores and the captured chain. The [Codex review's
replay discipline](issue-5c-release-order-candidate-codex-review.md#next-step-and-replay-discipline)
pins the old/current source recipes and native code. An output directory name
does not select the old recipe: an old-release rebuild needs a disposable
pre-edit source snapshot. Use full intended scratch output paths; do not
revert the active working tree or overwrite existing outputs.


Run from the repository root with
`RTK_DISABLED=1 PYTHONUTF8=1 MYPYPATH=src venv/Scripts/python.exe`. The
scripts and the runner are retained in `scripts/`, pinned by SHA-256 in each
log's `input` lines. The scripts read and write
`.claude/_sp/release-order-candidate/`.

1. `build.py` builds whatever `CORPUS_FILES` the working tree holds.
   - `rel-old` was built at 03:03Z from the **pre-edit** `source_units.py`
     (SHA-256 `279d8708…dc076`).
   - The `CORPUS_FILES` edit landed at 03:04:55Z, and `rel-new` was built at
     03:05Z from the edited file.
   - To replay `rel-old`, reverse-apply `source_units.diff-vs-pre-edit.patch`
     to a copy of the tree, run `build.py …/rel-old`, and confirm its identity
     equals `releases/old/identity.json`. That identity is the live binding;
     `recompose.py` asserts every oracle binding equals it.
   - Then restore the edited file and run `build.py …/rel-new`.
   - The scratch DBs (15.7 MB each) and `leaves.json` files are not retained.
     Steps 2–8 read them from `.claude/_sp/release-order-candidate/`, so replay
     depends on step 1.
2. `compare_release.py`.
3. `capture.py chain/live-chain.pkl`.
4. `recompose.py chain/live-chain.pkl candidate`.
5. `compare_oracles.py candidate/srd-5-2-1-corpus-8781d4e0-a3b.json OUT.json`.
6. `reader_proof2.py candidate/srd-5-2-1-corpus-8781d4e0-a3b.json OUT.json`.
7. `reconstruct_diag.py candidate/srd-5-2-1-corpus-8781d4e0-a3b.json`.
8. `reconstruct_diag2.py candidate/srd-5-2-1-corpus-8781d4e0-a3b.json` (the
   asserting version).

Every run behind the accepted evidence logs the SHA-256 of its script, and each
matches the retained copy below. The superseded attempts `compare-oracles`
(`d22c4fef…`), `compare-oracles-2` (`edf8af10…`),
`reader-proof-attempt1-missing-tables` (`e7f92bf1…`),
`reader-proof-attempt2-aborted` (`20b7ce5a…`) and `reader-diag1` (`ba452b01…`)
pin script versions that were edited in place and are **not retained**. Their
logs remain as history only.

| Script | SHA-256 |
| --- | --- |
| build.py | `0ccb212c285e27b7016be1939b007e035d54c5c3df374d94633e9a9bf3062960` |
| compare_release.py | `25e33ab8e762d871f3eb4988d6e0c2c13558882995f4ae1bbcde139a5682cc25` |
| capture.py | `d73f4f61d17ff756a54aea3c9be721b0535139532c121826dd639df9f2567749` |
| recompose.py | `76e5b79899e6c751f9a04de1e52936097bea07d07dada0fc090cdc0ce9f739f4` |
| compare_oracles.py | `14c279dbe6544c3502075973fc9ffadb937fdcb09b562d122aa45973714ca67b` |
| reader_proof2.py | `ee45247e52932eaee42a09da466b5c3d6afcbfec4f53825c57631519635a9442` |
| reconstruct_diag.py | `ec93b5fbce7542103cde75e452c211949312491db9848b1f64d85ec15699e825` |
| reconstruct_diag2.py | `01e66f283198baa32dd79334a4159430c9a9ebaea176fde1c44654567446e4c9` |
| claude_preservation.py / claude_preservation_final.py | `7cc9a34a79c9363ffd2b3b48fa009937174f6af5ad53d7bbca2d0ae67e3eed9d` / `3ff476565289e7b7bc401a7edff536bd738f4477f0b83ef6cc9d5839e35cc980` |
| reader_proof.py (superseded; matches reader-diag2 only) | `748cb1127410d876b05711273d5f72d32abafde63804994877a02d9ab7a8eef8` |

Report SHA-256s:
- `oracle-delta-final.json`: `20ec193738d6520a46743af46474feb0e514b38ae59558cfcb09f7345620af1c`
- `reader-proof2.json`: `bed0d98b5243f6f6822fb01e186a86bd7ebc9c06ec5cd8d4a533e8feee398ef4`

## Stop condition

Stopped before recording. Next steps:
1. Independent [Codex review](issue-5c-release-order-candidate-codex-review.md)
   is complete and includes this final clarified packet.
2. The Owner's exact acceptance, or decline, of candidate SHA-256 `8a6a9a9c…`.
