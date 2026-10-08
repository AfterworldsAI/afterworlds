# CRD Issue 5d — Equipment cited targets recorded: follow-up (#132, #137)

The Owner accepted the exact replacement Equipment proposal and its 161 reference resolutions. This records them in
the committed oracle for the Monsters-corrected release, then moves the dependent live tests to that authority. It
is the record Codex verifies independently before the remaining 5d work continues. No renewed semantic approval is
needed for these exact accepted items.

## Authorization recorded

**Owner statement, verbatim (as given in the request):**

> I accept the exact replacement Equipment proposal and its 161 reference resolutions, retaining 91 reference
> findings and the partial-publication block.

This is the recorded `APPROVAL`: it is the Equipment batch's `rule` and ends every new resolution's
`authorization_reference`. The owner review's suggested response prints the same sentence with two spaces missing
("its161", "retaining91"). The recorded rule uses the Owner's actual statement, with spaces; the review's spelling
was not substituted.

**Owner files** (read-only, in the Codex prompt directory
`C:/Users/raven/.codex/visualizations/2026/09/21/01a0c27d-eef6-78f0-82cb-89e991b26cfe/`), rechecked before the writes:

| File | SHA-256 |
|---|---|
| `equipment-cited-targets-owner-review.md` | `248a8fc6f38e5e686357ec075a91a73c459022cbd2f88ecd769b04112da314e9` |
| `equipment-cited-targets-owner-manifest.json` | `32da2d9e87231c64d0006916e39a73bac611e3d45d2b38899dba87ab7ae9459d` |
| `equipment-cited-targets-recording.md` (this request) | `970f282aeebe59fed9d5fcf2d833d12af249c5d8578be71d5c5e9400ef8c6003` |

The recording request was written at 2026-09-28T21:41:35Z, before either step.

**Exact artifacts authorized** (all 9 manifest rows matched before the writes):

- PROPOSAL `.claude/review-notes/issue-5d-equipment-cited-targets-PROPOSAL.json`, SHA-256
  `13271e035f76316a6f78cf90ccca1f68ec233738ce31a93c7303052bc5bb02e0`, `proposal_identity`
  `309e4405a4dc630b477adac0e83e2bc86bae0e2e6f76550775e5dae2b1bc1680`.
- DRAFTS `issue-5d-equipment-cited-targets-resolutions-DRAFTS.json` (161 resolutions), SHA-256
  `bfbf5a7ac78fa96fd568148d26bd2690415a4add9196d8ca393ef7b4f0c139eb`.
- Starting oracle `srd-5-2-1-corpus-3fe24ff6-4e3.json` at the Animals recording, `4ad85dab…90ba`.
- The generator, REPLACEMENT, DELTA, review, candidate test and `authoring.py` rows, unchanged.

After the recording the manifest recheck (`.claude/_sp/eqr/manifest.log`) shows 8 of 9 rows matching. The one
mismatch is the oracle row, as expected: `4ad85dab` → `76a16103`.

## Recording

**Script:** `.claude/review-notes/issue-5d-equipment-cited-targets-ACCEPT.py` (new), SHA-256
`91e8aea1898af928333fd666ff2ede91469bf7d1f609de5ebdf060c100190507`. It records the reviewed native REPLACEMENT
composition with only the Equipment evidence parameterized: the rule is `APPROVAL` when the reviewer is the Owner.
The other 21 proposals are composed byte-identically, with their exact recorded rules, reviewers, times, resolutions
and evidence, taken from the prior.

**No supersession.** The acceptance module has no supersession, so the changed Equipment batch is recorded as REPLACEMENT
composes it: a fresh 22-batch chain over no prior. There was no prior-proposal regeneration, reauthoring,
generalized carry-forward or source/release rewrite.

**Prior:** the 22 batches, rebuilt natively through `issue-5d-animals-ACCEPT.py` `recorded()` and checked against
its pinned bytes (`4ad85dab…90ba`). The prior is never read from the file being overwritten.

