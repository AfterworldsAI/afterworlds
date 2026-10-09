# CRD Issues 5c/5d restart — concrete Git delivery packet

Prepared 8 October 2026 UTC for Owner review. This packet proposes delivery; it
does not authorize staging, commits, a push, a PR, merge, runtime publication,
activation, or shared-state writes. The bounded release-readiness correction is
complete. Review of the eventual complete PR and its exact committed head remains
required.

## Recommended delivery

Create an isolated delivery checkout and a new topic branch,
`codex/5c-restart-delivery`, from the verified current `main`. Assemble the final
restart contents using [the exact manifest](delivery-manifest.json), then make
one atomic delivery commit and a draft PR against `main` when authorized. Keep
the existing restart branch, its index and four stashes untouched. Do not push
the existing branch or rewrite its history.

Proposed commit subject: `feat(ingestion): deliver the qualified SRD restart and accepted recording`.
Proposed PR title: `Deliver the qualified SRD source and accepted restart recording (#132, #137)`.
[The draft PR description](PR-DRAFT.md) covers the whole restart, including the
earlier source, quarantine, persistence, reader and schema work.

This route carries the final tree rather than 115 branch-only commits. The local
overlay commit stays local, and obsolete intermediate artifacts do not enter the
new PR merely because they exist in branch history. This is a new delivery
branch; it does not alter or discard the original history.

## Verified Git state and base

| Item | Observed state |
| --- | --- |
| Source branch | `codex/5c-5d-clean-restart` |
| Source HEAD | `1388939b1bda445d93cf7ec8ae9a445e967e0fa9` |
| Original index SHA-256 | `40473ee3d69a67442602f4b0d83ec4b3cefce7ad7c3011489ff8970289661c6c` |
| Existing staged work | 36 deletions, 4 additions and a staged baseline modification; preserved |
| Other tracked working changes | 79 unstaged paths plus the further unstaged baseline change |
| Untracked files before this packet | 4,062 files; not a staging list |
| Cached `origin/main` | `1c484e3a83f736bed212fd415114dcef96c15bcf`; source branch ahead 115 / behind 10 |
| Live `main`, read from GitHub | `f5a78aa638243297ca2a280b8548f6f542c231dd`; no remote restart branch returned |
| Live main tree | `7c92fdf7237af33ac890b18e10a4e6e2bf6eda2e` |

Live `main` adds two commits beyond the cached ref: the focused-test diagnostic
runner and its merge. GitHub's live main tree exactly equals the locally available
`d3bc34ae0255d8028baf59bf30f6b966bbec5d7f` tree. The manifest therefore uses that
verified tree for a current-base comparison without fetching or modifying refs.
The 115/10 divergence is against the cached ref, not a live divergence claim.
Refresh the remote tip before assembly; any later base changes require a bounded
comparison before applying this packet.

The packet retains [the raw initial status](status-before.raw),
[staged patch](staged-before.patch), [working patch](working-before.patch), and
[branch-only commit inventory](head-only-commits.txt) locally. These inspection
exports are excluded from the proposed PR.

## Exact content and disposition

[delivery-paths.txt](delivery-paths.txt) and [delivery-manifest.json](delivery-manifest.json)
enumerate proposed final-tree files, actions, byte sizes, hashes and reasons.
[held-paths.txt](held-paths.txt) records exclusions without deleting them.
[selection-summary.json](selection-summary.json) gives the final counts and size.
The manifest includes unchanged-on-main dependencies by inheritance rather than
duplicating them as changes.
The proposal contains **930 source/evidence file changes, about 314 MB of
uncompressed contents**, plus 17 packet exports. Most paths are retained review
and replay evidence; this is the complete restart delivery, not merely the final
typing correction. None of these counts imply a clean-checkout gate has run.

| Delivery group | Contents |
| --- | --- |
| Governing and source evidence | September 21 Decision and reconciled ADR/architecture documents; pinned corrected community source, qualification/coverage evidence; October 6 reference decisions; current restart summary |
| Implementation | Quarantine, cited coherent corpus units, source/release lifecycle, retrieval windows, authoring and mechanical authority, reference resolution, native persistence/projection and reader/service integration |
| Schema and packaging | Migration `0036_reference_alternatives.py`, typed schema 17 support, package manifest and pinned-source byte-preservation attributes |
| Accepted authority and replay | Current accepted oracle and Owner receipt; retained historical oracles, proposals, generators, acceptance scripts and replacement-chain fixtures required by regressions |
| Corrections and tests | Original and expanded typing corrections, current/historical fixture separation, superseded-selector refusal and controls, source-order and native approval-negative coverage |
| Evidence and delivery status | Relevant restart review records and paired raw gate logs/exits; final-readiness and preservation results; this packet's public drafts and compact delivery checks |
| Secrets baseline | Reviewed working baseline, preserving prior entries/settings; staged hook and any necessary metadata normalization are still packaging gates |

Three stale-base differences have explicit dispositions:

- Keep `main`'s Graphify workflow at 0.9.68. Do not replace it with this branch's
  older 0.9.58 workflow.
