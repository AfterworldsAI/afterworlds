# Thirteen-reference candidate — independent Owner review

3 October 2026. **Ready for exact Owner acceptance; UNACCEPTED and unrecorded.** Codex found no material gap in the completed candidate or its bounded reader correction. The Owner's instruction authorized preparation of the four Equipment/cursed-item and nine spell references, with the other ten deferred; it did not accept this exact candidate.

## Result and exact identity

The [implementation packet](issue-5d-equipment-spell-references-review.md) specifies all thirteen source occurrences, destinations, route meanings, preservation evidence, and deferred residue.

- Simulated candidate SHA-256: `faa46e9c5f4668bad2ed5ad764fccd9f1f8fb2f9471f5986186523961e418290`.
- Proposal SHA-256: `b9bf5638902b2384da3875963f4846d794339e3656efd2c8321c4c6094d8056d`.
- Delta SHA-256: `0e00a0d6cd7576ba43651f0b06d69062ed9e3ab7e40783b6bfc4ea48e2a8c601`.
- Constructor SHA-256: `623f0509812dc64872d09f8fa98d09b07b9b5a6f28b197cdb451933817bd6b7e`.
- Packet SHA-256: `29caa23daee5eb78404d637ba8149bd4ebd2f4895f286a46646475b6bcfd646d`.
- Reader SHA-256: `4a33bf3c5f07120623c943b06f22e327f53d47dafba820677d5780b008877e2d`.
- Test file SHA-256: `00111b870eb8f0c3e9fcc45da20ff2695fa6ac283c4b7a69abc876063fc7f8b5`.

Native simulation clears 13 reference findings, leaving **10 reference findings, zero uncovered leaves, and zero other findings**. It keeps 24 batches, 1,835 records, 10,493 spans, and 1,476 review units, with resolutions increasing from 1,463 to 1,476. All prior resolutions and approvals are preserved; only thirteen resolutions and their simulated approval records are added. Serialized reload and isolated persisted round trip succeed. The accepted oracle remains byte-identical at `e9678ab30c27ba92deda5757de4be082aba8bfc44690b6bf94f7bc1f747a45ca`, with **23** findings until authorized recording.

## Independent qualification

Source/mapping review (Sol, high) qualified the fourteen Equipment chapter sections in printed order, the four explicitly cursed item descriptions, Gaining plus Casting Spells for the eight class citations, and Casting Spells for the glossary's qualified entry-characteristics citation. The final proposal is byte-identical to that reviewed mapping. Exact original provenance spans were independently compared against the current oracle for all thirteen identities; no new resolution ID collides with existing acceptance.

The initial production-reader run exposed two row-37 failures: 39 passed / 2 failed. The Exploration pointer is accepted record-owned supporting text, not component governing prose. The previous guard rejected it despite ADR-005d Decision 7 permitting that ownership. This was classified as issue-scoped implementation work, not missing source information or a new Owner Decision.

The bounded correction admits unbound supporting provenance only for a record-owned citation whose base record survives. It checks reconstructed `SUPPORTING_AUTHORITY` classification and refuses override-supplied source records, including a same-key replacement retaining old span IDs. Prose-bound cited spans still must survive in effective source prose. Astra at high effort independently reviewed the correction and found no material gap; final source/test hashes match the reviewed revisions. No schema, corpus, component invention, reference re-keying, or accepted-batch replacement was needed.

The packet's bounded sibling census records pre-existing source-retention residue for later triage. It does not silently turn uninspected residue into Owner Decisions or repair deferred work. The ten held citation identities remain undrafted.

## Actual checks and limits

- `cand3` and restored `cand6`: native composition exits 0 with identical candidate, proposal, and delta bytes. The interim twelve-reference artifacts/checks are superseded.
- `focused4`: **20 passed**, exit 0, covering the failed Exploration cases, disabled/replaced record sources, record-owned prose dependencies, component/prose removal, append/unrelated overrides, and existing reader/destination regressions. This is **focused diagnostics only**, not acceptance or full-gate evidence. Unaffected evidence from the 39 prior passing diagnostics was reused.
- Codex direct Black `--check`, Ruff `check`, and mypy `--strict` on the three changed Python files each exit 0 without pipeline masking. Raw results are in `_sp/esr/codex-direct-gates.json` relative to `.claude/`.
- Final six-file hooks: real exit **1** because the baseline is unstaged; private-copy exit **0**, proving content coverage only. Every recorded final-file hash matches current bytes.
- Baseline `5796c5acea85b60e5be2d84ddaa00d2e850db9d50535d1ba32c41fa69144b44d`: independently compared with the starting baseline. Exactly eleven additions across constructor (1), proposal (6), and delta (4); each is a known public oracle/release/schema hash. No removals, unrelated entry changes, plugin/filter/configuration changes, or generated-time changes.
- Accepted oracle, source pin/PDF, settings, AGENTS.md/CLAUDE.md, HEAD, full index hash, and stashes are unchanged from the dispatch snapshot. The restart opening is current and its historical body is byte-preserved.

The raw implementation logs are under `.claude/_sp/esr/`. No broad suite, historical reconstruction, recording, staging, commit, push, merge, publication, activation, shared-database write, or automation change occurred. Dependency-vulnerability repairs, expanded mypy, and coverage remain deferred/non-green under the existing restart limits. The normal publication gates and bounded Owner release-order pass still apply.

## Acceptance boundary

The existing handoff requires exact candidate acceptance before another recording. Acceptance should identify **this exact thirteen-reference candidate and its reader correction**, retaining the ten findings and partial-publication block. Acceptance would authorize the next bounded recording step under the standing workflow; it would not authorize publication, activation, reorder, unrelated remediation, or a standalone PR against main.

Include the [restart document](../../docs/architecture/issue-5c-5d-clean-restart.md), disposition, packet, correction, and supporting evidence together in the normal restart delivery when its gates permit it.
