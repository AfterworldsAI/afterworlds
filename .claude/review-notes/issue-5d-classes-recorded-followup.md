# CRD Issue 5d — Classes packet — recorded follow-up

Status: **recorded, verified natively, dependent state reconciled.**

- The Owner-approved Classes packet (`classes` and `class-option-catalogues` batches plus one reference
  resolution) is recorded in the committed oracle through the existing native contracts.
- This run newly staged only `.secrets.baseline`. The 36 pre-existing staged deletions remain staged and
  untouched.
- Nothing is committed, pushed, merged, published or activated. There are no shared-DB or Chroma writes.
- Partial publication/activation remains blocked.
- The coordinating Codex reviews this independently.

## Authority

- **Owner approval (verbatim):** "I accept the exact Classes proposals and approve the one reference
  resolution, retaining 1,153 reference findings."
- **Answers:** `classes-owner-review.md` in
  `C:/Users/raven/.codex/visualizations/2026/09/21/01a0c27d-eef6-78f0-82cb-89e991b26cfe`
  (read only), SHA-256 `d75e915cd75e2f5c1c62b7f96ea9ef8caafd83ecccac75bf7691d716ba0f6d3c`.
- **Decision item.** The helper's `DECISION_ITEM` quotes the review's "Decision requested" items 1 and 2
  and its retention sentence, without bold markup. It was checked verbatim against the source.
- `AUTHORIZATION_REFERENCE` = `"Owner decision on classes-owner-review.md: " + repr(RULE) + ", answering "
  + repr(DECISION_ITEM)`.
- The reviewer is `Ravenlok (Owner)`. Times are the real execution UTC of each write. No simulation
  reviewer, authority or date was copied. `taskdir/classes-native-review.py` was treated as simulation
  evidence only.

Approved inputs (pins verified before any write):

| File | SHA-256 | Identity |
|---|---|---|
| `issue-5d-classes-PROPOSAL.json` | `08c8c91d65e69ba909cc5771aa26352e60d2019363790c21394ee1ddf4002ba7` | `025016704fbca10a7673e0040309a772d56780da434013588cd34fcafd4ffc87` |
| `issue-5d-class-option-catalogues-PROPOSAL.json` | `7172ae1ab2986a5617722f69dcf0781ddcb0286a86b663f75118e504f913cf82` | `3dae09105c4f2e30f0c1c902fef76155974f61320f8283904c2ef241072a3293` |
| `issue-5d-classes-resolutions-DRAFTS.json` | `516e141fd5c66a1146d09fbf4f0c8e8e70859c36e15b42b1c8000ecabcebf63c` | — |

The one resolution: `resolve-character-origins-elf-elven-lineage-wizard-spell-list-classes-1`, i.e.
`character_origins.elf` / `elven_lineage` "Wizard spell list" → `classes.wizard`. The proposal and draft
bytes were not mutated.

## Recording

Helper: `.claude/review-notes/issue-5d-classes-ACCEPT.py` (new). It:
- rebuilds the fifteen-batch prior natively (`GLOSSARY.accepted(GLOSSARY.prior(), …, 08:50:19Z)`) and
  asserts it equals the pinned prior bytes;
- recognizes exactly four states (`prior`, `accepted`, `options-accepted`, `resolved`) by native replay
  and byte equality, failing closed (`SystemExit`) on anything else;
- continues from a recognized intermediate by replaying it at its read-back time;
- re-verifies the state after each write.

Prior oracle: `962d6aee13022984ca47e012d8041633b4b2fad5de5aac1112806f6fc5b218b8` (295 records, 1613
spans, 229 units, 15 batches, 50 resolutions). `--verify` before writing: `state prior`.

| Step | Native call | Recorded UTC | Oracle SHA-256 after | Log |
|---|---|---|---|---|
| `accept` | `accept_proposal` (classes) | `2026-09-26T21:34:59Z` | `e9a63b14…f306` | `verified accepted` |
| `accept-options` | `accept_proposal` (class-option-catalogues) | `2026-09-26T21:35:14Z` | `41f1dc80…ec7e` | `verified options-accepted` |
| `resolve` | `resolve_references` (1 draft) | `2026-09-26T21:35:31Z` | `a3b81a03…a1e7` | `verified resolved` |

Final oracle: `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-626c83f8-209.json`,
SHA-256 `a3b81a03c41abf8495634f5118841db2b1f6cfb1759f06a5b88be05d3edaa1e7`, 8,195,194 bytes, 0 CR.
Snapshots of each state and raw step logs are in `.claude/_sp/clsrec/`.

The pre-write in-memory simulation (`simulate.log`) produced the same counts and findings. Its bytes
(`1b862ee6…73ac`) differ only by the simulation reviewer and time.

## Native verification

`rtk proxy venv\Scripts\python.exe .claude/review-notes/issue-5d-classes-ACCEPT.py --verify`
(`verify-final.log`):