**Precheck** (`--simulate`, `.claude/_sp/eqr/simulate.log`, exit 0, 93 s): step 1 under the simulated reviewer is
byte-identical to `REPLACEMENT.replayed(prior)`, the reviewed composition. The simulated final bytes are
`26e23480…1eff`, as in the reviewed round.

**Steps** (real UTC execution times; each step reloads to the same bytes):

| Step | Command | Time (UTC) | Bytes (SHA-256) | Counts (batches, records, spans, units, resolutions) |
|---|---|---|---|---|
| Prior | (rebuilt) | — | `4ad85dab…90ba` | (22, 1759, 10424, 1459, 1247) |
| 1 | `record-equipment` | 2026-09-28T21:51:03Z | `a820243f7dd0e0d34cdad35dcfbc761ccf2e88eb82625b02a86d0848c1151fde` | (22, 1826, 10484, 1459, 1247) |
| 2 | `resolve-equipment-cited` | 2026-09-28T21:52:52Z | `76a16103a08db564ee00b9c8d493d2f5dd48b05e312c77780dd3a74639da86ac` | (22, 1826, 10484, 1459, 1408) |

Logs: `.claude/_sp/eqr/record.log` (exit 0, 142 s) and `.claude/_sp/eqr/resolve.log` (exit 0, 94 s). The times and
both SHAs are pinned in the ACCEPT (`RECORDED_AT`, `RECORDED_SHA256`).

**Non-monotonic chain times, by design.** The Equipment batch keeps its chain position, so its new time
(21:51:03Z) sits between batches whose recorded times are earlier. Monsters and Animals were recorded at 09:4xZ and
17:28Z. The reused batches keep their original times; none was re-stamped.

**Final oracle:** `76a16103…86ac`. It holds 22 batches, 1826 records, 10484 spans, 1459 review units and 1408
resolutions; 0 resolution violations; 91 reference findings, 29 uncovered leaves, 0 other findings.

### Preservation

Checked by the ACCEPT for both steps and again by `--verify` and the moved tests:

- **Outside Equipment, evidence included:** every `REPL.COLLECTIONS` path compared as a raw multiset of its
  non-Equipment items, plus `Delta.kept_outside_equipment` and equal Equipment accepted-text coverage. 0 differences.
- **Nothing recorded twice:** the non-Equipment acceptances and review-unit acceptances keep their prior counts, and
  the prior's 1247 resolution acceptances are all present unchanged beside the 161 new ones.
- **Approvals:** the Equipment batch's rule is `APPROVAL`. Every new span and review-unit acceptance names the Owner.
  Each of the 161 new resolutions names the Owner as reviewer and authorizer, with `AUTHORIZATION_REFERENCE`, which
  names the Owner-review and manifest SHAs, the PROPOSAL SHA and identity, the DRAFTS SHA and the prior oracle SHA.
- **Semantic evidence reused, not re-derived:** the source, the full 70793 characters, the direct/section consumer
  reads, Net, Wand ownership and anchors, the 18 candidate tests and the 20 byte-reproduction tests, and `src` mypy
  (235 files). All of these came from the reviewed round against the same PROPOSAL/DRAFTS bytes. None changed and none
  was rerun.

### Replay

- `--verify` (`.claude/_sp/eqr/verify.log`): exit 0, 69 s. State `resolved`, the pinned bytes and times, all new
  acceptances name the Owner and this decision, counts and findings as above, outside Equipment kept, reloads to the
  same bytes.
- Independent replay: `recorded()` rebuilt from `RECORDED_AT` and serialized (`.claude/_sp/eqr/rebuild.log`): exit
  0, `76a16103…86ac`, equal to the file.
- **Now fail closed (expected, not edited):**
  - `issue-5d-equipment-cited-targets-REPLACEMENT.py` `main()`/`recorded()` assert the disk file is the Animals bytes;
  - `issue-5d-animals-ACCEPT.py --verify` exits 1 with `AssertionError: resolved artifact drifted`
    (`.claude/_sp/eqr/verify-animals.log`);
  - `issue-5d-monsters-corrections-ACCEPT.py --verify` exits 1, refusing the file's batch set as
    `unrecognized batches [...]` (`.claude/_sp/eqr/verify-monsters-corrections.log`).

  Their in-memory rebuilds still hold. The new ACCEPT and the moved tests rebuild the prior through them.

