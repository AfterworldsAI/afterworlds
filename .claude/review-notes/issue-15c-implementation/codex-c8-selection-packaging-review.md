# CRD Issue 15c — C8 selection and packaging review

**Verdict: no blocking defect found in the committed selection/packaging slice at `183a664e8645ecadd97c55517e8ba1120e9c5b19`.** This closes the static integration-review subset left pending by `codex-c8-recording-review.md`. It is an internal check in the already authorized whole-PR workflow, not a new Owner acceptance milestone or whole-PR gate clearance.

Read the full governing preparation draft, the exact C8 Owner acceptance and `owner-whole-pr-review-2026-10-13.md`. Reused installed Review/routing and the task's verified-current Library guidance. The completed RAW/schema/native/recording/conservation proof is reused because the committed artifact and preserved predecessors retain their reviewed byte identities.

## Committed behavior

Reviewed immutable Git blobs and the exact parent-to-commit diff for `oracle.py`, `MANIFEST.in`, `pyproject.toml`, and all seven changed test files. Mutable RPG edits were outside this review.

- **Supersession:** `oracle.py:227–234` adds exactly C7's digest `2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373` to the existing predecessor/G1/C5 set. Every old digest and both superseded-release guards remain. The four resolver entry/helper functions have identical ASTs to the parent: fixed directory, quarantine refusal, exact identity handling and duplicate-claimant refusal are unchanged. No filename-based shortcut or blanket same-release exclusion was introduced.
- **Actual claimant:** independent JSON/digest inspection of the committed oracle directory finds exactly C8 matching this package/release after the declared digest skips. The committed C8 bytes still hash to `ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d`. C7/C5/G1/predecessor hashes match both the parent commit and the completed recording review. That preserves the evidence while selecting the accepted successor.
- **Packages:** `MANIFEST.in:23` and `pyproject.toml:78` add only the C7 file exclusion. Existing includes/exclusions stay intact. The current C8 file remains covered by package data and the sdist include. Static evaluation over the committed oracle file set leaves C8 as the only packaged oracle for both declared paths; C7 and earlier artifacts remain in Git. No source evidence was deleted.

## Tests and actual diagnostics

The changed tests advance expected authority to the real recorded C8, rather than changing behavior to accept an arbitrary new artifact:

- `test_oracle_succession.py:74` asserts the exact four superseded digests and unchanged prior artifact hashes; `:155` resolves the actual current release and compares the C5/C7/C8 proposal overlay and accepted C8 semantic oracle identity. Existing duplicate-claimant and missing-current tests remain unchanged.
- The C8 proposal constants equal the five identities already independently verified against the Owner receipt and retained proposals. Overlay order preserves C7 equipment while replacing its character-origins-feats contribution with C8. Current-release publication tests use the accepted projection UUID and real recorded file digest. Directory inventories gain C8 while retaining C7; the reviewed-proposal allowlist adds exactly the accepted C8 identities. No negative test or gate assertion was removed.
- `tests/ingestion/corpus/test_packaging.py:151` still builds actual wheel and sdist, checks the shipped artifact bytes, omits retired/superseded products, installs both into separate targets and probes from a neutral directory with editable-source imports disabled. Its updated constants pin exact C8 and add C7 to the omitted set. It still verifies installed module origin, one packaged oracle, 24 batches and quarantined-release refusal.

Read the committed `runs/recording-focused.result.json` and actual stdout/stderr. The recorded diagnostic ended `2026-10-13T18:40:34.8004864Z`, exit **0**, with **168 passed in 1889.68 seconds**. The runner checks formatting and invokes six mechanical test files with `--no-cov`. It does **not** include `tests/ingestion/corpus/test_packaging.py`, so this is not evidence that the real wheel/sdist/install smoke test has run for C8. The output itself correctly labels the run focused diagnostics, not acceptance/full-gate evidence. No long test run or package build was repeated here.

## Evidence boundary and remaining work

Independent read-only script `c8-native-review/selection/check_selection.py` completed exit 0. `selection/results.json` records immutable blob hashes, actual artifact bindings/digests, constant/manifest comparisons, supplied diagnostic evidence and the current-file boundary. At its `2026-10-13T18:48:07Z` check, HEAD was still `183a664` and every inspected source/manifest/test/runner/current-artifact file matched that commit. Later changes to those inputs require the coordinator's normal changed-input review; unrelated mutable gameplay edits do not invalidate these comparisons.

This inspection did not invoke the application selector anew; its implementation is unchanged and its new exact data input was independently checked. Runtime selector diagnostics are supplied by the focused run. Static manifest evaluation is not a substitute for the actual distribution build/install smoke test. The latter, full configured-coverage pytest, all unchanged repository gates, exact-head CI and final consolidated PR review remain with the whole-PR process.

The same commit's `.secrets.baseline` additions and independent gameplay implementation are outside this bounded review. No source, baseline, Git or Claude mutation, native store access, builder, recording, source census, pytest or package build was performed. Only this report and the bounded `selection/` review files were written. Continue the complete PR; no new Owner question or engineer pause is required.
