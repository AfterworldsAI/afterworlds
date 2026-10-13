# CRD Issue 15c — C8 secrets-baseline delta review

Verdict: **delta cleared; no blocking defect found**. Disposition: **already safe / no change**. This is bounded evidence for the complete PR review, not an additional Owner acceptance milestone, full-gate success, merge clearance or runtime authority.

Reviewed immutable commit `5c4d8d6e56c015862cb16f5e34d2229c985faf5a` against the last independently cleared baseline at `1d4193c4b162e3db4df3a3240d00313f36dd918b`. The base baseline SHA-256 is `ca3f383cbb646de71737d965c5168393c657972d24c17c1820ff316092531156`; reviewed baseline SHA-256 is `c22026f52d39b72530437b3ddf0e3429fe342f93060d2fcafb276d5d53b4dc0c`.

Applied the installed Afterworlds Review and routing skills, reusing this task's verified Library resolutions (Review 2026-09-25; Prompting 2026-10-05). Read the full governing `issue-15c-preparation/issue-draft.md`, the current `owner-whole-pr-review-2026-10-13.md` correction and the earlier C7/post-C7 baseline reviews. The Owner accepts or rejects the complete PR; existing exact C8 and bounded species-input decisions remain in force.

## Actual delta and source classification

The net delta is **284 exact `(filename, detector, hashed-value)` entries across 19 files**. The engineer's 198 figure describes only the final evidence commit: `ad1ef59f388e8146231fe846fc84c159a6fa669c` adds 86 and `5c4d8d6e56c015862cb16f5e34d2229c985faf5a` adds 198. Both increments are covered here; the previously reviewed 105 additions through `1d4193c` are reused rather than reviewed again.

Every added entry names `Hex High Entropy String`, has exactly one matching hexadecimal token on its recorded source line, and reproduces with the installed 1.5.0 Hex detector at the unchanged entropy limit 3.0. SHA-1 of the actual token matches the baseline's `hashed_secret`; its filename matches the containing baseline path. Source reads used only exact committed blobs. The inventory records every location, redacted source context, JSON field context, classification and matching result without copying matched values.

| Reviewed content category | Entries |
| --- | ---: |
| Artifact/source SHA-256 pins | 206 |
| Mechanical proposal identities | 35 |
| Mechanical schema digests | 11 |
| Mechanical projection payload digests | 11 |
| Mechanical oracle identities | 4 |
| Git revision pins | 17 |
| **Total** | **284** |

The 206 artifact pins name retained source, candidate, preview, review, script, baseline, proposal-rendering and run-evidence bytes. Their field/constant contexts were inspected, including the shared script's isolated-store digest; that value is a file digest, not a store password. All 17 Git values resolve to commit objects. None of these new entries is a mechanical certificate/template fingerprint or a credential field. No actual key or newly masked credential was found.

Static producer inspection establishes the remaining identity types rather than assuming that any long hex value is harmless: `build_c8_preview.py:127` hashes bytes with SHA-256; its accepted-input tuples at line 179 distinguish rendered file hashes from proposal identities, and its report at line 749 distinguishes pins, proposal identities, oracle identity and schema. `proposal_identity` and `oracle_identity` hash canonical mechanical payloads; `identify_projection` sets `payload_hash=hash_obj(payload)`; `representation_schema_hash` hashes the closed schema contract. `ingestion/corpus/hashing.py:hash_obj` uses canonical SHA-256. `c8-native-review/check_artifacts.py:11` and line 110 record byte hashes and independently check retained proposal identities. No application/native producer was imported or executed for this review.

The 27 entries in `issue-15c-c8-native/reports/c8-build.log.out` were also reviewed from its **tracked blob at the exact reviewed commit**. The log's JSON is the builder's printed report subset; it contains the same artifact/schema/oracle/projection pins. Contrary to an initial concern, this `.log.out` file has committed provenance. The separate `*.log` supervisor/focused-test files are the ignored logs; no working-file fallback was needed.

## Matching controls and unchanged evidence

There are **zero removals and zero changes to existing entries**, including line numbers and audit flags. All 284 additions have `is_verified: false` and no `is_secret` field. This metadata does not independently certify harmlessness; the content review supplies the false-positive disposition.

Detector plugins, thresholds, filters and all other non-results baseline fields are byte-value equivalent after JSON parsing. `.pre-commit-config.yaml` and `.github` have no changes across the reviewed range. The hook remains detect-secrets v1.5.0 with `--baseline .secrets.baseline`. The only `.gitignore` addition is the specific C8 regenerated preview directory, following the existing C6/C7 artifact pattern; it does not alter detector/filter matching or exempt the tracked evidence files reviewed here.

Reused the independently recorded C7 negative control, carried forward by the post-C7 review: three synthetic changed-value findings survived real `SecretsCollection` baseline subtraction with the actual settings. Matching machinery and settings remain unchanged, so this unaffected control was not rerun. The only detector execution here was narrow, in-memory reproduction on the 284 new recorded lines.

## Evidence and invalidation

- `c8-baseline-review/check.py` reads immutable Git blobs, verifies identities/configuration and emits `results.json`, including all 284 redacted entry records and committed source-blob hashes.
- `c8-baseline-review/check_invalidation.py` emits `invalidation.json`. At **2026-10-13 17:54:56 UTC**, HEAD remained the reviewed `5c4d8d6`; no later committed or current-working changes affected the baseline, its 19 referenced files, detector/hook/CI controls or `.gitignore`. Working source comparison normalizes CRLF/LF only; the raw working baseline hash also exactly matched.

These checks ran with the selected checkout's `venv/Scripts/python.exe -B`. No application import, candidate generation, store access, full test/gate run, network/CI execution, source/baseline/Owner-document modification or Git mutation occurred. Writes are limited to this report and `c8-baseline-review/`. The active engineer's work and unrelated `merge_baseline.tmp.py` were untouched.

Clearance is scoped to the exact reviewed baseline and source content. Later additions, changed values/paths/flags, detector/filter/hook/CI changes or changed referenced content invalidate only the affected evidence and require the corresponding delta review. Ongoing untracked C8 recording/oracle work was visible in status but is outside this baseline slice; it is not covered by these results. Newly written review evidence is likewise not a fresh repository secret-scan result. Whole-PR exact-head gates, integration acceptance, merge and shared-runtime boundaries retain their existing requirements.