- Keep `main`'s `pyproject.toml`, which removed the SQLAlchemy mypy plugin. The
  restart tree's reintroduction of that plugin is excluded.
- Apply only the accepted restart-continuation insertion to `main`'s `CLAUDE.md`.
  [CLAUDE.delivery-preview.md](CLAUDE.delivery-preview.md) is the exact proposed
  file. Preserve `main`'s newer model/Graphify guidance and diagnostic-runner text.
  Keep `.claude-pr/CLAUDE.md` at main's version and its local restoration history local.

Private `.claude/_sp`, `_rc` and other scratch trees, caches, isolated databases,
launcher/session transcripts, temporary PDF renders, unrelated settings and old
checkpoint dumps remain local. The Awakened Plant house-rule template is excluded;
the Owner Decision describing its SRD-reference boundary is included as authority.
Reader-retention residue and supplement integration remain outside delivery scope.
No accepted artifact is regenerated or rerecorded.

## Accepted identity

The exact Owner-accepted release-order candidate has SHA-256
`8a6a9a9c305f41207190c0deb55875a027019116ce3f825a6a0425a3a115b4bf`.
The recorded oracle is `srd-5-2-1-corpus-8781d4e0-a3b.json`, SHA-256
`def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c`.
It represents release `1299484e-c72d-509b-bd8d-d0169ee1f8d2` /
`5.2.1-corpus.8781d4e0-a3b`, with 24 accepted batches, 1,835 records,
1,486 reference resolutions, schema 17 and zero native findings.
Only the six approval-evidence fields changed from accepted candidate to recording;
proposal identities and all other content are preserved. Delivery authorization
must not be treated as new semantic acceptance or runtime activation authority.

## Evidence reuse and remaining gates

The completed full default backend run remains evidence: **7,397 passed,
141 skipped, no failures/errors; 92.48% coverage**. Root Black/Ruff and the 42-file
strict affected-test typing union passed. Accepted native persistence,
reconstruction, reader and source-order results are retained. The packet's new
read-only input check found **no drift in 612 non-generated files** from the final
gate freeze. Its exclusions are bytecode and egg-info outputs; this is a separate
check from the earlier 616-input gate check, not a replacement count.

Keeping main's mypy configuration invalidates reuse of typing results as proof of
that configuration. Only those checks were repeated: production typing passes
235 files, and the affected-test strict union passes 42 files, using the unchanged
main configuration in a separate preview. See the paired `main-config-*.log` and
`.exit` receipts in this directory. No full pytest run was repeated.

Before a push/PR, in the authorized isolated delivery checkout:

1. Verify the source hashes, exact accepted identity, inherited base and intended
   final tree. Check dynamic fixture reachability and documentary evidence links;
   the packet's literal-reference audit has no omitted existing fixture targets,
   but is not an executed clean-checkout acceptance test.
2. Stage only the approved delivery paths and the reviewed baseline. Explicitly
   include selected ignored raw `.log` receipts; do not broad-stage the source
   checkout. Run the real relative detect-secrets hook. Any baseline metadata
   normalization must preserve all reviewed rows/settings and be inspected and
   restaged; never substitute the private normalized baseline from prior checks.
   Whole-delivery secrets coverage is required: the earlier 202-file check only
   covered the correction increment.
3. Verify formatting, lint, typing and clean-checkout/packaging behavior on the
   assembled contents. Reuse unchanged proof; rerun checks invalidated by actual
   base/content/packaging changes. Preserve failed receipts as failures.
4. Commit the final contents and baseline together. Confirm the exact committed
   tree and its relationship to main before an authorized push and draft PR.

Before merge, require the exact committed-head Codex review and all configured CI
jobs: **Lint, Type-check, Test, Audit**; **Frontend — Typecheck, Lint, Format, Test,
Audit, Build**; **E2E — minimal spine (Playwright, faked provider passes)**.
These are outstanding, not local green claims. Full PR Architecture Notes must
cover all source/schema/retrieval/authority changes, not only the final correction.
[External synchronization draft](ISSUE-SYNC-DRAFT.md) is prepared but unposted.

The unchanged local environment audit reports 36 vulnerabilities in 13 packages.
Only repairs are Owner-deferred until restart completion. This does not waive a
required audit gate: if exact-head CI fails only for deferred dependency findings,
report the actual failing findings and resolve that merge-boundary disposition
with the Owner. Do not suppress the audit, invent exceptions, or expand this
delivery into dependency repairs.

Merge remains held for the Owner. Runtime publication/activation, shared-store
writes, external issue comments and restart-completion declaration each retain
their applicable authorization boundaries. Creating or merging a code PR does
not lift the partial-publication block.

## Immediate next action after approval

Authorize Claude to assemble this exact final-tree proposal in an isolated
delivery checkout, preserving the source checkout and accepted artifacts, then
complete its packaging gates and return the exact proposed commit/tree for Codex
review. Push/PR and merge authority can be granted separately; this packet alone
does not grant them. [ASSEMBLY-BRIEF.md](ASSEMBLY-BRIEF.md) is the prepared handoff.
