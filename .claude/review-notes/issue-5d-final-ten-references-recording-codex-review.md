# Final-ten reference recording: Codex review

Reviewed 6 October 2026 locally, following the Owner's exact acceptance:
"I accept this exact candidate."

**Completed: no blocking finding in this exact working-tree recording.**
The independent payload/preservation checks, all 53 selected diagnostics and
private-copy content checks pass. This is not full-gate, publication or
activation approval.

## Artifact and authority

The [Owner acceptance](issue-5d-final-ten-references-owner-acceptance.md),
[candidate packet](issue-5d-final-ten-references-candidate.md) and
[candidate review](issue-5d-final-ten-references-codex-review.md) remain
unchanged as accepted history. The exact proposal is
`46808846b0ad6712393b0f058a71e03d6e664a2ffdf8734de7d046bf4b4d68e3`.
Claude recorded one native `resolve_references` action at
`2026-10-07T01:30:07Z` under `Ravenlok (Owner)`, with the real acceptance
reference and timestamp. The live oracle SHA-256 is
`e6f5f36aa3af13807bbff721797d971dcf0d8e588a97483c7d769cf88cbd1308`.

The same release, `67c81736-15fd-5e82-8523-e84922f0a7c6` /
`5.2.1-corpus.3fe24ff6-4e3`, retains schema 17, 24 batches, 1,835 records,
10,493 spans and 1,476 review units. It now has 1,486 resolutions and real
resolution approvals; reference, uncovered-leaf and other findings are zero.
The ten new resolutions have 144 labelled routes and 201 destinations.

Codex compared primitive full payloads against the saved prior oracle
`5909e5bdd8c73bf32525b17942924364871146d648b83681518561361a434c0d`:

- All 1,476 prior resolutions and approvals retain their exact content and order.
- Every other top-level payload and acceptance collection is identical.
- The ten new resolution objects exactly equal the accepted PROPOSAL, in order.
- Each has one real Owner approval, quoting the exact acceptance and pinning
  its receipt and proposal. Their single actual UTC time follows this run's launch.
- Native readback reproduces the recorded bytes. Against the reviewed simulation,
  only 40 new-approval leaves differ: reviewer, authorizer, authorization reference
  and timestamp, ten of each. No simulated approvals were copied.

Independent proof: `.claude/_sp/final-ten/recording/codex-payload-verification.json`.
The raw recording, saved-prior verification, historical replay verification and
relocated-constructor check each have exit 0 in `recording/run/`. They include
isolated persistence checks; no shared database was written.

## Recording-invalidated consumers

The accepted constructor, PROPOSAL, DELTA and reviewed test were retained
byte-identically under `issue-5d-final-ten-references/candidate/`. The live test
uses that retained constructor, persists the recorded oracle, and uses the prior
recording for its unresolved-reference control. Its content assertions are
unchanged from the accepted test; the passing 33 candidate reader diagnostics
remain applicable to unchanged resolution content.

The replacement-chain helper now pins the final recording and retains the
thirteen-reference state as historical replay. The Animals tests distinguish
that historical recording from the new live recording. Readiness expects 1,486
resolutions. The earlier thirteen-reference reader test retains its own historical
fixture, including the Gear citation that was unresolved at that stage.

Codex reversed only the literal consumer edits in memory and recovered the
pre-recording hashes of all five affected Python files. This verifies the change
boundaries independently, without undoing working-tree files. Evidence:
`recording/codex-consumer-diff.json`. No production reader, acceptance contract,
schema, source corpus or house-rule installation changed.

## Checks and limits

The recording script passes scoped Black, Ruff and strict mypy. The five affected
consumer files pass Black and Ruff. Their strict mypy invocation exits 1 with
11 errors in existing test code: five on unchanged Animals statements and six
in two unchanged files. Codex mapped the Animals error lines back to the exact
pre-recording content; the other files retain their snapshot hashes. This gate
is non-green. It does not authorize unrelated type repairs or a claim of full
gate success.

The corrected selected diagnostic run passes all 53 tests in 1,837.64 seconds,
raw exit 0 (`recording/run/focused-2.log` and `.exit`). It exercises the live
identity consumers, historical recording checks, all ten new unresolved-reference
controls and recorded routes, disabled/unrelated destination behavior, and the
retained thirteen-reference reader fixture. Its initial invocation exited 2
because the wrapper rejected an extra pytest flag; no tests ran in that attempt.
No broad suite, coverage, pip-audit or expanded mypy success is claimed.

The baseline adds exactly 22 public integrity-hash entries in four new retained
evidence files. It also refreshes only line-number metadata in two affected files:
963 entries in the oracle and three in the Animals test. Removing the additions
and restoring those line numbers recovers the previous baseline byte-for-byte.
Existing hashes, all other entry fields, plugin/filter settings, version, order
and generated-at are preserved. Codex identified every new value independently
and checked the refreshed line-number inventory against the final scan.
Evidence: `recording/codex-baseline-verification.json`. The relative-baseline
hook exits 1 because the real baseline remains unstaged. The first full
private-copy hook exits 3 and updates stale line-number metadata in its private
copy (`recording/final-hook.log`). Only the two affected files' line numbers were
reconciled in the live baseline; unrelated private-copy changes were excluded.
The final full private-copy hook exits 0 and leaves its baseline unchanged
(`recording/final-hook-3.log`, after the final follow-up wording changes). The empty-file-list trial is not counted as a
content check. Final reviewer-document results and pins are in
`recording/codex-final-hook-2.log`. No green staged gate is claimed.

The restart opening records the new acceptance and live artifact; its historical
body remains byte-identical. HEAD, branch, full index, four stashes and external
guidance/settings/launcher remain unchanged. The final preservation scan covers
all 3,925 pre-existing Git-visible files outside this task's scratch directory.
Only nine existing files changed: oracle, oracle README, five affected test/helper
files, the narrowly additive baseline and the restart opening. Eight new retained
artifacts are the recording script, acceptance receipt, recorded follow-up, this
review and four byte-identical candidate-history copies. No pre-existing file was
deleted. Final exact file pins, raw exits and guards:
`recording/codex-final-verification.json`.

## Remaining boundary

The partial-publication block and bounded Owner release-order pass stand.
Pre-existing reader-retention residue and dependency repairs remain deferred.
Awakened Plant remains an isolated Afterworlds house-rule template, uninstalled
and unactivated; no SRD creature record was added. There was no stage, commit,
push, merge, publication, activation, shared-database write, reset, clean or
corpus reorder. Deliver these evidence and opening updates through the normal
restart workflow when authorized, never a standalone PR against `main`.

Architecture Notes: **No drift from design principles.** Existing recorded scope
exceptions and Owner directions remain as described in the accepted packet.