```
state resolved a3b81a03c41abf8495634f5118841db2b1f6cfb1759f06a5b88be05d3edaa1e7
verified
  batches 17 last class-option-catalogues
  records 603
  spans 2776 review units 305
  resolutions 51
  resolution violations 0
  prior preserved (295 records, 50 resolutions, 15 batches) True
  counts (17, 603, 2776, 305, 51)
  times (classes, options, resolved) ('2026-09-26T21:34:59Z', '2026-09-26T21:35:14Z', '2026-09-26T21:35:31Z')
  reference findings 1153 leaf/uncovered 7657
  other findings 0 []
```

- Serialization/reload: the replay serializes to the committed bytes, and the production resolver
  (`committed_inputs_for`) reloads them to the same bytes.
- Prior preservation: `EQUIPMENT._check_preserved(prior, result)` holds in the replay. A loaded file holds
  its batches in canonical order, so the prefix is checked there. The prior approvals were not restamped.
- The earlier helpers' `--verify` all report `appended` and check only their own prefix:
  - glossary: fifteen-batch prefix equal to `PRIOR_SHA256`, 66/8831, `accepted_at 2026-09-26T08:50:19Z`;
  - Spellcasting: times `2026-09-25T18:05:59Z` / `2026-09-25T18:06:11Z` read back;
  - Equipment: thirteen-batch prefix;
  - REPLACEMENT: twelve-batch prefix `7b1d6f43…abdd8` (`verify-replacement.log`, exit 0).
- The REPLACEMENT, Equipment and Spellcasting pointers still name the glossary script, whose `--verify`
  now points onward to the Classes script. The chain reaches the current file in one more hop; the
  pointers were left as they are to keep this run's edits minimal.

| | Prior | Classes | Class-option-catalogues | Final |
|---|---|---|---|---|
| Batches | 15 | +1 | +1 | 17 |
| Records | 295 | +268 | +40 | 603 |
| Spans | 1613 | +1028 | +135 | 2776 |
| Review units | 229 | +36 | +40 | 305 |
| Resolutions | 50 | | +1 (resolve step) | 51 |

## Findings

- **1,153 reference findings**, matching the Owner's retained count:
  - 65 from the earlier batches (the previous 66, less the Elf's "Wizard spell list", now resolved);
  - 1,088 unresolved pointers the Classes packet keeps: 1,026 spells, 44 equipment items / "(see
    Equipment)", 9 monsters, 5 animals, 3 class-list phrases and 1 "Playing the Game".
- **7,657 uncovered leaves.**
- **0 other findings.** Resolution violations: 0.
- None of the findings was given a guessed destination.

## Settled dependency updates

No assertion was weakened, and the prior-prefix reconstruction and identity assertions are kept.

| File | Change | After SHA-256 |
|---|---|---|
| `issue-5d-classes-ACCEPT.py` | new recording helper | `21be69c0…4ef7` |
| `issue-5d-rules-glossary-completion-ACCEPT.py` | `_state` returns `appended` once the Classes replay recognizes the file; `--verify` then checks the fifteen-batch prefix against `classes.PRIOR_SHA256` and points to the Classes script | `1c57fdc6…ea63` |
| `issue-5d-spellcasting-ACCEPT.py` | appended branch accepts the glossary's `appended`; `_read_back` scoped to its own draft ids (see the audit below) | `88018854…b354` |
| `test_classes_proposal.py` | prior rebuilt natively (`CLS.prior()`), equal to `ORACLE_SHA256 == CLS.PRIOR_SHA256`, preserved in the replay; new `test_the_committed_oracle_records_the_owner_acceptance` (replay == file, read-back times, rule, identities, scope, reviewer, the one new resolution and its authorization, counts, 0 violations, 1153/7657) | `8af341f3…5ad2` |
| `test_rules_glossary_completion_proposal.py` | expects `appended`; the replay equals `classes.PRIOR_SHA256` and is preserved in the Classes replay | `f8c19556…5748` |
| `test_spellcasting_acceptance.py` | `GL._state(FINAL)` expects `appended` | `2f9b7335…bbf0` |
| `test_committed_accepted_authority.py` | both Classes identities added to the named-candidate set | `85d05c2e…88a1` |
| `oracles/README.md` | seventeen batches, fifty-one resolutions, the Classes script as whole-file verifier, a Classes bullet with its times, the Elf resolution, 1,153 references and 7 657 uncovered leaves | `d176e73b…fb93` |

The listed after-SHAs are whole-file hashes, not this run's diff. Several tests, notably
`test_committed_accepted_authority.py`, also carry pre-existing uncommitted restart edits; this run
changed only what the table describes.

The Equipment and REPLACEMENT helpers did not need changes. Other readers of the oracle hash its bytes or
are quarantine tests, and are unaffected.

**Sibling audit — read-back defect family.** Trigger: the Spellcasting `--verify` first failed with
`AssertionError: spellcasting resolved_at: [...18:06:11Z, ...21:35:31Z]`, because its `_read_back` took the
Classes resolution time as its own.

| Structure | Disposition |
|---|---|
| Spellcasting `_read_back` | patched: scoped to its own draft ids |
| Classes `_read_back` | patched: scoped to `RESOLUTION_ID` |
| Glossary `_accepted_at` | already safe: filters by `batch_id` |
| Equipment `_read_back` | already safe: `_state` returns `appended` before it is reached; its test uses an in-memory final |
| REPLACEMENT helper | already safe: has no `_read_back` |

