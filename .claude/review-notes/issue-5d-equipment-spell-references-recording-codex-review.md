# CRD Issue 5d — thirteen-reference recording: Codex final review

3 October 2026. **Recorded and independently verified; no material gap found.** The [exact Owner acceptance](issue-5d-equipment-spell-references-owner-acceptance.md) authorizes this recording and the reader correction. The [recorded follow-up](issue-5d-equipment-spell-references-recorded-followup.md) identifies the actual artifacts, native checks, diagnostics, and remaining limits.

## Exact result

- Recorded oracle SHA-256: `5909e5bdd8c73bf32525b17942924364871146d648b83681518561361a434c0d`.
- Actual recording time: `2026-10-03T09:30:23Z`.
- Native recording script SHA-256: `a6763ef89326ff85d6f782689e36f00573d32be9f0acf36ae5c4b60e239cfd28`.
- Recorded follow-up SHA-256: `ab1822b13258005a30d0260b20d21611d9daffcbfd07e6dd5d5ce79090079e34`.
- Schema 17 and the existing release binding are unchanged: 24 batches, 1,835 records, 10,493 spans, 1,476 review units, and 1,476 resolutions. **Ten reference findings remain; uncovered-leaf and other findings are zero.**

## Independent qualification

Codex independently compared the finished JSON with the sha-verified saved prior and the accepted proposal. All 1,463 prior resolutions and approvals, their relative order, and every other payload are preserved. The thirteen additions exactly match the proposal; only their new Owner authorization and actual-time approval evidence differs from simulation. Evidence: [payload comparison](../_sp/esr/recording/codex-payload-verification.json).

Astra at high effort reviewed the bounded recording script without running it or duplicating runtime checks. No material gap was found in authorization pinning, native additive recording, preservation, or fail-closed replay. The final timestamp/hash pins were checked against the executed result; reversing only those pins and the resulting dictionary formatting reproduced the initially reviewed script hash. The current script hash still matches that final review.

The native simulation, one recording, and pinned post-write verification each exited 0. The recorded-reader diagnostics passed **39**, and live-identity diagnostics passed **17**. These 56 checks are focused diagnostics, not full-gate evidence. The pre-write reader correction's source hash remains `4a33bf3c5f07120623c943b06f22e327f53d47dafba820677d5780b008877e2d`; the subsequent test changes move fixtures to recorded bytes and a replayed control, without changing test bodies.

Codex independently qualified the scoped baseline delta: ten known public-hash additions in the recording script, 963 oracle and three Animals-test line-number updates, no prunes, no other entry changes, unchanged plugins/settings/generated time, and no unrelated-file changes. Final baseline SHA-256: `ae2268b60aa6ed124fb22c0753f6b91f0f3537e8a754baa0cad4aa82326d2c61`. Evidence: [baseline comparison](../_sp/esr/recording/codex-baseline-verification.json).

The [final eight-file hook log](../_sp/esr/recording/final-hook.log) covers current artifact hashes. Real hook exit **1** identifies the unstaged baseline; private-copy exit **0** proves content coverage only. No staging was used to turn this into a commit-gate success.

Codex verified unchanged HEAD, full index hash, stashes, source pin/PDF, settings, guidance files, immutable candidate/proposal/delta/review packets, and production reader. The restart opening is current and its historical body is preserved.

## Standing boundaries

The ten held citations and pre-existing out-of-scope reader-retention residue remain for later work. The partial-publication block, bounded Owner release-order pass, and normal delivery gates remain. Scoped script format/lint/type checks pass; expanded mypy still reports eleven pre-existing errors, and the broad suite, coverage, and dependency-vulnerability gates remain deferred/non-green.

No commit, push, merge, publication, activation, shared-database write, corpus reorder, or automation change occurred. Include the restart opening and supporting evidence in the normal restart delivery when authorized; do not extract a standalone PR against main.
