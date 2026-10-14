# CRD Issue 15c — C8 recording baseline delta review

Verdict: **delta cleared; no blocking defect found**. Disposition: **already safe / no change**. This is evidence for the complete PR review, not an Owner milestone, full-gate result or merge/runtime authority.

Reviewed immutable recording commit `183a664e8645ecadd97c55517e8ba1120e9c5b19` against independently cleared `5c4d8d6e56c015862cb16f5e34d2229c985faf5a`. Reused the prior 284-entry C8 clearance in `codex-c8-baseline-review.md`; those entries were not reaudited. Governing issue, skills, current-task Library resolutions and whole-PR Owner workflow remain as recorded in that review. The independent source-recording review is separate evidence and was read for its exact artifact and producer context.

The baseline SHA-256 moves from `c22026f52d39b72530437b3ddf0e3429fe342f93060d2fcafb276d5d53b4dc0c` to `a8555f69c00b2500357be7e5a79c23eca5e6d174ec0fcdf89bc33e908efdb162`.

## Verified addition

The 351 added baseline text lines represent **49 exact `(filename, detector, hashed-value)` additions** across four committed recording files:

| File under `issue-15c-c8-recording/` | Entries |
| --- | ---: |
| `record_successor.py` | 23 |
| `owner-acceptance.json` | 12 |
| `recorded-followup.json` | 13 |
| `record.out.txt` | 1 |

Every addition uses `Hex High Entropy String`; SHA-1 of exactly one actual hex token on the recorded line matches `hashed_secret`. Each filename agrees with its containing baseline path. All 49 reproduce with installed detect-secrets 1.5.0 at the unchanged Hex entropy limit of 3.0. Reads used only exact committed source blobs, not the actively edited gameplay files.

| Actual value category | Entries |
| --- | ---: |
| Artifact/source SHA-256 pins | 28 |
| Mechanical proposal identities | 10 |
| Mechanical projection payload digests | 4 |
| Mechanical schema digests | 3 |
| Mechanical oracle identities | 3 |
| Git revision pin | 1 |

All values are public construction evidence or mechanical identities, not credentials. Recorder lines 70–119 declare rendered proposal pins, canonical proposal identities, retained input/receipt/review/preview pins, schema and oracle/projection identity. Its pin checks at line 283 and report construction at line 339 establish their uses. The JSON receipt and follow-up contain those same typed identities; the single stdout entry at line 45 is the native mechanical `payload_hash`, printed from the recorder's native result. The Git value resolves to a commit object. The reviewed SHA-256 identity producers and negative-control proof from the prior review remain applicable without rerunning native construction.

Independently hashing the exact committed successor bytes also matches the newly reported artifact digest **`ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d`**. This byte check confirms the new baseline value's artifact meaning; it does not repeat or replace the independent acceptance-receipt and recording review.

## Unchanged controls and current boundary

There are **zero removals or changes to existing baseline entries**, including line numbers and flags. All 49 additions have `is_verified: false` and no `is_secret` field. These metadata facts are not the basis for harmlessness; actual source classification supplies that disposition.

Every non-results baseline field, detector, threshold and filter is unchanged. `.pre-commit-config.yaml`, `.github` and `.gitignore` are unchanged across this delta. The previous synthetic changed-value negative control is reused because its matching settings and machinery are unaffected. No full scan, test, install, native builder, recording, private-store validation, network or CI operation was run.

Evidence: `c8-baseline-review/recording/check.py` and `results.json`. The script records committed source hashes and all 49 redacted contexts, fields, classifications and content/detector matches. It runs with the selected checkout's `venv/Scripts/python.exe -B` and imports no application code.

At **2026-10-13 18:48:12 UTC**, HEAD remained `183a664`; the baseline, four reviewed source files and control files had no later committed or working changes (source comparison normalizes CRLF/LF only). Active mutable RPG work and new diagnostic/review outputs are outside this immutable input boundary. Later baseline additions or changed referenced content require only their affected delta review; this finding does not cover future suppressions automatically.

No reliance was placed on the original recorder shell exit marker or the 168-test diagnostic as whole-PR acceptance evidence. Actual process completion and source-recording validity belong to the separate recording review; parent-coordinated exact-head gates and whole-PR acceptance remain required. Writes here are limited to this note and its bounded evidence directory. No baseline, source, Owner document, Git state, active engineer work or unrelated file was modified.