Regression coverage: `test_spellcasting_acceptance.py` and the Classes owner-acceptance test both check
the read-back times against the committed file.

## Gates

All runs used `rtk proxy venv\Scripts\python.exe -m pytest … -q -p no:cacheprovider --no-cov`, attached.
Raw logs are in `.claude/_sp/clsrec/`.

| Gate | Result |
|---|---|
| `gate-1`: `test_classes_proposal.py`, `test_rules_glossary_completion_proposal.py` | 61 passed (518.82s) |
| `gate-2`: `test_spellcasting_acceptance.py`, `test_spellcasting_proposal.py`, `test_equipment_acceptance.py` | 49 passed (170.00s) |
| `gate-3`: `test_committed_accepted_authority`, `test_accepted_inputs`, `test_oracle`, `test_packaging`, `test_character_origins_feats_acceptance` | 163 passed (118.18s) |
| Helper `--verify`: Classes / glossary / Spellcasting / Equipment | resolved / appended / appended / appended |
| Black and Ruff on every changed `.py` file | clean |
| CR check on every changed file | 0 |

The gate logs hold only pytest's output; each summary shows no failures or errors. Exit 0 was observed
when they ran but is not written in the logs.

Unchanged broad suites were not re-run, per scope. mypy did not apply because no `src/` Python changed.

## Untouched items, blockers and retained limits

- `issue-5d-source-correction-REPLACEMENT-PACKET.md` is untouched (`e462e235…cae1`).
- Also untouched: the quarantined oracle, the staged deletions, the unrelated ` M` files and the 4 stashes.
- The 1,153 reference findings and the partial-publication/activation block are retained.
- pip-audit (31 findings in 11 packages) remains deferred and not green.
- After 5d: the broad accepted-material review, the Casting Spells follow-up and the shared-coverage
  follow-up.
- There was no new batch authoring, commit or push. There were no new permission denials.

## Secrets baseline reconciliation

The scan used the baseline's own `plugins_used` / `filters_used` via `transient_settings`, over a private
copy that was deleted afterwards. It never ran `detect-secrets scan --baseline`, and there were no
exclusions, pragmas or CI changes.

Files in `.claude/_sp/clsrec/`:
- `baseline-before.json` (exact prior bytes) and `baseline-after.json`;
- `baseline-delta.json` (machine-readable: added, line-refreshed, pruned, preservation checks);
- `scan-probe2.{log,json}` (before), `verify-probe2.{log,json}` (per-value verification) and
  `scan-after.{log,json}` and `scan-final.{log,json}` (after this note was completed);
- `bl_apply.log` and `hook.log`.

| | Before | After |
|---|---|---|
| SHA-256 | `d3751292e620e7d5f77fb256422eca75b2f919b87fdcb2a71be240746a5a8fd7` | `4b0bcdd0366c8f7fa2ebdde5b9f7c0e8352f0d0819a9fbf3905f18e186a8fe4e` |
| Size | 638,260 bytes, LF | 812,807 bytes, LF (0 CR) |
| Files / entries | 70 / 2161 | 71 / 2749 |

**Delta: 588 added, 154 lines refreshed, 0 pruned.** The before-scan found 0 obsolete entries.
- Oracle: 581 added, 147 refreshed.
- Classes helper (new file): 7 added.
- Glossary helper: 4 refreshed. `test_classes_proposal.py`: 3 refreshed.
- This follow-up, the README and the other tests: 0 findings.

Each of the 588 was recomputed from its source and checked as a public identifier (`verify-probe2.log`:
588/588 verified):
- 577 `fact_key` values, recomputed natively from the proposals and required to sit in a
  `"target_kind": "fact"` / `"target_key"` context;
- 4 proposal identities (two each), recomputed with `proposal_identity`;
- 2 `semantic_diff_hash` values, recomputed with `accounting.batch_diff_hash`;
- 5 file SHA-256s: both proposals, the drafts, the prior oracle and the Owner review.

Every value also had to match its baseline `hashed_secret` (SHA-1).

**Preserved (asserted before writing):** `version`, `plugins_used`, `filters_used` and `generated_at`
unchanged; every untouched file's entries identical; existing key order kept, with the new file appended;
every `is_verified` flag kept, and new entries `false`.

**After-scan:** every candidate file has 0 new, 0 obsolete and 0 moved entries.

**Staged hook.** Before staging, the index blob was the `d3751292…` version, equal to the
working copy and to `baseline-before.json`. `git add -- .secrets.baseline` was the only staging this run
did; the index now holds 36
pre-existing deletions and `M  .secrets.baseline`. `venv\Scripts\detect-secrets-hook.exe --baseline
.secrets.baseline` (v1.5.0, the config's pinned rev) ran twice on the staged ACMR set (`.secrets.baseline`)
and twice on the 10 candidate files plus the baseline. All four runs exited 0 with no output (exit codes
captured explicitly in `hook.log`). The baseline hash stayed `4b0bcdd0…fe4e` after each run, and the index
blob equals the worktree.
