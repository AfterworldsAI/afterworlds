# CRD Issue 5d — rules-glossary-completion — recorded follow-up

Status: **recorded, verified, and the dependent state is reconciled.**

- This run newly staged only `.secrets.baseline`. The pre-existing staged deletions remain staged and
  untouched.
- Nothing is committed, pushed, merged, published or activated.
- There are no shared-DB or Chroma writes.
- The coordinating Codex reviews this independently.

## Authority

- **Acceptance.** The Owner accepted "this exact proposal, retaining 66 reference findings", in answer to
  `rules-glossary-owner-review.md` (SHA-256 `c62cd253…1d83`). There are no new resolutions.
- **Verification.** The Owner later authorized the read-only `--verify` and the hash/size inspection that
  had been denied, through normal permission checks. Both ran with no new denial.
- **Scope of this run.** `accept` was not re-run. The recorded approval and timestamp were not altered.

## Recording (from the previous run, unchanged)

`accept` printed `accept srd-5-2-1-corpus-626c83f8-209.json 962d6aee…18b8` / `verified accepted`
(raw log `.claude/_sp/glrec/accept.log`).

## Native verification

Command: `rtk proxy venv\Scripts\python.exe .claude/review-notes/issue-5d-rules-glossary-completion-ACCEPT.py --verify`
Raw logs: `.claude/_sp/glrec/verify.log` and `verify-rules-glossary-completion.log`.

```
State accepted 962d6aee13022984ca47e012d8041633b4b2fad5de5aac1112806f6fc5b218b8
verified
  batches 15
  records 295
  spans 1613 review units 229
  resolutions 50
  resolution violations 0
  prior preserved (235 records, 50 resolutions, 14 batches) True
  accepted_at 2026-09-26T08:50:19Z
  reference findings 66 leaf/uncovered 8831
```

| Check | Result |
|---|---|
| State | `accepted` |
| Oracle SHA-256 | `962d6aee13022984ca47e012d8041633b4b2fad5de5aac1112806f6fc5b218b8` |
| Oracle size | 4,061,122 bytes, 0 CR |
| Real UTC acceptance time (`accepted_at`, read back) | `2026-09-26T08:50:19Z` |
| Batches / records / spans / units / resolutions | 15 / 295 / 1613 / 229 / 50 |
| Resolution violations | 0 |
| Prior (14 batches, 235 records, 50 resolutions, `c5971b89…572f`) | preserved |
| Reference findings / uncovered leaves | 66 / 8831 |

The glossary helper is unchanged at `16ad411a…2c4c`. The before snapshot is at
`.claude/_sp/glrec/oracle-before.json`.

## Settled dependency updates

These follow the handoff table for the fifteen-batch state. No assertion was weakened.

The earlier note recorded the Equipment and REPLACEMENT before-pins only in abbreviated form, and no full
copy was kept, so those rows show the prefix.

| File | Before SHA-256 | After SHA-256 |
|---|---|---|
| Glossary helper | `16ad411a396687060b26dbc4c651dd0cb88003819690303bb27cd6c06ee72c4c` | unchanged |
| Glossary proposal | `b31621c0bf97834dad28e136ad6516687d63010cf675ab87226d1527787658bd` | unchanged |
| Spellcasting helper | `2bed9d9bf1e8606911ba21d6aacef8a1ce8eb7da37518f2fcb6177b939ac22f6` | `98a73fcd3a25258085faf6b7afad8e47f48408c56acc29796415aea0672322ae` |
| Equipment helper | `458dcee7…c312` | `6ac3dd918cc95b52aba539161ac53e57ce41b95f5075eecf24d8c820b0cee7f1` |
| REPLACEMENT helper | `791ef715…1044` | `848418c0ddf3da2070915780186bc14e969af2a1fa6939bfce9f258959fb4860` |
| `oracles/README.md` | `d6a860af38cf6478125471eebb7b062800ccab4a7638fcc8e07113b97298ffcf` (`README-before.md`) | `128a176f6779a9c5dfe32e4f255c662228ceaf2df60059aae5da5ef60bb47936` |

