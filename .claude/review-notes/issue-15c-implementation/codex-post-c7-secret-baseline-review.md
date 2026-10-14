# CRD Issue 15c — post-C7 secrets-baseline delta review

Verdict: **delta cleared; no blocking defect found**. Disposition: **already safe / no change**. This is a bounded secrets-baseline review, not full-gate success, CRD Issue 15c completion, C8 semantic acceptance or merge clearance.

Reviewed commit `1d4193c4b162e3db4df3a3240d00313f36dd918b` against independently cleared C7 revision `b5051d8433ac2be7336daa41f2aae038b9d21c9e`, named in `codex-c7-recording-final-review.md`. The base baseline SHA-256 is `3006e93343aee4ec5150631db5af7bddc0c935031b76711b7f2ed6ac683bfe55`; reviewed committed and current-working-file baseline SHA-256 is `ca3f383cbb646de71737d965c5168393c657972d24c17c1820ff316092531156`.

Applied installed Afterworlds Review 2026-09-25 and routing, reusing the coordinator's task-verified Library resolutions (Review 2026-09-25; Prompting 2026-10-05). Read the full governing `issue-15c-preparation/issue-draft.md`, local `AGENTS.md`, and the prior C7 report. Codex remains reviewer; Claude remains implementer.

## Verified delta

The net delta adds **105 exact `(filename, detector, hashed-value)` entries across 14 review-evidence files**, all `Hex High Entropy String`. No prior-C7 entry was removed or altered. Every added entry's SHA-1 matches exactly one hexadecimal token on its recorded line, and all 105 reproduce with the installed Hex detector at the unchanged baseline entropy limit of 3.0. Each recorded filename matches its containing baseline path. Current referenced files match the reviewed commit after CRLF/LF normalization.

| Actual content category | Entries |
| --- | ---: |
| Artifact/source SHA-256 pins | 72 |
| Git revision pins | 8 |
| Mechanical certificate fingerprints | 7 |
| Mechanical template fingerprints | 18 |

The artifact pins occur in C7 inspection, frozen spatial-review module hashes, own-creature review input hashes, and C8 current/r1 candidate, derivation and static-inspection evidence. The fingerprint values occur under mechanical `provenance/certificate/fingerprint` and `provenance/templates` fields, not credential fields. Static producer inspection confirms file hashing and mechanical provenance serialization; the mechanical fingerprint code uses SHA-256 (`capability.py:623`, `:641`). All eight revision values resolve to Git commit objects. No credential fixture exception or newly masked real secret was found in this delta.

Representative locations: `candidate-c8/c8.json:2` and `:5356`, `candidate-c8/codex-review/static-inspection.json:4`, `delivery-review/spatial-4a39f27-frozen-results.jsonl:4`, `owncreature-review/correction-probes.json:14` and `:67`. Paths in this paragraph are relative to this report's directory. The bounded result inventory records every added location, category and content/detector match without copying matched values.

The baseline-changing commits since the cleared revision are:

| Commit | Added | Removed | Other change |
| --- | ---: | ---: | --- |
| `41f892cc9d1e2ce235fc4334b4b63a3fd2d71650` | 29 | 0 | None |
| `dc68b3c9aa1f2a33d4d7185b01ed7edd82706ff3` | 10 | 0 | None |
| `f8be6caa8b6d3dc7e86c2d7c23b50718869ee2ba` | 23 | 0 | None |
| `1d4193c4b162e3db4df3a3240d00313f36dd918b` | 43 | 0 | Eight C8 source-pin line numbers move by +23 |

Those eight line changes affect entries introduced after C7, explaining why the net comparison has zero modifications to pre-existing C7 entries. They alter no path, detector or hash.

## Matching and audit metadata

Detector plugins, thresholds, filters and every other non-results baseline field are identical to the independently cleared baseline, including generation metadata. `.pre-commit-config.yaml` and `.github` are unchanged across the reviewed range and against the current working tree. No broad matching/filter/detector/CI suppression was introduced by this delta.

None of the 105 additions contains an `is_secret` field; all have `is_verified: false`. These are metadata facts, not evidence that the detector independently adjudicated them harmless. Their false-positive disposition comes from the content review above. No `is_secret` flag was added, removed or changed in this delta; unchanged C7 audit metadata is covered by the prior review.

Reused the prior independent C7 negative control, which found three synthetic changed-value detector findings surviving real baseline subtraction. Settings and matching machinery are unchanged, so that unaffected control was not repeated. The additional control actually run here was read-only, in-memory detector reproduction for every newly baselined line; it performed no network verification and printed no matched values.

## Reproduction and limits

`post-c7-baseline-review/check.py` and `post-c7-baseline-review/results.json` contain the bounded checks and result inventory. Run the check only from this implementation checkout with `venv/Scripts/python.exe -B`; it guards the exact reviewed HEAD, reads immutable Git blobs and current referenced files, compares configuration, verifies hashes and invokes only the Hex detector in memory. No application/native candidate code is imported or executed.

Baseline bytes, source, tests, prior review scripts, Git state and authority were not modified. Writes were limited to this report and its new bounded evidence directory. No full hook/suite/gate, network operation, candidate derivation, native candidate inspection, store access, shared-runtime action, Claude action or semantic review ran. The separate incomplete native C8 worktree was not inspected.

Clearance applies only to this exact baseline and its reviewed content. Subsequent entries, changed suppression settings, or changed referenced values require review of the affected delta; the new report/evidence files themselves are not a fresh full-scan result. Exact C8 semantic acceptance, GameMaster species policy, full repository/CI gates, merge and runtime boundaries remain with their existing authorities.