## Dependency moves

Invalidation was identified first by grep and by batch order. Only states that hold the replaced Equipment batch
stop being kept whole by the file: Equipment and every batch after it, plus Monsters and Animals. The 12 batches
before Equipment are unaffected. The candidate test and its `persisted` fixture do not read the file and were not
touched (they are manifest-pinned).

**Pattern.** Each "kept whole in the committed file" check now reads "kept whole in the Animals recording", rebuilt
in memory at its recorded bytes. The file keeps that recording outside Equipment, which is asserted once in the
Animals and Monsters tests. Disk byte checks and production-resolver checks stay on the file. Historical assertions
about the replaced batch, including its old times, approval and counts, stay as they were, against the rebuilt
recording.

| File | Change |
|---|---|
| `tests/ingestion/mechanical/_replacement_chain.py` | Loads the new ACCEPT as `EQUIPMENT_CITED`. `COMMITTED_SHA256` is now its `resolved` pin. Adds the cached `animals_recorded()` (the ACCEPT's pinned `prior()`). |
| `test_animals_proposal.py` | The Animals committed test checks the rebuilt Animals recording (its pin, its 22/1759/10424/1459/1247 and 252/29) and that the file keeps it outside Equipment. New `test_the_committed_oracle_records_the_equipment_replacement`: file == `COMMITTED_SHA256` == ACCEPT replay, outside Equipment kept, approvals, identity and rule, recorded times, 22/1826/10484/1459/1408, 0 violations, findings 91/29. |
| `test_monsters_proposal.py` | The Monsters recording is kept whole in the Animals recording; the file keeps that outside Equipment. |
| `test_equipment_acceptance.py`, `test_spellcasting_acceptance.py` | `COMMITTED` is the Animals recording (its historical Equipment/Spellcasting times). The disk byte check stays on the resolver's file. The in-body comments now name the Animals recording. |
| `test_spellcasting_proposal.py`, `test_rules_glossary_completion_proposal.py` (fixture and committed test), `test_classes_proposal.py`, `test_spell_descriptions_proposal.py`, `test_gameplay_toolbox_proposal.py`, `test_magic_items_proposal.py` | `kept_whole`/`_preserved` target the Animals recording instead of the file. The now-unused `ORACLE` constant was removed from `test_spellcasting_proposal.py`. |
| `test_source_release_readiness.py` | Pins 10484 spans and 1408 resolutions; docstring names the Equipment replacement. |
| `test_committed_accepted_authority.py` | The named-identity set drops the replaced regenerated Equipment identity (`f97f2449…154c`), both from the `BATCHES` expansion and from the explicit `EQUIPMENT_PROPOSAL` listing (constant removed), and adds `309e4405…1680`. |
| `src/afterworlds/ingestion/mechanical/oracles/README.md` | "Current" section: 1826 records, 1408 resolutions, `76a16103…`, 91 findings, and the Equipment replacement recording. |

No `src/` Python changed.

## Tracked cross-file release-order defects (Owner decision, carried forward)

Under `release-order-owner-decision.md`, finish the packets, track the known cross-file defects, then make one bounded
order correction before publication or activation. There is no reorder now, and content acceptance does not certify
the current order.

| # | Defect | Status |
|---|---|---|
| RO-1 | `CORPUS_FILES` is largely alphabetical: Animals precedes its governing Monsters rules. | Deferred to the one release-order pass. |
| RO-2 | The remaining chapter order beyond Monsters rules/A–Z is unverified against the official order. | Same pass. |

This run made no source review and found no within-rule, table or statblock order defect.

## Secrets baseline

This was a scoped update from the starting bytes only (`START` `2bab5a74…ad4f`). It used a private-settings scan
under the baseline's own plugins and filters. `detect-secrets scan --baseline` was never run, and no
`pragma: allowlist secret` was added. Settings, filters, version, `generated_at`, untouched files' entries, key order
and `is_verified` flags were asserted preserved before writing; added entries have `is_verified: false`; LF.

- **Before:** `2bab5a74…ad4f` (123 files, 5555 entries).
- **After:** `3a542f99…c0cd` (124 files, 5562 entries): 9 added, 2 pruned, 987 line numbers refreshed.
- **Staged:** `.secrets.baseline`, by name.

| File | Added | Moved | Pruned |
|---|---|---|---|
| `src/…/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json` | 2 | 981 | 2 |
| `.claude/review-notes/issue-5d-equipment-cited-targets-ACCEPT.py` (new file) | 7 | 0 | 0 |
| `tests/ingestion/mechanical/test_animals_proposal.py` | 0 | 3 | 0 |
| `tests/ingestion/mechanical/test_monsters_proposal.py` | 0 | 3 | 0 |
| The other 13 scanned files (hub, other moved tests, README, this doc) | 0 | 0 | 0 |

**Pruned (2):** the replaced Equipment batch's oracle `proposal_identity` (`f97f2449…`) and `semantic_diff_hash`
(`a474c87e…`). Each was matched by SHA-1 against the rebuilt prior's Equipment batch.

**Added (9)**, each recovered from its line, checked against its SHA-1 and verified as a named public value
(`.claude/_sp/eqr/bl/verify.json`, 0 unverified of 9):

- oracle `proposal_identity`, recomputed from the PROPOSAL, and oracle `semantic_diff_hash`, the `batch_diff_hash`
  of the recorded Equipment batch (equal to the stored field);
- ACCEPT: the PROPOSAL SHA-256, identity and DRAFTS SHA-256; both Owner-file SHA-256s; the rebuilt
  `equipment-recorded` bytes and the recorded oracle bytes.

**Rescan:** 0 new, 0 obsolete in all 17 files (`rescan.json`). The machine-readable delta is
`.claude/_sp/eqr/bl/baseline-delta.json`.

**Hook.** `detect-secrets-hook --baseline .secrets.baseline` on the final bytes of all 17 files
(`.claude/_sp/eqr/bl/files.txt`), PowerShell via `rtk proxy`: after staging, run twice before this line was filled and twice on the final bytes, every run exit 0; `.secrets.baseline` stayed byte-identical at `3a542f99…c0cd` and `git diff --quiet -- .secrets.baseline` exited 0 (nothing unstaged).

## Gates (raw)

This is not an all-green claim.

PowerShell, repo root, explicit venv via `rtk proxy`:

| Gate | Command | Result |
|---|---|---|
| Simulate | `python .claude/review-notes/issue-5d-equipment-cited-targets-ACCEPT.py --simulate` | exit 0 (93 s) |
| Record step 1 | `… ACCEPT.py record-equipment` | exit 0 (142 s); `a820243f…1fde` |
| Record step 2 | `… ACCEPT.py resolve-equipment-cited` | exit 0 (94 s); `76a16103…86ac` |
| Verify | `… ACCEPT.py --verify` | exit 0 (69 s) |
| Independent replay | `recorded()` rebuilt and hashed | exit 0; `76a16103…86ac` |
| Collect (selection) | `python -m pytest --collect-only -q <21 ids>` | exit 0; 21 collected (not empty) |
| Changed tests | `python -m pytest -q --no-cov -p no:randomly <21 ids in .claude/_sp/eqr/ids.txt>` | exit 1: 20 passed, 1 failed in 681.91 s. The failure was `test_no_refused_candidate_is_selectable`: the replaced Equipment identity was still listed explicitly. |
| Fixed test | `python -m pytest -q --no-cov -p no:randomly …test_committed_accepted_authority.py::test_no_refused_candidate_is_selectable` | exit 0; 1 passed in 10.32 s |
| Loader group + untouched seam | `python -m pytest -q -p no:cacheprovider test_character_origins_feats_acceptance.py::test_the_recorded_bytes_are_what_the_two_seams_record test_committed_accepted_authority.py test_accepted_inputs.py test_oracle.py test_packaging.py tests/test_quarantine_5c_5d.py` (`.claude/_sp/eqr/pytest-loaders.log`) | 196 passed in 257.73 s; exit 1 only from the repository-wide 80% coverage floor on a partial selection (40.77%), no test failure |
| Invalidation grep (whole `tests/`) | `grep -rlE "COMMITTED_ORACLE_DIR\|3fe24ff6\|load_accepted_inputs\(" tests/` | one hit outside `mechanical/`: `tests/test_quarantine_5c_5d.py`, which reads only the quarantined `36b786d8` file; unaffected, run above |
| Black | `python -m black <13 changed .py>` | exit 0, unchanged |
| Ruff | `python -m ruff check <13 changed .py>` (import order fixed by `--select I --fix`) | exit 0 |
| Manifest recheck | 9 rows | 8 match; the oracle row is the expected mismatch |
| detect-secrets hook | see Secrets baseline | see Secrets baseline |
| mypy (`src/`) | not run: no `src/` Python changed (README only); 235 files passed in the reviewed round | — |
| Expanded mypy | deferred | non-green |
| pip-audit | deferred | non-green |
| Full suite | not run: only the invalidated tests were in scope | — |

The 21 selected tests are the changed test functions plus the two acceptance modules whose module-level state
changed. The earlier optional Task D selection that exited 5 with no matches is not counted as passing anywhere here.

## Retention (current purpose only)

Nothing was deleted.

- **The new ACCEPT**, the PROPOSAL/DRAFTS, generator, REPLACEMENT, DELTA, review and candidate test: replay and
  review evidence for the recorded batch. `--verify` and the live tests read them.
- **`issue-5d-animals-ACCEPT.py`** and **`issue-5d-monsters-corrections-ACCEPT.py`**: the prior's authority, rebuilt
  in memory by the new ACCEPT and the tests.
- **`.claude/_rc/msc/rel/afterworlds.db`** (`SCRATCH_DB`, untracked): retained while the ACCEPT's `--verify` and
  `--simulate` need `REPL._findings`. A fresh checkout without it cannot run those two modes; the live tests use
  their own fixtures.
- **`.claude/_sp/eqr/`** (scratch, never committed): the step logs, pin script, test ids and logs, manifest recheck
  and `bl/` baseline work. Kept while Codex verifies. The pre-recording snapshots from the reviewed rounds
  (`.claude/_sp/eqc/`) stay for the same reason.
- **Untouched:** quarantined `srd-5-2-1-corpus-36b786d8-fa2.json`; protected
  `issue-5d-source-correction-REPLACEMENT-PACKET.md`; the 574662e9 oracle; root `afterworlds.db`; the 4 stashes; the
  pre-existing staged deletions and unrelated changes.

## Blockers and deferrals

- **Partial publication:** blocked. There are 91 reference findings and 29 uncovered leaves, and the release-order
  pass (RO-1, RO-2) is still pending.
- **Spellbook:** stays unresolved (Owner decision).
- **Deferred, non-green:** pip-audit and expanded mypy.
- **Separate follow-ups, not expanded here:** other mapping, shared coverage, broad review, the remaining 5d
  packets, and the one bounded release-order correction.
- **Source errors:** official SRD errata first, then the official resource, then notify the Owner. No silent source
  correction.
- **Codex:** independently verifies before the remaining 5d work continues.

## Process disclosures

- **Nothing committed.** Nothing was committed, pushed, merged, published or activated. There was no shared DB and no
  Chroma write. The only change staged is `.secrets.baseline`, by name.
- **Denials:** none. In the preceding Task D, one Bash call hit a transient classifier timeout and was retried once,
  as the harness allows.
- **Connectors.** Context7, Expedia, Google Calendar, Intuit TurboTax and Shopify need authorization in claude.ai
  connector settings. They were not used.

## Sources

- https://www.dndbeyond.com/srd
- https://media.dndbeyond.com/compendium-images/errata/MM-25/MM-2025_v1.pdf
- https://www.dndbeyond.com/sources/dnd/sae/monster-manual
- https://www.dndbeyond.com/posts/1950-sage-advice-and-errata-for-the-new-core-rules-is