**Helpers**
- **Spellcasting helper** (`98a73fcd…22ae`): `_state` now returns `appended` once more than 14 batches are
  present. In that case it:
  - delegates to `glossary.prior()` / `glossary._state()`;
  - asserts `accepted` and `_check_preserved`;
  - points `--verify` at the glossary script.
- **Equipment helper** (`6ac3dd91…e7f1`): the pointer and comment now name the glossary script.
- **REPLACEMENT helper** (`848418c0…4860`): the `verify()` docstring and its current-artifact pointer now
  name the glossary script.

**Tests**
- `test_spellcasting_acceptance.py` replays both Spellcasting steps over the native prior. It checks:
  - the result equals `GL.PRIOR_SHA256`;
  - `GL._state` returns `accepted` with the prior preserved;
  - `SC._state` returns `appended`;
  - the times read back from both the replay and the committed file.
- `test_equipment_acceptance.py` and `test_spellcasting_proposal.py` now expect `appended`.
- `test_rules_glossary_completion_proposal.py`:
  - the prior is rebuilt natively, equals `ORACLE_SHA256 == GL.PRIOR_SHA256`, and is preserved in the
    committed file.
  - A new test, `test_the_committed_oracle_records_the_owner_acceptance`, replays at the recorded time to
    the committed bytes and checks identity, rule, scope, reviewer, time, counts, resolutions (as a set,
    because the loaded file is in canonical order), 0 violations and 66/8831.
- `test_committed_accepted_authority.py`: the glossary proposal identity is added to the named-candidate
  set in `test_no_refused_candidate_is_selectable`.

**Docs**
- `oracles/README.md` (`128a176f…7936`) now covers:
  - fifteen batches;
  - the glossary script as the whole-file verifier;
  - a new rules-glossary-completion bullet;
  - 66 remaining references, including the eight part-level pointers the batch keeps;
  - 8 831 uncovered leaves.
- The diff is in `.claude/_sp/glrec/README.diff`. No test pins the README.

## Gates

All runs used `rtk proxy venv\Scripts\python.exe …`, with pytest `-p no:cacheprovider --no-cov`. Raw logs
are in `.claude/_sp/glrec/`.

| Gate | Result |
|---|---|
| `test_rules_glossary_completion_proposal.py` | 34 passed |
| `test_spellcasting_acceptance.py` | 5 passed |
| `test_equipment_acceptance.py` | 5 passed |
| `test_spellcasting_proposal.py` | 39 passed |
| Committed-oracle loaders: `test_committed_accepted_authority`, `test_accepted_inputs`, `test_oracle`, `test_packaging`, `test_character_origins_feats_acceptance` | 163 passed |
| Helper `--verify`: glossary | accepted |
| Helper `--verify`: Spellcasting | appended; 15-batch current, 0 violations, prior 216/49/13 preserved, times read back |
| Helper `--verify`: Equipment | appended |
| Helper `--verify`: REPLACEMENT | twelve-batch prefix `7b1d6f43…`, current pointer → glossary |
| Black and Ruff on every changed `.py` file | clean |
| CR check on every changed file | 0 |

Two failures surfaced during the run and were settled:
- **Resolution order.** One test first compared resolutions by position. It now compares them as a set.
- **Missing pin.** `test_committed_accepted_authority` first failed on the unpinned glossary identity. The
  identity is now pinned.

Unchanged broad suites were not re-run, per scope, and mypy did not apply because no `src/` Python
changed.

## Secrets baseline reconciliation

The scan used the baseline's own `plugins_used` / `filters_used` via `transient_settings`, over a private
copy that was deleted afterwards. It never ran `detect-secrets scan --baseline`, and there were no
exclusions or pragmas.

Files in `.claude/_sp/glrec/`:
- `baseline-before.json` (exact bytes, `4554f802…efb2f`)
- `baseline-after.json`
- `baseline-delta.json` (machine-readable)
- `scan-before.{log,json}`
- `scan-after.{log,json}`
- `bl_verify.{log,json}`
- `bl_apply.log`

| | Before | After |
|---|---|---|
| SHA-256 | `4554f802f2d69a8dd870ff53c15aaa018b0f12337d361bd57d246dd6e69efb2f` | `a94b6f4f4656455cd0619b2ae15765eb3fff57eb3c4e2788bfee5322398a35bb` |
| Size | 486,684 bytes (CRLF, last written in text mode) | 479,896 bytes (LF, which is the `eol=lf` attribute and the index form) |
| Files / entries | 63 / 1551 | 66 / 1565 |

