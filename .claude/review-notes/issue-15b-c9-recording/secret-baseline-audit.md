# Checksum baseline audit (CRD Issue 15b C9)

Compared with #194's baseline (`5d05f473`), this PR adds **291** `.secrets.baseline` entries, all `Hex High Entropy String`. Scanner `plugins_used` and `filters_used` are unchanged. There is no path, entropy or plugin exemption and no allowlist of future recording-note content.

| File | Entries | Content |
| --- | --- | --- |
| `recert/governing-components.json` | 259 | component schema ids and operation fingerprints |
| `recorded-followup.json` | 13 | acceptance identities and digests |
| `owner-acceptance.json` | 12 | acceptance identities and digests |
| `ci-38555377777-completed.json`, `pr-194-accepted-head-ci.json` | 1 + 1 | public GitHub CI commit IDs |
| `record.out.txt`, `record_successor.py` | 1 + 1 | the successor digest; #194's head commit ID |
| `s1-on-c9/s1-on-c9.json` | 1 | the accepted S1 SHA-256 `c232a786…`, added in the review-closure round |
| `secret-negative-control/*-result.json` (2) | 1 + 1 | the baseline file's own SHA-256 `e6f34984…` at control time, added in the review-closure round |

**Audit.**
- **The first 288 entries** (seven files) were independently matched by Codex (`CODEX-C9-SECRET-BASELINE-AUDIT.md` in the coordination directory). It matched each hashed secret by SHA-1 to the literal at its reported line: 283 SHA-256/component/fingerprint digests and five commit IDs, with no unmatched entry.
- **Entries 289–291** were checked here as the only 40+-hex literal in each file: the S1 digest, and the baseline digest recorded by Codex's two receipts.
- **All 291** are checksum or commit metadata, not credentials, and are marked `"is_secret": false`. Entries carried from earlier baselines are unchanged; for `oracle.py` and one test, only line numbers moved, with identical hash sets.

**Negative control (Codex, preserved as received).** With this baseline's scanner configuration unchanged, the pre-commit hook detects a new literal outside baselined files and exits 1 (`secret-negative-control/secret-negative-control-result.json`, copied byte for byte from the coordination directory; the control literal itself is not committed: expected 1, actual 1, detector matched; baseline then `e6f34984…`). The earlier attempt stopped at the hook's unstaged-baseline guard before detection, so it is **not** detector proof. Codex re-verifies the final baseline.