**Delta: 14 added, 131 lines refreshed, 0 pruned.** A before-scan found 0 obsolete entries, so nothing
was pruned.

- **Oracle:** 127 lines refreshed, plus 2 new entries:
  - `proposal_identity 6cafaf57` at line 12350;
  - `semantic_diff_hash 7b522be5…` at line 12470.
- **Spellcasting helper:** 4 lines refreshed.
- **New files:**
  - Glossary proposal JSON: 6 release-binding / schema / policy hashes, already baselined elsewhere.
  - Glossary ACCEPT: prior SHA `c5971b89`, proposal file SHA `b31621c0`, identity `6cafaf57`, Owner-review
    SHA `c62cd253`.
  - Glossary test: identity and prior SHA.

Each of the 14 was checked against its actual source value as a public identifier (`bl_verify.log`: all
14 True). That matches the forecast of 12 existing + 2 oracle findings.

**Preserved (asserted before writing):**
- `version`, `plugins_used`, `filters_used` and `generated_at` are unchanged.
- Every untouched file's entries are identical.
- The existing key order is kept, and the new files are appended.
- Every `is_verified` flag is kept; new entries are `false`.

**After-scan:** every candidate file has 0 new, 0 obsolete and 0 moved entries.

**Staged hook.** `git add .secrets.baseline` was the only file this run staged; the pre-existing staged
deletions were already there. pre-commit is not installed in the
venv (`No module named pre_commit`), and installing it was out of scope under "no dependency changes".
The substitution is deliberate: the hook the config runs was invoked directly as
`venv\Scripts\detect-secrets-hook.exe --baseline .secrets.baseline`. `detect-secrets --version` reports
`1.5.0`, which is the `rev: v1.5.0` the pre-commit config pins. It ran on:
- the staged ACMR set (`.secrets.baseline`);
- the 18 candidate files plus the baseline.

It ran twice on each set. All four runs exited 0, and the baseline stayed at `a94b6f4f…35bb` with index ==
worktree (`M  .secrets.baseline`).

The evidence is the raw command stream, which printed `staged run 1 exit=0`, `candidate run 1 (19 files)
exit=0`, the hash, `staged run 2 exit=0`, `candidate run 2 (19 files) exit=0` and the same hash. The hook
prints nothing on success, and an empty pipeline does not rewrite a `Tee-Object` target. So:
- `hook-staged-{1,2}.log` are stale: they still hold the earlier `No module named pre_commit` attempt;
- `hook-candidates-{1,2}.log` were never created.

Neither set of log files is evidence of these runs.

**Disclosure.** The staged blob differs from HEAD by more than this run's delta.
- **Observed:** the working copy at the expected `4554f802…` already differed from HEAD (`fe5d5fe`) by
  +422 / −397 / 13 moved entries. The coordinator has since confirmed this is known, already-authorized
  maintenance, not a new Owner decision.
- **Not captured:** the index blob before `git add`, so this run has no evidence of whether the index
  equalled HEAD before staging.
- **This run's change:** only the before→after delta above. `.claude/_sp/glrec/baseline-HEAD.json`
is kept for comparison.

## Handoffs and untouched items

- `issue-5d-rules-glossary-completion-accepted-recording-handoff.md` is kept, because its live use is Codex's
  comparison of the scanner forecast. It becomes a retirement candidate once Codex has reviewed. No other
  handoff was retired in this run.
- `issue-5d-source-correction-REPLACEMENT-PACKET.md` is untouched (`e462e235…cae1`).
- Also untouched:
  - the quarantined oracle;
  - the staged deletions;
  - the unrelated ` M` files;
  - the 4 stashes.

## Blockers and retained limits

- The 66 reference findings and the partial-publication block are retained.
- pip-audit (31 findings in 11 packages) remains deferred and not green.
- After 5d:
  - the broad accepted-material review;
  - the Casting Spells follow-up;
  - the shared-coverage follow-up.
- There is no new batch, commit or push. Codex review is the next step.
